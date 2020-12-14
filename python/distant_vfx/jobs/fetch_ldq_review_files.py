import os
import subprocess
import sys
from fmrest import CloudServer

from ..constants import FMP_URL, FMP_PASSWORD, FMP_USERNAME, FMP_ADMINDB, FMP_TRANSFER_DATA_LAYOUT, SHOT_TREE_BASE_PATH


def main():

    # Get eligible review files (tagged with SupReviewFlag = 1)
    print('Searching for review files, please wait...')
    review_records = _get_records_from_fmp()

    # If there are no records, exit
    if not review_records:
        sys.exit()

    # Fill in missing file paths where possible
    file_paths = []
    for file in review_records:
        try:
            path = file.Path
        except AttributeError:
            path = _find_missing_filepath(file)
        if path is not None:
            file_paths.append(path)
        else:
            print(f'Could not locate file {file}')

    # Launch files in RV
    cmd = ['rv']
    for path in file_paths:
        cmd += path

    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True,
                               shell=False)
    stdout, stderr = process.communicate()


def _find_missing_filepath(filename):
    vfxid = filename[:7]
    seq = vfxid[:3]
    shot_dir_path = os.path.join(SHOT_TREE_BASE_PATH, seq, vfxid, 'shot')
    for root, dirs, files in os.walk(shot_dir_path):
        for file in files:
            if file in filename:
                return os.path.join(root, file)
    return None


def _get_records_from_fmp():
    with CloudServer(url=FMP_URL,
                     user=FMP_USERNAME,
                     password=FMP_PASSWORD,
                     database=FMP_ADMINDB,
                     layout=FMP_TRANSFER_DATA_LAYOUT
                     ) as fmp:
        fmp.login()

        # Find eligible review records
        query = {'SupReviewFlag': 1}
        try:
            records = fmp.find([query], limit=500)
        except Exception as e:
            if fmp.last_error == 401:  # no records were found
                records = None
            else:
                print('No review items found.')

        return records
