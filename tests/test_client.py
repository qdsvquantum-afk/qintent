from __future__ import annotations

import pytest
import requests

from qintent import QIntentClient
from qintent.exceptions import QIntentAPIError, QIntentHTTPError


def test_normalizes_api_url() -> None:
    assert QIntentClient("https://api.qdsv.cloud").api_url == "https://api.qdsv.cloud/api"
    assert QIntentClient("https://api.qdsv.cloud/api").api_url == "https://api.qdsv.cloud/api"
    assert QIntentClient().api_url == "https://api.qdsv.cloud/api"
    assert QIntentClient.local().api_url == "http://localhost:18080/api"


def test_payload_includes_rows_and_backend() -> None:
    payload = QIntentClient._payload(
        'find_rows("candidate_index").where("score", ">=", 850)',
        rows=[{"candidate_index": 0, "score": 900}],
        backend="quest",
        backend_mode=None,
        shots=256,
    )

    assert payload["backend"] == "quest"
    assert payload["shots"] == 256
    assert payload["rows"] == [{"candidate_index": 0, "score": 900}]


def test_explain_calls_public_explain_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {}

    class FakeResponse:
        ok = True
        status_code = 200

        @staticmethod
        def json():
            return {
                "status": "SUCCESS",
                "product": "QIntent Explain",
                "semantic_execution_passport": {
                    "execution_plan": {"selected_backend": "quest", "uses_circuits": False}
                },
            }

    def fake_request(method, url, **kwargs):
        calls["method"] = method
        calls["url"] = url
        calls["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("qintent.client.requests.request", fake_request)

    result = QIntentClient().explain(
        'find_rows("candidate_index").where("score", ">=", 850)',
        rows=[{"candidate_index": 0, "score": 900}],
    )

    assert result["product"] == "QIntent Explain"
    assert calls["method"] == "POST"
    assert calls["url"].endswith("/qintent/explain")
    assert calls["kwargs"]["json"]["backend"] == "quest"
    assert calls["kwargs"]["json"]["rows"] == [{"candidate_index": 0, "score": 900}]


def test_api_key_is_sent_as_header_and_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {}

    class FakeResponse:
        ok = True
        status_code = 200

        @staticmethod
        def json():
            return {"status": "SUCCESS"}

    def fake_request(method, url, **kwargs):
        calls["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("qintent.client.requests.request", fake_request)

    QIntentClient(api_key="qdsvi_demo_key").spec()

    headers = calls["kwargs"]["headers"]
    assert headers["x-api-key"] == "qdsvi_demo_key"
    assert headers["Authorization"] == "Bearer qdsvi_demo_key"


def test_import_surface() -> None:
    import qintent

    assert qintent.QIntentClient is QIntentClient


def test_get_request_does_not_send_empty_json_body(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {}

    class FakeResponse:
        ok = True
        status_code = 200

        @staticmethod
        def json():
            return {"status": "SUCCESS"}

    def fake_request(method, url, **kwargs):
        calls["method"] = method
        calls["url"] = url
        calls["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("qintent.client.requests.request", fake_request)

    result = QIntentClient("https://api.qdsv.cloud/api").spec()

    assert result["status"] == "SUCCESS"
    assert calls["method"] == "GET"
    assert "json" not in calls["kwargs"]


def test_private_node_transport_error_is_user_friendly(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(method, url, **kwargs):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr("qintent.client.requests.request", fake_request)

    with pytest.raises(QIntentAPIError) as exc:
        QIntentClient.local().spec()

    assert "Private QDSV node temporarily unavailable" in str(exc.value)
    assert "public cloud examples" in str(exc.value)


def test_public_cloud_transport_error_keeps_original_message(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(method, url, **kwargs):
        raise requests.Timeout("cloud timeout")

    monkeypatch.setattr("qintent.client.requests.request", fake_request)

    with pytest.raises(QIntentAPIError) as exc:
        QIntentClient().spec()

    assert "cloud timeout" in str(exc.value)
    assert "Private QDSV node temporarily unavailable" not in str(exc.value)


def test_private_node_http_error_is_not_hidden(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        ok = False
        status_code = 429

        @staticmethod
        def json():
            return {"detail": {"error_code": "E_RATE_LIMIT", "message": "Rate limit"}}

    def fake_request(method, url, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("qintent.client.requests.request", fake_request)

    with pytest.raises(QIntentHTTPError) as exc:
        QIntentClient.local().spec()

    assert exc.value.status_code == 429
    assert exc.value.payload["detail"]["error_code"] == "E_RATE_LIMIT"
