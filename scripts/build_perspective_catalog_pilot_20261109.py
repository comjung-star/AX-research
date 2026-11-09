"""Assistant-curated, source-only pilot perspective cards; no scores or API calls."""
from collections import Counter
from itertools import combinations
import hashlib
import json

from scripts.improvement_cycle import ROOT, read

OUT = ROOT / 'docs/perspective-catalog-pilot-20261109'
REGISTRY = 'docs/dense-bm25-candidates-2026-10-27/case_registry.json'

CANDIDATES = [
    ('P01', '업무 지식이 길고 분산돼 필요한 근거를 찾는 데 시간이 걸림', ['AXALL_US_OMB_2025_02663', 'AXV2N_0110']),
    ('P02', '비정형 자료를 수기로 옮기고 업무 정보로 정리하는 부담', ['AXALL_US_OMB_2025_01589', 'AXV24_bc6444cc1b61']),
    ('P03', '업무 자료를 기준·다른 자료와 대조하는 검증 부담', ['AXALL_US_OMB_2025_01754', 'AXV2P2_0011_01']),
    ('P04', '문의량·접수 시간대가 응대 가능 용량을 넘어 대기·누락이 생김', ['AXV24_df5d48fedff4', 'AXV2H_0001_01']),
    ('P05', '채널이 바뀔 때 고객이 이전 상황을 반복 설명해야 함', ['AXV2C_0017_01']),
    ('P06', '상담·회의가 끝난 뒤 기록과 후속조치 정리에 시간이 걸림', ['AXV2H_0075_01', 'AXV2N_0111']),
    ('P07', '분산된 품질 기록 때문에 이상 원인 후보 파악이 늦음', ['AXV2C_0093_01', 'AXV2P2_0065_01']),
    ('P08', '설비 고장 전에 위험을 파악하기 어려워 운영 중단에 대비하지 못함', ['AXV2H_0021_01', 'AXV24_2be1ea1c5140']),
    ('P09', '상품 수요가 불확실해 공급 부족과 폐기를 함께 관리하기 어려움', ['AXV2C_0050_01']),
    ('P10', '생산 일정 변경이 느리고 입력·조정 오류가 발생함', ['AXV2C_0093_02']),
    ('P11', '번역 속도와 용어·문체의 일관성이 발행을 제약함', ['AXV24_523997b7101f']),
    ('P12', '광고 이미지 제작 비용·속도·현지 적합성이 캠페인을 제약함', ['AXV2N_0114', 'AXV2N_0116']),
    ('P13', '하역·고온·저온 환경의 물리적 작업이 사람에게 부담을 줌', ['AXV2N_0118', 'AXV2P2_0097_01', 'AXV2P2_0099_01']),
    ('P14', '생산 이미지에 사람이 식별 가능하게 남음', ['AXV2N_0136']),
    ('P15', '새 업무의 담당팀을 수작업으로 정하는 데 시간과 오배정이 생김', ['AXV2H_0083_01']),
    ('P16', '접수·상태변경·시스템 반영 같은 후속 행정처리가 반복됨', ['AXV24_f6f7a1e65ea7', 'AXV2N_0130']),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quote(cases, case, field, fragment=None):
    source = cases[case][field]
    value = source if fragment is None else fragment
    start = source.find(value)
    if start < 0 or not value:
        raise ValueError((case, field, value))
    return {'field': field, 'quote': value, 'start': start, 'end': start + len(value)}


def build(cases):
    def link(case, status, reason, supported_scope, condition_limit):
        return {'case_id': case, 'status': status, 'reason': reason, 'supported_scope': supported_scope,
                'condition_limit': condition_limit,
                'evidence': [quote(cases, case, f) for f in ('problem', 'task', 'context')],
                'unknown': ['원출판물의 전체 구현 범위는 이번에 재검증하지 않음', '다른 질문에 대한 관련성과 성능은 아직 평가하지 않음'],
                'query_relevance': 'NOT_EVALUATED', 'semantic_review': 'SAME_ASSISTANT_SOURCE_REVIEW_NOT_HUMAN_GOLD'}
    S, H, X = 'SUPPORTED_FOR_PILOT', 'HOLD', 'EXCLUDED_FROM_CARD'
    cards = [
        {'id': 'P01', 'name': CANDIDATES[0][1],
         'definition': '이미 존재하는 업무 문서·지식이 길거나 여러 곳에 있어 필요한 근거를 찾아 업무에 쓰기 어렵다.',
         'include_if': ['Problem에 정보 탐색·이해의 시간/접근 부담이 있음', 'Task에 문서·지식 검색 또는 참조 지원이 명시됨'],
         'exclude_if': ['문서라는 이유만으로 연결', '요약·번역·정형데이터 조회만 있고 문서/지식 검색 근거는 없음'],
         'query_conditions': ['사용자가 기존 자료에서 정보를 찾거나 참조하려 함', '단순 검색 지원과 답변 작성·실행 권한을 구분'],
         'unknown': ['검색 색인·문서 갱신·접근권한의 구현 범위', '답변 생성 및 정확도 보장은 사례마다 추가 확인'],
         'links': [
             link('AXALL_US_OMB_2025_02663', S, '긴 문서·정책의 탐색 병목과 검색·교차참조 작업이 함께 명시됨.', '문서 검색 및 교차참조 지원', '정책 승인이나 규제 적합성 확정 기능까지 뜻하지 않음'),
             link('AXV2N_0110', S, '금융자문 직원의 내부문서 탐색 시간이 문제이고 지식 검색을 수행함.', '내부 지식 검색', '외부 고객의 금융판단 대행으로 확대하지 않음'),
             link('AXV2P2_0010_01', S, '접근하기 어려운 제품 전문지식을 검색하는 작업이 명시됨.', 'CAD/CAM 지원지식 검색', '제품 조작·설계 변경의 자동 실행은 미확인'),
             link('AXV24_f27ca1e6fb82', S, '다수 업무시스템 정보 활용에 별도 연동 부담이 있고 통합 검색을 수행함.', '여러 시스템의 지식 통합 검색', '임의 시스템의 읽기/쓰기 권한을 갖는다는 뜻은 아님'),
             link('AXV2H_0078_01', H, '정보 접근 문제는 비슷하지만 Task는 기업 관리데이터의 자연어 조회임.', '정형 관리데이터 조회', '문서 검색과 같은 관점에 묶을지 원자료·인터페이스 범위를 더 확인해야 함'),
             link('AXV2H_0081_01', X, '금융권 사례라는 공통점이 있어도 핵심 작업은 상담 대화록 요약임.', '상담 후 기록 요약', '이 요약에 문서·지식 검색을 수행한다는 근거는 없음'),
             link('AXV2N_0139', X, '계약 내용을 이해하기 쉽게 요약하는 업무로 검색 작업 근거가 없음.', '계약 요약', '검색과 요약을 동일 기능으로 연결하지 않음'),
         ]},
        {'id': 'P02', 'name': CANDIDATES[1][1],
         'definition': '문서·자유서술 자료에서 필요한 정보를 수기로 꺼내거나 옮겨 업무 데이터로 만드는 데 부담이 있다.',
         'include_if': ['자료 형식·비정형성·수기 입력의 부담이 명시됨', 'Task에 정보 추출·구조화·분류가 명시됨'],
         'exclude_if': ['문서를 읽는 모든 업무를 포함', '내용 검증·번역·요약만 수행하고 정보 추출·구조화는 확인되지 않음'],
         'query_conditions': ['원자료에서 필요한 항목을 꺼내 정리하려는 요청', '추출 결과를 시스템에 쓰는 행위는 별도 권한·기능 확인'],
         'unknown': ['정확한 출력 스키마와 필드별 추출 정확도', '추출 항목의 사실 검증·자동 등록 여부'],
         'links': [
             link('AXALL_US_OMB_2025_01589', S, '신청 PDF의 수기 전사로 지연·오류가 생기며 문서 데이터 추출을 수행함.', '대출 문서 데이터 추출', '대출 승인·사실 확인까지 수행한다고 해석하지 않음'),
             link('AXV24_bc6444cc1b61', S, '다양한 청구서 PDF에서 가입자 정보를 수동 복사하는 부담과 추출 Task가 일치함.', '견적용 청구서 정보 추출', '보험 견적 산정이나 심사 판단 자체는 미확인'),
             link('AXV2C_0080_01', S, '대량 무역문서의 수기 입력 부담에 대해 필드 추출을 수행함.', '무역금융 문서 필드 추출', '규제위험 판단·제재 심사로 확대하지 않음'),
             link('AXV24_98092b8ca357', S, '카탈로그 세부정보의 수동 추출·정리 부담과 속성 추출·분류가 명시됨.', '상품 속성 추출·분류', '상품 검색·추천 기능 자체의 증거는 아님'),
             link('AXV24_28baf265c6cf', S, '형식이 다른 보험 자료를 수작업으로 추출하는 부담과 추출·분류 Task가 명시됨.', '보험 신청 서류 추출·분류', '최종 보험 인수 결정은 미확인'),
             link('AXALL_US_OMB_2025_01754', S, '자유서술 자료의 수동·불일치 추적에 대해 데이터 구조화를 수행함.', '의뢰 자료 데이터 구조화', '필수항목 확인도 별도 명시되어 P03과 중복 연결하되 역할을 구분'),
             link('AXV24_efe56d53f5fd', H, '추출 기능은 있지만 Problem은 추출 오류와 고객불만으로 수기 정리 부담은 명시되지 않음.', '탑승권 추출·오류 확인', '기능만 같다는 이유로 문제 관점의 직접 연결로 확정하지 않음'),
             link('AXV2H_0003_01', X, '문서 관련 업무지만 Task는 보고서 검증이며 정보 추출 근거는 없음.', '보고서 검증', 'P03의 근거와 P02의 근거를 혼동하지 않음'),
         ]},
        {'id': 'P03', 'name': CANDIDATES[2][1],
         'definition': '업무 문서·등록 데이터의 내용이나 필수항목을 다른 자료 또는 기준과 대조해야 하므로 검토 부담·오류·누락이 생긴다.',
         'include_if': ['Problem 또는 Task에 자료·기준·필수항목을 대조하는 확인 부담이 있음', '실제 Task에서 검증·대조·완전성 점검·감사를 수행함'],
         'exclude_if': ['같은 문서·업종·검증 단어만 공유', '추출만 수행', '물리 제품 영상검사 또는 이상탐지만 있고 문서/기준 대조는 불명확'],
         'query_conditions': ['문서·등록 데이터의 확인 대상과 기준을 식별할 수 있음', '검토 목록 작성과 수정·승인·차단은 분리'],
         'unknown': ['검증 규칙과 오류 유형의 세부 범위', '수정·병합·지급 보류·자동 승인 권한'],
         'links': [
             link('AXALL_US_OMB_2025_01754', S, '필수 의뢰항목 누락이 문제이고 Task에 완전성 점검이 명시됨.', '필수항목 완전성 점검', '구조화 자체는 P02, 내용 누락 확인은 P03의 별도 근거'),
             link('AXV2C_0006_02', S, '주문가격 불일치·입력 오류 문제에 대해 청구 전 가격 검증을 수행함.', '고객 주문가격 검증', '가격 자동변경·대금 지급 실행은 미확인'),
             link('AXV2H_0003_01', S, '다수 파일과 검증기준을 수작업 대조하는 부담이 있고 보고서 검증을 수행함.', '신원조회 보고서의 기준 대조 검증', '채용 의사결정·신원 사실의 절대 보장으로 해석하지 않음'),
             link('AXV2P2_0011_01', S, '운송 청구서와 약정요율 불일치를 확인하는 수기 부담과 감사 Task가 명시됨.', '청구서 과다청구 감사', '환급·대금차감 자동 실행은 미확인'),
             link('AXV24_36c7ef329920', S, '대량 지원서·증빙 검토의 인력 부담과 대조 검토 Task가 명시됨.', '지원서·증빙 자료 대조', '지원자의 최종 합격판정과 별개'),
             link('AXV2C_0068_01', H, '불완전 지급지시 문제는 관련되지만 실제 Task는 Repair로 단순 확인보다 강한 행위임.', '불완전 지급지시 수정', '수정 없는 점검 요청에 연결하려면 읽기/확인만 지원하는 범위를 별도 확인'),
             link('AXV24_e9e5114a33fe', H, '경비 정책위반·이상 탐지는 관련될 수 있으나 어떤 기준·자료를 대조하는지 요약만으로 불명확함.', '경비 이상·정책위반 탐지', '규칙 대조와 맥락 기반 이상탐지의 역할을 구분할 근거 필요'),
             link('AXV24_efe56d53f5fd', H, '오류 확인은 수행하지만 어떤 기준과 대조하는지 명시되지 않음.', '탑승권 추출 오류 확인', '기준 대조 관점에 직접 연결하려면 검증 근거 추가 확인'),
             link('AXV2N_0135', X, '검증이라는 단어는 같지만 카메라로 차량 부품의 라벨을 검사하는 물리적 작업임.', '차량 라벨 영상검사', '이번 문서/등록 데이터 대조 관점과 입력·작업 조건이 다름'),
         ]},
        {'id': 'P04', 'name': CANDIDATES[3][1],
         'definition': '문의가 몰리거나 기존 응대경로가 처리하지 못해 사람의 응대용량과 시간대 한계를 넘어 대기·누락이 생긴다.',
         'include_if': ['Problem에 문의량·응대공백·상담원 쏠림과 대기/처리 부담이 있음', 'Task에 실제 문의 응대가 명시됨'],
         'exclude_if': ['고객상담 업종이라는 이유만으로 연결', '검색 품질·상담 후 요약이 문제의 중심이고 응대용량 근거는 없음'],
         'query_conditions': ['사용자 질문에 문의처리 대기·공백·용량 문제의 근거가 있음', '야간 응대·음성/문자 채널·사람 인계는 각 사례의 지원 근거를 개별 확인'],
         'unknown': ['지원 시간대·채널·예외처리 범위', '모든 문의의 완결 처리나 거래 실행 여부'],
         'links': [
             link('AXV24_df5d48fedff4', S, '계절성 문의와 야간 공백으로 대기·누락이 생기며 상시 응대 및 인계 Task가 명시됨.', '상시 문의 응대·상담원 인계', '인계 자체는 명시됐지만 인계 시 맥락 손실 해결 효과까지 증명하지 않음'),
             link('AXV2H_0001_01', S, '대량 문의로 정시/영업외 대응 유지가 어려우며 문의 자율응답을 수행함.', '서면 고객 문의 응답', '음성이나 CRM변경 기능으로 확대하지 않음'),
             link('AXV2P2_0060_01', S, '대량 고객 문의가 지원조직을 압도하고 지연을 만들며 고객응대를 수행함.', '항공 고객서비스 질문 응답', '이 요약만으로 야간·모든 채널·예약변경 실행을 보장하지 않음'),
             link('AXV24_71def85d86bd', S, '정형 자격·보장 문의의 상담원 쏠림으로 대기 부담이 있고 음성 문의에 응대함.', '보험 자격·보장 음성 문의 응대', '청구 승인·보험금 지급·24시간 지원은 이 요약에서 확정하지 않음'),
             link('AXV2N_0123', H, '고객응대 Task는 있으나 Problem의 초점은 정적 지식과 느린 답변·수동 색인임.', '은행 챗봇 문의 응대', '용량 초과가 지연의 핵심인지 지식 갱신 문제가 핵심인지 추가 확인'),
             link('AXV2C_0092_01', X, '은행 고객문의라는 공통점이 있어도 Problem은 복잡한 답을 찾기 어려운 문제임.', '금융질문 채팅 응답', '대량·시간대 공백·상담원 쏠림의 근거가 없어 이번 관점에 넣지 않음'),
             link('AXV2H_0081_01', X, '고객지원 사례지만 Task는 상담 종료 후 대화록 요약임.', '상담 후 기록 요약', '실시간 문의 응답·대기 해소 기능이 이 요약에 명시되지 않음'),
         ]},
    ]
    pair_reviews = [
        ('P01', 'P02', '검색은 이미 있는 정보에 접근하는 문제, 추출은 원자료를 업무 항목으로 정리하는 문제다. 문서가 공통이어도 합치지 않음.'),
        ('P01', 'P03', '근거 탐색과 기준 대조 검증은 필요한 수행 기능이 다르다. 검색만으로 사실 검증을 수행했다고 보지 않음.'),
        ('P01', 'P04', '지식 접근 지연과 문의 응대용량은 다른 병목이다. 검색이 응대에 쓰여도 원문에 두 문제 근거가 있어야 각각 연결.'),
        ('P02', 'P03', '추출·구조화와 완전성/정합성 확인을 분리한다. 의뢰 자료 사례는 Task에 두 작업이 모두 명시돼 양쪽 연결을 허용.'),
        ('P02', 'P04', '문서 정보 정리와 문의 응대는 입출력·실제 작업이 다르다. 시간절감이라는 일반 목적만으로 합치지 않음.'),
        ('P03', 'P04', '자료의 기준 대조와 문의 응답의 처리용량은 다른 문제다. 고객업무라는 공통점으로 연결하지 않음.'),
    ]
    reviews = []
    for a, b, reason in pair_reviews:
        left = next(c for c in cards if c['id'] == a)
        right = next(c for c in cards if c['id'] == b)
        sets = [{v['case_id'] for v in c['links'] if v['status'] == S} for c in (left, right)]
        reviews.append({'pair': [a, b], 'decision': 'KEEP_SEPARATE_IN_PILOT', 'reason': reason,
                        'shared_supported_cases': sorted(sets[0] & sets[1])})
    candidates = [{'id': i, 'problem_candidate': name, 'seed_cases': ids,
                   'status': 'PILOT_CARD_REVIEWED' if i in ('P01', 'P02', 'P03', 'P04') else 'CANDIDATE_ONLY_NOT_FULLY_REVIEWED'}
                  for i, name, ids in CANDIDATES]
    return {'version': 'case-grounded-perspective-catalog-pilot-v1-20261109', 'candidate_pool': candidates,
            'cards': cards, 'pair_reviews': reviews, 'applicability_policy': {
                'eligible_links': S, 'hold_links_are_not_recommendation_evidence': True,
                'no_match_result': 'SUPPORTED_PERSPECTIVE_OR_CASE_NOT_FOUND', 'force_perspective_selection': False,
                'any_user_query_requires_new_scope_check': True, 'multiple_links_per_case_allowed_with_distinct_evidence': True},
            'review_provenance': 'Assistant-authored and self-reviewed using stored summaries; not independent human validation',
            'case_inventory_size': len(cases), 'full_case_classification_complete': False,
            'paid_calls': 0, 'relevance_scores_read': False, 'new_predictions': 0, 'runtime_selector_implemented': False}


def validate(catalog, cases):
    statuses = {'SUPPORTED_FOR_PILOT', 'HOLD', 'EXCLUDED_FROM_CARD'}
    card_ids = {c['id'] for c in catalog['cards']}
    assert len(card_ids) == len(catalog['cards'])
    for candidate in catalog['candidate_pool']:
        assert all(case in cases for case in candidate['seed_cases'])
    evidence_checks = 0
    for card in catalog['cards']:
        assert card['definition'] and card['include_if'] and card['exclude_if'] and card['query_conditions'] and card['unknown']
        seen = set()
        for link in card['links']:
            case = link['case_id']
            assert case in cases and case not in seen
            seen.add(case)
            assert link['status'] in statuses
            assert link['reason'] and link['supported_scope'] and link['condition_limit'] and link['unknown']
            assert link['query_relevance'] == 'NOT_EVALUATED'
            for evidence in link['evidence']:
                source = cases[case][evidence['field']]
                assert source[evidence['start']:evidence['end']] == evidence['quote'] and evidence['quote']
                evidence_checks += 1
            assert {e['field'] for e in link['evidence']} >= {'problem', 'task', 'context'}
        assert any(link['status'] == 'SUPPORTED_FOR_PILOT' for link in card['links'])
        assert any(link['status'] == 'EXCLUDED_FROM_CARD' for link in card['links'])
    assert {tuple(r['pair']) for r in catalog['pair_reviews']} == set(combinations(sorted(card_ids), 2))
    for review in catalog['pair_reviews']:
        assert review['reason'] and review['decision']
    return evidence_checks


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    cases = read(REGISTRY)['cases']
    assert len(cases) == 112
    catalog = build(cases)
    checks = validate(catalog, cases)
    statuses = Counter(link['status'] for card in catalog['cards'] for link in card['links'])
    unique_supported = {link['case_id'] for card in catalog['cards'] for link in card['links'] if link['status'] == 'SUPPORTED_FOR_PILOT'}
    sources = [REGISTRY, 'scripts/build_perspective_catalog_pilot_20261109.py', 'docs/perspective-catalog-pilot-20261109-protocol.md']
    OUT.mkdir()
    for name, value in [('catalog.json', catalog), ('verification.json', {
        'state': 'PASS_STRUCTURAL_AND_LITERAL_CHECKS_WITH_DOCUMENTED_SEMANTIC_SELF_REVIEW',
        'candidate_count': len(catalog['candidate_pool']), 'pilot_card_count': len(catalog['cards']),
        'link_status_counts': dict(statuses), 'unique_supported_cases': len(unique_supported),
        'literal_evidence_spans_checked': checks, 'pairwise_boundary_reviews': len(catalog['pair_reviews']),
        'independent_semantic_validation': False, 'full112_coverage_or_recall_claim': False,
        'source_sha256': {p: sha(ROOT / p) for p in sources}, 'paid_calls': 0, 'new_predictions': 0})]:
        with (OUT / name).open('x', encoding='utf-8') as target:
            target.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    loaded = json.loads((OUT / 'catalog.json').read_text(encoding='utf-8'))
    assert loaded == build(cases) and validate(loaded, cases) == checks
    print(json.dumps({'candidates': len(catalog['candidate_pool']), 'cards': len(catalog['cards']),
                      'links': dict(statuses), 'unique_supported_cases': len(unique_supported), 'literal_checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()
