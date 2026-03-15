"""Private helpers for reading raw dict-or-object payloads."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .helpers import as_bool, get_field


def _coerce_int(value: object | None) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _is_record_like(value: object | None) -> bool:
    return value is not None and not isinstance(
        value, str | bytes | int | float | bool | list | tuple | set | frozenset
    )


@dataclass(frozen=True)
class RawRecord:
    """Read fields from raw API payloads without caring about dict vs object shape."""

    source: object

    def get(self, name: str) -> object | None:
        return get_field(self.source, name)

    def first(self, *names: str) -> object | None:
        for name in names:
            value = self.get(name)
            if value is not None:
                return value
        return None

    def present(
        self,
        *names: str,
        skip_values: tuple[object, ...] = (None,),
    ) -> object | None:
        for name in names:
            value = self.get(name)
            if value not in skip_values:
                return value
        return None

    def text(self, *names: str) -> str | None:
        value = self.first(*names)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    def integer(self, *names: str) -> int | None:
        for name in names:
            parsed = _coerce_int(self.get(name))
            if parsed is not None:
                return parsed
        return None

    def optional_bool(self, *names: str) -> bool | None:
        value = self.first(*names)
        if value is None:
            return None
        return as_bool(value)


def nested_records(source: object, *names: str) -> Iterator[RawRecord]:
    """Yield nested raw records when a field contains another record-like object."""
    record = RawRecord(source)
    for name in names:
        value = record.get(name)
        if _is_record_like(value):
            yield RawRecord(value)
