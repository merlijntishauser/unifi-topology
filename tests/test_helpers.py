"""Tests for helpers.py to improve coverage."""

from unifi_topology.model.helpers import as_int, as_list

# --- as_list ---


def test_as_list_string_returns_empty():
    """Strings should return an empty list (not be iterated)."""
    assert as_list("hello") == []


def test_as_list_bytes_returns_empty():
    """Bytes should return an empty list (not be iterated)."""
    assert as_list(b"data") == []


def test_as_list_non_iterable_returns_empty():
    """Non-iterable, non-dict, non-None values return empty list."""
    assert as_list(42) == []
    assert as_list(3.14) == []
    assert as_list(True) == []


# --- as_int ---


def test_as_int_float_truncates():
    """Floats should be truncated to int."""
    assert as_int(3.7) == 3
    assert as_int(0.5) == 0
    assert as_int(-2.9) == -2


def test_as_int_string_valid():
    """Valid numeric strings should be parsed to int."""
    assert as_int("42") == 42
    assert as_int(" 7 ") == 7
    assert as_int("-3") == -3


def test_as_int_string_invalid_returns_default():
    """Invalid strings should return the default value."""
    assert as_int("abc") == 0
    assert as_int("abc", default=99) == 99
    assert as_int("", default=5) == 5


def test_normalize_mac_unifies_separators_and_case():
    from unifi_topology.model.helpers import normalize_mac

    canonical = "aa:bb:cc:dd:ee:ff"
    assert normalize_mac("AA-BB-CC-DD-EE-FF") == canonical
    assert normalize_mac("aa:bb:cc:dd:ee:ff") == canonical
    assert normalize_mac("AABBCCDDEEFF") == canonical


def test_normalize_mac_leaves_non_mac_strings_lowercased():
    from unifi_topology.model.helpers import normalize_mac

    assert normalize_mac("Core-Switch") == "core-switch"
    assert normalize_mac("aa") == "aa"
