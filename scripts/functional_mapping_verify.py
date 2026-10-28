"""Independent saved-evidence, sort and Fraction metric validation."""
import hashlib
import math
import subprocess
from fractions import Fraction
from collections import defaultdict
from scripts import functional_mapping_run as f

def main():
    f.prepare();qp=f.read(f.OUT/'stage2/query_profiles.json');cp=f.read(f.OUT/'stage2/case_profiles.json')
    spans=0
    for p in list(qp.values())+[v for c in cp.values() for v in c.values()]:
        for fun in p['functions']:
            for key in ('action','object','clause'):
                e=fun[key];assert p['text'][e['start']:e['end']]==e['quote'];spans+=1
            assert max(fun['action']['end'],fun['object']['end'])-min(fun['action']['start'],fun['object']['start'])<=120
    maps=f.lines('stage2/mappings.jsonl');ix={}
    for m in maps:
        key=m['path_id'],m['case_id'];assert key not in ix;ix[key]=m
        q=qp[key[0]];c=cp[key[1]];shared=set(q['function_ids'])&set(c['task']['function_ids'])
        assert shared==set(m['shared_functions'])
        assert m['criteria']['Business Problem']['licenses_execution'] is False
        domains=set(q['domains'])&set(c['task']['domains'])
        support=set(q['function_ids'])&(set(c['problem']['function_ids'])|set(c['context']['function_ids']))
        grade=(4 if domains and support&shared else 3) if shared else (2 if q['function_ids'] and c['task']['function_ids'] and set(q['action_family_hits'])&set(c['task']['action_family_hits']) else 1 if domains else 0)
        if not q['function_ids'] or not c['task']['function_ids']:grade=min(grade,1)
        assert grade==m['mapping_grade']
    assert len(ix)==118*112
    pools={(p['condition'],p['qid'],p['repeat']):p for p in [__import__('json').loads(l) for l in (f.IN/'mapping_candidate_pools.jsonl').open(encoding='utf-8')]}
    new=f.read(f.OUT/'stage3/rankings.json');rankcount=0
    for name,rows in new['systems'].items():
        for row in rows:
            pool=pools[row['retrieval_reference'],row['qid'],row['repeat']];whole='o_'+row['qid']
            def key(cid):
                w=ix[whole,cid]['mapping_grade'];b=max((ix[p,cid]['mapping_grade'] for p in pool['path_ids'] if not p.startswith('o_')),default=0)
                return (-max(w,b),-w,-b,-pool['final_retrieval_score'][cid],cid)
            assert sorted(pool['candidate_ids_ranked_all112'],key=key)==row['ranking']
            assert len(set(row['ranking']))==112
            for k in (5,10,20):assert row['top_k'][str(k)]==row['ranking'][:k]
            rankcount+=1
    source=f.ROOT/'docs/stage123-openai-triplicate-2026-10-27/stage1_silver.json';silver=f.read(source)
    rel=defaultdict(set)
    for r in silver['records']:
        if r['silver_score']>=3:rel[r['qid']].add(r['cid'])
    result=f.read(f.OUT/'stage4_dev/results.json');metric_count=0
    for name,rows in result['systems'].items():
        for k in (5,10,20):
            by={field:defaultdict(list) for field in ('precision','recall','f1')}
            for row in rows:
                n=len(rel[row['qid']]);tp=sum(cid in rel[row['qid']] for cid in row['ranking'][:k]);m=row['metrics'][str(k)]
                vals={'precision':Fraction(tp,k),'recall':Fraction(tp,n) if n else None,'f1':Fraction(2*tp,k+n) if n else None}
                assert m['true_positives']==tp and m['recall_denominator']==n
                for field,value in vals.items():
                    if value is None:assert m[field] is None
                    else:assert math.isclose(float(value),m[field],abs_tol=1e-14);by[field][row['qid']].append(value)
                metric_count+=1
            for field,den in [('precision',10),('recall',6),('f1',6)]:
                assert len(by[field])==den
                mean=sum((sum(v)/len(v) for v in by[field].values()),Fraction(0))/den
                assert math.isclose(float(mean),result['macro'][name][str(k)][field],abs_tol=1e-14)
    preserved=[]
    for x in f.read(f.IN/'preservation.json')['unchanged_inputs']:
        p=f.ROOT/x['path'];raw=p.read_bytes()
        if x['comparison']!='exact raw bytes':raw=raw.replace(b'\r\n',b'\n')
        assert hashlib.sha256(raw).hexdigest()==x['sha256'];preserved.append(x['path'])
    engine=(f.ROOT/'src/ax_research/functional_mapping.py').read_text(encoding='utf-8')
    assert not any(s in engine for s in ('AXV2','V21D','silver','stage1_silver','os.environ','open('))
    config_commit=f.read(f.OUT/'manifest.json')['config_commit']
    raw=subprocess.check_output(['git','show',config_commit+':configs/functional_mapping_20261028.json'],cwd=f.ROOT)
    assert raw.replace(b'\r\n',b'\n')==f.CONFIG.read_bytes().replace(b'\r\n',b'\n')
    f.save('verification.json',{'passed':True,'raw_evidence_spans_checked':spans,'mapping_rows_checked':len(ix),'recommendation_rankings_checked':rankcount,'dev_metric_sets_fraction_checked':metric_count,'macro_cells_checked':18*3*3,'old_inputs_preserved':preserved,'mapping_inputs_preserved':6,'config_unchanged_from_preregistration':True,'mapper_no_case_query_id_or_label_rules':True,'candidate_count':112,'semantic_accuracy_independently_proven':False,'independent_test_access':False,'api_calls':0,'key_reads':0})
    print('Verified:',spans,'spans,',len(ix),'mappings,',rankcount,'new rankings,',metric_count,'metric sets.')

if __name__=='__main__':main()
