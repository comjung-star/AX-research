"""Export only existing source locators, never old grades or recommendation ranks."""
import csv
import json

from scripts.improvement_cycle import ROOT, read


def main():
    registry = read('docs/core-preserved-e-validation-2026-11-07/source_registry.json')
    cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    destination = ROOT / 'docs/independent-validation-20261108/review/source_locators.csv'
    count = 0
    with destination.open('x', encoding='utf-8-sig', newline='') as target:
        fields = ['case_id', 'evidence_id', 'source_url', 'evidence_locator', 'new_fact_check_done']
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for case in sorted(cases):
            assert registry[case]['structured_case'] == cases[case]
            for source in registry[case]['sources']:
                writer.writerow({'case_id': case, 'evidence_id': source['evidence_id'], 'source_url': source['source_url'],
                                 'evidence_locator': source['evidence_locator'], 'new_fact_check_done': 'FALSE'})
                count += 1
    print(json.dumps({'cases': len(cases), 'source_rows': count, 'new_web_checks': 0, 'old_labels_exported': False}))


if __name__ == '__main__':
    main()
