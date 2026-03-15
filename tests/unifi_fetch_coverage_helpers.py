from __future__ import annotations

import json
import time
from pathlib import Path

from unifi_topology.adapters import unifi
from unifi_topology.adapters.config import Config

CONFIG = Config(
    url="https://example",
    site="default",
    user="user",
    password="pass",
    verify_ssl=True,
)


def write_cache(path: Path, data: list[object], *, age_seconds: float = 0.0) -> None:
    payload = {"timestamp": time.time() - age_seconds, "data": data}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")


class StubClient:
    def __init__(
        self,
        *,
        devices: list | None = None,
        clients: list | None = None,
        networks: list | None = None,
    ):
        self._devices = devices or []
        self._clients = clients or []
        self._networks = networks or []

    def get_devices(self, site: str, *, detailed: bool = False) -> list:
        return self._devices

    def get_clients(self, site: str) -> list:
        return self._clients

    def get_networkconf(self, site: str) -> list:
        return self._networks


def patch_client(monkeypatch, client: object) -> None:
    monkeypatch.setattr(unifi, "_create_client", lambda *_a, **_k: client)
