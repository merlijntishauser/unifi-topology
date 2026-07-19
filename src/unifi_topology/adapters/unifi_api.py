"""Thin UniFi controller HTTP client.

Replaces the ``unifi-controller-api`` external dependency with ~120 lines
of code covering the three GET endpoints this project actually uses.
"""

from __future__ import annotations

import logging
import warnings
from collections.abc import Callable

import requests
from urllib3.exceptions import InsecureRequestWarning

logger = logging.getLogger(__name__)


def _payload_meta(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {}
    meta = payload.get("meta", {})
    return meta if isinstance(meta, dict) else {}


def _auth_has_identity(payload: object) -> bool:
    return isinstance(payload, dict) and ("isSuperAdmin" in payload or "roles" in payload)


def _v2_payload_error(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    if not {"errorCode", "error"} & payload.keys():
        return None
    message = payload.get("message") or payload.get("error") or "unknown error"
    return str(message)


def _require_list_data(path: str, data: object) -> list[dict[str, object]]:
    if not isinstance(data, list):
        raise UnifiApiError(f"'data' field is not a list for {path}")
    return data


def _v2_payload_items(path: str, payload: object) -> list[dict[str, object]]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise UnifiApiError(f"Unexpected response format for {path}")
    if "data" in payload:
        return _require_list_data(path, payload["data"])
    error_message = _v2_payload_error(payload)
    if error_message is not None:
        raise UnifiApiError(f"Error response for {path}: {error_message}")
    return [payload]


def _find_policy_by_id(
    policies: list[dict[str, object]],
    policy_id: str,
) -> dict[str, object] | None:
    return next((policy for policy in policies if policy.get("_id") == policy_id), None)


def _missing_policy_ids(
    policy_pairs: tuple[tuple[str, dict[str, object] | None], ...],
) -> list[str]:
    return [policy_id for policy_id, policy in policy_pairs if policy is None]


def _require_policy_pair(
    policies: list[dict[str, object]],
    policy_id_a: str,
    policy_id_b: str,
) -> tuple[dict[str, object], dict[str, object]]:
    policy_a = _find_policy_by_id(policies, policy_id_a)
    policy_b = _find_policy_by_id(policies, policy_id_b)
    missing = _missing_policy_ids(((policy_id_a, policy_a), (policy_id_b, policy_b)))
    if missing:
        raise UnifiWriteError(f"Policy not found: {', '.join(missing)}")
    assert policy_a is not None
    assert policy_b is not None
    return policy_a, policy_b


def _swap_policy_indexes(
    policy_a: dict[str, object],
    policy_b: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    updated_a = dict(policy_a)
    updated_b = dict(policy_b)
    updated_a["index"], updated_b["index"] = updated_b["index"], updated_a["index"]
    return updated_a, updated_b


class UnifiError(Exception):
    """Base class for all unifi-topology errors."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


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
        username: str | None = None,
        password: str | None = None,
        *,
        api_key: str | None = None,
        is_udm_pro: bool = False,
        verify_ssl: bool = True,
        request_timeout: float | None = None,
    ) -> None:
        self._url = url.rstrip("/")
        self._username = username
        self._password = password
        self._api_key = api_key
        self._is_udm_pro = is_udm_pro
        self._verify_ssl = verify_ssl
        self._request_timeout = request_timeout if request_timeout and request_timeout > 0 else None
        self._api_base = f"{self._url}/proxy/network" if is_udm_pro else self._url
        self._session = requests.Session()
        self._csrf_token: str | None = None

        self._initialize_auth()

    def _initialize_auth(self) -> None:
        if self._api_key:
            self._session.headers["X-API-KEY"] = self._api_key
            return
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
        if self._verify_ssl:
            return request_method(url, **kwargs)
        # Scope the insecure-request warning suppression to this call instead of
        # disabling it process-wide for the host application.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=InsecureRequestWarning)
            return request_method(url, **kwargs)

    def _request_with_reauth(
        self,
        method: str,
        url: str,
        *,
        payload: dict[str, object] | None = None,
        headers_factory: Callable[[], dict[str, str] | None] | None = None,
    ) -> requests.Response:
        response = self._safe_request(
            method,
            url,
            payload=payload,
            headers=headers_factory() if headers_factory else None,
        )
        if response.status_code == 401:
            if self._api_key:
                raise UnifiAuthError("API key rejected (HTTP 401)", status_code=401)
            logger.debug("Got 401 on %s, re-authenticating", method)
            self._authenticate()
            response = self._safe_request(
                method,
                url,
                payload=payload,
                headers=headers_factory() if headers_factory else None,
            )
        return response

    def _safe_request(
        self,
        method: str,
        url: str,
        *,
        payload: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        try:
            return self._request(method, url, payload=payload, headers=headers)
        except requests.RequestException as exc:
            raise UnifiApiError(f"{method} {url} failed: {exc}") from exc

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
        if (
            isinstance(payload, dict)
            and "code" in payload
            and "message" in payload
            and "meta" not in payload
        ):
            return f"{payload['code']}: {payload['message']}"
        return None

    @staticmethod
    def _auth_succeeded(payload: object) -> bool:
        return _payload_meta(payload).get("rc") == "ok" or _auth_has_identity(payload)

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
                raise UnifiAuthError(
                    f"HTTP {response.status_code}: {detail}", status_code=response.status_code
                )
            raise UnifiAuthError(
                f"Authentication failed (HTTP {response.status_code})",
                status_code=response.status_code,
            )
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
            raise UnifiApiError(
                f"GET {path} failed (HTTP {response.status_code})",
                status_code=response.status_code,
            )

        payload = self._parse_json(
            response,
            error_type=UnifiApiError,
            error_message=f"Non-JSON response for {path}",
        )

        if not isinstance(payload, dict) or "data" not in payload:
            raise UnifiApiError(f"Missing 'data' field in response for {path}")

        return _require_list_data(path, payload["data"])

    @staticmethod
    def _parse_v2_list_payload(path: str, payload: object) -> list[dict[str, object]]:
        return _v2_payload_items(path, payload)

    def _get_v2(self, path: str) -> list[dict[str, object]]:
        """GET for V2/Integration API endpoints.

        These endpoints may return a plain list or a different envelope.
        Handles both cases.
        """
        url = f"{self._api_base}{path}"
        response = self._request_with_reauth("GET", url)

        if not response.ok:
            raise UnifiApiError(
                f"GET {path} failed (HTTP {response.status_code})",
                status_code=response.status_code,
            )

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
            raise UnifiWriteError(
                f"PUT {path} failed (HTTP {response.status_code}): {detail}",
                status_code=response.status_code,
            )

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
        """Swap the index (priority) of two firewall policies.

        The two PUTs are not transactional. If the second fails, the first is
        rolled back so both policies keep their original indexes. A failed
        rollback leaves the policies with duplicate indexes and is reported.
        """
        path = f"/v2/api/site/{site}/firewall-policies"
        all_policies = self._get_v2(path)
        policy_a, policy_b = _require_policy_pair(all_policies, policy_id_a, policy_id_b)
        updated_a, updated_b = _swap_policy_indexes(policy_a, policy_b)
        self._put_v2(f"{path}/{policy_id_a}", updated_a)
        try:
            self._put_v2(f"{path}/{policy_id_b}", updated_b)
        except UnifiError as exc:
            self._rollback_policy_index(path, policy_id_a, policy_a, cause=exc)

    def _rollback_policy_index(
        self,
        path: str,
        policy_id: str,
        original: dict[str, object],
        *,
        cause: UnifiError,
    ) -> None:
        try:
            self._put_v2(f"{path}/{policy_id}", original)
        except UnifiError as rollback_exc:
            raise UnifiWriteError(
                f"Policy swap failed and rollback of {policy_id} also failed; "
                f"policies may have duplicate indexes: {rollback_exc}"
            ) from cause
        raise UnifiWriteError(f"Policy swap failed and was rolled back: {cause}") from cause
