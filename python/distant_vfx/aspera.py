import json
import requests
from distant_vfx.constants import FASPEX_API_PATHS


class AsperaSession:

    def __init__(self, url, user, password, admin=False):
        self.url = url
        self.user = user
        self.password = password
        self.admin = admin
        self.last_processed_package_id = None
        self.latest_package_id = None
        self._token = None
        self._refresh_token = None
        self._headers = {}
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

    def fetch_packages(self):
        api_path = self._format_api_path(FASPEX_API_PATHS['packages'])
        packages = self._call_faspex(
            method='GET',
            api_path=api_path,
        )
        return packages

    def get_latest_package_id(self, packages_list):
        package_ids = [self._get_package_id(package) for package in packages_list]
        self.latest_package_id = max(package_ids)
        return self.latest_package_id

    def get_packages_to_process(self, packages_list):
        packages_to_process = [package for package in packages_list if
                               self._get_package_id(package) > self.last_processed_package_id]
        return packages_to_process

    def get_last_processed_package_id_from_file(self, json_file):
        try:
            with open(json_file, 'r') as file:
                data = json.load(file)
                self.last_processed_package_id = self._get_package_id(data)
        except FileNotFoundError:
            self.last_processed_package_id = None
        finally:
            return self.last_processed_package_id

    def write_last_processed_package_id_file(self, json_file):
        json_dict = {
            'id': self.last_processed_package_id
        }
        if self.last_processed_package_id is None:
            raise ValueError('Last processed package id cannot be None')
        else:
            with open(json_file, 'w') as file:
                json.dump(json_dict, file)

    @staticmethod
    def _get_package_id(package_json):
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
        if self.admin:
            user_id = self.user
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
