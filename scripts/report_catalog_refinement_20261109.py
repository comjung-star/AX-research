"""Readable results of the completed refinement; never changes model decisions or labels."""
from collections import Counter
import json

from scripts.catalog_refinement_20261109 import OUT,load,inputs,questions,SYSTEMS
from scripts.task_alignment_20261109 import sha


def main():
    x=load('evaluation.json');raw=load('predictions.json');qs=questions();pred=raw['questions'];fits=load('fits.json')
    recovery=load('fit-recovery-summary.json');verification=load('verification.json')
    fresh=load('fresh-labels.json');registry=inputs()[3]
    pct=lambda v:'NA' if v is None else f'{100*v:.1f}'
    names={'original':'기존20 원본','working_transfer':'기존20 작업용','partial_review_464':'기존20 부분검토',
           'claude':'기존40 Claude','gemini':'기존40 Gemini'}
    methods={'B_Task':'업무 중심 검색','E_Previous':'이전 LLM 방식','J_RepairOnly':'해석 오류 수정',
             'F_StrictFit':'관점 안 정밀 선별','G_WidenedFit':'전체 후보도 함께 선별','H_GlobalFit':'전역 후보 점수순'}
    providers={'openai':'GPT-5.4 medium','gemini':'Gemini3 Flash high'}
    complete=[q for q in pred if not pred[q]['fit_technical_failure']]
    failure_ids=[q for q in pred if pred[q]['fit_technical_failure']]
    old03=[q for q in pred if q in load('selections.json') and load('selections.json')[q]['selected_ids']==['P03']]
    p03sets={q:pred[q]['systems']['F_StrictFit']['ranking'] for q in old03}
    fit_positive_status=Counter(r['status'] for v in fits.values() for r in v.values() if r['fit']>=2)
    lines=['# 사례 선별 보완 1~4단계 결과','',
      '질문 해석 오류 수정, 질문−사례 원문 대조 선별, 관점 밖 전역 후보와의 비교, 기존60개와 새12개 평가를 수행했다. **아래는 기술적 실패와 모델 변경을 포함한 개발용 평가다. 깔끔한 단일 모델 사전등록 시험이나 사람 Gold 검증으로 보고하지 않는다.**','',
      '**판단: 이번 강한 사례 필터는 채택하지 않는다.** 새 질문에서 이전 LLM 방식의 F1은 GPT70.1/Gemini64.0이었지만 새 필터는14.5/17.7로 낮아졌다. 핵심 업무 관련성과 모든 세부 조건의 적용 가능성을 하나의 통과 기준에 묶어 유용한 참고 사례까지 많이 보류했다. 기존 동결 기준본은 보존하며 새 필터를 기본값으로 교체하지 않았다.','',
      f"핵심 업무가 맞는다고 예측한81쌍 중 {fit_positive_status['CONDITION_UNKNOWN']}쌍은 CONDITION_UNKNOWN, {fit_positive_status['SUPPORTED']}쌍만 SUPPORTED였다. 이 수치는 모델 자신의 fit 예측 분포이지 실제 정답 수가 아니다. 다만 왜 출력이 급감했는지를 보여준다.",'',
      '예를 들어 IVQ010에서 상품 카탈로그 속성 추출 사례를 fit3으로 봤으면서, 협력사 파일과 누락 알림이 원문에 명시되지 않았다는 이유로 보류했다. 적용 전에 확인할 조건과 참고 사례의 관련성을 별도로 다룰 여지가 있는데, 내가 이 두 판단을 한 통과 기준에 묶은 설계가 지나치게 엄격했다. 원문에 없는 기능을 지원한다고 주장해서는 안 된다는 원칙은 유지한다.','',
      '## 이번에 바꾼 것','',
      '- ‘제안하고’의 단어 일부를 부정으로 읽는 오류를 수정하고 실제 ‘안 합니다’·‘하지 마세요’는 보존했다.',
      '- 이미 문자화된 ‘통화 녹취 텍스트’가 음성 입력 조건으로 잡히지 않게 보완했다. 모든 자연어 변형을 해결한 것은 아니다.',
      '- 각 사례의 실제 Problem/Task/Context를 질문과 대조해 핵심 업무가 맞는지0~3으로 예측한다. fit2이상·필수조건 지원 근거가 있을 때만 제시한다. 보조작업 겹침이나 조건 미확인은 빈자리를 채우는 데 쓰지 않는다.',
      '- 관점 안 후보만 선별하는 F와, 전체17개 검색 후보까지 함께 선별하는 G를 비교한다. G와 같은 전역 후보·조건을 점수순으로만 내는 H도 두어 관점 배정의 추가 이득을 구분한다.',
      '- fit 판단은 모델의 예측이며 평가 정답이 아니다. 평가자는 방법·추천 순위·예측 fit을 보지 않았다. 관점명이나 사례 연결표도 fit 모델과 평가자에게 보내지 않았다.',
      '- 기존4관점·17사례·후보상한20·출력상한5를 유지했다. 전체112 확장·새 모델 학습은 하지 않았다. 결과 점수를 보고 임계값·순위 정책을 바꾸지 않았다.','',
      '## 비교 방식','', '|기호|방식|','|---|---|']
    lines += [f'|{s[0]}|{methods[s]}|' for s in SYSTEMS]
    lines += ['', 'H는 G의 전역 후보와 조건 판정을 공유하고 관점별 대표 배정만 제거한다. 관점 정보와 완전히 독립적인 모델이라고 부르지 않는다. 선별 조건 F/G/H는 같은 질문에서 같은 사례별 fit 응답을 공유한다. B/E/J는 이 추가 fit 호출을 사용하지 않는다. 검색·출력 예산은 같지만 계산 비용까지 같은 모델 비교는 아니다.','',
      '## 기존60개 개발 재비교','',
      'F1@5×100, 높을수록 좋다. 양성 질문에서 실제 제시 수와 전체 양성 수를 함께 계산하며 빈 답은0이다. 양성 없는 질문은 F1평균 NA이고 출력 회계에는 포함한다. 현재17개 안의 기존 AI Silver 기준이며 정답표를 바꾸거나 합치지 않았다.','',
      '|채점표|양성 질문|B 업무 검색|E 이전|J 오류수정|F 관점안 선별|G 전체도 선별|H 전역순위|',
      '|---|---:|---:|---:|---:|---:|---:|---:|']
    for n,r in x['development60'].items():
      lines.append('|'+names[n]+'|'+str(r['positive_questions'])+'|'+'|'.join(pct(r['summary'][s]['F1@5']['mean']) for s in SYSTEMS)+'|')
    lines += ['', '기존20개와40개는 이미 보았던 개발 자료다. 부분검토 표는464쌍의 검토를 작업용 표에 적용한 것이며 전체 사람 Gold가 아니다. 기술적으로 유효한 fit이 없는 질문도 주 비교에서 지우지 않고 빈 출력으로 남겼다.','',
      '## 새 질문12개','',
      '새 질문은 초기 알고리즘·기준 고정 후 사례 목록이나 과거 질문·실패 결과를 제공하지 않고 Claude가 작성했다. GeminiPro의 작성 요청이429로 실패해, 새 질문 생성 전 서비스 변경을 기록했다. 질문을 다시 쓰거나 성공할 것 같은 것만 남기지 않았다. 이전60개 및 관점선택 개발 문장과의 완전 문자 중복은 없었지만 의미적 독립성을 인증한 것은 아니다.', '',
      'API 오류·출력 잘림 때문에 새 질문 작성 뒤 fit 제공 모델과 추론 설정도 기술적으로 변경됐다. 따라서 ‘질문을 보지 않고 모든 실행 설정까지 고정한 최종 시험’은 아니다. 이번 버전의 개발 기준을 이 질문의 채점 결과에 맞춰 재조정하지는 않았다.','',
      '12개는 실제 현업 제출 질문이 아닌 AI 작성 시범 질문이다. 두 문항은 문의에 답하는 일이 아니라 인력·처리용량 분석을 물어 P04의 실제 문의 응대와 다르다. 원래 의도한 모든 관점의 검색 성능을 균형 있게 평가했다고 주장하지 않는다.','',
      '|독립 요청 채점 모델|채점 완료 질문|양성 질문|B 업무 검색|E 이전|J 오류수정|F 관점안 선별|G 전체도 선별|H 전역순위|',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for n,r in x['fresh12'].items():
      lines.append('|'+providers[n]+'|'+str(len(r['per_query']))+'|'+str(r['positive_questions'])+'|'+'|'.join(pct(r['summary'][s]['F1@5']['mean']) for s in SYSTEMS)+'|')
    lines += ['', 'GPT-5.4는 새 질문 fit 제공자와 공급자가 같아 자기평가 편향 가능성이 있다. GeminiFlash는 다른 공급자지만 원래 계획한 GeminiPro보다 낮은 등급이다. 서로 같아질 때까지 재채점하지 않았고 두 표를 하나의 확정 정답으로 합치지 않았다.','',
      '새12개의 fit 응답은 모두 유효했다. 따라서 새 질문에서의 하락을 기존5개 fit 기술 실패만으로 설명할 수 없다. 두 평가자가 모두 양성이 있다고 본 동일7개 질문에서도 E→G는 GPT65.9→16.6, Gemini64.0→17.7로 낮아졌다.','',
      '추가 관찰로, 이전 LLM 방식 E는 새 시범 질문에서 업무 중심 검색 B보다 높았다(GPT70.1 대46.8, Gemini64.0 대49.9). 이 비교를 이번 새 필터의 성공으로 보고하지 않는다. 현재 관점 범위를 고려한 작은 AI 질문 집합의 관찰이며, 보편적 개선이나 관점의 독립 기여 증명은 아니다.','',
      f"두 채점자가 모두 완료한 질문은 {len(x['fresh_complete_questions_both'])}개, 두 모델 모두 양성이 있다고 본 질문은 {len(x['fresh_common_positive_queries'])}개다. 이진 양성 불일치 쌍은 {len(x['fresh_binary_disagreements'])}개다. 양성 교집합·합집합 민감도와 동일 양성 질문 비교는 evaluation.json에 보존했다. 전체 음성 일치율을 정답 신뢰도라고 부르지 않는다.",'',
      '## 맞힌 수와 빈 답을 함께 확인','',
      '|자료/채점표|방식|출력 수|정답 적중 수|양성인데 빈 답인 질문|양성 없는 질문에 출력한 수|',
      '|---|---|---:|---:|---:|---:|']
    for source,group in [('기존',x['development60']),('새12',x['fresh12'])]:
      for n,r in group.items():
        if source=='기존' and n not in ('working_transfer','claude','gemini'):continue
        for s in ('B_Task','E_Previous','F_StrictFit','G_WidenedFit'):
          a=r['summary'][s]['output']
          lines.append('|'+source+' '+n+'|'+s[0]+'|'+str(a['emitted'])+'|'+str(a['hits'])+'|'+str(a['positive_but_empty'])+'|'+str(a['zero_positive_but_emitted'])+'|')
    lines += ['', '무조건 적게 내면 적중률이 좋아 보일 수 있으므로 빈 답과 놓친 사례를 함께 본다. 단일 지표나 유리한 채점자만 골라 성공으로 판단하지 않는다. 95%질문 bootstrap은 작은 시범 자료의 기술통계이며 탐색·다중검정 보정 없는 값이다.','',
      '## 관점 배정의 추가 이득','',
      f"72개 중 G와 H의 최종 사례 집합이 같은 질문은 {x['G_equals_H_sets']}개, 순서까지 같은 질문은 {x['G_equals_H_rankings']}개다. G=H인 결과를 관점 자체의 성능 이득으로 주장할 수 없다. 좋아졌다면 사례별 fit 선별의 효과와 전역 후보 회수의 효과를 나눠 보아야 한다.",'',
      '이번에는 F·G·H의 순위가72개 모두 같았다. 강한 필터를 통과한 사례가 이미 관점 안에 있어 전역 후보를 더 보아도 회수 효과가 없었다. 전역 검색이나 관점의 잠재 가치를 일반적으로 기각하는 결과는 아니며 이번 구성의 추가 이득이 없었다는 뜻이다.','',
      f"P03만 선택한 질문 {len(old03)}개의 F 출력은 서로 다른 사례 집합 {len({tuple(sorted(v)) for v in p03sets.values()})}종류다. 기존처럼 모두 같은5개를 채우는 동작은 피하도록 바꿨지만, 이것만으로 정답을 잘 골랐다는 뜻은 아니다. 실제 양성 적중과 누락은 위 표와 질문별 결과로 판단한다.",'',
      '## 기술 실패와 실행 변경','',
      f"원래 Claude fit 응답43개는 그대로 보존했다. 제공자별 유효 fit 수는 {dict(Counter(recovery['provider_by_query'].values()))}다. 유효 fit이 없는 문항은 {failure_ids}이며 주 비교에서 삭제하지 않았다. 새12개에 유효 fit이 없는 질문은 {[q for q in failure_ids if q.startswith('NQ')]}다.",'',
      '- GeminiPro 작성 요청429, Claude fit29개 HTTP400, GPT-5.4 high의 일부 길이 제한 응답과 중단 당시 전달 미확정 요청을 기록했다.',
      '- 정상 응답을 좋은 결과로 바꿔치기하지 않았다. Claude가 실패한 요청 중 GPT에서 이미 시도한 문항은 다시 보내지 않고, 아직 보내지 않은 문항만 medium 설정으로 마무리했다.',
      '- 실제 순위 정책·fit 기준·fit2 임계값은 고정했지만 제공 모델/추론 설정이 바뀌었다. 단일 모델의 깨끗한 인과 비교나 공식 최종 시험으로 볼 수 없다.',
      '- 이미 문자화된 녹취의 모든 한국어 표현을 고친 것은 아니다. 긴 문장과 복수 작업 조건 연결도 여전히 제한적이다.', '',
      '## 비용과 재현','',
      f"응답 usage가 돌아온 요청의 비용 추정 합계는 ${verification['estimated_usd']:.6f}다. 전체 시도 예약 상한 합계는 ${verification['reserved_usd']:.6f}이며 작업 한도$15 안이다. 응답을 받지 못한 일부 전송은 청구 여부가 불명확하므로 알려진 usage 합계가 최종 청구액이라고 단정하지 않는다.",'',
      '관련 기능 검사57개를 통과했다. 저장한 fit·선택·벡터·기존/신규 순위·평가 지표를 재현했다. 재현 성공은 데이터 의미나 AI 채점의 정답 인증이 아니다. 봉인 Test15와 전체112 확장에는 접근하지 않았다. 자료는 로컬 작업사본에 저장했고 GitHub에 커밋/업로드하지 않았다.','',
      '## 확인 자료','',
      '- [처음 고정한 계획](../catalog-refinement-20261109-protocol.md)',
      '- [새 질문 원문](fresh-questions.json) / [문자 중복 진단](fresh-novelty.json)',
      '- [전체 지표·질문별 점수·구간·민감도](evaluation.json)',
      '- [질문별 실제 후보와 선별 근거](questions-and-cases.ko.md)',
      '- [새 질문의 두 채점표](fresh-labels.json) / [모델의 사례 fit 예측](fits.json)',
      '- [순위·조건·출처](predictions.json) / [API 입력 접근 기록](inference-audit.json)',
      '- [초기 동결](freeze.json) / [소스 보관본](source-snapshot.zip)',
      '- [서비스 변경1](service-amendment.json) / [변경2](execution-amendment.json) / [실행 설정 변경](completion-amendment.json)',
      '- [유효 fit 출처와 실패](fit-recovery-summary.json) / [재현 확인](verification.json)',
      '- [채점 출력 형식 수정](judge-schema-amendment.json) / [알려진 비용과 전송 미확정](cost-summary.json)',
      '- 공식 요금: [GPT-5.4](https://developers.openai.com/api/docs/models/gpt-5.4), [Claude](https://platform.claude.com/docs/en/models/sonnet-5-5/overview), [Gemini](https://ai.google.dev/gemini-api/docs/pricing?authuser=6)', '',
      '## 이번 종료 판단','',
      '명백한 문장 해석 오류의 기능 수정은 보존한다. 강한 필터는 실험본으로 남기고 현재 기준본을 대체하지 않는다. 다음 보완이 필요하다면 핵심 업무에 도움이 되는 참고 사례와 직접 적용 조건의 충족을 구분해야 한다. 조건 미확인을 관련성0점처럼 취급해서도, 실제로 없는 핵심 기능이나 필수 채널을 지원한다고 만들어서도 안 된다. 이 후속 가설을 이번 점수에 맞춰 다시 구현·실험하지 않았다.','',
      '요청한1~4단계의 구현·비교 실행·분석은 여기서 종료했다. 새 필터의 성능 검증이 성공했다는 뜻은 아니다. 전체112 확장이나 추가 API 호출은 하지 않는다.','',
      '재현 실행: `python -m scripts.catalog_refinement_finalize_20261109 verify`.','']
    (OUT/'README.ko.md').write_text('\n'.join(lines),encoding='utf-8')
    examples=['# 질문별 후보와 사례별 fit 근거','','fit은 선별 모델의 예측이며 평가 정답이 아니다. 기술 실패도 표시한다.','']
    for q,r in qs.items():
      examples+=['## '+q,'','> '+r['text'],'', '- 구분: '+r['scope'],
        '- fit 기술 실패: '+str(pred[q]['fit_technical_failure']),'', '|방식|사례ID|','|---|---|']
      for s in SYSTEMS:examples.append('|'+s[0]+' '+methods[s]+'|'+(', '.join(pred[q]['systems'][s]['ranking']) or '제시 없음')+'|')
      examples+=['','**전체 후보 선별 G의 근거:**','']
      for c in pred[q]['systems']['G_WidenedFit']['ranking']:
        f=fits[q][c]
        examples+=['- '+c+': '+registry[c]['task'],'  - fit '+str(f['fit'])+' / '+f['status']+': '+f['reason'],
          '  - 질문: “'+f['query_quote']+'”']
        examples+=['  - '+e['field']+': “'+e['quote']+'”' for e in f['evidence']]
      examples+=['']
    (OUT/'questions-and-cases.ko.md').write_text('\n'.join(examples),encoding='utf-8')
    (OUT/'same-P03-diagnostic.json').write_text(json.dumps(p03sets,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    receipts=[json.loads(p.read_text(encoding='utf-8')) for p in (OUT/'calls').glob('*-receipt.json')]
    attempts=list((OUT/'calls').glob('*-attempt.json'))
    unresolved=[]
    for a in attempts:
      prefix=a.name[:-len('-attempt.json')]
      if not (OUT/'calls'/(prefix+'-receipt.json')).exists() and not (OUT/'calls'/(prefix+'-failure.json')).exists():
        unresolved.append({'name':prefix,**json.loads(a.read_text(encoding='utf-8'))})
    costs={'known_usage_estimate_usd':sum(r['estimated_usd'] for r in receipts),'unresolved_deliveries':unresolved,
      'unresolved_reserved_usd':sum(r['reserved_usd'] for r in unresolved),'attempt_count':len(attempts),'receipt_count':len(receipts)}
    (OUT/'cost-summary.json').write_text(json.dumps(costs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest={'report_is_post_run_interpretation':True,'report_script_sha256':sha(__file__),
      'evaluation_sha256':sha(OUT/'evaluation.json'),'artifact_sha256':{p:sha(OUT/p) for p in ['README.ko.md','questions-and-cases.ko.md','same-P03-diagnostic.json','cost-summary.json']},
      'extra_paid_calls':0,'ranking_policy_or_labels_changed':False}
    (OUT/'report-provenance.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('FOUR_STEPS_REPORTED_WITH_LIMITATIONS')


if __name__=='__main__':main()
