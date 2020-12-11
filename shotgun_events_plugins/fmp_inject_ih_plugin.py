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
        'Shotgun_Version_Change': ['*'],  # look for any version change event
    }
    reg.registerCallback(CONFIG['SG_INJECT_IH_NAME'],
                         CONFIG['SG_INJECT_IH_KEY'],
                         inject,
                         matchEvents,
                         None)


def inject(sg, logger, event, args):

    # Check if the version status has just been changed to 'ihapp', exit if not
    is_inject_candidate = _validate_event(event)
    if not is_inject_candidate:
        return

    logger.info(f'Processing event {event}')

    # Wait to make sure entity is fully created
    time.sleep(1)

    # Get the relevant version data from shotgun
    version_data = _get_version(sg, event)
    if not version_data:
        logger.error('Could not load version data for event: {event}'.format(event=event))
        return

    try:
        # Prep data for FileMaker inject
        version_name = _format_version_name(version_data)
        fmp_version = _build_version_dict(version_data, version_name)
        fmp_transfer_log = _convert_dict_data_to_str({'package': _get_package_name()})
        published_files = _get_published_file(sg, version_data)
        fmp_transfer_data_dicts = _build_transfer_data_dicts(published_files, version_name)

        # Generate a thumbnail if applicable
        mov_path = _get_mov_path(version_data)
        thumb_name, thumb_path = None, None
        if mov_path:
            thumb_name, thumb_path = _get_thumbnail(mov_path)
        fmp_thumb_data = _build_thumb_dict(thumb_name, thumb_path)

    except Exception as e:
        logger.exception(e)
        return

    # Inject data to filemaker
    with CloudServer(url=CONFIG['FMP_URL'],
                     user=CONFIG['FMP_USERNAME'],
                     password=CONFIG['FMP_PASSWORD'],
                     database=CONFIG['FMP_ADMINDB'],
                     layout=CONFIG['FMP_VERSIONS_LAYOUT']
                     ) as fmp:
        fmp.login()

        # Inject version
        try:
            version_record_id = fmp.create_record(fmp_version)
        except Exception as e:
            logger.exception(e)

        # Inject transfer log
        fmp.layout = CONFIG['FMP_TRANSFER_LOG_LAYOUT']
        try:
            records = fmp.find([fmp_transfer_log])
        except Exception as e:
            if fmp.last_error == 401:  # no records were found
                records = None
            else:
                logger.exception(e)

        # If transfer log does not exist, create a new one
        if not records:
            try:
                transfer_record_id = fmp.create_record(fmp_transfer_log)
                transfer_record_data = fmp.get_record(transfer_record_id)
                transfer_primary_key = transfer_record_data.PrimaryKey
            except Exception as e:
                logger.exception(e)
        else:
            transfer_primary_key = records[0].PrimaryKey

        # Inject transfer data
        fmp.layout = CONFIG['FMP_TRANSFER_DATA_LAYOUT']
        try:
            if fmp_transfer_data_dicts:
                for data_dict in fmp_transfer_data_dicts:
                    data_dict['Foriegnkey'] = transfer_primary_key
                    filename_record_id = fmp.create_record(data_dict)
        except Exception as e:
            logger.exception(e)

        # Inject thumb if available
        if thumb_path is not None:
            fmp.layout = CONFIG['FMP_IMAGES_LAYOUT']
            try:
                thumb_file = open(thumb_path, 'rb')
                img_record_id = fmp.create_record(fmp_thumb_data)
                img_did_upload = fmp.upload_container(img_record_id, field_name='Image', file_=thumb_file)
                thumb_file.close()
            except Exception as e:
                logger.exception(e)

        try:
            img_record = fmp.get_record(img_record_id)
            img_primary_key = img_record.PrimaryKey
            script_res = fmp.perform_script(
                name=CONFIG['FMP_PROCESS_IMAGE_SCRIPT'],
                param=img_primary_key
            )
        except Exception as e:
            msg = f'Error performing image processing script. Please see below for details.\n\n{e}'
            logger.exception(e)

        logger.info(f'Completed event processing {event}')
        _send_success_email(fmp_version, fmp_transfer_log, fmp_transfer_data_dicts, fmp_thumb_data)


def _send_success_email(version_data, fmp_transfer_log, fmp_transfer_data_dicts, thumb_data):
    subject = f'[DISTANT_API] Successful In House data injection at {datetime.datetime.now()}'
    content = 'Shotgun data successfully injected into FileMaker. Please see below for details.\n\n' \
              '<hr>' \
              f'<h3>VERSION DATA</h3>\n{pformat(version_data)}\n\n' \
              f'<h3>TRANSFER LOG DATA</h3>\n{pformat(fmp_transfer_log)}\n\n' \
              f'<h3>TRANSFER FILES DATA</h3>\n{pformat(fmp_transfer_data_dicts)}\n\n' \
              f'<h3>IMAGE DATA</h3>\n{pformat(thumb_data)}\n\n' \
              f'<hr>'
    yag = yagmail.SMTP(
        user=CONFIG['EMAIL_USERNAME'],
        password=CONFIG['EMAIL_PASSWORD']
    )
    yag.send(
        to=CONFIG['EMAIL_RECIPIENTS'].split(','),
        subject=subject,
        contents=content
    )


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


def _get_mov_path(version_data):
    return version_data.get('sg_path_to_movie')

    # Do we want to use published files?
    # for published_file in published_files:
    #     path = _get_published_file_path(published_file)
    #     if path and os.path.splitext(path)[1] in LEGAL_THUMB_SRC_EXTENSIONS:
    #         return path
    # return None


def _format_version_name(version_data):
    version_code = version_data.get('code')
    if version_code:
        return version_code.replace(' ', '_').lower()
    return ''


def _build_transfer_data_dicts(published_files, version_name_fmt):
    transfer_dicts = []
    if not published_files:
        return None
    for published_file in published_files:
        transfer_data = {
            'Filename': published_file.get('code'),
            'PublishedFileID': published_file.get('id'),
            'Path': _get_published_file_path(published_file),
            'VersionLink': version_name_fmt
        }
        transfer_dicts.append(_convert_dict_data_to_str(transfer_data))
    return transfer_dicts


def _get_published_file_path(published_file):
    try:
        path = published_file['path']['local_path_linux']
        return path
    except:
        return ''


def _get_published_file(sg, version_data):
    published_files = sg.find(
        entity_type='PublishedFile',
        filters=[
            ['version.Version.code', 'is', version_data.get('code')]
        ],
        fields=[
            'code',
            'path',
        ]
    )
    return published_files


def _build_version_dict(version_data, version_name_fmt):
    version_dict = {
        'VFXID': _get_vfx_entity_code(version_data),
        'ShotgunID': version_data.get('id'),
        'DeliveryNote': version_data.get('description'),
        'DeliveryPackage': _get_package_name(),
        'Filename': version_name_fmt
    }
    return _convert_dict_data_to_str(version_dict)


def _get_package_name():
    return 'dst_ih_' + datetime.datetime.now().strftime('%Y%m%d')


def _convert_dict_data_to_str(dictionary):
    return {str(key): ('' if value is None else str(value)) for key, value in dictionary.items()}


def _get_vfx_entity_code(version_data):
    try:
        vfx_entity_name = version_data['entity']['name']
        return vfx_entity_name
    except:
        return ''


def _get_version(sg, event):
    version = sg.find_one(
        entity_type='Version',
        filters=[
            ['id', 'is', event.get('meta').get('entity_id')]
        ],
        fields=[
            'code',
            'description',
            'entity',  # gets the shots / assets links
            'published_files',  # gets the file links
            'sg_path_to_movie'
        ]
    )
    return version


def _validate_event(event):
    event_attr = event.get('attribute_name')
    new_value = event.get('meta').get('new_value')
    return event_attr == 'sg_status_list' and new_value == 'ihapp'
