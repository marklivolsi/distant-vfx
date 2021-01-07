import os
import sys
import traceback

from ..filemaker import CloudServerWrapper
from ..sequences import ImageSequence
from ..utilities import make_basename_map_from_file_path_list, parse_files_from_basename_map, dict_items_to_str
from ..constants import FMP_URL, FMP_USERNAME, FMP_PASSWORD, FMP_ADMIN_DB, FMP_VERSIONS_LAYOUT, \
    FMP_TRANSFER_LOG_LAYOUT, FMP_TRANSFER_DATA_LAYOUT


def main(package_path):
    all_files = _scan_package_files(package_path)
    basename_map = make_basename_map_from_file_path_list(all_files)
    unique_paths = parse_files_from_basename_map(basename_map)
    package_name = _get_package_name(package_path)
    versions_list = _build_version_dicts(unique_paths, package_name)
    transfer_log = _build_transfer_log(package_path, package_name)
    transfer_data_list = _build_transfer_data(unique_paths)

    with CloudServerWrapper(url=FMP_URL,
                            user=FMP_USERNAME,
                            password=FMP_PASSWORD,
                            database=FMP_ADMIN_DB,
                            layout=FMP_VERSIONS_LAYOUT
                            ) as fmp:
        fmp.login()

        for version in versions_list:
            try:
                version_name = version.get('Filename')
                version_records = None
                if version_name is not None:
                    try:
                        version_records = fmp.find([{'Filename': version_name}])
                    except:
                        if fmp.last_error == 401:
                            pass
                if not version_records:
                    record_id = fmp.create_record(version)
            except:
                traceback.print_exc()

        fmp.layout = FMP_TRANSFER_LOG_LAYOUT
        try:
            transfer_log_id = fmp.create_record(transfer_log)
        except:
            traceback.print_exc()
            transfer_log_id = ''

        if transfer_log_id:
            try:
                transfer_log_primary_key = fmp.get_record(transfer_log_id).PrimaryKey
            except:
                traceback.print_exc()
                transfer_log_primary_key = ''

        fmp.layout = FMP_TRANSFER_DATA_LAYOUT
        for transfer_data in transfer_data_list:
            transfer_data['Foriegnkey'] = transfer_log_primary_key
            try:
                transfer_data_id = fmp.create_record(transfer_data)
            except:
                traceback.print_exc()

        print(f'Data injection complete for package: {package_path}')


def _scan_package_files(package_path):
    for root, dirs, files in os.walk(package_path):
        for file in files:
            if os.path.splitext(file)[1] == '.csv':
                sys.exit('Please ingest this package using Shotgun.')
            elif file.startswith('.'):
                continue
            else:
                path = os.path.join(root, file)
                yield path


def _build_version_dicts(unique_files, package_name):
    versions = []
    for path in unique_files:
        version_dict = _build_one_version_dict(path, package_name)
        versions.append(version_dict)
    return versions


@dict_items_to_str
def _build_one_version_dict(filepath, package_name):
    version_name = _get_version_name_from_path(filepath)
    version_dict = {
        'VFXID': version_name[:7],
        'DeliveryPackage': package_name,
        'Filename': version_name,
    }
    return version_dict


def _get_start_and_end_frame(file):
    if isinstance(file, ImageSequence):
        return file.start, file.end
    return None, None


def _get_version_name_from_path(path):
    if isinstance(path, ImageSequence):
        return path.basename
    basename = os.path.basename(path)
    split = basename.split('.')
    version_name = split[0]
    return version_name


def _get_package_name(package_path):
    return os.path.basename(package_path)


@dict_items_to_str
def _build_transfer_log(package_path, package_name):
    transfer_log_dict = {
        'package': package_name,
        'path': package_path
    }
    return transfer_log_dict


def _build_transfer_data(unique_paths):
    transfer_data = []
    for path in unique_paths:
        transfer_data_dict = _build_one_transfer_data_dict(path)
        transfer_data.append(transfer_data_dict)
    return transfer_data


@dict_items_to_str
def _build_one_transfer_data_dict(filepath):
    if isinstance(filepath, ImageSequence):
        filename = filepath.name
        filepath = filepath.path
    else:
        filename = os.path.basename(filepath)
    start_frame, end_frame = _get_start_and_end_frame(filepath)
    transfer_data = {
        'Filename': filename,
        'Path': filepath,
        'VersionLink': _get_version_name_from_path(filepath),
        'Frame Start': start_frame,
        'Frame End': end_frame
    }
    return transfer_data
