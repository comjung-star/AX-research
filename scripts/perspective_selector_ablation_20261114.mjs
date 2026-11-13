// Reproduce the frozen 2026-11-14 perspective selector / curated-pool ablation.
// Uses only JSON already checked into the repository; no APIs, network, training or dependencies.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(ROOT,'docs/perspective-selector-ablation-20261114');
const paths=["docs/perspective-omission-validation20-20261110/rankings.json","docs/perspective-omission-validation20-20261110/labels.json","docs/perspective-panels-full112-20261109/stage4/catalog-expanded.json","docs/perspective-omission-validation20-20261110/metrics.json"];
const texts=paths.map(p=>fs.readFileSync(path.join(ROOT,p),'utf8'));
const [R,L,C,M]=texts.map(JSON.parse);
const compute=function compute(R,L,C,M){
  const cards=C.cards.map(x=>x.id);
  const links=Object.fromEntries(C.cards.map(c=>[c.id,c.links.filter(l=>l.status==="SUPPORTED_FOR_PILOT").map(l=>l.case_id)]));
  const pool=[...new Set(cards.flatMap(c=>links[c]))];
  const qs=Object.keys(R).sort(), avg=a=>a.reduce((s,x)=>s+x,0)/a.length;
  const unique=a=>[...new Set(a)];
  function combinations(xs,n){if(n===0)return [[]];if(n===xs.length)return [xs];return [...combinations(xs.slice(1),n-1).map(x=>[xs[0],...x]),...combinations(xs.slice(1),n)];}
  function select(row,candidates){
    const sc=row.base_scores,U=row.unique_budget;
    const order=(a,b)=>sc[b]-sc[a]||(a<b?-1:a>b?1:0);
    const out=unique([...row.base_order.slice(0,5),...unique(candidates).sort(order)]);
    for(const c of row.base_order){if(out.length>=U)break;if(!out.includes(c))out.push(c);}
    return out.slice(0,U);
  }
  function byCards(row,chosen){
    const sc=row.base_scores,order=(a,b)=>sc[b]-sc[a]||(a<b?-1:a>b?1:0);
    return select(row,chosen.flatMap(card=>links[card].slice().sort(order).slice(0,5)));
  }
  function metrics(ids,rel){
    let hits=ids.filter(c=>rel.has(c)).length,N=ids.length,Y=rel.size;
    return {returned:N,hits,precision:N?hits/N:0,recall:Y?hits/Y:null,f1:Y?2*hits/(N+Y):null};
  }
  if(qs.length!==20||cards.join(",")!=="P01,P02,P03,P04"||pool.length!==49||cards.reduce((a,c)=>a+links[c].length,0)!==53)throw Error("Frozen input mismatch");
  let per={},checks={questions:0,judgments:0,all_controls_equal_U:true,all_base5_preserved:true,all112_labeled:true};
  for(const q of qs){
    const row=R[q],gold=L[q].cases,base5=row.base_order.slice(0,5),U=row.unique_budget;
    const known=Object.keys(gold);
    if(known.length!==112||Object.keys(row.base_scores).length!==112||row.base_order.length!==112)throw Error(q+" incomplete 112");
    const rel=new Set(Object.entries(gold).filter(([id,x])=>x.grade>=2).map(([id])=>id));
    if(!rel.size)throw Error(q+" no positive relevance: unsupported scoring");
    let main=row.panels.panels.filter(x=>x.search_role==="MAIN").map(x=>x.id);
    let candidateSets=combinations(cards,main.length).map(ids=>({cards:ids,prediction:byCards(row,ids)}));
    let predictions={A_BASE:row.sets.A_BASE,B_MAIN_ORIGINAL:row.sets.B_MAIN,POOL_ONLY_PTC:select(row,pool),SELECTED_CARD_PTC:byCards(row,main)};
    for(const [name,pred] of Object.entries(predictions)){
      if(pred.length!==U||unique(pred).length!==U)throw Error(q+" "+name+" unequal U");
      if(base5.some(id=>!pred.includes(id)))throw Error(q+" "+name+" base5 changed");
      if(pred.some(id=>!gold[id]))throw Error(q+" "+name+" case outside gold");
    }
    for(const item of candidateSets)if(item.prediction.length!==U||unique(item.prediction).length!==U||base5.some(id=>!item.prediction.includes(id)))throw Error(q+" random arm invalid");
    const m=Object.fromEntries(Object.entries(predictions).map(([name,pred])=>[name,metrics(pred,rel)]));
    let optionRows=candidateSets.map(x=>({cards:x.cards,prediction:x.prediction,metrics:metrics(x.prediction,rel)}));
    m.RANDOM_CARD_PTC=Object.fromEntries(["returned","hits","precision","recall","f1"].map(k=>[k,avg(optionRows.map(x=>x.metrics[k]))]));
    per[q]={U,main_cards:main,positive_total:rel.size,random_option_count:optionRows.length,metrics:m,predictions,random_options:optionRows};
    checks.questions++;checks.judgments+=known.length;
  }
  const armNames=["A_BASE","B_MAIN_ORIGINAL","POOL_ONLY_PTC","SELECTED_CARD_PTC","RANDOM_CARD_PTC"],summary={};
  for(const arm of armNames)summary[arm]=Object.fromEntries(["returned","hits","precision","recall","f1"].map(k=>[k,avg(qs.map(q=>per[q].metrics[arm][k]))]));
  if(Math.abs(summary.A_BASE.f1-M.summary.A_BASE.f1)>1e-12||Math.abs(summary.B_MAIN_ORIGINAL.f1-M.summary.B_MAIN.f1)>1e-12)throw Error("Original A/B results not reproduced");
  let state=20261114;function rng(){state^=state<<13;state^=state>>>17;state^=state<<5;return (state>>>0)/4294967296;}
  function ci(a){let boot=[];for(let b=0;b<20000;b++){let s=0;for(let i=0;i<a.length;i++)s+=a[Math.floor(rng()*a.length)];boot.push(s/a.length);}boot.sort((a,b)=>a-b);return [boot[Math.floor(0.025*(boot.length-1))],boot[Math.floor(0.975*(boot.length-1))]];}
  const comparisons=[["B_MAIN_ORIGINAL","A_BASE"],["POOL_ONLY_PTC","A_BASE"],["B_MAIN_ORIGINAL","POOL_ONLY_PTC"],["SELECTED_CARD_PTC","RANDOM_CARD_PTC"],["SELECTED_CARD_PTC","POOL_ONLY_PTC"]];
  let contrasts={};for(const [x,y] of comparisons){
    const a=qs.map(q=>per[q].metrics[x].f1-per[q].metrics[y].f1);
    contrasts[x+"_minus_"+y]={mean_difference:avg(a),paired_question_bootstrap95:ci(a),bootstrap_seed:20261114,bootstrap_replicates:20000,wins:a.filter(z=>z>1e-12).length,losses:a.filter(z=>z< -1e-12).length,ties:a.filter(z=>Math.abs(z)<=1e-12).length};
  }
  return {experiment:"frozen20-view-selector-vs-curated-pool",date:"2026-11-14",source_commit:"f76fb69e9684be0b7f537d22cb430b7e44dfd937",definitions:{A_BASE:"Original all-112 PTC topU",B_MAIN_ORIGINAL:"Original base5 + MAIN task branch + PTC fill",POOL_ONLY_PTC:"base5 + top PTC of union all 49 curated links + PTC fill",SELECTED_CARD_PTC:"base5 + selected MAIN cards per-view top5 by PTC + PTC fill",RANDOM_CARD_PTC:"mean of all choose(4,main_card_count) PTC view selections"},corpus:{records:112,questions:20,label_pairs:2240,cards:4,curated_unique_cases:pool.length,curated_links:53,mean_output_U:12.7},checks,summary,contrasts,per_question:per,limitations:["Existing 20 synthetic questions reused; no sealed independent test","Same model family selected roles and judged full-112 relevance","Pool-only and original B use different scoring/selection, so B-vs-pool is not pure causal view effect","Random-vs-selected controls curated links, PTC scoring, same number of cards and U; does not exactly reproduce original B task scoring","No new human grading of ablated control candidates; no new case-source audit"]};
};
const renderReport=function renderReport(x){
  const f=v=>(v*100).toFixed(2)+"%",pp=v=>(v*100>=0?"+":"")+(v*100).toFixed(2)+"%p", k=x.contrasts;
  const metrics=["A_BASE","POOL_ONLY_PTC","B_MAIN_ORIGINAL","SELECTED_CARD_PTC","RANDOM_CARD_PTC"];
  const desc={"A_BASE":"A: 기본검색","POOL_ONLY_PTC":"풀만 활용 (49건)","B_MAIN_ORIGINAL":"B: 기존 주요관점","SELECTED_CARD_PTC":"주요관점 선택, PTC 공통점수","RANDOM_CARD_PTC":"무작위 관점, PTC 공통점수"};
  let report=`# 관점 선택 효과 vs 사례풀 효과 — 고정 20문항 재분석 (2026-11-14)\n\n> **결과 미화·실험 후 기준 수정 없음.** [사전 동결 프로토콜](PROTOCOL.ko.md) 기준. 원본 A/B 결과와 전량 동일 재현. 연구용 검증 브랜치이며 미사용 최종 Test나 사람 평가 결과가 아니다.\n\n## 쉽게 요약\n\n1. **기존 B와 사례풀만 활용한 통제군이 거의 같다.** B−풀의 F1 차이는 ${pp(k.B_MAIN_ORIGINAL_minus_POOL_ONLY_PTC.mean_difference)}이고 95% 질문 부트스트랩 구간은 ${pp(k.B_MAIN_ORIGINAL_minus_POOL_ONLY_PTC.paired_question_bootstrap95[0])} ~ ${pp(k.B_MAIN_ORIGINAL_minus_POOL_ONLY_PTC.paired_question_bootstrap95[1])}. **기존 B의 전체 향상을 관점 선택만의 효과로 귀속하면 안 된다.**\n2. **관점 역할 선택을 고정 PTC 점수로 비교하면 무작위 관점보다 높다.** 선택−무작위 F1 ${pp(k.SELECTED_CARD_PTC_minus_RANDOM_CARD_PTC.mean_difference)}, 95% 구간 ${pp(k.SELECTED_CARD_PTC_minus_RANDOM_CARD_PTC.paired_question_bootstrap95[0])} ~ ${pp(k.SELECTED_CARD_PTC_minus_RANDOM_CARD_PTC.paired_question_bootstrap95[1])}. 다만 이는 원본 B의 Task 분기 점수가 아닌 **보조 통제실험**이고, 선택과 채점이 같은 계열 LLM이므로 일반화/인과 효과의 독립 입증은 아니다.\n3. **사례풀만 갖춰도 A보다 많이 개선**됐다: 풀−A F1 ${pp(k.POOL_ONLY_PTC_minus_A_BASE.mean_difference)}. 이는 사례의 사전 구조화/연결 자체가 중요한 설계 요인일 수 있음을 시사한다.\n\n## 조건별 성능 — 전 질문 평균\n\n| 조건 | Precision | Recall | F1 | 질문당 추천수 |\n|---|---:|---:|---:|---:|\n`;
  for(const name of metrics){let v=x.summary[name];report+=`| ${desc[name]} | ${f(v.precision)} | ${f(v.recall)} | ${f(v.f1)} | ${v.returned.toFixed(2)} |\n`;}
  report+=`\n질문별 U는 A/B/풀/선택/무작위에서 정확히 같고 평균 12.70개다. 선정된 기본 5건을 보존했다. 4개 관점, 승인된 연결 53건, **고유 AX 사례 49건**을 사용했으며 원본 112개 사례와 질문/평가 2,240쌍은 변경하지 않았다.\n\n## 사전 지정 F1 비교\n\n| 비교 (앞−뒤) | 평균 변화 | 질문 부트스트랩 95% | 개선/악화/동률 |\n|---|---:|---|---|\n`;
  for(const [id,label] of [["B_MAIN_ORIGINAL_minus_A_BASE","기존 B − A"],["POOL_ONLY_PTC_minus_A_BASE","사례풀 − A"],["B_MAIN_ORIGINAL_minus_POOL_ONLY_PTC","기존 B − 사례풀"],["SELECTED_CARD_PTC_minus_RANDOM_CARD_PTC","실제 관점 선택 − 무작위 관점"],["SELECTED_CARD_PTC_minus_POOL_ONLY_PTC","선택 관점(PTC) − 사례풀"]]){
    let y=k[id];report+=`| ${label} | ${pp(y.mean_difference)} | ${pp(y.paired_question_bootstrap95[0])} ~ ${pp(y.paired_question_bootstrap95[1])} | ${y.wins}/${y.losses}/${y.ties} |\n`;
  }
  report+=`\n부트스트랩: 질문 단위 20,000회 복원추출, 고정 seed=20261114, 양측 백분위 구간. 질문들이 합성되고 사례가 반복되므로 이 구간은 **동일 평가모형/같은 질문 구성의 탐색적 불확실성**이다. 통계적 인과효과나 실제 기업 사용자 집단의 성능을 의미하지 않는다.\n\n## 질문별 F1(%) — 누락 없이 20개\n\n| 질문 | U | MAIN | A | 풀만 | 기존 B | 선택 PTC | 무작위 PTC 평균 |\n|---|---:|---|---:|---:|---:|---:|---:|\n`;
  for(const [q,r] of Object.entries(x.per_question)){const v=r.metrics;report+=`| ${q} | ${r.U} | ${r.main_cards.join(",")||"없음"} | ${(v.A_BASE.f1*100).toFixed(1)} | ${(v.POOL_ONLY_PTC.f1*100).toFixed(1)} | ${(v.B_MAIN_ORIGINAL.f1*100).toFixed(1)} | ${(v.SELECTED_CARD_PTC.f1*100).toFixed(1)} | ${(v.RANDOM_CARD_PTC.f1*100).toFixed(1)} |\n`;}
  report+=`\n## 해석 시 중요한 제한\n\n- **POOL_ONLY_PTC는 사전에 검토한 49개를 고른다.** 이는 검색 시스템에 수작업 지식/사례 연결을 추가한 효과를 포함한다. 성능 개선을 순수한 자동 관점 선택에 귀속시키지 말아야 한다.\n- **선택관점−무작위관점**은 카드의 수와 미리 연결한 사례풀이 동일하고 PTC 점수를 공통 사용하므로 역할 선택의 **조건부 효과를 더 가깝게 통제**하지만, 원래 B에서는 별도 질문+카드 정의를 Task와 비교했으므로 원본 B의 순수 기여는 이 실험만으로 확정되지 않는다.\n- 모든 관점을 선택하지 않은 4개 질문(VQ017~020)은 비교에 그대로 포함했다. 추가 관점/미선정 사례 정보의 부재도 원래대로 유지했다.\n- 인간 152쌍 교차검증은 A/B에만 해당하며 새 풀 통제군에는 인간 정답이 없다. 새 통제군에 사람 평가의 신뢰도를 전가하지 않는다.\n- 개선 여부에 맞춰 모델·정답·질문·관점 라벨·랭킹·사례 목록을 수정하지 않았다. 유료 API 요청도 없다.\n\n## 재현 방법\n\n기준 브랜치에서: \`node scripts/perspective_selector_ablation_20261114.mjs\` (Node.js 18 이상; 추가 패키지 불필요). 이 명령은 동결된 원본 JSON을 읽어 \`results.json\`과 \`RESULTS.ko.md\`를 생성한다. 원본 파일을 수정하지 않는다.\n\n실험 입력: \`docs/perspective-omission-validation20-20261110/{rankings,labels,metrics}.json\`, \`docs/perspective-panels-full112-20261109/stage4/catalog-expanded.json\`. 상세 예측·무작위 카드 전체 조합·통계/검증 결과는 \`results.json\` 참고.\n\n## 논문 작성에 미치는 영향\n\n**기존 주장 수정 권고:** “업무 관점 선택으로 F1이 +5.14%p 향상됐다” 대신 “업무관점 결합 방법은 기본검색보다 +5.14%p 높았다. 그러나 동일 사전 연결 사례풀을 활용하는 대조군도 +5.02%p였으므로, 자동 관점 선택만의 차별적 기여는 추가 검증이 필요하다.” 로 제한한다.\n`;
  return report;
};
const result=compute(R,L,C,M);
result.source_blobs={"docs/perspective-omission-validation20-20261110/rankings.json":"7bedb58ccaab12256d93e1128c6649690dae4f51","docs/perspective-omission-validation20-20261110/labels.json":"8db6e9e87ce989deb03b5948908d24a1a780c65f","docs/perspective-panels-full112-20261109/stage4/catalog-expanded.json":"b4f2f7dcf7e4add167ced88c1f5d1d1ed585c676","docs/perspective-omission-validation20-20261110/metrics.json":"f7d703a348329d3224b10df0debfaad5df80056a"};
const report=renderReport(result);
fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(result,null,2)+'\n');
fs.writeFileSync(path.join(out,'RESULTS.ko.md'),report);
console.log(JSON.stringify({checks:result.checks,summary:result.summary,contrasts:result.contrasts},null,2));
