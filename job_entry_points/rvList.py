#!/bin/env python3

import argparse
import os
import subprocess
from python.distant_vfx.constants import SHOT_TREE_BASE_PATH, RV_PATH


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'shot',
        type=str,
        action='store',
        help='The VFXID of the shot to load in RV.'
    )
    args = parser.parse_args()
    shot = args.shot

    seq = shot[:3]
    shot_dir = os.path.join(SHOT_TREE_BASE_PATH, seq, shot)
    comp_dir = os.path.join(shot_dir, 'shot')
    plates_dir = os.path.join(shot_dir, 'plate')
    elem_dir = os.path.join(shot_dir, 'element')

    comp_files = _find_files(comp_dir)
    plate_files = _find_files(plates_dir)
    plate_files = [plate for plate in plate_files if '_bg' in plate or '_fg' in plate]
    elem_files = _find_files(elem_dir)

    latest_comp = _find_latest_dnx(comp_files)
    latest_elem = _find_latest_dnx(elem_files)

    files = []
    if latest_comp:
        comp_arg = _format_comp_arg(latest_comp, 17)  # todo: get the offset from the db
        files += comp_arg
    else:
        print(f'No comps found for shot {shot}.')
    if latest_elem:
        # files.append(latest_elem)
        elem_arg = _format_comp_arg(latest_elem, 17)
        files += elem_arg

    else:
        print(f'No elements found for shot {shot}.')
    if plate_files:
        plate_args = []
        for plate in plate_files:
            plate_arg = _format_plate_arg(plate, 17)
            plate_args += plate_arg
        files += plate_args
    else:
        print(f'No plates found for shot {shot}.')

    _launch_rv(files)


def _launch_rv(files):
    cmd = [RV_PATH, '-wipe'] + files

    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True,
                               shell=False)
    stdout, stderr = process.communicate()


def _format_comp_arg(file, start_frame_shift):
    return ['[', file, '-rs', str(start_frame_shift), '-in', str(start_frame_shift + 1), ']']


def _format_plate_arg(file, cut_in_frame):
    return ['[', file, '-in', str(cut_in_frame + 1), ']']


def _find_latest_dnx(files):
    if files:
        return max(files, key=os.path.getctime)
    return None


def _find_files(directory):  # only find dnx
    paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if 'dnx' in root:
                paths.append(os.path.join(root, file))
    return paths


if __name__ == '__main__':
    main()
