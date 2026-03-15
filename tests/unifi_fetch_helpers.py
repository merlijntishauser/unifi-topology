from __future__ import annotations

from unifi_topology.adapters.config import Config


def config() -> Config:
    return Config(
        url="https://example",
        site="default",
        user="user",
        password="pass",
        verify_ssl=True,
    )


def first_mapping(values: list[object]) -> dict[str, object]:
    value = values[0]
    assert isinstance(value, dict)
    return value
