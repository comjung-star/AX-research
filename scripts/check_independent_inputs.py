"""Read-only readiness checks; empty templates never become independent data."""
import csv
import hashlib
import json
import re
import unicodedata

from scripts.improvement_cycle import ROOT, read

OUT = ROOT / 'docs/independent-validation-20261108'


def normalize_question(text):
    return re.sub(r'[^\w]', '', unicodedata.normalize('NFKC', text).casefold())


def check():
    freeze = read('docs/independent-validation-20261108/source_freeze.json')
    for path, expected in freeze['sha256'].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen source changed: ' + path)
    with (OUT / 'author/questions_to_fill.csv').open(encoding='utf-8-sig', newline='') as source:
        rows = list(csv.DictReader(source))
    populated = [row for row in rows if any(row[field].strip() for field in ('business_problem', 'input', 'desired_output', 'constraints'))]
    if not populated:
        return {'state': 'WAITING_FOR_INDEPENDENT_AUTHORS_AND_REVIEWERS', 'actual_new_queries': 0,
                'actual_human_grades': 0, 'source_freeze_matches': True,
                'inference_executed': False, 'paid_calls': 0, 'test15_accessed': False}
    declaration = json.loads((OUT / 'author/authorship_to_fill.json').read_text(encoding='utf-8'))
    if not (declaration['author_id'].strip() and declaration['independent_of_model_development'] is True
            and declaration['saw_case_corpus'] is False and declaration['saw_rankings_or_old_labels'] is False
            and declaration['authored_from_real_work_needs'] is True):
        raise ValueError('Independent authorship declaration is missing or incompatible')
    if len(populated) != 40 or len({row['query_id'] for row in populated}) != 40:
        raise ValueError('The pilot requires40distinct submitted questions; blanks are not questions')
    known = set()
    for path in ['docs/validation-new20-20261107/questions.jsonl', 'docs/core-preserved-three-views-2026-11-07/questions.jsonl']:
        for line in (ROOT / path).read_text(encoding='utf-8').splitlines():
            known.add(normalize_question(json.loads(line)['text']))
    seen = set()
    for row in populated:
        if not row['business_problem'].strip() or not row['desired_output'].strip() or row['author_id'] != declaration['author_id']:
            raise ValueError('Missing problem/output or inconsistent author')
        question = normalize_question(row['business_problem'])
        if question in seen or question in known:
            raise ValueError('Duplicate or previously used question: ' + row['query_id'])
        seen.add(question)
    return {'state': 'AUTHOR_DECLARED_QUESTIONS_RECEIVED_NOT_YET_ADMITTED', 'actual_new_queries': 40,
            'authorship_independence': 'SELF_ATTESTED_NOT_EXTERNALLY_VERIFIED',
            'semantic_duplicate_review': 'REQUIRED_AGAINST_ALL_PRIOR_DEVELOPMENT_QUESTIONS',
            'runtime_branch_generation': 'PENDING_SAME_FROZEN_POLICY_AND_NO_PAID_CALL_AUTHORIZATION',
            'human_grading': 'PENDING', 'inference_executed': False, 'paid_calls': 0}


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False, indent=2))
