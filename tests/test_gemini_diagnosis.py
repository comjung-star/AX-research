import json

import pytest

from scripts import diagnose_gemini_connection as diagnosis


def test_error_summary_does_not_store_secret_or_raw_message():
    result = diagnosis.safe_error(json.dumps({"error": {"status": "NOT_FOUND", "message": "models/example not found for API version v1beta fake-sensitive-value projects/123456"}}))
    assert result["rpc_status"] == "NOT_FOUND"
    assert result["message_mentions_model_not_found"] is True
    assert result["message_mentions_api_version"] is True
    assert "fake-sensitive-value" not in json.dumps(result)
    assert "123456" not in json.dumps(result)


def test_unexpected_status_is_not_echoed():
    assert diagnosis.safe_error('{"error":{"status":"fake-sensitive-value"}}')["rpc_status"] == "UNCLASSIFIED"


def test_minimal_legacy_request_changes_only_thinking_configuration():
    original = diagnosis.build_case("legacy_original")
    minimal = diagnosis.build_case("legacy_minimal")
    original["generationConfig"].pop("thinkingConfig")
    assert original == minimal


def test_current_request_uses_supported_minimal_thinking_level():
    body = diagnosis.build_case("current_minimal")
    assert body["generationConfig"] == {"maxOutputTokens": 256, "thinkingConfig": {"thinkingLevel": "minimal"}}


def test_generation_reservation_cannot_be_reused(tmp_path, monkeypatch):
    monkeypatch.setattr(diagnosis, "RESERVATIONS", tmp_path)
    assert diagnosis.reserve("legacy_original", False)
    assert not diagnosis.reserve("legacy_original", False)
    assert diagnosis.reserve("legacy_original", True)


def test_missing_key_never_sends_request(monkeypatch):
    monkeypatch.setattr(diagnosis, "read_key", lambda name: None)
    monkeypatch.setattr(diagnosis, "execute", lambda *args: pytest.fail("Must not send request"))
    assert diagnosis.main(["--case", "legacy_original", "--execute"]) == 2


def test_timeout_comparison_changes_wait_not_prompt_or_generation_options():
    assert diagnosis.build_case("current_minimal") == diagnosis.build_case("current_extended_timeout")
    assert diagnosis.CASES["current_extended_timeout"]["timeout"] == 120


def test_timeout_is_reported_without_exception_contents(monkeypatch):
    class FakeOpener:
        def open(self, request, timeout):
            raise TimeoutError("fake-sensitive-value")

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: FakeOpener())
    result = diagnosis.execute("current_extended_timeout", "fake-sensitive-value")
    assert result["transport_timeout"] is True
    assert result["attempts"] == 1
    assert "fake-sensitive-value" not in json.dumps(result)


def test_non_string_rpc_status_does_not_crash_or_leak():
    assert diagnosis.safe_error('{"error":{"status":["fake-sensitive-value"]}}')["rpc_status"] == "UNCLASSIFIED"
