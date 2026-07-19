"""Device must be hashable (by identity) rather than raising on hash."""

from unifi_topology.model.topology import Device


def _device() -> Device:
    return Device(
        name="sw",
        model_name="",
        model="",
        mac="aa:bb:cc:dd:ee:ff",
        ip="",
        type="switch",
        lldp_info=[],
        port_table=[],
        poe_ports={},
    )


def test_device_is_hashable():
    device = _device()
    # A frozen dataclass with mutable list/dict fields generates a __hash__ that
    # raises TypeError; identity hashing must be used instead.
    assert hash(device) == hash(device)
    assert device in {device}
