"""Public device and client classification API.

The implementation lives in ``_classify_client`` and ``_classify_device``; this
module re-exports only the public entry points.
"""

from ._classify_client import classify_client_type as classify_client_type
from ._classify_client import client_display_name as client_display_name
from ._classify_client import client_is_unifi as client_is_unifi
from ._classify_device import classify_device_type as classify_device_type

__all__ = [
    "classify_client_type",
    "classify_device_type",
    "client_display_name",
    "client_is_unifi",
]
