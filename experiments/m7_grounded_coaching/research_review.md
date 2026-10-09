# M7A Research Review — Categorized Literature Survey

**Correction to prior framing:** an earlier pass treated a Papers-with-Code candidate
list as an implementation backlog and attached specific numeric thresholds (Pearson
r ≥ 0.6, 15% variance reduction, N=50) to future experiments without justification from
any source. **Those numbers are retracted.** No threshold appears anywhere in this
document unless it is directly attributable to one of: (a) the source paper's own
reported statistic, (b) an established benchmark, (c) an existing SpeakLab product
requirement, or (d) an explicit statistical/design rationale stated inline. Where no
such justification exists, the corresponding experiment design below says so plainly
and proposes a **transparent comparison** (report the numbers, describe the pattern) —
not a manufactured pass/fail line.

## Provenance and verification level

This review was built by web-searching and fetching primary sources (arXiv
abstracts/PDFs), not from unverified recall. Every paper below is tagged with how it
was verified:

- **[fetched]** — abstract or substantial paper text was retrieved and read directly
  in this session.
- **[snippet]** — only a search-engine result snippet/summary was seen, not the primary
  source text. Treated as lower-confidence; findings from these are phrased more
  cautiously and should be independently verified before any claim from them is
  reused in `conclusions.md` or a future decision-log entry.

Full source list with links is at the bottom of this document.

**Throughout this document, five things are kept explicitly separate, per this
milestone's correction — each per-paper entry's numbered fields map onto these:**

- **Paper-reported evidence** (entry field 1, "Actual finding") — what the source
  actually measured, in its own domain, stated as that source's own result.
- **Transfer assumption** (entry field 3, "What assumption would need to transfer") —
  the specific, named gap between the paper's domain (writing, code, clinical QA,
  general NLG, etc.) and SpeakLab's actual domain (solo spoken impromptu practice) that
  would have to hold for the finding to apply here. Stated as an open question, not
  assumed true.
- **SpeakLab hypothesis** (entry field 2, "What SpeakLab decision it could influence") —
  what we think *might* follow for SpeakLab *if* the transfer assumption holds, stated
  as a hypothesis, not a fact.
- **Future experiment** (entry field 5, "Small reproducible experiment") — the
  transparent, threshold-free comparison that would actually test the hypothesis in
  SpeakLab's own domain.
- **Production decision** (entry field 9, "Adopt/Reject/Defer") — what this review
  actually commits SpeakLab to today. **For every entry in this document, no live M7
  experiment has been run** (see `experiment_plan.md`'s existing NOT RUN status on
  EXP-M7-001 through 005) — so "Adopt" below never means "ship this in production,"
  only "adopt as a design input, a methodology, or a naming/limitation correction to
  an existing M7A document." Where an entry says "Defer," it commits SpeakLab to
  nothing beyond keeping the idea on file for M7A-2/M7B.

---

## Category A — Directly relevant to M7 grounded coaching

Papers/prior art about automated **speaking/presentation coaching** specifically —
the same product surface M7 is designing for.

### A1. Probing Experts' Perspectives on AI-Assisted Public Speaking Training

**Source:** arXiv 2507.07930 [fetched]

1. **Actual finding:** 16 semi-structured interviews + 2 focus groups with public
   speaking experts evaluating commercial AI speaking-training tools. Experts valued AI
   for repetitive technical aspects (pace, filler counting) but identified a
   need for "personalised, understandable, carefully selected feedback and clear
   instructional design," and generally favored a **hybrid model** (AI-supported
   exercises alongside, not replacing, human coaching) over an AI-only tool.
2. **SpeakLab decision it could influence:** Directly supports M7A's own conclusion
   (section 1/17 of `conclusions.md`) that the coach must surface **one** prioritized,
   well-explained improvement rather than a raw metrics dump — this paper is
   independent, domain-specific confirmation of that design instinct, not just this
   project's own reasoning.
3. **Assumption that would need to transfer:** Experts were evaluating *existing
   commercial tools* (not SpeakLab specifically) and were speaking-coaching
   professionals, not the actual end users (solo practicers). Whether their
   "understandable, carefully selected" preference matches what a solo, non-expert
   practicer actually wants from feedback is an assumption, not shown by this paper.
4. **Baseline:** SpeakLab's own Approach A vs. B vs. C illustrative comparison
   (`results/summary.md`) — this paper doesn't provide a numeric baseline, only a
   qualitative design preference to weigh against ours.
5. **Small reproducible experiment:** Not a quantitative-replication candidate (this is
   a qualitative interview study). The transferable idea is procedural: run a small
   number of structured interviews/think-alouds with actual SpeakLab practicers once a
   real coach exists, asking specifically whether they find the technique-library-
   selected recommendation "understandable" — the same qualitative question this paper
   asked of experts, not a statistic to replicate.
6. **Metrics:** Qualitative (interview themes), not applicable as a numeric metric for
   SpeakLab.
7. **Cost/compute:** None (no model call) — this is a design-review reference, not an
   experiment to run.
8. **Risks:** Findings come from an expert population, not novice/solo practicers —
   risk of over-indexing on coach-professional preferences that don't match SpeakLab's
   actual target user (`docs/requirements.md` "Target User").
9. **Decision: Adopt as design input, not as a runnable experiment.** Already
   reflected in M7A's existing "one main improvement" principle; cited here as external
   corroboration, not as license to add new scope.

### A2. A Survey of Automated Presentation Coaching: Systems, Methods, and Open Challenges

**Source:** arXiv 2606.27380 [snippet only]

1. **Actual finding (low confidence, snippet-only):** A survey covering
   pronunciation, lexical stress, prosody, pacing, and content-faithfulness dimensions
   across existing automated coaching systems.
2. **SpeakLab decision it could influence:** Useful as a landscape map for what
   dimensions the field considers standard (matches M7A's own "Coaching Dimensions"
   list in `conclusions.md` section 2 reasonably well) — no specific numeric finding to
   adopt.
3. **Assumption:** None specific — this is a secondary/survey source, not a primary
   result.
4. **Baseline / experiment / metrics:** Not applicable — a survey paper, not an
   experiment to reproduce.
5. **Cost/compute:** N/A.
6. **Risks:** Snippet-only verification — do not cite specific claims from this paper
   in `conclusions.md` or a decision-log entry without reading the full paper first.
7. **Decision: Defer** — read in full before citing further; useful as a pointer to
   "what does the field consider the standard dimension set," already roughly matched
   by M7A's independently-derived dimension list.

### A3. Commercial prior art (Orai, Yoodli, Ummo, Microsoft Presenter Coach)

Not academic papers — named in a search result as existing commercial speech-coaching
apps offering pace/articulation/filler feedback. **Not evaluated here** (no
access/trial performed, no findings to report) — noted only as competitive-landscape
context. **Decision: not applicable to this review's template** (no paper, no
reproducible finding); worth a separate, explicitly-scoped competitive review if
useful later, not folded into M7 research evidence.

---

## Category B — Relevant methodology that may transfer to M7

Papers about LLM-as-judge, rubric-based evaluation, feedback quality, and
feedback-driven improvement **in other domains** (writing, essay grading, general NLG).
Per this milestone's explicit instruction, **no finding here is assumed to transfer to
speaking feedback automatically** — each entry states the transfer assumption
separately.

### B1. AI-Mediated Feedback Improves Student Revisions: A Randomized Trial with FeedbackWriter

**Source:** arXiv 2602.16820 [fetched]

1. **Actual finding:** Randomized controlled trial, **N=354** students in a large
   undergraduate economics course, 1,366 essays graded. Students randomly assigned to
   AI-mediated feedback vs. human (TA) feedback. AI-mediated-feedback group produced
   **significantly higher-quality revisions** than the human-feedback control group,
   with gains increasing as TAs adopted more AI suggestions.
2. **SpeakLab decision it could influence:** This is the closest real evidence found
   for the task brief's "feedback that improves a second attempt" priority area —
   directly relevant to whether SpeakLab's retry-goal mechanism (FR-15/FR-16) is a
   sound product bet at all.
3. **Assumption that would need to transfer:** Written-essay revision (same student,
   asynchronous, text-only, TA-mediated AI suggestions used by a human grader) is a
   different task from a solo speaker re-recording a ~60s impromptu response
   immediately after reading a retry goal, with no human in the loop. Whether feedback
   quality gains observed in *text revision with a human-in-the-loop mediator*
   transfer to *unmediated, same-session spoken retry* is an open, untested
   assumption — this paper does not show it, it only shows the writing-domain
   analog works.
4. **Baseline:** SpeakLab has no existing measurement of retry improvement at all yet
   (FR-17's Comparison screen is spec'd but not populated with real coaching-driven
   retries in any milestone through M7A).
5. **Small reproducible experiment:** Once a real coach exists (M7B/M8): for a small
   set of practicers, compare attempt-2 metrics (WPM delta, pause-count delta,
   qualitative structure improvement) between a retry-goal-shown condition and a
   no-retry-goal-shown condition on the same prompt. Report the deltas transparently;
   **do not pre-commit to a "success" threshold** — this project has no prior data to
   justify one, and the FeedbackWriter paper's own effect size doesn't transfer
   directly (different task, different modality, different N feasible for SpeakLab's
   single-user local context).
6. **Metrics:** Attempt-1-vs-attempt-2 deltas SpeakLab already computes deterministically
   (`docs/requirements.md` FR-17) — WPM, pause count, filler count — plus a qualitative
   read of whether the retry goal was visibly acted on (e.g., did the flagged structural
   gap improve). No new metric needs to be invented for this experiment.
7. **Cost/compute:** Requires a working coaching call (Gemini/Ollama) plus several real
   two-attempt sessions — meaningfully more setup than a text-only evaluation.
8. **Risks:** SpeakLab's realistic sample size for this kind of study is far smaller
   than N=354 (single local-user product, no user base) — any result would be
   illustrative, not statistically powered; must not be reported with a confidence
   claim the sample can't support (consistent with the project's existing "8 examples
   is not enough" precedent for filler detection, DEC-015).
9. **Decision: Defer.** Directly relevant, worth designing the experiment now (done
   above), but cannot run until a real coaching call exists (M7B/M8) — logged as a
   forward-looking experiment design, not adopted as a claim about SpeakLab today.

**Secondary, lower-confidence note:** a search result (Hechinger Report, journalism
covering unspecified underlying research — **not independently fetched/verified**)
suggested that a single dose of AI writing feedback did not improve performance on a
*fresh* topic/task without repeated feedback rounds — i.e. gains may be
task-specific, not skill-transferring. If real, this would matter for SpeakLab's
same-prompt-retry design (FR-16 already scopes retry to the *same* prompt, which is
consistent with this caution) but this secondary source is too weak to cite as
evidence — flagged here only as a reason to keep same-prompt retry as the V1 design
rather than generalizing retry goals across prompts.

### B2. FeedEval: Pedagogically Aligned Evaluation of LLM-Generated Essay Feedback

**Source:** arXiv 2601.04574 [fetched]

1. **Actual finding:** Introduces an evaluation framework scoring LLM-generated essay
   feedback on **specificity, actionability, faithfulness, and rubric alignment** —
   evaluated by trained human annotators, with inter-rater agreement (Cohen's kappa)
   reported, comparing multiple LLMs' feedback-generation quality against these
   pedagogically-grounded dimensions.
2. **SpeakLab decision it could influence:** Strong methodology match —
   `evaluation_rubric.md`'s dimensions B (Specificity) and C (Actionability) are
   near-identical in spirit to this paper's framework, independently arrived at. This
   is validating precedent for the *shape* of SpeakLab's rubric, not new content to
   copy in.
3. **Assumption that would need to transfer:** Essay feedback is evaluated by trained
   human annotators with measured inter-rater agreement; SpeakLab's M7A self-scoring
   (`results/*.json`) has neither multiple raters nor an agreement statistic — a
   materially weaker evaluation setup than this paper's, which this review should not
   obscure.
4. **Baseline:** SpeakLab's own rubric (`evaluation_rubric.md`), already
   independently designed before this paper was found.
5. **Small reproducible experiment:** If/when a second human rater is available,
   re-score a subset of `results/*.json` outputs independently and compute agreement
   (e.g. Cohen's kappa or simple percent-agreement) against the original self-scores —
   report the number, do not pre-declare what counts as "good enough" agreement absent
   a stated rationale.
6. **Metrics:** Cohen's kappa (or simpler percent agreement, justified by small N) is
   the established metric for inter-rater reliability in this exact literature — this
   is an *established benchmark practice*, not an invented threshold, and applies to
   *whether raters agree*, not to any pass/fail bar for coaching quality itself.
7. **Cost/compute:** Human annotator time only (no model compute).
8. **Risks:** SpeakLab currently has one evaluator (the agent that authored both the
   outputs and the scores) — see B4 below on why this specific setup is a documented
   bias risk, not just a small-sample limitation.
9. **Decision: Adopt the dimension framework (already effectively done —
   `evaluation_rubric.md` independently matches it); defer the inter-rater-agreement
   methodology** until a second rater is actually available.

### B3. G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment

**Source:** arXiv 2303.16634 (Liu et al., EMNLP 2023) [snippet, well-established/highly-cited — 549 citations per one indexed source]

1. **Actual finding:** LLM-as-judge with chain-of-thought reasoning and a
   form-filling paradigm (generate evaluation steps, then score against them).
   G-Eval with GPT-4 achieved **Spearman correlation of 0.514 with human judgment on a
   summarization task** — this specific number is this paper's own reported result on
   its own task (text summarization), not a general-purpose benchmark for any NLG task.
2. **SpeakLab decision it could influence:** Methodological precedent for **how** an
   LLM might later be used to *evaluate* coaching outputs at scale (a future automated
   grader), and for the general "generate evaluation criteria, then score against them"
   pattern — loosely similar in spirit to Approach C's technique-eligibility checking,
   though G-Eval evaluates NLG quality, not coaching-specific grounding/safety.
3. **Assumption that would need to transfer:** The 0.514 correlation is
   **summarization-specific** — reusing that number as an expectation for a coaching-
   quality judge (a different task, different criteria, no comparable human-alignment
   study for coaching feedback) would be exactly the "code grading/writing result
   automatically applies to speaking feedback" error this milestone's instruction
   explicitly prohibits. It is cited here as a methodology precedent only, with its
   number attached strictly to its own task.
4. **Baseline:** None currently for SpeakLab — no automated coaching-quality judge
   exists yet; M7A's rubric is scored manually (currently, by the same agent that
   generated the output — see B4).
5. **Small reproducible experiment:** Once real coaching outputs exist, try a G-Eval-
   style CoT-based LLM judge against `evaluation_rubric.md`'s 8 dimensions, and compare
   its scores against human self-scores on the same outputs — report the agreement
   level transparently. No target correlation is declared in advance; this project has
   no basis (no prior SpeakLab-specific study) to expect G-Eval's 0.514 or any other
   number to hold on a structurally different task.
6. **Metrics:** Spearman/Pearson correlation between LLM-judge score and human score is
   an established metric *for comparing two raters*, reused here for that narrow
   purpose only — not repurposed as a coaching-quality pass/fail bar.
7. **Cost/compute:** One additional LLM call per output to be judged, per dimension
   or per full rubric — modest but non-zero added cost if adopted for scaled
   evaluation.
8. **Risks:** LLM judges are known (per B4/B5/B6 below) to have self-preference bias
   and imperfect reliability on nuanced/subjective content — using an LLM judge to
   validate SpeakLab's own coach without human spot-checking risks a closed loop where
   errors go undetected.
9. **Decision: Defer.** Not needed for M7A's own design work; worth revisiting as a
   *scaling* mechanism once enough real coaching output volume exists that manual
   rubric scoring becomes impractical — not adopted now.

### B4. Self-Preference Bias in Rubric-Based Evaluation of Large Language Models

**Source:** arXiv 2604.06996 [fetched]

1. **Actual finding:** LLM judges systematically favor outputs produced by themselves
   or models in their own family. On benchmarks with **verifiable rubrics**, judges
   were "more than 50% more likely to incorrectly mark [a rubric item] as satisfied
   when the output is their own." On subjective benchmarks, self-preference caused
   score disparities up to 10 points. Ensembling multiple judges reduces but does not
   eliminate the bias.
2. **SpeakLab decision it could influence — direct, urgent relevance to M7A's own
   evidence:** `results/*.json`'s rubric self-scores were produced by **the same agent
   that authored the outputs being scored** — exactly the setup this paper identifies
   as biased. This is not a hypothetical transfer question; it applies to work already
   done in this milestone.
3. **Assumption that would need to transfer:** This paper studies LLM judges scoring
   LLM outputs on general benchmarks; SpeakLab's self-scoring was a single agent
   session reasoning about its own just-written text, a closely analogous but not
   identical setup (no separate "judge model," one continuous reasoning process). The
   direction of the risk (inflated self-scores) plausibly transfers; the *magnitude*
   (>50%, up to 10 points) is this paper's own benchmark-specific number and should not
   be quoted as SpeakLab's own bias magnitude.
4. **Baseline:** M7A's existing self-scores in `results/*.json`, now understood as a
   likely-optimistic baseline, not a neutral one.
5. **Small reproducible experiment:** Re-score the same 18 illustrative outputs
   (6 cases × 3 approaches, already in `results/`) with a fresh, independent read —
   ideally by a different agent/session with no authorship stake in the outputs, or by
   a human — and report the score deltas transparently, dimension by dimension. No
   threshold is declared for "how much disagreement is acceptable" in advance.
6. **Metrics:** Simple score deltas per dimension (original self-score minus
   independent re-score) — descriptive, not hypothesis-tested at this sample size.
7. **Cost/compute:** One additional read-through pass; no new model infrastructure
   needed, since it can be done with a fresh Claude session/conversation with no
   memory of authoring the originals, or a human reviewer.
8. **Risks:** If left uncorrected, M7A's illustrative "Approach C wins" conclusion
   (`results/summary.md`) could itself be inflated by the same authoring agent scoring
   its own preferred, most-carefully-constructed condition (Approach C) most
   favorably — a direct, specific version of this paper's finding, not just an
   abstract concern.
9. **Decision: Adopt as an explicit limitation, immediately.** This document adds
   self-preference bias to `conclusions.md`'s limitations list (see "Correction applied
   to conclusions.md" below) and recommends an independent re-scoring pass before any
   of M7A's illustrative comparison is treated as more than a design sketch.

### B5. The Consistency Dilemma in LLMs: Generator-Evaluator Agreement and Vulnerability to Mistakes

**Source:** arXiv 2606.30653 [fetched]

1. **Actual finding:** Higher generator-evaluator self-consistency (a model applying
   concepts the same way when generating and later evaluating) correlates with
   **increased**, not decreased, vulnerability to specific validated mistakes in a
   clinical setting — i.e. self-consistency is not a proxy for correctness, and can
   mask confidently-repeated errors.
2. **SpeakLab decision it could influence:** Directly cautions against treating
   "the coach gives the same answer every time" (EXP-M7-004's planned consistency check,
   `experiment_plan.md`) as sufficient evidence of quality on its own — consistency and
   groundedness/correctness must be measured and reported as **separate** dimensions,
   never conflated into one signal.
3. **Assumption that would need to transfer:** This finding is from a clinical-
   decision-making domain; SpeakLab's failure mode (a wrong or unsupported coaching
   claim repeated consistently) is structurally analogous but not measured in the
   speaking-coaching domain by this paper.
4. **Baseline:** `failure_taxonomy.md`'s "inconsistent advice across identical inputs"
   entry currently frames consistency as purely good; this paper is a reason to add the
   corollary — consistently wrong is also a named risk, not just consistently variable.
5. **Small reproducible experiment:** When EXP-M7-004 (consistency, currently deferred
   per `experiment_plan.md`) becomes runnable, score each repeated run independently on
   `evaluation_rubric.md`'s Groundedness dimension *before* comparing the runs for
   agreement with each other — never treat inter-run agreement alone as a quality
   signal.
6. **Metrics:** Variance/agreement across repeated runs is one metric; Groundedness
   score per run is a separate, independently-required metric — the paper's finding is
   specifically that the first cannot substitute for the second.
7. **Cost/compute:** No additional cost beyond EXP-M7-004's already-planned repeated
   calls — this is a scoring-methodology correction, not new experimentation.
8. **Risks:** Without this correction, a future consistency measurement could be
   misread as a quality green light on its own.
9. **Decision: Adopt as a correction to EXP-M7-004's design** — update
   `experiment_plan.md` to require groundedness scoring alongside any future
   consistency measurement (done below, "Corrections applied").

### B6. How Trustworthy Are LLM-as-Judge Ratings for Interpretive Responses?

**Source:** arXiv 2604.00008 [fetched]

1. **Actual finding:** LLM-as-judge scores track broad directional trends versus human
   evaluation at the model level, but **diverge substantially in score magnitude**;
   faithfulness/correctness judgments showed systematic misalignment at the individual-
   excerpt level, especially for **non-literal, nuanced interpretations**. Recommends
   LLM judges for screening/elimination, not as a substitute for human judgment on
   qualitative, interpretive content.
2. **SpeakLab decision it could influence:** Directly cautions against relying solely
   on an LLM judge (e.g. a future G-Eval-style automated grader, B3) to certify
   coaching quality on the *interpretive* dimensions (Structure, Clarity of Thought) —
   exactly the Tier-4 dimensions M7A's own evidence hierarchy (`conclusions.md`
   section 5) already flags as generative interpretation, not deterministic fact.
3. **Assumption that would need to transfer:** This paper studies interpretive
   *response quality* broadly (e.g. reading-comprehension-style interpretation), not
   speaking-coaching output specifically — the caution about non-literal/nuanced
   content plausibly transfers to coaching's Structure/Clarity claims (also
   interpretive), but is not itself evidence about coaching feedback.
4. **Baseline:** None — SpeakLab has no automated judge yet.
5. **Small reproducible experiment:** If an LLM judge is ever adopted (per B3), reserve
   final human review specifically for Tier-4 (Structure/Clarity) claims, using the
   judge only to pre-screen Tier-1-3-grounded claims (which are closer to
   "verifiable," where B4's own findings suggest judges are still imperfect but
   somewhat more reliable than on subjective content).
6. **Metrics:** Same directional-trend-vs-magnitude distinction this paper uses — worth
   adopting as a reporting convention (report both, don't collapse to one number).
7. **Cost/compute:** N/A — a reporting-convention adoption, not a new experiment.
8. **Risks:** None beyond B3's — reinforces the same caution.
9. **Decision: Adopt as a design principle** — any future automated coaching-quality
   judge must be scoped to screening, with human review retained for Tier-4 claims,
   consistent with `docs/ai-boundaries.md`'s existing human-responsibility framing
   ("interpreting evaluation evidence" stays a human responsibility).

### B7. Human vs. AI/teacher feedback comparisons — grouped, lower confidence

**Sources, all [snippet only]:** "LLMs Do Not Grade Essays Like Humans" (arXiv
2603.23714), "Frontiers: AI vs. teacher feedback on EFL argumentative writing" (2025),
"Generative AI offers more, but students revise less" (Springer/IJETHE), "A Comparative
Study of Technical Writing Feedback Quality: LLMs, SLMs, and Humans" (arXiv 2601.11541),
"Comparison of Scoring Rationales Between LLMs and Human Raters" (arXiv 2509.23412).

1. **Actual finding (aggregate, low confidence):** Mixed picture — LLM
   feedback/grading partially aligns with human raters (better on surface-level
   features, weaker at score extremes and fine-grained distinctions); one source
   reports **students revise less** when AI feedback is easily available, despite
   feedback quality being comparable or higher — a behavioral/engagement finding
   distinct from feedback-quality itself.
2. **SpeakLab decision it could influence:** The "students revise less with AI
   feedback" pattern, if it holds, is a genuine product-design risk for SpeakLab's
   retry loop (does easy, always-available coaching reduce a practicer's own effort to
   interpret their own transcript?) — worth naming as a hypothesis, not adopting as
   fact given the confidence level here.
3. **Assumption:** Untested for a solo spoken-retry context; these are classroom
   writing-revision studies with a teacher/instructor context SpeakLab doesn't have
   (no instructor, no grade stakes).
4-8. **Baseline/experiment/metrics/cost/risks:** Not developed to the same depth as
   B1/B2/B4-B6 given snippet-only verification — flagged for full-text reading before
   further use, not for adoption now.
9. **Decision: Defer, verify further before use.** The "revise less" pattern is worth
   keeping in mind (a possible risk register candidate, once verified) but should not
   be cited in a SpeakLab decision until read in full.

### B8. Rubric-generation/decomposition methodology — grouped, lower confidence

**Sources, all [snippet only]:** "Rethinking Rubric Generation for Improving LLM Judge
and Reward Modeling" (arXiv 2602.05125), "Feedback-to-Rubrics: Can We Learn Expert
Criteria from Inline Comments?" (arXiv 2605.29857), "LLM-as-Judge in Education:
Curriculum-Grounded Marking Pipeline" (arXiv 2606.17507).

1. **Actual finding (low confidence):** Decomposing coarse rubric items into
   finer-grained subpoints improves both judge accuracy and reward-model usefulness;
   inline expert comments can be mined to derive rubric criteria; curriculum-grounded
   pipelines can structure LLM marking against explicit criteria in educational
   settings.
2. **SpeakLab decision it could influence:** A future refinement direction for
   `technique_library.md`'s eligibility rules (already somewhat "decomposed" — each
   technique has its own evidence bar and exclusion clause) — this is directional
   validation of that structure's shape, not a new requirement.
3-9. **Not developed further** given snippet-only verification. **Decision: Defer,
   read in full before adopting any specific decomposition method.**

---

## Category C — Relevant to future articulation/pronunciation milestones

Per this milestone's explicit instruction, pronunciation-specific work is a **future**
research track and does **not** change M7's coaching architecture — SpeakLab has no
pronunciation-scoring capability, no phoneme-level evidence, and no read-aloud mode in
V1 (`docs/requirements.md` "V1 Scope — Later": "Pronunciation analysis"). Logged here
for the future milestone, not acted on now.

### C1. speechocean762: An Open-Source Non-Native English Speech Corpus for Pronunciation Assessment

**Source:** arXiv 2104.01378 [fetched]

1. **Actual finding:** 5,000 English utterances from 250 non-native (native Chinese)
   speakers, half of them children. Five expert annotators scored each utterance at
   **sentence level** (accuracy, fluency, prosody, completeness, overall),
   **word level** (accuracy, stress, overall), and **phoneme level** (0-2 accuracy
   score per phoneme). Free for commercial/non-commercial use via OpenSLR; a Kaldi
   baseline system is published alongside it.
2. **SpeakLab decision it could influence:** **None for M7/V1.** This dataset requires
   a read-aloud/reference-text practice mode and phoneme-level acoustic modeling —
   both explicitly out of V1 scope (`docs/requirements.md`). Relevant only to a future
   articulation/pronunciation milestone (M12+ territory, alongside the already-planned
   CrisperWhisper evaluation).
3. **Assumption that would need to transfer:** Would require SpeakLab to build a
   reference-text comparison mode and phoneme-level acoustic scoring — currently
   nothing in the architecture (`docs/context.md`) supports either.
4-8. **Baseline/experiment/metrics/cost/risks:** Not developed — out of scope for this
   milestone.
9. **Decision: Defer to a future articulation/pronunciation milestone, explicitly not
   M7.** No action in M7A/M7B/M8.

### C2. Other pronunciation-assessment papers found (grouped, snippet-only)

"Transformer-Based Multi-Aspect Multi-Granularity Non-Native English Speaker
Pronunciation Assessment" (arXiv 2205.03432), "A Finetuned SpeechLLM for Joint
Multi-Granular L2 Assessment and Natural-Language Rationales" (arXiv 2606.09470),
"Exploring the Potential of Large Multimodal Models as Effective Alternatives for
Pronunciation Assessment" (arXiv 2503.11229), "Leveraging phone-level
linguistic-acoustic similarity for utterance-level pronunciation scoring" (arXiv
2302.10444). All pronunciation-scoring methodology papers, all **Category C — future
track only**, none read in full. Worth revisiting as a reading list when a
pronunciation milestone is actually scoped.

---

## Category D — Not currently useful

Papers surfaced by the searches that are real but too domain-distant, too
infrastructure-focused, or too tangential to inform M7's coaching design. Listed so
they're not silently dropped, per this project's "hide negative/irrelevant findings"
aversion (`docs/methodology.md`).

- **"Self-Logical Consistency Assessment of LLMs for Patient Feedback Classification"**
  (medRxiv) — a *classification* consistency study (categorizing patient feedback
  text), not feedback *generation*; clinical domain. Different task shape from
  SpeakLab's coach.
- **"ConAIR: Consistency-Augmented Iterative Interaction Framework... Code Generation"**
  (arXiv 2411.15587) — code-generation domain. Per this milestone's explicit
  instruction, a code-generation-domain finding is not assumed to transfer to speaking
  feedback; not pursued further.
- **"Evaluating Small Open LLMs for Medical Question Answering"** (arXiv 2604.10535) —
  medical QA domain, unrelated task shape.
- **"YESciEval: Robust LLM-as-a-Judge for Scientific Question Answering"** (arXiv
  2505.14279) — scientific-QA-specific judge design, not general enough to transfer.
- **"Open Rubric System: Scaling Reinforcement Learning with Pairwise Adaptive Rubric"**
  (arXiv 2602.14069) — RL training infrastructure for reward modeling, not applicable
  to SpeakLab's non-RL coaching pipeline.
- **"Robustness in Large Language Models: A Survey of Mitigation Strategies"** (arXiv
  2505.18658) — general LLM robustness survey, no coaching/feedback/education-specific
  content found in the snippet.
- **"HoWToBench," "SLMEval," "CaLM," "Context-Fidelity Boosting," "Auditing Proprietary
  Alignment," "Citation-Grounded Code Comprehension," "Progressive Training for
  Explainable Citation-Grounded Dialogue," "Grounded Optimization... Personal Document
  Rewriting"** — general NLG-evaluation, RAG-grounding, or code/dialogue-specific
  infrastructure papers surfaced by the "grounded generation" search. None specific to
  educational feedback, speaking coaching, or rubric-based quality evaluation closely
  enough to warrant a full template entry; the general "structured output + retrieval +
  abstain when unsure" pattern they collectively describe is already reflected in
  M7A's existing design (evidence-gated technique selection, abstention policy) without
  needing to cite any one of these specifically.

---

## Corrections applied to existing M7A documents as a result of this review

1. **`conclusions.md` "Limitations" (section 19)** should add: M7A's illustrative
   rubric self-scores (`results/*.json`) were produced by the same agent that authored
   the outputs being scored — a documented bias pattern (B4, self-preference bias),
   not merely a small-sample limitation. An independent re-scoring pass (by a different
   session or a human) is recommended before treating `results/summary.md`'s
   "Approach C wins" pattern as more than a design sketch.
2. **`experiment_plan.md` EXP-M7-004 (consistency)** should require Groundedness
   scoring on each individual repeated run, not only inter-run agreement — per B5's
   finding that self-consistency does not imply correctness and can mask confidently-
   repeated errors.
3. **No numeric success threshold is introduced anywhere in `experiment_plan.md` or
   `evaluation_rubric.md`** as a result of this review — consistent with this
   milestone's explicit correction. Where a metric from the literature is genuinely
   reusable (e.g. Cohen's kappa for inter-rater agreement, B2), it is adopted as a
   **measurement method**, not as a **pass/fail bar**.

These corrections are recorded here rather than silently rewriting the earlier
documents' prose, so the correction itself stays visible (matching this project's
existing practice of correcting-in-place with a visible note, e.g.
`experiments/m6_speech_metrics/conclusions.md`'s "Important correction" pattern for
DEC-014).

---

## Sources

- [LLM-as-Judge in Education: A Curriculum-Grounded Marking Pipeline](https://arxiv.org/html/2606.17507)
- [Rethinking Rubric Generation for Improving LLM Judge and Reward Modeling for Open-ended Tasks](https://arxiv.org/pdf/2602.05125)
- [How Trustworthy Are LLM-as-Judge Ratings for Interpretive Responses?](https://arxiv.org/abs/2604.00008)
- [Feedback-to-Rubrics: Can We Learn Expert Criteria from Inline Comments?](https://arxiv.org/pdf/2605.29857)
- [Self-Preference Bias in Rubric-Based Evaluation of Large Language Models](https://arxiv.org/abs/2604.06996)
- [Probing Experts' Perspectives on AI-Assisted Public Speaking Training](https://arxiv.org/abs/2507.07930)
- [A Survey of Automated Presentation Coaching: Systems, Methods, and Open Challenges](https://arxiv.org/html/2606.27380)
- [G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment](https://arxiv.org/abs/2303.16634)
- [AI-Mediated Feedback Improves Student Revisions: A Randomized Trial with FeedbackWriter](https://arxiv.org/abs/2602.16820)
- [FeedEval: Pedagogically Aligned Evaluation of LLM-Generated Essay Feedback](https://arxiv.org/pdf/2601.04574)
- [The Consistency Dilemma in LLMs: Generator-Evaluator Agreement and Vulnerability to Mistakes](https://arxiv.org/abs/2606.30653)
- [speechocean762: An Open-Source Non-native English Speech Corpus For Pronunciation Assessment](https://arxiv.org/abs/2104.01378)
- [Transformer-Based Multi-Aspect Multi-Granularity Non-Native English Speaker Pronunciation Assessment](https://arxiv.org/pdf/2205.03432)
- [A Finetuned SpeechLLM for Joint Multi-Granular L2 Assessment and Natural-Language Rationales](https://arxiv.org/pdf/2606.09470)
- [Exploring the Potential of Large Multimodal Models as Effective Alternatives for Pronunciation Assessment](https://arxiv.org/pdf/2503.11229)
- [LLMs Do Not Grade Essays Like Humans](https://arxiv.org/html/2603.23714v1)
- [Frontiers: AI vs. teacher feedback on EFL argumentative writing](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2025.1614673/full)
- [Generative AI offers more, but students revise less](https://link.springer.com/article/10.1186/s41239-026-00579-9)
- [A Comparative Study of Technical Writing Feedback Quality: LLMs, SLMs, and Humans](https://arxiv.org/pdf/2601.11541)
- [Comparison of Scoring Rationales Between Large Language Models and Human Raters](https://arxiv.org/pdf/2509.23412)
- [A researcher's view on using AI to become a better writer (Hechinger Report)](https://hechingerreport.org/proof-points-ai-writing-meyer/)
