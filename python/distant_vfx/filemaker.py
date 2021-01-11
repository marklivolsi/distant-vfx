from functools import wraps
from time import sleep
from fmrest import CloudServer
from fmrest.exceptions import BadJSON


def _request_with_retry(func):
    """
    Wrapper function that allows for CloudServer requests to be performed up to _tries number of times in the case of
    a BadJSON response, which happens intermittently. Will raise any other exception, or BadJSON if encountered again
    after _tries failed attempts.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        for i in range(self._tries):
            try:
                result = func(self, *args, **kwargs)
                return result
            except BadJSON:
                if i <= self._tries - 1:
                    sleep(0.5)
                    continue
                else:
                    raise
            except Exception:
                raise
            finally:
                # make sure Content-Type is set to avoid KeyError when popping Content-Type from header, which can
                # happen after a failed container upload attempt
                self._server._set_content_type()
        return None
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
        self.logout()

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
    def logout(self):
        return self._server.logout()

    @_request_with_retry
    def find(self, query, sort=None, limit=100):
        return self._server.find(query, sort=sort, limit=limit)

    @_request_with_retry
    def get_record(self, record_id):
        return self._server.get_record(record_id)

    @_request_with_retry
    def create_record(self, record):
        return self._server.create_record(record)

    @_request_with_retry
    def upload_container(self, record_id, field_name, file_):
        return self._server.upload_container(record_id, field_name, file_)

    @_request_with_retry
    def perform_script(self, name, param=None):
        return self._server.perform_script(name, param=param)
