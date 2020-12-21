import os
import subprocess
import sys
import time
from fmrest import CloudServer
from fmrest.exceptions import BadJSON

from ..constants import FMP_URL, FMP_PASSWORD, FMP_USERNAME, FMP_VFX_DB, FMP_VERSIONS_LAYOUT, SHOT_TREE_BASE_PATH


def main(screening_id):

    # Get eligible review files
    print('Searching for review files, please wait...')
    records = _get_records_from_fmp(screening_id)

    # If there are no records, exit
    if not records:
        print('No review records were found.')
        sys.exit()

    # Get file paths and cut order from records
    file_paths = []
    cut_order_map = {}

    for version_record in records:

        version_name = _get_version_name_from_record(version_record)
        path = _get_filepath_from_record(version_record)

        if path is None:
            if version_name is not None:
                path = _find_missing_filepath(version_name)  # defaults to dnx mov files
                if path is None:
                    print(f'Could not locate version on disk: {version_name}')
                    continue
            else:
                print(f'Cannot locate version name or path for record, skipping. (Record data: {version_record})')
                continue

        # If we get here, we have a path to the version
        cut_order = _get_cut_order_from_record(version_record)
        cut_order_map[path] = cut_order
        file_paths.append(path)

    # Sort files by cut order
    file_paths.sort(key=lambda x: cut_order_map[x])

    # Launch files in RV
    print('Launching files in RV...')
    _launch_files_in_rv(file_paths)


def _launch_files_in_rv(file_paths):
    cmd = ['/opt/rv/rv-centos7-x86-64-7.6.1/bin/rv']
    for path in file_paths:
        cmd.append(path)

    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True,
                               shell=False)
    stdout, stderr = process.communicate()


def _get_cut_order_from_record(record):
    try:
        cut_order = int(record['VFXEditorialShots::CutOrder'])
    except:
        cut_order = 0  # default to 0 if can't read cut order
    return cut_order


def _get_filepath_from_record(record):
    try:
        path = record.Path  # TODO: Change this, currently this will always fail because there is no 'Path' field
        if not path:
            return None
        return path
    except AttributeError:
        return None


def _get_version_name_from_record(record):
    try:
        version_name = record.Filename
        return version_name
    except:
        return None


def _find_missing_filepath(version_name, identifier='dnx'):
    paths = _find_all_matching_filepaths(version_name, _get_shot_dir_path(version_name))

    # If no paths found in shot dir, try ref dir
    if not paths:
        ref_path = _get_ref_dir_path(version_name)
        paths = _find_all_matching_filepaths(version_name, ref_path)

    if paths:
        for path in paths:
            if identifier.lower() in path.lower():
                return path
        return paths[0]  # if nothing matches identifier, default to the first file found
    return None


def _find_all_matching_filepaths(version_name, root_path):
    paths = []
    # shot_dir_path = _get_shot_dir_path(version_name)
    for root, dirs, files in os.walk(root_path):
        for file in files:
            path = os.path.join(root, file)
            if _is_frame_range(path):  # currently will skip over frame ranges
                break
            else:
                if version_name.lower() in file.lower():
                    paths.append(path)
    return paths


def _is_frame_range(filepath):
    # pattern = re.compile(r'\.\d{4}\.')
    # match = re.search(pattern, filepath)
    # if match:
    #     return True
    # return False
    return os.path.splitext(filepath)[1] in ['.exr']


def _get_shot_dir_path(filename):
    vfx_id = filename[:7]
    seq = vfx_id[:3]
    shot_dir_path = os.path.join(SHOT_TREE_BASE_PATH, seq, vfx_id)
    return shot_dir_path


def _get_ref_dir_path(filename):
    seq = filename[:3]
    ref_path = os.path.join(SHOT_TREE_BASE_PATH, seq, '_reference')
    return ref_path


def _get_records_from_fmp(screening_id, tries=3):
    with CloudServer(url=FMP_URL,
                     user=FMP_USERNAME,
                     password=FMP_PASSWORD,
                     database=FMP_VFX_DB,
                     layout=FMP_VERSIONS_LAYOUT
                     ) as fmp:
        fmp.login()

        # Find eligible review records
        query = {'Screenings:screeningID': int(screening_id)}
        records = None
        for i in range(tries):
            try:
                records = fmp.find([query], limit=500)  # limit is 100 by default
            except BadJSON as e:
                if i <= tries - 1:
                    time.sleep(0.5)
                    continue
                else:
                    print(f'Error connecting to FileMaker database.\nError: {e}\nResponse: {e._response}')
            except Exception as e:
                if fmp.last_error == 401:  # no records were found
                    pass
                else:
                    print(f'Error connecting to FileMaker database.\nError: {e}')
                break
            else:
                break

        return records
