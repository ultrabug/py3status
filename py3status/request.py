import base64
import json
import socket

try:
    # Python 3
    from urllib.error import URLError, HTTPError
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
    from urllib.request import (
        urlopen,
        Request,
        build_opener,
        install_opener,
        HTTPCookieProcessor,
    )

    IS_PYTHON_3 = True
except ImportError:
    # Python 2
    from urllib import urlencode
    from urllib2 import (
        urlopen,
        Request,
        URLError,
        HTTPError,
        build_opener,
        install_opener,
        HTTPCookieProcessor,
    )
    from urlparse import urlsplit, urlunsplit, parse_qsl

    IS_PYTHON_3 = False

from py3status.exceptions import RequestTimeout, RequestURLError, RequestInvalidJSON


class HttpResponse:
    """
    Simple encapsulation of a http response for a url

    The aim is to support both python 2 and 3 and be a simple as possible
    """

    def __init__(self, url, params, data, headers, timeout, auth, cookiejar):
        # fix the url if needed
        url_parts = urlsplit(url)
        if url_parts.query or params:
            # split into parts so we can update
            parts = list(url_parts)
            # Make sure the querystring params are correctly encoded
            url_params = parse_qsl(parts[3])
            if params:
                for key, value in params.items():
                    url_params.append((key, value))
            parts[3] = urlencode(url_params)
            # rebuild the url
            url = urlunsplit(parts)
        if auth:
            # we need to do the encode/decode to keep python 3 happy
            auth_str = base64.b64encode(("%s:%s" % (auth)).encode("utf-8"))
            headers["Authorization"] = "Basic %s" % auth_str.decode("utf-8")
        if data:
            data = urlencode(data).encode()
        if cookiejar is not None:
            self._cookiejar = cookiejar
            opener = build_opener(HTTPCookieProcessor(cookiejar))
            install_opener(opener)

        request = Request(url, headers=headers)

        try:
            self._response = urlopen(request, data=data, timeout=timeout)
            self._error_message = None
        except URLError as e:
            reason = e.reason
            if isinstance(reason, socket.timeout):
                raise RequestTimeout("request timed out")
            elif isinstance(e, HTTPError):
                self._status_code = e.code
                self._error_message = reason
                # we return an HttpResponse but have no response
                # so create some 'fake' response data.
                self._text = ""
                self._json = None
                self._headers = []
            else:
                # unknown exception, so just raise it
                raise RequestURLError(reason)
        except socket.timeout:
            raise RequestTimeout("request timed out")

    @property
    def status_code(self):
        """
        Get the http status code for the response
        """
        try:
            return self._status_code
        except AttributeError:
            self._status_code = self._response.getcode()
        return self._status_code

    @property
    def text(self):
        """
        Get the raw text for the response
        """
        try:
            return self._text
        except AttributeError:
            if IS_PYTHON_3:
                encoding = self._response.headers.get_content_charset("utf-8")
            else:
                encoding = self._response.headers.getparam("charset")
            self._text = self._response.read().decode(encoding or "utf-8")
        return self._text

    def json(self):
        """
        Return an object representing the return json for the request
        """
        try:
            return self._json
        except AttributeError:
            try:
                self._json = json.loads(self.text)
                return self._json
            except:  # noqa e722
                raise RequestInvalidJSON("Invalid JSON received")

    @property
    def headers(self):
        """
        Get the headers from the response.
        """
        try:
            return self._headers
        except AttributeError:
            self._headers = self._response.headers
            return self._headers

    @property
    def cookiejar(self):
        """
        Get the cookie jar
        """
        try:
            return self._cookiejar
        except AttributeError:
            return None

    @cookiejar.setter
    def cookiejar(self, cj):
        """
        Set the cookie jar in care we want to change it after object creation
        """
        self._cookiejar = cj
