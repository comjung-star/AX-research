"""Third blind model on disagreements, all transfer pairs, and newly positive zero-query pairs."""
import json

from scripts.autonomous_blind_review import OUT, PRICES, PROMPT, read, save


def main():
    plan = read(OUT / 'preregistration.json')
    original = read(OUT.parent / '18_trial2_metrics_and_independent_review.json')
    selected = {tuple(pair) for pair in plan['transfer_pairs']}
    selected.update((row['query_id'], row['case_id']) for row in original['review_comparison']
                    if row['status'] in ('DISAGREEMENT', 'UNRESOLVED', 'BOTH_POSITIVE'))
    payload = [row for batch in plan['batches'] for row in batch if (row['query_id'], row['case_id']) in selected]
    batches = [payload[start:start + 16] for start in range(0, len(payload), 16)]
    input_rate, output_rate = PRICES['sonnet']
    reserve = sum(((len((PROMPT + json.dumps(batch, ensure_ascii=False)).encode()) + 1000) * input_rate + 4096 * output_rate) / 1e6 for batch in batches)
    assert reserve + original['cost_upper_bound_usd'] < 2
    save(OUT / 'sonnet_preregistration.json', {
        'models': {'sonnet': 'claude-sonnet-5-5'}, 'conservative_reserved_usd': {'sonnet': reserve},
        'batches': batches, 'selection': 'All16 transfer pairs, initial2-model disagreements, newly corroborated positives on formerly zero queries; previous votes and ranks hidden.',
        'pricing_source': 'https://platform.claude.com/docs/en/models/sonnet-5-5/overview',
        'pricing_checked_date': '2026-11-08', 'rates': PRICES['sonnet'],
        'adjudication': 'Majority positive/negative threshold across3 blinded models; retain all grades and disagreement. AI-Silver only; not human Gold. Never change frozen original labels.'})
    print(json.dumps({'selected_pairs': len(payload), 'reserved_usd': reserve}))


if __name__ == '__main__':
    main()
