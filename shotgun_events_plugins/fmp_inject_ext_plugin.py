import datetime
import os
import time
import yagmail
from pprint import pformat
from fmrest import CloudServer
from fmrest.exceptions import BadJSON

from distant_vfx.config import Config
from distant_vfx.video import VideoProcessor
# from distant_vfx.constants import SG_EVENTS_CONFIG_PATH  # TODO: Enable this

SG_EVENTS_CONFIG_PATH = '/mnt/Plugins/python3.6/config/shotgun_events_config.yml'

CONFIG = Config().load_config_data(SG_EVENTS_CONFIG_PATH)

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

    # Inject data to filemaker
    with CloudServer(url=CONFIG['FMP_URL'],
                     user=CONFIG['FMP_USERNAME'],
                     password=CONFIG['FMP_PASSWORD'],
                     database=CONFIG['FMP_ADMINDB'],
                     layout=CONFIG['FMP_VERSIONS_LAYOUT']
                     ) as fmp:
        fmp.login()

        report_version, report_transfer_log, report_transfer_data, report_img = True, True, True, True

        # Check if version record already exists
        version_records = _find_fmp_version(fmp, version_name, logger)

        # If version record does not exist, create a new one
        if not version_records:
            version_record_id = _inject_version(fmp, fmp_version, logger)
            if not version_record_id:
                report_version = False

        # Switch to transfer log layout
        fmp.layout = CONFIG['FMP_TRANSFER_LOG_LAYOUT']
        transfer_primary_key = None

        # Perform find to see if transfer log already exists
        transfer_log_records = _find_transfer_log(fmp, fmp_transfer_log, logger)
        if transfer_log_records:
            # If so, set the primary key
            transfer_primary_key = transfer_log_records[0].PrimaryKey
        else:
            # If not, create a new transfer log record and get primary key
            transfer_log_id = _inject_transfer_log(fmp, fmp_transfer_log, logger)
            if transfer_log_id is None:  # record creation failed
                report_transfer_log = False
            else:
                transfer_primary_key = _get_transfer_log_primary_key(fmp, transfer_log_id, fmp_transfer_log, logger)

        # Inject transfer data
        fmp.layout = CONFIG['FMP_TRANSFER_DATA_LAYOUT']
        filename_record_id = _inject_transfer_data(fmp, fmp_transfer_data, transfer_primary_key, logger)
        if not filename_record_id:
            report_transfer_data = False

        # Inject thumb if available
        img_record_id = None
        if thumb_path is not None:
            fmp.layout = CONFIG['FMP_IMAGES_LAYOUT']
            img_record_id = _inject_image(fmp, fmp_thumb_data, logger)

        # Run process img script
        if img_record_id is not None:
            img_primary_key = _get_image_primary_key(fmp, img_record_id, logger)
            if img_primary_key is not None:
                script_res = _run_process_image_script(fmp, img_primary_key, logger)
        else:
            report_img = False

        logger.info(f'Completed event processing {event}')

        do_not_report_msg = 'There was an error injecting this data. Please see error emails for details.'
        version_report = fmp_version if report_version else do_not_report_msg
        transfer_log_report = fmp_transfer_log if report_transfer_log else do_not_report_msg
        transfer_data_report = fmp_transfer_data if report_transfer_data else do_not_report_msg
        img_report = fmp_thumb_data if report_img else do_not_report_msg

        _send_success_email(version_report, transfer_log_report, transfer_data_report, img_report)


def _send_success_email(version_data, fmp_transfer_log, fmp_transfer_data, thumb_data):
    subject = f'[DISTANT_API] Successful External Vendor data injection at {datetime.datetime.now()}'
    content = 'Shotgun data successfully injected into FileMaker. Please see below for details.\n\n' \
              '<hr>' \
              f'<h3>VERSION DATA</h3>\n{pformat(version_data)}\n\n' \
              f'<h3>TRANSFER LOG DATA</h3>\n{pformat(fmp_transfer_log)}\n\n' \
              f'<h3>TRANSFER FILES DATA</h3>\n{pformat(fmp_transfer_data)}\n\n' \
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


def _run_process_image_script(fmp, img_primary_key, logger, tries=3):
    script_res = None
    for i in range(tries):
        try:
            script_res = fmp.perform_script(
                name=CONFIG['FMP_PROCESS_IMAGE_SCRIPT'],
                param=img_primary_key
            )
        except BadJSON as e:
            if i <= tries - 1:
                time.sleep(0.5)
                continue
            else:
                logger.error(
                    f'Error running process image script for image {img_primary_key}  (response {e._response})',
                    exc_info=True)
        except Exception:
            logger.error(f'Error running process image script for image {img_primary_key}', exc_info=True)
            break
        else:
            break
    return script_res


def _get_image_primary_key(fmp, img_record_id, logger, tries=3):
    img_primary_key = None
    for i in range(tries):
        try:
            img_record = fmp.get_record(img_record_id)
            img_primary_key = img_record.PrimaryKey
        except BadJSON as e:
            if i <= tries - 1:
                time.sleep(0.5)
                continue
            else:
                logger.error(
                    f'Error running process image script for image {img_primary_key}  (response {e._response})',
                    exc_info=True)
        except Exception:
            logger.error(f'Error running process image script for image {img_primary_key}', exc_info=True)
            break
        else:
            break
    return img_primary_key


def _inject_image(fmp, fmp_thumb_data, logger, tries=3):
    img_record_id = None
    for i in range(tries):
        try:
            thumb_file = open(fmp_thumb_data.get('Path'), 'rb')
            img_record_id = fmp.create_record(fmp_thumb_data)
            img_did_upload = fmp.upload_container(img_record_id, field_name='Image', file_=thumb_file)
            thumb_file.close()
        except BadJSON as e:
            if i <= tries - 1:
                time.sleep(0.5)
                continue
            else:
                logger.error(f'Error injecting thumbnail record: {fmp_thumb_data} (response {e._response})',
                             exc_info=True)
        except Exception:
            logger.error(f'Error injecting thumbnail record: {fmp_thumb_data}', exc_info=True)
            break
        else:
            break
    return img_record_id


def _inject_transfer_data(fmp, fmp_transfer_data, transfer_primary_key, logger, tries=3):
    filename_record_id = None
    for i in range(tries):
        try:
            fmp_transfer_data['Foriegnkey'] = transfer_primary_key
            filename_record_id = fmp.create_record(fmp_transfer_data)
        except BadJSON as e:
            if i <= tries - 1:
                time.sleep(0.5)
                continue
            else:
                logger.error(f'Error creating transfer data record. (response {e._response})', exc_info=True)
        except Exception:
            logger.error('Error creating transfer data record.', exc_info=True)
    return filename_record_id


def _get_transfer_log_primary_key(fmp, transfer_record_id, fmp_transfer_log, logger, tries=3):
    transfer_primary_key = None
    for i in range(tries):
        try:
            transfer_record_data = fmp.get_record(transfer_record_id)
            transfer_primary_key = transfer_record_data.PrimaryKey
        except BadJSON as e:
            if i <= tries - 1:
                time.sleep(0.5)
                continue
            else:
                logger.error(f'Error creating transfer log record: {fmp_transfer_log}  (response {e._response})',
                             exc_info=True)
        except Exception:
            logger.error(f'Error creating transfer log record: {fmp_transfer_log}', exc_info=True)
            break
        else:
            break
    return transfer_primary_key


def _inject_transfer_log(fmp, fmp_transfer_log, logger, tries=3):
    transfer_record_id = None
    for i in range(tries):
        try:
            transfer_record_id = fmp.create_record(fmp_transfer_log)
        except BadJSON as e:
            if i <= tries - 1:
                time.sleep(0.5)
                continue
            else:
                logger.error(f'Error creating transfer log record: {fmp_transfer_log}  (response {e._response})',
                             exc_info=True)
        except Exception:
            logger.error(f'Error creating transfer log record: {fmp_transfer_log}', exc_info=True)
            break
        else:
            break
    return transfer_record_id


def _find_transfer_log(fmp, fmp_transfer_log, logger, tries=3):
    transfer_log_records = None
    for i in range(tries):
        try:
            transfer_log_records = fmp.find([fmp_transfer_log])
        except BadJSON as e:
            if i <= tries - 1:
                time.sleep(0.5)
                continue
            else:
                logger.error(f'Error finding transfer log record. (response {e._response})', exc_info=True)
        except Exception:
            if fmp.last_error == 401:  # no records were found
                break
            else:
                logger.error('Error finding transfer log record.', exc_info=True)
                break
        else:
            break
    return transfer_log_records


def _inject_version(fmp, fmp_version, logger, tries=3):
    version_record_id = None
    for i in range(tries):
        try:
            version_record_id = fmp.create_record(fmp_version)
        except BadJSON as e:
            if i <= tries - 1:
                time.sleep(0.5)
                continue
            else:
                logger.error(f'Error creating version record. (response {e._response})', exc_info=True)
        except Exception:
            logger.error('Error creating version record.', exc_info=True)
            break
        else:
            break
    return version_record_id


def _find_fmp_version(fmp, version_name, logger, tries=3):
    version_records = None
    for i in range(tries):
        try:
            version_query = {'Filename': version_name}
            version_records = fmp.find([version_query])
        except BadJSON as e:
            if i <= tries - 1:
                time.sleep(0.5)
                continue
            else:
                logger.error(f'Error finding version records. (response {e._response})', exc_info=True)
        except Exception:
            if fmp.last_error == 401:  # no records were found
                break
            else:
                logger.error('Error finding version records.', exc_info=True)
                break
        else:
            break
    return version_records


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


# TODO: Add 'subStatus' to injection
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


# TODO: Add 'subStatus' to injection - need alex to add
def _build_version_dict(published_file, version_name_fmt):
    version_dict = {
        'VFXID': _get_vfx_entity_code(published_file),
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
