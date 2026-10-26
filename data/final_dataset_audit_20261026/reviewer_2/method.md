# Independent AI reviewer B: blind DEV annotations

Reviewer: `independent_ai_reviewer_B`. This is AI annotation, not human Gold, independently confirmed causal truth, final held-out Test evaluation, or researcher approval.

Read scope: repository AGENTS.md, blind_relevance_input.json, factor_blind_input.csv, and frozen root_cause_taxonomy_v2_3.csv only. No solutions, implementations, outcomes, rankings, prior labels, other reviewers, network, or paid APIs are used. No further agents are used.

Relevance: individually compare the query and one reference perspective to the case Problem/Task/Context. Scores: 0 unrelated; 1 remote substantive relation; 2 meaningful overlap but a different central workflow; 3 same central problem/task with contextual differences; 4 directly matching problem/task and context. Positive threshold is 3. Generic volume, manual work, data, and AI alone do not establish relevance. A missing assertion is not silently inferred. Perspectives are scored independently, and empty positive sets are allowed.

Authoring: each query has an explicitly authored matrix, in the immutable input case order (001..117). Every row specifies three independent integer scores and a case-specific Korean evidence comparison. Where one explanation supports all three scores it is shared; differing grounds use three explicit explanations separated by `~`. Serialization appends the relevant perspective title for clear pair attribution. There is no inferred score, default score, keyword/regex classifier, similarity score, or model-output label. The expansion program only checks coverage and serializes the written decisions. Case indices are resolved to exact input IDs, never to company-name guesses.

Relevance input fingerprint: SHA256 of UTF-8 json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(',', ':')) = `758a3ef1622218ef4232a328af8df2492cb5b1c14df82c68aa12a8c757dfdf0c`.

Factor input fingerprint: SHA256 of raw CSV bytes = `fd61a890e0d972071d591de34fbedb7ef916baf1aa42b66958faf2c53a855919`.

Factor review uses only each row's Problem, not Task/Context. Explicit factors may be multi-label. Missing support leads to ABSTAIN. Each rationale includes an uncertainty qualification, because the requested CSV has no separate uncertainty column. Taxonomy names are expanded from explicitly authored numeric factor IDs; no assignment is inferred by the expansion program.

DEV relevance was sealed before opening the newly authorized Test input. DEV CSV raw SHA256: `99a8ed37bf7a9b23c06b4044a945894e2fda39aa2cd354d7575cee0b51e876cb`. No subsequent independent-stage changes are allowed. Test input canonical SHA256: `fd8bbb3aab58a30d8e8b37ef95ad6e78da2c3513a3a707a2a5bbb459b65aeef9`. Test has 12 synthetic queries, 30 perspectives, 117 identical PTC cases. Test judgments are newly authored; DEV grades are not read or copied to produce them.

Test compact notation: each row explicitly supplies its entire score vector (two or three independently selected scores). `N` is an explicitly authored all-zero exclusion, expanded using the reviewed case-specific evidence in `test_case_evidence.txt` and the individually authored perspective comparison in `serialize_test.py`. It is allowed only when every explicit score is zero. All nonzero vectors have an explicit case/query comparison, optionally one explanation per perspective. Neither scores nor relevance decisions are inferred by this notation. This keeps unrelated pairs judged rather than unjudged while making their evidence auditable.

Requested sequence: seal DEV relevance; seal Test relevance; seal Problem-only factors; only then open the additionally authorized disagreement input and write proposals for even DEV queries. Reconciliation is post-independent AI adjudication, not a third independent pass or human Gold. Originals remain sealed. Solutions and strategy material remain outside scope.
