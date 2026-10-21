# Dev Ground Truth v1 Freeze

Freeze date: **2026-10-21**

## Scope

Active Dev/Pilot benchmark:
- GTQ001~GTQ010
- Main Dataset v1 AX0001~AX0100
- 3 Reference Perspectives per active Query in the current Pilot format
- 300 Perspective × Case labels per Query
- **3000 active relevance labels total**

All active Query rows are `PILOT_GOLD_ADJUDICATED`.

## Frozen files

- `data/main_cases_v1.csv`  
  SHA: `4b85e296f797dd2759bf7f9e57b26d5473a72b38`

- `data/retrieval_queries_v0.1.csv`  
  SHA: `60ed29a080b6df48cb7322fc69e0ce8c7403f8fb`

- `data/perspective_case_relevance_v0.1.csv`  
  SHA: `d9ad98b5dad6b05c1dba54d02b46d47dedfb003c`

- `data/retrieval_gold_v0.1.csv`  
  SHA: `8044289de023c8f58796a6acdd3e1ef156b36d3d`

- `data/ground_truth_protocol.md`  
  SHA: `d7d0d29199cf3ea5b434b12f52ef71f43abbab51`

## Archive / audit trail

Low-discrimination or sparse initial Pilot queries were not deleted.

Archived:
- initial GTQ006
- initial GTQ007
- initial GTQ009
- initial GTQ010

Archive files preserve the reasons and prior labels where available.

## Freeze rule

Baseline and proposed-model comparisons should use this snapshot without modifying active relevance labels to improve downstream scores.

If Ground Truth must be changed after baseline results are observed:
1. record the reason,
2. create a new Ground Truth version,
3. do not silently overwrite v1.

## Next experiment

1. Single-query BM25
2. Single-query Dense Retrieval
3. GPT-only
4. Multi-Perspective Retrieval
5. compare Recall@K / Perspective Coverage@K / Strategy Coverage@K under comparable search/output budgets
