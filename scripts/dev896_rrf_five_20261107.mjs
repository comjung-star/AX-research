// Reproduce five offline weighted-RRF variants on the frozen 8-question Dev set.
// Run from repository root: node scripts/dev896_rrf_five_20261107.mjs [output.json]
// This does not read independent Test or call any paid API.
import {readFileSync,writeFileSync} from 'node:fs';
const data = p => JSON.parse(readFileSync(p,'utf8'));
const compute = function compute(pred,label,reviews){
 const weights={I1:{E:0.5,C:0.5},I2:{E:0.75,C:0.25},I3:{E:0.75,A:0.25},I4:{E:0.5,A:0.5},I5:{E:0.5,C:0.25,A:0.25}};
 const d={};for(const x of label.records)(d[x.query_id]??={})[x.case_id]=x.grade;
 if(pred.case_ids.length!==112||pred.query_ids.length!==8||label.records.length!==896)throw Error("Registry cardinality mismatch");
 for(const q of pred.query_ids){if(Object.keys(d[q]).length!==112||pred.case_ids.some(c=>!Number.isInteger(d[q][c])))throw Error("Incomplete or nonnumeric dev qrels");}
 const low=reviews.records.filter(x=>x.confidence==="LOW_TO_MODERATE").map(x=>[x.query_id,x.case_id]);
 if(low.length!==24)throw Error("Low-confidence set differs from expected version");
 const rankIndex={};for(const [s,rows]of Object.entries(pred.systems))for(const r of rows)rankIndex[[s,r.query_id,r.repeat||0].join("|")]=r.ranking;
 const rank=(s,q,t)=>{const a=rankIndex[[s,q,s==="A"?0:t].join("|")];if(!a||a.length!==112||new Set(a).size!==112)throw Error("Bad source rank");return a;};
 const ranks={};
 for(const m of Object.keys(weights))for(const q of pred.query_ids)for(const t of [1,2,3]){
   const w=weights[m],p=Object.fromEntries(Object.keys(w).map(s=>[s,new Map(rank(s,q,t).map((c,i)=>[c,i+1]))]));
   const baseE=new Map(rank("E",q,t).map((c,i)=>[c,i]));
   const scores=new Map(pred.case_ids.map(c=>[c,Object.entries(w).reduce((v,[s,a])=>v+a/(60+p[s].get(c)),0)]));
   ranks[[m,q,t].join("|")]=[...pred.case_ids].sort((a,b)=>scores.get(b)-scores.get(a)||baseE.get(a)-baseE.get(b));
 }
 const get=(s,q,t)=>s in weights?ranks[[s,q,t].join("|")]:rank(s,q,t);
 const models=["A","B","C","E",...Object.keys(weights)];
 const evaluate=(a,q,g)=>{
   const ds=g[q],positives=Object.values(ds).filter(x=>x>=2).length;
   const hits=a.slice(0,5).filter(c=>ds[c]>=2).length;
   const dcg=xs=>xs.reduce((sum,x,i)=>sum+(Math.pow(2,x)-1)/Math.log2(i+2),0);
   const ideal=dcg(Object.values(ds).sort((x,y)=>y-x).slice(0,10));
   if(!positives||!ideal)throw Error("Zero-positive question");
   return {f1_at5:2*hits/(5+positives),ndcg_at10:dcg(a.slice(0,10).map(c=>ds[c]))/ideal,positive_count:positives,hits_top5:hits};
 };
 const scenarios={},per_question={};
 for(const scenario of ["base","low_confidence_minus1","low_confidence_plus1"]){
   const g=Object.fromEntries(Object.entries(d).map(([q,rows])=>[q,{...rows}]));
   if(scenario!=="base")for(const [q,c]of low)g[q][c]=Math.min(3,Math.max(0,g[q][c]+(scenario.endsWith("minus1")?-1:1)));
   scenarios[scenario]={};
   for(const m of models){
     const questions={};
     for(const q of pred.query_ids){
       const run=(m==="A"?[0]:[1,2,3]).map(t=>evaluate(get(m,q,t),q,g));
       questions[q]={f1_at5:run.reduce((s,v)=>s+v.f1_at5,0)/run.length,ndcg_at10:run.reduce((s,v)=>s+v.ndcg_at10,0)/run.length,positive_count:run[0].positive_count,mean_hits_top5:run.reduce((s,v)=>s+v.hits_top5,0)/run.length};
     }
     scenarios[scenario][m]={
       f1_at5:pred.query_ids.reduce((s,q)=>s+questions[q].f1_at5,0)/8,
       ndcg_at10:pred.query_ids.reduce((s,q)=>s+questions[q].ndcg_at10,0)/8
     };
     if(scenario==="base")per_question[m]=questions;
   }
 }
 const stability={};for(const m of models.filter(m=>m!=="A")){
   let js=[];for(const q of pred.query_ids)for(const [a,b] of [[1,2],[1,3],[2,3]]){
     const x=new Set(get(m,q,a).slice(0,5)),y=new Set(get(m,q,b).slice(0,5));
     const intersection=[...x].filter(c=>y.has(c)).length;js.push(intersection/(10-intersection));
   }
   stability[m]=js.reduce((s,v)=>s+v,0)/js.length;
 }
 const diagnostic=pred.query_ids.map(q=>{
   const qlabels=d[q],pos=pred.case_ids.filter(c=>qlabels[c]>=2),e=get("E",q,1),a=get("A",q,0),c=get("C",q,1),i3=get("I3",q,1);
   return {query_id:q,positive_count:pos.length,e_top5_grades:e.slice(0,5).map(c=>qlabels[c]),E_F1:per_question.E[q].f1_at5,C_F1:per_question.C[q].f1_at5,I3_F1:per_question.I3[q].f1_at5,grade3_missed_by_E_top5:pos.filter(c=>qlabels[c]===3&&!e.slice(0,5).includes(c)).map(id=>({case_id:id,rank_E:e.indexOf(id)+1,rank_A:a.indexOf(id)+1,rank_C:c.indexOf(id)+1,rank_I3:i3.indexOf(id)+1}))};
 });
 const paired={};
 for(const m of Object.keys(weights)){
   const diff=pred.query_ids.map(q=>({
     query_id:q,f1_at5:per_question[m][q].f1_at5-per_question.E[q].f1_at5,
     ndcg_at10:per_question[m][q].ndcg_at10-per_question.E[q].ndcg_at10
   }));
   paired[m]={mean_delta_f1_at5:scenarios.base[m].f1_at5-scenarios.base.E.f1_at5,mean_delta_ndcg_at10:scenarios.base[m].ndcg_at10-scenarios.base.E.ndcg_at10,question_deltas:diff,leave_one_out_delta_f1_range:[Math.min(...diff.map((v,i)=>diff.filter((_,j)=>j!==i).reduce((s,x)=>s+x.f1_at5,0)/7)),Math.max(...diff.map((v,i)=>diff.filter((_,j)=>j!==i).reduce((s,x)=>s+x.f1_at5,0)/7))]};
 }
 // Deterministic question-level paired bootstrap, exploratory only.
 let seed=20261107;const rand=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
 const quantile=(values,p)=>{const a=[...values].sort((x,y)=>x-y);return a[Math.floor(p*(a.length-1))];};
 const bootstrap={};for(const m of Object.keys(weights)){
   const diffs=paired[m].question_deltas;const f=[],n=[];
   for(let b=0;b<10000;b++){let x=0,y=0;for(let i=0;i<8;i++){const d=diffs[Math.floor(rand()*8)];x+=d.f1_at5;y+=d.ndcg_at10;}f.push(x/8);n.push(y/8);}
   bootstrap[m]={f1_at5_paired_question_bootstrap95:[quantile(f,0.025),quantile(f,0.975)],ndcg_at10_paired_question_bootstrap95:[quantile(n,0.025),quantile(n,0.975)]};
 }
 return {scope:"Exploratory Dev-only offline ranking fusion; NOT independent Test, NOT end-to-end model training",question_count:8,case_count:112,qrel_count:896,original_judged_preserved:821,ai_provisional_additions:75,low_confidence_new:low.length,metric_threshold:2,rrf_k:60,recipes:weights,baseline_and_trials:scenarios.base,low_confidence_sensitivity:{all_24_minus_one_grade:scenarios.low_confidence_minus1,all_24_plus_one_grade:scenarios.low_confidence_plus1},per_question,stability_top5_jaccard:stability,root_cause_diagnostics:diagnostic,paired_deltas_vs_E:paired,paired_question_bootstrap_exploratory:bootstrap,prediction_inputs_unchanged:true,independent_test_accessed:false,api_calls:0,model_retrained:false,claim_of_statistically_validated_improvement:false};
};
const result = compute(
  data('docs/core-preserved-three-views-2026-11-07/predictions.json'),
  data('docs/ai-dev-provisional-75-2026-11-07/development_qrels_ai_provisional.json'),
  data('docs/ai-dev-provisional-75-2026-11-07/reviews.json')
);
const target = process.argv[2] || 'docs/dev896-rrf-five-20261107/metrics_recomputed.json';
writeFileSync(target,JSON.stringify(result,null,2)+'\n','utf8');
console.log(JSON.stringify({target,models:result.baseline_and_trials,stability:result.stability_top5_jaccard},null,2));
