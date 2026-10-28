import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8766')
    parser.add_argument('--skip-http', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'demo_manifest.json').read_text())
    for name, expected in manifest.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    documents = [ROOT / 'README.md', *sorted((ROOT / 'docs/professor-review').glob('*.md'))]
    link_count = 0
    for document in documents:
        content = document.read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)', content):
            parsed = urlsplit(target)
            if parsed.scheme or not parsed.path:
                continue
            destination = (document.parent / unquote(parsed.path)).resolve()
            assert destination.is_relative_to(ROOT), target
            assert destination.exists(), (document.name, target)
            if parsed.fragment:
                headings = re.findall(r'^#+ (.+)$', destination.read_text(encoding='utf-8'), re.M)
                anchors = [re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-') for heading in headings]
                assert unquote(parsed.fragment) in anchors, target
            link_count += 1
    branches = ['ba5308d1', 'be64f9c1', '715c4050', 'cf30b73c', '2140dc27']
    for commit in branches:
        subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'], cwd=ROOT, check=True)
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    forbidden = [name for name in tracked if name and (
        Path(name).name == '.env' or name.endswith(('.safetensors', '.pem', '.key'))
        or 'pytorch_model.bin' in name or '.ax-heldout-work-b' in name)]
    assert not forbidden, forbidden
    report = {'manifest_files_unchanged': len(manifest), 'local_links_valid': link_count,
              'ancestor_commits_verified': branches, 'forbidden_tracked_files': forbidden,
              'sealed_test_access': False, 'paid_api_calls': 0, 'http_checks': []}
    if not args.skip_http:
        assert urlsplit(args.base_url).hostname in ('127.0.0.1', 'localhost')
        with urllib.request.urlopen(args.base_url + '/api/status', timeout=10) as response:
            status = json.load(response)
        assert status['ready'], status.get('error') or 'Model still warming up'
        report['local_model_ready'] = True
        examples = ['고객 문의에 반복 답변하는 시간을 줄이고 싶습니다.',
                    '대출 PDF 문서에서 필요한 항목을 추출하고 누락을 확인하고 싶습니다.',
                    '직원이 사내 규정 문서를 검색하고 근거를 찾는 시간을 줄이고 싶습니다.']
        for query, method in [(example, 'C') for example in examples] + [(examples[0], method) for method in ('A', 'B', 'dense', 'bm25')]:
            request = urllib.request.Request(args.base_url + '/api/search',
                data=json.dumps({'query': query, 'method': method}).encode(),
                headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.load(response)
            assert result['candidate_count'] == 112
            rows = result['results']
            assert len({row['case_id'] for row in rows}) == 5
            assert all(row['case']['evidence_ids'] and row['fields']['task'] for row in rows)
            assert all(rows[index]['score'] >= rows[index + 1]['score'] for index in range(4))
            report['http_checks'].append({'method': method, 'candidates': 112, 'top_count': 5})
        request = urllib.request.Request(args.base_url + '/api/search',
            data=b'{"query":"","method":"C"}', headers={'Content-Type': 'application/json'})
        try:
            urllib.request.urlopen(request, timeout=10)
            raise AssertionError('Empty query accepted')
        except urllib.error.HTTPError as error:
            assert error.code == 400
        report['empty_query_rejected'] = True
        with urllib.request.urlopen(args.base_url + '/', timeout=10) as response:
            html = response.read().decode('utf-8')
        assert '/api/live-search' in html
        report['default_ui_uses_live_search'] = True
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
