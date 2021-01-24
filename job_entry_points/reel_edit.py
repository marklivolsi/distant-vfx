#!/bin/env python3

import argparse
import os
import subprocess
import sys
from python.distant_vfx.filemaker import CloudServerWrapper
from python.distant_vfx.constants import FMP_URL, FMP_USERNAME, FMP_PASSWORD, FMP_VFX_DB, FMP_SHOTS_LAYOUT, RV_PATH, \
    SHOT_TREE_BASE_PATH


# REEL_FRAME_OFFSET = {
#     1: 86400,
#
# }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('reel',
                        type=int,
                        action='store',
                        help='Reel number to conform.')
    args = parser.parse_args()
    reel = args.reel

    # Find latest reel qt
    print('Finding latest reel QT...')
    reel_qt = _find_latest_reel_qt(reel)
    if not reel_qt:
        print(f'Could not find QT for reel {reel}.')
    else:
        print(f'Found reel QT: {reel_qt}')

    # Find shot records in filemaker
    print('Searching FileMaker database for shot records...')
    records = _get_reel_versions_from_filemaker(reel)
    if not records:
        print(f'No shot records found for reel {reel}.')
        sys.exit()
    else:
        print(f'Found records in reel {reel}.')

    # Filter records to those with in-cut versions
    print('Filtering records with in-cut versions...')
    in_cut_records = _filter_records_with_cut_in_version(records)
    if not in_cut_records:
        print('No records found with in-cut versions.')
        sys.exit()
    else:
        print(f'Found {len(in_cut_records)} records with in-cut versions.')

    # Find versions on disk
    path_tuples = []
    codec_type = 'h264'
    print(f'Finding {codec_type} versions on disk...')
    for version_tuple in in_cut_records:
        version, cut_in, duration = version_tuple
        path = _find_version_on_disk(version, codec_type=codec_type)
        if path:
            print(f'Found version {version} at path: {path}')
            path_tuple = (path, cut_in, duration)
            path_tuples.append(path_tuple)
        else:
            print(f'Could not find version {version} on disk.')

    # Build RV command
    print(f'Building RV command...')
    cmd = _build_rv_command(reel_qt, path_tuples)

    # Launch RV
    print(f'Launching files in RV...')
    _launch_rv(cmd)


def _launch_rv(cmd):
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True,
                               shell=False)
    stdout, stderr = process.communicate()


def _find_latest_reel_qt(reel_num):
    identifier = f'_r{reel_num}'
    reel_dir = '/mnt/Projects/dst/post/reference/reels'
    for file in os.listdir(reel_dir):
        if identifier in file:
            return os.path.join(reel_dir, file)
    return None


def _find_version_on_disk(version, codec_type='dnx'):
    shot = version[:7]
    seq = shot[:3]
    shot_dir = os.path.join(SHOT_TREE_BASE_PATH, seq, shot)
    shot_files = _find_files(shot_dir)
    for file in shot_files:
        ext = file.split('.')[-1]
        file_lower = file.lower()
        if codec_type in file_lower and ext == 'mov' and version.lower() in file_lower:
            return file
    return None


def _find_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            yield os.path.join(root, file)


def _build_rv_command(reel_qt_path, version_path_cut_order_tuple_list):
    first_version_cut = version_path_cut_order_tuple_list[0][1]
    first_reel_arg = _construct_reel_qt_source_arg(reel_qt_path, cut_out=first_version_cut)
    cmd = [RV_PATH] + first_reel_arg

    list_len = len(version_path_cut_order_tuple_list)
    for index, version_tuple in enumerate(version_path_cut_order_tuple_list):
        path, cut_in, duration = version_tuple
        range_start = cut_in - 1
        cut_out = range_start + duration
        version_arg = _construct_version_qt_source_arg(path, range_start=range_start, cut_in=cut_in, cut_out=cut_out)
        cmd += version_arg

        if index == list_len - 1:
            last_reel_arg = _construct_reel_qt_source_arg(reel_qt_path, cut_in=cut_out+1)
            cmd += last_reel_arg
            break

        next_cut_in = version_path_cut_order_tuple_list[index + 1][1]
        if next_cut_in == cut_out + 1:
            continue
        else:
            # fill in gaps if needed with reel qt
            reel_arg = _construct_reel_qt_source_arg(reel_qt_path, cut_in=cut_out+1, cut_out=next_cut_in-1)
            cmd += reel_arg
    return cmd


def _construct_version_qt_source_arg(version_qt_path, range_start=None, cut_in=None, cut_out=None):
    arg = ['[', version_qt_path]
    if range_start:
        arg += ['-rs', str(range_start)]
    if cut_in:
        arg += ['-in', str(cut_in)]
    if cut_out:
        arg += ['-out', str(cut_out)]
    arg.append(']')
    return arg


def _construct_reel_qt_source_arg(reel_qt_path, cut_in=None, cut_out=None):
    arg = ['[', reel_qt_path]
    if cut_in:
        arg += ['-in', str(cut_in)]
    if cut_out:
        arg += ['-out', str(cut_out)]
    arg.append(']')
    return arg


def _filter_records_with_cut_in_version(records):
    record_cut_order_tuples = []
    for record in records:
        try:
            current_filename = record['CurrentFilename']
            assert current_filename
            cut_order = int(record['VFXEditorialShots::CutOrder'])
            duration = int(record['VFXEditorialShots::Duration'])
            record_cut_order_tuples.append((current_filename, cut_order, duration))
        except:
            pass
    return sorted(record_cut_order_tuples, key=lambda x: x[1])  # sort by cut order


def _get_reel_versions_from_filemaker(reel_num):
    with CloudServerWrapper(url=FMP_URL,
                            user=FMP_USERNAME,
                            password=FMP_PASSWORD,
                            database=FMP_VFX_DB,
                            layout=FMP_SHOTS_LAYOUT
                            ) as fmp:
        fmp.login()

        query = {'VFXEditorialShots::Reel': str(reel_num)}
        records = fmp.find([query], limit=1000)
        return records


if __name__ == '__main__':
    main()
