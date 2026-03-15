"""Configuration loading from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..paths import resolve_env_file


def _parse_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _load_env_file(env_file: str | Path) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        raise ValueError("python-dotenv required for --env-file") from None
    env_path = resolve_env_file(env_file)
    load_dotenv(dotenv_path=env_path)


def _env_string(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _required_env(name: str) -> str:
    value = _env_string(name)
    if not value:
        raise ValueError(f"{name} is required")
    return value


@dataclass(frozen=True)
class Config:
    url: str
    site: str
    user: str
    password: str
    verify_ssl: bool

    @classmethod
    def from_env(cls, *, env_file: str | Path | None = None) -> Config:
        if env_file:
            _load_env_file(env_file)
        url = _required_env("UNIFI_URL")
        site = _env_string("UNIFI_SITE", "default")
        user = _required_env("UNIFI_USER")
        password = _required_env("UNIFI_PASS")
        verify_ssl = _parse_bool(os.environ.get("UNIFI_VERIFY_SSL"), default=True)

        return cls(url=url, site=site, user=user, password=password, verify_ssl=verify_ssl)
