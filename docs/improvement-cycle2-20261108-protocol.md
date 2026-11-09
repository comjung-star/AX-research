# Cycle 2: candidate preservation and query-grounded branches

Frozen before cycle-2 scores. Use stored evidence only, no new generation, training, embedding execution, or test access. All variants are development diagnostics, not professor-approved replacements.

Candidate experiment: retain 20 candidates using original Dense20 or unique alternating original Dense/Sparse20, and rerank with the previously tested original-rules-only scorer. Output remains Top5; ideal nDCG uses all112 grades. Compare each with the corresponding E scorer restricted to exactly the same candidates, with full112 E and Dense, and report candidate recall separately.

Branch preservation experiment: on full112, allow only branches sharing a recognized original-query function with the case Task (existing allowed_branches policy). Test the existing max compose and original-rules-only compose under that policy. This asks whether unrelated branch functions and semantic drift explain ranking loss. Also test lexical core grounding: a branch may participate only if it preserves at least one original recognized function, independent of the candidate. Missing original function recognition falls back to original-query scoring, not inferred synonyms.

Primary labels remain working_transfer. Sensitivity labels are original and the already stored 464-pair scoped independent consensus overlay. Preserve all three, report exact query counts, and never combine their absolute means. Reuse the same query bootstrap and report differences versus Dense and E. Success criteria remain those in cycle1; no tuning using final test results.

Cycle3 language hypothesis, to execute only after cycle2: inspect existing bilingual lexical rules for concrete tokenization/normalization defects, test only source-grounded normalization or existing source-provided bilingual fields. No fabricated translations, new paid LLM calls, new labels or external model downloads. If available evidence cannot support a language experiment, document the missing input explicitly rather than claiming it was tested.
