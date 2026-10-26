import copy
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from prototype.core import Engine, clean_text
from prototype.strategy import StrategyResponse, attach_report, compose_report, selected_evidence, template_report, validate_report


class StrategyOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = Engine()
        cls.result = cls.engine.recommend({"query": cls.engine.examples[0]["query"]})

    def valid_model_output(self):
        report = copy.deepcopy(template_report(self.result["query"], self.result["branches"]))
        cards = {card["case_id"]: card for branch in self.result["branches"] for card in branch["cases"][:3]}
        report["case_explanations"] = [{"case_id": case_id, "solution": card["solution"], "outcome": card["outcome"]} for case_id, card in cards.items()]
        return report

    def test_all_examples_have_concrete_actions_and_branch_local_case_evidence(self):
        for example in self.engine.examples:
            result = self.engine.recommend({"query": example["query"]})
            self.assertEqual(result["strategy_report"]["provider"], "evidence_template")
            self.assertGreater(result["strategy_report"]["strategy_count"], 0)
            for branch in result["branches"]:
                allowed = {card["case_id"]: card for card in branch["cases"]}
                for strategy in branch["recommendation"]["strategies"]:
                    self.assertGreaterEqual(len(strategy["actions"]), 2)
                    self.assertTrue(strategy["prerequisites"])
                    self.assertTrue(strategy["limitations"])
                    for case_id in strategy["supporting_case_ids"]:
                        self.assertIn(case_id, allowed)
                        self.assertIn(strategy["strategy_id"], [item["id"] for item in allowed[case_id]["strategies"]])

    def test_ey_actual_solution_is_visible_separately_from_suggested_actions(self):
        card = self.engine._card("AXV2H_0008_01", 0.5, [0.5, 0.5, 0.5], 1, {"id": "P1", "title": "문서 수작업"})
        self.assertIn("Azure AI Document Intelligence", card["solution"])
        self.assertIn("K-1", card["solution"])
        self.assertIn("최대 90%", card["outcome"])
        self.assertEqual(card["original"]["implementation"], self.engine.cases[card["case_id"]]["implementation"])

    def test_only_top_three_selected_case_fields_are_sent(self):
        result = self.engine.recommend({"query": self.engine.examples[0]["query"], "top_k": 10})
        evidence = selected_evidence(result["branches"])
        self.assertTrue(all(len(branch["cases"]) == 3 for branch in evidence))
        self.assertLess(len({card["case_id"] for branch in evidence for card in branch["cases"]}), 84)
        for branch in evidence:
            for card in branch["cases"]:
                for excluded in ("factor_review", "qrels", "human_ground_truth", "feedback", "OPENAI_API_KEY"):
                    self.assertNotIn(excluded, card)

    def test_report_rejects_unknown_or_cross_branch_evidence(self):
        evidence = selected_evidence(self.result["branches"])
        report = self.valid_model_output()
        report["perspectives"][0]["strategies"][0]["supporting_case_ids"] = ["AX_CASE_NOT_RETRIEVED"]
        with self.assertRaises(ValueError):
            validate_report(report, evidence, clean_text)
        report = self.valid_model_output()
        report["perspectives"][0]["perspective_id"] = "P999"
        with self.assertRaises(ValueError):
            validate_report(report, evidence, clean_text)

    def test_report_rejects_unsupported_taxonomy_and_invented_case_summary(self):
        report = self.valid_model_output()
        report["perspectives"][0]["strategies"][0]["strategy_id"] = "S999_UNSUPPORTED"
        with self.assertRaises(ValueError):
            validate_report(report, selected_evidence(self.result["branches"]), clean_text)
        report = self.valid_model_output()
        report["case_explanations"][0]["case_id"] = "NOT_IN_EVIDENCE"
        with self.assertRaises(ValueError):
            validate_report(report, selected_evidence(self.result["branches"]), clean_text)

    def test_actual_llm_adapter_validates_schema_and_records_safe_provenance(self):
        parsed = StrategyResponse.model_validate(self.valid_model_output())
        response = SimpleNamespace(output_parsed=parsed, id="resp-unit-test", usage=SimpleNamespace(input_tokens=300, output_tokens=200))
        secret = "sk-test-strategy-placeholder-12345678"
        with patch.dict(os.environ, {"OPENAI_API_KEY": secret}), patch("openai.OpenAI") as client:
            client.return_value.responses.parse.return_value = response
            report = compose_report(self.result["query"], self.result["branches"], self.engine.strategies, clean_text, live=True)
        self.assertEqual(report["provider"], "live_llm")
        self.assertEqual(report["api_evidence"]["response_id"], "resp-unit-test")
        self.assertNotIn(secret, json.dumps(report))
        request = client.return_value.responses.parse.call_args.kwargs
        self.assertIs(request["store"], False)
        self.assertNotIn("temperature", request)
        evidence_request = json.loads(request["input"][1]["content"])
        selected_ids = [card["case_id"] for card in evidence_request["selected_cases"]]
        self.assertEqual(selected_ids, evidence_request["required_case_explanation_ids"])
        self.assertEqual(len(selected_ids), len(set(selected_ids)))
        self.assertTrue(all(set(branch["selected_case_ids"]) <= set(selected_ids) for branch in evidence_request["perspectives"]))
        self.assertNotRegex(" ".join(message["content"] for message in request["input"]), r"[\u3040-\u30ff]")

    def test_mixed_japanese_explanations_are_not_presented_as_korean_results(self):
        report = self.valid_model_output()
        report["perspectives"][0]["strategies"][0]["actions"][0] = "문서 내용을 확인します"
        with self.assertRaisesRegex(ValueError, "Strategy text must be Korean"):
            validate_report(report, selected_evidence(self.result["branches"]), clean_text)

    def test_failed_generation_preserves_search_and_discloses_template_fallback(self):
        original = copy.deepcopy(self.result["branches"])
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-not-a-real-key-123456"}), patch("openai.OpenAI") as client:
            client.return_value.responses.parse.side_effect = RuntimeError("private upstream detail")
            report = attach_report(self.result["query"], original, self.engine.strategies, clean_text, live=True)
        self.assertEqual(report["provider"], "evidence_template")
        self.assertTrue(report["generation_error"])
        self.assertNotIn("private upstream detail", json.dumps(report))
        self.assertEqual([[card["case_id"] for card in branch["cases"]] for branch in original], [[card["case_id"] for card in branch["cases"]] for branch in self.result["branches"]])

    def test_no_evidence_does_not_generate_a_strategy_or_call_api(self):
        branches = [{"id": "P1", "title": "불명확", "description": "관련 사례 없음", "cases": []}]
        with patch("openai.OpenAI") as client:
            report = attach_report("관련 사례가 없는 질문", branches, self.engine.strategies, clean_text, live=True)
        client.assert_not_called()
        self.assertEqual(report["strategy_count"], 0)
        self.assertEqual(branches[0]["recommendation"]["strategies"], [])


if __name__ == "__main__":
    unittest.main()
