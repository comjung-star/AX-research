"""Dev-only experiment using the existing frozen C1 multiview scorer."""
import argparse
from collections import defaultdict
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from ax_research.heldout import jsonl, read, sha, write
from ax_research.semantic_mapping import combined_score
from scripts import validation123_api as api
from scripts import validation123_multiview as multiview
from scripts.heldout_run import freeze

ROOT = api.ROOT
OUT = ROOT / 'docs/fixed-three-views-2026-11-07'
DEV = api.OLD
PRIOR = api.OUT
QUESTIONS = DEV / 'input/questions.jsonl'
LABELS = PRIOR / 'stage1/qrels_v2.json'
MODEL = ROOT.parent / 'AX-prototype/.local/models/bge-m3'
SLOTS = ('BUSINESS', 'OPERATIONS', 'TECHNICAL')
old_body = api.body
old_validate = api.validate
DYNAMIC = api.view_system().replace('Return1 to6', 'Return exactly 3')
FIXED = """Using only the original business problem, return exactly three
perspective slots in this order: BUSINESS, OPERATIONS, TECHNICAL.
BUSINESS: actual worker, problem, business purpose and requested work.
OPERATIONS: explicit workflow, handoff, monitoring, incidents or maintenance.
TECHNICAL: explicit input data, action, object and output. Name only systems
or technologies explicitly stated in the source. Do not propose solutions.
Preserve actors, functions, inputs, outputs, temporal scope and exclusions
where relevant to the slot. Do not invent a function, technology or effect.
For supported slots use status PRESENT, a concise Korean title and description,
keywords and a short exact contiguous source_quote. Do not prepend category
labels to titles. For a slot with no relevant source information use status
MISSING and empty title, description, source_quote and keywords. Keep the
original distinction between requested work and excluded work. JSON only."""


def request(kind, query_id, repeat=1):
    body = old_body('views', query_id, repeat)
    if kind == 'dynamic':
        body['instructions'] = DYNAMIC
        body['input'] = body['input'].replace('generate1to6', 'generate exactly 3')
    else:
        body['instructions'] = FIXED
        body['input'] = body['input'].replace(
            '{id,title,description,keywords:[words],source_quote}',
            '{id,status,title,description,keywords:[words],source_quote}'
        ).replace('generate1to6', 'return exactly 3 fixed slots')
    return body


def validate(kind, query_id, data):
    assert set(data) == {'perspectives'}
    views = data['perspectives']
    assert isinstance(views, list) and len(views) == 3
    if kind == 'dynamic':
        old_validate('views', query_id, data)
        return
    assert tuple(view['id'] for view in views) == SLOTS
    present = []
    for view in views:
        assert set(view) == {'id', 'status', 'title', 'description', 'keywords', 'source_quote'}
        if view['status'] == 'MISSING':
            assert all(view[field] == '' for field in ('title', 'description', 'source_quote'))
            assert view['keywords'] == []
        else:
            assert view['status'] == 'PRESENT'
            present.append({k: v for k, v in view.items() if k != 'status'})
    assert present
    old_validate('views', query_id, {'perspectives': present})


def prepare():
    protected = [QUESTIONS, LABELS, DEV / 'predictions/rankings.json',
                 DEV / 'predictions/evidence.json', DEV / 'predictions/C1_details.json',
                 ROOT / 'configs/action_aggregation_20261102.json',
                 ROOT / 'src/ax_research/action_aggregation.py',
                 ROOT / 'src/ax_research/new_validation.py',
                 Path(multiview.__file__), Path(api.__file__), Path(__file__)]
    write(OUT / 'preregistration.json', {
        'base': 'c7e3cfa0e6b9a0b71e8d23fac2b361f64477a64a',
        'dev_reference': 'a4ca91555733e0d954df87cd8b2d46597cbe3a7b',
        'files': {p.relative_to(ROOT).as_posix(): sha(p) for p in protected},
        'environment': freeze(MODEL), 'calls_planned': 60, 'api_cap_usd': 2,
        'prompts': {'dynamic': DYNAMIC, 'fixed': FIXED},
        'request_template': {kind: request(kind, 'NV20261102_01') for kind in ('dynamic', 'fixed')},
        'inference': 'Reuse existing scorer, with internal repeat IDs 1-3 dynamic and 4-6 fixed',
        'test_scope': 'Dev questions only',
    })


def ledger():
    api.OUT = OUT
    records = []
    cumulative = Decimal(0)
    reserved = Decimal(0)
    for path in sorted((OUT / 'api/attempts').glob('*.json'), key=lambda p: p.stat().st_mtime_ns):
        row = read(path)
        usage = row.get('usage', {})
        writes = usage.get('input_tokens_details', {}).get('cache_write_tokens', 0)
        cost = Decimal(row.get('standard_usage_usd', '0')) + Decimal(writes) * Decimal('.025') / 1_000_000
        cumulative += cost
        reserved += Decimal(row.get('conservative_usage_usd', row['reserved_usd']))
        records.append({**row, 'estimated_usd': str(cost), 'cumulative_usd': str(cumulative),
                        'cumulative_upper_usd': str(reserved),
                        'valid': (OUT / 'api/results' / (row['id'] + '.json')).exists()})
    write(OUT / 'api_ledger.json', {'calls': records, 'estimated_usd': str(cumulative),
                                   'conservative_usd': str(reserved), 'budget_usd': 2})


def generate():
    plan = read(OUT / 'preregistration.json')
    for name, digest in plan['files'].items():
        assert sha(ROOT / name) == digest, name
    api.OUT = OUT
    api.body = request
    api.validate = validate
    try:
        for repeat in (1, 2, 3):
            for query in jsonl(QUESTIONS):
                for kind in ('dynamic', 'fixed'):
                    try:
                        api.call(kind, query['query_id'], repeat)
                    except RuntimeError as error:
                        if str(error) != 'RECEIVED_BUT_INVALID_NO_AUTOMATIC_RETRY':
                            raise
                        api.call(kind, query['query_id'], repeat, 'format_retry')
    finally:
        ledger()


def load_paths():
    paths, sources, slots = [], {}, []
    for kind, offset in (('dynamic', 0), ('fixed', 3)):
        for repeat in (1, 2, 3):
            for query in jsonl(QUESTIONS):
                query_id = query['query_id']
                name = f'{kind}_{query_id}_r{repeat}'
                source = OUT / 'api/results' / (name + '.json')
                if not source.exists():
                    source = source.with_name(name + '_format_retry.json')
                response = read(source)
                validate(kind, query_id, response['data'])
                sources[source.relative_to(ROOT).as_posix()] = sha(source)
                for i, view in enumerate(response['data']['perspectives'], 1):
                    path_id = f'{kind}_{query_id}_r{repeat}_{i}'
                    slots.append({'kind': kind, 'query_id': query_id, 'repeat': repeat,
                                  'path_id': path_id, **view})
                    if view.get('status') != 'MISSING':
                        paths.append({'query_id': path_id, 'text': view['title'] + '\n' + view['description'],
                                      'parent_query_id': query_id, 'repeat': repeat + offset,
                                      'perspective': view})
    return paths, sources, slots


def fixed_only(paths, branch_scores, case_ids):
    values, ties = {}, {}
    for case_id in case_ids:
        rows = [branch_scores[path, case_id] for path in paths]
        values[case_id] = combined_score(max(row['C1_rule']['mapping_grade'] for row in rows),
                                         max(row['semantic']['score'] for row in rows))
        ties[case_id] = multiview.mean_tie([Fraction(row['hybrid_exact']) for row in rows])
    ranking = sorted(case_ids, key=lambda cid: (-values[cid], -ties[cid], cid))
    return {'ranking': ranking, 'scores': values, **{f'top{k}': ranking[:k] for k in (5, 10, 20)}}


def infer(scratch):
    paths, sources, slots = load_paths()
    write(OUT / 'slots.json', {'records': slots})
    multiview.load_views = lambda: (paths, sources)
    dest = OUT / 'inference'
    multiview.infer(scratch.resolve(), MODEL.resolve(), dest)
    pred = read(dest / 'rankings.json')
    # The reused adapter labels repeats 1–3 by default. The actual rows contain
    # the internal IDs 1–6, translated here into three repeats per condition.
    grouped = defaultdict(list)
    for path in paths:
        if path['repeat'] > 3:
            grouped[path['parent_query_id'], path['repeat'] - 3].append(path['query_id'])
    branch_scores = {(row['path_id'], row['case_id']): row for row in jsonl(dest / 'branch_scores.jsonl')}
    systems = {'A': pred['systems']['E3'], 'B': [], 'C': [], 'D': []}
    for row in pred['systems']['E4']:
        if row['repeat'] <= 3:
            systems['B'].append(row)
        else:
            systems['C'].append({**row, 'repeat': row['repeat'] - 3})
    for (query_id, repeat), path_ids in grouped.items():
        systems['D'].append({'query_id': query_id, 'repeat': repeat,
                             **fixed_only(path_ids, branch_scores, pred['case_ids'])})
    write(OUT / 'predictions.json', {'query_ids': pred['query_ids'], 'case_ids': pred['case_ids'],
                                    'systems': systems})
    write(OUT / 'prediction_seal.json', {'predictions_sha256': sha(OUT / 'predictions.json'),
                                          'inference_seal_sha256': sha(dest / 'complete.json'),
                                          'slots_sha256': sha(OUT / 'slots.json')})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['prepare', 'generate', 'infer'])
    parser.add_argument('--scratch', type=Path)
    args = parser.parse_args()
    {'prepare': prepare, 'generate': generate, 'infer': lambda: infer(args.scratch)}[args.stage]()
