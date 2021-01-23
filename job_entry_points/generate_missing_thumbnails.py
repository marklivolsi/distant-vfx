import json
import os
import traceback
from python.distant_vfx.filemaker import CloudServerWrapper
from python.distant_vfx.video import VideoProcessor
from python.distant_vfx.utilities import dict_items_to_str
from python.distant_vfx.constants import FMP_URL, FMP_USERNAME, FMP_PASSWORD, FMP_ADMIN_DB, FMP_IMAGES_LAYOUT, \
    THUMBS_BASE_PATH, FMP_PROCESS_IMAGE_SCRIPT


def main():
    thumb_json_file = '/mnt/Plugins/python3.6/config/thumbs.json'
    try:
        with open(thumb_json_file, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        traceback.print_exc()

    movies = data.get('sg_path_to_movie')
    if not movies:
        print('No movies listed in thumbs.json file. Exiting.')
        return

    for movie in movies:
        try:
            thumb_name, thumb_path = _get_thumbnail(movie)
            fmp_thumb_data = _build_thumb_dict(thumb_name, thumb_path)
        except:
            traceback.print_exc()

    with CloudServerWrapper(url=FMP_URL,
                            user=FMP_USERNAME,
                            password=FMP_PASSWORD,
                            database=FMP_ADMIN_DB,
                            layout=FMP_IMAGES_LAYOUT
                            ) as fmp:
        fmp.login()

        for movie in movies:
            try:
                thumb_name, thumb_path = _get_thumbnail(movie)
                fmp_thumb_data = _build_thumb_dict(thumb_name, thumb_path)
            except:
                traceback.print_exc()
                continue

            # Check if image exists
            image_record = _check_image_record_exists(fmp, fmp_thumb_data)
            if not image_record or image_record.Width == '?':

                # Inject thumb if available
                img_record_id = None
                if thumb_path is not None:
                    fmp.layout = FMP_IMAGES_LAYOUT
                    img_record_id = _inject_image(fmp, fmp_thumb_data)

                # Check to make sure it injected correctly, if not try again
                if img_record_id is not None:
                    new_img = fmp.get_record(img_record_id)
                    if new_img.Width == '?':
                        img_record_id = _inject_image(fmp, fmp_thumb_data)

                # Run process img script
                if img_record_id is not None and img_record_id != -1:
                    img_primary_key = _get_image_primary_key(fmp, img_record_id)
                    if img_primary_key is not None:
                        script_res = _run_process_image_script(fmp, img_primary_key)

    # clear out the file
    with open(thumb_json_file, 'w') as file:
        empty_dict = {'sg_path_to_movie': []}
        json.dump(empty_dict, file)


def _check_image_record_exists(fmp, fmp_thumb_data):
    try:
        image_records = fmp.find([fmp_thumb_data])
        if image_records:
            return image_records[0]
        return None
    except:
        return None


def _inject_image(fmp, fmp_thumb_data):
    # image_exists = _check_image_record_exists(fmp, fmp_thumb_data)
    # if image_exists:
    #     return -1
    img_record_id = None
    try:
        thumb_file = open(fmp_thumb_data.get('Path'), 'rb')
        img_record_id = fmp.create_record(fmp_thumb_data)
        img_did_upload = fmp.upload_container(img_record_id, field_name='Image', file_=thumb_file)
        thumb_file.close()
    except:
        pass
    return img_record_id


def _get_image_primary_key(fmp, img_record_id):
    img_primary_key = None
    try:
        img_record = fmp.get_record(img_record_id)
        img_primary_key = img_record.PrimaryKey
    except:
        pass
    return img_primary_key


def _run_process_image_script(fmp, img_primary_key):
    script_res = None
    try:
        script_res = fmp.perform_script(
            name=FMP_PROCESS_IMAGE_SCRIPT,
            param=img_primary_key
        )
    except:
        pass
    return script_res


def _get_thumbnail(mov_path):
    # Get the thumbnail output path
    mov_filename = os.path.basename(mov_path)
    mov_split = os.path.splitext(mov_filename)
    mov_basename, mov_ext = mov_split[0], mov_split[1]
    thumb_filename = '0000 ' + mov_basename + '.jpg'  # Naming structure necessary to parse vfx id with current setup
    thumb_dest = os.path.join(THUMBS_BASE_PATH, thumb_filename)

    # Generate thumbnail
    if not os.path.exists(thumb_dest):
        video_processor = VideoProcessor()
        video_processor.generate_thumbnail(mov_path, thumb_dest)
    return thumb_filename, thumb_dest


@dict_items_to_str
def _build_thumb_dict(thumb_name, thumb_path):
    thumb_dict = {
        'Filename': thumb_name,
        'Path': thumb_path,
    }
    return thumb_dict
