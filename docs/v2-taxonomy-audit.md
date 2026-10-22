# v2 taxonomy audit — provisional, not frozen

The v1 nine-factor and six-strategy dictionaries remain unchanged. Fresh labels in the reconstruction files are proposals justified by newly written problem and implementation fields; seeing these fields sequentially in one review is not an independently blinded RCA experiment.

## Confirmed or plausible gaps

1. **Generated visual media / virtual try-on (AX0087).** Google Cloud's Black Eyewear source separates specialist frame recommendation from Nano Banana 2 image synthesis. S5 can describe choosing frames; it does not adequately encode synthesizing an on-brand try-on image. Candidate new strategy: `S7_GENERATIVE_VISUAL_MEDIA`, defined as generating or editing image/video content as the delivered workflow output. Exclude visual classification/detection (S4), document extraction (S3), and recommendations without generated media (S5). This is a proposal, not an accepted label. No legacy F09 label is inherited merely because the solution uses a model.
2. **Live translation (AX0054).** STT followed by industry-term-aware multilingual translation is not automatically document intelligence or a customer chatbot. Candidate strategy boundary: `LANGUAGE_TRANSFORMATION_TRANSLATION`. The checked article is secondary; primary implementation source needs passage review before proposing an accepted taxonomy extension.
3. **Code remediation (AX0064).** MISRA error repair generates changes to source code. S6 describes workflow automation, but does not distinguish code transformation from other execution. The cited implementation is experimental/project-stage; no production sample is admitted merely to justify a new label.
4. **Product attribute classification (AX0079).** Classifying catalog attributes is neither future prediction nor necessarily document analysis. Use a provisional `CONTENT_CLASSIFICATION` boundary review instead of forcing S3/S4 from the names of model technologies.
5. **Physical actuation (AX0097/AX0099).** S6's execution/automation definition can express robotic unloading and marking, with vision/robotics separately represented in implementation. A new strategy is not automatically needed simply because the embodiment is a robot.

The v1 extension protocol asks for repeated evidence in at least three cases before changing a dictionary. The sources above establish several different boundary questions, not three interchangeable examples of one new category. Do not count them together to manufacture support for S7. The NIPA report's printed pp.68–69 (physical PDF page 37) describes text-to-video outputs for manuals and financial terms as possible additional scope for later sampling; those are not automatically extra cases in the current 100-parent dataset.

## Mapping discipline

- Factor labels use Problem/Task/Context evidence; strategy labels use implemented Solution evidence.
- A proposed applicability rationale means the implementation addresses the documented problem within that workflow. It is not a causal effect, not a Wald association, and not an approved Ground Truth link.
- One rationale accompanies each proposed direct pair in the detailed split reconstruction. No Cartesian product of secondary factors and strategies is generated.
- Missing deployment, ambiguous workflow boundaries, unisolated aggregate KPIs and dictionary gaps remain explicit abstentions. No new retrieval, Ground Truth or Wald experiments consume these candidates.
