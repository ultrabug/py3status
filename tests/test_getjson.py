import base64
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from types import SimpleNamespace

import pytest

from py3status.composite import Composite
from py3status.module import Module
from py3status.module_test import MockPy3statusWrapper
from py3status.modules.getjson import Py3status


@pytest.fixture
def json_server():
    state = SimpleNamespace(requests=[], required_headers={})

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            state.requests.append((self.path, self.headers))
            authorized = all(
                self.headers.get(name) == value
                for name, value in state.required_headers.items()
            )
            body = json.dumps({"items": [{"name": "ready"}]}).encode()
            self.send_response(200 if authorized else 401)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        state.url = f"http://127.0.0.1:{server.server_port}/data"
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        thread.start()
        try:
            yield state
        finally:
            server.shutdown()
            thread.join(timeout=5)


def load_module(server, **config):
    wrapper = MockPy3statusWrapper(
        {
            "general": {},
            "py3status": {},
            ".module_groups": {},
            "getjson": {
                "url": server.url,
                "format": "{items-0-name}",
                **config,
            },
        }
    )
    instance = Py3status()
    module = Module("getjson", {}, wrapper, instance)
    module.prepare_module()
    assert not module.error_messages
    return instance


@pytest.mark.parametrize(
    "headers",
    [
        {"X-API-Key": "test-key", "Accept": "application/json"},
        {"Authorization": "Bearer test-token", "User-Agent": "getjson-test"},
    ],
)
def test_headers_reach_json_server(json_server, headers):
    json_server.required_headers = headers
    module = load_module(json_server, headers=headers)

    result = module.getjson()

    assert Composite(result["full_text"]).text() == "ready"
    assert json_server.requests[0][0] == "/data"
    for name, value in headers.items():
        assert json_server.requests[0][1][name] == value


@pytest.mark.parametrize("config", [{}, {"headers": None}, {"headers": {}}])
def test_headers_remain_optional(json_server, config):
    module = load_module(json_server, **config)

    assert Composite(module.getjson()["full_text"]).text() == "ready"
    request_headers = json_server.requests[0][1]
    assert request_headers["User-Agent"].startswith("py3status/")
    assert request_headers["Authorization"] is None
    assert request_headers["X-API-Key"] is None


def test_basic_auth_with_headers_preserves_config(json_server):
    headers = {"X-API-Key": "test-key", "Authorization": "Bearer test-token"}
    original = headers.copy()
    authorization = "Basic " + base64.b64encode(b"user:password").decode()
    json_server.required_headers = {
        "X-API-Key": "test-key",
        "Authorization": authorization,
    }
    module = load_module(json_server, headers=headers, username="user", password="password")

    for _ in range(2):
        assert Composite(module.getjson()["full_text"]).text() == "ready"
        assert module.headers == original
        assert headers == original

    assert len(json_server.requests) == 2
    for _, received in json_server.requests:
        assert received["Authorization"] == authorization
        assert received["X-API-Key"] == "test-key"

    # Another module using the same config must still send the bearer token.
    json_server.required_headers = original
    other_module = load_module(json_server, headers=headers)
    assert Composite(other_module.getjson()["full_text"]).text() == "ready"


def test_basic_auth_without_headers(json_server):
    authorization = "Basic " + base64.b64encode(b"user:password").decode()
    json_server.required_headers = {"Authorization": authorization}
    module = load_module(json_server, username="user", password="password")

    assert Composite(module.getjson()["full_text"]).text() == "ready"
    assert json_server.requests[0][1]["Authorization"] == authorization
