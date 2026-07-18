"""Top-level fw_version must survive client snapshot round-trip."""

from unifi_topology.model.inventory import build_client_inventory
from unifi_topology.model.snapshot import client_from_dict, client_to_dict


def test_top_level_fw_version_survives_round_trip():
    client = {
        "mac": "cc:dd:ee:ff:00:11",
        "name": "Camera",
        "ip": "10.0.0.5",
        "is_wired": True,
        "fw_version": "4.1.2",
    }
    restored = client_from_dict(client_to_dict(client))
    inventory = build_client_inventory([restored])
    assert inventory[0].firmware == "4.1.2"
