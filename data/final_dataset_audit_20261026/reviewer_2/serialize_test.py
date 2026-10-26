import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWN = ROOT / 'reviewer_2'
DOC = json.loads((ROOT / 'blind_test_relevance_input.json').read_text(encoding='utf-8-sig'))
HASH = hashlib.sha256(json.dumps(DOC, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert HASH == 'fd8bbb3aab58a30d8e8b37ef95ad6e78da2c3513a3a707a2a5bbb459b65aeef9'
EVIDENCE = dict(line.split('|', 1) for line in (OWN / 'test_case_evidence.txt').read_text(encoding='utf-8').splitlines())
# Each suffix is an authored semantic exclusion for its individual perspective.
NEG = {
'T01_P1': '보조금 설명·자격·예산 서류 반복 대조와 중심 업무가 다름.',
'T01_P2': '부서별 보조금 심사기준·자격·예산 오류 문제가 아님.',
'T01_P3': '보조금 심사근거 기록의 분산·감사추적 문제가 아님.',
'T02_P1': '자유서술 설문에서 조치 가능한 의견을 고르는 업무가 아님.',
'T02_P2': '가치 낮은 설문응답에 검토시간을 쓰는 문제가 아님.',
'T03_P1': '자유서술 이관자료에서 필수 접수항목을 파악하는 업무가 아님.',
'T03_P2': '이관정보 수동기록의 불일치·누락 문제가 아님.',
'T03_P3': '기관 간 이관정보 추가확인·재요청 지연이 아님.',
'T04_P1': '저시력 사용자의 일상 시각정보 접근 문제가 아님.',
'T04_P2': '시각정보를 타인의 설명에 의존하는 문제가 아님.',
'T05_P1': '언어회화 대본 때문에 실제 표현을 바꾸기 어려운 문제가 아님.',
'T05_P2': '언어 대화연습 상대에 접근하기 어려운 문제가 아님.',
'T05_P3': '개별 언어 오답의 맥락형 설명 부족이 아님.',
'T06_P1': '사람이 여러 감시영상을 계속 지켜보는 업무가 아님.',
'T06_P2': '보안영상 사건 누락·사후확인에 따른 대응 지연이 아님.',
'T07_P1': '기사 수동번역 때문에 영문 발행이 늦는 문제가 아님.',
'T07_P2': '기사 번역의 용어·인명 표기 불일치·교정 문제가 아님.',
'T08_P1': '가변 상자 적재·하역의 반복 육체작업이 아님.',
'T08_P2': '물류 작업환경·하역인력에 따른 처리량 확장 문제가 아님.',
'T09_P1': '식품 매장·상품별 일일 수요·재고 예측이 아님.',
'T09_P2': '유통기한·재고를 고려한 상품 할인결정이 아님.',
'T09_P3': '식품 수요·할인 판단 지연의 폐기·품절 위험이 아님.',
'T10_P1': '감사자료 반려·재제출 안내문을 반복 작성하는 업무가 아님.',
'T10_P2': '감사자료 요건 안내의 누락·표현 불일치 문제가 아님.',
'T10_P3': '감사자료 고객 재제출·확인 왕복 지연이 아님.',
'T11_P1': '탑승권 이미지 필드 전사·추출오류 확인이 아님.',
'T11_P2': '고객의 여행 상황·제약을 이해해 답하는 업무가 아님.',
'T11_P3': '이동 중 복잡한 고객지원 문의를 처리하는 업무가 아님.',
'T12_P1': '결근·지각 전화접수와 근무시스템 재입력이 아님.',
'T12_P2': '담당자 부재·전달 불일치로 근무정보 반영이 늦는 문제가 아님.',
}

out = []
done = []
for q in DOC['queries']:
    path = OWN / (q['query_id'] + '.txt')
    if not path.exists():
        continue
    done.append(q['query_id'])
    lines = [line for line in path.read_text(encoding='utf-8').splitlines() if line.strip() and not line.startswith('#')]
    assert len(lines) == 117
    for number, line in enumerate(lines, 1):
        index, scores, reasons = line.split('|', 2)
        assert int(index) == number
        assert len(scores) == len(q['reference_perspectives']) and all(s in '01234' for s in scores)
        parts = reasons.split('~')
        assert len(parts) in (1, len(scores)) and all(p.strip() for p in parts)
        if reasons == 'N':
            assert set(scores) == {'0'}
        for j, p in enumerate(q['reference_perspectives']):
            reason = EVIDENCE[index] + '; ' + NEG[p['id']] if reasons == 'N' else parts[j] if len(parts) > 1 else parts[0]
            out.append(dict(query_id=q['query_id'], perspective_id=p['id'], case_id=DOC['cases'][number-1]['case_id'], relevance_0_4=int(scores[j]), reviewer_id='independent_ai_reviewer_B', rationale=reason + ' (관점: ' + p['title'] + ')', input_sha256=HASH))
assert len({(r['query_id'], r['perspective_id'], r['case_id']) for r in out}) == len(out)
full = len(done) == 12
if full:
    assert len(out) == 3510
destination = OWN / ('test.publish.tmp.csv' if full else 'test_relevance.partial.csv')
with destination.open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['query_id', 'perspective_id', 'case_id', 'relevance_0_4', 'reviewer_id', 'rationale', 'input_sha256'])
    w.writeheader()
    w.writerows(out)
if full:
    destination.replace(ROOT / 'test_relevance_pass_2.csv')
report = {'status': 'SEALED_TEST_AI_ANNOTATION' if full else 'PARTIAL_NOT_COMPLETE', 'queries': done, 'count': len(out), 'histogram': dict(sorted(Counter(r['relevance_0_4'] for r in out).items())), 'positive': sum(r['relevance_0_4'] >= 3 for r in out), 'input_sha256': HASH}
(OWN / 'test_progress.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
