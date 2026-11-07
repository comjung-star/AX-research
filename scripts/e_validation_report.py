"""Korean validation report. Saved rankings are never recomputed or tuned."""
from collections import Counter, defaultdict
from decimal import Decimal
from statistics import mean
import json

from ax_research.heldout import read, write, sha
from scripts import e_validation as run

NAMES={'v0_original':'기존 판정', 'v1_missing_only':'미판정29건 재검토',
       'v2_reviewed_strict':'두 검토 등급 일치만 확정',
       'v2_openai_sensitivity':'GPT 단독 판단 민감도',
       'v2_second_reviewer_sensitivity':'두 번째 검토자 단독 민감도'}


def pct(x):
    return '계산 보류' if x is None else f'{100*x:.2f}%'


def pp(x):
    return '계산 보류' if x is None else f'{100*x:+.2f}%p'


def main():
    out=run.OUT
    stage1=read(out/'stage1_summary.json')
    review=read(out/'relevance_reviews.json')
    quality=read(out/'quality_revalidation.json')
    index=read(out/'evaluation_index.json')
    ledger=run.ledger()
    evaluations={v:read(out/v/'evaluation.json') for v in index['versions']}
    versions={v:read(out/v/'labels.json')['records'] for v in index['versions']}
    predictions=read(run.old.OUT/'predictions.json')
    qs=predictions['query_ids']
    label={(r['query_id'],r['case_id']):r for r in versions['v2_reviewed_strict']}
    original={(r['query_id'],r['case_id']):r for r in versions['v0_original']}
    grouped=defaultdict(list)
    for row in review['records']:grouped[row['query_id'],row['case_id']].append(row)
    comparable=[rs for rs in grouped.values() if all(r['valid'] and r['assessment']['status']=='JUDGED' for r in rs)]
    exact=sum(rs[0]['assessment']['grade']==rs[1]['assessment']['grade'] for rs in comparable)
    binary=sum((rs[0]['assessment']['grade']>=2)==(rs[1]['assessment']['grade']>=2) for rs in comparable)
    macro={v:{(r['condition'],r['metric']):r for r in data['macro']} for v,data in evaluations.items()}
    text=['# 핵심 업무 보존형 E 모델 검증', '', '2026-11-07', '',
          '## 1. 전체 작업 결과', '',
          '미판정 재검토, 보존 품질 재평가, 추가 사례 검토, 정답 버전별 재계산을 수행했다. 불일치와 판단 보류는 결과에 남겼다. 기존 봉인 순위만 재사용했으며 이번 점수 변화는 정답 판단의 변화에서 나온다. 새로운 검색·관점 생성·독립 Test 실행은 없었다.', '',
          f"검토 대상은 기존896쌍 중{index['selected_pairs']}쌍이다. 기존 미판정29쌍, E의 Top-5, C·E의 Top-5/10/20 진입·이탈, 질문별1점·2점 경계의 고정 ID 표본을 포함했다. 나머지716쌍은 기존 AI 판정을 출처와 함께 이어 사용했다. 선정 기준은 새 API 요청 전에 커밋했다.", '',
          f"추가 검토는 {review['independent_provider_count']}개 제공자에서 진행했다. GPT와 두 번째 검토자는 같은 원문만 받고 서로의 점수·이유, 기존 점수, 방식명과 추천 순위를 받지 않았다. 조정자는 과거 결과를 알고 있고 사례 선정도 순위 변화를 참고했다. 새 블라인드 입력이 연구 전체를 미개봉 독립 실험으로 만들지는 않는다.", '',
          '사용 모델은 `gpt-6-luna`와 접근 점검을 통과한 `claude-haiku-4-5-20251001`이다. 같은 검토자 모델을 반복한 결과와 다른 제공자의 결과를 구분해서 기록했다.', '',
          '## 2. 미판정29건 검증 결과', '',
          f"정확한 등급이 일치한 {stage1['resolved']}건을 새 버전에 기록했고 {stage1['remaining_abstain']}건은 ABSTAIN으로 남겼다. 유효한 등급이 서로 달라도 다수결로 확정하지 않았다. 기존867건은 미판정 전용 버전에서 그대로 유지했다.", '',
          '| 질문 | 기존 미판정 | 새 등급 확정 | 남은 보류 |', '|---|---:|---:|---:|']
    missing={(r['query_id'],r['case_id']) for r in versions['v0_original'] if r['status']!='JUDGED'}
    for q in ('CPD06','CPD07'):
        rows=[r for r in stage1['records'] if r['query_id']==q]
        text.append(f"| {q} | {len(rows)} | {sum(r['status']=='JUDGED' for r in rows)} | {sum(r['status']=='ABSTAIN' for r in rows)} |")
    text += ['', '원문 출처는 기존 사례의 Problem·Task·Context, 근거 ID와 원본 위치·URL로 기록했다. 원 출판물의 최신 페이지를 새로 전수 확인한 것은 아니며, 구조화된 사례 설명의 정보 부족이 남는다. [29건 기록](stage1_summary.json) · [출처 목록](source_registry.json)', '',
             '## 3. 업무 보존 평가 오류와 새 검토', '',
             '새 기준은 세 관점 전체에서 목적·행동·대상·입력·출력·제약을 확인한다. 역할 구분은 별도 항목이다. 사람이 전송·승인 권한을 가진다는 말은 AI의 자동 수행이나 사람의 두 작업 동시 수행을 뜻하지 않는다. 실제 행동과 필요, 조회와 수정, 탐지와 예측을 나눠 판단했다. 기준은 새 요청 전에 고정했고 E 생성 프롬프트는 바꾸지 않았다.', '',
             '| 검토자 | 항목 | C·E 공통 비교 수 | E−C 점수 차이/2 | 개선 / 악화 |',
             '|---|---|---:|---:|---:|']
    fields={'purpose':'목적','action':'행동','object':'대상','input':'입력','output':'결과',
            'constraints':'제외·권한','no_added_functions':'추가 기능 없음','roles':'역할 구분'}
    for row in quality['paired_C_E']:
        value='미정의' if row['E_minus_C'] is None else f"{row['E_minus_C']:+.3f}"
        text.append(f"| {row['reviewer']} | {fields[row['field']]} | {row['matched_triplet_pairs']} | {value} | {row['improved']} / {row['worse']} |")
    valid=Counter(r['reviewer'] for r in quality['records'] if r['valid'])
    text += ['', f"품질 요청의 형식·인용 근거 검사를 통과한 건수는 {dict(valid)}다. 일치하는 원문 인용은 의미가 맞음을 자동 보장하지 않는다. 이전 점수와 새 점수를 모두 저장했고 새로 추가된 입력·추가 기능 항목은 이전 출력 점수와 같은 척도로 직접 비교하지 않았다.", '',
             'C와 E는 두 검토자 모두24개 관점 묶음의8개 항목에2점을 부여했다. 이번 척도에서 E의 보존 우위는 관찰되지 않았다. 점수가 모두 상한에 모여 작은 의미 차이를 구분하는 능력도 확인되지 않았다. 기존 추출168필드 중13개, E 관점 인용72개 중3개의 정확한 원문 인용 불일치는 그대로 남아 있다. 의미 평가2점이 인용 오류를 없애지는 않는다. [인용 검사](literal_grounding_audit.json)', '',
             '과거 오류5건의 원문과 새 검토를 연결해 보존했다. 이전 AI의 감점 이유가 새 기준에 맞는지 확인할 수 있다. C·E의 생성 내용은 모두 기존과 같은 내용이므로 품질 점수 변화도 검토 방식의 변화다. [원점수·이유 비교](quality_revalidation.json)', '',
             '| 과거 오류 대상 | 회차 | 기존 제약 점수/2 | 새 검토자별 제약 점수/2 |',
             '|---|---:|---:|---|']
    for error in quality['previous_error_rechecks']:
        before=error['old_error']
        scores=[]
        for new in error['new_reviews']:
            value=next(c['score'] for c in new['data']['checks'] if c['field']=='constraints') if new['valid'] else None
            scores.append(f"{new['reviewer']} {value}")
        text.append(f"| {before['condition']} {before['query_id']} | {before['repeat']} | {before['raw_assessment']['constraints']} | "+', '.join(scores)+' |')
    text += ['',
             '## 4. 성능 비교', '',
             '| 판정 버전 | 방식 | F1@5 | F1@10 | F1@20 | nDCG@5 | nDCG@10 |',
             '|---|---|---:|---:|---:|---:|---:|']
    for version in evaluations:
        for condition in 'ABCE':
            cells=[]
            for metric in ('F1@5','F1@10','F1@20','nDCG@5','nDCG@10'):
                r=macro[version][condition,metric]
                spread=f" ±{r['repeat_sd']*100:.2f}%p" if r['repeat_sd'] is not None else ''
                cells.append(f"{pct(r['mean'])}{spread} (n={r['n']})")
            text.append(f"| {NAMES[version]} | {condition} | "+' | '.join(cells)+' |')
    text += ['', '각 지표의 n은 해당 버전의 A·B·C·E를 같은 질문 집합으로 비교한 질문 수다. 버전마다 질문 수가 다른 평균을 그대로 성능 개선량으로 비교하지 않는다.', '',
             '보류가1건이라도 남는 질문의 전체 Recall·F1·nDCG는 확정하지 않는다. Top-K 판정이 갖춰진 Precision은 질문별 파일에 남겼다. 단독 검토자 버전은 검토자에 따른 차이를 살펴보는 민감도 분석이다.', '',
             '| 기존6질문 집합 안에서 비교 | 실제 포함 질문 수 | A F1@5 | B | C | E |',
             '|---|---:|---:|---:|---:|---:|']
    for version,data in evaluations.items():
        cohort={(r['condition'],r['metric']):r for r in data['original_six_cohort_macro']}
        text.append(f"| {NAMES[version]} | {cohort['E','F1@5']['n']} | "+
                    ' | '.join(pct(cohort[c,'F1@5']['mean']) for c in 'ABCE')+' |')
    text += ['', '이 표는 새로 판정한 CPD06·CPD07을 더해 생긴 질문 구성 효과와, 기존 질문의 판정 변경 효과를 구분하기 위한 것이다. 보류로 질문 수가 줄면 실제 포함 수를 그대로 표시했다. 버전 쌍의 공통 질문만 비교한 자료도 별도로 저장했다. [공통 질문 비교](label_version_common_cohort_comparison.json)', '',
             '| 판정 버전 | 방식 | P@5 | R@5 | P@10 | R@10 | P@20 | R@20 |',
             '|---|---|---:|---:|---:|---:|---:|---:|']
    for version in evaluations:
        for condition in 'ABCE':
            cells=[f"{pct(macro[version][condition,m]['mean'])} (n={macro[version][condition,m]['n']})"
                   for m in ('Precision@5','Recall@5','Precision@10','Recall@10','Precision@20','Recall@20')]
            text.append(f"| {NAMES[version]} | {condition} | "+' | '.join(cells)+' |')
    text += ['', f"등급 비교 가능한 {len(comparable)}쌍 중 정확한 등급 일치는 {exact}쌍, 관련 여부(2점 이상) 일치는 {binary}쌍이었다. 0점 대1점처럼 이진 관련 여부가 같아도 정확한 등급이 다르면 엄격한 정답 버전은 보류로 남겼다.", '',
             '| 판정 버전 | 전체8질문 F1@5 E−C 하한 | 상한 |', '|---|---:|---:|']
    for version,data in evaluations.items():
        r=next(r for r in data['incomplete_f1_difference_bounds'] if r['baseline']=='C' and r['metric']=='F1@5')
        text.append(f"| {NAMES[version]} | {pp(r['lower'])} | {pp(r['upper'])} |")
    text += ['', '하한·상한은 미판정 사례를 관련 또는 무관으로 둘 수 있는 모든 경우를 고려한 수학적 범위다. 빈 값을 채운 점수나 신뢰구간은 아니다. 양성이0개일 가능성이 남으면 전체8질문의 범위도 확정하지 않는다. 질문별 범위와 질문 재표집 구간, 하나씩 제외한 결과는 버전별 evaluation.json에 있다.', '',
             '## 5. 개선 사례와 검토 결과', '']
    rank={(c,r['query_id'],r.get('repeat',0)):r['ranking'] for c,rows in predictions['systems'].items() for r in rows}
    discovery=read(run.old.OUT/'discovery.json')
    cases=read(run.ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    examples=[('CPD03',1,'AXV2H_0071_01'),('CPD06',2,'AXV2C_0006_02')]
    gain=next((x for x in discovery['changes'] if x['baseline']=='C' and x['query_id']=='CPD04' and x['k']==5 and x['gained']),None)
    if gain:examples.append(('CPD04',gain['repeat'],gain['gained'][0]))
    case_review=[]
    for q,rep,cid in examples:
        item={'query_id':q,'repeat':rep,'case_id':cid,'task':cases[cid]['task'],
              'C_rank':rank['C',q,rep].index(cid)+1,'E_rank':rank['E',q,rep].index(cid)+1,
              'old':original[q,cid],'new':label[q,cid],'reviews':grouped.get((q,cid),[])}
        case_review.append(item)
        opinions=', '.join(f"{r['reviewer']} {r['assessment']['grade'] if r['valid'] else '검사 미통과'}" for r in item['reviews'])
        text.append(f"- {q} {cases[cid]['task']} ({cid}). C {item['C_rank']}위→E {item['E_rank']}위. 기존 {item['old']['grade']}점, 새 엄격 판정 {item['new']['grade']} / {item['new']['status']}. 별도 판단은 {opinions}였다.")
    write(out/'case_review.json',{'records':case_review,'human_verified':False})
    text += ['', '## 6. 남은 실패와 불확실성', '',
             f"엄격한 새 판정 상태는 {evaluations['v2_reviewed_strict']['label_counts']}다. 두 모델의 정상적인 판단 차이와 응답 형식·인용 오류는 별도 저장했다. 원점수나 이유를 임의로 맞추지 않았다.", '',
             '기존 규칙이 CPD04의 요약 대상을 고객 의견 대신 ‘회의’로 잡은 기록이 남아 있다. 기능 ID 검출 수 증가가 올바른 행동·대상 연결을 입증하지 않는다. 사례 관련도 추가 검토는 기능 매핑 전체의 정확도를 전수 검증한 것이 아니다. [기존 기능 추적](../core-preserved-three-views-2026-11-07/inference/query_profiles.json)', '',
             '검색 반복 안정성은 동일한 봉인 순위이므로 기존 결과와 같다. Top-5 사례 겹침은 C91.67%, E86.81%였다. E의 반복 안정성 향상은 확인되지 않았다.', '',
             '| E 관점 | Top-5 알려진 관련 발견 | 그 관점만의 알려진 발견 | Top-5 미해결 판정 |',
             '|---|---:|---:|---:|']
    reviewed_discovery=read(out/'discovery_reviewed.json')
    for role,name in zip(run.old.SLOTS,('현업','운영','기술')):
        paths=[r for r in reviewed_discovery['path_discovery'] if r['condition']=='E' and r['view']==role and r['k']==5]
        text.append(f"| {name} | {sum(len(r['related_cases']) for r in paths)} | {sum(len(r['unique_cases']) for r in paths)} | {sum(r['unresolved_in_topk'] for r in paths)} |")
    text += ['', '발견 수는 질문·사례·회차별 합계다. 미해결 판정이 있어 알려진 관련 발견은 하한 성격이며 전체 관점 성능으로 해석할 수 없다. 원질문 관련도에 따른 발견 경로이며 관점 자체의 별도 정답이나 관점 제거 효과를 측정한 것은 아니다.', '',
             '| 높은 규칙 점수의 선정 사례 | 판정된 질문·사례·회차 | 그중 관련 판정 | 미해결 |',
             '|---|---:|---:|---:|']
    mapping=read(out/'mapping_support_audit.json')['records']
    for c in ('C','E'):
        rows=[r for r in mapping if r['condition']==c]
        judged=[r for r in rows if r['status']=='JUDGED']
        text.append(f"| {c} | {len(judged)} | {sum(r['grade']>=2 for r in judged)} | {len(rows)-len(judged)} |")
    text += ['', '이 표는 선정180쌍 중 규칙 점수3이상의 전체 문제 관련도 지지 여부다. 반복은 독립 표본이 아니며 기능 매핑 자체의 정확도나 전체 코퍼스 정확률로 발표하지 않는다.', '',
             '## 7. 연구적 판단', '',
             '| 판정 버전 | 비교 | F1@5 E의 차이 | 평가 질문 수 |', '|---|---|---:|---:|']
    differences=[]
    for version in evaluations:
        for baseline in 'ABC':
            a=macro[version]['E','F1@5'];b=macro[version][baseline,'F1@5']
            value=a['mean']-b['mean'] if a['mean'] is not None and b['mean'] is not None else None
            differences.append({'version':version,'baseline':baseline,'delta':value,'n':a['n']})
            text.append(f"| {NAMES[version]} | E−{baseline} | {pp(value)} | {a['n']} |")
    text += ['', '| 판정 버전 | 질문 | E−C F1@5 |', '|---|---|---:|']
    concentration=[]
    for version,data in evaluations.items():
        for q in qs:
            means=[]
            for c in ('C','E'):
                vals=[r['metrics']['F1@5'] for r in data['per_query'] if r['query_id']==q and r['condition']==c]
                means.append(mean(vals) if vals and None not in vals else None)
            delta=means[1]-means[0] if None not in means else None
            concentration.append({'version':version,'query_id':q,'delta':delta})
            text.append(f"| {NAMES[version]} | {q} | {pp(delta)} |")
    text += ['', 'E가 확실히 C·B·A보다 좋다는 판단은 새 판정의 분모, 검토자별 결과와 보류 범위를 함께 봐야 한다. 작은 개발 질문8개와 같은 코퍼스에서 나온 수치만으로 새로운 업무 전체의 우위를 주장하기 어렵다. 정답 버전 사이의 점수 변화는 모델 개선 실험의 효과와 구분한다.', '',
             '업무 보존 검토는 두 제공자의 별도 요청으로 확대했지만 여전히 AI 판단이다. 같은 입력·원문을 공유하고 문제 작성자가 코퍼스를 알고 있어 공통 오류 가능성이 남는다. 사람 Gold나 완전히 독립적인 외부 검증 수준의 근거는 확보되지 않았다.', '',
             '## 8. 다음 단계', '',
             '추천 결과가 바뀌기 전 미판정·불일치의 판정 정책과 실제 수행 기능의 근거를 먼저 확정해야 한다. 사람 또는 독립된 업무 담당자가 중요한 관련성 경계와 권한·제외 조건을 검토한 뒤 E를 최종 후보로 동결할지 결정하는 것이 적절하다. 신규 독립 Test는 이후 별도 결정 사항이다.', '',
             '## 9. GitHub와 비용', '',
             '- 브랜치 `research/core-preserved-e-validation-20261107`',
             f"- 유료 호출 {len(ledger['calls'])}회, 사용량 기준 추정 ${ledger['estimated_received_usd']}, 미확정 예약 ${ledger['unconfirmed_reserved_usd']}, 보수적 누적 ${ledger['conservative_spent_or_reserved_usd']}로 상한$2를 관리했다.",
             '- 기존 코드·가중치·프롬프트·사례·질문·정답·봉인 순위의 해시를 검증했다. 추가 충전은 하지 않았다.',
             '- [사전 기준](protocol.json) · [검토 선정](selection.json) · [검토 원문과 변경 이유](relevance_reviews.json) · [최종 상태](final_status.json) · [테스트](tests.json) · [실행 방법](REPRODUCE.md)',
             '- [OpenAI 단가](https://developers.openai.com/api/docs/models/gpt-6-luna) · [Claude 단가](https://platform.claude.com/docs/en/about-claude/pricing)', '']
    (out/'README.md').write_text('\n'.join(text),encoding='utf-8',newline='\n')
    write(out/'report_summary.json',{'differences':differences,'concentration':concentration,
                                    'grade_agreement':{'n':len(comparable),'agree':exact},
                                    'binary_agreement':{'n':len(comparable),'agree':binary},
                                    'case_examples':case_review,
                                    'new_Test_executed':False,'human_verified':False})


if __name__=='__main__':
    main()
