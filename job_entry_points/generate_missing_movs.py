#!/usr/bin/env python

# Note - this job MUST be run on python 2 for access to Arch module

from collections import defaultdict
import os
import sys

from python.distant_quicktime.farm.jobs.distant_dnx115 import DistantDNxHDFarmJob
from python.distant_quicktime.farm.jobs.distant_h264 import DistantH264FarmJob


# TODO: If mov exists but in wrong place, move it to the right place
# TODO: Find .cube files

def main(root_path):
    files = _scan_files(root_path)
    basename_map, frame_map = _make_basename_map(files)
    for basename, ext_map in basename_map.items():

        exr_path = ext_map.get('exr')
        dnx_path = ext_map.get('dnx')
        h264_path = ext_map.get('h264')

        if exr_path is None:
            continue  # skip it if we don't have exr
        else:
            exr_container_path = os.path.dirname(exr_path)

        parent_path = os.path.dirname(exr_container_path)
        width, height = _get_qt_dimensions(exr_container_path)
        resolution_folder_base = str(width) + 'x' + str(height)
        filename = basename + '.mov'

        first_frame, last_frame = min(frame_map[basename]), max(frame_map[basename])

        if dnx_path is None:
            resolution_folder_name = resolution_folder_base + '_dnx115'
            output_path = os.path.join(parent_path, resolution_folder_name, filename)
            _render_dnx115(
                image_path=exr_path,
                output_path=output_path,
                nukescript_template_path=None,
                first_frame=first_frame,
                last_frame=last_frame,
                scene_name=basename,
                username='Distant VFX',
                notes='Plate check render',
                width=width,
                height=height,
            )

        if h264_path is None:
            resolution_folder_name = resolution_folder_base + '_h264'
            output_path = os.path.join(parent_path, resolution_folder_name, filename)
            _render_h264(
                image_path=exr_path,
                output_path=output_path,
                nukescript_template_path=None,
                first_frame=first_frame,
                last_frame=last_frame,
                scene_name=basename,
                username='Distant VFX',
                notes='Plate check render',
                width=width,
                height=height
            )


def _get_qt_dimensions(exr_container_dir_path):
    basename = os.path.basename(exr_container_dir_path)
    split = basename.split('_')
    split2 = split[0].split('x')
    width, height = split2[0], split2[1]
    return int(width), int(height)


def _render_dnx115(image_path, output_path, nukescript_template_path, first_frame, last_frame, scene_name, username,
                   notes, width=1920, height=1080):
    dnxhd_job = DistantDNxHDFarmJob(
        image_sequence=image_path,
        output_path=output_path,
        nukescript_path=nukescript_template_path,
        width=width,
        height=height,
        text_tl=os.path.basename(output_path).split('.')[0],
        text_br='[value frame]',
        first_frame=first_frame,
        last_frame=last_frame,
        name=scene_name + ' - DNxHD 115 Render',
        slate_left_text=os.path.basename(output_path).split('.')[0],
        slate_right_text=username,
        slate_bottom_text=notes,
    )
    job_id = dnxhd_job.submit()


def _render_h264(image_path, output_path, nukescript_template_path, first_frame, last_frame, scene_name, username,
                 notes, width=1920, height=1080):
    h264_job = DistantH264FarmJob(
        image_sequence=image_path,
        output_path=output_path,
        nukescript_path=nukescript_template_path,
        width=width,
        height=height,
        text_tl=os.path.basename(output_path).split('.')[0],
        text_br='[value frame]',
        first_frame=first_frame,
        last_frame=last_frame,
        name=scene_name + ' - DNxHD 115 Render',
        slate_left_text=os.path.basename(output_path).split('.')[0],
        slate_right_text=username,
        slate_bottom_text=notes,
    )
    job_id = h264_job.submit()


def _make_basename_map(filepath_list):
    basename_map = defaultdict(dict)
    frame_map = defaultdict(list)

    for path in filepath_list:
        filename = os.path.basename(path)
        split = filename.split('.')
        basename, ext = split[0], split[-1]
        path_lower = path.lower()

        key = None
        if (ext in 'exr') and ('exr' not in basename_map):
            key = 'exr'
        elif ext in 'mov':
            if 'dnx' in path_lower:
                key = 'dnx'
            elif 'h264' in path_lower:
                key = 'h264'
        # elif (ext in 'cube') and ('cube' not in basename_map):
        #     key = 'cube'

        if key is None:
            continue

        if key in 'exr':
            frame = split[-2]

            frame_map[basename].append(int(frame))

            split[-2] = '%{}d'.format(str(len(frame)).zfill(2))
            exr_filename_fmt = '.'.join(split)
            dir_name = os.path.dirname(path)
            path = os.path.join(dir_name, exr_filename_fmt)

        basename_map[basename][key] = path

    return basename_map, frame_map


def _scan_files(root_path):
    for root, dirs, files in os.walk(root_path):
        for file in files:
            path = os.path.join(root, file)
            yield path


if __name__ == '__main__':
    main(sys.argv[1])
