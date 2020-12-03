import logging
import os
import pandas as pd

LOG = logging.getLogger(__name__)


class ALEParser:

    def __init__(self):
        self.ale_path = None
        self.header_data = None
        self.column_data = None

    @property
    def ale_name(self):
        if self.ale_path is not None:
            return os.path.basename(self.ale_path)

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
        print('Reading ALE data for {ale_path}'.format(ale_path=self.ale_path))
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
        def column_replacer(column_name):
            """
            :param str column_name:
            :return: Replaced column name
            """
            forbidden_chars = '",+-*/^&=≠><()[]{};:$ '
            for char in forbidden_chars:
                column_name.replace(char, "_")
            return column_name
        # Replace problematic characters in the headers with _
        self.column_data.rename(columns=column_replacer, inplace=True)

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


class EDLParser:

    def __init__(self):
        self.title = None
        self.fcm = None
        self.event_list = None
        self.events = None

    def parse_edl(self, edl_path):
        self._read_edl_file(edl_path)
        for event in self.event_list:
            self._parse_event(event)

    @staticmethod
    def _parse_event(event_str):
        event_dict = {}
        # TODO: Parse data from event string.

    def _read_edl_file(self, edl_path):
        title, fcm, event, events = None, None, None, []

        # Read in the lines from the edl
        with open(edl_path, 'r') as edl:
            lines = edl.readlines()

        for line in lines:

            # Extract the title and fcm values.
            if line.startswith('TITLE'):
                title = line
            elif line.startswith('FCM'):
                fcm = line

            # If line starts with a digit, it is assumed to be an event
            elif line.split()[0].isdigit():
                if event is not None:
                    events.append(event)
                event = line

            # If not the start of a new event, add the line to the current event
            else:
                event += line

        # Add the final event
        events.append(event)
        self.title, self.fcm, self.event_list = title, fcm, events

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
