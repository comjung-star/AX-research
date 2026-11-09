"""Verify raw rater coverage and repeat complete pilot metric calculations offline."""
import hashlib
import json

from scripts.claude_blind_questions import OUT, save
from scripts.improvement_cycle import read
from scripts.ai_pilot_review_v2 import parse_rows
from scripts.ai_pilot_evaluate import assemble_votes, score_version


def main():
    predictions = json.loads((OUT / 'predictions.json').read_text(encoding='utf-8'))
    questions = [json.loads(line) for line in (OUT / 'questions.jsonl').read_text(encoding='utf-8').splitlines()]
    ids = predictions['case_ids']
    assert len(questions) == 40 and len(ids) == 112
    registered = {(row['query_id'], repeat, system) for row in questions for repeat in (1, 2, 3)
                  for system in ('Dense', 'E', 'TokenSingle', 'TokenMulti')}
    actual = {(row['query_id'], row['repeat'], row['system']) for row in predictions['rankings']}
    assert len(predictions['rankings']) == len(actual) == len(registered) == 480 and actual == registered
    assert all(len(row['ranking']) == len(set(row['ranking'])) == 112 and set(row['ranking']) == set(ids) for row in predictions['rankings'])
    votes, consensus = assemble_votes()
    raw_rows = 0
    for provider in ('claude', 'gemini'):
        for query in questions:
            stem = provider + '_' + query['query_id']
            original = OUT / 'blind_review_v2' / (stem + '_response.json')
            recovered = OUT / 'blind_review_429_recovery' / (stem + '_response.json')
            assert not (original.exists() and recovered.exists())
            path = original if original.exists() else recovered
            rows = parse_rows(json.loads(path.read_text(encoding='utf-8')), provider)
            assert len(rows) == 112 and {row['position'] for row in rows} == set(range(112))
            for row in rows:
                expected = votes[provider][query['query_id'], ids[row['position']]]
                assert row['grade'] == expected['grade']
            raw_rows += len(rows)
    assert raw_rows == 8960
    stored = json.loads((OUT / 'evaluation.json').read_text(encoding='utf-8'))
    for provider, records in votes.items():
        assert score_version(predictions['rankings'], list(records.values())) == stored['results'][provider]
    assert score_version(predictions['rankings'], consensus) == stored['results']['consensus']
    assert not predictions['relevance_inputs_opened'] and not predictions['test15_opened']
    report = {'state': 'NEW_AI_PILOT_RAW_VOTES_RANKINGS_AND_METRICS_VERIFIED', 'questions': 40,
              'raw_ai_rating_rows': raw_rows, 'rankings': 480, 'case_ids_each_ranking': 112,
              'multiple_comparison_bootstraps_recalculated': sum(len(result.get('six_prespecified_contrasts', {})) for result in stored['results'].values()),
              'no_label_read_during_recorded_inference': True, 'test15_opened': False, 'verification_paid_calls': 0,
              'artifacts_sha256': {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
                                  for name in ('questions.jsonl', 'predictions.json', 'ai_consensus.json', 'evaluation.json')}}
    save(OUT / 'verification.json', report)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
