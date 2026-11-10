"""Claude-only frozen symmetric-difference audit; one delivery per question."""
import argparse
import json
import urllib.request
from scripts import independent_cross_validation_20261110 as core
from scripts import continue_cross_validation_20261110 as transport
from ax_research.independent_cross_validation import summarize, agreement

ORIGINAL = core.OUT
OUT = core.ROOT / 'docs/claude-difference-20261110'


def prepare():
    core.verify_frozen()
    assert not (OUT / 'protocol.json').exists()
    recommendations = core.read(ORIGINAL / 'recommendations.json')
    counts = {'A': 0, 'B': 0, 'shared': 0, 'A_only': 0, 'B_only': 0}
    for question, row in recommendations.items():
        left, right = set(row['A']), set(row['B'])
        for name, value in [('A', len(left)), ('B', len(right)), ('shared', len(left & right)), ('A_only', len(left-right)), ('B_only', len(right-left))]:
            counts[name] += value
        payload = core.read(ORIGINAL / 'blind-inputs' / (question + '.json'))
        payload['cases'] = [case for case in payload['cases'] if case['case_id'] in left ^ right]
        core.save(OUT / 'blind-inputs' / (question + '.json'), payload)
    assert counts == {'A':254, 'B':254, 'shared':178, 'A_only':76, 'B_only':76}
    previous = [core.read(path) for path in core.receipt_paths()]
    assert all('raw' not in receipt for receipt in previous if receipt['provider'] == 'anthropic')
    core.save(OUT / 'protocol.json', {'date':'2026-11-10 Asia/Seoul', 'base_commit':'d5fe089ce27abd4f034e3769de690cbe8810b6b2', 'counts':counts,
        'rubric':core.SYSTEM, 'model':core.MODELS['anthropic'], 'schema':core.SCHEMA,
        'previous_reserved_usd':sum(receipt['reserved_usd'] for receipt in previous),
        'budget_cap_usd':15, 'retry_policy':'No resend, including invalid citation or unknown delivery; keep partial judgments and report bounds.',
        'scope':'152 pairs only; original per-pair facts, rubric, model and output cap unchanged. No Gemini calls or labels used.',
        'credit_check':'Model discovery cannot prove balance. First requested evaluation doubles as credit validity check; preserve successful response.',
        'prices':[2,10], 'pricing_source':'https://platform.claude.com/docs/en/models/sonnet-5-5/overview',
        'hashes':{str(path.relative_to(OUT)):core.sha(path) for path in (OUT/'blind-inputs').glob('*.json')}})


def execute():
    core.verify_frozen()
    protocol = core.read(OUT/'protocol.json')
    for name, digest in protocol['hashes'].items():
        assert core.sha(OUT/name) == digest
    core.OUT = OUT
    transport.OUT = OUT
    core.BUDGET = 15 - protocol['previous_reserved_usd']
    with urllib.request.urlopen(urllib.request.Request('https://api.anthropic.com/v1/models/'+core.MODELS['anthropic'], headers=core.headers('anthropic')), timeout=40) as response:
        core.save(OUT/'model-access.json', json.loads(response.read()))
    for path in sorted((OUT/'blind-inputs').glob('*.json')):
        payload = core.read(path)
        if not payload['cases']:
            continue
        request_body = core.body('anthropic', payload)
        reserve = ((len(json.dumps(request_body,ensure_ascii=False).encode())+8192)*2+core.CAP*10)/1e6
        receipt = transport.request('anthropic', path.stem, payload, path.stem, reserve)
        if receipt['status'] not in ('VALID','INVALID_OUTPUT'):
            break


def report():
    core.OUT = ORIGINAL
    core.verify_frozen()
    recommendations = core.read(ORIGINAL/'recommendations.json')
    grades, raw_grades, failures, provenance = {}, {}, [], []
    receipts = []
    for path in sorted((OUT/'api').glob('*.response.json')):
        receipt = core.read(path)
        receipts.append(receipt)
        payload = core.read(OUT/'blind-inputs'/(receipt['question_id']+'.json'))
        request = core.read(path.with_name(path.name.replace('.response.','.request.')))
        assert request['body'] == core.body('anthropic',payload)
        good, bad = transport.accepted(receipt,payload)
        failures.extend({'question':receipt['question_id'], **row} for row in bad)
        for case, row in good.items():
            key = (receipt['question_id'],case)
            assert key not in grades
            grades[key] = row['grade']
            provenance.append({'question_id':key[0], **row, 'receipt':path.name})
        if 'raw' in receipt:
            for row in core.parse('anthropic',receipt['raw'])['judgments']:
                raw_grades[receipt['question_id'],row['case_id']] = row['grade']
    expected = {(question,case) for question,row in recommendations.items() for case in set(row['A'])^set(row['B'])}
    assert set(grades) <= expected and len(expected)==152
    old = core.read(core.OLD/'labels.json')
    reference = {(question,case):str(old[question]['cases'][case]['grade']) for question,case in expected}
    def stats(values):
        result = summarize(recommendations,{question:{case:grade for (qid,case),grade in values.items() if qid==question} for question in recommendations})
        result.pop('macro')
        for row in result['per_question'].values():
            row.pop('A'); row.pop('B')
        return result
    sensitivity = {str(threshold):stats({key:grade if grade=='ABSTAIN' else ('3' if int(grade)>=threshold else '0') for key,grade in grades.items()}) for threshold in (1,2,3)}
    disagreements = [{'question_id':key[0], 'case_id':key[1], 'claude':grades[key], 'openai':reference[key], 'claude_evidence':next(row for row in provenance if (row['question_id'],row['case_id'])==key), 'openai_evidence':old[key[0]]['cases'][key[1]]} for key in sorted(grades) if grades[key]!=reference[key]]
    result = {'coverage':{'expected':152,'accepted':len(grades),'raw':len(raw_grades),'abstain':sum(value=='ABSTAIN' for value in grades.values()),'invalid_citations':len(failures),'never_delivered':len(expected-set(raw_grades))},
        'claude':stats(grades),'openai':stats(reference),'agreement':agreement(reference,grades),'sensitivity':sensitivity,
        'cost_usd':sum(receipt.get('usage',{}).get('estimated_cost_usd',0) for receipt in receipts),'reserved_usd':sum(receipt['reserved_usd'] for receipt in receipts),
        'prior_reserved_usd':core.read(OUT/'protocol.json')['previous_reserved_usd'], 'api_calls':len(receipts),
        'statuses':[{'question':receipt['question_id'],'status':receipt['status'],'error':receipt.get('error')} for receipt in receipts], 'failures':failures}
    core.save(OUT/'analysis.json',result)
    core.save(OUT/'judgments.json',provenance)
    core.save(OUT/'disagreements.json',disagreements)
    core.save(OUT/'hashes.json',{str(path.relative_to(OUT)):core.sha(path) for path in OUT.rglob('*') if path.is_file() and path.name!='hashes.json'})
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','execute','report'])
    globals()[parser.parse_args().action]()
