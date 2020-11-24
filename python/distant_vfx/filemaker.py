import logging
import json
import requests
import pycognito


LOG = logging.getLogger(__name__)


class FMCloudInstance:

    def __init__(self, host_url, username, password, database, user_pool_id, client_id, api_version='vLatest'):
        """
        Create an new FMCloudInstance object. Uses the specified params to connect to a FileMaker Cloud hosted DB.
        This API is based off of the FileMaker 19 Data API Guide, see here for more information:
        https://help.claris.com/en/data-api-guide/

        :param host_url: The base url of the FileMaker Cloud server.
        :param username: The Claris ID username used to sign in to FileMaker Cloud.
        :param password: The Claris ID password used to sign in to FileMaker Cloud.
        :param database: The name of the database to connect to.
        :param user_pool_id: The Userpool_ID value used to retrieve the FMID token required to authenticate with
                             FileMaker Cloud via Amazon Cognito. This can be obtained per instructions here:
                             https://help.claris.com/en/customer-console-help/content/create-fmid-token.html
        :param client_id: The Client_ID value used to retrieve the FMID token required to authenticate with
                             FileMaker Cloud via Amazon Cognito. This can be obtained per instructions here:
                             https://help.claris.com/en/customer-console-help/content/create-fmid-token.html
        :param api_version: The FileMaker Cloud Data API version to use for API calls. This is set to latest by default.
        """
        self.host_url = host_url
        self.username = username
        self.password = password
        self.database = database
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.api_version = api_version
        self._fmid_token = None
        self._refresh_token = None
        self._bearer_token = None

    def __enter__(self):
        # Automatically log in with context manager, i.e. with FMCloudInstance(...) as fm:
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Automatically log out when we leave the context
        self.logout()
        if exc_type:
            LOG.error(f'{exc_type}: {exc_val}')

    def login(self):
        """
        Establish connection to the specified FMP Cloud DB via the sessions api endpoint.
        :return: None.
        """

        # Get the FMID token from Amazon Cognito.
        self._get_fmid_token()

        # Set the url and headers and perform the login api request.
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'FMID {self._fmid_token}'
        }
        url = self.host_url + f'/fmi/data/{self.api_version}/databases/{self.database}/sessions'
        response = requests.post(url, headers=headers, data='{}')

        # Using raise_for_status here since if login fails, we can't do anything else.
        response.raise_for_status()

        # Extract bearer token from json response (used for all subsequent API calls).
        response_json = response.json()
        self._bearer_token = response_json.get('response').get('token')

    def logout(self):
        """
        Log out of the current DB session. Called automatically when leaving context if using context manager.
        :return: None.
        """

        # Set headers and url and perform the logout api request.
        headers = {'Content-Type': 'application/json'}
        url = self.host_url + f'/fmi/data/{self.api_version}/databases/{self.database}/sessions/{self._bearer_token}'
        response = requests.delete(url, headers=headers)

        # If the response is valid, reset the bearer token.
        if response.ok:
            self._bearer_token = None
        else:
            pass
            # TODO: Notify user of invalid http response.

    def new_record(self, layout, data):
        """
        Create a new record on the given layout with the provided field names.
        :param layout: The layout on which to create a new record.
        :param data: A dict of field names and values, e.g. { "String Field": "value_1", "Number Field": 99.99,
                     "repetitionField(1)" : "fieldValue"}
        :return: The unique record ID of the newly created record (use to access the record in subsequent calls).
        """

        # Set headers and url for the request.
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self._bearer_token}'
        }
        url = self.host_url + f'/fmi/data/{self.api_version}/databases/{self.database}/layouts/{layout}/records'

        # Convert new record data to JSON.
        request_json = json.dumps({'fieldData': data})

        # Perform the api request.
        response = requests.post(url, headers=headers, data=request_json)

        # If successful, convert the response to json and return the newly created record ID.
        if response.ok:
            response_json = response.json()
            record_id = response_json.get('response').get('recordId')
            return record_id
        else:
            pass
            # TODO: Notify user of invalid http response (this will not throw an error).

    def get_record(self, layout, record_id):
        """
        Get data for a single record based on the provided unique record ID.
        :param layout: The layout to retrieve the record from.
        :param record_id: The unique ID of the record to retrieve.
        :return: A dict containing the field data for the requested record.
        """

        # Set the headers and url for the request.
        headers = {'Authorization': f'Bearer {self._bearer_token}'}
        url = self.host_url + f'/fmi/data/{self.api_version}/databases/{self.database}/layouts/{layout}/records/{record_id}'

        # Perform the api request.
        response = requests.get(url, headers=headers)

        # If successful, convert the response to json and return the record data.
        if response.ok:
            response_json = response.json()
            record = response_json.get('response').get('data')
            return record[0]
        else:
            pass
        # TODO: Notify user of invalid http response.

    def find_records(self, layout, query, sort=None, limit=None):
        """
        Perform a find request matching one or more queries on the given layout.
        :param layout: The name of the layout on which to perform the request.
        :param query: A list of dicts specifying the find parameters, e.g. [{"Group": "=Surgeon"}, {"Field2: "=val2"}]
                      Use "omit": "true" to perform omit requests, e.g. [{"Work State" : "NY", "omit" : "true"}]
        :param sort: A list of dicts specifying the sort parameters, e.g. [{"fieldName": "Work State","sortOrder":
                     "ascend"}, {"fieldName": "First Name", "sortOrder": "ascend"}]
        :param limit: Limit the number of records returned, e.g. a value of 1 will return 1 record.
        :return: List of record dicts matching the find request params.
        """

        # Set the headers and url.
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self._bearer_token}'
        }
        url = self.host_url + f'/fmi/data/{self.api_version}/databases/{self.database}/layouts/{layout}/_find'

        # At minimum, query must be provided.
        data = {'query': query}

        # Add sort or limit params if provided.
        if sort is not None:
            data['sort'] = sort
        if limit is not None:
            data['limit'] = limit

        # Convert request data to json and perform the request.
        request_json = json.dumps(data, default=self._set_default)
        response = requests.post(url, headers=headers, data=request_json)

        # If successful, extract and return the list of record data.
        if response.ok:
            response_json = response.json()
            response_data = response_json.get('response').get('data')
            return response_data
        else:
            pass
            # TODO: Notify user of invalid http response.

    def upload_container_data(self, layout, record_id, field_name, filepath):
        """
        Upload a file to a container field in the specified record.
        :param layout: The layout to access.
        :param record_id: The ID of the record (use get_record method to get the ID).
        :param field_name: The name of the container field to upload to.
        :param filepath: The path of the file to upload.
        :return: The response in JSON format.
        """

        # Set headers and url.
        headers = {
            'Authorization': f'Bearer {self._bearer_token}'
        }
        url = self.host_url + f'/fmi/data/{self.api_version}/databases/{self.database}/layouts/{layout}/records/' \
                              f'{record_id}/containers/{field_name}/1'

        # Open the file in binary mode and set the request dict
        file = open(filepath, 'rb')
        container_data = {'upload': file}

        # Perform the api call and close the open file
        response = requests.post(url, headers=headers, files=container_data)
        file.close()

        if response.ok:
            response_json = response.json()
            return response_json
        else:
            pass

    def _get_fmid_token(self):
        """
        Obtain a FMID token from Amazon Cognito, necessary for authenticating FileMaker Cloud Data API login requests.
        :return: None.
        """
        # Get the FMID token for FMP Cloud login via Amazon Cognito.
        user = pycognito.Cognito(user_pool_id=self.user_pool_id,
                                 client_id=self.client_id,
                                 username=self.username)
        user.authenticate(self.password)
        self._fmid_token = user.id_token
        self._refresh_token = user.refresh_token

    @staticmethod
    def _set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError
