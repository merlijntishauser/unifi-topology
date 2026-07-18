"""Configuration loading from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
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
    user: str | None = None
    password: str | None = field(default=None, repr=False)
    api_key: str | None = field(default=None, repr=False)
    verify_ssl: bool = True

    def __post_init__(self) -> None:
        has_api_key = bool(self.api_key)
        has_credentials = bool(self.user) and bool(self.password)
        if has_api_key == has_credentials:
            raise ValueError("Config requires exactly one of api_key or user+password")

    @classmethod
    def from_env(cls, *, env_file: str | Path | None = None) -> Config:
        if env_file:
            _load_env_file(env_file)
        url = _required_env("UNIFI_URL")
        site = _env_string("UNIFI_SITE", "default")
        verify_ssl = _parse_bool(os.environ.get("UNIFI_VERIFY_SSL"), default=True)
        api_key = _env_string("UNIFI_API_KEY") or None
        if api_key:
            return cls(url=url, site=site, api_key=api_key, verify_ssl=verify_ssl)
        user = _required_env("UNIFI_USER")
        password = _required_env("UNIFI_PASS")
        return cls(url=url, site=site, user=user, password=password, verify_ssl=verify_ssl)
