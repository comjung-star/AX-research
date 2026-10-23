#!/usr/bin/env python3
"""Stage 2-1/2/3/4 controlled v2.3 Dev experiments.

Replays frozen Stage 1 perspectives and embeddings. Trainable gate/MLP
use leave-one-QUERY-out splits (no target query relevance in training).
Do not treat Silver scoring as independently verified human Ground Truth.
"""
import csv,json,math
from collections import OrderedDict,defaultdict
from pathlib import Path
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from ax_research.selection import branch_balanced_unique

torch.set_num_threads(2)
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/"experiments/v23_dev/stage1"
OUT=ROOT/"experiments/v23_dev/stage2";OUT.mkdir(parents=True,exist_ok=True)
DOC=json.loads((ROOT/"data/v2_3/main_cases_v2_3.json").read_text(encoding="utf-8"))
CASES={v["case_id"]:v for v in DOC["cases"]}
QS=json.loads((ROOT/"data/v2_3/dev_query_candidates_v2_3.json").read_text(encoding="utf-8"))["queries"]
QIDS=[q["query_id"] for q in QS];GT=ROOT/"data/v2_3/ground_truth/silver_dev_qrels_2520.csv"
def read(path):
 with open(path,encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def write(path,rows):
 assert rows
 with open(path,"w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
gold=defaultdict(lambda:defaultdict(set))
for r in read(GT):
 if int(r["relevance_0_4"])>=3:gold[r["query_id"]][r["perspective_id"]].add(r["case_id"])
G={q:set().union(*gold[q].values()) for q in QIDS}
npz=np.load(SRC/"fixed_bge_m3_embeddings.npz")
ids=npz["case_ids"].tolist()
idx={cid:i for i,cid in enumerate(ids)}
view=np.stack([npz["problem_embeddings"],npz["task_embeddings"],npz["context_embeddings"]],axis=0)
qemb={k:v for k,v in zip(npz["branch_keys"].tolist(),npz["branch_embeddings"])}
keys=[k for k in npz["branch_keys"].tolist()]
brdata=read(SRC/"branch_rankings.csv")
B=defaultdict(dict)
for r in brdata:B[(r["query_id"],int(r["run_id"]),r["perspective_id"])].setdefault(r["retrieval"],[]).append(r["case_id"])
assert len(B)==len(keys) and all(len(v["bm25"])==len(v["dense"])==84 for v in B.values())
def ranking(score):return [ids[i] for i in sorted(range(len(ids)),key=lambda i:(-float(score[i]),ids[i]))]
def mets(q,ranked):
 sel=set(ranked);g=G[q];prs=[p for p in gold[q].values() if p]
 st={s for cid in g for s in CASES[cid]["strategy_labels"]}
 topstr={s for cid in sel for s in CASES[cid]["strategy_labels"]}
 return len(sel&g)/len(g) if g else None, sum(bool(sel&p) for p in prs)/len(prs) if prs else None, len(st&topstr)/len(st) if st else None
rows=[];rankings=[];candidate_rows=[];training_rows=[]
def result(system,q,run,ranked):
 assert len(set(ranked))==len(ranked)
 for rank,cid in enumerate(ranked[:20],1):
  rankings.append(dict(stage="2",system=system,query_id=q,run_id=run,rank=rank,case_id=cid))
 for k in (5,10,20):
  a,b,c=mets(q,ranked[:k])
  rows.append(dict(stage="2",system=system,query_id=q,run_id=run,k=k,
   recall=a,perspective_coverage=b,strategy_coverage=c,
   relevance_source="DEV_AI_SILVER_NOT_HUMAN_GOLD"))
# cache per-perspective 84x3 similarity (P/T/C) and candidate lists
sim={};equal={};hybrid={};dense20={}
for (q,rep,pid),v in B.items():
 key=f"{q}|{rep}|{pid}";x=qemb[key]
 sims=np.asarray([view[z]@x for z in range(3)],dtype=np.float32).T
 sim[key]=sims
 equal[key]=ranking(sims.mean(axis=1))
 dense20[key]=equal[key][:20]
 half=dense20[key][:10]+[x for x in v["bm25"][:10] if x not in dense20[key][:10]]
 hybrid[key]=half
 assert 10<=len(half)<=20
# Stage 2-1
for q in QIDS:
 for rep in (1,2,3):
  d=OrderedDict((k.split("|")[2],equal[k]) for k in keys if k.startswith(f"{q}|{rep}|"))
  result("stage2_1_equal_view",q,rep,[cid for _,cid in branch_balanced_unique(d,84)])
# Stage 2-2: query-conditioned gate learned from other questions only.
class Gate(nn.Module):
 def __init__(self, dim):
  super().__init__();self.linear=nn.Linear(dim,3);nn.init.zeros_(self.linear.weight);nn.init.zeros_(self.linear.bias)
 def forward(self,q,x):
  weights=F.softmax(self.linear(q),dim=-1);return (x*weights).sum(-1)
def fold_data(qtrain):
 feature=[];qvec=[];labs=[]
 for key in keys:
  q=key.split("|")[0]
  if q not in qtrain:continue
  qvec.extend([qemb[key]]*84);feature.extend(sim[key]);labs.extend([int(cid in G[q]) for cid in ids])
 return torch.tensor(np.asarray(qvec),dtype=torch.float32),torch.tensor(np.asarray(feature),dtype=torch.float32),torch.tensor(labs,dtype=torch.float32)
# train independent LOQO gate and MLP once for each query, then reuse across 3 repetitions
# Stage 2-3 same-slot union: 20 dense vs (10 dense + 10 sparse) per generated branch
for q in QIDS:
 for rep in (1,2,3):
  pkeys=[k for k in keys if k.startswith(f"{q}|{rep}|")]
  dd={cid for k in pkeys for cid in dense20[k]}
  uu={cid for k in pkeys for cid in hybrid[k]}
  g=G[q];active=[v for v in gold[q].values() if v]
  candidate_rows.append(dict(stage="2-3",query_id=q,run_id=rep,
   same_slots_per_branch=20,dense_candidate_count=len(dd),union_candidate_count=len(uu),
   dense_candidate_recall=len(dd&g)/len(g) if g else 0,
   hybrid_candidate_recall=len(uu&g)/len(g) if g else 0,
   dense_covered_views=sum(bool(dd&p) for p in active)/len(active) if active else None,
   hybrid_covered_views=sum(bool(uu&p) for p in active)/len(active) if active else None,
   hybrid_added_relevant=len((uu-dd)&g),hybrid_lost_relevant=len((dd-uu)&g)))
# Stage2-4 interaction [q,c,q*c,|q-c|] -> MLP.
D=npz["document_embeddings"].shape[1]; rng=np.random.default_rng(42)
P=rng.normal(0,1/math.sqrt(D),size=(D,48)).astype(np.float32)
cn=(npz["document_embeddings"]@P).astype(np.float32)
qn={key:qemb[key]@P for key in keys}
def interaction(key,cids):
 qq=qn[key]; cc=cn[[idx[c] for c in cids]]
 return np.concatenate([np.repeat(qq[None,:],len(cids),axis=0),cc,cc*qq[None,:],np.abs(cc-qq[None,:])],axis=1)
class MLP(nn.Module):
 def __init__(self):super().__init__();self.net=nn.Sequential(nn.Linear(48*4,64),nn.ReLU(),nn.Linear(64,1))
 def forward(self,x):return self.net(x).squeeze(1)
for held in QIDS:
 training=[q for q in QIDS if q!=held]
 assert held not in training
 torch.manual_seed(42)
 gate=Gate(D)
 xq,xv,y=fold_data(set(training))
 optim=torch.optim.Adam(gate.parameters(),lr=.012,weight_decay=0.0005)
 pos=max(float(y.sum()),1); neg=max(float(len(y)-y.sum()),1)
 for ep in range(32):
  optim.zero_grad();out=gate(xq,xv)
  loss=F.binary_cross_entropy_with_logits(out*8,y,pos_weight=torch.tensor(neg/pos))
  loss.backward();optim.step()
 torch.manual_seed(42)
 model=MLP();op=torch.optim.Adam(model.parameters(),lr=.003,weight_decay=.003)
 feats=[];labs=[]
 for key in keys:
  q=key.split("|")[0]
  if q not in training:continue
  cs=hybrid[key]
  feats.append(interaction(key,cs));labs.extend([int(cid in G[q]) for cid in cs])
 x=torch.tensor(np.concatenate(feats),dtype=torch.float32)
 yy=torch.tensor(labs,dtype=torch.float32)
 pos=max(float(yy.sum()),1);neg=max(float(len(yy)-yy.sum()),1)
 for ep in range(32):
  op.zero_grad();v=model(x)
  loss=F.binary_cross_entropy_with_logits(v,yy,pos_weight=torch.tensor(neg/pos))
  loss.backward();op.step()
 training_rows.append(dict(heldout_query=held,training_queries="|".join(training),
  gate_training_examples=len(y),interaction_training_examples=len(yy),
  train_label="SILVER_QUERY_UNION",label_leakage_to_heldout=False,
  gate_final_loss=float(loss.item()),random_seed=42))
 for rep in (1,2,3):
  pkeys=[k for k in keys if k.startswith(f"{held}|{rep}|")]
  gates=OrderedDict();rrf=OrderedDict();interaction_ranks=OrderedDict()
  for key in pkeys:
   with torch.no_grad():
    scores=gate(torch.tensor(np.repeat(qemb[key][None,:],84,axis=0),dtype=torch.float32),
      torch.tensor(sim[key],dtype=torch.float32)).numpy()
   gates[key.split("|")[2]]=ranking(scores)
   cs=hybrid[key]; bm=B[(held,rep,key.split("|")[2])]["bm25"]
   dr=dense20[key]
   rv={cid:1/(60+i+1) for i,cid in enumerate(dr)}
   for i,cid in enumerate(bm[:10]):rv[cid]=rv.get(cid,0)+1/(60+i+1)
   rrf[key.split("|")[2]]=sorted(cs,key=lambda c:(-rv.get(c,0),c))
   with torch.no_grad():p=model(torch.tensor(interaction(key,cs),dtype=torch.float32)).numpy()
   interaction_ranks[key.split("|")[2]]=[c for c,_ in sorted(zip(cs,p),key=lambda z:(-float(z[1]),z[0]))]
  result("stage2_2_learned_gated_LOQO",held,rep,[c for _,c in branch_balanced_unique(gates,84)])
  result("stage2_4_same_pool_rrf",held,rep,[c for _,c in branch_balanced_unique(rrf,20)])
  result("stage2_4_query_case_MLP_LOQO",held,rep,[c for _,c in branch_balanced_unique(interaction_ranks,20)])
write(OUT/"rankings_top20.csv",rankings);write(OUT/"metrics_by_query.csv",rows)
write(OUT/"candidate_union_metrics.csv",candidate_rows);write(OUT/"leave_one_query_out_folds.csv",training_rows)
summary=[]
for system in sorted({r["system"] for r in rows}):
 for k in (5,10,20):
  xx=[r for r in rows if r["system"]==system and r["k"]==k]
  summary.append(dict(system=system,k=k,n=len(xx),
   recall_mean=float(np.mean([r["recall"] for r in xx if r["recall"] is not None])),
   perspective_coverage_mean=float(np.mean([r["perspective_coverage"] for r in xx if r["perspective_coverage"] is not None])),
   strategy_coverage_mean=float(np.mean([r["strategy_coverage"] for r in xx if r["strategy_coverage"] is not None]))))
write(OUT/"summary.csv",summary)
manifest=dict(stage="STAGE_2_REAL_EXECUTED",corpus_cases=84,source=SRC.as_posix(),
 methods=["2-1 equal-view","2-2 learned query-conditioned gate LOQO","2-3 dense+sparse candidate union equal budget",
 "2-4 query-case MLP LOQO with identical RRF pool"],
 target_scores="DEV_AI_SILVER_NOT_HUMAN_GT",positive_threshold=3,
 test_set="NOT_AVAILABLE",train_test_leakage="QUERY_LOQO_HOLDS_TARGET_OUT",
 evaluation_reference_perspectives_not_in_runtime=True,
 same_candidate_budget_per_branch=20,folds=10,perspective_branches=len(keys))
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("STAGE2 COMPLETE",json.dumps(summary),flush=True)
