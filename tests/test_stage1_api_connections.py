import io
import json
import urllib.error

import pytest

from scripts.test_stage1_api_connections import PROVIDERS, error_category, request_spec, send_once, summarize_response
from scripts import test_stage1_api_connections as connections


@pytest.mark.parametrize("provider", PROVIDERS)
def test_keys_only_go_in_headers_not_url_or_body(provider):
    secret = "fake-test-secret-value"
    url, headers, body = request_spec(provider, secret)
    assert secret not in url
    assert secret not in json.dumps(body)
    assert any(secret in value for value in headers.values())
    assert "Reply with exactly OK." in json.dumps(body)


def test_openai_test_disables_storage_and_caps_output():
    _, _, body = request_spec("openai", "fake")
    assert body["store"] is False
    assert body["max_output_tokens"] == 64
    assert body["reasoning"] == {"effort": "none"}


def test_gemini_usage_includes_thinking_if_reported():
    result = summarize_response("gemini", {"usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 2, "thoughtsTokenCount": 3},
                                          "candidates": [{"content": {"parts": [{"text": "OK"}]}}]})
    assert result["status"] == "SUCCESS"
    assert result["output_tokens_including_reported_thinking"] == 5
    assert result["estimated_standard_token_cost_usd"] == pytest.approx(0.000003)


def test_missing_usage_is_unknown_cost_not_zero():
    result = summarize_response("claude", {"content": [{"type": "text", "text": "OK"}]})
    assert result["estimated_standard_token_cost_usd"] is None


def test_credit_failure_is_classified_without_exposing_body():
    assert error_category(400, "Your credit balance is too low") == "BILLING_OR_CREDIT_BLOCKED"


def test_http_failure_is_one_attempt_and_never_echoes_secret(monkeypatch):
    calls = []

    class FakeOpener:
        def open(self, request, timeout):
            calls.append(request)
            raise urllib.error.HTTPError(request.full_url, 401, "error", {}, io.BytesIO(b"fake-test-secret-value"))

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: FakeOpener())
    result = send_once("openai", "fake-test-secret-value")
    assert len(calls) == 1
    assert result["status"] == "AUTHENTICATION_OR_PERMISSION_FAILED"
    assert "fake-test-secret-value" not in json.dumps(result)


def test_second_run_sends_no_requests_and_preserves_results(tmp_path, monkeypatch):
    attempts = []
    monkeypatch.setattr(connections, "ROOT", tmp_path)
    monkeypatch.setattr(connections, "read_key", lambda name: "fake-test-secret-value")

    def fake_send(provider, key):
        attempts.append(provider)
        return {"provider": provider, "status": "SUCCESS", "attempts": 1, "estimated_standard_token_cost_usd": 0.00001}

    monkeypatch.setattr(connections, "send_once", fake_send)
    assert connections.main(["--execute"]) == 0
    output = tmp_path / "docs/stage1-api-connection-2026-10-26/results.json"
    original = output.read_bytes()
    assert connections.main(["--execute"]) == 2
    assert len(attempts) == 3
    assert output.read_bytes() == original


def test_unexpected_response_model_cannot_echo_key():
    result = summarize_response("claude", {"model": "fake-test-secret-value", "content": []})
    assert result["response_model"] == "RESPONSE_MODEL_NOT_RECORDED"
