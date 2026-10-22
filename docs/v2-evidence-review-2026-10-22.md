# Primary-source workflow review, production-only scope

This report supersedes the pilot-inclusion question in the earlier blocker note. User decision: production deployments only. No new frozen corpus is claimed.

Later authorized action: the unresolved 28 parents plus held AX0098 and 11 split hypotheses are now excluded from the active candidate corpus and administratively replaced by 40 new production workflow candidates. This report preserves the original source findings; its remaining-source list is historical, not a requirement to recover excluded cases. [The replacement report](v2-production-replacements-2026-10-22.md) states current scope and remaining independent-review restrictions. `validate_v2_evidence.py` still audits historical staging; the separate replacement validator governs active candidate reproducibility. Neither approves final GT.

## Completed evidence work

- Inventoried all 94 candidate parents against 99 distinct cited URLs. Recorded response status, UTC access time, redirects and response SHA-256 where downloaded. A successful download is explicitly not semantic verification. Full downloaded texts and the NIPA PDF remain ignored local cache files and are not redistributed in Git.
- Re-read sources for all 19 split parents and recorded 38 individual dispositions: 20 production candidates, 5 pilot exclusions, 11 evidence/boundary holds, and 2 rejected generic/platform splits. These are source-review dispositions, not independently approved Ground Truth.
- Reconstructed all 20 split production candidates in `workflow_candidates_v2.json`, with newly written Problem/Task/Context/Implementation, deployment anchors, outcome qualifications, one proposed factor and strategy and a specific applicability rationale. Added 23 further parent reconstructions in `parent_reconstructions_v2.json`, including one explicitly held for implementation detail. No factor-by-strategy Cartesian product or statistical causal claim was generated.
- Recorded source-screening findings and limitations for all 51 other non-split parents. This completes their screening inventory, not independent approval or detailed re-extraction of all cases.
- Kept the old staging inventory, 38 hypotheses, immutable v1 and all historical experiments intact. The historical 24-parent first-pass file remains an audit artifact; it is not the current production eligibility list.

## Material corrections

- Telstra's 84%/90%/20% numbers describe trials; the cited story describes full deployment as future. Vodafone's specific generative TOBi and SuperAgent implementations are pilots despite an existing older TOBi service.
- Home Credit's 130-user controlled pilot and CRM conversion claim do not explicitly establish a subsequent regular-production transition. Security governance is not a second frontline business workflow.
- BNY payment repair covers over 10% of repair issues, not 10% of all payments. Onboarding and inquiry speed benefits concern AI-assisted subsets.
- Cashfree's over-24-hour merchant onboarding baseline is a p99 measure for some merchant categories. Comparison to the new ten-minute claim requires a population/percentile caveat. Future automation coverage is not a realized outcome.
- Albert Heijn's hoped-for >10% waste reduction is distinct from daily forecast throughput. The 250000 kg annual waste saving belongs to Dynamic Markdown, not the demand forecast workflow.
- Black Eyewear's frame recommendation and generated try-on images have different mechanisms. Overall sales and consultation improvements cannot be isolated to try-on from the source.
- HEINEKEN's logistics validation app uses Power Apps/Automate; its company-wide 3.1 million productivity hours must not be attributed to a specific AI agent. The source separately describes an operational Amstel website FAQ agent with approximately 300 hours/year returned.
- Sicredi's primary IBM page independently confirms a three-week co-creation and 20-day pilot, followed by future expansion. Its “retention” is query resolution without escalation, not customer retention.

## NIPA report retrieval and page numbering

The web reader failed to open the PDF attachment. A subsequent direct download succeeded. Do not treat that initial access failure as a permanent source blocker.

- Landing page: https://www.nipa.kr/home/bsnsAll/3/nttDetail?bbsNo=1&nttNo=15766&tab=3
- Attachment: https://www.nipa.kr/comm/getFile?srvcId=BBSTY1&upperNo=Co1q7uuEpe2WvBi9**6DZg==&fileTy=ATTACH&fileNo=Aa7YtxzX3F8qeDCOXtcHPw==
- Downloaded response: 19486100 bytes; SHA-256 `c86e77c560d42d3053bd40e98ef46772645bcc8a91b9e10967fd86fe100e8fe5`.
- PDF has 70 physical pages containing two printed pages per spread. Printed pages 12–13 (Lunit) are physical PDF page 8; 20–21 (SuperBin) page 12; 22–23 (SI Analytics) page 13; 36–37 (RexGen) page 20; 44–45 (Mathpresso) page 24; 50–51 (December & Company) page 27; 54–55 (AIZEN) page 29; 58–59 (Law&Company) page 31. Never equate printed page numbers with zero-based PDF indices.
- SI Analytics' spread presents several products and broad applications. It does not identify a specific deployed customer problem and matching solution separately for OVISION and Super X. Both split hypotheses remain held on workflow/deployment evidence, not inability to download the report.

## Remaining work and final-freeze restrictions

Of 51 non-split parents outside the historical first-pass 24, 23 now have newly written reconstructions. For the other 28, screening records specify source access failures, secondary-only support, vague deployment, workflow boundaries or insufficient implementation detail. This does not complete the requested passage-by-passage verification of those 28. The source access inventory must not be used as a substitute. In particular the cited original LOTTE pages need recovered primary text and source-poor provider patterns need actual customer deployment evidence; existing legacy labels or secondary summaries cannot fill those gaps.

The cited LOTTE cloud newsroom URLs for AX0056–AX0059 timed out both in direct requests and the web reader. Supplier or company-wide AI availability does not replace evidence for each named deployed workflow. AX0087's generated-image strategy remains outside the frozen six-class vocabulary; no S5 label is forced. Label proposals and applicability rationales have not received independent approval or established causal effects.

`validate_v2_evidence.py --freeze` intentionally fails while these conditions remain. Its ordinary successful run validates schema and lineage only. It does not certify source truth or approve the final research corpus.
