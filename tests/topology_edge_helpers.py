from __future__ import annotations


class DummyDevice:
    def __init__(self, name, mac, lldp_info, port_table=None):
        self.name = name
        self.mac = mac
        self.lldp_info = lldp_info
        self.port_table = port_table or []
        self.model_name = ""
        self.ip = ""
        self.type = ""


def make_device_with_uplink_no_lldp():
    class MissingLldpWithUplink:
        name = "Device"
        model_name = ""
        mac = "aa"
        ip = ""
        type = ""
        lldp_info = None
        lldp = None
        uplink = {"uplink_mac": "bb", "uplink_device_name": "Gateway", "uplink_remote_port": 1}
        port_table = []

    return MissingLldpWithUplink()
