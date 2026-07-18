"""_client_is_wired must coerce stringly-typed is_wired values."""

from unifi_topology.model._client_access import _client_is_wired


def test_string_false_is_not_wired():
    assert _client_is_wired({"is_wired": "false"}) is False


def test_string_true_is_wired():
    assert _client_is_wired({"is_wired": "true"}) is True


def test_bool_values_preserved():
    assert _client_is_wired({"is_wired": True}) is True
    assert _client_is_wired({"is_wired": False}) is False
