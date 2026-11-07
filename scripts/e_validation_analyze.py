"""Versioned labels, reviewer disagreement, and fixed-prediction sensitivity."""
import argparse
from collections import Counter, defaultdict
from statistics import mean
import json

from ax_research.heldout import read, jsonl, sha, write
from scripts import e_validation as run
from scripts import core_preservation_evaluate as metrics


def effective_identifier(provider, identifier):
    link=run.OUT/'repairs'/(provider+'_'+identifier+'.json')
    return read(link)['recovery_identifier'] if link.exists() else identifier


def received(provider, identifier):
    identifier=effective_identifier(provider,identifier)
    stem = provider+'_'+identifier
    path = run.OUT/'api'/(stem+'_response.json')
    if not path.exists():
        return None
    raw = read(path)
    if provider == 'openai':
        if raw.get('status') != 'completed':
            return None
        text = ''.join(c.get('text', '') for x in raw.get('output', [])
                       for c in x.get('content', []) if c.get('type') == 'output_text')
    else:
        if raw.get('stop_reason') != 'end_turn':
            return None
        text = ''.join(c.get('text', '') for c in raw.get('content', []) if c.get('type') == 'text')
    text = text.strip()
    if text.startswith('```') and text.endswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0]
    try:
        return json.loads(text)
    except ValueError:
        return None


def reviewers():
    if read(run.OUT/'provider_access.json')['claude_generation_available']:
        return [('openai', 'openai', ''), ('claude', 'claude', '')]
    return [('openai', 'openai', ''), ('openai_repeat2', 'openai', '_repeat2')]


def validate_relevance(row, payload):
    cases = {c['id']: c for c in payload['cases']}
    assert row['id'] in cases and row['query_id'] == payload['query_id']
    assert row['status'] in ('JUDGED', 'ABSTAIN')
    assert ((row['status'] == 'JUDGED' and type(row['grade']) is int and 0 <= row['grade'] <= 3)
            or (row['status'] == 'ABSTAIN' and row['grade'] is None))
    assert isinstance(row['reason'], str) and row['reason'].strip()
    quote = row['task_quote']
    assert isinstance(quote, str) and 1 <= len(quote) <= 140 and quote in cases[row['id']]['Task']
    for field in ('case_action', 'case_object', 'case_output', 'permission_scope'):
        assert row[field] is None or isinstance(row[field], str)


def collect_relevance(missing_only=False):
    result = []
    for missing in ((True,) if missing_only else (True, False)):
        prefix = 'missing' if missing else 'review'
        for group in run.batches(missing):
            payload = run.rel_payload(group)
            for reviewer, provider, suffix in reviewers():
                identifier = prefix+'_'+group[0]['id']+suffix
                data = received(provider, identifier)
                raw_rows = data.get('assessments', []) if isinstance(data, dict) else []
                counts = Counter(x.get('id', x.get('case_id')) for x in raw_rows if isinstance(x, dict))
                for record in group:
                    matches = [x for x in raw_rows if isinstance(x, dict) and
                               x.get('id', x.get('case_id')) == record['id']]
                    reason = None
                    row = None
                    try:
                        assert len(matches) == 1 and counts[record['id']] == 1
                        row = dict(matches[0])
                        if 'id' not in row:
                            row['id'] = row['case_id']
                        validate_relevance(row, payload)
                    except (AssertionError, KeyError, TypeError):
                        reason = 'MISSING_INVALID_OR_UNCERTAIN_RESPONSE'
                    result.append({**record, 'reviewer': reviewer, 'provider': provider,
                                   'request_id': provider+'_'+effective_identifier(provider,identifier),
                                   'valid': reason is None, 'invalid_reason': reason,
                                   'assessment': row, 'raw_assessment': matches[0] if len(matches)==1 else None})
    return result


def consensus(reviews):
    valid = [x['assessment'] for x in reviews if x['valid']]
    if len(valid) == 2 and all(x['status'] == 'JUDGED' for x in valid) and valid[0]['grade'] == valid[1]['grade']:
        return {'grade': valid[0]['grade'], 'status': 'JUDGED',
                'rationale': '두 별도 요청의 원문 근거·등급이 일치. '+valid[0]['reason'],
                'review_status': 'TWO_SOURCE_VALID_REVIEWS_AGREE'}
    return {'grade': None, 'status': 'ABSTAIN',
            'rationale': '별도 요청의 등급 불일치·보류 또는 유효한 근거 부족. 임의 확정하지 않음.',
            'review_status': 'UNRESOLVED_REVIEW_DIFFERENCE'}


def source_registry():
    cases = read(run.ROOT/'docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    wanted = {e for case in cases.values() for e in json.loads(case['evidence_ids'])}
    catalog = {e['evidence_id']: e for e in jsonl(run.ROOT/'data/v2_5/research/evidence_catalog.jsonl')
               if e['evidence_id'] in wanted}
    return {cid: {'structured_case': case, 'sources': [{k: catalog[e].get(k) for k in
                     ('evidence_id', 'source_url', 'evidence_locator', 'access_status', 'independent_fact_corroboration')}
                     for e in json.loads(case['evidence_ids']) if e in catalog]}
            for cid, case in cases.items()}


def label_versions(reviews, missing_only=False):
    originals = read(run.old.OUT/'labels.json')['records']
    grouped = defaultdict(list)
    for row in reviews:
        grouped[row['query_id'], row['case_id']].append(row)
    versions = {}
    changes = []
    for version in ('v1_missing_only',) if missing_only else (
            'v1_missing_only', 'v2_reviewed_strict', 'v2_openai_sensitivity', 'v2_second_reviewer_sensitivity'):
        rows = []
        for original in originals:
            key = original['query_id'], original['case_id']
            selected = key in grouped and (version != 'v1_missing_only' or original['status'] != 'JUDGED')
            row = {**original, 'inherited_from_original': not selected}
            if selected:
                opinions = grouped[key]
                if version.endswith('_sensitivity'):
                    target = 'openai' if version == 'v2_openai_sensitivity' else reviewers()[1][0]
                    chosen = next(x for x in opinions if x['reviewer'] == target)
                    a = chosen['assessment'] if chosen['valid'] else None
                    decision = {'grade': a['grade'] if a else None,
                                'status': a['status'] if a else 'ABSTAIN',
                                'rationale': a['reason'] if a else '응답 누락 또는 근거 검증 미통과.',
                                'review_status': 'SINGLE_REVIEWER_SENSITIVITY_ONLY'}
                else:
                    decision = consensus(opinions)
                row.update(decision)
                row['task_quote'] = next((x['assessment']['task_quote'] for x in opinions if x['valid']), '')
                row['review_request_ids'] = [x['request_id'] for x in opinions]
                if version == 'v2_reviewed_strict' or missing_only:
                    changes.append({'query_id': key[0], 'case_id': key[1],
                                    'old_grade': original['grade'], 'old_status': original['status'],
                                    'new_grade': row['grade'], 'new_status': row['status'],
                                    'changed': (original['grade'], original['status']) != (row['grade'], row['status']),
                                    'reason': row['rationale'], 'opinions': opinions})
            rows.append(row)
        versions[version] = rows
    return versions, changes


def stage1():
    reviews = collect_relevance(True)
    versions, changes = label_versions(reviews, True)
    rows = versions['v1_missing_only']
    former_missing = {(r['query_id'], r['case_id']) for r in read(run.old.OUT/'labels.json')['records']
                      if r['status'] != 'JUDGED'}
    subset = [r for r in rows if (r['query_id'], r['case_id']) in former_missing]
    write(run.OUT/'stage1_summary.json', {'original_missing': 29,
                                        'resolved': sum(x['status']=='JUDGED' for x in subset),
                                        'remaining_abstain': sum(x['status']=='ABSTAIN' for x in subset),
                                        'records': subset, 'changes': changes,
                                        'reviewer_counts': dict(Counter(x['reviewer'] for x in reviews)),
                                        'invalid_responses': sum(not x['valid'] for x in reviews),
                                        'human_verified': False})


def validate_quality(data, payload):
    assert data['id'] == payload['id']
    checks = data['checks']
    assert len(checks) == len(run.QUALITY_FIELDS)
    assert {c['field'] for c in checks} == set(run.QUALITY_FIELDS)
    for c in checks:
        assert c['score'] is None or (type(c['score']) is int and c['score'] in (0, 1, 2))
        assert isinstance(c['reason'], str) and c['reason'].strip()
    issue_checks = []
    candidate = '\n'.join(v['title']+'\n'+v['description'] for v in payload['views'])
    for issue in data['issues']:
        assert issue['type'] in ('OMISSION', 'CONTRADICTION', 'ADDITION')
        source, view = issue['source_quote'], issue['view_quote']
        valid = ((bool(source) and source in payload['original_business_problem']) or
                 (not source and issue['type']=='ADDITION'))
        valid = valid and ((not view and issue['type']=='OMISSION') or (bool(view) and view in candidate))
        issue_checks.append({'issue': issue, 'literal_evidence_valid': valid})
    assert isinstance(data['permission_interpretation'], str)
    return issue_checks


def quality_results():
    rows = []
    for record in read(run.OUT/'selection.json')['quality_mapping']:
        payload = run.quality_payload(record)
        for reviewer, provider, suffix in reviewers():
            data = received(provider, 'quality_'+record['id']+suffix)
            valid = False
            issues = []
            invalid_reason='INCOMPLETE_OR_UNREADABLE_RESPONSE'
            try:
                issues = validate_quality(data, payload)
                valid = all(x['literal_evidence_valid'] for x in issues)
                invalid_reason=None if valid else 'NONLITERAL_ISSUE_EVIDENCE'
            except (AssertionError, KeyError, TypeError):
                if data is not None:invalid_reason='SCHEMA_OR_ID_INVALID'
            rows.append({**record, 'reviewer': reviewer, 'valid': valid,
                         'request_id':provider+'_'+effective_identifier(provider,'quality_'+record['id']+suffix),
                         'invalid_reason':invalid_reason,
                         'data': data, 'issue_evidence_checks': issues})
    summary = []
    for reviewer, _, _ in reviewers():
        for condition in 'BCE':
            group = [r for r in rows if r['reviewer']==reviewer and r['condition']==condition]
            values = {}
            for field in run.QUALITY_FIELDS:
                scores = [c['score'] for r in group if r['valid'] for c in r['data']['checks']
                          if c['field']==field and c['score'] is not None]
                values[field] = {'mean': mean(scores) if scores else None, 'n': len(scores),
                                 'full_count': sum(x==2 for x in scores)}
            summary.append({'reviewer': reviewer, 'condition': condition,
                            'valid_triplets': sum(r['valid'] for r in group), 'fields': values})
    lookup = {(r['reviewer'],r['condition'],r['query_id'],r['repeat']):r for r in rows}
    pairs = []
    for field in run.QUALITY_FIELDS:
        for reviewer, _, _ in reviewers():
            diffs = []
            for q in jsonl(run.old.QUESTIONS):
                for rep in (1,2,3):
                    scores = []
                    for c in ('C','E'):
                        item = lookup[reviewer,c,q['query_id'],rep]
                        scores.append(next(x['score'] for x in item['data']['checks'] if x['field']==field)
                                      if item['valid'] else None)
                    if None not in scores:
                        diffs.append(scores[1]-scores[0])
            pairs.append({'reviewer': reviewer, 'field': field, 'matched_triplet_pairs': len(diffs),
                          'E_minus_C': mean(diffs) if diffs else None,
                          'improved': sum(x>0 for x in diffs), 'worse': sum(x<0 for x in diffs)})
    previous = read(run.old.OUT/'quality_summary.json')['assessments']
    comparison = []
    for row in rows:
        before = next(x for x in previous if (x['condition'],x['query_id'],x['repeat']) ==
                      (row['condition'],row['query_id'],row['repeat']))
        comparison.append({'query_id':row['query_id'],'condition':row['condition'],'repeat':row['repeat'],
                           'reviewer':row['reviewer'],'old':before,
                           'new':row['data'],'new_literal_evidence_valid':row['valid'],
                           'new_input_and_no_added_functions_not_directly_comparable_to_old_fields':True})
    agreement=[]
    first, second = (r[0] for r in reviewers())
    for field in run.QUALITY_FIELDS:
        values=[]
        for item in read(run.OUT/'selection.json')['quality_mapping']:
            scores=[]
            for reviewer in (first,second):
                row=lookup[reviewer,item['condition'],item['query_id'],item['repeat']]
                scores.append(next(c['score'] for c in row['data']['checks'] if c['field']==field)
                              if row['valid'] else None)
            if None not in scores:values.append(scores[0]==scores[1])
        agreement.append({'field':field,'n':len(values),'exact_agreement':mean(values) if values else None})
    previous_errors=[]
    for old_error in read(run.old.OUT/'quality_validation.json')['examples']:
        key=old_error['condition'],old_error['query_id'],old_error['repeat']
        previous_errors.append({'old_error':old_error,'new_reviews':[
            lookup[reviewer,*key] for reviewer,_,_ in reviewers()]})
    return {'records': rows, 'summary': summary, 'paired_C_E': pairs, 'old_new_comparison': comparison,
            'reviewer_agreement':agreement,'previous_error_rechecks':previous_errors,
            'meaning_correctness_not_proved_by_literal_checks': True, 'human_verified':False}


def main():
    pred = read(run.old.OUT/'predictions.json')
    for path, digest in read(run.OUT/'protocol.json')['protected_sha256'].items():
        assert sha(run.ROOT/path)==digest, path
    relevance = collect_relevance()
    versions, changes = label_versions(relevance)
    versions = {'v0_original': read(run.old.OUT/'labels.json')['records'], **versions}
    sources = source_registry()
    write(run.OUT/'source_registry.json', sources)
    write(run.OUT/'relevance_reviews.json', {'records':relevance,'changes':changes,
                                            'independent_provider_count':len({x[1] for x in reviewers()}),
                                            'human_verified':False})
    evaluations = {}
    original_complete = [q for q in pred['query_ids'] if all(r['status']=='JUDGED'
                         for r in versions['v0_original'] if r['query_id']==q)]
    for version, labels in versions.items():
        directory = run.OUT/version
        directory.mkdir(exist_ok=False)
        write(directory/'labels.json', {'records':labels,'human_verified':False,
                                        'label_source':'AI-Silver with inherited and reviewed provenance'})
        rows, macro, leave = metrics.evaluate(pred, labels)
        original_cohort_macro = metrics.existing.summarize(
            [{**r,'condition':'D' if r['condition']=='E' else r['condition']} for r in rows],
            set(pred['query_ids'])-set(original_complete))
        for row in original_cohort_macro:
            if row['condition']=='D':row['condition']='E'
        result = {'per_query':rows,'macro':macro,'leave_one_out':leave,
                  'bootstrap':metrics.bootstrap(rows,macro),
                  'incomplete_f1_difference_bounds':metrics.incomplete_f1_bounds(pred,labels),
                  'original_six_cohort_macro':original_cohort_macro,
                  'label_counts':dict(Counter(x['status'] for x in labels)),
                  'prediction_sha256':sha(run.old.OUT/'predictions.json'),
                  'same_predictions_reused':True,'no_model_improvement_between_label_versions':True}
        write(directory/'evaluation.json', result)
        evaluations[version]=result
    write(run.OUT/'quality_revalidation.json',quality_results())
    strict=versions['v2_reviewed_strict']
    write(run.OUT/'discovery_reviewed.json', metrics.diagnostics(pred,strict))
    write(run.OUT/'evaluation_index.json',{'versions':list(versions),'original_complete_questions':original_complete,
                                          'prediction_sha256':sha(run.old.OUT/'predictions.json'),
                                          'invalid_relevance_rows':sum(not x['valid'] for x in relevance),
                                          'selected_pairs':len(relevance)//2,
                                          'changed_or_abstained':sum(x['changed'] for x in changes)})
    paired=[]
    for version in versions:
        if version=='v0_original':continue
        left=evaluations['v0_original'];right=evaluations[version]
        for metric in left['per_query'][0]['metrics']:
            old_group=next(r for r in left['macro'] if r['condition']=='E' and r['metric']==metric)
            new_group=next(r for r in right['macro'] if r['condition']=='E' and r['metric']==metric)
            common=set(old_group['questions']) & set(new_group['questions'])
            for c in 'ABCE':
                before=[r['metrics'][metric] for r in left['per_query']
                        if r['condition']==c and r['query_id'] in common]
                after=[r['metrics'][metric] for r in right['per_query']
                       if r['condition']==c and r['query_id'] in common]
                paired.append({'version':version,'condition':c,'metric':metric,'n':len(common),
                               'query_ids':sorted(common),'old':mean(before) if before else None,
                               'new':mean(after) if after else None,
                               'reason':'Same saved predictions; change arises from label revision only.'})
    write(run.OUT/'label_version_common_cohort_comparison.json',{'records':paired})


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=['missing','all'])
    args=parser.parse_args()
    stage1() if args.stage=='missing' else main()
