import os
import subprocess
from . import new_package
from ..constants import TO_EDT_MAILBOX_PATH


def main(scan_dir, output_dir=TO_EDT_MAILBOX_PATH, new_delivery=True):

    # Get all dnx files in pkg
    dnx_files = _find_dnx_files(scan_dir)

    if not dnx_files:
        print(f'No dnx files found at path: {scan_dir}')
    else:
        print('Found dnx files:')
        for dnx in dnx_files:
            print(dnx)

    if new_delivery:
        output_dir = new_package.main(output_dir)
        print(f'Creating new package: {output_dir}')

    print('Copying files...')
    for dnx in dnx_files:
        _copy_dnx(dnx, output_dir)


def _copy_dnx(dnx_path, output_dir):
    try:
        cmd = ['cp', dnx_path, output_dir]
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True,
                                   shell=False)
        _, _ = process.communicate()
        print(f'Copied dnx file: {dnx_path}')
    except:
        print(f'Error copying dnx file: {dnx_path}')


def _find_dnx_files(root_path):
    dnx_files = []
    for root, dirs, files in os.walk(root_path):
        if 'dnx' in root:
            for file in files:
                path = os.path.join(root, file)
                dnx_files.append(path)
    return dnx_files
