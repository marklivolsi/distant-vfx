from datetime import datetime
from functools import wraps
import os
from time import sleep
import yagmail
from pprint import pformat
from ..filemaker import CloudServerWrapper
from ..video import VideoProcessor
from ..constants import FMP_URL, FMP_USERNAME, FMP_PASSWORD, FMP_ADMIN_DB, FMP_VERSIONS_LAYOUT, FMP_TRANSFER_LOG_LAYOUT, \
    FMP_TRANSFER_DATA_LAYOUT, FMP_IMAGES_LAYOUT, FMP_PROCESS_IMAGE_SCRIPT, THUMBS_BASE_PATH, LEGAL_THUMB_SRC_EXTENSIONS, \
    EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_RECIPIENTS


def _dict_items_to_str(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        dictionary = func(*args, **kwargs)
        result = {str(key): ('' if value is None else str(value)) for key, value in dictionary.items()}
        return result
    return wrapper


class BaseInjector:

    def __init__(self, sg, logger, event, args):
        self.sg = sg
        self.logger = logger
        self.event = event
        self.args = args
        self.fmp_version = None
        self.fmp_transfer_log = None
        self.fmp_transfer_data = None
        self.fmp_image_data = None
        self._transfer_log_primary_key = None
        self.report = {
            'version': True,
            'transfer_log': True,
            'transfer_data': True,
            'image': True
        }
        self._email_subject = None

    def inject(self):

        # validate the event
        is_inject_candidate = self.validate_event()
        if not is_inject_candidate:
            return

        # wait to make sure entity is fully created
        sleep(1)

        # try to fetch the submission data
        did_fetch_submission_data = self.fetch_submission_data()
        if not did_fetch_submission_data:
            self.logger.error(f'Could not fetch submission data for event: {self.event}')
            return

        # format data for injection
        try:
            self.format_data_for_fmp_injection()
        except:
            self.logger.error('Error formatting data for FMP injection.', exc_info=True)
            return

        # format image data for injection
        try:
            self.format_image_data_for_fmp_injection()
        except:
            self.logger.error(f'Error generating thumbnail.', exc_info=True)

        # inject the data
        self.inject_to_fmp()

        # send an email report
        self.send_email()

    def send_email(self):
        version = self.fmp_version if self.report['version'] else ''
        transfer_log = self.fmp_transfer_log if self.report['transfer_log'] else ''
        transfer_data = self.fmp_transfer_data if self.report['transfer_data'] else ''
        image = self.fmp_image_data if self.report['image'] else ''
        content = 'Shotgun data successfully injected into FileMaker. Please see below for details.\n\n' \
                  '<hr>' \
                  f'<h3>VERSION DATA</h3>\n{pformat(version)}\n\n' \
                  f'<h3>TRANSFER LOG DATA</h3>\n{pformat(transfer_log)}\n\n' \
                  f'<h3>TRANSFER FILES DATA</h3>\n{pformat(transfer_data)}\n\n' \
                  f'<h3>IMAGE DATA</h3>\n{pformat(image)}\n\n' \
                  f'<hr>'
        yag = yagmail.SMTP(
            user=EMAIL_USERNAME,
            password=EMAIL_PASSWORD,
        )
        yag.send(
            to=EMAIL_RECIPIENTS.split(','),
            subject=self._email_subject,
            contents=content
        )

    def inject_to_fmp(self):
        with CloudServerWrapper(url=FMP_URL,
                                user=FMP_USERNAME,
                                password=FMP_PASSWORD,
                                database=FMP_ADMIN_DB,
                                layout=FMP_VERSIONS_LAYOUT
                                ) as fmp:
            fmp.login()

            # inject version
            try:
                version_id = self._inject_version(fmp)
            except:
                self.logger.error(f'Error injecting version: {self.fmp_version}', exc_info=True)
                self.report['version'] = False

            # inject transfer log
            fmp.layout = FMP_TRANSFER_LOG_LAYOUT
            try:
                transfer_log_id = self._find_transfer_log(fmp)
                self._transfer_log_primary_key = transfer_log_id[0].PrimaryKey
            except:
                if not fmp.last_error == 401:
                    self.logger.error(f'Error finding transfer log record: {self.fmp_transfer_log}', exc_info=True)
                transfer_log_id = None

            if not transfer_log_id:
                try:
                    transfer_log_id = self._inject_transfer_log(fmp)
                except:
                    self.report['transfer_log'] = False
                    self.logger.error(f'Error injecting transfer log record: {self.fmp_transfer_log}', exc_info=True)

                try:
                    self._get_transfer_log_primary_key(fmp, transfer_log_id)
                except:
                    self.logger.error(f'Error finding transfer log key: {self.fmp_transfer_log}', exc_info=True)

            # inject transfer data
            try:
                fmp.layout = FMP_TRANSFER_DATA_LAYOUT
                record_id = self._inject_transfer_data(fmp)
            except:
                self.logger.error(f'Error injecting transfer data records: {self.fmp_transfer_data}', exc_info=True)
                self.report['transfer_data'] = False

            # inject image data
            image_path = self.fmp_image_data.get('image_path')
            if image_path is None:
                self.report['image'] = False
                return
            else:
                fmp.layout = FMP_IMAGES_LAYOUT
                try:
                    image_record_id = self._inject_image(fmp)
                except:
                    self.logger.error(f'Error injecting image data: {self.fmp_image_data}', exc_info=True)
                    self.report['image'] = False
                    return

            # get image primary key
            try:
                image_primary_key = self._get_image_primary_key(fmp, image_record_id)
            except:
                self.logger.error(f'Error getting image key: {self.fmp_image_data}', exc_info=True)
                return

            # run process image script
            try:
                script_result = self._run_process_image_script(fmp, image_primary_key)
            except:
                self.logger.error(f'Error running process image script: {self.fmp_image_data}', exc_info=True)

    def validate_event(self):
        raise NotImplementedError

    def fetch_submission_data(self):
        raise NotImplementedError

    def format_data_for_fmp_injection(self):
        self.fmp_version = self._build_fmp_version()
        self.fmp_transfer_log = self._build_fmp_transfer_log()
        self.fmp_transfer_data = self._build_fmp_transfer_data()

    def format_image_data_for_fmp_injection(self):
        mov_path = self._get_mov_path()
        image_name, image_path = None, None
        if mov_path:
            image_name, image_path = self.get_thumbnail(mov_path)
        self.fmp_image_data = self._build_fmp_image_data(image_name, image_path)

    @staticmethod
    def get_thumbnail(mov_path):

        # Get the thumbnail output path
        mov_filename = os.path.basename(mov_path)
        mov_split = os.path.splitext(mov_filename)
        mov_basename, mov_ext = mov_split[0], mov_split[1]
        thumb_filename = '0000 ' + mov_basename + '.jpg'  # Naming structure needed to parse vfx id with current setup
        thumb_dest = os.path.join(THUMBS_BASE_PATH, thumb_filename)

        # Generate thumbnail
        if not os.path.exists(thumb_dest):
            video_processor = VideoProcessor()
            video_processor.generate_thumbnail(mov_path, thumb_dest)
        return thumb_filename, thumb_dest

    def _get_event_attr_and_new_value(self):
        event_attr = self.event.get('attribute_name')
        new_value = self.event.get('meta').get('new_value')
        return event_attr, new_value

    @staticmethod
    def _parse_vfx_entity_code(data_dict):
        try:
            vfx_entity_code = data_dict['entity']['name']
            return vfx_entity_code
        except:
            return ''

    def _get_vfx_code(self):
        raise NotImplementedError

    @staticmethod
    def _get_sg_published_file_path(published_file):
        try:
            path = published_file['path']['local_path_linux']
            return path
        except:
            return ''

    def _get_package_name(self):
        raise NotImplementedError

    def _format_version_name(self):
        raise NotImplementedError

    def _build_fmp_version(self):
        raise NotImplementedError

    def _build_fmp_transfer_log(self):
        raise NotImplementedError

    def _build_fmp_transfer_data(self):
        raise NotImplementedError

    @staticmethod
    @_dict_items_to_str
    def _build_fmp_image_data(image_name, image_path):
        fmp_image_data = {
            'Filename': image_name,
            'Path': image_path,
        }
        return fmp_image_data

    def _get_mov_path(self):
        raise NotImplementedError

    def _inject_version(self, fmp):
        return fmp.create_record(self.fmp_version)

    def _find_transfer_log(self, fmp):
        return fmp.find([self.fmp_transfer_log])

    def _inject_transfer_log(self, fmp):
        return fmp.create_record(self.fmp_transfer_log)

    def _inject_transfer_data(self, fmp):
        raise NotImplementedError

    def _get_transfer_log_primary_key(self, fmp, transfer_log_record_id):
        transfer_log_data = fmp.get_record(transfer_log_record_id)
        primary_key = transfer_log_data.PrimaryKey
        self._transfer_log_primary_key = primary_key

    def _inject_image(self, fmp):
        record_id = None
        try:
            thumb_file = open(self.fmp_image_data.get('Path'), 'rb')
            record_id = fmp.create_record(self.fmp_image_data)
            image_did_upload = fmp.upload_container(record_id, field_name='Image', file_=thumb_file)
        except:
            self.logger.error(f'Error injecting thumbnail record: {self.fmp_image_data}', exc_info=True)
        return record_id

    @staticmethod
    def _get_image_primary_key(fmp, image_record_id):
        image_data = fmp.get_record(image_record_id)
        primary_key = image_data.PrimaryKey
        return primary_key

    @staticmethod
    def _run_process_image_script(fmp, image_primary_key):
        script_result = fmp.perform_script(name=FMP_PROCESS_IMAGE_SCRIPT,
                                           param=image_primary_key)
        return script_result


class SgEventsInHouseInjector(BaseInjector):

    def __init__(self, sg, logger, event, args):
        super().__init__(sg, logger, event, args)
        self.sg_version = None
        self.sg_published_files = None
        self._email_subject = f'[DISTANT_API] Successful In House data injection at {datetime.now()}'

    def validate_event(self):
        event_attr, new_value = self._get_event_attr_and_new_value()
        return event_attr == 'sg_status_list' and new_value == 'ihapp'

    def fetch_submission_data(self):
        self.sg_version = self._fetch_shotgun_version()
        self.sg_published_files = self._fetch_shotgun_published_files()
        if self.sg_version and self.sg_published_files:
            return True
        return False

    def _fetch_shotgun_version(self):
        version = self.sg.find_one(
            entity_type='Version',
            filters=[
                ['id', 'is', self.event.get('meta').get('entity_id')]
            ],
            fields=[
                'code',
                'description',
                'entity',           # gets the shots / assets links
                'published_files',  # gets the file links
                'sg_path_to_movie',
                'sg_task'
            ]
        )
        return version

    def _fetch_shotgun_published_files(self):
        published_files = self.sg.find(
            entity_type='PublishedFile',
            filters=[
                ['version.Version.code', 'is', self.sg_version.get('code')]
            ],
            fields=[
                'code',
                'path',
            ]
        )
        return published_files

    def _get_vfx_code(self):
        return self._parse_vfx_entity_code(self.sg_version)

    def _get_task_name(self):
        try:
            task_name = self.sg_version['sg_task']['name']
            return task_name
        except:
            return ''

    def _get_package_name(self):
        return 'dst_ih_' + datetime.now().strftime('%Y%m%d')

    def _format_version_name(self):
        version_code = self.sg_version.get('code')
        if version_code:
            return version_code.replace(' ', '_').lower()
        return ''

    @_dict_items_to_str
    def _build_fmp_version(self):
        fmp_version = {
            'VFXID': self._get_vfx_code(),
            'ShotgunID': self.sg_version.get('id'),
            'DeliveryNote': self.sg_version.get('description'),
            'DeliveryPackage': self._get_package_name(),
            'Filename': self._format_version_name(),
            'ShotgunTaskName': self._get_task_name()
        }
        return fmp_version

    @_dict_items_to_str
    def _build_fmp_transfer_log(self):
        fmp_transfer_log = {
            'package': self._get_package_name()
        }
        return fmp_transfer_log

    def _build_fmp_transfer_data(self):
        transfer_dicts = []
        if not self.sg_published_files:
            return None
        for published_file in self.sg_published_files:
            transfer_data = self._build_one_fmp_transfer_data_dict(published_file)
            transfer_dicts.append(transfer_data)
        return transfer_dicts

    @_dict_items_to_str
    def _build_one_fmp_transfer_data_dict(self, sg_published_file):
        transfer_data = {
            'Filename': sg_published_file.get('code'),
            'PublishedFileID': sg_published_file.get('id'),
            'Path': self._get_sg_published_file_path(sg_published_file),
            'VersionLink': self._format_version_name()
        }
        return transfer_data

    def _get_mov_path(self):
        return self.sg_version.get('sg_path_to_movie')

    def _inject_transfer_data(self, fmp):
        record_ids = []
        for transfer_data_record in self.fmp_transfer_data:
            primary_key = self._transfer_log_primary_key if self._transfer_log_primary_key else ''
            transfer_data_record['Foriegnkey'] = primary_key
            record_id = fmp.create_record(transfer_data_record)
            record_ids.append(record_id)
        return record_ids


class SgEventsExtVendorInjector(BaseInjector):

    def __init__(self, sg, logger, event, args):
        super().__init__(sg, logger, event, args)
        self.sg_published_file = None
        self._email_subject = f'[DISTANT_API] Successful External Vendor data injection at {datetime.now()}'

    def validate_event(self):
        event_attr, new_value = self._get_event_attr_and_new_value()
        return event_attr == 'sg_status_list' and new_value == 'extapp'

    def fetch_submission_data(self):
        self.sg_published_file = self._fetch_shotgun_published_file()
        if self.sg_published_file:
            return True
        return False

    def _fetch_shotgun_published_file(self):
        published_file = self.sg.find_one(
            entity_type='PublishedFile',
            filters=[
                ['id', 'is', self.event.get('meta').get('entity_id')]
            ],
            fields=[
                'code',                       # filename
                'description',                # submission note
                'path',                       # filepath on disk
                'entity',                     # provides access to shot / asset entity
                'sg_delivery_package_name',   # delivery package
                'sg_delivery_package_path',   # package path
                'sg_intended_status'
            ]
        )
        return published_file

    def _get_vfx_code(self):
        return self._parse_vfx_entity_code(self.sg_published_file)

    def _get_package_name(self):
        return self.sg_published_file.get('sg_delivery_package_name')

    def _format_version_name(self):
        filename = self.sg_published_file.get('code')
        if filename:
            dot_count = filename.count('.')
            if dot_count == 2:  # likely a frame range
                version = filename.split('.')[0]
            else:
                version = os.path.splitext(filename)[0]
            return version.replace(' ', '_').lower()
        return ''

    @_dict_items_to_str
    def _build_fmp_version(self):
        fmp_version = {
            'VFXID': self._get_vfx_code(),
            'DeliveryNote': self.sg_published_file.get('description'),
            'DeliveryPackage': self.sg_published_file.get('sg_delivery_package_name'),
            'Filename': self._format_version_name(),
            'IntendedStatus': self.sg_published_file.get('sg_intended_status')
        }
        return fmp_version

    @_dict_items_to_str
    def _build_fmp_transfer_log(self):
        fmp_transfer_log = {
            'package': self.sg_published_file.get('sg_delivery_package_name'),
            'path': self.sg_published_file.get('sg_delivery_package_path')
        }
        return fmp_transfer_log

    @_dict_items_to_str
    def _build_fmp_transfer_data(self):
        transfer_data = {
            'Filename': self.sg_published_file.get('code'),
            'PublishedFileID': self.sg_published_file.get('id'),
            'Path': self._get_sg_published_file_path(self.sg_published_file),
            'VersionLink': self._format_version_name()
        }
        return transfer_data

    def _get_mov_path(self):
        path = self._get_sg_published_file_path(self.sg_published_file)
        if path and os.path.splitext(path)[1] in LEGAL_THUMB_SRC_EXTENSIONS:
            return path
        return None

    def _inject_transfer_data(self, fmp):
        primary_key = self._transfer_log_primary_key if self._transfer_log_primary_key else ''
        self.fmp_transfer_data['Foriegnkey'] = primary_key
        record_id = fmp.create_record(self.fmp_transfer_data)
        return record_id


class ManualInjector(BaseInjector):

    def __init__(self, sg=None, logger=None, event=None, args=None):
        super().__init__(sg, logger, event, args)
        self._email_subject = f'[DISTANT_API] Successful Manual data injection at {datetime.now()}'

    def validate_event(self):
        return True  # always valid for manual injections

    def fetch_submission_data(self):
        raise NotImplementedError

    def _get_vfx_code(self):
        raise NotImplementedError  # TODO: Implement this

    def _get_package_name(self):
        raise NotImplementedError

    def _format_version_name(self):
        raise NotImplementedError

    @_dict_items_to_str
    def _build_fmp_version(self):
        raise NotImplementedError

    @_dict_items_to_str
    def _build_fmp_transfer_log(self):
        raise NotImplementedError

    def _build_fmp_transfer_data(self):
        raise NotImplementedError

    def _get_mov_path(self):
        raise NotImplementedError

    def _inject_version(self, fmp):
        raise NotImplementedError

    def _inject_transfer_data(self, fmp):
        record_ids = []
        for transfer_data_record in self.fmp_transfer_data:
            primary_key = self._transfer_log_primary_key if self._transfer_log_primary_key else ''
            transfer_data_record['Foriegnkey'] = primary_key
            record_id = fmp.create_record(transfer_data_record)
            record_ids.append(record_id)
        return record_ids

    def _inject_image(self, fmp):
        raise NotImplementedError