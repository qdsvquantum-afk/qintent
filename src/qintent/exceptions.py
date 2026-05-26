from __future__ import annotations

from typing import Any


class QIntentError(Exception):
    """Base exception for the QIntent SDK."""


class QIntentHTTPError(QIntentError):
    """Raised when the API returns an HTTP error response."""

    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"QIntent API HTTP {status_code}: {payload}")


class QIntentAPIError(QIntentError):
    """Raised when a transport error prevents calling the API."""

