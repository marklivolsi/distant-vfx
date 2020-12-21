#!/usr/bin/env python

# Note - this job MUST be run on python 2 for access to Arch module

from collections import defaultdict
import os

# from python.distant_quicktime.farm.jobs.distant_dnx115 import DistantDNxHDFarmJob
# from python.distant_quicktime.farm.jobs.distant_h264 import DistantH264FarmJob


IMG_SEQ_EXTS = ['exr']
MOVIE_EXTS = ['mov', 'mp4']


def main(root_path):
    files = _scan_files(root_path)
    basename_map = _make_basename_map(files)
    for basename, ext_map in basename_map.items():

        exr_path = ext_map.get('exr')
        dnx_path = ext_map.get('dnx')
        h264_path = ext_map.get('h264')

        print(exr_path, dnx_path, h264_path)

        if exr_path is None:
            continue
        else:
            exr_container_path = os.path.dirname(exr_path)

        if dnx_path is None:
            pass  # render dnx

        if h264_path is None:
            pass  # render h264



# def _render_dnx115(image_path, output_path, nukescript_template_path, first_frame, last_frame, scene_name, username,
#                    notes, width=1920, height=1080):
#     dnxhd_job = DistantDNxHDFarmJob(
#         image_path=image_path,
#         output_path=output_path,
#         nukescript_path=nukescript_template_path,
#         width=width,
#         height=height,
#         text_tl=os.path.basename(output_path).split('.')[0],
#         text_br='[value frame]',
#         first_frame=first_frame,
#         last_frame=last_frame,
#         name=scene_name + ' - DNxHD 115 Render',
#         slate_left_text=os.path.basename(output_path).split('.')[0],
#         slate_right_text=username,
#         slate_bottom_text=notes,
#         priority=1
#     )
#     job_id = dnxhd_job.submit()
#
#
# def _render_h264(image_path, output_path, nukescript_template_path, first_frame, last_frame, scene_name, username,
#                  notes, width=1920, height=1080):
#     h264_job = DistantH264FarmJob(
#         image_path=image_path,
#         output_path=output_path,
#         nukescript_path=nukescript_template_path,
#         width=width,
#         height=height,
#         text_tl=os.path.basename(output_path).split('.')[0],
#         text_br='[value frame]',
#         first_frame=first_frame,
#         last_frame=last_frame,
#         name=scene_name + ' - DNxHD 115 Render',
#         slate_left_text=os.path.basename(output_path).split('.')[0],
#         slate_right_text=username,
#         slate_bottom_text=notes,
#         priority=1
#     )
#     job_id = h264_job.submit()


def _make_basename_map(filepath_list):
    basename_map = defaultdict(dict)

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

        if key is not None:
            basename_map[basename][key] = path

    return basename_map


def _scan_files(root_path):
    for root, dirs, files in os.walk(root_path):
        for file in files:
            path = os.path.join(root, file)
            yield path


if __name__ == '__main__':
    main('/Users/marklivolsi/Desktop/LUM_20200117_01')
