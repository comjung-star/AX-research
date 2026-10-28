"""Offline original-only four-system runner; qrels never opened during inference."""
import argparse
import importlib.metadata
import os
import platform
import re
import socket
import subprocess
import sys
import traceback
from fractions import Fraction
from pathlib import Path

import numpy as np
from ax_research.heldout import (read, sha, write, jsonl, questions, manifest,
    input_path, evaluate, validate_predictions, SYSTEMS)
from ax_research.functional_mapping import extract, compare, case_profile, ranking_key as rule_key
from ax_research.semantic_mapping import field_profile, compare_fields, combined_score, ranking_key

ROOT = Path(__file__).resolve().parents[1]
BASE = '1e9523ed2da67ec43fabc901774b1f163edc51ab'
SEM = ROOT/'docs/query-case-semantic-mapping-2026-10-28'
RETR = ROOT/'docs/dense-bm25-candidates-2026-10-27'
POLICY = ROOT/'configs/heldout_policy_v1.json'
CORPUS = RETR/'case_registry.json'
PROTECTED = [
    'configs/semantic_mapping_20261028.json', 'configs/functional_mapping_20261028.json',
    'src/ax_research/semantic_mapping.py', 'src/ax_research/functional_mapping.py',
    'src/ax_research/retrieval/bm25.py', 'data/v2_5/research/evidence_catalog.jsonl',
    'data/v2_5/research/dev_queries.json', 'configs/blind_pilot_five_20261028.json',
    'docs/query-case-semantic-mapping-2026-10-28/preregistration.json',
    'docs/query-case-semantic-mapping-2026-10-28/mapping/case_profiles.json',
    'docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz',
    'docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json',
    'docs/stage123-openai-triplicate-2026-10-27/embeddings.npz',
    'docs/dense-bm25-candidates-2026-10-27/case_registry.json',
    'docs/dense-bm25-candidates-2026-10-27/bm25_corpus_statistics.json']


def blocked(*args, **kwargs):
    raise RuntimeError('Network disabled in heldout runner')


def freeze(model_path):
    hashes = {}
    for name in PROTECTED:
        original = subprocess.check_output(['git', 'show', f'{BASE}:{name}'], cwd=ROOT)
        raw = (ROOT/name).read_bytes()
        if raw.replace(b'\r\n', b'\n') != original.replace(b'\r\n', b'\n'):
            raise ValueError('Frozen input drift: '+name)
        hashes[name] = sha(ROOT/name)
    old = read(SEM/'preregistration.json')
    models = {n: sha(model_path/n) for n in old['model_sha256']}
    if models != old['model_sha256']:
        raise ValueError('Model drift')
    versions = {n: importlib.metadata.version(n) for n in old['packages']}
    if versions != old['packages']:
        raise ValueError('Frozen package drift')
    own = [POLICY, Path(__file__), ROOT/'src/ax_research/heldout.py']
    return {'base': BASE, 'protected': hashes, 'model': models, 'packages': versions,
            'adapter': {p.relative_to(ROOT).as_posix(): sha(p) for p in own},
            'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'python': platform.python_version(), 'platform': platform.platform(),
            'command': sys.argv, 'model_path': str(model_path), 'policy': read(POLICY)}


def known_queries():
    dev = read(ROOT/'data/v2_5/research/dev_queries.json')['queries']
    pilot = read(ROOT/'configs/blind_pilot_five_20261028.json')['questions']
    return ([{'query_id': q['query_id'], 'text': q['query']} for q in dev] +
            [{'query_id': q['qid'], 'text': q['text']} for q in pilot])


def predict(qs, model_path, out):
    """Frozen pilot computation copied as adapter; no label-dependent inputs."""
    from ax_research.retrieval.bm25 import KiwiTokenizer
    cfg = read(ROOT/'configs/semantic_mapping_20261028.json')
    rules = read(ROOT/'configs/functional_mapping_20261028.json')
    cases = read(CORPUS)['cases']; ids = sorted(cases)
    if len(ids) != 112: raise ValueError('Expected frozen112 corpus')
    cp = read(SEM/'mapping/case_profiles.json')
    rp = read(ROOT/'docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json')
    if any(case_profile(c,rules) != rp[cid] or field_profile(c['task'],cfg,rules['negation_guard'],executed=True,context=c['context']) != cp[cid] for cid,c in cases.items()):
        raise ValueError('Case profile drift')
    qp = {q['query_id']:field_profile(q['text'],cfg,rules['negation_guard']) for q in qs}
    rq = {q['query_id']:extract(q['text'],rules) for q in qs}
    z = np.load(SEM/'mapping/embeddings.npz', allow_pickle=False)
    emb = dict(zip(z['texts'].tolist(), z['vectors']))
    alltexts = sorted({q['text'] for q in qs} | {v for p in qp.values() for v in p['fields'].values() if v})
    texts = sorted(set(alltexts)-set(emb))
    for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','HF_HUB_DISABLE_TELEMETRY'): os.environ[key] = '1'
    import torch
    from sentence_transformers import SentenceTransformer
    torch.manual_seed(cfg['seed']); np.random.seed(cfg['seed']); torch.set_num_threads(cfg['threads']); torch.use_deterministic_algorithms(True)
    model = SentenceTransformer(str(model_path),device=cfg['device'],local_files_only=True)
    model.max_seq_length = cfg['max_tokens']
    lengths = [len(model.tokenizer.encode(t)) for t in alltexts]
    if max(lengths) > cfg['max_tokens']: raise ValueError('Input exceeds4096 tokens; no truncation')
    if texts:
        vectors = model.encode(texts,batch_size=cfg['batch_size'],normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False).astype(np.float32)
        if vectors.shape != (len(texts),1024) or not np.isfinite(vectors).all() or not np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-5):
            raise ValueError('Invalid query embeddings')
        emb.update(zip(texts,vectors))
        np.savez_compressed(out/'new_query_vectors.npz',texts=np.array(texts),vectors=vectors)
    dense = np.load(ROOT/'docs/stage123-openai-triplicate-2026-10-27/embeddings.npz',allow_pickle=False)
    matrix = dict(zip(dense['case_ids'].tolist(),dense['single']))
    corpus = read(RETR/'bm25_corpus_statistics.json'); tokenizer = KiwiTokenizer()
    systems = {s:[] for s in SYSTEMS}; details = []
    for q in qs:
        qid = q['query_id']; dv = {c:float(np.dot(matrix[c],emb[q['text']])) for c in ids}
        tokens = tokenizer.tokenize(q['text']); bv = {}
        for c in ids:
            tf=corpus['document_frequencies_by_case'][c]; length=corpus['document_lengths_by_case'][c]
            k1=corpus['k1']; b=corpus['b']; avg=corpus['average_document_length']
            bv[c]=sum(corpus['idf'].get(t,0)*tf.get(t,0)*(k1+1)/(tf.get(t,0)+k1*(1-b+b*length/avg)) for t in tokens)
        dr=sorted(ids,key=lambda c:(-dv[c],c)); br=sorted(ids,key=lambda c:(-bv[c],c))
        tie={c:float((Fraction(1,60+dr.index(c)+1)+Fraction(1,60+br.index(c)+1))/2) for c in ids}
        maps={c:compare(rq[qid],rp[c]) for c in ids}
        sem={c:compare_fields(qp[qid],cp[c],emb,cfg['weights']) for c in ids}
        comb={c:combined_score(maps[c]['mapping_grade'],sem[c]['score']) for c in ids}
        rankings={'Single Dense':dr,'A':sorted(ids,key=lambda c:rule_key(maps[c],[],tie[c],c)),
                  'B':sorted(ids,key=lambda c:ranking_key(sem[c]['score'],tie[c],c)),
                  'C':sorted(ids,key=lambda c:ranking_key(comb[c],tie[c],c))}
        scores={'Single Dense':dv,'A':{c:maps[c]['mapping_grade'] for c in ids},'B':{c:sem[c]['score'] for c in ids},'C':comb}
        for s,ranking in rankings.items():
            systems[s].append({'query_id':qid,'ranking':ranking, **{f'top{k}':ranking[:k] for k in (5,10,20)},'scores':scores[s]})
        for c in ids:
            details.append({'query_id':qid,'case_id':c,'case':cases[c],'rule':maps[c],'semantic':sem[c], 'combined':comb[c],'dense':dv[c],'bm25':bv[c],'retrieval_tie':tie[c]})
    write(out/'evidence.json',{'records':details,'query_profiles':qp,'rule_profiles':rq})
    pred={'case_ids':ids,'query_ids':[q['query_id'] for q in qs],'systems':systems,'scope':'original_only_O_SINGLE'}
    validate_predictions(pred)
    return pred


def inference(args, out):
    model_path=Path(args.model_path).resolve()
    state=freeze(model_path); write(out/'freeze.json',state)
    if args.development:
        path=Path(args.questions).resolve(); m=None
    else:
        m=manifest(args.manifest,sha(CORPUS))  # metadata only; never opens qrels
        path=input_path(args.manifest,m['files']['questions'])
        write(out/'manifest_metadata.json',m)
    qs=questions(path,development=args.development,previous=known_queries())
    write(out/'input_receipt.json',{'questions_sha256':sha(path),'query_count':len(qs),'development':args.development,'manifest_sha256':sha(args.manifest) if m else None,'qrels_read':False})
    pred=predict(qs,model_path,out)
    write(out/'predictions.json',pred)
    for k in (5,10,20):
        write(out/f'top{k}.json',{s:[{'query_id':r['query_id'],'case_ids':r[f'top{k}']} for r in rows] for s,rows in pred['systems'].items()})
    # No data/config/core drift during inference.
    if freeze(model_path) != state: raise ValueError('Runtime input drift')
    files={p.name:sha(p) for p in out.iterdir() if p.is_file()}
    write(out/'complete.json',{'state':'COMPLETE','files':files,'api_calls':0,'qrels_read':False,'development':args.development})


def evaluation(args,out):
    source=Path(args.prediction_run).resolve(); done=read(source/'complete.json')
    if done['state'] != 'COMPLETE': raise ValueError('Prediction incomplete')
    for name,digest in done['files'].items():
        if Path(name).name != name or sha(source/name) != digest: raise ValueError('Prediction artifact drift')
    frozen=read(source/'freeze.json')
    for name,digest in frozen['adapter'].items():
        if sha(ROOT/name) != digest: raise ValueError('Adapter/policy changed after prediction')
    write(out/'evaluation_environment.json',{'python':platform.python_version(),'platform':platform.platform(),'command':sys.argv})
    receipt=read(source/'input_receipt.json'); pred=read(source/'predictions.json')
    if args.development:
        if not receipt['development']: raise ValueError('Cannot evaluate TEST as DEV')
        qpath=Path(args.qrels); scope=args.scope; sources=args.label_sources
    else:
        if receipt['development']: raise ValueError('DEV cannot become TEST')
        m=manifest(args.manifest,sha(CORPUS))
        if sha(args.manifest) != receipt['manifest_sha256'] or m != read(source/'manifest_metadata.json'): raise ValueError('Manifest drift')
        if m['files']['questions']['sha256'] != receipt['questions_sha256']: raise ValueError('Question drift')
        qpath=input_path(args.manifest,m['files']['qrels']); scope=m['judgment_scope']; sources=m['label_sources']
    result=evaluate(pred,jsonl(qpath),scope,sources)
    result['development']=args.development
    write(out/'metrics.json',result)
    write(out/'complete.json',{'state':'COMPLETE','prediction_seal_sha256':sha(source/'complete.json'),'qrels_sha256':sha(qpath),'policy_sha256':sha(POLICY),'metrics_sha256':sha(out/'metrics.json'),'development':args.development})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='stage',required=True)
    for name in ('infer','evaluate'):
        a=sub.add_parser(name); a.add_argument('--run-id',required=True); a.add_argument('--output-root',required=True)
        a.add_argument('--manifest'); a.add_argument('--development',action='store_true')
        if name=='infer':
            a.add_argument('--questions'); a.add_argument('--model-path',required=True)
        else:
            a.add_argument('--prediction-run',required=True); a.add_argument('--qrels')
            a.add_argument('--scope',choices=['FULL_CORPUS','PARTIAL'],default='PARTIAL')
            a.add_argument('--label-sources',nargs='+',choices=['AI-Silver','Human-Gold'],default=['AI-Silver'])
    args=p.parse_args()
    if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,99}',args.run_id): p.error('Invalid run-id')
    if args.development:
        if not (args.questions if args.stage=='infer' else args.qrels) or args.manifest: p.error('DEV requires explicit input and no manifest')
    elif not args.manifest or (args.stage=='infer' and args.questions) or (args.stage=='evaluate' and args.qrels):
        p.error('TEST requires manifest; no direct input override')
    root=Path(args.output_root).resolve()
    # Never write into tracked research output trees.
    if root == ROOT or ROOT in root.parents: p.error('Output root must be outside repository')
    root.mkdir(parents=True,exist_ok=True); out=root/args.run_id; out.mkdir(exist_ok=False)
    socket.socket.connect=blocked; socket.create_connection=blocked
    try:
        write(out/'started.json',{'stage':args.stage,'command':sys.argv,'development':args.development})
        (inference if args.stage=='infer' else evaluation)(args,out)
    except BaseException as exc:
        write(out/'failed.json',{'state':'FAILED','error_type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc(),'resume':'Do not overwrite or blindly retry. Inspect failure; new run-id only.'})
        raise
    print(str(out),flush=True)


if __name__=='__main__': main()
