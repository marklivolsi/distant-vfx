import os
from ..config import Config
from ..filemaker import FMCloudInstance


def main(versions_dict_list, filename_dict_list, package_dict):
    """
    Inject new vendor submission data into FileMaker Cloud.

    :param versions_dict_list: A list of version dicts containing version data. Format each dict like:
                               version_dict = { 'Filename': <filename>,
                                                'DeliveryPackage': <package>,
                                                'Status': <subStatus>,
                                                'DeliveryNote': <subNote> }

    :param filename_dict_list: A list of filename dicts containing filename data. Format each dict like:
                               filename_dict = { 'Filename': <filename> }
    :param package_dict: A single dictionary describing the package data. Format like:
                         package_dict = { 'package': <package_name>,
                                          'path': <package_path> }
    :return: None.
    """

    # TODO: Replace with os.environ variables
    # config = Config()
    # config_did_load = config.load_config()
    # data = config.data
    # url = data['fmp_data_api']['base_url']
    # username = data['fmp_data_api']['username']
    # password = data['fmp_data_api']['password']
    # user_pool_id = data['fmp_data_api']['cognito_userpool_id']
    # client_id = data['fmp_data_api']['cognito_client_id']

    url = os.environ['FMP_URL']
    username = os.environ['FMP_USERNAME']
    password = os.environ['FMP_PASSWORD']
    user_pool_id = os.environ['FMP_USERPOOL']
    client_id = os.environ['FMP_CLIENT']

    # Inject new versions from vendor csv doc
    if versions_dict_list:
        # database = data['fmp_data_api']['databases']['vfx']
        database = os.environ['FMP_VFXDB']
        with FMCloudInstance(url, username, password, database, user_pool_id, client_id) as fmp:
            versions_layout = 'api_Versions_form'
            for version_dict in versions_dict_list:
                version_record_id = fmp.new_record(versions_layout, version_dict)

    # Inject filename and package records
    if filename_dict_list and package_dict:
        # database = data['fmp_data_api']['databases']['admin']
        database = os.environ['FMP_ADMINDB']
        with FMCloudInstance(url, username, password, database, user_pool_id, client_id) as fmp:

            transfers_layout = 'api_Transfers_form'
            pkg_record_id = fmp.new_record(transfers_layout, package_dict)

            # Link the package record to each filename record via package record PrimaryKey
            pkg_data = fmp.get_record(transfers_layout, record_id=pkg_record_id)
            pkg_primary_key = pkg_data.get('fieldData').get('PrimaryKey')

            transfers_data_layout = 'api_TransfersData_form'
            for filename_dict in filename_dict_list:
                if pkg_primary_key is not None:
                    filename_dict['Foriegnkey'] = pkg_primary_key
                filename_record_id = fmp.new_record(transfers_data_layout, filename_dict)
