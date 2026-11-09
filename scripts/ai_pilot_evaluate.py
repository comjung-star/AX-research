"""Evaluate sealed four-system rankings against fresh AI votes without changing labels."""
import json
from collections import Counter, defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from scripts.claude_blind_questions import OUT, save
from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate
from scripts.check_independent_inputs import normalize_question


def assemble_votes():
    registry = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    votes = {}
    for provider in ('claude', 'gemini'):
        records = {}
        for position in range(1, 41):
            name = f'{provider}_IVQ{position:03d}_validated.json'
            original = OUT / 'blind_review_v2' / name
            recovered = OUT / 'blind_review_429_recovery' / name
            assert not (original.exists() and recovered.exists()), 'Valid vote regeneration not allowed'
            path = original if original.exists() else recovered
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding='utf-8'))
            assert len(data['records']) == 112 and not data['parse_error']
            for row in data['records']:
                key = (row['query_id'], row['case_id'])
                assert key not in records and row['case_id'] in registry
                records[key] = row
        votes[provider] = records
    consensus = []
    for position in range(1, 41):
        query = f'IVQ{position:03d}'
        for case in sorted(registry):
            pair = [votes[provider].get((query, case)) for provider in ('claude', 'gemini')]
            agreed = all(row and row['status'] == 'JUDGED' for row in pair) and (pair[0]['grade'] >= 2) == (pair[1]['grade'] >= 2)
            consensus.append({'query_id': query, 'case_id': case,
                              'grade': min(row['grade'] for row in pair) if agreed else None,
                              'status': 'JUDGED' if agreed else 'ABSTAIN',
                              'votes': {provider: row for provider, row in zip(('claude', 'gemini'), pair)}})
    return votes, consensus


def score_version(rankings, records):
    grouped = defaultdict(dict)
    for row in records:
        grouped[row['query_id']][row['case_id']] = row['grade']
    complete = {query: values for query, values in grouped.items() if len(values) == 112 and all(value is not None for value in values.values())}
    if not complete or not any(any(value >= 2 for value in values.values()) for values in complete.values()):
        return {'state': 'NO_DEFINED_POSITIVE_QUERY_METRICS', 'fully_judged_queries': len(complete), 'summary': {}, 'per_query': {}}
    result = evaluate([row for row in rankings if row['query_id'] in complete], complete)
    result['fully_judged_queries'] = len(complete)
    result['excluded_incomplete_queries'] = sorted(set(grouped) - set(complete))
    result['zero_positive_queries'] = sorted(query for query, values in complete.items() if not any(value >= 2 for value in values.values()))
    contrasts = {}
    for baseline in ('Dense', 'E', 'TokenSingle'):
        for metric in ('F1@5', 'nDCG@10'):
            differences = np.asarray([row['TokenMulti'][metric] - row[baseline][metric] for row in result['per_query'].values() if row[baseline][metric] is not None])
            generator = np.random.default_rng(20261108)
            samples = np.concatenate([generator.choice(differences, size=(1000, len(differences))).mean(axis=1) for _ in range(100)])
            lower, upper = np.quantile(samples, [.05 / 12, 1 - .05 / 12])
            contrasts[baseline + ':' + metric] = {'eligible_queries': len(differences), 'delta': float(differences.mean()),
                'simultaneous_bonferroni_ci': [float(lower), float(upper)], 'lower_gt_zero': bool(lower > 0), 'resamples': 100000}
    result['six_prespecified_contrasts'] = contrasts
    return result


def author_screen():
    questions = json.loads((OUT / 'claude_authored_questions.json').read_text(encoding='utf-8'))['questions']
    old = []
    for path in ['docs/validation-new20-20261107/questions.jsonl', 'docs/core-preserved-three-views-2026-11-07/questions.jsonl',
                 'docs/c0-c1-new-validation-2026-11-02/input/questions.jsonl']:
        old.extend(json.loads(line)['text'] for line in (ROOT / path).read_text(encoding='utf-8').splitlines())
    texts = [row['business_problem'] for row in questions]
    assert len(set(map(normalize_question, texts))) == 40
    exact = [row['query_id'] for row in questions if normalize_question(row['business_problem']) in set(map(normalize_question, old))]
    vectors = TfidfVectorizer(analyzer='char', ngram_range=(3, 5)).fit_transform(texts + old)
    similarity = (vectors[:40] @ vectors[40:].T).toarray()
    return {'questions': 40, 'sector_counts': dict(Counter(row['sector'] for row in questions)), 'exact_development_duplicates': exact,
            'known_dev_questions_checked': len(old), 'max_old_character_similarity': similarity.max(axis=1).tolist(),
            'screening_is_not_human_realism_or_semantic_novelty_certification': True, 'questions_removed_or_rewritten': 0}


def main():
    screen = author_screen()
    assert not screen['exact_development_duplicates']
    save(OUT / 'author_screen.json', screen)
    predictions = json.loads((OUT / 'predictions.json').read_text(encoding='utf-8'))
    assert len(predictions['rankings']) == 480 and not predictions['relevance_inputs_opened']
    votes, consensus = assemble_votes()
    assert all(len(rows) == 4480 for rows in votes.values())
    save(OUT / 'ai_consensus.json', {'records': consensus, 'human_gold': False, 'policy': 'Two-provider binary agreement, min grade; disagreement or missing is ABSTAIN'})
    results = {provider: score_version(predictions['rankings'], list(records.values())) for provider, records in votes.items()}
    results['consensus'] = score_version(predictions['rankings'], consensus)
    output = {'state': 'NEW_CLAUDE_AUTHORED_AI_SILVER_PILOT_EVALUATED', 'results': results,
              'pairs_per_provider': {provider: len(rows) for provider, rows in votes.items()},
              'consensus_judged': sum(row['grade'] is not None for row in consensus),
              'consensus_abstain': sum(row['grade'] is None for row in consensus), 'human_gold': False,
              'new_final_independent_test_claim': False, 'pilot_questions': 40,
              'limits': ['AI-generated plausible scenarios, not human-authored real work submissions',
                         'Author and one rater share Anthropic; raters are2providers, not wholly independent truth',
                         'Input Task excerpts are supplied evidence, not model-selected quotations',
                         'Technical preflight failures and429recoveries retained; valid votes not regenerated',
                         '40questions was an explicitly designated pilot, not guaranteed-powered confirmation']}
    save(OUT / 'evaluation.json', output)
    for provider, result in results.items():
        for name, values in result.get('summary', {}).items():
            print(provider, name, values['F1@5']['queries'], round(values['F1@5']['mean'], 5), round(values['nDCG@10']['mean'], 5))


if __name__ == '__main__':
    main()
