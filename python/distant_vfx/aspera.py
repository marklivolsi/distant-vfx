import json
import requests
from distant_vfx.constants import FASPEX_API_PATHS


class AsperaSession:

    def __init__(self, url, user, password, admin=False):
        self.url = url
        self.user = user
        self.password = password
        self.admin = admin
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
            request_type='POST',
            api_path=auth_path,
            data=data,
            auth=(self.user, self.password)
        )
        self._token = response.get('access_token')
        self._refresh_token = response.get('refresh_token')

    def get_all_packages(self):
        api_path = self._format_api_path(FASPEX_API_PATHS['packages'])
        response = self._call_faspex(
            request_type='GET',
            api_path=api_path,
        )
        return response

    def _call_faspex(self, request_type, api_path, data=None, params=None, **kwargs):
        url = self.url + api_path
        request_data = json.dumps(data) if data else None
        self._update_token_header()
        response = requests.request(
            method=request_type,
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
