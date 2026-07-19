"""Generic entity-comparison machinery for topology diffing."""

from __future__ import annotations

from collections.abc import Callable, Hashable
from dataclasses import dataclass
from typing import Any

from ._diff_events import TopologyChangeEvent


def _compare_properties(
    old_props: dict[str, Any],
    new_props: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Compare two property dicts and return changes."""
    changes: dict[str, dict[str, Any]] = {}
    all_keys = set(old_props.keys()) | set(new_props.keys())
    for key in all_keys:
        old_val = old_props.get(key)
        new_val = new_props.get(key)
        if old_val != new_val:
            changes[key] = {"old": old_val, "new": new_val}
    return changes


def _single_change(
    changes: dict[str, dict[str, Any]],
) -> tuple[str, Any, Any] | None:
    if len(changes) != 1:
        return None
    key, values = next(iter(changes.items()))
    return key, values.get("old"), values.get("new")


@dataclass(frozen=True)
class EntityCompareSpec[T]:
    """Specification for comparing a particular entity type."""

    entity_type: str
    event_prefix: str
    key: Callable[[T], Hashable | None]
    sort_key: Callable[[Any], Any]
    name: Callable[[T], str | None]
    identifier: Callable[[T, Hashable], str]
    properties: Callable[[T], dict[str, Any]]
    serialize: Callable[[T], dict[str, Any]]
    describe_added: Callable[[T], str]
    describe_removed: Callable[[T], str]
    describe_changed: Callable[[T, dict[str, dict[str, Any]]], str]


def _build_entity_map[T](
    items: list[T], key_fn: Callable[[T], Hashable | None]
) -> dict[Hashable, T]:
    """Build a lookup map from items, skipping any whose key is None."""
    return {k: item for item in items if (k := key_fn(item)) is not None}


def _compare_entities[T](
    old_items: list[T],
    new_items: list[T],
    spec: EntityCompareSpec[T],
    events: list[TopologyChangeEvent],
    timestamp: str,
) -> None:
    """Compare two entity lists and emit change events."""
    old_map = _build_entity_map(old_items, spec.key)
    new_map = _build_entity_map(new_items, spec.key)
    old_keys = set(old_map)
    new_keys = set(new_map)

    for key in sorted(new_keys - old_keys, key=spec.sort_key):
        item = new_map[key]
        events.append(
            TopologyChangeEvent(
                event_type=f"{spec.event_prefix}_added",
                entity_type=spec.entity_type,
                identifier=spec.identifier(item, key),
                name=spec.name(item),
                description=spec.describe_added(item),
                details=spec.serialize(item),
                timestamp=timestamp,
            )
        )

    for key in sorted(old_keys - new_keys, key=spec.sort_key):
        item = old_map[key]
        events.append(
            TopologyChangeEvent(
                event_type=f"{spec.event_prefix}_removed",
                entity_type=spec.entity_type,
                identifier=spec.identifier(item, key),
                name=spec.name(item),
                description=spec.describe_removed(item),
                details=spec.serialize(item),
                timestamp=timestamp,
            )
        )

    for key in sorted(old_keys & new_keys, key=spec.sort_key):
        new_item = new_map[key]
        changes = _compare_properties(spec.properties(old_map[key]), spec.properties(new_item))
        if changes:
            events.append(
                TopologyChangeEvent(
                    event_type=f"{spec.event_prefix}_changed",
                    entity_type=spec.entity_type,
                    identifier=spec.identifier(new_item, key),
                    name=spec.name(new_item),
                    description=spec.describe_changed(new_item, changes),
                    details={"changes": changes},
                    timestamp=timestamp,
                )
            )


def _compare_optional_entities[T](
    old_items: list[T] | None,
    new_items: list[T] | None,
    spec: EntityCompareSpec[T],
    events: list[TopologyChangeEvent],
    timestamp: str,
) -> None:
    if old_items is None or new_items is None:
        return
    _compare_entities(old_items, new_items, spec, events, timestamp)
