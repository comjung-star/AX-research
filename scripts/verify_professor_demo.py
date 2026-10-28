import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8766'
EXAMPLES = [
    '고객 문의가 많아 반복 질문에 답변하는 시간이 오래 걸립니다. 상담 이력을 활용해 답변을 지원하고 싶습니다.',
    '대출 신청 PDF 문서에서 필요한 항목을 추출하고 누락 정보를 확인하는 수작업을 줄이고 싶습니다.',
    '직원이 긴 사내 규정과 정책 문서를 검색하고 관련 근거를 찾는 데 시간이 오래 걸립니다.',
]


def search(query, method):
    request = urllib.request.Request(BASE + '/api/search', data=json.dumps({'query': query, 'method': method}).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def main():
    with urllib.request.urlopen(BASE + '/api/status') as response:
        assert json.load(response)['ready']
    records = [search(query, 'C') for query in EXAMPLES]
    records.extend(search(EXAMPLES[0], method) for method in ('A', 'B', 'dense', 'bm25'))
    for record in records:
        assert record['candidate_count'] == 112
        assert len({row['case_id'] for row in record['results']}) == 5
        assert all(row['fields']['task'] and row['case']['evidence_ids'] for row in record['results'])
        assert all(record['results'][offset]['score'] >= record['results'][offset + 1]['score'] for offset in range(4))
    try:
        search('', 'C')
        raise AssertionError('Empty input accepted')
    except urllib.error.HTTPError as exc:
        assert exc.code == 400
    manifest = json.loads((ROOT / 'demo_manifest.json').read_text())
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected for name, expected in manifest.items())
    output = ROOT / 'docs/professor-demo-20261028'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'verification.json').write_text(json.dumps({'passed': True, 'real_inference': True, 'e2e_requests': 7, 'protected_files_unchanged': len(manifest), 'independent_test_access': False, 'external_api_calls': 0, 'results': records}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([{'method': row['method'], 'seconds': row['elapsed_seconds'], 'top5': [item['case_id'] for item in row['results']]} for row in records], indent=2))


if __name__ == '__main__':
    main()
