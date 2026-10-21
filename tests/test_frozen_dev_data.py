"""Frozen Dev 데이터 자체의 기본 조건을 검사하는 통합 성격 테스트."""

import unittest

from ax_research.data import (
    load_cases,
    load_gold,
    load_queries,
    load_relevance_labels,
)


class FrozenDevDataTest(unittest.TestCase):
    def test_frozen_dev_counts(self) -> None:
        cases = load_cases()
        queries = load_queries()
        labels = load_relevance_labels()
        gold = load_gold()

        self.assertEqual(len(cases), 100)
        self.assertEqual(len(queries), 10)
        self.assertEqual(len(labels), 3000)
        self.assertEqual(len(gold), 10)

    def test_all_active_queries_are_adjudicated(self) -> None:
        queries = load_queries()
        self.assertTrue(
            all(q.status == "PILOT_GOLD_ADJUDICATED" for q in queries.values())
        )


if __name__ == "__main__":
    unittest.main()
