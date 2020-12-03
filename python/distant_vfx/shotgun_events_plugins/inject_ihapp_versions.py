from datetime import datetime
import os
import time

from ..filemaker import FMCloudInstance

# TODO: Get from env variable
SCRIPT_NAME = ''
SCRIPT_KEY = ''


def registerCallbacks(reg):
    matchEvents = {
        'Shotgun_Version_Change': ['*'],
    }
    reg.registerCallback(SCRIPT_NAME,
                         SCRIPT_KEY,
                         inject_ihapp_versions_to_filemaker,
                         matchEvents,
                         None)


def inject_ihapp_versions_to_filemaker(sg, logger, event, args):

    match_phrase = 'to "ihapp" on Version'
    description = event.get('description')

    if match_phrase in description:

        # Wait for any additional changes
        time.sleep(1)
        entity_id = event.get('meta').get('entity_id')
        entity_type = event.get('meta').get('entity_type')

        # Get the version code
        entity = sg.find_one(entity_type, [['id', 'is', entity_id]], ['code',
                                                                      'description',
                                                                      'published_files',
                                                                      'sg_uploaded_movie',
                                                                      'sg_path_to_movie'])

        if entity is None:
            logger.error('Could not find matching {entity_type} entity with ID {entity_id}'
                         .format(entity_type=entity_type, entity_id=entity_id))
            return

        # Extract entity data
        description = entity.get('description', '')
        code = entity.get('code', '')
        published_files = entity.get('published_files', '')
        uploaded_movie = entity.get('sg_uploaded_movie', '')
        path_to_movie = entity.get('sg_path_to_movie', '')

        # Grab filemaker env vars
        url = os.environ['FMP_URL']
        username = os.environ['FMP_USERNAME']
        password = os.environ['FMP_PASSWORD']
        database = os.environ['FMP_VFXDB']
        user_pool_id = os.environ['FMP_USERPOOL']
        client_id = os.environ['FMP_CLIENT']

        # Prep version data for injection to filemaker
        versions_layout = 'api_Versions_form'
        package = 'dst_inh_' + datetime.now().strftime('%Y%m%d')  # TODO: How do we want these IH pkgs named?
        version_dict = {
            'Filename': code,
            'DeliveryPackage': package,
            'Status': 'ihapp',
            'DeliveryNote': description,
            'ShotgunID': entity_id,
            'ShotgunPublishedFiles': published_files,
            'ShotgunUploadedMovie': uploaded_movie,
            'ShotgunPathToMovie': path_to_movie
        }

        # Inject new version data
        with FMCloudInstance(url, username, password, database, user_pool_id, client_id) as fmp:

            new_record_id = fmp.new_record(versions_layout, version_dict)
            if new_record_id is None:
                pass  # Flag this

        # Prep transfer log data for injection to filemaker
        database = os.environ['FMP_ADMINDB']
        transfers_layout = 'api_Transfers_form'
        transfers_data_layout = 'api_TransfersData_form'
        package_dict = {
            'package': package,
        }
        filename_dict = {
            'Filename': uploaded_movie,
            'Path': path_to_movie
        }

        with FMCloudInstance(url, username, password, database, user_pool_id, client_id) as fmp:

            # First check to see if package exists so we don't create multiple of the same package
            records = fmp.find_records(transfers_layout, query=[package_dict])

            if not records:
                # Create a new transfer log record
                record_id = fmp.new_record(transfers_layout, package_dict)
                record_data = fmp.get_record(transfers_layout, record_id=record_id)
                primary_key = record_data.get('fieldData').get('PrimaryKey')

            else:
                primary_key = records[0].get('fieldData').get('PrimaryKey')

            # Create transfer data records
            filename_dict['Foriegnkey'] = primary_key
            filename_record_id = fmp.new_record(transfers_data_layout, filename_dict)




