import logging
from pathlib import Path
import os
import sys
import pandas as pd
from yaml import safe_load, YAMLError
import shotgun_api3
import pycognito
import requests
import json


LOG = logging.getLogger(__name__)


class DistantError(Exception):
    # A custom exception for distant_vfx classes.
    pass


class ALEHandler:

    def __init__(self):
        self.ale_path = None
        self.header_data = None
        self.column_data = None

    @property
    def ale_name(self):
        if self.ale_path is not None:
            return Path(self.ale_path).name

    @property
    def field_delim(self):
        if self.header_data is not None:
            return self.header_data.iloc[0][0]

    @property
    def video_format(self):
        if self.header_data is not None:
            return self.header_data.iloc[1][0]

    @property
    def audio_format(self):
        if self.header_data is not None:
            return self.header_data.iloc[2][0]

    @property
    def fps(self):
        if self.header_data is not None:
            return self.header_data.iloc[3][0]

    def parse_ale(self, ale_path):
        # Parse the header and column data from the ALE file.
        self.ale_path = ale_path
        self._read_header_data()
        self._read_column_data()
        self._drop_data_header_row()
        self._rename_columns()
        self._add_header_data_as_columns()
        self._drop_empty_columns()

    def _read_header_data(self):
        # Reads the ALE header data.
        self.header_data = pd.read_csv(self.ale_path, sep='\t', nrows=4)

    def _read_column_data(self):
        # Reads in the data columns, skipping the header and starting with the 'Name' column.
        print(f'Reading ALE data for {self.ale_path}')
        with open(self.ale_path, 'r') as file:
            position = 0
            current_line = file.readline()
            while not current_line.startswith('Name'):
                position = file.tell()
                current_line = file.readline()
            file.seek(position)
            self.column_data = pd.read_csv(file, sep='\t')

    def _drop_data_header_row(self):
        # Remove the empty 'Data' row
        self.column_data = self.column_data[self.column_data.Name != 'Data']

    def _rename_columns(self):
        # Replace problematic characters in the headers with _
        forbidden_chars = '",+-*/^&=≠><()[]{};:$ '
        translate_table = str.maketrans(forbidden_chars, '_' * len(forbidden_chars))
        self.column_data.rename(columns=lambda x: x.translate(translate_table), inplace=True)

    def _add_header_data_as_columns(self):
        # Append the header data as columns to the dataframe.
        self.column_data['field_delim'] = self.field_delim
        self.column_data['video_format'] = self.video_format
        self.column_data['audio_format'] = self.audio_format
        self.column_data['fps'] = self.fps
        self.column_data['ale_name'] = self.ale_name

    def _drop_empty_columns(self):
        # Drop any completely empty columns.
        self.column_data = self.column_data.dropna(how='all', axis=1)


class EDLHandler:

    def __init__(self):
        pass

    @staticmethod
    def loc_to_lower(edl_path):
        # Read lines in edl.
        with open(edl_path, 'r') as file:
            lines = file.readlines()

        # If a *LOC line, replace everything after *LOC with lowercase.
        for index, line in enumerate(lines):
            identifier = '*LOC:'
            if line.startswith(identifier):
                length = len(identifier)
                str_lower = line[length:].lower()
                lines[index] = identifier + str_lower

        # Overwrite the original file with lowercase *LOC lines.
        with open(edl_path, 'w') as file:
            file.writelines(lines)


class Config:

    def __init__(self):
        self.config_path = None
        self.data = None

    def load_config(self, config_path='./config.yml'):
        # Load in sensitive data via a .yml config file.
        with open(config_path, 'r') as file:
            try:
                self.config_path = config_path
                self.data = safe_load(file)
                return True
            except YAMLError as e:
                LOG.error(e)
                return False


class ShotgunInstance:

    def __init__(self, base_url, script_name, api_key, project_id):
        self.base_url = base_url
        self.script_name = script_name
        self.api_key = api_key
        self.project_id = project_id
        self.session = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        if exc_type:
            LOG.error(f'{exc_type}: {exc_val}')

    def connect(self):
        """
        Connect to the Shotgun instance.
        :return: None.
        """
        self._connect_via_script(self.script_name, self.api_key)

    def _connect_via_script(self, script_name, api_key):
        """
        Connects to Shotgun API via script-based authentication. Session can then be accessed via self.session
        :param script_name: The name of the script to use for authentication.
        :param api_key: The API key associated with the named script.
        :return: None.
        """
        session = shotgun_api3.Shotgun(self.base_url,
                                       script_name=script_name,
                                       api_key=api_key,
                                       # Manually pass cert path to avoid FileNotFoundError.
                                       ca_certs=ShotgunInstance._get_cert_path())
        self.session = session

    def create_shot(self, shot_code, sequence_id, status='wtg', other_data=None):
        """
        Create a new shot if it does not already exist in the Shotgun database. At minimum, a shot code, status, and
        sequence id must be provided. Additional data (e.g. shot description) can be provided as a dictionary in the
        other_data parameter.
        :param shot_code: The VFX ID of the shot to create.
        :param sequence_id: The sequence id for the sequence to which the shot belongs.
        :param status: The status of the shot. Should follow Shotgun standards, e.g. 'ip' for in progress, 'wtg' for
                       waiting to start, etc. Defaults to waiting to start.
        :param other_data: An optional dict of additional data in the format {'fieldName': 'value'}, e.g.
                           {'description': 'this is a shot description'}
        :return: a dict of
        """

        # Set the mandatory data for new shot creation. At minimum, a shot code and sequence ID must be provided.
        data = {
            'project': {'type': 'Project', 'id': self.project_id},
            'sg_sequence': {'type': 'Sequence', 'id': sequence_id},
            'code': shot_code,
            'sg_status_list': status,
        }

        # If additional data is provided, merge into the original data dict. Note this will override any duplicate keys.
        if other_data is not None:
            data = {**data, **other_data}

        # Create the shot and return the new shot data.
        new_shot = self.session.create('Shot', data)
        if new_shot is None:
            LOG.error(f'Create new shot {shot_code} failed.')
        return new_shot

    def find_shot(self, shot_code):
        """
        Find details for a single shot based on the shot code.
        :param shot_code: The VFX ID for the shot in question.
        :return: A dict of data for the shot (or None if no matching shot is found). Returned fields are specified in
                 the 'fields' variable below.
        """

        # Set the filters and fields to use in the find request.
        filters = [
            ['project', 'is', {'type': 'Project', 'id': self.project_id}],
            ['code', 'is', shot_code]
        ]
        fields = ['code', 'id', 'sg_status_list', 'description']

        # Look for a matching shot. Will only return one result, if a match is found.
        shot_data = self.session.find_one('Shot', filters, fields)
        if shot_data is None:
            LOG.error(f'Could not find Shotgun data for shot {shot_code}.')
        return shot_data

    def update_shot(self, shot_code, data):
        """
        Update data for a shot with new data.
        :param shot_code: The VFX ID of the shot to update.
        :param data: A dict of fields to update and new values, e.g. {'field1': 'value1', 'field2': 'value2'}
        :return: A dict of the fields updated, with the default keys type and id added as well.
        """
        found_shot = self.find_shot(shot_code)
        if found_shot is not None:
            shot_id = found_shot.get('id')
            updated_shot = self.session.update('Shot', shot_id, data)
            return updated_shot
        else:
            LOG.error(f'Could not update data for shot {shot_code}.')

    def update_shot_status(self, shot_code, status):
        """
        A wrapper around the update_shot method, specifically to update a shot status.
        :param shot_code: The VFX ID of the shot to update.
        :param status: The new status of the shot.
        :return: A dict of the fields updated, with the default keys type and id added as well.
        """
        data = {'sg_status_list': status}
        return self.update_shot(shot_code, data)

    def create_sequence(self, seq_code, status='wtg', other_data=None):
        """
        Create a new sequence with the provided sequence code, status, and any other additional provided data.
        :param seq_code: The sequence code for the new sequence.
        :param status: The status of the sequence, defaults to 'wtg' (waiting to start).
        :param other_data: An optional dict of additional data in the format {'fieldName': 'value'}, e.g.
                           {'description': 'this is a sequence description'}
        :return: The new sequence data (or None if the sequence was not created successfully).
        """

        # Set the mandatory data for new sequence creation. At minimum, a sequence code must be provided.
        data = {
            'project': {'type': 'Project', 'id': self.project_id},
            'code': seq_code,
            'sg_status_list': status,
        }

        # If additional data is provided, merge into the original data dict. Note this will override any duplicate keys.
        if other_data is not None:
            data = {**data, **other_data}

        # Create the sequence and return the new sequence data.
        new_seq = self.session.create('Sequence', data)
        if new_seq is None:
            LOG.error(f'Create new sequence {seq_code} failed.')
        return new_seq

    def get_sequence_id(self, seq_code):
        """
        A utility method to easily retrieve a sequence ID.
        :param seq_code: The sequence code for which to retrieve the sequence ID.
        :return: Sequence ID (or None if the sequence was not found).
        """
        seq = self.find_sequence(seq_code)
        if seq is not None:
            return seq.get('id')
        return None

    def find_sequence(self, seq_code):
        """
        Retrieve sequence data for a single sequence based on the sequence code.
        :param seq_code: The sequence code to find.
        :return: The data for the given sequence (or None if no sequence was found).
        """

        # Set the filters and fields to use in the find request.
        filters = [
            ['project', 'is', {'type': 'Project', 'id': self.project_id}],
            ['code', 'is', seq_code]
        ]
        fields = ['code', 'id', 'sg_status_list', 'description', 'shots']

        # Look for a matching sequence. Will only return one result, if a match is found.
        seq_data = self.session.find_one('Sequence', filters, fields)
        if seq_data is None:
            LOG.error(f'Could not find Shotgun data for sequence {seq_code}.')
        return seq_data

    @staticmethod
    def _get_cert_path():
        # Get the ca_certs file path (depending on Python installation, this is different for 2 vs. 3)
        module_parent_path = os.path.abspath(os.path.dirname(shotgun_api3.__file__))
        if sys.version_info[0] == 3:
            cert_path = os.path.join(module_parent_path, 'lib/httplib2/python3/cacerts.txt')
        else:
            cert_path = os.path.join(module_parent_path, 'lib/httplib2/python2/cacerts.txt')
        return cert_path


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
        request_json = json.dumps(data)
        response = requests.post(url, headers=headers, data=request_json)

        # If successful, extract and return the list of record data.
        if response.ok:
            response_json = response.json()
            response_data = response_json.get('response').get('data')
            return response_data
        else:
            pass
            # TODO: Notify user of invalid http response.

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
