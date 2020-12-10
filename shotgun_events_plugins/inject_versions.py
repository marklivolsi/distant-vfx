from datetime import datetime
import os
import time
import yagmail
from fmrest import CloudServer

from distant_vfx.video import VideoProcessor
from distant_vfx.config import Config


def _load_config(config_path):
    config = Config()
    config_did_load = config.load_config(config_path)
    if config_did_load:
        return config.data
    return None


CONFIG = _load_config('/mnt/Plugins/python3.6/shotgun_events_plugins/shotgun_events_config.yml')


# Shotgun constants
SG_SCRIPT_NAME = CONFIG['SG_VERSION_INJECT_NAME']
SG_SCRIPT_KEY = CONFIG['SG_VERSION_INJECT_KEY']

# FileMaker constants
FMP_URL = CONFIG['FMP_URL']
FMP_USERNAME = CONFIG['FMP_USERNAME']
FMP_PASSWORD = CONFIG['FMP_PASSWORD']
FMP_ADMINDB = CONFIG['FMP_ADMINDB']
FMP_USERPOOL = CONFIG['FMP_USERPOOL']
FMP_CLIENT = CONFIG['FMP_CLIENT']
FMP_VERSIONS_LAYOUT = 'api_Versions_form'
FMP_TRANSFER_LOG_LAYOUT = 'api_Transfers_form'
FMP_TRANSFER_DATA_LAYOUT = 'api_TransfersData_form'
FMP_IMAGES_LAYOUT = 'api_Images_form'
FMP_PROCESS_IMAGE_SCRIPT = 'process_image_set'

# Filesystem constants
THUMBS_BASE_PATH = '/mnt/Projects/dst/post/thumbs'

# Email constants
EMAIL_USER = CONFIG['EMAIL_USERNAME']
EMAIL_PASSWORD = CONFIG['EMAIL_PASSWORD']
EMAIL_RECIPIENTS = CONFIG['EMAIL_RECIPIENTS'].split(',')
EMAIL_EVENTS = []


def registerCallbacks(reg):
    matchEvents = {
        'Shotgun_Version_Change': ['*'],  # look for any version change event
    }
    reg.registerCallback(SG_SCRIPT_NAME,
                         SG_SCRIPT_KEY,
                         inject_versions,
                         matchEvents,
                         None)


def inject_versions(sg, logger, event, args):

    # event_description = event.get('description')
    event_id = event.get('id')
    event_entity = sg.find_one('EventLogEntry', [['id', 'is', event_id]], ['description'])
    event_description = event_entity.get('description')

    # Determine if this is an in house or external vendor version to inject, or not at all
    vendor = _get_vendor(event_description)
    if vendor is None:
        return

    msg = 'Valid injection candidate found for vendor type {vendor} in Event #{id}'.format(vendor=vendor, id=event_id)
    EMAIL_EVENTS.append(msg)
    logger.info(msg)

    # Wait to make sure the entity is fully created and updated
    time.sleep(1)

    # Extract entity data for the event in question
    entity_id = event.get('meta').get('entity_id')
    entity_type = event.get('meta').get('entity_type')

    # Find the version entity in SG and return relevant details
    entity = sg.find_one(entity_type, [['id', 'is', entity_id]], ['code',
                                                                  'description',
                                                                  'published_files',
                                                                  'sg_path_to_movie',
                                                                  'sg_status_list'])  # TODO: get mrx pkg name

    # If the entity can't be found, return.
    if entity is None:
        msg = 'Could not find matching {entity_type} entity with ID {entity_id}. Cannot inject.'.format(
            entity_type=entity_type, entity_id=entity_id)
        logger.error(msg)
        EMAIL_EVENTS.append(msg)
        _send_email()
        return

    # Extract entity data
    description = entity.get('description', '')
    code = entity.get('code', '')
    published_files = entity.get('published_files', '')
    path_to_movie = entity.get('sg_path_to_movie', '')
    status = entity.get('sg_status_list', '')

    # TODO: Parse exr path.

    # Get the package name (varies between ih and ext vendors)
    if vendor == 'ext':
        package = ''  # TODO: Get mrx pkg name - what sg field will this live in?
    else:
        package = 'dst_ih_' + datetime.now().strftime('%Y%m%d')

    # Prep version data for injection to filemaker
    version_dict = {
        'Filename': code if code else '',  # TODO: We might want to use the basename of the movie file instead here
        'DeliveryPackage': package if package else '',
        'Status': status if status else '',
        'DeliveryNote': description if description else '',
        'ShotgunID': entity_id if entity else '',
        'ShotgunPublishedFiles': str(published_files) if published_files else '',  # TODO : fix this
        'ShotgunPathToMovie': path_to_movie if path_to_movie else ''
    }

    # Prep transfer log data for injection to filemaker
    package_dict = {
        'package': package if package else 'tmp_{}'.format(datetime.now().strftime('%Y%m%d')),
        'path': ''  # TODO: Add path to package for mrx packages - what sg field will this be?
    }
    filename_dict = {
        'Filename': os.path.basename(path_to_movie) if path_to_movie else '',
        'Path': path_to_movie if path_to_movie else ''
    }

    # Generate a thumbnail
    thumb_filename, thumb_path = None, None
    try:
        thumb_filename, thumb_path = _get_thumbnail(path_to_movie)
    except Exception as e:
        msg = 'Could not generate thumbnail for version {code}. (error: {exc})'.format(code=code, exc=e)
        logger.error(msg)
        EMAIL_EVENTS.append(msg)

    # Connect to FMP admin DB and inject data
    with CloudServer(url=FMP_URL,
                     user=FMP_USERNAME,
                     password=FMP_PASSWORD,
                     database=FMP_ADMINDB,
                     layout=FMP_VERSIONS_LAYOUT) as fmp:

        fmp.login()

        # Inject new version into versions table
        try:
            version_record_id = fmp.create_record(version_dict)
            msg = 'Version created (record id: {id}, data: {data})'.format(id=version_record_id, data=version_dict)
            logger.info(msg)
            EMAIL_EVENTS.append(msg)
        except Exception as e:
            msg = 'Error injecting version data (data: {data}, error: {error})'.format(data=version_dict, error=e)
            logger.error(msg)
            EMAIL_EVENTS.append(msg)
            # If we fail creating version, let users know and return
            _send_email()
            return

        # Inject transfer log data to transfer log table
        fmp.layout = FMP_TRANSFER_LOG_LAYOUT

        # First check to see if package exists so we don't create multiple of the same package
        try:
            records = fmp.find([package_dict])
        except Exception as e:
            if fmp.last_error == 401:  # no records were found
                records = None
            else:
                msg = 'Error searching for transfer log records (query {query}, error {error}'.format(query=package_dict,
                                                                                                      error=e)
                logger.error(msg)
                EMAIL_EVENTS.append(msg)
                _send_email()
                return

        # If the transfer log record doesn't exist, create it
        if not records:
            try:
                transfer_record_id = fmp.create_record(package_dict)
                transfer_record_data = fmp.get_record(transfer_record_id)
                transfer_primary_key = transfer_record_data.PrimaryKey
                msg = 'Created new transfer record for {package} (record id {id})'.format(package=package,
                                                                                          id=transfer_record_id)
                logger.info(msg)
                EMAIL_EVENTS.append(msg)
            except Exception as e:
                msg = 'Error creating transfer log record for {package} (error {error})'.format(package=package,
                                                                                                error=e)
                logger.error(msg)
                EMAIL_EVENTS.append(msg)

        else:
            transfer_primary_key = records[0].PrimaryKey

        # Create transfer data records
        fmp.layout = FMP_TRANSFER_DATA_LAYOUT
        filename_dict['Foriegnkey'] = transfer_primary_key  # Foriegnkey is intentionally misspelled to match db field

        try:
            filename_record_id = fmp.create_record(filename_dict)
            msg = 'Created new transfer data record (record id {id}, data {data})'.format(id=filename_record_id,
                                                                                          data=filename_dict)
            logger.info(msg)
            EMAIL_EVENTS.append(msg)
        except Exception as e:
            msg = 'Error creating new transfer data record (data {data}, error {error})'.format(data=filename_dict,
                                                                                                error=e)
            logger.error(msg)
            EMAIL_EVENTS.append(msg)

        # If there is no thumbnail, we're done
        if thumb_path is None:
            _send_email()
            return

        # If we do have a thumb, inject to image layout
        fmp.layout = FMP_IMAGES_LAYOUT

        thumb_data = {
            'Filename': thumb_filename if thumb_filename else '',
            'Path': thumb_path
        }

        try:
            thumb_file = open(thumb_path, 'rb')
            img_record_id = fmp.create_record(thumb_data)
            img_did_upload = fmp.upload_container(img_record_id, field_name='Image', file_=thumb_file)
            thumb_file.close()
            img_record = fmp.get_record(img_record_id)
            msg = 'Created new image record (record id {id}, filename {name})'.format(id=img_record_id,
                                                                                      name=thumb_data['Filename'])
            logger.info(msg)
            EMAIL_EVENTS.append(msg)
        except Exception as e:
            msg = 'Error creating new image record (filename {name}, error {error})'.format(name=thumb_data['Filename'],
                                                                                            error=e)
            logger.error(e)
            EMAIL_EVENTS.append(msg)
            _send_email()
            return

        # If we successfully create an image record, kick off a script to process the images
        try:
            img_primary_key = img_record.PrimaryKey
            script_res = fmp.perform_script(FMP_PROCESS_IMAGE_SCRIPT, param=img_primary_key)
            msg = 'Launched process image script for image record {key}'.format(key=img_primary_key)
            EMAIL_EVENTS.append(msg)
            logger.info(msg)
        except Exception as e:
            msg = 'Error launching process image script for image record {name} (error {error})'.format(
                name=thumb_data['Filename'], error=e)
            logger.error(msg)
            EMAIL_EVENTS.append(msg)
        finally:
            _send_email()


def _send_email():
    subject, contents = _format_email()
    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASSWORD)
    yag.send(EMAIL_RECIPIENTS, subject=subject, contents=contents)


def _format_email():
    dt = datetime.now()
    subject = '[DISTANT_API] {} events processed by Shotgun Events at {}'.format(len(EMAIL_EVENTS), dt)
    contents = ''
    for index, event in enumerate(EMAIL_EVENTS):
        line = '[{}]'.format(index) + ': ' + event + '\n\n'
        contents += line
    return subject, contents


def _get_thumbnail(path_to_movie):

    # Get the thumbnail output path
    mov_filename = os.path.basename(path_to_movie)
    mov_split = os.path.splitext(mov_filename)
    mov_basename, mov_ext = mov_split[0], mov_split[1]
    thumb_filename = '0000 ' + mov_basename + '.jpg'  # Naming structure necessary to parse vfx id with current setup
    thumb_dest = os.path.join(THUMBS_BASE_PATH, thumb_filename)

    # Generate thumbnail
    if not os.path.exists(thumb_dest) and mov_ext in ['.mov', '.mp4']:
        video_processor = VideoProcessor()
        video_processor.generate_thumbnail(path_to_movie, thumb_dest)
    return thumb_filename, thumb_dest


def _get_vendor(event_description):
    ih_phrase = 'to "ihapp" on Version'
    ext_phrase = 'to "extapp" on Version'
    if ih_phrase in event_description:
        return 'ih'
    elif ext_phrase in event_description:
        return 'ext'
    return None
