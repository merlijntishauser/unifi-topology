"""Change-event and diff-result types for topology comparison."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TopologyChangeEvent:
    """A single change detected between two topology snapshots."""

    event_type: str
    """One of: node_added, node_removed, node_changed, edge_added, edge_removed, edge_changed"""

    entity_type: str
    """'device', 'client', or 'edge'"""

    identifier: str
    """MAC address - stable identifier across renames"""

    name: str | None
    """Human-readable name (from newer topology if changed)"""

    description: str
    """Human-readable message for notifications"""

    details: dict[str, Any] = field(default_factory=dict)
    """Event-specific payload"""

    timestamp: str | None = None
    """ISO timestamp if available"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "identifier": self.identifier,
            "name": self.name,
            "description": self.description,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class TopologyDiff:
    """Result of comparing two topology snapshots."""

    events: list[TopologyChangeEvent] = field(default_factory=list)
    """All detected changes"""

    old_timestamp: str | None = None
    """Timestamp from old topology metadata"""

    new_timestamp: str | None = None
    """Timestamp from new topology metadata"""

    summary: str = ""
    """Human-readable summary like '3 devices added, 1 removed'"""

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "events": [e.to_dict() for e in self.events],
            "old_timestamp": self.old_timestamp,
            "new_timestamp": self.new_timestamp,
            "summary": self.summary,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def filter(
        self,
        event_types: set[str] | None = None,
        entity_types: set[str] | None = None,
    ) -> TopologyDiff:
        """Return filtered diff with only matching events."""
        filtered = [
            event
            for event in self.events
            if _event_matches(event, event_types=event_types, entity_types=entity_types)
        ]
        return TopologyDiff(
            events=filtered,
            old_timestamp=self.old_timestamp,
            new_timestamp=self.new_timestamp,
            summary=_build_summary(filtered),
        )


def _event_matches(
    event: TopologyChangeEvent,
    *,
    event_types: set[str] | None,
    entity_types: set[str] | None,
) -> bool:
    if event_types is not None and event.event_type not in event_types:
        return False
    if entity_types is not None and event.entity_type not in entity_types:
        return False
    return True


def _pluralize(count: int, singular: str) -> str:
    """Return 'N item' or 'N items' based on count."""
    return f"{count} {singular}{'s' if count != 1 else ''}"


def _add_count_part(parts: list[str], count: int, noun: str, verb: str) -> None:
    """Add a count part to the summary list if count > 0."""
    if count:
        parts.append(f"{_pluralize(count, noun)} {verb}")


def _build_summary(events: list[TopologyChangeEvent]) -> str:
    """Build a human-readable summary of changes."""
    counts: dict[str, int] = {}
    for event in events:
        key = f"{event.entity_type}_{event.event_type}"
        counts[key] = counts.get(key, 0) + 1

    parts: list[str] = []

    # Devices
    _add_count_part(parts, counts.get("device_node_added", 0), "device", "added")
    _add_count_part(parts, counts.get("device_node_removed", 0), "device", "removed")
    _add_count_part(parts, counts.get("device_node_changed", 0), "device", "changed")

    # Clients
    _add_count_part(parts, counts.get("client_node_added", 0), "client", "added")
    _add_count_part(parts, counts.get("client_node_removed", 0), "client", "removed")
    _add_count_part(parts, counts.get("client_node_changed", 0), "client", "changed")

    # Edges
    _add_count_part(parts, counts.get("edge_edge_added", 0), "connection", "added")
    _add_count_part(parts, counts.get("edge_edge_removed", 0), "connection", "removed")
    _add_count_part(parts, counts.get("edge_edge_changed", 0), "connection", "changed")

    return ", ".join(parts) if parts else "No changes"
