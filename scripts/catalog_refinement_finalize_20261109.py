"""Merge format-corrected blind grades, replay all saved decisions; no new API calls."""
import argparse
import json

from scripts import catalog_refinement_complete_20261109 as complete
from scripts import catalog_refinement_20261109 as run
from scripts.task_alignment_20261109 import sha


def merge():
    complete.guarded();assert (run.OUT/'judge-final-run.json').exists() and (run.OUT/'judge-schema-run.json').exists()
    previous=run.load('fresh-labels.json');run.save(run.OUT/'fresh-labels-before-schema.json',previous)
    labels=previous['labels'];failed=dict(previous['failures']);ids=sorted(run.inputs()[2]['cases']);reg=run.inputs()[3]
    corrected={}
    for q in run.load('fresh-questions.json'):
        source='calls/judge_schema_openai_'+q+'-data.json'
        try:
            rows=run.load(source)['rows'];order=run.judge_order(q,ids)
            assert len(rows)==17 and {r['position'] for r in rows}==set(range(17))
            g={}
            for r in rows:
                c=order[r['position']];assert r['grade'] in (0,1,2,3)
                if r['grade']>=2:assert r['task_quote'] and r['task_quote'] in reg[c]['task']
                g[c]=r['grade']
            assert q not in labels['openai'],'No valid label may be regenerated'
            labels['openai'][q]=g;failed.pop('openai_'+q,None);corrected[q]=source
        except Exception as e:failed['openai_'+q]=type(e).__name__
    updated={'labels':labels,'failures':failed,'human_gold':False,'rankings_sent':False,
      'actual_providers':{'openai':'gpt-5.4/medium4096 strict schema','gemini':'gemini-3-flash-preview/high6144'},
      'prior_rejected_request_failures_preserved':'fresh-labels-before-schema.json','corrected_label_sources':corrected}
    (run.OUT/'fresh-labels.json').write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('FINAL_BLIND_LABELS',{p:len(g) for p,g in labels.items()},'RETAINED_FAILURES',failed,flush=True)


def verify():
    complete.guarded();original=run.load
    sources=original('fit-recovery-summary.json')['source_by_query'];grades=original('fresh-labels.json')['corrected_label_sources']
    def routed(name):
        if name.startswith('calls/fit_') and name.endswith('-data.json'):
            q=name[len('calls/fit_'):-len('-data.json')]
            if q in sources:name=sources[q]
        if name.startswith('calls/judge_openai_'):
            for suffix in ('-data.json','-response.json'):
                if name.endswith(suffix):
                    q=name[len('calls/judge_openai_'):-len(suffix)]
                    if q in grades:name='calls/judge_schema_openai_'+q+suffix
        return original(name)
    run.load=routed;run.verify()
    report=original('verification.json')
    report.update({'method_changed_after_fresh_questions':True,'API_settings_changed_after_fresh_questions':True,
      'ranking_policy_or_fit_threshold_changed_after_evaluation':False,'clean_single_model_preregistered_test':False,
      'technical_failure_fit_questions':list(original('fit-recovery-summary.json')['still_failed']),
      'technical_failure_fresh_grade_requests':original('fresh-labels.json')['failures'],
      'actual_fresh_labels_per_provider':{p:len(v) for p,v in original('fresh-labels.json')['labels'].items()},
      'API_corrected_judge_format':'strict schema instead of rejected json_object; no valid grade replaced',
      'final_verifier_sha256':sha(__file__)})
    (run.OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['merge','evaluate','verify'])
    p=parser.parse_args().phase
    if p=='merge':merge()
    elif p=='verify':verify()
    else:complete.guarded();run.evaluate()
