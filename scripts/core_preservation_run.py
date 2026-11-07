"""Frozen new-Dev core-preservation experiment with bounded paid calls."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import socket

from ax_research.heldout import jsonl, read, sha, write
from ax_research.functional_mapping import compare, extract
from ax_research.action_aggregation import purpose_filter
from ax_research.semantic_mapping import combined_score
from scripts import validation123_api as api
from scripts import validation123_multiview as multiview
from scripts.heldout_run import freeze, predict
from scripts import core_preservation_prompts as prompts

ROOT = api.ROOT
OUT = ROOT/'docs/core-preserved-three-views-2026-11-07'
MODEL = ROOT.parent/'AX-prototype/.local/models/bge-m3'
QUESTIONS = OUT/'questions.jsonl'
SLOTS = ('BUSINESS', 'OPERATIONS', 'TECHNICAL')
REVIEW_VALIDATOR = api.validate
ACTIVE_JUDGE_PAYLOAD = None


def body(kind, query_id, repeat=1):
    question = next(q['text'] for q in jsonl(QUESTIONS) if q['query_id'] == query_id)
    payload = {'original_business_problem': question}
    instructions = {'B': prompts.DYNAMIC, 'C': prompts.C_PROMPT,
                    'X': prompts.EXTRACTION, 'E': prompts.E_PROMPT,
                    'judge': prompts.JUDGE}
    if kind in ('B', 'C', 'E'):
        payload['format'] = '{perspectives:[{id,title,description,keywords:[words],source_quote}]} exactly3'
        if kind != 'B':
            payload['format'] += '; fixed IDs BUSINESS,OPERATIONS,TECHNICAL; include status PRESENT or MISSING'
    if kind == 'E':
        payload['core'] = read(OUT/'api/results'/f'X_{query_id}_r{repeat}.json')['data']['core']
    if kind == 'judge':
        payload = ACTIVE_JUDGE_PAYLOAD
    return {'model': 'gpt-6-luna', 'instructions': instructions[kind],
            'input': json.dumps(payload, ensure_ascii=False)+'\nReturn JSON.',
            'text': {'format': {'type': 'json_object'}},
            'reasoning': {'effort': 'none'}, 'max_output_tokens': 2200 if kind == 'judge' else 1600,
            'service_tier': 'default', 'store': False}


def validate(kind, query_id, data):
    if kind == 'judge':
        REVIEW_VALIDATOR('review', query_id, data)
        return
    if kind == 'X':
        assert set(data) == {'core'} and set(data['core']) == set(prompts.FIELDS)
        for field in data['core'].values():
            assert set(field) == {'text', 'evidence'}
            assert field['text'] is None or isinstance(field['text'], str)
            assert isinstance(field['evidence'], list)
            assert all(isinstance(e, str) and e.strip() for e in field['evidence'])
            if field['text'] is None:
                assert not field['evidence']
        return
    assert set(data) == {'perspectives'} and len(data['perspectives']) == 3
    assert len({p['id'] for p in data['perspectives']}) == 3
    if kind != 'B':
        assert tuple(p['id'] for p in data['perspectives']) == SLOTS
    for view in data['perspectives']:
        required = {'id', 'title', 'description', 'keywords', 'source_quote'}
        assert set(view) == (required if kind == 'B' else required | {'status'})
        assert all(isinstance(view[k], str) for k in ('id', 'title', 'description', 'source_quote'))
        assert isinstance(view['keywords'], list) and all(isinstance(k, str) for k in view['keywords'])
        if view.get('status') == 'MISSING':
            assert view['title'] == view['description'] == view['source_quote'] == ''
            assert not view['keywords']
        else:
            assert kind == 'B' or view['status'] == 'PRESENT'
            assert view['title'].strip() and view['description'].strip()


def configure():
    api.OUT = OUT
    api.body = body
    api.validate = validate
    api.request_for_review = lambda _: ACTIVE_JUDGE_PAYLOAD


def prepare():
    configure()
    qs = jsonl(QUESTIONS)
    assert len(qs) == 8 and len({q['query_id'] for q in qs}) == 8
    assert all(q['split'] == 'NEW_DEV' for q in qs)
    original_cases = ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json'
    protected = [original_cases, QUESTIONS, Path(prompts.__file__), Path(multiview.__file__),
                 ROOT/'src/ax_research/action_aggregation.py',
                 ROOT/'configs/action_aggregation_20261102.json',
                 ROOT/'src/ax_research/new_validation.py']
    write(OUT/'preregistration.json', {
        'base': 'f4b65d56dea1521216a4f7ce9c6c8a9eb6bd0777',
        'prompt_commit_before_question_authoring': 'b251b7e7',
        'prompt_sha256': sha(Path(prompts.__file__)),
        'protected_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in protected},
        'environment': freeze(MODEL),
        'data_origin': '8 new corpus-aware Dev questions written by same assistant after prompts frozen; no prior Test payload opened',
        'counts': {'questions': 8, 'cases': 112, 'label_pairs': 896,
                   'B_calls': 24, 'C_calls': 24, 'X_calls': 24, 'E_calls': 24, 'judge_calls': 56},
        'budget_usd': 2, 'regeneration_allowed': False,
        'generation': {'model': 'gpt-6-luna', 'reasoning': 'none',
                       'max_output_tokens': 1600, 'repeat_count': 3, 'view_count': 3},
        'labeling': 'question-only grouped batches16, all112 cases, no system/rank/previous score;0to3>=2;ABSTAIN null;no human Gold',
        'evaluation': 'common fully judged query cohort per metric acrossABCE;zero-positive R/F1undefined;partialTopK precision only in separate per-query results',
        'aggregation': 'unchanged original+maxbranch rule and (whole+maxbranch)/2 semantics with frozen50:50; original Hybrid vs dynamic mean path Hybrid tie',
        'quality': 'exact evidence plus separate semantic source review; invalid quotes retained as quality findings, not repaired or regenerated',
        'uncertainty': 'population SD of3runs; paired question bootstrap95% 10000resamples seed20261107; leave-one-query-out',
        'new_independent_test': 'not executed',
    })
    write(OUT/'final_status.json', {'status': 'RUNNING', 'new_Test_executed': False})


def ledger():
    configure()
    total = Decimal(0)
    upper = Decimal(0)
    rows = []
    for p in sorted((OUT/'api/attempts').glob('*.json'), key=lambda p: p.stat().st_mtime_ns):
        row = read(p)
        usage = row.get('usage', {})
        writes = usage.get('input_tokens_details', {}).get('cache_write_tokens', 0)
        cost = Decimal(row.get('standard_usage_usd', '0'))+Decimal(writes)*Decimal('.025')/1_000_000
        total += cost
        upper += Decimal(row.get('conservative_usage_usd', row['reserved_usd']))
        rows.append({**row, 'estimated_usd': str(cost), 'cumulative_usd': str(total),
                     'cumulative_upper_usd': str(upper),
                     'structure_valid': (OUT/'api/results'/(row['id']+'.json')).exists()})
    (OUT/'api_ledger.json').write_text(json.dumps({
        'calls': rows, 'estimated_usd': str(total), 'conservative_usd': str(upper),
        'budget_usd': 2, 'no_regeneration': True,
    }, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


def generate():
    configure()
    try:
        for repeat in (1, 2, 3):
            for question in jsonl(QUESTIONS):
                for kind in ('B', 'C', 'X', 'E'):
                    api.call(kind, question['query_id'], repeat)
    finally:
        ledger()


def blocked(*args, **kwargs):
    raise RuntimeError('Network blocked in offline inference')


def inference(scratch):
    plan = read(OUT/'preregistration.json')
    for name, digest in plan['protected_sha256'].items():
        assert sha(ROOT/name) == digest, name
    accesses = []
    def audit(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = str(args[0]).replace('\\', '/').lower()
            if any(x in path for x in (
                    '.ax-heldout', 'work-b', 'heldout-final-resume', '/qrels', '/labels')):
                raise RuntimeError('Forbidden Test or relevance input during inference')
            if path.endswith(('.json', '.jsonl', '.npz')):
                accesses.append(str(args[0]))
    import sys
    sys.addaudithook(audit)
    socket.socket.connect = blocked
    socket.create_connection = blocked
    scratch.mkdir(exist_ok=False)
    original_scratch = scratch/'original'
    original_scratch.mkdir()
    qs = jsonl(QUESTIONS)
    original = predict(qs, MODEL, original_scratch)
    scaffold = OUT/'original'
    (scaffold/'predictions').mkdir(parents=True, exist_ok=False)
    details = read(original_scratch/'evidence.json')
    by = {(r['query_id'], r['case_id']): r for r in details['records']}
    rules = read(ROOT/'configs/functional_mapping_20261028.json')
    config = read(ROOT/'configs/action_aggregation_20261102.json')
    cp = read(ROOT/'docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json')
    filtered = {c: {role: purpose_filter(p, config) for role, p in parts.items()} for c, parts in cp.items()}
    systems = {'C0': original['systems']['C'], 'C1': [], 'C1_NO_EMBEDDING': []}
    c1_details = []
    for q in qs:
        qid = q['query_id']
        profile = purpose_filter(extract(q['text'], rules), config)
        scores = {}
        neutral = {}
        for cid in original['case_ids']:
            mapping = compare(profile, filtered[cid])
            semantics = by[qid, cid]['semantic']['score']
            scores[cid] = combined_score(mapping['mapping_grade'], semantics)
            neutral[cid] = mapping['mapping_grade']/8+.25
            c1_details.append({'query_id': qid, 'case_id': cid, 'new_rule': mapping})
        for name, values in (('C1', scores), ('C1_NO_EMBEDDING', neutral)):
            ranking = sorted(values, key=lambda c: (-values[c], -by[qid, c]['retrieval_tie'], c))
            systems[name].append({'query_id': qid, 'ranking': ranking, 'scores': values,
                                  **{f'top{k}': ranking[:k] for k in (5, 10, 20)}})
    write(scaffold/'predictions/rankings.json', {**original, 'systems': systems})
    write(scaffold/'predictions/evidence.json', details)
    write(scaffold/'predictions/C1_details.json', {'records': c1_details})
    paths, slots, sources = [], [], {}
    for condition, offset in (('B', 0), ('C', 3), ('E', 6)):
        for repeat in (1, 2, 3):
            for q in qs:
                stem = f"{condition}_{q['query_id']}_r{repeat}"
                p = OUT/'api/results'/(stem+'.json')
                result = read(p)
                validate(condition, q['query_id'], result['data'])
                sources[p.relative_to(ROOT).as_posix()] = sha(p)
                for i, view in enumerate(result['data']['perspectives'], 1):
                    path_id = f'{stem}_{i}'
                    slots.append({'condition': condition, 'repeat': repeat,
                                  'query_id': q['query_id'], 'path_id': path_id, **view})
                    if view.get('status') != 'MISSING':
                        paths.append({'query_id': path_id, 'text': view['title']+'\n'+view['description'],
                                      'parent_query_id': q['query_id'], 'repeat': repeat+offset,
                                      'perspective': view})
    write(OUT/'slots.json', {'records': slots})
    multiview.OLD = scaffold
    multiview.load_views = lambda: (paths, sources)
    multiview.infer(scratch/'branches', MODEL, OUT/'inference')
    generated = read(OUT/'inference/rankings.json')
    comparison = {'A': systems['C1'], 'B': [], 'C': [], 'E': []}
    for row in generated['systems']['E4']:
        condition = ('B', 'C', 'E')[(row['repeat']-1)//3]
        comparison[condition].append({**row, 'repeat': (row['repeat']-1)%3+1})
    write(OUT/'predictions.json', {'case_ids': original['case_ids'],
                                   'query_ids': original['query_ids'], 'systems': comparison})
    write(OUT/'prediction_seal.json', {
        'files': {name: sha(OUT/name) for name in ('predictions.json', 'slots.json')},
        'inference_seal_sha256': sha(OUT/'inference/complete.json'),
        'input_accesses': accesses, 'relevance_labels_read': False,
        'old_Test_read': False, 'all_ABCE_newly_executed': True,
    })


def judge():
    global ACTIVE_JUDGE_PAYLOAD
    configure()
    seal = read(OUT/'prediction_seal.json')
    for name, digest in seal['files'].items():
        assert sha(OUT/name) == digest
    cases = read(ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    results = []
    try:
        for q in jsonl(QUESTIONS):
            ids = sorted(cases)
            for start in range(0, len(ids), 16):
                ACTIVE_JUDGE_PAYLOAD = {
                    'query_id': q['query_id'], 'business_problem': q['text'],
                    'cases': [{'case_id': c, 'Problem': cases[c]['problem'],
                               'Task': cases[c]['task'], 'Context': cases[c]['context']}
                              for c in ids[start:start+16]],
                }
                result = api.call('judge', q['query_id'], start//16+1)
                results.extend(result['data']['assessments'])
        write(OUT/'labels.json', {'records': [
            {'query_id': r['query_id'], 'case_id': r['case_id'], 'grade': r['grade'],
             'status': r['status'], 'label_source': 'AI-Silver', 'rationale': r['reason'],
             'task_quote': r['task_quote']}
            for r in results], 'human_verified': False})
    finally:
        ledger()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['prepare', 'generate', 'infer', 'judge', 'ledger'])
    parser.add_argument('--scratch', type=Path)
    args = parser.parse_args()
    {'prepare': prepare, 'generate': generate, 'infer': lambda: inference(args.scratch.resolve()),
     'judge': judge, 'ledger': ledger}[args.stage]()
