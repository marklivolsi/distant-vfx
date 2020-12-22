from functools import wraps
import time
from fmrest import CloudServer
from fmrest.exceptions import BadJSON


def _request_with_retry(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = None
        for i in range(self._tries):
            try:
                result = func(self, *args, **kwargs)
            except BadJSON:
                if i <= self._tries - 1:
                    time.sleep(0.5)
                    continue
                else:
                    raise
            except Exception:
                raise
            else:
                break
        return result
    return wrapper


class CloudServerWrapper:

    def __init__(self, url, user, password, database, layout):
        self.url = url
        self.user = user
        self.password = password
        self.database = database
        self._layout = layout
        self._server = self._set_server()
        self._tries = 3  # try requests up to _tries times to get past BadJSON response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._server.logout()

    def _set_server(self):
        return CloudServer(url=self.url,
                           user=self.user,
                           password=self.password,
                           database=self.database,
                           layout=self._layout)

    @property
    def layout(self):
        return self._layout

    @layout.setter
    def layout(self, value):
        self._layout = value
        self._server.layout = value

    @property
    def last_error(self):
        return self._server.last_error

    def login(self):
        self._server.login()

    @_request_with_retry
    def find(self, query, limit=100):
        return self._server.find(query, limit=limit)

    @_request_with_retry
    def create_record(self, record):
        return self._server.create_record(record)
