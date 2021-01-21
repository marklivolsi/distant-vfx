#!/bin/env python3

import argparse
import os
import re
import subprocess
import traceback

from python.distant_vfx.constants import SHOT_TREE_BASE_PATH
from python.distant_vfx.jobs import new_vendor_package


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'versions',
        nargs='+',
        type=str,
        action='store',
        help='The list of versions to find and copy.'
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '--dir',
        action='store',
        type=str,
        help='Copy files to the specified destination directory. Must specify either --dir or --pkg.'
    )

    group.add_argument(
        '--pkg',
        action='store',
        type=str,
        help='Specify a vendor code to create a new outgoing package and copy files to that package. Must specify '
             'either --dir or --pkg.'
    )

    args = parser.parse_args()
    versions = args.versions

    paths = []
    for version in versions:
        path = _get_version_path_on_disk(version)
        if path:
            paths.append(path)
        else:
            print(f'Could not find version {version}, please locate manually.')

    if args.pkg:
        dest = new_vendor_package.main(vendor_codes=[args.pkg])[0]
    else:
        dest = args.dir

    for path in paths:
        try:
            _copy_version(path, dest)
            print(f'{os.path.basename(path)} copied to {dest}')
        except:
            traceback.print_exc()


def _copy_version(path, destination):
    if not os.path.isdir(destination):
        raise OSError(f'Destination does not exist: {destination}')
    cmd = ['cp', path, destination]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=False
    )
    stdout, stderr = process.communicate()
    return stdout, stderr


def _get_version_path_on_disk(version):
    match = re.match(r'[A-Za-z]{3}\d{4}', version, re.IGNORECASE)
    if not match:
        return None
    shot, seq = version[:7], version[:3]
    expected_root = os.path.join(SHOT_TREE_BASE_PATH, seq, shot)
    for root, dirs, files in os.walk(expected_root):
        for file in files:
            if (version.lower() in file.lower()) and ('dnx' in root.lower()):  # only finds dnx files
                path = os.path.join(root, file)
                return path
    return None


if __name__ == '__main__':
    main()
