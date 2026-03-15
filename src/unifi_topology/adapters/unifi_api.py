"""Thin UniFi controller HTTP client.

Replaces the ``unifi-controller-api`` external dependency with ~120 lines
of code covering the three GET endpoints this project actually uses.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import requests

logger = logging.getLogger(__name__)


class UnifiError(Exception):
    """Base class for all unifi-topology errors."""


class UnifiAuthError(UnifiError):
    """Authentication with the UniFi controller failed."""


class UnifiApiError(UnifiError):
    """An API request to the UniFi controller failed."""


class UnifiWriteError(UnifiApiError):
    """A write (mutation) operation to the UniFi controller failed."""


class UnifiClient:
    """Minimal UniFi controller client.

    Supports both UDM Pro (UniFi OS) and legacy controller authentication.
    All data methods return ``list[dict[str, object]]``.
    """

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        *,
        is_udm_pro: bool = False,
        verify_ssl: bool = True,
        request_timeout: float | None = None,
    ) -> None:
        self._url = url.rstrip("/")
        self._username = username
        self._password = password
        self._is_udm_pro = is_udm_pro
        self._verify_ssl = verify_ssl
        self._request_timeout = request_timeout if request_timeout and request_timeout > 0 else None
        self._api_base = f"{self._url}/proxy/network" if is_udm_pro else self._url
        self._session = requests.Session()
        self._csrf_token: str | None = None

        if not verify_ssl:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self._authenticate()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        url: str,
        *,
        payload: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        request_method = getattr(self._session, method.lower())
        kwargs: dict[str, object] = {"verify": self._verify_ssl}
        if payload is not None:
            kwargs["json"] = payload
        if headers is not None:
            kwargs["headers"] = headers
        if self._request_timeout is not None:
            kwargs["timeout"] = self._request_timeout
        return request_method(url, **kwargs)

    def _request_with_reauth(
        self,
        method: str,
        url: str,
        *,
        payload: dict[str, object] | None = None,
        headers_factory: Callable[[], dict[str, str] | None] | None = None,
    ) -> requests.Response:
        response = self._request(
            method,
            url,
            payload=payload,
            headers=headers_factory() if headers_factory else None,
        )
        if response.status_code == 401:
            logger.debug("Got 401 on %s, re-authenticating", method)
            self._authenticate()
            response = self._request(
                method,
                url,
                payload=payload,
                headers=headers_factory() if headers_factory else None,
            )
        return response

    @staticmethod
    def _parse_json(
        response: requests.Response,
        *,
        error_type: type[UnifiError],
        error_message: str,
    ) -> object:
        try:
            return response.json()
        except ValueError as exc:
            raise error_type(error_message) from exc

    @staticmethod
    def _error_detail(payload: object) -> str | None:
        if not isinstance(payload, dict):
            return None
        for key in ("message", "error", "code", "errorCode"):
            value = payload.get(key)
            if value is not None:
                return str(value)
        return None

    @staticmethod
    def _auth_payload_error(payload: object) -> str | None:
        if isinstance(payload, dict) and "code" in payload and "message" in payload and "meta" not in payload:
            return f"{payload['code']}: {payload['message']}"
        return None

    @staticmethod
    def _auth_succeeded(payload: object) -> bool:
        meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
        if isinstance(meta, dict) and meta.get("rc") == "ok":
            return True
        return isinstance(payload, dict) and ("isSuperAdmin" in payload or "roles" in payload)

    def _csrf_headers(self) -> dict[str, str]:
        if not self._csrf_token:
            return {}
        return {"X-CSRF-Token": self._csrf_token}

    def _authenticate(self) -> None:
        login_path = "/api/auth/login" if self._is_udm_pro else "/api/login"
        login_url = f"{self._url}{login_path}"
        try:
            response = self._request(
                "POST",
                login_url,
                payload={"username": self._username, "password": self._password},
            )
        except requests.RequestException as exc:
            raise UnifiAuthError(f"Login request failed: {exc}") from exc
        self._validate_auth_response(response)
        self._csrf_token = response.headers.get("X-CSRF-Token")

    def _validate_auth_response(self, response: requests.Response) -> None:
        data = self._parse_json(
            response,
            error_type=UnifiAuthError,
            error_message=f"Non-JSON auth response (HTTP {response.status_code})",
        )
        if not response.ok:
            detail = self._error_detail(data)
            if detail:
                raise UnifiAuthError(f"HTTP {response.status_code}: {detail}")
            raise UnifiAuthError(f"Authentication failed (HTTP {response.status_code})")
        payload_error = self._auth_payload_error(data)
        if payload_error is not None:
            raise UnifiAuthError(payload_error)
        if self._auth_succeeded(data):
            return
        raise UnifiAuthError(f"Unknown auth response format (HTTP {response.status_code})")

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------

    def _get(self, path: str) -> list[dict[str, object]]:
        url = f"{self._api_base}{path}"
        response = self._request_with_reauth("GET", url)

        if not response.ok:
            raise UnifiApiError(f"GET {path} failed (HTTP {response.status_code})")

        payload = self._parse_json(
            response,
            error_type=UnifiApiError,
            error_message=f"Non-JSON response for {path}",
        )

        if not isinstance(payload, dict) or "data" not in payload:
            raise UnifiApiError(f"Missing 'data' field in response for {path}")

        return payload["data"]

    @staticmethod
    def _parse_v2_list_payload(path: str, payload: object) -> list[dict[str, object]]:
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            raise UnifiApiError(f"Unexpected response format for {path}")
        if "data" in payload:
            return payload["data"]
        if "errorCode" in payload or "error" in payload:
            message = payload.get("message") or payload.get("error") or "unknown error"
            raise UnifiApiError(f"Error response for {path}: {message}")
        return [payload]

    def _get_v2(self, path: str) -> list[dict[str, object]]:
        """GET for V2/Integration API endpoints.

        These endpoints may return a plain list or a different envelope.
        Handles both cases.
        """
        url = f"{self._api_base}{path}"
        response = self._request_with_reauth("GET", url)

        if not response.ok:
            raise UnifiApiError(f"GET {path} failed (HTTP {response.status_code})")

        payload = self._parse_json(
            response,
            error_type=UnifiApiError,
            error_message=f"Non-JSON response for {path}",
        )
        return self._parse_v2_list_payload(path, payload)

    def get_devices(self, site: str, *, detailed: bool = False) -> list[dict[str, object]]:
        endpoint = "stat/device" if detailed else "stat/device-basic"
        return self._get(f"/api/s/{site}/{endpoint}")

    def get_clients(self, site: str) -> list[dict[str, object]]:
        return self._get(f"/api/s/{site}/stat/sta")

    def get_networkconf(self, site: str) -> list[dict[str, object]]:
        return self._get(f"/api/s/{site}/rest/networkconf")

    def get_firewall_zones(self, site: str) -> list[dict[str, object]]:
        """Fetch firewall zone definitions (V2 API)."""
        return self._get_v2(f"/v2/api/site/{site}/firewall/zone")

    def get_firewall_policies(self, site: str) -> list[dict[str, object]]:
        """Fetch zone-based firewall policies (V2 API)."""
        return self._get_v2(f"/v2/api/site/{site}/firewall-policies")

    def get_firewall_groups(self, site: str) -> list[dict[str, object]]:
        """Fetch firewall address/port groups (classic API)."""
        return self._get(f"/api/s/{site}/rest/firewallgroup")

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def _put_v2(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        """PUT to a V2/Integration API endpoint."""
        url = f"{self._api_base}{path}"
        response = self._request_with_reauth(
            "PUT",
            url,
            payload=payload,
            headers_factory=self._csrf_headers,
        )

        if not response.ok:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise UnifiWriteError(f"PUT {path} failed (HTTP {response.status_code}): {detail}")

        result = self._parse_json(
            response,
            error_type=UnifiWriteError,
            error_message=f"Non-JSON response for PUT {path}",
        )

        if isinstance(result, dict):
            return result
        raise UnifiWriteError(f"Unexpected response format for PUT {path}")

    def _get_v2_single(self, path: str) -> dict[str, object]:
        """GET a single resource from a V2 API endpoint."""
        results = self._get_v2(path)
        if len(results) != 1:
            raise UnifiApiError(f"Expected single resource at {path}, got {len(results)}")
        return results[0]

    def update_firewall_policy(
        self, site: str, policy_id: str, updates: dict[str, object]
    ) -> dict[str, object]:
        """Fetch a policy, apply updates, and PUT it back. Returns the updated policy."""
        path = f"/v2/api/site/{site}/firewall-policies/{policy_id}"
        policy = self._get_v2_single(path)
        policy.update(updates)
        return self._put_v2(path, policy)

    def swap_firewall_policy_order(self, site: str, policy_id_a: str, policy_id_b: str) -> None:
        """Swap the index (priority) of two firewall policies."""
        path = f"/v2/api/site/{site}/firewall-policies"
        all_policies = self._get_v2(path)
        policy_a = next((p for p in all_policies if p.get("_id") == policy_id_a), None)
        policy_b = next((p for p in all_policies if p.get("_id") == policy_id_b), None)
        if policy_a is None or policy_b is None:
            missing = [
                pid for pid, p in [(policy_id_a, policy_a), (policy_id_b, policy_b)] if p is None
            ]
            raise UnifiWriteError(f"Policy not found: {', '.join(missing)}")
        idx_a = policy_a["index"]
        idx_b = policy_b["index"]
        policy_a["index"] = idx_b
        policy_b["index"] = idx_a
        self._put_v2(f"{path}/{policy_id_a}", policy_a)
        self._put_v2(f"{path}/{policy_id_b}", policy_b)
