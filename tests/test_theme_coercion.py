from unifi_topology.render.theme import _coerce_pair, _coerce_vlan_colors


def test_coerce_pair_from_list():
    result = _coerce_pair(["#aaa", "#bbb"], ("#000", "#111"))
    assert result == ("#aaa", "#bbb")


def test_coerce_pair_from_tuple():
    result = _coerce_pair(("#ccc", "#ddd"), ("#000", "#111"))
    assert result == ("#ccc", "#ddd")


def test_coerce_pair_dict_non_string_values_returns_default():
    result = _coerce_pair({"from": 123, "to": 456}, ("#000", "#111"))
    assert result == ("#000", "#111")


def test_coerce_vlan_colors_string_digit_keys():
    result = _coerce_vlan_colors({"10": "#aaa", "20": "#bbb"})
    assert result == {10: "#aaa", 20: "#bbb"}


def test_coerce_vlan_colors_skips_non_string_color():
    result = _coerce_vlan_colors({1: 12345, 2: "#bbb"})
    assert result == {2: "#bbb"}
