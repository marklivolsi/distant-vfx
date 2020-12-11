import datetime
import os
import time
import yagmail
from pprint import pformat
from fmrest import CloudServer

from distant_vfx.config import Config
from distant_vfx.video import VideoProcessor


CONFIG = Config().load_config_data('/mnt/Plugins/python3.6/shotgun_events_plugins/shotgun_events_config.yml')

LEGAL_THUMB_SRC_EXTENSIONS = ['.mov', '.mp4', '.jpg']
THUMBS_BASE_PATH = CONFIG['THUMBS_BASE_PATH']


def registerCallbacks(reg):
    matchEvents = {
        'Shotgun_PublishedFile_Change': ['*'],  # monitor for published files
    }
    reg.registerCallback(CONFIG['SG_INJECT_EXT_NAME'],  # TODO: Add SG script
                         CONFIG['SG_INJECT_EXT_KEY'],   # TODO: Add SG script
                         inject,
                         matchEvents,
                         None)


def inject(sg, logger, event, args):

    is_inject_candidate = _validate_event(event)
    if not is_inject_candidate:
        return

    logger.info(f'Processing event {event}')

    # Wait to make sure entity is fully created
    time.sleep(1)

    published_file = _get_published_file(sg, event)
    if not published_file:
        logger.error('Could not load version data for event: {event}'.format(event=event))
        return

    # Prep data for filemaker inject
    try:
        version_name = _format_version_name(published_file)
        fmp_version = _build_version_dict(published_file, version_name)
        fmp_transfer_log = _build_transfer_log_dict(published_file)
        fmp_transfer_data = _build_transfer_data_dict(published_file, version_name)

        # Generate a thumbnail if applicable
        mov_path = _get_mov_path(published_file)
        thumb_name, thumb_path = None, None
        if mov_path:
            thumb_name, thumb_path = _get_thumbnail(mov_path)
        fmp_thumb_data = _build_thumb_dict(thumb_name, thumb_path)

    except Exception as e:
        logger.exception(e)
        return


def _build_thumb_dict(thumb_name, thumb_path):
    thumb_dict = {
        'Filename': thumb_name,
        'Path': thumb_path,
    }
    return _convert_dict_data_to_str(thumb_dict)


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


def _get_mov_path(published_file):
    path = _get_published_file_path(published_file)
    if path and os.path.splitext(path)[1] in LEGAL_THUMB_SRC_EXTENSIONS:
        return path
    return None


def _build_transfer_data_dict(published_file, version_name_fmt):
    transfer_data = {
        'Filename': published_file.get('code'),
        'PublishedFileID': published_file.get('id'),
        'Path': _get_published_file_path(published_file),
        'VersionLink': version_name_fmt
    }
    return _convert_dict_data_to_str(transfer_data)


def _build_transfer_log_dict(published_file):
    transfer_log_dict = {
        'package': published_file.get('sg_delivery_package_name'),
        'path': published_file.get('sg_delivery_package_path')
    }
    return _convert_dict_data_to_str(transfer_log_dict)


def _build_version_dict(published_file, version_name_fmt):
    version_dict = {
        'VFXID': _get_vfx_entity_code(published_file),
        'ShotgunID': published_file.get('id'),  # TODO: Do we want this? Does this make sense?
        'DeliveryNote': published_file.get('description'),
        'DeliveryPackage': published_file.get('sg_delivery_package_name'),
        'Filename': version_name_fmt
    }
    return _convert_dict_data_to_str(version_dict)


def _get_vfx_entity_code(published_file):
    try:
        vfx_entity_name = published_file['entity']['name']
        return vfx_entity_name
    except:
        return ''


def _convert_dict_data_to_str(dictionary):
    return {str(key): ('' if value is None else str(value)) for key, value in dictionary.items()}


def _format_version_name(published_file):
    filename = published_file.get('code')
    if filename:
        dot_count = filename.count('.')
        if dot_count == 2:  # likely a frame range
            version = filename.split('.')[0]
        else:
            version = os.path.splitext(filename)[0]
        return version.replace(' ', '_').lower()
    return ''


def _get_published_file_path(published_file):
    try:
        path = published_file['path']['local_path_linux']
        return path
    except:
        return ''


def _get_published_file(sg, event):
    published_file = sg.find_one(
        entity_type='PublishedFile',
        filters=[
            ['id', 'is', event.get('meta').get('entity_id')]
        ],
        fields=[
            'code',                      # filename
            'description',               # submission note
            'path',                      # filepath on disk
            'entity',                    # provides access to shot / asset entity
            'sg_delivery_package_name',  # delivery package
            'sg_delivery_package_path'   # package path
        ]
    )
    return published_file


def _validate_event(event):
    event_attr = event.get('attribute_name')
    new_value = event.get('meta').get('new_value')
    return event_attr == 'sg_status_list' and new_value == 'extapp'
