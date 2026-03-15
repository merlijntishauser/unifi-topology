"""Compatibility facade for private UniFi cache helpers."""

__all__ = [
    "_acquire_cache_lock",
    "_cache_dir",
    "_cache_key",
    "_cache_lock",
    "_cache_lock_path",
    "_cache_ttl_seconds",
    "_device_lldp_value",
    "_device_uplink_fields",
    "_is_cache_dir_safe",
    "_load_cache",
    "_load_cache_with_age",
    "_release_cache_lock",
    "_save_cache",
    "_serialize_device_for_cache",
    "_serialize_devices_for_cache",
    "_serialize_lldp_entries",
    "_serialize_network_for_cache",
    "_serialize_network_table",
    "_serialize_networks_for_cache",
    "_serialize_port_entry",
    "_serialize_port_table",
    "_serialize_uplink",
]

from ._cache_serialize import _device_lldp_value as _device_lldp_value
from ._cache_serialize import _device_uplink_fields as _device_uplink_fields
from ._cache_serialize import _serialize_device_for_cache as _serialize_device_for_cache
from ._cache_serialize import _serialize_devices_for_cache as _serialize_devices_for_cache
from ._cache_serialize import _serialize_lldp_entries as _serialize_lldp_entries
from ._cache_serialize import _serialize_network_for_cache as _serialize_network_for_cache
from ._cache_serialize import _serialize_network_table as _serialize_network_table
from ._cache_serialize import _serialize_networks_for_cache as _serialize_networks_for_cache
from ._cache_serialize import _serialize_port_entry as _serialize_port_entry
from ._cache_serialize import _serialize_port_table as _serialize_port_table
from ._cache_serialize import _serialize_uplink as _serialize_uplink
from ._cache_store import _acquire_cache_lock as _acquire_cache_lock
from ._cache_store import _cache_dir as _cache_dir
from ._cache_store import _cache_key as _cache_key
from ._cache_store import _cache_lock as _cache_lock
from ._cache_store import _cache_lock_path as _cache_lock_path
from ._cache_store import _cache_ttl_seconds as _cache_ttl_seconds
from ._cache_store import _is_cache_dir_safe as _is_cache_dir_safe
from ._cache_store import _load_cache as _load_cache
from ._cache_store import _load_cache_with_age as _load_cache_with_age
from ._cache_store import _release_cache_lock as _release_cache_lock
from ._cache_store import _save_cache as _save_cache
