#!/usr/bin/env python3
"""Stage3/4: genuine 256D query-conditioned Gated Multi-view + QCI LOQO audit.

Primary scoring: 2-pass AI-Silver consensus only. Supplemental 3-pass audit only
on originally conflicted pairs; no evaluation-score-driven tuning. No human Gold.
"""
from __future__ import annotations
import csv,json,math,random
from pathlib import Path
from collections import defaultdict,Counter
from statistics import mean
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"experiments/v23_dev/stage1"
LABELS=ROOT/"experiments/v23_runtime_perspective_qrels/runtime_qrels_8148.csv"
TRAIN=ROOT/"experiments/v23_qci256_four_step/stage2_training_label_manifest.csv"
OUT=ROOT/"experiments/v23_qci256_four_step"
SEED=42
EPOCHS=24
KVALS=(5,10)
MODEL_NAMES=("dense_3view","gated_qci_256","dense_anchor_gated_qci_256")
ALPHA=0.10
def read(p):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def write(p,rs):
    if not rs:raise AssertionError(f"Empty {p}")
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def parsekey(row):
    return (row["query_id"],int(row["run_id"]),
           row.get("runtime_perspective_id",row.get("perspective_id")),row["case_id"])

class GatedFusionQCI(nn.Module):
    """Frozen 1024D embedding -> trainable 256D shared view projection + query-case gate.

    The gate is query conditioned, returns three attention weights for each case.
    QCI MLP then compares projected query to fused 3-view case representation.
    """
    def __init__(self,in_dim=1024,out_dim=256):
        super().__init__()
        self.projection=nn.Linear(in_dim,out_dim,bias=False)
        self.view_gate=nn.Linear(2*out_dim,1)
        self.reranker=nn.Sequential(nn.Linear(4*out_dim,64),nn.ReLU(),
                                    nn.Linear(64,1))
    def forward(self, query,view_emb):
        # query n,1024; view_emb case,3,1024
        q=F.normalize(self.projection(query),dim=-1)
        v=F.normalize(self.projection(view_emb),dim=-1)
        qq=q[:,None,None,:].expand(-1,v.shape[0],v.shape[1],-1)
        cc=v[None].expand(q.shape[0],-1,-1,-1)
        gate=torch.softmax(self.view_gate(torch.cat((qq,cc),dim=-1)).squeeze(-1),dim=-1)
        fused=F.normalize((gate[...,None]*cc).sum(dim=2),dim=-1)
        qb=q[:,None,:].expand_as(fused)
        interaction=torch.cat((qb,fused,qb*fused,torch.abs(qb-fused)),dim=-1)
        output=self.reranker(interaction).squeeze(-1)
        return output,gate

def load():
    if not TRAIN.exists():
        raise FileNotFoundError("Stage 1-2 third blind judgement outputs not yet validated")
    raw=np.load(SRC/"fixed_bge_m3_embeddings.npz")
    ids=[str(c) for c in raw["case_ids"].tolist()]
    keys=[str(c) for c in raw["branch_keys"].tolist()]
    assert len(ids)==84 and len(keys)==97 and len(set(keys))==97
    query=np.asarray(raw["branch_embeddings"],dtype=np.float32)
    views=np.stack([raw["problem_embeddings"],raw["task_embeddings"],raw["context_embeddings"]],axis=1).astype(np.float32)
    if query.shape!=(97,1024) or views.shape!=(84,3,1024):
        raise AssertionError((query.shape,views.shape))
    original=read(LABELS)
    revised=read(TRAIN)
    case_idx={cid:i for i,cid in enumerate(ids)}
    view_idx={x:i for i,x in enumerate(keys)}
    assert len(original)==len(revised)==8148
    assert len({parsekey(r) for r in original})==8148
    assert len({parsekey(r) for r in revised})==8148
    primary=np.full((len(keys),len(ids)),-1,dtype=np.int8)
    supplemental=np.full_like(primary,-1)
    for x in original:
        k=f'{x["query_id"]}|{x["run_id"]}|{x["runtime_perspective_id"]}'
        i,j=view_idx[k],case_idx[x["case_id"]]
        if x["include_in_training"]=="1":
            primary[i,j]=int(x["provisional_train_binary_relevant"])
    for x in revised:
        k=f'{x["query_id"]}|{x["run_id"]}|{x["perspective_id"]}'
        i,j=view_idx[k],case_idx[x["case_id"]]
        if x["train_eligible"]=="1":
            supplemental[i,j]=int(x["train_binary"])
        if primary[i,j]!=-1 and supplemental[i,j]!=primary[i,j]:
            raise AssertionError("Review silently modified original agreed label")
        if primary[i,j]==-1 and supplemental[i,j]!=-1 and not (x["old_threshold_dispute"]=="1" and x["third_pass_checked"]=="1"):
            raise AssertionError("Non-conflicted label reclassified")
    if (primary>=0).sum()!=7979 or (primary==1).sum()!=311 or (primary==-1).sum()!=169:
        raise AssertionError("Original two-pass qrels changed unexpectedly")
    if np.any((primary>=0)&(supplemental<0)):
        raise AssertionError("Lost originally agreed training examples")
    return ids,keys,query,views,primary,supplemental

def pair_indices(trainlabels, dense, seed):
    """Deterministic within-training-view positive/hard-negative pairs.
    Draw hard negatives from Dense (not from any held query relevance).
    """
    rng=np.random.default_rng(seed)
    posrow=[];negrow=[];pi=[];ni=[]
    for bi in range(len(trainlabels)):
        p=np.where(trainlabels[bi]==1)[0]
        n=np.where(trainlabels[bi]==0)[0]
        if not len(p) or not len(n):
            continue
        order=n[np.argsort(-dense[bi,n])]
        hardest=order[:min(24,len(order))]
        for x in p:
            picks=rng.choice(hardest,size=min(3,len(hardest)),replace=False)
            for y in picks:
                posrow.append(bi);negrow.append(bi);pi.append(int(x));ni.append(int(y))
    if not pi:raise AssertionError("No training positive vs negative pair")
    return [torch.tensor(z,dtype=torch.long) for z in (posrow,negrow,pi,ni)]

def train_one(held,keys,query,case_views,train_labels,dense_matrix):
    qids=sorted({k.split("|")[0] for k in keys})
    idx=np.array([i for i,k in enumerate(keys) if k.split("|")[0]!=held])
    assert set(k.split("|")[0] for i,k in enumerate(keys) if i in set(idx))==set(qids)-{held}
    assert not any(keys[i].startswith(held+"|") for i in idx)
    torch.manual_seed(SEED);np.random.seed(SEED);random.seed(SEED)
    model=GatedFusionQCI()
    opt=torch.optim.AdamW(model.parameters(),lr=.002,weight_decay=.001)
    qt=torch.from_numpy(query[idx].copy())
    case=torch.from_numpy(case_views.copy())
    labs=torch.from_numpy(train_labels[idx].astype(np.int64))
    known=labs>=0
    if not bool(known.any()) or not bool((labs==1).any()):raise AssertionError("No positive training labels")
    positives=int((labs==1).sum())
    negatives=int((labs==0).sum())
    weight=float(min(30,negatives/positives))
    pw=pair_indices(train_labels[idx],dense_matrix[idx],seed=SEED)
    final={}
    for epoch in range(EPOCHS):
        model.train()
        raw,_=model(qt,case)
        targets=labs[known].float()
        loss_bce=F.binary_cross_entropy_with_logits(raw[known],targets,pos_weight=torch.tensor(weight))
        rp,rn,cp,cn=pw
        loss_pair=F.softplus(-(raw[rp,cp]-raw[rn,cn])).mean()
        loss=loss_bce+0.35*loss_pair
        if not torch.isfinite(loss):raise AssertionError("NaN training loss")
        opt.zero_grad();loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(),2.)
        opt.step()
        final={"train_loss":float(loss.detach()),"bce":float(loss_bce.detach()),
               "pairwise":float(loss_pair.detach())}
    model.eval()
    return model,dict(held_query=held,train_query_ids="|".join(q for q in qids if q!=held),
        train_query_count=9,training_views=int(len(idx)),training_pairs=int(known.sum()),
        training_positives=positives,training_negatives=negatives,
        param_count=sum(p.numel() for p in model.parameters()),epochs=EPOCHS,
        seed=SEED,**final)

def evaluate(keys,ids,scores,primary,supplemental):
    # Metrics defined per runtime generated perspective. No collapsing Rashomon.
    rmetrics=[]; rankings=[]
    views_by_query=defaultdict(list)
    for i,key in enumerate(keys):
        qid,run,pid=key.split("|")
        views_by_query[qid].append(i)
        for scorer in MODEL_NAMES:
            ranks=np.lexsort((np.asarray(ids),-scores[scorer][i]))
            for j,ci in enumerate(ranks[:10],1):
                rankings.append(dict(query_id=qid,run_id=run,perspective_id=pid,
                      scorer=scorer,rank=j,case_id=ids[ci],score=float(scores[scorer][i,ci])))
            for basis,lbl in (("primary_two_pass",primary),("supplemental_three_pass",supplemental)):
                relevant=np.where(lbl[i]==1)[0]
                unknown=int((lbl[i]<0).sum())
                for k in KVALS:
                    chosen=ranks[:k]
                    hits=int(np.isin(chosen,relevant).sum())
                    rmetrics.append(dict(query_id=qid,run_id=run,perspective_id=pid,
                        scorer=scorer,label_basis=basis,k=k,
                        confirmed_positive=len(relevant),
                        unresolved_case_labels=unknown,
                        zero_positive_view=int(len(relevant)==0),
                        retrieved_relevant=hits,
                        recall="" if not len(relevant) else hits/len(relevant),
                        known_silver_precision=hits/k,
                        topk_unknown_labels=int((lbl[i,chosen]<0).sum())))
    by_q=defaultdict(list)
    by_view=defaultdict(list)
    for r in rmetrics:
        by_q[(r["label_basis"],r["scorer"],r["k"],r["query_id"])].append(r)
        by_view[(r["label_basis"],r["scorer"],r["k"])].append(r)
    qrows=[]; summary=[]
    for (basis,scorer,k,q),rs in sorted(by_q.items()):
        valid=[r for r in rs if r["recall"]!=""]
        qrows.append(dict(label_basis=basis,scorer=scorer,k=k,query_id=q,
            views=len(rs),answerable_views=len(valid),empty_views=len(rs)-len(valid),
            macro_recall="" if not valid else mean(float(x["recall"]) for x in valid),
            macro_known_silver_precision=mean(float(x["known_silver_precision"]) for x in rs),
            confirmed_positive_total=sum(x["confirmed_positive"] for x in rs),
            hits_total=sum(x["retrieved_relevant"] for x in rs)))
    for (basis,scorer,k),rs in sorted(by_view.items()):
        qq=[x for x in qrows if x["label_basis"]==basis and x["scorer"]==scorer and x["k"]==k]
        valid=[x for x in rs if x["recall"]!=""]
        goodquery=[float(x["macro_recall"]) for x in qq if x["macro_recall"]!=""]
        if len(qq)!=10 or len(goodquery)<8:
            raise AssertionError("Query folds unexpectedly missing")
        summary.append(dict(label_basis=basis,scorer=scorer,k=k,
            original_queries=10,query_runs=30,generated_views=len(rs),
            answerable_views=len(valid),zero_positive_views=len(rs)-len(valid),
            query_macro_recall=mean(goodquery),
            perspective_macro_recall=mean(float(x["recall"]) for x in valid),
            query_macro_known_precision=mean(float(x["macro_known_silver_precision"]) for x in qq),
            perspective_macro_known_precision=mean(float(x["known_silver_precision"]) for x in rs),
            relevant_case_retrievals=sum(int(x["retrieved_relevant"]) for x in rs),
            query_macro_denominator_count=len(goodquery),
            note="TWO_PASS_AI_SILVER_NOT_INDEPENDENT_TEST" if basis=="primary_two_pass" else
                 "SELECTIVELY_AUGMENTED_THIRD_AI_SILVER_NOT_HUMAN_GOLD"))
    return rmetrics,qrows,summary,rankings

def main():
    torch.set_num_threads(2)
    ids,keys,queries,caseviews,primary,supplemental=load()
    casevecs=caseviews.transpose(1,0,2)
    dense=(casevecs@queries.T).mean(axis=0).T.astype(np.float32)
    assert dense.shape==(97,84)
    score={"dense_3view":dense,"gated_qci_256":np.full((97,84),np.nan,dtype=np.float32),
           "dense_anchor_gated_qci_256":np.full((97,84),np.nan,dtype=np.float32)}
    audit=[]
    selected=set()
    for held in sorted({s.split("|")[0] for s in keys}):
        model,fold=train_one(held,keys,queries,caseviews,supplemental,dense)
        ix=np.array([i for i,k in enumerate(keys) if k.startswith(held+"|")])
        assert len(ix)>0 and not (selected & set(ix))
        selected.update(ix.tolist())
        with torch.no_grad():
            t,_=model(torch.from_numpy(queries[ix].copy()),torch.from_numpy(caseviews.copy()))
            predicted=t.detach().numpy()
        if not np.isfinite(predicted).all():raise AssertionError("Nonfinite QCI scores")
        score["gated_qci_256"][ix]=predicted
        score["dense_anchor_gated_qci_256"][ix]=dense[ix]+ALPHA*np.tanh(predicted)
        fold["held_views"]=len(ix)
        audit.append(fold)
        print("QCI256_LOQO_FOLD",held,"loss",round(fold["train_loss"],6),flush=True)
    assert selected==set(range(97))
    assert all(np.isfinite(x).all() for x in score.values())
    rmetrics,qrows,summary,ranking=evaluate(keys,ids,score,primary,supplemental)
    OUT.mkdir(parents=True,exist_ok=True)
    write(OUT/"stage34_fold_train_audit.csv",audit)
    write(OUT/"stage34_perspective_metrics.csv",rmetrics)
    write(OUT/"stage34_query_metrics.csv",qrows)
    write(OUT/"stage34_summary.csv",summary)
    write(OUT/"stage34_top10_rankings.csv",ranking)
    table={(r["label_basis"],r["scorer"],int(r["k"])):r for r in summary}
    primary10={m:table[("primary_two_pass",m,10)]["query_macro_recall"] for m in MODEL_NAMES}
    primary5={m:table[("primary_two_pass",m,5)]["query_macro_recall"] for m in MODEL_NAMES}
    reference=primary10["dense_3view"]
    winner=max(MODEL_NAMES,key=lambda m:primary10[m])
    result=dict(status="FOUR_STEP_256QCI_REAL_CPU_LOQO_COMPLETE_DEV_AI_SILVER",
        created_from="frozen_1024d_BGE_M3_stage1_embeddings_97_perspectives_84_cases",
        primary_evaluation="TWO_PASS_RUNTIME_PERSPECTIVE_SILVER_NOT_INDEPENDENT_GOLD",
        reference_baseline_old_6332_percent_is_different_label_protocol=True,
        attention_gate="LEARNED_QUERY_CONDITIONED_3VIEW_SOFTMAX",
        model="SHARED_LINEAR_1024_TO_256_PLUS_GATED_FUSION_PLUS_INTERACTION_1024_TO_64_TO_1",
        training="BCE_POS_WEIGHT_PLUS_PAIRWISE_RANKNET",training_epochs=EPOCHS,
        anchor_alpha=ALPHA,
        train_split="10_QUERY_GROUP_LOQO_NO_SAME_QUERY_3RUNS_LEAK",
        primary_macro_recall_at_10=primary10,primary_macro_recall_at_5=primary5,
        winner_primary_top10=winner,
        model_adoption="ADOPT_AS_DEV_CANDIDATE_ONLY" if winner!="dense_3view" else "RETAIN_DENSE_BASELINE",
        outputs=["stage34_fold_train_audit.csv","stage34_perspective_metrics.csv",
            "stage34_query_metrics.csv","stage34_summary.csv","stage34_top10_rankings.csv"],
        caveats=["Only 10 independent business questions, not external Test",
          "Gold human data unavailable; both reference/test are AI-Silver",
          "Training used 3rd pass to resolve 17 selectively reviewed conflicts, primary evaluation uses original 2-pass agreement",
          "Unknown qrels excluded from positive recall denominators, reported separately",
          "Earlier Dense 63.32% used different reference union metric; do not directly compare"])
    (OUT/"stage34_summary.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("STAGE3_4_COMPLETED",json.dumps(result,ensure_ascii=False),flush=True)

if __name__=="__main__":main()
