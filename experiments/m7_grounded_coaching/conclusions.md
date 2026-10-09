# M7A Conclusions — Grounded Coaching Design & Evaluation

**Status: design and evaluation milestone.** No production coaching code exists as a
result of this document. Nothing here is wired into `backend/` or `frontend/`. This is
the M7A final report, structured against the task brief's 23-item "Final Output" list.

---

## 1. Coaching product definition

The V1 coach's output is exactly five parts, in this order, matching the task brief's
required shape:

1. **What worked** — one genuine strength, grounded in evidence.
2. **Biggest improvement opportunity** — exactly one, not a list.
3. **Evidence** — the specific transcript quote or metric value the improvement claim
   traces to.
4. **Recommended technique** — one entry from `technique_library.md`, or none if no
   technique's evidence bar is met.
5. **One retry goal** — a single, concrete, same-prompt-achievable action.

The coach prioritizes one main improvement over an exhaustive list, per
`docs/requirements.md` FR-15 ("exactly one concrete retry goal") — this is a product
requirement already decided, not a new M7A invention; M7A designs *how* the coach
satisfies it.

## 2. Coaching dimensions

Of the five dimensions in the task brief (Delivery, Clarity of Thought, Structure,
Language, Audience Fit), V1's actually-supportable dimensions are:

| Dimension | V1 support | Why |
|---|---|---|
| **Delivery** (pace, pauses, fillers) | **Supported** | Directly backed by `words_per_minute` (Tier 2), `long_pauses` (Tier 2), `fillers` (Tier 3) — all already shipped in M6B. |
| **Clarity of thought** (unfinished ideas, wandering, abrupt transitions) | **Supported, with hedging** | Backed by transcript text (Tier 4 interpretation) — usable, but every claim must hedge for imperfect STT (`docs/ai-boundaries.md`). |
| **Structure** (opening, main point, example, conclusion, focus) | **Supported, with hedging** | Same basis as clarity — transcript-derived, Tier 4, TECH-003 is the flagship technique for this dimension. |
| **Language** (grammar, phrasing, vocabulary variety, conciseness) | **Partially supported, narrow** | No deterministic lexical-variety or grammar metric exists. Only claims the coach can literally quote (repeated verbatim words/phrases, per TECH-006) are supportable; general "your grammar needs work" is not — no evidence pathway exists for grammar correctness at all. |
| **Audience fit** (tone, jargon, detail level, listener clarity) | **Not supported in V1** | V1 prompts (`docs/requirements.md`) do not specify an intended audience — there is no evidence field this dimension could ground itself in. Deferred to TECH-008 and future audience-aware prompt design. |

Not every dimension is evaluated on every attempt — the coach only speaks to a
dimension when that attempt's evidence actually supports a claim in it (see "Evidence
hierarchy" and "Abstention policy" below).

## 3. Toastmasters-role mapping

| Role | Maps to | Decision |
|---|---|---|
| Timer | Duration / pace (WPM) | **Now** — folded into the unified coach's Delivery dimension, not a separate persona. |
| Ah-Counter | Fillers / verbal habits | **Now** — folded into Delivery, gated by TECH-004's high evidence bar. |
| Grammarian | Grammar / wording / vocabulary | **Later** — no grammar-correctness evidence exists yet; only the narrow quoted-repetition case (TECH-006) is in scope now. |
| Evaluator | Overall feedback / strongest point / main improvement / retry goal | **Now** — this *is* the V1 coach's core job. |
| Structure Coach | Organization and flow | **Now** — folded into Clarity of Thought / Structure via TECH-002/TECH-003. |

**Decision: one unified coach for V1**, not separate agents per role. The task brief's
own instruction ("prefer one unified coach unless experiments justify multiple
specialist roles") is followed directly — nothing in this milestone's evidence (which
dimensions are supportable, how small the V1 evidence surface is) justifies the added
complexity of multiple LLM calls/personas. A future Grammarian-equivalent role becomes
relevant only if a grammar/style metric is ever added (a metrics-layer decision, not a
coaching-layer one).

## 4. Technique library

See `technique_library.md` for the full TECH-001–008 entries. Summary: TECH-001, 002,
003, 004, and 006 are eligible for the V1 coach today; TECH-005, 007, 008 are
documented placeholders for future practice modes with no current evidence pathway.

## 5. Evidence hierarchy

| Tier | Contents | Coach may... |
|---|---|---|
| **Tier 1 — deterministic/high-confidence** | Decoded recording duration | State directly, no hedge. |
| **Tier 2 — approximate derived metrics** | Word count, WPM, pause flags | State with "approximate"/"detected" phrasing; never as an exact count/duration. |
| **Tier 3 — experimental** | Fillers | State only with "experimental" phrasing and a raised evidence bar (see below); never as ground truth. |
| **Tier 4 — generative interpretation** | Structure, clarity, language feedback, coaching recommendations | Generate only when grounded in a Tier 1-3 fact or a directly quoted transcript span; must never outrank the certainty of the tier it's derived from. |

This mirrors `experiments/m6_speech_metrics/conclusions.md` Step 14's classification
exactly (duration=exact, word count/WPM/pauses=approximate, fillers=experimental) — M7A
does not re-derive or change any metric's tier, only defines how the LLM may speak
about each tier.

## 6. Evidence-to-technique policy

- **High WPM alone** may support TECH-001 (Deliberate Pause); must never imply
  nervousness/anxiety (an unrelated inference the WPM value does not license).
- **Fillers**: experimental evidence only; phrased cautiously ("detected," never "you
  used exactly N fillers"); **one or two detections must not automatically trigger
  TECH-004 or make fillers the main improvement** — the evidence bar is 3+ detections
  (see `technique_library.md` TECH-004).
- **Pause events**: approximate word-gap evidence only; must never claim an exact
  acoustic pause duration (DEC-014's explicit correction); may support TECH-002, but
  must never support recommending *more* pausing (TECH-001) on an attempt that already
  has detected pauses (see `failure_taxonomy.md`).
- **Transcript**: may support structure/clarity/language interpretation, always hedged
  as imperfect STT output — claims about restarts/fragments/wandering must be phrased
  as "the transcript shows..." not "you said...", per TECH-002's exclusion clause.
- **No evidence** (near-empty transcript, no detections, metric unavailable): the coach
  must abstain rather than invent criticism — see section 8.

## 7. Abstention policy

The coach outputs `abstained: true` with an `abstention_reason` (instead of
strength/main_improvement/technique/retry_goal) when:

- Transcript is empty or near-empty (word count 0, or below a minimum word threshold
  for any structural claim to be meaningful).
- Transcript is obviously STT-corrupted (repeated word-level duplication patterns
  characteristic of a decode/ASR artifact, not real speech — see CASE-12 in
  `cases/manifest.json` for the design test case).
- Near-silence (duration present, but no words — matches `docs/context.md` "No
  speech detected," which already skips coaching entirely at the product level; this
  policy is the coaching-layer mirror of that existing rule).
- Insufficient speech duration for any pacing/structure claim to be meaningful (e.g.
  a few words at most).
- A metric the coach would need is unavailable (`words_per_minute: null`,
  `metrics.status: "failed"`).
- Evidence conflicts in a way no single main improvement can be chosen responsibly
  (rare; prefer picking the clearer signal per the technique library's evidence bars
  first — see CASE-16's fillers-vs-pauses resolution in `results/
  approach_c_technique_library.json` — and abstain only if no technique's bar is met at
  all).
- The only available signal is experimental and below its raised evidence bar (e.g.
  exactly one filler detection and nothing else notable — in this specific case the
  coach still names the genuine strength it found, per CASE-15's result, rather than a
  full abstention; full abstention is reserved for cases with *no* usable evidence at
  all, not merely a *thin* main-improvement case).

**Not implemented in M7A** — this is policy definition only, per the task brief's
explicit "do not implement the abstention system yet."

## 8. (see 7 — the brief's items 7 and 8 both concern abstention; consolidated above per the task's own numbering, which lists abstention rules as item 8 and the evidence-to-technique rules as item 6/7)

## 9. Approaches compared

Approach A (generic), B (evidence-grounded structured), C (structured + curated
technique library) — see `experiment_plan.md` EXP-M7-001/002/003 and `results/
summary.md` for the full illustrative comparison. **Approach C is the leading
architecture hypothesis** coming out of this illustrative comparison, and the
candidate for real-model validation at M7A-2 (see section 16 below) — it is **not** an
experimentally proven winner. No live model was run for any approach in M7A.

## 10. Model/provider options considered

| Option | Quality | Grounding | Structured-output reliability | Latency | Cost | Privacy | Complexity | Reproducibility |
|---|---|---|---|---|---|---|---|---|
| **Rule-based only** (no LLM, templated sentences filled from metric values) | Low — cannot produce structure/clarity feedback at all (Tier 4 dimensions need generative interpretation) | Perfect (nothing to hallucinate) | N/A | Fastest | Free | Fully local | Lowest | Perfectly reproducible |
| **Local LLM via Ollama** | Unknown — **not evaluated in this environment; no Ollama installation exists here** (`which ollama` found nothing) | Depends on model + prompt discipline | Depends on model's instruction-following/JSON-mode support | Depends on local hardware, likely acceptable for a ~60s-latency-tolerant flow | Free after setup | Fully local — strongest privacy option, keeps `docs/privacy.md`'s local-first framing intact even for coaching | Adds a local model-serving dependency | Reproducible if model/version pinned |
| **Gemini free/low-cost tier** | Unknown — **not tested here**; current pricing/quota/model availability requires up-to-date verification at implementation time, not a guess made now | Depends on prompt discipline (this milestone's structured contract is provider-agnostic) | Gemini's structured-output/JSON-mode support would need direct verification when implemented | Network round-trip, adds latency the local pipeline doesn't have today | Requires current verification — do not guess a number | Sends structured evidence (never raw audio) off-machine — a real, if scoped, privacy change (RISK-005) | Requires `GEMINI_API_KEY`, network handling, retry/failure UX (already scoped in `docs/context.md`) | Reproducibility depends on provider-side model versioning, outside this project's control |
| **Another local/free option** (e.g. a different open-weights model) | Not evaluated — none was available in this environment either | — | — | — | Free | Fully local | Similar to Ollama | Depends on option |

**This table intentionally reports "not evaluated" rather than inventing quality/cost
numbers** — per the project's explicit research-integrity rule (`docs/methodology.md`) against fabricating benchmark numbers.
Pricing/API availability for Gemini specifically requires current verification at
implementation time (M7B/M8), not a number guessed here from training-time knowledge
that may already be stale.

**Why AI at all, compared to the non-LLM alternatives** — see section 18.

## 11. Evaluation-set design

16 synthetic/fixture cases in `cases/manifest.json`, covering every category the task
brief requested (strong structure, high/low WPM, fillers/no fillers, long pauses,
wandering answer, weak/strong conclusion, fragmented thought, concise clear answer,
ambiguous transcript, near-silence, conflicting signals, single-filler-only) plus one
additional real-human-grounded case. Two cases (CASE-13, CASE-16) reuse already-public,
already-committed real-human evidence from `experiments/m6_speech_metrics/
real_human_validation_results.md`, explicitly labeled as such per `docs/privacy.md`'s
policy — no new audio was captured, no private human data was used. See `cases/
README.md` for the full index and coverage table.

## 12. Rubric

8 dimensions (Groundedness, Specificity, Actionability, Prioritization, Safety,
Uncertainty handling, Retry-goal quality, Conciseness), 0-3 ordinal scale, no composite
score. See `evaluation_rubric.md` for the full per-dimension scoring guide. Groundedness
and Safety scoring 0 are treated as shipping blockers regardless of other scores.

## 13. Failure taxonomy

See `failure_taxonomy.md` — 12 failure modes, each with consequence and mitigation,
covering invented measurements, diagnostic overreach, filler/pause overreaction and
mislabeling, contradictory advice, STT-trust failures, near-silence confabulation,
generic advice, evidence-unrelated advice, too-many-suggestions, vague retry goals, and
run-to-run inconsistency.

## 14. Prompt/output contract

Minimum clean schema (not the task brief's example taken literally — adapted to what
this milestone's evidence actually justifies):

```json
{
  "strength": { "message": "string | null", "evidence": ["string", "..."] },
  "main_improvement": { "message": "string | null", "evidence": ["string", "..."] },
  "technique": { "id": "TECH-XXX | null", "name": "string | null", "reason": "string | null" },
  "retry_goal": "string | null",
  "abstained": "boolean",
  "abstention_reason": "string | null"
}
```

Differences from the task brief's illustrative example, and why:

- `strength`/`main_improvement`/`technique`/`retry_goal` are all **nullable together**
  when `abstained: true` — the brief's example didn't show this explicitly, but
  section 8's abstention policy requires a representable "no output" state, not an
  empty-string workaround.
- `main_improvement.message` can also be `null` with `abstained: false` (see CASE-01,
  CASE-15 in `results/`) — a genuinely strong or thin-evidence attempt may have no
  responsible "main improvement" to name even without a full abstention. This is a
  deliberate schema choice this milestone's illustrative results surfaced as necessary,
  not present in the brief's example.
- `technique.id` is constrained to the curated `TECH-XXX` enum (`technique_library.md`)
  per Approach C, plus `null` for "no technique's bar was met" — never a free-text
  technique name, closing off the "LLM invents a technique" failure mode named in
  section 4 of the task brief.
- No `fluency score` or other composite numeric field exists anywhere in this schema,
  consistent with `docs/decision-log.md`'s existing no-composite-score precedent for
  metrics and this milestone's explicit prohibition (section 7 below).

This is a **design proposal**, not a locked schema — `docs/decision-log.md`'s
"Architecture Change Rule" and this milestone's own instruction ("do not implement this
exact schema blindly") mean the actual M7B/M8 schema should be finalized against real
model output, which may reveal fields this design didn't anticipate.

## 15. Prompt-versioning policy

Production coaching prompts are versioned explicitly, e.g. `COACH_PROMPT_V1`. A
behavior-changing prompt update requires the same pattern already established for
model/threshold changes (`docs/ai-boundaries.md` "Model-Change Policy",
`docs/methodology.md` "Research-integrity rules"):

```
reason → evaluation → comparison (against current prompt, not evaluated in isolation)
  → documented decision (docs/decision-log.md)
```

No production prompt may be silently edited. This extends, rather than duplicates, the
model-change policy already in force for the transcription model/pause threshold/filler
vocabulary (DEC-004, DEC-014, DEC-015, DEC-017) — a coaching prompt version is exactly
the kind of "AI parameter that changes user-facing output" that policy already covers.

## 16. Experiment results

See `experiment_plan.md` (EXP-M7-001 through 005) and `results/summary.md` for the full
illustrative comparison. Headline: on the 6-case illustrative subset, Approach A scored
0 on groundedness in half the cases and never abstained even on a near-silent
transcript; Approach B eliminated all groundedness/safety zeros but left a
prioritization gap; Approach C matched B and closed the prioritization gap via the
technique library's explicit evidence bars and exclusion rules. **None of this is a
measured comparison of real model behavior** — see the "Important limitation" in
`README.md`.

## 17. Leading architecture hypothesis (candidate for M7A-2 validation)

**This is a hypothesis produced by illustrative comparison, not an experimentally
proven winner.** No live model was run in M7A. The architecture below is what M7A
recommends carrying into M7A-2 for real-model validation — not a decision to build
against yet.

```
deterministic evidence (M6B's SpeechMetrics + Transcript)
  → deterministic eligibility/guardrails (evidence-to-technique policy, section 6;
     abstention gate, section 7)
    → LLM interpretation (Tier 4 — strength/main_improvement generation, grounded in
       the passed-through evidence only)
      → approved technique selection (constrained to technique_library.md's TECH-XXX
         enum, with each technique's own evidence bar checked)
        → structured output validation (schema from section 14; reject/flag output
           that fails to cite evidence for a claim, or that selects an ineligible
           technique)
```

This matches the task brief's own suggested architecture. **Why it looked strongest in
this milestone's illustrative comparison** (not "why it beat the alternatives" —
nothing here was measured competitively against a real model):

- vs. **rule-based only**: cannot produce Tier 4 (structure/clarity/language)
  interpretation at all — the coaching job explicitly needs generative reasoning over a
  transcript, not just metric-value templating.
- vs. **unconstrained LLM (Approach A)**: EXP-M7-001's illustrative result — invented
  claims, no abstention, poor prioritization.
- vs. **structured-only, no library (Approach B)**: EXP-M7-002/003's illustrative
  delta — the library's explicit per-technique evidence bars and exclusion rules
  close a prioritization/contradiction gap that structure alone left open.

## 18. Why AI?

**The coaching job needs interpretation a deterministic rule table cannot produce.**
Comparing against every alternative the task brief named:

- **Deterministic rules** (if-metric-then-message): can state *that* WPM was high or a
  pause was detected, but cannot produce a specific, attempt-grounded observation about
  *this transcript's* structure or clarity — there is no rule table expressive enough
  to name "the response drifted from leadership to remote-work logistics after the
  second sentence" without reading the actual text.
- **Simple templated coaching** (fill-in-the-blank sentences per metric): same
  limitation — templates can acknowledge a metric exists but cannot quote or reason
  about transcript content, which is where most of the task brief's requested
  dimensions (Clarity of Thought, Structure) live.
- **Heuristic mapping from metrics to techniques**: this is *part* of the leading
  architecture hypothesis already (the evidence-to-technique policy, section 6, and the technique
  library's evidence bars, section 4, are exactly this) — but a heuristic alone cannot
  generate the `strength`/`main_improvement` natural-language messages or quote the
  relevant transcript span; it can select a technique, not write the coaching.
- **LLM-generated coaching, unconstrained**: EXP-M7-001's illustrative result shows why
  this alone is insufficient (groundedness/safety failures).
- **Hybrid deterministic + LLM** (the leading architecture hypothesis, section 17): the
  deterministic layer owns everything that must never be wrong (evidence gating,
  technique eligibility, schema validation); the LLM owns only the part that
  genuinely requires language generation over transcript content (Tier 4
  interpretation), constrained on every side by deterministic guardrails.

**Conclusion: the LLM does not own all coaching.** It owns exactly the slice
(natural-language interpretation of transcript content, phrased as strength/improvement
messages) that no deterministic layer can produce, bounded by deterministic evidence
gates and a deterministic technique enum on both sides.

## 19. Limitations

- **No live model comparison was performed** — the single largest limitation of this
  entire milestone. Every "result" in `experiment_plan.md`/`results/` is an
  illustrative design exercise authored by the same agent that designed the contracts
  being compared, not an independent or model-backed measurement. See "Important
  limitation" in `README.md`.
- **Illustrative self-scoring is not blind evaluation** — the rubric scores in
  `results/` were assigned by the same agent that wrote the outputs being scored, a
  conflict of interest a real evaluation should avoid (e.g. a separate scoring pass, or
  a different model as judge). **Correction added post-review:** this is not merely a
  small-sample limitation but a documented, named bias pattern — see
  `research_review.md` B4 ("Self-Preference Bias in Rubric-Based Evaluation of Large
  Language Models," arXiv 2604.06996), which found LLM judges score their own output
  more favorably than an independent judge would, including on ostensibly objective
  criteria. `results/summary.md`'s "Approach C wins" pattern should be treated as a
  design sketch, not a validated result, until an independent re-scoring pass (a
  different session/agent or a human, with no authorship stake in the outputs) is run
  against the same 18 illustrative outputs.
- **6-case subset, not the full 16-case evaluation set** — chosen to cover the
  highest-stakes design questions, not exhaustively; the full set is intended for the
  real model comparison.
- **EXP-M7-004 (consistency) could not be attempted at all** — no meaningful way to
  simulate repeated-sampling variance without a real model.
- **No real transcript beyond the two reused M6B samples** — 14 of 16 cases are
  synthetic text fixtures, not real speech; real speech's actual STT-error patterns
  (per `experiments/m5_transcription/conclusions.md`) are only indirectly represented
  (CASE-10, CASE-12 are designed to *resemble* STT artifacts, not captured from one).
- **Technique library is community-derived opinion, not validated pedagogy** — stated
  explicitly at the top of `technique_library.md`; no technique's effectiveness is
  claimed as scientifically proven, per the task brief's own instruction.
- **Pricing/availability for Gemini and quality for Ollama were not verified** in this
  environment — reported as "requires current verification," not guessed.

## 20. Cost/latency/privacy considerations

- **Cost**: unresolved pending real provider verification (section 10). A local option
  (Ollama, or the rule-based/heuristic layer alone) has effectively zero marginal cost;
  Gemini's specific current pricing was not verified here.
- **Latency**: the existing pipeline's transcription step alone already takes ~2-8s for
  a ~15-100s clip (`docs/context.md` "Current Performance Characteristics"); any
  coaching call adds to that. A local model adds no network round-trip but depends on
  local hardware; a remote API adds a network round-trip whose latency was not measured
  here.
- **Privacy**: per `docs/ai-boundaries.md` "Interface Isolation," the coach receives
  only structured evidence (transcript text + `SpeechMetrics`) — **never raw audio** —
  regardless of which provider is eventually chosen. A local option (Ollama) keeps even
  that structured evidence on-machine, fully preserving `docs/privacy.md`'s
  local-first framing; a remote provider (Gemini) is a real, if narrowly scoped,
  privacy change (`docs/risks.md` RISK-005) that `docs/privacy.md` will need to update
  concretely once implemented, per that risk's own "trigger to revisit."

## 21. Decisions made

- V1 coach output shape: what worked → main improvement → evidence → technique → one
  retry goal (section 1).
- One unified coach, not per-role specialist agents, for V1 (section 3).
- Coaching dimensions actually supportable in V1: Delivery, Clarity of Thought,
  Structure fully; Language narrowly (quoted-repetition only); Audience Fit not at all
  (section 2).
- Curated technique library (TECH-001–008) with per-technique evidence bars and
  exclusion rules; LLM must select from it, not invent techniques (sections 4, 6).
- Evidence-to-technique policy and evidence hierarchy tiers (sections 5, 6), directly
  extending M6B's existing reliability classifications — no metric's tier changed.
- Abstention policy defined (not implemented) — explicit trigger list (section 7).
- Leading architecture hypothesis (not proven, candidate for M7A-2 validation): hybrid
  deterministic-gate + LLM-interpretation + constrained-technique-selection +
  schema-validated output (section 17), based on illustrative
  (not yet measured) comparison evidence.
- Prompt/output contract draft, explicitly marked as a design proposal, not a locked
  schema (section 14).
- Prompt-versioning policy: extends the existing model-change policy pattern to
  coaching prompts (section 15).
- 16-case evaluation set and 8-dimension rubric created for future real-model
  evaluation (sections 11, 12).

## 22. Decisions deferred

- **Which model/provider to use** (Gemini vs. Ollama vs. another local option) —
  requires real cost/quality/latency verification this environment could not perform.
- **The exact production prompt text for `COACH_PROMPT_V1`** — this milestone designed
  the contract and constraints, not the literal prompt string; that requires iteration
  against a real model.
- **The final output schema** — the section 14 schema is a proposal to be revised once
  real model output is observed (per the task brief's own instruction not to implement
  it blindly).
- **EXP-M7-004 (consistency across runs)** — cannot be attempted without real model
  access.
- **Whether TECH-006 (Vocabulary Expansion) is worth keeping** given how narrow its
  current evidence bar is — flagged as borderline in `technique_library.md`, not
  resolved either way.
- **Whether "no main improvement, no abstention" (CASE-01/CASE-15's schema case,
  section 14) is the right modeling choice**, versus folding it into a broader
  abstention definition — a genuine design question this milestone's illustrative
  results surfaced but did not resolve with real-model evidence.
- **Real Gemini/Ollama-backed re-runs of EXP-M7-001/002/003/005** against the full
  16-case set, per each experiment's own "Decision" entry in `experiment_plan.md`.

## 23. Files created/modified

**Created** (all under `experiments/m7_grounded_coaching/`, nothing outside
`experiments/`):

- `README.md`
- `experiment_plan.md`
- `technique_library.md`
- `evaluation_rubric.md`
- `failure_taxonomy.md`
- `conclusions.md` (this file)
- `cases/README.md`
- `cases/manifest.json`
- `results/README.md`
- `results/approach_a_generic.json`
- `results/approach_b_structured.json`
- `results/approach_c_technique_library.json`
- `results/summary.md`

**Modified:** none. No file under `backend/`, `frontend/`, `docs/`, or any other
experiment directory was changed. `docs/decision-log.md` was **not** updated, since no
new production decision (model choice, prompt text, schema lock-in) was actually made —
only design proposals, consistent with the project's architecture-change rule (decisions are recorded in `docs/decision-log.md` first) (a
decision-log entry is warranted once M7B implements something from this design, not for
the design document itself).

## Git status

No files were staged or committed. Per this milestone's explicit instruction ("Do not
commit") and the project's standing rule (explicit human approval
required before any commit), all files above remain untracked, pending review.
