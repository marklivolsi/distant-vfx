import json
import subprocess
import traceback
import xml.etree.ElementTree as ET
from lxml import etree
from html import unescape
from bs4 import BeautifulSoup
import requests
from .constants import FASPEX_API_PATHS


class AsperaCLI:

    def __init__(self, user, password, url, url_prefix='aspera/faspex/'):
        self.user = user
        self.password = password
        self.url = url
        self.url_prefix = url_prefix

    def fetch_sent_package_list(self):
        pass

    def fetch_inbox_package_list(self):
        pass

    def _fetch_package_list(self, mailbox):
        if mailbox not in ['inbox', 'sent', 'archived']:
            raise ValueError('package_type must be either inbox, sent, or archived')
        mailbox_flag = '--' + mailbox
        opt_flags = ['--xml', mailbox_flag]
        cmd = self._construct_cmd(sub_cmd='list', opt_flags=opt_flags)
        response, errors = self._call_aspera_cli(cmd)
        return self._parse_xml_response(response)

    @staticmethod
    def _parse_xml_response(xml):
        packages = {}
        xml = xml[xml.index('<'):]
        soup = BeautifulSoup(xml, 'xml')
        entries = soup.find_all('entry')
        for entry in entries:
            delivery_id = entry.findChild('package:delivery_id').get_text()
            link = entry.findChild('link', {'rel': 'package'})['href']
            packages[delivery_id] = link
        return packages

    def _construct_cmd(self, sub_cmd, opt_flags=None):
        cmd = ['aspera', 'faspex', sub_cmd]
        std_flags = ['--host', self.url, '--user', self.user, '--password', self.password, '-U', self.url_prefix]
        cmd += std_flags
        if opt_flags:
            cmd += opt_flags
        cmd = [str(i) for i in cmd]
        return cmd

    @staticmethod
    def _call_aspera_cli(cmd):
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=False
        )
        try:
            stdout, stderr = process.communicate()
            return stdout, stderr
        except:
            traceback.print_exc()


class FaspexSession:

    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password
        self.last_processed_package_id = None
        self.latest_package_id = None
        self._token = None
        self._refresh_token = None
        self._headers = {}
        self._user_id = None
        self._set_content_type()

    def login(self):
        auth_path = FASPEX_API_PATHS['auth']
        data = {
            'grant_type': 'password'
        }
        response = self._call_faspex(
            method='POST',
            api_path=auth_path,
            data=data,
            auth=(self.user, self.password)
        )
        self._token = response.get('access_token')
        self._refresh_token = response.get('refresh_token')
        # user_data = self.fetch_user_data()
        # self._user_id = int(user_data.get('id'))

    def fetch_user_data(self):
        api_path = self._format_api_path(FASPEX_API_PATHS['users'])
        user_data = self._call_faspex(
            method='GET',
            api_path=api_path
        )
        return user_data

    def fetch_transfer_specs(self, package_id, transfer_direction):
        if transfer_direction not in ['send', 'receive']:
            raise ValueError('Transfer direction must be either "send" or "receive"')
        api_path = self._format_api_path(FASPEX_API_PATHS['transfer_specs'],
                                         package_id=package_id)
        transfer_specs = self._call_faspex(
            method='POST',
            api_path=api_path,
            data={'direction': transfer_direction},
        )
        return transfer_specs

    def fetch_packages(self):
        api_path = self._format_api_path(FASPEX_API_PATHS['packages'])
        packages = self._call_faspex(
            method='GET',
            api_path=api_path,
        )
        return packages

    def fetch_one_package(self, package_id):
        api_path = FASPEX_API_PATHS['packages'] + '/{package_id}'
        api_path = self._format_api_path(api_path,
                                         package_id=package_id)
        package_data = self._call_faspex(
            method='GET',
            api_path=api_path,
        )
        return package_data

    def get_latest_package_id(self, packages_list):
        package_ids = [self.get_package_id(package) for package in packages_list]
        self.latest_package_id = max(package_ids)
        return self.latest_package_id

    def get_packages_to_process(self, packages_list):
        if self.last_processed_package_id:
            packages_to_process = [package for package in packages_list if
                                   self.get_package_id(package) > self.last_processed_package_id]
            return packages_to_process
        else:
            return None

    def get_last_processed_package_id_from_file(self, json_file):
        try:
            with open(json_file, 'r') as file:
                data = json.load(file)
                self.last_processed_package_id = self.get_package_id(data)
        except FileNotFoundError:
            self.last_processed_package_id = None
        finally:
            return self.last_processed_package_id

    def write_last_processed_package_id_file(self, package_id, json_file):
        self.last_processed_package_id = package_id
        json_dict = {
            'id': self.last_processed_package_id
        }
        if self.last_processed_package_id is None:
            raise ValueError('Last processed package id cannot be None')
        else:
            with open(json_file, 'w') as file:
                json.dump(json_dict, file)

    @staticmethod
    def get_package_id(package_json):
        return package_json.get('id')

    def _call_faspex(self, method, api_path, data=None, params=None, **kwargs):
        url = self.url + api_path
        request_data = json.dumps(data) if data else None
        self._update_token_header()
        response = requests.request(
            method=method,
            headers=self._headers,
            url=url,
            data=request_data,
            params=params,
            **kwargs
        )
        return response.json()

    def _format_api_path(self, api_path, **kwargs):
        if self._user_id:
            user_id = self._user_id
        else:
            user_id = 'me'
        return api_path.format(user_id=user_id, **kwargs)

    def _update_token_header(self):
        if self._token:
            self._headers['Authorization'] = 'Bearer ' + self._token
        else:
            self._headers.pop('Authorization', None)
        return self._headers

    def _set_content_type(self, content_type='application/json'):
        if isinstance(content_type, str):
            self._headers['Content-Type'] = content_type
        elif not content_type:
            self._headers.pop('Content-Type')
        else:
            raise ValueError
        return self._headers
