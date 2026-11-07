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

class RepairedBM25Retriever:
    """New-experiment BM25 retriever using repaired tokens, preserving all cases.

    Do not silently swap this into historical frozen experiments. This class
    is the explicit repaired search component for future validation.
    """
    def __init__(self, documents):
        if not documents:
            raise ValueError("Documents cannot be empty")
        from rank_bm25 import BM25Okapi
        from ax_research.retrieval.bm25 import RankedCase
        self._case_ids=list(documents)
        self._tokenizer=RepairedKiwiTokenizer()
        self._bm25=BM25Okapi([self._tokenizer.tokenize(documents[c]) for c in self._case_ids])
        self._rank_type=RankedCase
        if any(n==0 for n in self._bm25.doc_len):
            raise ValueError("Empty repaired BM25 document: inspect case/source preprocessing")
    def search(self,query,top_k=None):
        scores=self._bm25.get_scores(self._tokenizer.tokenize(query))
        results=sorted((self._rank_type(c,float(s)) for c,s in zip(self._case_ids,scores,strict=True)),
          key=lambda x:(-x.score,x.case_id))
        return results if top_k is None else results[:top_k]
