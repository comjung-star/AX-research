# Cycle11: frozen candidate10 transfer to old CPD development queries

Candidate10 first exceeded E and Dense mean F1/nDCG under all3 fixed new20 label versions; all descriptive intervals still include0. Freeze its complete formula and all weights before this transfer. No fitting or parameter changes are permitted.

Use existing CPD01-08 development queries,112cases, original E72branches, original-case Tasks and same frozen BGE-M3 local backbone. Reuse original/branch CLS vectors from preserved CPD caches and verify original Dense and Ebranch Dense against stored evidence to1e-6. Recompute token outputs locally using exactly cycle10 encode and score functions. Original Dense and centered token scores get50:50min-max fusion; original50% and query-fidelity-weighted branches50% late fusion, same temperature0.1. Preserve per-repeat outputs. Also run the fixed token single-query control, E and Dense.

Original CPD qrels have896pairs,867graded and29unjudged. Before computing metrics, include only questions with all112grades for the common F1/nDCG comparison (6questions). Exclude CPD06/07 rather than replacing missing grades. P@5 macro reported on the same6complete questions; full8question rankings remain stored. No new labeling or imputation.

This is transfer to a different previously inspected development set, not independent external test. CPD results informed historical design and were visible in the audit, although candidate10 was not numerically tuned on them. Report positive and negative transfer, question-paired intervals and the small6query sample. Do not tune candidate10 on CPD or open Test15. No paid calls, downloads or original-data edits.
