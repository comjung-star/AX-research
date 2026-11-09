"""Source-grounded reference axes, not runtime slots or evaluated relevance labels."""
import hashlib
import json

from scripts.improvement_cycle import ROOT, read

OUT = ROOT / 'docs/dynamic-perspective-evidence-20261109'
AXES = [
    {'id': 'information_access', 'name': '필요한 정보에 접근하고 이해하기 어려움',
     'question': '찾아야 할 지식이나 설명이 어디에서 막히는가?',
     'examples': ['AXALL_US_OMB_2025_02663', 'AXV2N_0110', 'AXV2P2_0010_01'],
     'guard': '질문에 검색·조회·이해의 어려움이 있을 때만 사용. 문서가 있다는 이유만으로 검색 관점을 만들지 않음.'},
    {'id': 'record_structure', 'name': '자료를 업무에 쓸 수 있도록 정리·기록하는 부담',
     'question': '어떤 자료가 비정형이거나 수기 입력에 의존하는가?',
     'examples': ['AXV24_bc6444cc1b61', 'AXV24_98092b8ca357', 'AXV2N_0132'],
     'guard': '추출·정리·기록의 요청 근거가 있어야 함. 입력 자료가 있다는 것과 정리 작업이 필요하다는 것은 다름.'},
    {'id': 'verification_detection', 'name': '오류·누락·현재 이상을 놓치는 문제',
     'question': '무엇이 맞지 않거나 빠졌는지, 현재 어떤 이상이 있는지 확인하기 어려운가?',
     'examples': ['AXALL_US_OMB_2025_01754', 'AXV2C_0006_02', 'AXV2N_0117'],
     'guard': '문서 대조·제품 결함·이상 사건을 구체적 대상으로 분리. 현재 탐지를 미래 예측과 동일시하지 않음.'},
    {'id': 'pattern_explanation', 'name': '현상의 원인 후보·추세·판단 맥락을 파악하기 어려움',
     'question': '발생한 현상에 어떤 공통 조건이나 설명 근거가 있는가?',
     'examples': ['AXV2C_0093_01', 'AXV2P2_0065_01', 'AXV2N_0126'],
     'guard': '원인 후보나 추세 분석을 인과관계의 확정으로 바꾸지 않음. 단순 탐지와 설명 요구를 구분.'},
    {'id': 'future_planning', 'name': '미래 수요·위험과 계획의 불확실성',
     'question': '앞으로 무엇이 얼마나 발생할지, 어떤 계획을 세울지 판단하기 어려운가?',
     'examples': ['AXV2C_0050_01', 'AXV24_2be1ea1c5140', 'AXV2C_0093_02', 'AXV2C_0094_02'],
     'guard': '수요 예측·고장 예측·일정 계획은 이 축 안에서도 다른 문제다. 질문에 있는 세부 문제만 생성하고 상호 대체하지 않음.'},
    {'id': 'capacity_service_gap', 'name': '처리량 증가·응대 공백·반복 처리의 병목',
     'question': '어느 시간대나 처리 단계에서 대기와 누락, 인력 부담이 생기는가?',
     'examples': ['AXV2H_0001_01', 'AXV24_df5d48fedff4', 'AXV24_36c7ef329920'],
     'guard': '모든 문제를 비용절감/자동화로 바꾸지 않음. 과부하·대기·공백이라는 명시 근거가 필요.'},
    {'id': 'handoff_integration', 'name': '담당자·채널·시스템 사이의 전달과 연결 단절',
     'question': '담당자 전환이나 시스템 이동에서 어떤 맥락·처리 연결이 끊기는가?',
     'examples': ['AXV2C_0017_01', 'AXV2H_0083_01', 'AXV2P2_0069_01', 'AXV24_f6f7a1e65ea7'],
     'guard': '인계·배정·등록·갱신은 각각 다른 행동. 질문이 조회만 허용하면 시스템 쓰기/자동 실행을 제안하지 않음.'},
    {'id': 'content_production', 'name': '결과물 작성·제작의 부담과 품질·맞춤화 문제',
     'question': '어떤 결과물을 만드는 데 시간이 들거나 품질과 적합성이 흔들리는가?',
     'examples': ['AXV24_523997b7101f', 'AXV2N_0116', 'AXV2C_0074_01'],
     'guard': '번역·이미지 생성·답변 작성은 별도 작업. 모든 요약이나 검색을 생성 작업과 같게 취급하지 않음.'},
    {'id': 'physical_work_safety', 'name': '현장 작업의 육체적 부담·환경 위험',
     'question': '어떤 물리적 작업이나 환경이 사람에게 부담과 위험을 주는가?',
     'examples': ['AXV2N_0118', 'AXV2P2_0097_01', 'AXV2P2_0099_01'],
     'guard': '문서 처리와 구별되는 물리적 작업 축. 작업 부담의 언급만으로 실제 안전 개선 효과를 수치화하지 않음.'},
    {'id': 'privacy_protection', 'name': '개인정보가 남거나 노출되는 문제',
     'question': '어떤 자료에서 누가 식별될 수 있으며 무엇을 보호해야 하는가?',
     'examples': ['AXV2N_0136'],
     'guard': '직접 비식별 작업을 수행하는 예시는 이번 목록에서 한 건을 근거로 제시. 보안 전반·권한 관리·법적 준수 전체의 성능 근거로 확대하지 않음.'},
]


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    path = ROOT / 'docs/dense-bm25-candidates-2026-10-27/case_registry.json'
    cases = read(path.relative_to(ROOT).as_posix())['cases']
    axes = []
    for definition in AXES:
        examples = []
        for case in definition['examples']:
            row = cases[case]
            examples.append({'case_id': case, 'problem_quote': row['problem'], 'performed_task_quote': row['task'],
                             'context_quote': row['context'], 'source_fields': ['problem', 'task', 'context']})
        axes.append({**definition, 'examples': examples})
    assert len(cases) == 112 and len(axes) == 10
    OUT.mkdir()
    result = {'state': 'SOURCE_EVIDENCE_FOR_DYNAMIC_PERSPECTIVE_REFERENCE_AXES', 'case_count_reviewed': len(cases),
              'reference_axes': axes, 'example_references': sum(len(a['examples']) for a in axes),
              'case_registry_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'script_sha256': hashlib.sha256((ROOT / 'scripts/map_dynamic_perspective_evidence_20261109.py').read_bytes()).hexdigest(),
              'not_fixed_runtime_slots': True, 'not_exhaustive_case_labels': True,
              'not_independently_validated_semantic_taxonomy': True, 'no_frequency_estimate': True,
              'runtime_rule': 'Generate only source-grounded problem perspectives from the user query; count and titles vary; corpus gap is reported, not silently removed',
              'constraints': ['Temporal direction', 'Human approval and execution permission', 'Data privacy', 'Scope of desired output'],
              'paid_calls': 0, 'new_predictions': 0, 'relevance_labels_read': False,
              'limitations': ['Stored case summaries, not a renewed original-publication audit',
                              'Axes are analyst proposals with literal examples, not learned clusters or Gold',
                              'Examples establish corpus support, not suitability for an arbitrary new query',
                              'No performance improvement claim or new dynamic-generation experiment']}
    with (OUT / 'evidence.json').open('x', encoding='utf-8') as target:
        target.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    actual = json.loads((OUT / 'evidence.json').read_text(encoding='utf-8'))
    for axis in actual['reference_axes']:
        for example in axis['examples']:
            source = cases[example['case_id']]
            assert example['problem_quote'] == source['problem'] and example['performed_task_quote'] == source['task'] and example['context_quote'] == source['context']
    print(json.dumps({'case_inventory': len(cases), 'proposed_reference_axes': len(axes),
                      'literal_example_references_verified': result['example_references'], 'paid_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
