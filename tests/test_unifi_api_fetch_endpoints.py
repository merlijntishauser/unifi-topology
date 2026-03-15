import pytest

from tests.unifi_api_helpers import FakeResponse, FakeSession, make_client

pytestmark = pytest.mark.unit


def test_get_devices_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    detailed_resp = FakeResponse(json_data={"data": [{"mac": "aa"}]})
    basic_resp = FakeResponse(json_data={"data": [{"mac": "bb"}]})
    session = FakeSession([auth_resp, detailed_resp, basic_resp])
    client = make_client(monkeypatch, session)

    result = client.get_devices("default", detailed=True)
    assert result == [{"mac": "aa"}]
    assert session.calls[1][1] == "https://unifi.local/api/s/default/stat/device"

    result = client.get_devices("default", detailed=False)
    assert result == [{"mac": "bb"}]
    assert session.calls[2][1] == "https://unifi.local/api/s/default/stat/device-basic"


def test_get_clients_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"mac": "cc"}]})
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session)

    result = client.get_clients("mysite")
    assert result == [{"mac": "cc"}]
    assert session.calls[1][1] == "https://unifi.local/api/s/mysite/stat/sta"


def test_get_networkconf_url(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"_id": "net1"}]})
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session)

    result = client.get_networkconf("default")
    assert result == [{"_id": "net1"}]
    assert session.calls[1][1] == "https://unifi.local/api/s/default/rest/networkconf"


def test_parse_data_field(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"a": 1}, {"b": 2}]})
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session)

    result = client.get_clients("default")
    assert len(result) == 2
    assert result[0] == {"a": 1}


def test_request_timeout_is_passed_to_auth_and_get(monkeypatch):
    auth_resp = FakeResponse(json_data={"meta": {"rc": "ok"}})
    data_resp = FakeResponse(json_data={"data": [{"mac": "cc"}]})
    session = FakeSession([auth_resp, data_resp])
    client = make_client(monkeypatch, session, request_timeout=5.0)

    client.get_clients("mysite")
    assert session.calls[0][2]["timeout"] == 5.0
    assert session.calls[1][2]["timeout"] == 5.0
