"""Define fresh policy validation expectations before any ABC model output."""
from decimal import Decimal

from ax_research.heldout import read, write, sha
from scripts import evaluator_abc as run
from scripts import autonomous_ax_gate as legacy


def fresh_examples():
    # Synthetic controls exercise policy, not retrieval rank or corpus-specific answers.
    return [
        ('진동이 갑자기 커지는 순간을 알리는 사례로 내일 베어링 고장을 예측하고 싶습니다.',
         'Detect present vibration spikes and alert the operator.','Only current measurements are checked.',[0,1],False,'temporal'),
        ('오늘 확인된 계좌 잔액을 조회해 그대로 보여주세요.',
         'Forecast next quarter cash balances.','The implemented output is a future forecast, not current-balance lookup.',[0,1],False,'temporal'),
        ('핵심은 청구 금액과 계약 요율을 대조해 오류 항목을 검증하는 것입니다. 추출은 준비 단계입니다.',
         'Extract invoice line items into a table.','No comparison or validation function is implemented.',[1],False,'auxiliary'),
        ('계약서에서 회사명과 만료일을 추출해 표로 보여주세요.',
         'Check entered amounts against a policy and flag violations.','No field-extraction table is produced.',[0,1],False,'auxiliary'),
        ('인사 규정에 관한 질문에 문서 근거로 답변하고 싶습니다.',
         'Generate product advertising images.','This is an implemented image-generation workflow.',[0],False,'unrelated'),
        ('운영 기록을 요약하고 싶습니다. 실제 사례의 수행 기능을 비교해 주세요.',
         '', 'No description of the implemented function is available.',[],True,'insufficient'),
        ('수요량을 예측하는 기능을 찾고 싶습니다.',
         'Prepare a proposal for AI adoption.','Implementation has not been confirmed.',[],True,'insufficient'),
        ('발주서 초안을 만들고 사람에게 최종 전송 승인을 남깁니다.',
         'Generate purchase-order drafts.','A person approves final sending; AI does not send orders.',[3],False,'authority'),
        ('고객 기록을 읽어 보여주기만 하고 값을 바꾸지 않습니다.',
         'Automatically change stored customer account values.','No read-only display function is specified.',[0,1],False,'authority'),
        ('직원의 사내 안내 문서 질문에 근거를 찾아 답변하고 싶습니다.',
         'Answer resident questions using municipal service manuals.','The source workflow is document-based answers in another domain.',[2],False,'transfer'),
        ('제품 설명에서 정해진 속성을 추출해 검토용 표로 정리하고 싶습니다.',
         'Extract specified attributes from inspection reports into review tables.','The input domain differs, but extraction and tabulation are implemented.',[2],False,'transfer'),
        ('접수한 고객 의견에서 주제를 분석하고 근거 의견이 포함된 요약을 만들고 싶습니다.',
         'Analyze customer feedback themes and generate summaries with supporting comments.','The actual output is a theme summary with source feedback.',[3],False,'direct'),
        ('서버 설정을 자동으로 변경하는 실행 기능이 필요합니다.',
         'Recommend server settings for an administrator.','The system only recommends; it does not execute changes.',[0,1],False,'execution'),
        ('제품 사진을 유지하면서 새로운 광고 배경 장면을 생성하고 싶습니다.',
         'Anonymize faces in production photographs.','It removes identifying details; no new scene generation is implemented.',[0,1],False,'auxiliary'),
        ('고객 상담 대화를 요약하고 원문 위치도 함께 제시해 주세요.',
         'Summarize customer support conversations and provide source locations.','The implemented output includes summaries and traceable conversation references.',[3],False,'direct'),
        ('문서 분류 기능과 실제 사례를 비교하고 싶습니다.',
         'Unknown.', 'Only the system name is recorded; actual work is not described.',[],True,'insufficient'),
    ]


def main():
    out=run.OUT;out.mkdir(exist_ok=False)
    records=[]
    for f in legacy.fixtures():
        records.append({'id':f'L{len(records)+1:03}','split':'REPRODUCTION','text':f['text'],
                        'case':{k:f['case'][k] for k in ('Problem','Task','Context')},
                        'expected':f['expected_grade_band'],'expected_abstain':f['expected_uncertain'],
                        'kind':'previous_failure_reproduction'})
    for q,t,c,band,abstain,kind in fresh_examples():
        records.append({'id':f'N{len(records)-7:03}','split':'FRESH_VALIDATION','text':q,
                        'case':{'Problem':'A business workflow needs assistance.','Task':t,'Context':c},
                        'expected':band,'expected_abstain':abstain,'kind':kind})
    write(out/'benchmark.json',{'records':records,'expected_values_frozen_before_model_outputs':True,
                               'expected_values_source':'policy-derived synthetic examples; no human Gold',
                               'no_recommendation_results_used':True,'prompt_commit':'065eccea'})
    prior=read(run.PRIOR/'pending75.json')['records']
    cases=read(run.ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    questions={q['query_id']:q['text'] for q in legacy.jsonl(run.transport.old.QUESTIONS)}
    pending=[{'id':p['id'],'query_id':p['query_id'],'case_id':p['case_id'],'text':questions[p['query_id']],
              'case':{'Problem':cases[p['case_id']]['problem'],'Task':cases[p['case_id']]['task'],
                      'Context':cases[p['case_id']]['context']}} for p in prior]
    write(out/'pending_items.json',{'records':pending})
    protected={p.relative_to(run.ROOT).as_posix():sha(p) for p in run.PRIOR.rglob('*') if p.is_file()}
    protected.update(read(run.PRIOR/'preregistration.json')['protected_sha256'])
    write(out/'protocol.json',{
        'base_commit':'76b1cc93a859086d3f07dfe9b315ef6475a58cd0','prompt_commit_before_fresh_examples':'065eccea',
        'prompt_file_sha256':sha(run.ROOT/'scripts/evaluator_abc_prompts.py'),'protected_sha256':protected,
        'common_rubric':run.prompts.COMMON,'methods':{'A':'Legacy direct assessment, common clarified rubric and single-case request','B':'Independent query-only and case-only extraction, then direct comparison','C':'Same frozen separate extractions, evidence-first ordered checks, explicit program decision rules'},
        'same_material_and_common_criterion':True,'fresh_examples':16,'reproduction_examples':8,
        'fresh_expected_values_not_human_Gold':True,'selection_uses_only_fresh_controls':True,
        'selection_order':['minimize dangerous false-high>=2 on low-core cases and false0 on missing-source cases','maximize expected-band adherence','minimize output/evidence failures','maximize grade/relevance agreement'],
        'no_method_tuning_after_fresh_outputs':True,'source_case_extraction_never_sees_question':True,
        'shared_B_C_extractions':True,'single_case_per_request':True,
        'quotes':'Program maps T/C anchor IDs to exact original field and character range. Never fabricate quotations. Legacy exact quotes may relocate to the correct permitted field without changing the text or grade.',
        'retry_policy':{'max_extra_attempts':1,'allowed':sorted(run.TECHNICAL),'not_allowed':['valid low scores','semantic disagreement','Problem as performed evidence','uncertain transport or credit/auth errors'],'all_raw_and_cost_preserved':True},
        'human_approval_obtained':False,'new_labels_status':'AI provisional, not verification-complete or Human-Gold',
        'algorithm_entry':'All major policy/source controls pass; meaningful unresolved decisions appropriately retained; common-label fair comparison and sensitivity cannot reverse the claimed comparison. Otherwise technical cleanup and expert queue, no forced tuning.',
        'max_algorithm_iterations':5,'goals':{'F1@5_delta':.05,'nDCG@10_delta':.03,'paired_bootstrap95_lower_above':0,'Top5_Jaccard':.90,'reliable_labels':True,'new_independent_Test_replication':True},
        'work_API_cap_usd':2,'provider_subcaps_usd':{k:str(v) for k,v in run.CAPS.items()},
        'prior_Claude_known_usd':'1.850220','Claude_safety_usd':'.50','additional_topup':False,
        'independent_Test40':'Separate frozen-model stage; not part of evaluator development or selection',
    })
    expected={'openai':Decimal(0),'claude':Decimal(0)}
    for provider in expected:
        inp,outp=(Decimal('.10'),Decimal('.50')) if provider=='openai' else (Decimal(1),Decimal(5))
        # Scenario estimate, not an upper guarantee. Every request also has a hard reserved-cost subcap.
        benchmark_calls=24*5
        unique_cases=len({run.transport.digest(p['case']) for p in pending})
        pending_calls=75+8+unique_cases
        expected[provider]=(Decimal(benchmark_calls+pending_calls)*(700*inp+350*outp))/1_000_000
    write(out/'budget_preflight.json',{'scenario_estimate_usd':{p:str(x) for p,x in expected.items()},
        'scenario_total_usd':str(sum(expected.values())),'not_a_maximum_guarantee':True,'max_reserved_before_each_call':True,
        'provider_caps_sum_usd':str(sum(run.CAPS.values())),'all_work_cap_usd':2,
        'basis':'24 controls, three methods with shared separate extraction;75 cases,8 cached question cores and unique cached case cores;700 input/350 output tokens per call scenario.',
        'technical_retry_reserve':'within hard provider subcaps; no retry of uncertain requests',
        'prices':['https://developers.openai.com/api/docs/models/gpt-6-luna','https://platform.claude.com/docs/en/about-claude/pricing']})
    (out/'.gitattributes').write_text('** -text whitespace=cr-at-eol\n',encoding='utf-8')
    print('Prepared24 controls and75 pending pairs; expected scenario USD',sum(expected.values()),flush=True)


if __name__=='__main__':main()
