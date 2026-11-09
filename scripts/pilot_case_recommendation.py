"""Local CLI for the isolated stage-five evidence-based case prototype."""
import argparse
import json
import os
from pathlib import Path

import numpy as np

from ax_research.pilot_case_recommender import recommend_cases
from scripts.improvement_cycle import ROOT, read
from scripts.pilot_perspective_selection import CATALOG, RULES
from scripts.task_alignment_20261109 import MODEL, sha

PROFILES = 'configs/pilot_case_profiles_20261109.json'
REGISTRY = 'docs/dense-bm25-candidates-2026-10-27/case_registry.json'
BANKS = ['docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz',
         'docs/query-understanding-v2-20261109/vectors.npz',
         'docs/pilot-case-recommendation-20261109/vectors.npz',
         'docs/pilot-case-recommendation-20261109-v1_1/vectors.npz']


def inputs():
    catalog, rules, profiles, registry = read(CATALOG), read(RULES), read(PROFILES), read(REGISTRY)['cases']
    eligible = {l['case_id'] for c in catalog['cards'] for l in c['links'] if l['status'] == 'SUPPORTED_FOR_PILOT'}
    if set(profiles['cases']) != eligible:
        raise ValueError('세부 메타데이터와 승인된 시범 사례가 일치하지 않습니다.')
    return catalog, rules, profiles, registry


class LocalTaskScorer:
    """Frozen multilingual Task cosine for ordering only, loaded lazily offline."""
    def __init__(self, registry):
        self.registry = registry
        self.bank = {}
        self.encoder = None
        self.new_vectors = {}
        for path in BANKS:
            with np.load(ROOT / path, allow_pickle=False) as archive:
                for text, vector in zip(archive['texts'].tolist(), archive['vectors']):
                    self.bank.setdefault(text, vector)

    def warm(self, texts):
        missing = sorted({text for text in texts if text} - set(self.bank))
        if not missing:
            return
        if self.encoder is None:
            expected = read('docs/task-alignment-reference-20261109/config.json')['model_sha256']
            if any(sha(MODEL / name) != value for name, value in expected.items()):
                raise ValueError('기존 로컬 임베딩 모델과 파일 지문이 다릅니다.')
            for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY'):
                os.environ[key] = '1'
            import socket
            def blocked(*args, **kwargs):
                raise RuntimeError('로컬 모델만 사용합니다.')
            socket.socket.connect = blocked
            socket.create_connection = blocked
            import torch
            from sentence_transformers import SentenceTransformer
            torch.set_num_threads(4)
            torch.manual_seed(20261028)
            torch.use_deterministic_algorithms(True)
            self.encoder = SentenceTransformer(str(MODEL), device='cpu', local_files_only=True)
            self.encoder.max_seq_length = 4096
        if max(len(self.encoder.tokenizer.encode(t)) for t in missing) > 4096:
            raise ValueError('질문이 최대 입력 길이를 넘었습니다.')
        vectors = self.encoder.encode(missing, batch_size=8, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
        assert vectors.shape == (len(missing), 1024) and np.isfinite(vectors).all()
        assert np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5)
        for text, vector in zip(missing, vectors.astype(np.float32)):
            self.bank[text] = vector
            self.new_vectors[text] = vector

    def __call__(self, perspective, query_text, case_ids):
        tasks = {case: self.registry[case]['task'] for case in case_ids}
        self.warm([query_text] + list(tasks.values()))
        return {case: float(np.clip(self.bank[query_text] @ self.bank[text], -1, 1)) for case, text in tasks.items()}


def recommend(question, *, max_results=5, scorer=None):
    catalog, rules, profiles, registry = inputs()
    scorer = scorer if scorer is not None else LocalTaskScorer(registry)
    return recommend_cases(question, catalog, rules, profiles, registry, scorer, max_results=max_results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--question')
    parser.add_argument('--input', help='UTF-8 question text path')
    parser.add_argument('--max-results', type=int, default=5)
    args = parser.parse_args()
    question = (ROOT / args.input).read_text(encoding='utf-8') if args.input else args.question
    if not question:
        parser.error('Use --question or --input')
    print(json.dumps(recommend(question, max_results=args.max_results), ensure_ascii=False, indent=2))
