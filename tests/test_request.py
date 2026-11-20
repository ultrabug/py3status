import threading
from http.cookiejar import CookieJar
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from py3status.request import HttpResponse

# fixed cookies, not built from the request path (CodeQL: header injection)
COOKIES = {"/a": "a=1; Path=/", "/b": "b=1; Path=/"}


class Handler(BaseHTTPRequestHandler):
    """
    Set the cookie for the path and echo back the Cookie header.
    """

    def do_GET(self):
        self.send_response(200)
        self.send_header("Set-Cookie", COOKIES[self.path])
        self.end_headers()
        self.wfile.write((self.headers.get("Cookie") or "").encode())

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def get(url, path, cookiejar=None):
    return HttpResponse(url + path, None, None, {}, 5, None, cookiejar).text


def test_module_keeps_its_cookies(url):
    jar = CookieJar()
    assert get(url, "/a", jar) == ""
    assert get(url, "/a", jar) == "a=1"


def test_module_without_jar_gets_no_cookies(url):
    jar = CookieJar()
    get(url, "/a", jar)
    assert get(url, "/b") == ""
    assert [c.name for c in jar] == ["a"]


def test_modules_do_not_share_jars(url):
    jar_a, jar_b = CookieJar(), CookieJar()
    get(url, "/a", jar_a)
    get(url, "/b", jar_b)
    assert get(url, "/a", jar_a) == "a=1"
    assert get(url, "/b", jar_b) == "b=1"
