#!/usr/bin/env python3

import argparse
import os
import traceback

import python.distant_vfx.constants as CONST
from python.distant_vfx.utilities import dict_items_to_str
from python.distant_vfx.video import VideoProcessor
from python.distant_vfx.filemaker import CloudServerWrapper


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'filepath',
        type=str,
        help='Path to the video file from which to generate and inject a thumbnail.'
    )
    args = parser.parse_args()
    filepath = args.filepath

    # Check the video exists
    if not os.path.exists(filepath):
        raise FileNotFoundError
    elif os.path.splitext(filepath)[1] not in CONST.LEGAL_THUMB_SRC_EXTENSIONS:
        raise ValueError('Invalid source file type for generating thumbnails.')

    # Generate thumbnail
    mov_filename = os.path.basename(filepath)
    mov_basename = mov_filename.split('.')[0]
    thumb_filename = f'0000 {mov_basename}.jpg'
    thumb_destination = os.path.join(CONST.THUMBS_BASE_PATH, thumb_filename)
    if not os.path.exists(thumb_destination):
        print('Generating thumbnail...')
        processor = VideoProcessor()
        processor.generate_thumbnail(filepath, thumb_destination)
    else:
        print('Thumbnail already exists.')

    # Prep thumb dict
    thumb_dict = _build_thumb_dict(thumb_filename, thumb_destination)

    # Inject to FileMaker
    with CloudServerWrapper(
        url=CONST.FMP_URL,
        user=CONST.FMP_USERNAME,
        password=CONST.FMP_PASSWORD,
        database=CONST.FMP_ADMIN_DB,
        layout=CONST.FMP_IMAGES_LAYOUT
    ) as fmp:
        fmp.login()

        print('Injecting image...')
        img_record_id = _inject_image(fmp, fmp_thumb_data=thumb_dict)
        if img_record_id is not None:
            new_img = fmp.get_record(img_record_id)
            if new_img.Width == '?':
                img_record_id = _inject_image(fmp, thumb_dict)

        # Run process img script
        if img_record_id is not None:
            img_primary_key = _get_image_primary_key(fmp, img_record_id)
            if img_primary_key is not None:
                print('Running process image script...')
                script_res = _run_process_image_script(fmp, img_primary_key)

    print(f'Injection complete. New image primary key is {img_primary_key}')


def _run_process_image_script(fmp, img_primary_key):
    script_res = None
    try:
        script_res = fmp.perform_script(
            name=CONST.FMP_PROCESS_IMAGE_SCRIPT,
            param=img_primary_key
        )
    except:
        traceback.print_exc()
    return script_res


def _get_image_primary_key(fmp, img_record_id):
    img_primary_key = None
    try:
        img_record = fmp.get_record(img_record_id)
        img_primary_key = img_record.PrimaryKey
    except:
        print(f'Error running process image script for image {img_primary_key}')
        traceback.print_exc()
    return img_primary_key


def _inject_image(fmp, fmp_thumb_data):
    img_record_id = None
    try:
        thumb_file = open(fmp_thumb_data.get('Path'), 'rb')
        img_record_id = fmp.create_record(fmp_thumb_data)
        img_did_upload = fmp.upload_container(img_record_id, field_name='Image', file_=thumb_file)
        thumb_file.close()
    except:
        traceback.print_exc()
    return img_record_id


@dict_items_to_str
def _build_thumb_dict(thumb_name, thumb_path):
    thumb_dict = {
        'Filename': thumb_name,
        'Path': thumb_path,
    }
    return thumb_dict


if __name__ == '__main__':
    main()
