# AX operational workflow dataset v2

The current release is **v2.0.0: 98 production workflows**, source-curated by the author and separately AI-annotated under the user's explicit authorization. It is **not human Ground Truth**, not a causal-effect dataset and not a held-out retrieval benchmark.

## Current files

- `main_cases_v2.json`: full cases, primary evidence anchors, lineage, qualified outcomes, actual independent AI-review records and the 101-candidate inclusion/exclusion ledger.
- `main_cases_v2.csv`: the same 98 workflows in a table, including uncertainty, evidence and direct-relation JSON columns. Empty factor/strategy cells mean explicit abstention, not an omitted review.
- `release_manifest_v2.json`: reproducible canonical data/input hashes, counts, scope and use restrictions.
- `strategy_taxonomy_v2_frozen.csv`: seven-class v2 release vocabulary; v1 remains unchanged.
- `inherited_evidence_review_v2.json`: all 41 inherited candidates' passage alignments and decisions; 38 retained and 3 excluded.
- `final_source_corrections_v2.json`: additional source-backed corrections, including a named retailer's annual report confirming operational AI markdown.
- `independent_label_review_v2.json`: exact isolated review prompts, input-ID map and raw results. Factor reviewers received only problem text; separate strategy reviewers received only task/implementation. Changed texts were resubmitted.
- `independent_mapping_review_v2.json`: separate applicability reviews of 72 eligible single pairs: 68 supported, 4 abstained. No Cartesian expansion.

There are **25 factor abstentions and 2 strategy abstentions** (one case overlaps). These are final explicit annotation decisions under a conservative policy, not 27 unfinished source reviews. A missing label is excluded from analyses requiring that label; a withheld direct relation is never manufactured from the two labels alone. Do not report AI annotations as human-verified accuracy.

There are **67 conservative source/organization/parent clusters**. Keep a whole `sampling_group_id` together before any future split. The sample is purposeful/convenience-based, not representative of an industry population. No new v2 retrieval, relevance-GT or Wald experiments have been run.

## Validation

```text
python scripts/build_v2_final_release.py --check
python scripts/validate_v2_release.py --freeze
python scripts/validate_v2_evidence.py --check-immutable
python -m unittest discover -s tests -p "test_v2*.py" -v
```

The final-release validator verifies snapshot reproduction, review-input binding, blinding boundaries, provenance completeness, abstentions and cluster integrity. It does not automatically prove supplier claims true. Source assessment and AI review are described in [the release report](../../docs/v2-final-release-2026-10-22.md).

## Historical staging is not the final release

`active_candidate_corpus_v2.json` remains the earlier 101-candidate inventory. The 94-parent staging, 38 split hypotheses, original first-pass records, source-access audits and replacement ledger are preserved historical inputs. Their statuses intentionally remain unapproved; their older validators' zero-approval/blocked-freeze outputs refer to those staging files, not the final 98-case release. Do not train from them or overwrite them to make the counters look completed.

Immutable v1 and all historical experiment outputs remain unchanged. Final source text, PDFs and local caches are not redistributed.
