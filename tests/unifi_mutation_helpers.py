"""Shared helpers for UniFi mutation tests."""

from unifi_topology.adapters.config import Config


def make_config() -> Config:
    return Config(
        url="https://example",
        site="default",
        user="user",
        password="pass",
        verify_ssl=True,
    )
