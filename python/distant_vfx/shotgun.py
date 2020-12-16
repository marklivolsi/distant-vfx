import logging
import os
import sys
import shotgun_api3

LOG = logging.getLogger(__name__)


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
            LOG.error('{exc_type}: {exc_val}'.format(exc_type=exc_type, exc_val=exc_val))

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
            data.update(other_data)

        # Create the shot and return the new shot data.
        new_shot = self.session.create('Shot', data)
        if new_shot is None:
            LOG.error('Create new shot {shot_code} failed.'.format(shot_code=shot_code))
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
            LOG.error('Could not find Shotgun data for shot {shot_code}.'.format(shot_code=shot_code))
            # TODO : Replace log statements here and elsewhere.
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
            LOG.error('Could not update data for shot {shot_code}.'.format(shot_code=shot_code))

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
            data.update(other_data)

        # Create the sequence and return the new sequence data.
        new_seq = self.session.create('Sequence', data)
        if new_seq is None:
            LOG.error('Create new sequence {seq_code} failed.'.format(seq_code=seq_code))
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
            LOG.error('Could not find Shotgun data for sequence {seq_code}.'.format(seq_code=seq_code))
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
