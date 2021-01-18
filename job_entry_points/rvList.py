#!/bin/env python3

import argparse
import os
import subprocess
from python.distant_vfx.filemaker import CloudServerWrapper
from python.distant_vfx.constants import SHOT_TREE_BASE_PATH, RV_PATH, FMP_URL, FMP_USERNAME, FMP_PASSWORD, \
    FMP_VFX_DB, FMP_VERSIONS_LAYOUT


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

    # Get the correct paths to comps / plates / elements directories
    seq = shot[:3]
    shot_dir = os.path.join(SHOT_TREE_BASE_PATH, seq, shot)
    comp_dir = os.path.join(shot_dir, 'shot')
    plates_dir = os.path.join(shot_dir, 'plate')
    elem_dir = os.path.join(shot_dir, 'element')

    # Scan the above directories for files
    comp_files = _find_files(comp_dir)
    plate_files = _find_files(plates_dir)
    plate_files = [plate for plate in plate_files if '_bg' in plate or '_fg' in plate]  # only grab main bg/fg plates
    elem_files = _find_files(elem_dir)

    # Find the most recently created files
    latest_comp = _find_latest_dnx(comp_files)
    latest_elem = _find_latest_dnx(elem_files)

    files = []
    try:
        # Grab version data from filemaker (to get frame offset based on lineups)
        version_records = _find_version_data(latest_comp)
        record = version_records[0]
        frame_offset, range_start = _get_frame_offset_and_range_start_from_version_data(record)
    except:
        # Set a default of 17, works for most shots
        frame_offset, range_start = 17, 17

    if latest_comp:
        # Format the source file comp arg for RV
        comp_arg = _format_comp_arg(file=latest_comp, range_start=range_start)
        files += comp_arg
    else:
        print(f'No comps found for shot {shot}.')

    if latest_elem:
        # Format the element arg for RV
        elem_arg = _format_comp_arg(file=latest_elem, range_start=range_start)
        files += elem_arg
    else:
        print(f'No elements found for shot {shot}.')

    if plate_files:
        plate_args = []
        for plate in plate_files:  # open all plates since we don't know which is correct
            plate_arg = _format_plate_arg(plate, frame_offset=frame_offset)
            plate_args += plate_arg
        files += plate_args
    else:
        print(f'No plates found for shot {shot}.')

    # Launch files in RV with -wipe overlay mode
    _launch_rv(files)


def _launch_rv(files):
    cmd = [RV_PATH, '-wipe'] + files
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True,
                               shell=False)
    stdout, stderr = process.communicate()


def _format_comp_arg(file, range_start):
    return ['[', file, '-rs', str(range_start), ']']


def _format_plate_arg(file, frame_offset):
    return ['[', file, '-in', str(frame_offset), ']']


def _get_frame_offset_and_range_start_from_version_data(record):
    comp_start = record['VFXEditorialShots::CompStart']
    frame_offset, range_start = 0, 0
    if comp_start:
        comp_start = int(comp_start)
        if comp_start > 1000:
            frame_offset = comp_start - 1000
            range_start = frame_offset

    # vendor = record['Vendor'].lower().replace(' ', '').replace('.', '')
    # if 'ih' in vendor:
        # range_start += 1

    return frame_offset, range_start


def _find_version_data(filepath):
    filename = os.path.basename(filepath)
    version_name = filename.split('.')[0]
    with CloudServerWrapper(url=FMP_URL,
                            user=FMP_USERNAME,
                            password=FMP_PASSWORD,
                            database=FMP_VFX_DB,
                            layout=FMP_VERSIONS_LAYOUT
                            ) as fmp:
        fmp.login()
        query = {'Filename': version_name}
        records = None
        try:
            records = fmp.find([query])
        except:
            if fmp.last_error == 401:
                pass
            else:
                raise
        return records


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
