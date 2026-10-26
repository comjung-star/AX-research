import csv
import hashlib
import http.client
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from prototype.core import CORPUS, STAGE1, Engine, UserError
from prototype.server import Application, PrototypeHTTPServer, make_handler
from prototype.storage import FeedbackStore


class RecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = Engine()

    def test_all_ten_examples_recalculate_real_dense_and_keep_branches(self):
        original_hash = hashlib.sha256(CORPUS.read_bytes()).hexdigest()
        expected_counts = []
        for example in self.engine.examples:
            result = self.engine.recommend({"query": example["query"], "top_k": 5})
            expected = [row for row in self.engine.perspectives if row["query_id"] == example["query_id"] and row["run_id"] == 1]
            self.assertEqual(result["provider"], "cached_llm_dense")
            self.assertEqual(len(result["branches"]), len(expected))
            expected_counts.append(len(expected))
            for branch in result["branches"]:
                vector = self.engine.branch_vectors[f"{example['query_id']}|1|{branch['id']}"]
                scores = (self.engine.views @ vector).mean(axis=0)
                indices = sorted(range(84), key=lambda offset: (-float(scores[offset]), self.engine.case_ids[offset]))[:5]
                self.assertEqual([card["case_id"] for card in branch["cases"]], [self.engine.case_ids[offset] for offset in indices])
                self.assertEqual(len(set(card["case_id"] for card in branch["cases"])), 5)
                for card in branch["cases"]:
                    self.assertEqual(card["trace"][0], branch["id"])
                    self.assertTrue(card["source_url"].startswith("https://"))
                    self.assertEqual(len(card["view_scores"]), 3)
        self.assertGreater(len(set(expected_counts)), 1)
        self.assertEqual(hashlib.sha256(CORPUS.read_bytes()).hexdigest(), original_hash)

    def test_dense_matches_original_published_256_comparison(self):
        example = self.engine.examples[0]
        result = self.engine.recommend({"query": example["query"], "top_k": 10})
        expected = [row for row in self.engine.qci_rows if row["query_id"] == example["query_id"] and row["run_id"] == "1" and row["scorer"] == "dense_3view"]
        for branch in result["branches"]:
            rows = sorted([row for row in expected if row["perspective_id"] == branch["id"]], key=lambda row: int(row["rank"]))
            self.assertEqual([card["case_id"] for card in branch["cases"]], [row["case_id"] for row in rows])
            np.testing.assert_allclose([card["score"] for card in branch["cases"]], [float(row["score"]) for row in rows], atol=1e-6)

    def test_qci_is_only_explicit_replay(self):
        result = self.engine.recommend({"query": self.engine.examples[0]["query"], "scorer": "qci_replay"})
        self.assertEqual(result["provider"], "cached_qci256")
        rows = [row for row in self.engine.qci_rows if row["query_id"] == "V21D001" and row["run_id"] == "1" and row["perspective_id"] == "P1" and row["scorer"] == "gated_qci_256"]
        rows.sort(key=lambda row: int(row["rank"]))
        self.assertEqual(result["branches"][0]["cases"][0]["case_id"], rows[0]["case_id"])
        with self.assertRaises(UserError):
            self.engine.recommend({"query": "새로운 자유 입력 업무 문제", "scorer": "qci_replay"})

    def test_free_input_is_explicit_lexical_not_disguised_dense(self):
        with patch.object(self.engine, "_model_path", return_value=None):
            result = self.engine.recommend({"query": "고객상담 통화 기록을 사람이 요약합니다. 그리고 이메일의 핵심 정보를 찾아야 합니다."})
        self.assertEqual(result["provider"], "local_lexical")
        self.assertEqual(len(result["branches"]), 2)
        self.assertIn("LLM·Dense를 실행하지 않았습니다", result["notice"])
        self.assertTrue(result["branches"][0]["cases"])

    def test_no_match_does_not_fabricate_cases(self):
        with patch.object(self.engine, "_model_path", return_value=None):
            result = self.engine.recommend({"query": "zzzzzzzzzzzzzzzz"})
        self.assertTrue(result["branches"][0]["empty"])
        self.assertEqual(result["branches"][0]["cases"], [])

    def test_runtime_can_have_two_or_five_dynamic_perspectives(self):
        for count in (2, 5):
            perspectives = [{"id": f"P{index}", "title": f"새로운 입력 관점 {index}", "description": "입력 근거 문제"} for index in range(1, count + 1)]
            vectors = np.repeat(self.engine.branch_vectors["V21D001|1|P1"][None, :], count, axis=0)
            with patch.object(self.engine, "_live_perspectives", return_value=(perspectives, vectors)):
                result = self.engine.recommend({"query": "새 업무를 동적으로 분석할 입력입니다.", "mode": "live"})
            self.assertEqual(len(result["branches"]), count)
            self.assertEqual(result["provider"], "live_llm_dense")
            self.assertEqual([branch["title"] for branch in result["branches"]], [branch["title"] for branch in perspectives])

    def test_missing_key_is_actionable_and_no_silent_fallback(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with self.assertRaisesRegex(UserError, "API 연결"):
                self.engine.recommend({"query": "직원들이 사내 정보를 찾기 어렵습니다", "mode": "live"})

    def test_actual_llm_adapter_parses_dynamic_schema_without_gold_or_temperature(self):
        def parse_response(**arguments):
            self.assertNotIn("temperature", arguments)
            self.assertNotIn("draft_perspectives", json.dumps(arguments["input"]))
            parsed = arguments["text_format"].model_validate({"perspectives": [
                {"title": "정보 탐색 지연", "description": "직원이 자료를 찾기 어렵습니다"},
                {"title": "중복 자료 작성", "description": "기존 자료를 못 찾아 다시 작성합니다"}]})
            return SimpleNamespace(output_parsed=parsed)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-only-placeholder"}), patch.object(self.engine, "_model_path", return_value=Path("local-model")), patch.object(self.engine, "_encode", return_value=np.repeat(self.engine.branch_vectors["V21D001|1|P1"][None, :], 2, axis=0)), patch("openai.OpenAI") as client:
            client.return_value.responses.parse.side_effect = parse_response
            result = self.engine.recommend({"query": "직원이 자료를 찾기 어렵고 기존 자료를 다시 작성합니다", "mode": "live", "include_strategy": False})
            client.assert_called_once_with(api_key="sk-test-only-placeholder", base_url="https://api.openai.com/v1", timeout=45, max_retries=0)
        self.assertEqual(len(result["branches"]), 2)
        self.assertEqual(result["branches"][0]["title"], "정보 탐색 지연")

    def test_llm_connection_error_does_not_expose_upstream_key(self):
        secret = "sk-test-upstream-error-secret"
        with patch.dict(os.environ, {"OPENAI_API_KEY": secret}), patch.object(self.engine, "_model_path", return_value=Path("local-model")), patch("openai.OpenAI") as client:
            client.return_value.responses.parse.side_effect = RuntimeError(secret)
            with self.assertRaises(UserError) as caught:
                self.engine.recommend({"query": "직원이 규정 문서를 찾기 어렵습니다", "mode": "live"})
        self.assertNotIn(secret, str(caught.exception))

    def test_validation_and_request_lock(self):
        for payload in ({"query": "짧다"}, {"query": "충분한 길이 입력", "top_k": 0}, {"query": "충분한 길이 입력", "top_k": True}, {"query": "충분한 길이 입력", "mode": "unknown"}, {"query": "a" * 4001}):
            with self.assertRaises(UserError):
                self.engine.recommend(payload)
        with self.engine.lock:
            with self.assertRaisesRegex(UserError, "진행 중"):
                self.engine.recommend({"query": "충분한 길이 입력"})

    def test_secret_is_redacted_before_result_or_storage(self):
        secret = "sk-test-secret-12345678901234567890"
        with patch.dict(os.environ, {"OPENAI_API_KEY": secret}), patch.object(self.engine, "_model_path", return_value=None):
            result = self.engine.recommend({"query": f"문서 검색이 어렵습니다 {secret}"})
        self.assertNotIn(secret, json.dumps(result))

    def test_keyless_custom_dense_uses_local_encoder_when_ready(self):
        with patch.object(self.engine, "_model_path", return_value=Path("local-model")), patch.object(self.engine, "_encode", return_value=np.array([self.engine.branch_vectors["V21D001|1|P1"]])) as encode:
            result = self.engine.recommend({"query": "새로운 고객상담 처리 업무문제입니다"})
        self.assertEqual(result["provider"], "local_dense")
        encode.assert_called_once()
        self.assertTrue(result["branches"][0]["cases"][0]["view_scores"])


class MemoryCredentialStore:
    supported = True

    def __init__(self):
        self.saved = None

    def read(self):
        return self.saved

    def save(self, api_key, model):
        self.saved = {"api_key": api_key, "model": model}

    def delete(self):
        self.saved = None


class APIConnectionTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"OPENAI_API_KEY": "", "AX_LLM_MODEL": "gpt-6-luna"})
        self.environment.start()
        self.temporary = tempfile.TemporaryDirectory()
        self.vault = MemoryCredentialStore()
        self.app = Application(Path(self.temporary.name) / "connection.sqlite3", credential_store=self.vault)
        self.key = "sk-test-connection-placeholder-123456"

    def tearDown(self):
        self.temporary.cleanup()
        self.environment.stop()

    def test_connection_requires_real_probe_before_registration(self):
        with patch.object(self.app.engine, "_generate_perspectives", return_value=[{"id": "P1"}, {"id": "P2"}]) as probe:
            result = self.app.connect_api({"api_key": self.key, "model": "gpt-6-luna", "remember": True})
        self.assertEqual(probe.call_args.kwargs, {"api_key": self.key, "model": "gpt-6-luna"})
        self.assertEqual(os.environ["OPENAI_API_KEY"], self.key)
        self.assertTrue(result["connection"]["verified"])
        self.assertEqual(result["default_mode"], "live")
        self.assertEqual(result["connection"]["test_perspective_count"], 2)
        self.assertEqual(self.vault.saved["api_key"], self.key)
        self.assertNotIn(self.key, json.dumps(result))
        self.assertEqual(self.app.store.summary()["total"], 0)

    def test_failed_probe_preserves_previous_working_key_and_saved_secret(self):
        os.environ["OPENAI_API_KEY"] = "sk-test-old-working-placeholder"
        self.vault.save("sk-test-old-working-placeholder", "gpt-6-luna")
        with patch.object(self.app.engine, "_generate_perspectives", side_effect=UserError("API키 인증에 실패했습니다")):
            with self.assertRaises(UserError):
                self.app.connect_api({"api_key": self.key, "remember": True})
        self.assertEqual(os.environ["OPENAI_API_KEY"], "sk-test-old-working-placeholder")
        self.assertEqual(self.vault.saved["api_key"], "sk-test-old-working-placeholder")

    def test_session_only_connection_and_disconnect(self):
        self.vault.save("sk-test-previous-placeholder", "gpt-6-luna")
        with patch.object(self.app.engine, "_generate_perspectives", return_value=[{"id": "P1"}]):
            self.app.connect_api({"api_key": self.key, "remember": False})
        self.assertIsNone(self.vault.saved)
        self.assertTrue(os.environ["OPENAI_API_KEY"])
        result = self.app.disconnect_api()
        self.assertFalse(result["live_key_configured"])
        self.assertFalse(result["connection"]["verified"])
        self.assertEqual(result["default_mode"], "demo")

    def test_invalid_input_and_busy_state_never_call_api(self):
        for payload in ({"api_key": "not-a-key"}, {"api_key": self.key, "model": "https://evil.invalid"}, {"api_key": self.key, "remember": "yes"}):
            with patch.object(self.app.engine, "_generate_perspectives") as probe:
                with self.assertRaises(UserError):
                    self.app.connect_api(payload)
                probe.assert_not_called()
        with self.app.engine.lock:
            with self.assertRaises(UserError):
                self.app.connect_api({"api_key": self.key})

    def test_upstream_authentication_error_is_sanitized_and_actionable(self):
        error = RuntimeError(self.key)
        error.status_code = 401
        with patch("openai.OpenAI") as client:
            client.return_value.responses.parse.side_effect = error
            with self.assertRaisesRegex(UserError, "인증에 실패") as caught:
                self.app.engine._generate_perspectives("고객의 반복 문의 처리 부담", api_key=self.key)
        self.assertNotIn(self.key, str(caught.exception))

    def test_existing_server_key_can_be_verified_without_sending_it_to_browser(self):
        os.environ["OPENAI_API_KEY"] = self.key
        with patch.object(self.app.engine, "_generate_perspectives", return_value=[{"id": "P1"}]) as probe:
            result = self.app.connect_api({"api_key": "", "model": "gpt-6-luna"})
        self.assertEqual(probe.call_args.kwargs["api_key"], self.key)
        self.assertNotIn(self.key, json.dumps(result))


class StorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        engine = Engine()
        cls.result = engine.recommend({"query": engine.examples[0]["query"]})

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "test.sqlite3"
        self.store = FeedbackStore(self.path)
        self.payload = {"consent": True, "perspective_id": "P1", "case_id": self.result["branches"][0]["cases"][0]["case_id"], "rating": "useful", "comment": "실제 업무에 관련 있습니다", "tester": "검증용"}

    def tearDown(self):
        self.temporary.cleanup()

    def test_consent_and_actual_recommendation_membership(self):
        for payload in ({**self.payload, "consent": False}, {**self.payload, "perspective_id": "GOLD_P1"}, {**self.payload, "case_id": "invalid"}, {**self.payload, "rating": "unknown"}):
            with self.assertRaises(UserError):
                self.store.save(self.result, payload)
        self.assertEqual(self.store.summary()["total"], 0)

    def test_saved_rating_updates_without_duplicate_and_survives_restart(self):
        self.store.save(self.result, self.payload)
        self.store.save(self.result, {**self.payload, "rating": "partial", "comment": "수정한 의견"})
        restarted = FeedbackStore(self.path)
        self.assertEqual(restarted.summary(), {"sessions": 1, "ratings": {"partial": 1}, "total": 1})
        export = json.loads(restarted.export("json"))
        self.assertEqual(export["feedback"][0]["comment"], "수정한 의견")
        self.assertEqual(export["sessions"][0]["branches"], self.result["branches"])

    def test_same_case_in_other_branch_keeps_independent_feedback(self):
        self.store.save(self.result, self.payload)
        branch = self.result["branches"][1]
        self.store.save(self.result, {**self.payload, "perspective_id": branch["id"], "case_id": branch["cases"][0]["case_id"], "rating": "irrelevant"})
        self.assertEqual(self.store.summary()["total"], 2)

    def test_overall_comment_csv_unicode_formula_protection_and_redaction(self):
        self.store.save(self.result, {"consent": True, "perspective_id": "", "case_id": "", "rating": "overall", "comment": "=HYPERLINK(悪意)", "tester": "@SUM(1)"})
        exported = self.store.export("csv")
        self.assertTrue(exported.startswith(b"\xef\xbb\xbf"))
        rows = list(csv.reader(io.StringIO(exported.decode("utf-8-sig"))))
        self.assertTrue(rows[1][3].startswith("'@"))
        self.assertTrue(rows[1][10].startswith("'="))
        self.assertEqual(json.loads(self.store.export("json"))["kind"], "USER_TEST_NOT_RESEARCH_GOLD")


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.app = Application(Path(cls.temporary.name) / "http.sqlite3")
        cls.server = PrototypeHTTPServer(("127.0.0.1", 0), make_handler(cls.app))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temporary.cleanup()

    def call(self, path, payload=None, token=True, extra_headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-AX-Token"] = self.app.token
        headers.update(extra_headers or {})
        connection.request("POST" if payload is not None else "GET", path, json.dumps(payload) if payload is not None else None, headers)
        response = connection.getresponse()
        body = response.read()
        result = response.status, dict(response.getheaders()), body
        connection.close()
        return result

    def test_health_and_static_allowlist_security_headers(self):
        for path in ("/", "/app.js", "/style.css", "/research.js", "/research.css", "/api/health"):
            status, headers, body = self.call(path)
            self.assertEqual(status, 200)
            self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
            self.assertTrue(body)
        for path in ("/../../.env", "/.env", "/data/v2_3/main_cases_v2_3.json", "/.local/ax-prototype/feedback.sqlite3"):
            self.assertEqual(self.call(path)[0], 404)

    def test_second_listener_cannot_replace_running_app(self):
        with self.assertRaises(OSError):
            PrototypeHTTPServer(("127.0.0.1", self.port), make_handler(self.app))

    def test_no_key_in_bootstrap_or_errors(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-very-secret-1234567890"}):
            status, headers, body = self.call("/api/bootstrap")
        self.assertEqual(status, 200)
        self.assertNotIn(b"sk-very-secret", body)
        self.assertEqual(json.loads(body)["default_scorer"], "dense")

    def test_csrf_host_origin_and_export_protection(self):
        query = {"query": "고객 문의가 늘어 대응하기 어렵습니다"}
        self.assertEqual(self.call("/api/recommend", query, token=False)[0], 403)
        self.assertEqual(self.call("/api/recommend", query, extra_headers={"Origin": "https://evil.invalid"})[0], 403)
        self.assertEqual(self.call("/api/bootstrap", extra_headers={"Host": f"evil.invalid:{self.port}"})[0], 403)
        self.assertEqual(self.call("/api/export.json", token=False)[0], 403)
        self.assertEqual(self.call("/api/connection", {}, token=False)[0], 403)
        self.assertEqual(self.call("/api/disconnect", {}, token=False)[0], 403)

    def test_connection_endpoint_returns_only_safe_status(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}), patch.object(self.app.engine, "_generate_perspectives", return_value=[{"id": "P1"}]), patch.object(self.app.credentials, "delete"):
            status, headers, body = self.call("/api/connection", {"api_key": "sk-test-http-placeholder-123456789", "remember": False})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["connection"]["verified"])
        self.assertNotIn(b"sk-test-http", body)

    def test_end_to_end_recommend_evaluate_export(self):
        status, headers, body = self.call("/api/recommend", {"query": self.app.engine.examples[1]["query"], "top_k": 1})
        self.assertEqual(status, 200)
        result = json.loads(body)
        branch = result["branches"][0]
        status, headers, body = self.call("/api/feedback", {"session_id": result["session_id"], "perspective_id": branch["id"], "case_id": branch["cases"][0]["case_id"], "rating": "useful", "comment": "시연 검증", "consent": True})
        self.assertEqual(status, 200)
        exported = json.loads(self.call("/api/export.json")[2])
        self.assertEqual(exported["feedback"][0]["comment"], "시연 검증")
        self.assertEqual(exported["sessions"][0]["query"], result["query"])
        self.assertEqual(self.call("/api/feedback", {"session_id": "expired"})[0], 400)

    def test_validation_and_size_limits(self):
        self.assertEqual(self.call("/api/recommend", {"query": "a" * 40000})[0], 413)
        self.assertEqual(self.call("/api/recommend", {"query": "짧다"})[0], 400)
        self.assertEqual(self.call("/api/recommend", {"query": "업무 입력이 충분합니다"}, extra_headers={"Content-Type": "text/plain"})[0], 415)


if __name__ == "__main__":
    unittest.main()
