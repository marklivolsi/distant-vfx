#!/bin/env python3

import argparse
import os
import sys


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'root',
        type=str,
        action='store',
        help='Path to root level directory that will be recursively searched for plate QTs to delete.'
    )
    args = parser.parse_args()
    root = args.root

    files = _scan_files(root)
    plate_qts = []
    for file in files:
        if _is_plate_qt(file):
            plate_qts.append(file)

    if not plate_qts:
        print('No plate qts found.')
        sys.exit()

    print('The following files will be deleted:')
    for qt in plate_qts:
        print(qt)
    proceed = input('Do you want to proceed? y/n\n')

    if proceed.lower() == 'y':
        for qt in plate_qts:
            print(f'Deleting {qt}')
            os.remove(qt)
    else:
        sys.exit()


def _is_plate_qt(file):
    ext = file.split('.')[-1]
    h264_dirname, dnx_dirname = '1920x1080_h264', '1920x1080_dnx115'
    return ('plate' in file) and ((h264_dirname in file) or (dnx_dirname in file)) and (ext in 'mov')


def _scan_files(root):
    for root_path, dirs, files in os.walk(root):
        for filename in files:
            yield os.path.join(root_path, filename)


if __name__ == '__main__':
    main()
