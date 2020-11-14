import logging
from pathlib import Path
import os
import sys
import pandas as pd
from yaml import safe_load, YAMLError
import shotgun_api3
import pycognito


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

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.client = None

    def connect(self):
        # Initialize Shotgun connection. Must pass cert path to avoid FileNotFoundError.
        try:
            client = shotgun_api3.Shotgun(self.base_url,
                                          login=self.username,
                                          password=self.password,
                                          ca_certs=ShotgunInstance.__get_cert_path())
            self.client = client
            return True
        except shotgun_api3.ShotgunError as e:
            LOG.error(e)
            return False

    @staticmethod
    def __get_cert_path():
        # Get the ca_certs file path (depending on Python installation, this is different for 2 vs. 3)
        module_parent_path = os.path.abspath(os.path.dirname(shotgun_api3.__file__))
        if sys.version_info[0] == 3:
            cert_path = os.path.join(module_parent_path, 'lib/httplib2/python3/cacerts.txt')
        else:
            cert_path = os.path.join(module_parent_path, 'lib/httplib2/python2/cacerts.txt')
        return cert_path


class FileMakerInstance:

    def __init__(self, username, password, user_pool_id, client_id):
        self.username = username
        self.password = password
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.fmid_token = None
        self.refresh_token = None

    def connect(self):
        pass

    def __get_fmid_token(self):
        user = pycognito.Cognito(user_pool_id=self.user_pool_id,
                                 client_id=self.client_id,
                                 username=self.username)
        user.authenticate(self.password)
        self.fmid_token = user.id_token
        self.refresh_token = user.refresh_token
