# Ways the Coach Could Embarrass Us in Public

Failure → consequence → mitigation. Ordered roughly by severity (safety/trust failures
first, quality failures after).

---

**Invented measurements** (a duration, count, or timestamp not in the evidence)
→ Consequence: destroys user trust instantly, the single fastest way to make the coach
look fraudulent; directly contradicts `docs/ai-boundaries.md`'s core rule.
→ Mitigation: Approach B/C's structured contract requires every claim to cite a
specific evidence field; output-schema validation (see `conclusions.md` "Prompt/output
contract") rejects/flags any coaching output whose `evidence` array is empty for a
claim that reads as a measurement.

**Claiming user is anxious / diagnosing anxiety, a speech disorder, ADHD/autism, or any
other condition**
→ Consequence: the single most reputationally dangerous failure mode — an unqualified
tool making a clinical-sounding claim about a stranger's speech.
→ Mitigation: explicit prohibition in the system prompt (see `conclusions.md` "Coach
must never"); rubric dimension E is a shipping blocker at score 0; this is the primary
reason V1 uses a curated technique library (Approach C) instead of unconstrained
generation — the library itself contains no diagnostic language to draw from.

**Overreacting to one experimental filler detection**
→ Consequence: user is told their "filler-heavy" delivery needs work based on a single
detected "um" — disproportionate to DEC-015's own EXPERIMENTAL classification and 8-
example evaluation size.
→ Mitigation: TECH-004's evidence bar (≥3 detections) in `technique_library.md`; the
evidence-to-technique policy in `conclusions.md` explicitly states "one or two
detections should not automatically trigger a filler-focused retry goal."

**Calling semantic "like" a filler**
→ Consequence: visibly wrong to any user who reads their own transcript closely
("looks like her sister" flagged as a filler is an obvious, credibility-destroying
error) — and the deterministic detector (DEC-015) already solves this at the metrics
layer; the coach re-introducing the error at the interpretation layer would be a
regression the metrics layer specifically fixed.
→ Mitigation: coach receives only the deterministic `fillers` list (already
context-filtered) as its filler evidence — it must never independently scan the
transcript for filler-like words itself; this is enforced by the input contract
(coach input = `SpeechMetrics.fillers`, not raw transcript re-analysis for fillers).

**Claiming exact acoustic pause durations** ("you paused for exactly 2.3 seconds")
→ Consequence: contradicts `docs/decision-log.md` DEC-014's explicit correction (a 0.5s
true pause read as a 1.00s observed gap) — a confident-sounding number that is
demonstrably not what was measured.
→ Mitigation: `PauseEvent` has no `duration_seconds` field by design
(`docs/context.md`); the coach's input never contains a pause duration to cite, so
it structurally cannot invent one from the evidence — only from confabulation, which
groundedness scoring (rubric A) is designed to catch.

**Giving contradictory feedback** (e.g. recommending TECH-001 "slow down and pause
more" to someone who already has multiple detected long pauses)
→ Consequence: reads as not having actually looked at the evidence — worse than generic
advice, because it's specifically wrong.
→ Mitigation: TECH-001's "when NOT to recommend" clause in `technique_library.md`
explicitly excludes speakers with existing pause evidence; Approach C's structured
selection (evidence → eligible technique set → pick one) makes this check mechanical
rather than relying on the LLM to notice unprompted.

**Treating the Whisper transcript as perfect ground truth**
→ Consequence: coaching built on a transcription error (e.g. "you used the word X
several times" when Whisper mis-transcribed a different word each time) is
confidently wrong in a way the user can't predict or defend against.
→ Mitigation: `docs/ai-boundaries.md` and `experiments/m5_transcription/conclusions.md`
already establish this; the coaching prompt contract must repeat the caveat ("the
transcript may contain transcription errors") whenever quoting transcript text as
evidence, and structure/language claims (Tier 4) must be phrased as "the transcript
shows..." not "you said...".

**Giving feedback on near-silence / insufficient evidence**
→ Consequence: fabricated-sounding coaching on a near-empty or corrupted transcript
(e.g. Test C's punctuation-only transcript) — nothing to ground feedback in, so any
output is confabulation by construction.
→ Mitigation: the abstention policy (`conclusions.md` section 8) — the coach must
output `abstained: true` rather than generate a strength/improvement/technique when the
evidence-sufficiency gate fails.

**Generic advice that ignores the specific evidence** ("be more confident," "practice
more," "work on your delivery")
→ Consequence: the exact failure this milestone's core product question calls out —
"fluent generic advice" that doesn't distinguish SpeakLab from a canned tip list.
→ Mitigation: rubric dimension B (Specificity); Approach A (unconstrained generic
prompt) is expected to fail here by design — this is the experiment's own hypothesis
(see `experiment_plan.md` EXP-M7-001).

**Advice unrelated to the evidence presented** (e.g. talking about grammar when no
grammar evidence exists)
→ Consequence: reveals the coach isn't actually reasoning from the supplied evidence.
→ Mitigation: evidence-to-technique policy restricts technique selection to techniques
whose evidence bar is met by *this attempt's* evidence, not any plausible-sounding
advice.

**Too many suggestions in one output**
→ Consequence: overwhelms the user and dilutes the "one retry goal" product principle
(FR-15); a 2026 user practicing 60-second impromptu speaking cannot act on five
simultaneous corrections.
→ Mitigation: output schema hard-caps at one `main_improvement` and one `retry_goal`;
rubric dimension D.

**Retry goal too vague to act on** ("work on structure next time")
→ Consequence: technically present but functionally useless — fails the product's core
retry-improvement loop (`docs/requirements.md` "Core Product Loop").
→ Mitigation: rubric dimension G requires the goal be phrased as a concrete in-the-
moment action; technique library's "example retry instruction" field gives the coach a
template for the right level of concreteness.

**Inconsistent advice across identical/near-identical inputs**
→ Consequence: undermines trust that the coach is actually evidence-driven rather than
randomly sampling — especially damaging on the Comparison screen, where the user
directly compares two coaching outputs.
→ Mitigation: EXP-M7-004 (deferred — see `experiment_plan.md`) is designed to test
this directly once real model access exists; structured output + low-temperature
generation + the technique library's constrained selection space (5 eligible
techniques, not open-ended) are the design levers expected to reduce variance, but this
is a hypothesis pending real measurement, not a claim of resolved consistency.
