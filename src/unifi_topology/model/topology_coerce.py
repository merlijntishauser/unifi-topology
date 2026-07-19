"""Public device normalization API.

The implementation lives in ``_topology_device_coerce`` and
``_topology_port_coerce``; this module re-exports only the public entry points.
"""

from __future__ import annotations

from ._topology_device_coerce import coerce_device as coerce_device
from ._topology_device_coerce import normalize_devices as normalize_devices

__all__ = [
    "coerce_device",
    "normalize_devices",
]
