from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any, Mapping, Sequence

import requests

from .exceptions import QIntentAPIError, QIntentHTTPError


DEFAULT_API_URL = "https://api.qdsv.cloud/api"
PRIVATE_NODE_UNAVAILABLE_MESSAGE = (
    "Private QDSV node temporarily unavailable. It may be offline, reserved for "
    "private processing, or busy. Try again later or use QIntentClient() for "
    "public cloud examples."
)


class QIntentClient:
    """Lightweight client for QIntent public API endpoints.

    The SDK does not embed the QDSV runtime. It sends QIntent source to a QDSV
    API and returns the compiled or executed response.
    """

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        *,
        timeout: float = 30.0,
        license_key: str | None = None,
        sdk_name: str = "qdsv-qintent",
    ) -> None:
        self.api_url = self._normalize_api_url(
            api_url or os.getenv("QINTENT_API_URL") or os.getenv("QDSV_API_URL") or DEFAULT_API_URL
        )
        self.api_key = api_key or os.getenv("QINTENT_API_KEY") or os.getenv("QDSV_API_KEY")
        self.license_key = license_key or os.getenv("QDSV_LICENSE_KEY")
        self.timeout = timeout
        self.sdk_name = sdk_name
        self._private_node = self._looks_like_private_node(self.api_url)

    @classmethod
    def local(
        cls,
        *,
        api_url: str = "http://localhost:18080/api",
        api_key: str | None = None,
        timeout: float = 30.0,
        license_key: str | None = None,
    ) -> "QIntentClient":
        """Create a client for the local Docker/private demo API."""

        return cls(api_url=api_url, api_key=api_key, timeout=timeout, license_key=license_key)

    @staticmethod
    def _normalize_api_url(value: str) -> str:
        clean = str(value or "").strip().rstrip("/")
        if not clean:
            return DEFAULT_API_URL
        return clean if clean.lower().endswith("/api") else f"{clean}/api"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "x-sdk-name": self.sdk_name,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.license_key:
            headers["x-license-key"] = self.license_key
        return headers

    @staticmethod
    def _looks_like_private_node(api_url: str) -> bool:
        clean = str(api_url or "").lower()
        return (
            "localhost" in clean
            or "127.0.0.1" in clean
            or "qintent-local.qdsv.cloud" in clean
            or "qruba.site" in clean
        )

    def _request(self, method: str, path: str, *, json: Mapping[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.api_url}{path}"
        request_kwargs: dict[str, Any] = {
            "headers": self._headers(),
            "timeout": self.timeout,
        }
        if json is not None:
            request_kwargs["json"] = dict(json)
        try:
            response = requests.request(
                method,
                url,
                **request_kwargs,
            )
        except requests.RequestException as exc:
            if self._private_node:
                raise QIntentAPIError(PRIVATE_NODE_UNAVAILABLE_MESSAGE) from exc
            raise QIntentAPIError(str(exc)) from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {"status": "ERROR", "message": response.text}

        if not response.ok:
            raise QIntentHTTPError(response.status_code, payload)
        if not isinstance(payload, dict):
            raise QIntentAPIError(f"Unexpected API response type: {type(payload).__name__}")
        return payload

    def spec(self) -> dict[str, Any]:
        return self._request("GET", "/qintent/spec")

    def examples(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/qintent/examples")
        examples = payload.get("examples", [])
        return examples if isinstance(examples, list) else []

    def validate(
        self,
        source: str,
        *,
        rows: Sequence[Mapping[str, Any]] | None = None,
        backend: str = "quest",
        backend_mode: str | None = None,
        shots: int = 256,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/qintent/validate",
            json=self._payload(source, rows=rows, backend=backend, backend_mode=backend_mode, shots=shots),
        )

    def compile(
        self,
        source: str,
        *,
        rows: Sequence[Mapping[str, Any]] | None = None,
        backend: str = "quest",
        backend_mode: str | None = None,
        shots: int = 256,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/qintent/compile",
            json=self._payload(source, rows=rows, backend=backend, backend_mode=backend_mode, shots=shots),
        )

    def explain(
        self,
        source: str,
        *,
        rows: Sequence[Mapping[str, Any]] | None = None,
        backend: str = "quest",
        backend_mode: str | None = None,
        shots: int = 256,
    ) -> dict[str, Any]:
        """Return a Semantic Execution Passport for the declared QIntent source."""

        return self._request(
            "POST",
            "/qintent/explain",
            json=self._payload(source, rows=rows, backend=backend, backend_mode=backend_mode, shots=shots),
        )

    def run(
        self,
        source: str,
        *,
        rows: Sequence[Mapping[str, Any]] | None = None,
        backend: str = "quest",
        backend_mode: str | None = None,
        shots: int = 256,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/qintent/execute",
            json=self._payload(source, rows=rows, backend=backend, backend_mode=backend_mode, shots=shots),
        )

    execute = run

    @staticmethod
    def read_csv(path: str | Path) -> list[dict[str, Any]]:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    @staticmethod
    def _payload(
        source: str,
        *,
        rows: Sequence[Mapping[str, Any]] | None,
        backend: str,
        backend_mode: str | None,
        shots: int,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": source,
            "backend": backend,
            "shots": shots,
        }
        if backend_mode:
            payload["backend_mode"] = backend_mode
        if rows is not None:
            payload["rows"] = [dict(row) for row in rows]
        return payload
