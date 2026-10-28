import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [
    '고객 문의가 많아 반복 답변에 시간이 걸리고, 상담 이력을 찾기 어려워 복잡한 문의의 대응이 늦어집니다.',
    '대출 신청 PDF에서 필요한 항목을 추출하고 누락 정보를 확인하는 수작업이 많습니다. 직원이 규정 문서에서 관련 근거를 찾는 시간도 줄이고 싶습니다.',
]


def main():
    for attempt in range(60):
        with urllib.request.urlopen('http://127.0.0.1:8766/api/status') as response:
            if json.load(response)['ready']:
                break
        time.sleep(1)
    results = []
    for query in EXAMPLES:
        request = urllib.request.Request('http://127.0.0.1:8766/api/live-search', data=json.dumps({'query': query, 'method': 'C'}).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=180) as response:
            record = json.load(response)
        assert record['live'] and record['llm_evidence']['api_called']
        assert record['llm_evidence']['response_id']
        assert 1 <= len(record['branches']) <= 6
        assert len({row['case_id'] for row in record['results']}) == 5
        for branch in record['branches']:
            assert branch['candidate_count'] == 112 and len(branch['results']) == 5
        for row in record['results']:
            assert len(row['branch_support']) == len(record['branches'])
            best = max(item['semantic'] for item in row['branch_support'])
            assert best >= -1
        results.append(record)
        print(json.dumps({'seconds': record['elapsed_seconds'], 'model': record['llm_evidence']['model'], 'response_id': record['llm_evidence']['response_id'], 'perspectives': [branch['title'] for branch in record['branches']], 'top5': [row['case_id'] for row in record['results']]}, ensure_ascii=True), flush=True)
    output = ROOT / 'docs/professor-demo-20261028/live-verification.json'
    output.write_text(json.dumps({'passed': True, 'real_api_calls': len(results), 'independent_test_access': False, 'results': results}, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
