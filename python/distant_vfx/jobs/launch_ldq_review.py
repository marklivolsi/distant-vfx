from ..filemaker import FMCloudInstance


def main():

    # TODO: Access FMP creds with environ variable

    host_url = None
    username = None
    password = None
    database = None
    user_pool_id = None

    from ..config import Config

    config = Config()
    config_did_load = config.load_config()
    data = config.data
    url = data['fmp_data_api']['base_url']
    username = data['fmp_data_api']['username']
    password = data['fmp_data_api']['password']
    database = data['fmp_data_api']['databases']['vfx']
    user_pool_id = data['fmp_data_api']['cognito_userpool_id']
    client_id = data['fmp_data_api']['cognito_client_id']
    layout = 'api_Notes_form'

    with FMCloudInstance(url, username, password, database, user_pool_id, client_id) as fmp:

        review_query = [
            {'Reviews::ReviewType': 'Supervisor'},
            {'Reviews::ReviewStatus': 'Open'}
        ]
        notes_layout = 'api_Notes_form'

        records = fmp.find_records(notes_layout, review_query)

        review_files = []
        for record in records:
            field_data = record.get('fieldData')
            filename = field_data.get('Filename')
            if filename:
                review_files.append(filename)
        print(review_files)
