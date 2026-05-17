import requests

from unifi_topology.adapters.unifi_api import UnifiClient


class FakeResponse:
    """Minimal stand-in for ``requests.Response``."""

    def __init__(self, status_code=200, json_data=None, *, ok=True, headers=None):
        self.status_code = status_code
        self._json_data = json_data
        self.ok = ok
        self.headers = headers or {}
        self.text = ""

    def json(self):
        if self._json_data is None:
            raise ValueError("No JSON")
        return self._json_data


class FakeSession:
    """Captures requests made through a ``requests.Session``."""

    def __init__(self, responses=None):
        self.calls: list[tuple[str, str, dict]] = []
        self._responses = list(responses or [])
        self._index = 0
        self.headers: dict[str, str] = {}

    def post(self, url, *, json=None, verify=True, timeout=None):
        self.calls.append(("POST", url, {"json": json, "verify": verify, "timeout": timeout}))
        return self._next()

    def get(self, url, *, verify=True, timeout=None):
        self.calls.append(("GET", url, {"verify": verify, "timeout": timeout}))
        return self._next()

    def put(self, url, *, json=None, headers=None, verify=True, timeout=None):
        self.calls.append(
            ("PUT", url, {"json": json, "headers": headers, "verify": verify, "timeout": timeout})
        )
        return self._next()

    def _next(self):
        response = self._responses[self._index]
        self._index += 1
        return response


def make_client(monkeypatch, session, *, is_udm_pro=False, request_timeout=None):
    """Construct a ``UnifiClient`` with a pre-built fake session."""
    monkeypatch.setattr(requests, "Session", lambda: session)
    return UnifiClient(
        url="https://unifi.local",
        username="admin",
        password="secret",
        is_udm_pro=is_udm_pro,
        verify_ssl=True,
        request_timeout=request_timeout,
    )
