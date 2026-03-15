"""Compatibility facade for device and client classification helpers."""

__all__ = [
    "_classify_by_device_name",
    "_classify_by_name",
    "_classify_by_unifi_info",
    "_classify_by_vendor",
    "_classify_known_device_type",
    "_client_ucore_display_name",
    "_client_ucore_info",
    "_client_unifi_flag",
    "_client_vendor",
    "_normalized_device_type",
    "_ucore_has_device_info",
    "classify_client_type",
    "classify_device_type",
    "client_display_name",
    "client_is_unifi",
]

from ._classify_client import _classify_by_name as _classify_by_name
from ._classify_client import _classify_by_unifi_info as _classify_by_unifi_info
from ._classify_client import _classify_by_vendor as _classify_by_vendor
from ._classify_client import _client_ucore_display_name as _client_ucore_display_name
from ._classify_client import _client_ucore_info as _client_ucore_info
from ._classify_client import _client_unifi_flag as _client_unifi_flag
from ._classify_client import _client_vendor as _client_vendor
from ._classify_client import _ucore_has_device_info as _ucore_has_device_info
from ._classify_client import classify_client_type as classify_client_type
from ._classify_client import client_display_name as client_display_name
from ._classify_client import client_is_unifi as client_is_unifi
from ._classify_device import _classify_by_device_name as _classify_by_device_name
from ._classify_device import _classify_known_device_type as _classify_known_device_type
from ._classify_device import _normalized_device_type as _normalized_device_type
from ._classify_device import classify_device_type as classify_device_type
