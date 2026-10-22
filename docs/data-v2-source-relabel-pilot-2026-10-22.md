# v2 source re-label pilot — ten specific business workflows (2026-10-22)

**STATUS: ONE-PASS SOURCE-CHECKED, NOT V2 FROZEN / NOT SECOND-REVIEWER APPROVED.**

`data/v2/source_relabel_pilot_v2.csv` reconstructs 10 candidate business workflow units from public original-source text, retaining v1 parent lineage but writing new single-workflow Problem/Task/Context and Solution fields. It classifies primary and secondary Factor and Strategy **as hypotheses justified by separate Problem/Solution original content**. All proposed direct Factor→Strategy relations remain `NOT_ESTABLISHED` pending passage-level explicit alignment, and second-reviewer approval is `NO`.

Rebuilt single-workflow parents: AX0001, AX0002, AX0003, AX0004, AX0008, AX0009, AX0021, AX0027, AX0075, AX0081. These are part of the 75 parent candidates, not extra new approved data points. As a strict anti-leakage practice, root factors were reasoned from Problem/Task/Context; implemented strategies from solution text. All source titles and section locator keywords accompany the rows.

## Important corrected interpretations

- **AX0004 / Orion Health**: 500k+ internal records retrieved under one minute is a presented capability. **The 50 staff hours per day saving is explicitly framed as *expected* in the source Outcome section**. The original v1 record already uses an expectation qualifier, so do NOT transform it into measured realized savings.
- **AX0021 / Hyundai–MakinaRocks**: source reports model predictions up to five days in advance with 90%+ accuracy; the broad 1,400-robot footprint is described as a **phased rollout**, not evidence all 1,400 robots are in production on that date.
- **AX0003 / Genpact**: AWS story also mentions a separate general GenAI Playground platform. Our unit contains **background-check report validation only**.
- **AX0081 / Starling**: Google story includes Scam Intelligence, Spending Intelligence and customer-service knowledge assistant as **other distinct workflows**. Only customer call transcript summarization and its monthly 8,000-hour saving are carried into this row.
- **AX0009 / Worten**: source includes earlier estimated search workload and claimed benefit; preserve vendor attribution and avoid presenting it as a separate independent study.
- **AX0075 / Chime**: source reports over 250k annual hours from customer call summarization, separate from overall customer satisfaction metrics.
- No second reviewer; no frozen v2 case IDs; no downstream retrieval/Wald retraining on these entries yet.

Next requirement: expand this exact workflow-level original evidence reconstruction from 10 to all remaining candidates and split children, adjudicate any unsupported or ambiguous labels, then freeze an independent verified v2 corpus.
