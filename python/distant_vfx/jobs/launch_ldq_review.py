import os
import subprocess
import sys
import time
from fmrest import CloudServer
from fmrest.exceptions import BadJSON

from ..constants import FMP_URL, FMP_PASSWORD, FMP_USERNAME, FMP_ADMIN_DB, FMP_TRANSFER_DATA_LAYOUT, SHOT_TREE_BASE_PATH


# TODO: --exr flag to grab all exrs where possible
# TODO: filter dup version files based on for final, also need to filter them out when building fmp review notes

def main():

    # Get eligible review files (tagged with SupReviewFlag = 1)
    print('Searching for review files, please wait...')
    review_records = _get_records_from_fmp()

    # If there are no records, exit
    if not review_records:
        print('No review records were found.')
        sys.exit()

    # Get file paths and cut order from records
    file_paths = []
    cut_order_map = {}
    for file in review_records:

        try:
            path = file.Path
        except AttributeError:
            path = _find_missing_filepath(file)  # fill in file path where possible if not provided

        try:
            cut_order = int(file['VFXEditorialShots::CutOrder'])
        except:
            cut_order = 0  # default to 0 if can't read cut order

        if path is not None:
            cut_order_map[path] = cut_order
            file_paths.append(path)
        else:
            print(f'Could not locate file {file}')

    # Sort files by cut order
    file_paths.sort(key=lambda x: cut_order_map[x])

    # Launch files in RV
    cmd = ['rv']
    for path in file_paths:
        cmd.append(path)

    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True,
                               shell=False)
    stdout, stderr = process.communicate()


def _find_missing_filepath(filename):
    vfx_id = filename[:7]
    seq = vfx_id[:3]
    shot_dir_path = os.path.join(SHOT_TREE_BASE_PATH, seq, vfx_id, 'shot')
    for root, dirs, files in os.walk(shot_dir_path):
        for file in files:
            if file in filename:
                return os.path.join(root, file)
    return None


def _get_records_from_fmp(tries=3):
    with CloudServer(url=FMP_URL,
                     user=FMP_USERNAME,
                     password=FMP_PASSWORD,
                     database=FMP_ADMIN_DB,
                     layout=FMP_TRANSFER_DATA_LAYOUT
                     ) as fmp:
        fmp.login()

        # Find eligible review records
        query = {'SupReviewFlag': 1}
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
                    print('No review items found.')
                else:
                    print(f'Error connecting to FileMaker database.\nError: {e}')
                break
            else:
                break

        return records
