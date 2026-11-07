"""Blind source-only audit used solely for measurement, never regeneration."""
import json
import random

from ax_research.heldout import jsonl, read, sha, write
from scripts import core_preservation_run as run

RUBRIC = """
Assess generated perspectives against the original business problem only.
Candidate IDs hide generation method. Do not infer quality from length or
format. For each candidate, inspect the union of all three views and return
purpose, action, object, output, constraints and role_distinction, each0/1/2
(0=changed/absent or merged roles,1=partial,2=preserved or clearly differentiated).
For constraints, preserve permission, condition, negation and priority strength.
Distinguish looking up from changing records and present detection from future
prediction. role_distinction asks whether BUSINESS purpose, OPERATIONS flow/
conditions and TECHNICAL input/function/output are differentiated.
Also return unsupported_quotes, exact contiguous substrings of the candidate
title/description asserting something unsupported or contradicted by source,
and concise Korean reason. No expected answer, retrieval result or model name
is provided. Return JSON {assessments:[{id,purpose,action,object,output,
constraints,role_distinction,unsupported_quotes,reason}]} for all9 IDs.
This audit is a source judgment, not a human Gold or a generation instruction.
"""
FIELDS = ('purpose', 'action', 'object', 'output', 'constraints', 'role_distinction')
ACTIVE = None


def body(kind, query_id, repeat=1):
    return {'model': 'gpt-6-luna', 'instructions': RUBRIC,
            'input': json.dumps(ACTIVE, ensure_ascii=False)+'\nReturn JSON.',
            'text': {'format': {'type': 'json_object'}}, 'reasoning': {'effort': 'none'},
            'max_output_tokens': 3000, 'service_tier': 'default', 'store': False}


def validate(kind, query_id, data):
    assert set(data) == {'assessments'}
    expected = {c['id']: c for c in ACTIVE['candidates']}
    rows = data['assessments']
    assert len(rows) == len(expected) and {r['id'] for r in rows} == set(expected)
    for row in rows:
        assert set(row) == {'id', *FIELDS, 'unsupported_quotes', 'reason'}
        assert all(type(row[f]) is int and row[f] in (0, 1, 2) for f in FIELDS)
        text = '\n'.join(v['title']+'\n'+v['description'] for v in expected[row['id']]['views'])
        assert isinstance(row['unsupported_quotes'], list)
        assert all(isinstance(q, str) and q and q in text for q in row['unsupported_quotes'])
        assert isinstance(row['reason'], str) and row['reason'].strip()


def main():
    global ACTIVE
    assert (run.OUT/'prediction_seal.json').exists()
    slots = read(run.OUT/'slots.json')['records']
    results = []
    mapping = []
    run.api.OUT = run.OUT
    run.api.body = body
    run.api.validate = validate
    try:
        for index, q in enumerate(jsonl(run.QUESTIONS)):
            groups = [(c, r) for c in ('B', 'C', 'E') for r in (1, 2, 3)]
            random.Random(20261107+index).shuffle(groups)
            candidates = []
            for j, (condition, repeat) in enumerate(groups):
                identifier = f'G{j+1}'
                views = [{'id': s['id'], 'title': s['title'], 'description': s['description']}
                         for s in slots if (s['condition'], s['query_id'], s['repeat']) ==
                         (condition, q['query_id'], repeat)]
                assert len(views) == 3
                candidates.append({'id': identifier, 'views': views})
                mapping.append({'query_id': q['query_id'], 'id': identifier,
                                'condition': condition, 'repeat': repeat})
            ACTIVE = {'query_id': q['query_id'], 'original_business_problem': q['text'],
                      'candidates': candidates}
            result = run.api.call('quality', q['query_id'], 1)
            results.extend({'query_id': q['query_id'], **r} for r in result['data']['assessments'])
        write(run.OUT/'quality.json', {'assessments': results, 'mapping': mapping,
                                      'rubric_sha256': run.api.digest(RUBRIC),
                                      'same_model_separate_requests': True,
                                      'recommendation_metrics_hidden': True,
                                      'used_to_regenerate_or_select': False})
    finally:
        run.ledger()


if __name__ == '__main__':
    main()
