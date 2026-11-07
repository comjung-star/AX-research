"""Trial 1: protect Latin and number tokens from Kiwi's S-prefix filtering.

The regression test uses a fake Kiwi tokenizer to isolate the bug and avoid
model downloads. Real-corpus BM25 evaluation is a separate required gate.
"""
from __future__ import annotations

from types import SimpleNamespace

from ax_research.retrieval.bm25 import KiwiTokenizer


def test_keeps_latin_and_numeric_tokens() -> None:
    tokenizer = KiwiTokenizer.__new__(KiwiTokenizer)
    tokenizer._kiwi = SimpleNamespace(
        tokenize=lambda _: [
            SimpleNamespace(form="Vision", tag="SL"),
            SimpleNamespace(form="2026", tag="SN"),
            SimpleNamespace(form="검사", tag="NNG"),
            SimpleNamespace(form=".", tag="SF"),
            SimpleNamespace(form=",", tag="SP"),
            SimpleNamespace(form="(", tag="SSO"),
            SimpleNamespace(form=")", tag="SSC"),
            SimpleNamespace(form="!", tag="SW"),
        ]
    )
    assert tokenizer.tokenize("ignored") == ["vision", "2026", "검사"]


def test_excludes_empty_and_whitespace_tokens() -> None:
    tokenizer = KiwiTokenizer.__new__(KiwiTokenizer)
    tokenizer._kiwi = SimpleNamespace(
        tokenize=lambda _: [
            SimpleNamespace(form=" ", tag="SL"),
            SimpleNamespace(form="", tag="NNG"),
            SimpleNamespace(form="AI", tag="SL"),
        ]
    )
    assert tokenizer.tokenize("ignored") == ["ai"]
