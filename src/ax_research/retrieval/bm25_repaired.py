"""Repaired lexical tokenizer; kept separate from frozen pre-fix implementation.
The legacy src/ax_research/retrieval/bm25.py is intentionally immutable.
"""
from ax_research.retrieval.bm25 import KiwiTokenizer

class RepairedKiwiTokenizer(KiwiTokenizer):
    """Keep meaning-bearing Latin(SL), numerals(SN), Han(Hanja SH).
    Drop sentence punctuation and other non-lexical symbol S* classes.
    """
    CONTENT_S_TAGS=frozenset(("SL","SN","SH"))

    def tokenize(self,text):
        if not isinstance(text,str):
            raise TypeError("BM25 requires text")
        terms=[]
        for token in self._kiwi.tokenize(text):
            form=token.form.strip().lower()
            if not form:
                continue
            tag=token.tag
            if tag.startswith("S") and tag not in self.CONTENT_S_TAGS:
                continue
            terms.append(form)
        return terms
