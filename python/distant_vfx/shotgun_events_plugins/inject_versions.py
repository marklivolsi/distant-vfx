from datetime import datetime
import os
import time

from ..filemaker import FMCloudInstance
from ..video import VideoProcessor

SG_SCRIPT_NAME = os.environ['SG_VERSION_INJECT_NAME']
SG_SCRIPT_KEY = os.environ['SG_VERSION_INJECT_KEY']

FMP_URL = os.environ['FMP_URL']
FMP_USERNAME = os.environ['FMP_USERNAME']
FMP_PASSWORD = os.environ['FMP_PASSWORD']
FMP_VFXDB = os.environ['FMP_VFXDB']
FMP_ADMINDB = os.environ['FMP_ADMINDB']
FMP_IMAGEDB = os.environ['FMP_IMAGEDB']
FMP_USERPOOL = os.environ['FMP_USERPOOL']
FMP_CLIENT = os.environ['FMP_CLIENT']
FMP_VERSIONS_LAYOUT = 'api_Versions_form'
FMP_TRANSFER_LOG_LAYOUT = 'api_Transfers_form'
FMP_TRANSFER_DATA_LAYOUT = 'api_TransfersData_form'
FMP_IMAGES_LAYOUT = 'api_Images_form'

THUMBS_BASE_PATH = '/mnt/Projects/dst/post/thumbs'


def registerCallbacks(reg):
    matchEvents = {
        'Shotgun_Version_Change': ['*'],
    }
    reg.registerCallback(SG_SCRIPT_NAME,
                         SG_SCRIPT_KEY,
                         inject_versions,
                         matchEvents,
                         None)


def inject_versions(sg, logger, event, args):

    event_description = event.get('description')
    event_id = event.get('id')

    # Determine if this is an in house or external vendor version to inject, or not at all
    vendor = _get_vendor(event_description)
    if vendor is None:
        return
    logger.info('Valid injection candidate found for vendor type {vendor} in Event #{id}'
                .format(vendor=vendor, id=event_id))

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
        logger.error('Could not find matching {entity_type} entity with ID {entity_id}. Cannot inject.'
                     .format(entity_type=entity_type, entity_id=entity_id))
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
        'Filename': code,  # TODO: We might want to use the basename of the movie file instead here
        'DeliveryPackage': package,
        'Status': status,
        'DeliveryNote': description,
        'ShotgunID': entity_id,
        'ShotgunPublishedFiles': published_files,
        'ShotgunPathToMovie': path_to_movie
    }

    # Prep transfer log data for injection to filemaker
    package_dict = {
        'package': package,
        'path': ''  # TODO: Add path to package for mrx packages - what sg field will this be?
    }
    filename_dict = {
        'Filename': os.path.basename(path_to_movie),
        'Path': path_to_movie
    }

    # Generate a thumbnail
    thumb_filename, thumb_path = None, None
    try:
        thumb_filename, thumb_path = _get_thumbnail(path_to_movie)
    except Exception as e:
        logger.error('Could not generate thumbnail for version {code}. (error: {exc})'
                     .format(code=code, exc=e))

    # Inject new version data into vfx db
    with FMCloudInstance(host_url=FMP_URL,
                         username=FMP_USERNAME,
                         password=FMP_PASSWORD,
                         database=FMP_VFXDB,
                         user_pool_id=FMP_USERPOOL,
                         client_id=FMP_CLIENT) as fmp:

        record_id = fmp.new_record(FMP_VERSIONS_LAYOUT, version_dict)
        if not record_id:
            logger.error('Error injecting version data (data: {data})'
                         .format(data=version_dict))
            return

        # TODO: Inject version thumbnail

    # Inject transfer log data to admin db
    with FMCloudInstance(host_url=FMP_URL,
                         username=FMP_USERNAME,
                         password=FMP_PASSWORD,
                         database=FMP_ADMINDB,
                         user_pool_id=FMP_USERPOOL,
                         client_id=FMP_CLIENT) as fmp:

        # First check to see if package exists so we don't create multiple of the same package
        records = fmp.find_records(FMP_TRANSFER_LOG_LAYOUT, query=[package_dict])
        logger.info('Searching for existing package records (data: {data})'
                    .format(data=package_dict))

        if not records:
            # Create a new transfer log record
            record_id = fmp.new_record(FMP_TRANSFER_LOG_LAYOUT, package_dict)
            record_data = fmp.get_record(FMP_TRANSFER_LOG_LAYOUT, record_id=record_id)
            primary_key = record_data.get('fieldData').get('PrimaryKey')
            logger.info('Created new transfer record for {package} (record id {id})'
                        .format(package=package, id=record_id))

        else:
            primary_key = records[0].get('fieldData').get('PrimaryKey')
            logger.info('Transfer record for {package} already exists.'
                        .format(package=package))

        # Create transfer data records
        filename_dict['Foriegnkey'] = primary_key  # Foriegnkey is intentionally misspelled to match db field name
        filename_record_id = fmp.new_record(FMP_TRANSFER_DATA_LAYOUT, filename_dict)

        if filename_record_id:
            logger.info('Created new transfer data record for version {version} (record id {id}).'
                        .format(version=code, id=filename_record_id))
        else:
            logger.error('Error creating transfer data record for version {version}.'
                         .format(version=code))

    if thumb_path is None:
        return

    thumb_data = {
        'Filename': thumb_filename,
        'Path': thumb_path
    }

    # If we have a thumbnail, inject to image db
    with FMCloudInstance(host_url=FMP_URL,
                         username=FMP_USERNAME,
                         password=FMP_PASSWORD,
                         database=FMP_IMAGEDB,
                         user_pool_id=FMP_USERPOOL,
                         client_id=FMP_CLIENT) as fmp:

        record_id = fmp.new_record(FMP_IMAGES_LAYOUT, thumb_data)

        if not record_id:
            logger.error('Error injecting thumbnail (data: {data})'
                         .format(data=version_dict))
            return

        response = fmp.upload_container_data(FMP_IMAGES_LAYOUT, record_id, 'Image', thumb_path)

        # TODO: Kick off FMP script to generate sub-images


def _get_thumbnail(path_to_movie):

    # Get the thumbnail output path
    mov_filename = os.path.basename(path_to_movie)
    mov_basename = os.path.splitext(mov_filename)[0]
    thumb_filename = '0000 ' + mov_basename + '.jpg'  # Naming structure necessary to parse vfx id with current setup
    thumb_dest = os.path.join(THUMBS_BASE_PATH, thumb_filename)

    # Generate thumbnail
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
