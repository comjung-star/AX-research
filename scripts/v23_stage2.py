#!/usr/bin/env python3
"""v2.3 Stage 2 ablations: equal multi-view, LOQO query-conditioned gate,
dense+sparse hybrid candidate union, LOQO interaction MLP.
Labels are AI-Silver Dev only and excluded from each held-out query's training.
"""
import csv,json,platform,random
from pathlib import Path
from collections import defaultdict
import numpy as np
import torch
from torch import nn
from sentence_transformers import SentenceTransformer
from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi

SEED=42;random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED)
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"data/v2_3";OUT=ROOT/"experiments/v23_stages/stage2";OUT.mkdir(parents=True,exist_ok=True)
PREV=ROOT/"experiments/v23_stages/stage1"
data=json.loads((PREV/"rankings.json").read_text(encoding="utf-8"))
cs=json.loads((BASE/"main_cases_v2_3.json").read_text(encoding="utf-8"))["cases"]
qs=json.loads((BASE/"dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))["queries"]
with (BASE/"ground_truth/silver_dev_qrels_2520.csv").open(encoding="utf-8",newline="") as f:allr=list(csv.DictReader(f))
IDS=[c["case_id"] for c in cs];CID={c["case_id"]:c for c in cs}
POS=defaultdict(set)
for x in allr:
 if int(x["relevance_0_4"])>=3:POS[(x["query_id"],x["perspective_id"])].add(x["case_id"])
QP={q["query_id"]:[p["id"] for p in q["draft_perspectives"]] for q in qs}
UNION={q:set().union(*(POS[(q,p)] for p in ps)) for q,ps in QP.items()}
STRAT={q:set().union(*(set(CID[c]["strategy_labels"]) for c in positive)) if positive else set() for q,positive in UNION.items()}
vecs=np.load(PREV/"case_embeddings.npz")
D=vecs["document"];V=[vecs[x] for x in ("problem","task","context")]
assert len(cs)==84 and set(data)==set(QP) and len(allr)==2520
ENC=SentenceTransformer("BAAI/bge-m3",device="cpu")
def emb(s):return np.asarray(ENC.encode(s,batch_size=8,normalize_embeddings=True,show_progress_bar=False),dtype=np.float32)
REF={}
RUNTIME={}
ANCHORS=emb(["업무의 문제, 병목, 오류, 지연, 비용, 위험","수행 업무, 처리해야 할 과업, 업무 기능, 작업","기업의 비즈니스 환경, 운영 맥락, 조직 조건, 시스템 제약"])
for q in qs:
 qid=q["query_id"]
 REF[qid]=emb([p["title"] for p in q["draft_perspectives"]])
 RUNTIME[qid]=emb([p["title"]+"; "+p["description"] for p in data[qid]["perspectives"]])
np.savez_compressed(OUT/"runtime_embeddings.npz",**{"R_"+q:RUNTIME[q] for q in RUNTIME},**{"G_"+q:REF[q] for q in REF})
def order(score):
 return [IDS[i] for i in sorted(range(len(IDS)),key=lambda i:(-float(score[i]),IDS[i]))]
def bb(branches,k=84):
 out=[];seen=set()
 for z in range(84):
  for b in branches:
   if z<len(b) and b[z] not in seen:
    out.append(b[z]);seen.add(b[z])
    if len(out)>=k:return out
 return out
def score(q,top,k):
 ss=set(top[:k]);ps=[POS[(q,p)] for p in QP[q] if POS[(q,p)]]
 s_found=set().union(*(set(CID[c]["strategy_labels"]) for c in ss)) if ss else set()
 return dict(recall=len(ss&UNION[q])/len(UNION[q]) if UNION[q] else None,
  perspective_coverage=sum(bool(ss&p) for p in ps)/len(ps) if ps else None,
  proxy_strategy_coverage=len(s_found&STRAT[q])/len(STRAT[q]) if STRAT[q] else None)

# Stage 2-1 equal weights. Guard that v2.3 runtime and main score are kept separate.
equal_branch={}
for q,runtime in RUNTIME.items():
 equal_branch[q]=[order(sum((np.dot(V[i],pv) for i in range(3)))/3) for pv in runtime]

# Stage 2-2 query-conditioned trainable gate with query-level leave-one-out.
# Input training examples: 9 other Dev questions × all reference perspectives × all cases.
# At inference: only runtime-generated perspectives, never held-out gold perspectives.
byq=defaultdict(list)
for r in allr:byq[r["query_id"]].append(r)
gate_branch={};gate_params={};fold_counts={}
for heldout in QP:
 feats=[];anchor=[];y=[]
 for q,ps in QP.items():
  if q==heldout:continue
  for j,p in enumerate(ps):
   pv=REF[q][j]
   a=pv@ANCHORS.T
   fs=np.stack([V[i]@pv for i in range(3)],axis=1)
   for i,cid in enumerate(IDS):
    feats.append(fs[i]);anchor.append(a)
    value=next(int(x["relevance_0_4"])>=3 for x in byq[q] if x["perspective_id"]==p and x["case_id"]==cid)
    y.append(int(value))
 x=torch.tensor(np.asarray(feats),dtype=torch.float32)
 a=torch.tensor(np.asarray(anchor),dtype=torch.float32)
 t=torch.tensor(y,dtype=torch.float32)
 theta=torch.nn.Parameter(torch.zeros(3))
 scale=torch.nn.Parameter(torch.tensor(1.0))
 bias=torch.nn.Parameter(torch.tensor(-3.0))
 opt=torch.optim.AdamW([theta,scale,bias],lr=.05,weight_decay=.01)
 for epoch in range(120):
  opt.zero_grad()
  ww=torch.softmax(theta+scale*a,dim=1)
  score_=torch.sum(x*ww,dim=1)
  logits=10*score_+bias
  loss=torch.nn.functional.binary_cross_entropy_with_logits(logits,t)
  loss.backward();opt.step()
 with torch.no_grad():
  wbase=theta.numpy().copy();sl=float(scale.item())
 weights=[];branches=[]
 for pv in RUNTIME[heldout]:
  a=pv@ANCHORS.T
  raw=wbase+sl*a
  w=np.exp(raw-np.max(raw));w=w/w.sum()
  weights.append(w.tolist())
  scores=sum(w[i]*(V[i]@pv) for i in range(3))
  branches.append(order(scores))
 gate_branch[heldout]=branches
 gate_params[heldout]={"global_logits":wbase.tolist(),"anchor_scale":sl,"runtime_weights":weights}
 fold_counts[heldout]={"train_questions":9,"train_examples":len(y),"positive_train":sum(y),"heldout_question":heldout}
 print("STAGE2 gate LOQO",heldout,len(y),"positive",sum(y),flush=True)

# Stage 2-3 same retrieval slot budget: k Dense + k sparse (2k total),
# compare with Dense-only 2k; use existing v2.3 Stage1 BM25 and case-doc scores.
docs=["Problem: "+c["problem"]+"\nTask: "+c["task"]+"\nContext: "+c["context"] for c in cs]
kiwi=Kiwi()
def tokenize(s):return [t.form.lower() for t in kiwi.tokenize(s) if t.tag not in ("SF","SP","SS","SE","SO","SW")]
bm=BM25Okapi([tokenize(x) for x in docs])
hybrid_branch={};rrf_branch={};sparse_branch={}
for q in QP:
 ts=[p["title"]+"; "+p["description"] for p in data[q]["perspectives"]]
 sparse=[order(bm.get_scores(tokenize(t))) for t in ts]
 sparse_branch[q]=sparse
 h=[];rr=[]
 for dense,sp in zip(equal_branch[q],sparse):
  pool=list(dict.fromkeys(dense[:40]+sp[:40]))
  h.append(pool)
  ranks={cid:i+1 for i,cid in enumerate(dense)}
  sr={cid:i+1 for i,cid in enumerate(sp)}
  # RRF rerank same candidate union, not preselected on gold.
  rr.append(sorted(pool,key=lambda c:(-1/(60+ranks.get(c,10000))-1/(60+sr.get(c,10000)),c)))
 hybrid_branch[q]=h;rrf_branch[q]=rr

# Stage 2-4: train 9-Q leave-one-query-out interaction MLP.
# Projection learned unsupervised ONLY from frozen case vectors; relevance never leaks into it.
from sklearn.decomposition import PCA
pca=PCA(n_components=64,svd_solver="full",random_state=SEED)
pca.fit(D)
C=torch.tensor(pca.transform(sum(V)/3),dtype=torch.float32)
def feature(qvec):
 q=torch.tensor(pca.transform(qvec.reshape(1,-1))[0],dtype=torch.float32)
 return torch.cat([q.expand(len(C),-1),C,q*C,torch.abs(q-C)],dim=1)
interaction_branch={};fit_notes={}
for heldout in QP:
 features=[];targets=[]
 for q,ps in QP.items():
  if q==heldout:continue
  for j,pid in enumerate(ps):
   xx=feature(REF[q][j])
   labels={r["case_id"]:int(r["relevance_0_4"])>=3 for r in byq[q] if r["perspective_id"]==pid}
   for i,cid in enumerate(IDS):
    features.append(xx[i].numpy());targets.append(float(labels[cid]))
 X=torch.tensor(np.asarray(features),dtype=torch.float32)
 Y=torch.tensor(targets,dtype=torch.float32)
 torch.manual_seed(SEED)
 mdl=nn.Sequential(nn.Linear(256,32),nn.ReLU(),nn.Dropout(.1),nn.Linear(32,1))
 opt=torch.optim.AdamW(mdl.parameters(),lr=.001,weight_decay=.001)
 weight=torch.tensor(min(10.0,(len(Y)-Y.sum().item())/max(Y.sum().item(),1.0)),dtype=torch.float32)
 for epoch in range(150):
  mdl.train();opt.zero_grad()
  logits=mdl(X).squeeze(-1)
  loss=torch.nn.functional.binary_cross_entropy_with_logits(logits,Y,pos_weight=weight)
  loss.backward();opt.step()
 mdl.eval();branches=[]
 with torch.no_grad():
  for pv,pool in zip(RUNTIME[heldout],rrf_branch[heldout]):
   pred=mdl(feature(pv)).squeeze(-1).numpy()
   branches.append(sorted(pool,key=lambda c:(-float(pred[IDS.index(c)]),c)))
 interaction_branch[heldout]=branches
 fit_notes[heldout]={"train_queries":9,"train_rows":len(targets),"train_positive":int(sum(targets))}
 print("STAGE2 interaction LOQO",heldout,len(targets),flush=True)

# Full ranking and same-budget candidate recovery diagnostics.
FINAL={}
detail=[]
hybrid_diag=[]
for q in QP:
 ranking={
  "stage1_mp_dense":data[q]["rankings"]["mp_dense"],
  "stage2_1_equal_multiview":bb(equal_branch[q]),
  "stage2_2_loqo_gated":bb(gate_branch[q]),
  "stage2_3_hybrid_rrf":bb(rrf_branch[q]),
  "stage2_4_loqo_interaction_mlp":bb(interaction_branch[q])}
 FINAL[q]=ranking
 for method,ranked in ranking.items():
  for k in (5,10,20):
   detail.append({"query_id":q,"method":method,"k":k,**score(q,ranked,k)})
 for k in (5,10,20):
  # Candidate union over per-branch k dense and k BM25 (2k slots);
  # Dense comparator k*2 alone for fairness.
  in_h=set().union(*(set(dense[:k]) | set(sparse[:k]) for dense,sparse in zip(equal_branch[q],sparse_branch[q])))
  in_d=set().union(*(set(br[:2*k]) for br in equal_branch[q]))
  in_rr=set().union(*(set(br[:k]) for br in rrf_branch[q]))
  h_pos=len(in_h&UNION[q]);d_pos=len(in_d&UNION[q])
  hybrid_diag.append({"query_id":q,"k":k,"dense_2k_gold":d_pos,
    "hybrid_union_2k_gold":h_pos,"hybrid_2k_unique_gold":len((in_h-in_d)&UNION[q]),
    "hybrid_2k_lost_gold":len((in_d-in_h)&UNION[q]),
    "dense_2k_candidate_count":len(in_d),"hybrid_2k_candidate_count":len(in_h)})
def save_csv(name,rows):
 with (OUT/name).open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
save_csv("per_query_metrics.csv",detail)
save_csv("hybrid_candidate_diagnostics.csv",hybrid_diag)
summary=[]
for m in FINAL[next(iter(FINAL))]:
 for k in (5,10,20):
  rs=[r for r in detail if r["method"]==m and r["k"]==k]
  summary.append({"method":m,"k":k,
   **{"mean_"+v:round(float(np.mean([x[v] for x in rs if x[v] is not None])),6) for v in ("recall","perspective_coverage","proxy_strategy_coverage")}})
save_csv("summary.csv",summary)
(OUT/"final_rankings.json").write_text(json.dumps(FINAL,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT/"gate_weights.json").write_text(json.dumps(gate_params,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
manifest={"stage":"2","dataset":"v2.3.0 frozen","evaluation_source":"AI-only Silver Dev proxy, NOT human Gold",
 "stage2_1":"problem/task/context equal weights, same perspectives as Stage1",
 "stage2_2":"query-conditioned anchor softmax trained on other 9 queries; LOQO",
 "stage2_3":"dense and sparse candidate union, 2k fair leg budget, without hindsight",
 "stage2_4":"PCA64+interaction MLP on other 9 queries; LOQO; compare same hybrid candidate union RRF",
 "train_on_heldout_query":False,"reuse_stage1_generated_perspectives":True,
 "frozen_source_dataset_changed":False,"gate_folds":fold_counts,"mlp_folds":fit_notes}
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
table="\n".join(f"| {r['method']} | {r['mean_recall']:.3f} | {r['mean_perspective_coverage']:.3f} | {r['mean_proxy_strategy_coverage']:.3f} |" for r in summary if r["k"]==10)
(OUT/"RESULT.md").write_text("# v2.3 Stage 2 — Actual Dev Ablation Results\n"
 "\nReference is 2520 AI-only Silver judgments, not human-adjudicated Gold. Ten Dev questions; no held-out Test.\n"
 "\n| Method | Recall@10 | Perspective Coverage@10 | Derived Strategy Proxy@10 |\n|---|---:|---:|---:|\n"+table+
 "\n\nThe hybrid candidate union is separately controlled at equal 2k retrieval slots; do not conflate union gain with top-K gain.\n"
 "Gated and Interaction models use leave-one-QUERY-out training to avoid evaluating on labels used in their own fit; they may still overfit 10 Dev queries across folds.\n",encoding="utf-8")
print("PASS Stage 2 ablations",len(summary),"summary cells",flush=True)
