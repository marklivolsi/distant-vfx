import time
from fmrest import CloudServer
from fmrest.exceptions import BadJSON


class CloudServerWrapper:

    def __init__(self, url, user, password, database, layout):
        self.url = url
        self.user = user
        self.password = password
        self.database = database
        self._layout = layout
        self._server = self._set_server()
        self._tries = 3

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

    def find(self, query, limit=100):
        records = None
        for i in range(self._tries):
            try:
                records = self._server.find([query], limit=limit)
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
        return records
