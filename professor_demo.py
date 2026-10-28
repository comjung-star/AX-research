import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

import numpy as np
from ax_research import functional_mapping as functional
from ax_research import semantic_mapping as semantic
from ax_research.retrieval.bm25 import BM25Retriever


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8-sig'))


class Demo:
    def __init__(self):
        self.lock = threading.Lock()
        self.ready = False
        self.error = None
        self.hashes = read('demo_manifest.json')

    def verify(self):
        for name, expected in self.hashes.items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
                raise RuntimeError('보존 파일 변경 감지: ' + name)

    def warmup(self):
        try:
            self.verify()
            import torch
            from sentence_transformers import SentenceTransformer
            torch.set_num_threads(4)
            self.config = read('configs/semantic_mapping_20261028.json')
            self.rules = read('configs/functional_mapping_20261028.json')
            self.cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
            assert len(self.cases) == 112
            self.metadata = {case['case_id']: case for case in read('data/v2_5/main_cases_v2_5.json')['cases']}
            self.localized = read('prototype/case_display_ko.json')
            self.profiles = {key: semantic.field_profile(case['task'], self.config, self.rules['negation_guard'], executed=True, context=case['context']) for key, case in self.cases.items()}
            self.functions = {key: functional.case_profile(case, self.rules) for key, case in self.cases.items()}
            with np.load(ROOT / 'docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz', allow_pickle=False) as archive:
                self.embeddings = dict(zip(archive['texts'].tolist(), archive['vectors']))
            with np.load(ROOT / 'docs/stage123-openai-triplicate-2026-10-27/embeddings.npz', allow_pickle=False) as archive:
                self.ids = archive['case_ids'].tolist()
                self.dense = archive['single'].copy()
            assert set(self.ids) == set(self.cases)
            self.bm25 = BM25Retriever({key: '\n'.join('[%s] %s' % (field.upper(), case[field]) for field in ('problem', 'task', 'context')) for key, case in self.cases.items()})
            model = Path(os.environ.get('AX_BGE_MODEL_PATH', str(ROOT.parent / 'AX-prototype/.local/models/bge-m3')))
            self.model = SentenceTransformer(str(model), device='cpu', local_files_only=True)
            self.model.max_seq_length = self.config['max_tokens']
            self.model.encode(['시연 준비'], normalize_embeddings=True, show_progress_bar=False)
            self.ready = True
        except Exception as exc:
            self.error = str(exc)
            import traceback
            traceback.print_exc()

    def search(self, query, method):
        if not isinstance(query, str) or not 2 <= len(query.strip()) <= 2000:
            raise ValueError('업무문제를 2~2,000자로 입력해 주세요.')
        if method not in ('C', 'B', 'A', 'dense', 'bm25'):
            raise ValueError('검색 방식을 확인해 주세요.')
        if not self.ready:
            raise ValueError(self.error or '모델 준비 중입니다. 잠시 뒤 실행해 주세요.')
        with self.lock:
            started = time.perf_counter()
            self.verify()
            query = query.strip()
            profile = semantic.field_profile(query, self.config, self.rules['negation_guard'])
            functions = functional.extract(query, self.rules)
            texts = list(dict.fromkeys([query] + [value for value in profile['fields'].values() if value]))
            if any(len(self.model.tokenizer.encode(text)) > self.config['max_tokens'] for text in texts):
                raise ValueError('입력이 모델 길이 제한을 초과했습니다. 짧게 입력해 주세요.')
            vectors = self.model.encode(texts, batch_size=8, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
            embeddings = {**self.embeddings, **dict(zip(texts, vectors))}
            dense = dict(zip(self.ids, map(float, self.dense @ embeddings[query])))
            sparse = {row.case_id: row.score for row in self.bm25.search(query)}
            rows = []
            for key, case in self.cases.items():
                rule = functional.compare(functions, self.functions[key])
                meaning = semantic.compare_fields(profile, self.profiles[key], embeddings, self.config['weights'])
                grade = rule['mapping_grade']
                score = {'C': semantic.combined_score(grade, meaning['score']), 'B': meaning['score'], 'A': grade / 4, 'dense': dense[key], 'bm25': sparse[key]}[method]
                local = self.localized.get(key, {})
                meta = self.metadata.get(key, {})
                rows.append({'case_id': key, 'score': score, 'dense': dense[key], 'bm25': sparse[key], 'rule': grade, 'semantic': meaning, 'evidence': rule, 'fields': self.profiles[key]['fields'], 'case': case, 'title': local.get('task') or case['task'], 'problem_ko': local.get('problem'), 'organization': meta.get('organization', ''), 'source_url': meta.get('source_url', ''), 'query_functions': functions['functions'], 'case_functions': self.functions[key]['task']['functions']})
            rows.sort(key=lambda row: (-row['score'], -row['dense'], row['case_id']))
            self.verify()
            return {'query': query, 'method': method, 'candidate_count': len(rows), 'elapsed_seconds': round(time.perf_counter() - started, 2), 'query_fields': profile['fields'], 'results': rows[:5], 'notice': '상대 추천 점수이며 정답 확률·학술 성능이 아닙니다. 미인식 기능은 부적합의 증거가 아닙니다.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    demo = Demo()

    class Handler(BaseHTTPRequestHandler):
        def send_json(self, value, status=200):
            payload = json.dumps(value, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path == '/api/status':
                return self.send_json({'ready': demo.ready, 'error': demo.error, 'case_count': 112})
            if self.path != '/':
                return self.send_json({'error': '찾을 수 없습니다.'}, 404)
            payload = (ROOT / 'professor_demo.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self):
            if self.path != '/api/search':
                return self.send_json({'error': '찾을 수 없습니다.'}, 404)
            if self.headers.get('Origin') not in (None, f'http://127.0.0.1:{args.port}', f'http://localhost:{args.port}'):
                return self.send_json({'error': '허용되지 않은 요청'}, 403)
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 16000:
                    raise ValueError('입력 크기를 확인해 주세요.')
                data = json.loads(self.rfile.read(length))
                self.send_json(demo.search(data.get('query'), data.get('method', 'C')))
            except ValueError as exc:
                self.send_json({'error': str(exc)}, 400)
            except Exception:
                import traceback
                traceback.print_exc()
                self.send_json({'error': '검색에 실패했습니다. 서버 실행 창을 확인해 주세요.'}, 500)

    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    threading.Thread(target=demo.warmup, daemon=True).start()
    print(f'AX 나침반 http://127.0.0.1:{args.port}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
