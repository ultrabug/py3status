try:
    # Python 3
    from http.cookiejar import CookieJar
except ImportError:
    # Python 2
    from cookielib import CookieJar

from py3status.storage import StorageObject


class PersistentCookieJar(CookieJar, StorageObject):
    """
    Custom CookieJar child class that will use our storage module.
    """
    def _data_dump(self):
        return self._cookies

    def _data_load(self, data):
        if data:
            self._cookies = data
