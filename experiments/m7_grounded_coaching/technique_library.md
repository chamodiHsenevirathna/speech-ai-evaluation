# Coaching Technique Library

**Status: curated, USER/COMMUNITY DISCOVERY evidence, not scientific proof.** These
techniques are common articulation/public-speaking advice patterns (Toastmasters-style
practice, general speech-coaching community knowledge), not techniques validated by any
SpeakLab experiment or clinical study. The LLM coach must select from this library
rather than invent arbitrary techniques (see `docs/ai-boundaries.md`'s spirit — the LLM
does not invent measurements, and by the same logic should not invent *unvetted
advice* presented as authoritative).

Each technique below is a candidate the coach may cite by ID. "Current/future support
status" reflects what M6B evidence can actually ground it in — a technique may be
well-designed but currently ineligible because SpeakLab has no reliable evidence for the
symptom it addresses (e.g. TECH-005/007/008 need evidence SpeakLab doesn't currently
produce).

---

### TECH-001 — Deliberate Pause

**Purpose:** Slow down and create thinking space, replacing rushed delivery with an
intentional pause.

**When it may be appropriate:**
- High approximate WPM relative to the speaker's own baseline or a reasonable
  conversational range (evidence: `words_per_minute`, tier 2).
- Weak/abrupt transitions visible in the transcript (evidence: transcript, tier 4
  interpretation).

**When it should NOT be recommended:**
- WPM evidence is unavailable (near-empty transcript, `words_per_minute: null`).
- The speaker already has multiple long pauses detected — recommending *more* pausing
  on top of existing pause evidence risks contradictory advice (see failure taxonomy
  "contradictory feedback").

**Evidence required before recommending:** `words_per_minute` present and
meaningfully high relative to a stated reasonable range (the coach states the number
it's reacting to, never invents a "normal" range as if it were a validated norm).

**Example retry instruction:** "On your next attempt, pause for a full breath after
your opening sentence before moving to your example."

**Current/future support status:** **Current** — WPM is `approximate` (Tier 2), usable
now with appropriate hedging.

---

### TECH-002 — Complete Sentence First

**Purpose:** Form a sentence mentally before speaking, reducing fragments and
abandoned restarts.

**When it may be appropriate:**
- Transcript shows fragmented ideas, abandoned sentences, or frequent restarts
  (evidence: transcript, tier 4 interpretation — the coach quotes the fragment).

**When it should NOT be recommended:**
- Fragmentation could be a transcription artifact rather than real speech (transcript
  is Tier 4/imperfect STT output, per `docs/ai-boundaries.md`) — the coach must hedge
  ("the transcript shows..." not "you said...") when the evidence is only a garbled
  transcript, and should prefer abstention over confidently diagnosing fragmentation
  from a transcript that looks STT-corrupted rather than genuinely fragmented.

**Evidence required before recommending:** At least one concrete quoted transcript
fragment showing an incomplete or abandoned sentence.

**Example retry instruction:** "Before your next sentence, finish the thought in your
head, then say it in one breath."

**Current/future support status:** **Current** — transcript-based, usable now with the
"imperfect STT" hedge already required by `docs/ai-boundaries.md`.

---

### TECH-003 — Point → Example → Conclusion

**Purpose:** Give the response a simple, repeatable structure: one main point, one
supporting example, one conclusion.

**When it may be appropriate:**
- Transcript shows a wandering answer, weak topic focus, or an unclear/missing
  conclusion (evidence: transcript, tier 4 interpretation).

**When it should NOT be recommended:**
- The transcript already shows this structure clearly (recommending it to someone who
  did it well is generic-advice failure mode, see failure taxonomy).
- Transcript is too short/fragmented to assess structure at all — abstain instead.

**Evidence required before recommending:** A specific structural gap the coach can
point to (e.g. "the transcript shifts between two unrelated ideas after the opening
sentence, with no return to the first" or "no closing statement appears in the final
segment").

**Example retry instruction:** "On your next attempt, give one main point, one example,
then finish with one clear conclusion."

**Current/future support status:** **Current** — the flagship V1 technique; structure
assessment is Tier 4 interpretation but grounded directly in transcript text, which is
available on every successful attempt.

---

### TECH-004 — Replace Filler With Silence

**Purpose:** Use a short pause instead of a filler word ("um"/"like").

**When it may be appropriate:**
- Filler evidence is **sufficiently strong** — meaning more than one or two isolated
  detections, per `docs/decision-log.md` DEC-015's EXPERIMENTAL classification. A
  single filler detection must not trigger this as the main retry goal (see "Evidence
  Hierarchy" and failure taxonomy "overreacting to one experimental filler").

**When it should NOT be recommended:**
- Fewer than ~3 filler detections in the attempt, or the only detected filler is a
  borderline/ambiguous category (e.g. a single discourse "like").
- Filler detection is explicitly EXPERIMENTAL (`docs/decision-log.md` DEC-015) — this
  technique's evidence bar is deliberately the highest of any technique in this
  library.

**Evidence required before recommending:** Multiple (3+) filler occurrences, cited with
their matched text and category (e.g. "um" ×4), phrased as "detected" not "you said
exactly N fillers" — count is experimental, not exact. **Threshold justification** (not
a statistical/experimental claim): "3" is a product-design choice, not a measured or
derived number. It operationalizes the M7A task brief's own explicit instruction that
"one or two detections should not automatically trigger a filler-focused retry goal,"
combined with DEC-015's EXPERIMENTAL classification (8-example evaluation set) —
i.e., the bar is set qualitatively above "one or two" because the brief names that
range directly, not because 3 was validated against any data. This should be revisited
once real coaching output exists and DEC-015 has more evaluation-set evidence, not
treated as a tuned constant.

**Example retry instruction:** "On your next attempt, when you feel a filler word
coming, pause silently for a beat instead."

**Current/future support status:** **Current, high evidence bar** — fillers are Tier 3
(experimental); usable only when the signal clears a volume threshold, never on a
single detection.

---

### TECH-005 — Read Aloud

**Purpose:** Practice natural phrasing and articulation by reading a fixed text aloud.

**When it may be appropriate:** A future read-aloud practice mode, comparing spoken
output against a known reference text.

**When it should NOT be recommended:** In V1's impromptu-speaking mode — there is no
reference text to read, so this technique has no application to the current product
surface.

**Evidence required before recommending:** N/A for V1 — this technique requires a
reference-text practice mode that does not exist yet (`docs/requirements.md` "V1 Scope
— Later").

**Example retry instruction:** N/A for V1.

**Current/future support status:** **Future** — depends on a read-aloud mode
(`docs/requirements.md` "Later"). Not eligible for the V1 impromptu coach; included here
so the library doesn't need re-designing when that mode is built.

---

### TECH-006 — Vocabulary Expansion

**Purpose:** Improve word choice over time by noticing repeated generic wording.

**When it may be appropriate:** Repeated generic wording or narrow vocabulary variety
is visible across the transcript (e.g. the same 2-3 adjectives used repeatedly).

**When it should NOT be recommended:** SpeakLab currently has **no deterministic
lexical-variety metric** (word count/WPM/pauses/fillers do not measure vocabulary
range) — any claim about "limited vocabulary" would be a pure Tier 4 generative
judgment with no structured evidence backing it, which is exactly the failure mode
`docs/ai-boundaries.md` warns against ("insufficient evidence... should abstain").
Because the transcript-quoting bar can be met (the coach can literally quote repeated
words), this technique is borderline: it is includable **only** if the coach quotes the
literal repeated words/phrases as evidence, never as a general "your vocabulary is
limited" claim.

**Evidence required before recommending:** At least 2 verbatim quoted instances of the
same word/phrase used as a generic filler-word substitute (e.g. "good" used 4 times
where the transcript shows 4 distinct contexts).

**Example retry instruction:** "On your next attempt, try replacing 'good' with a more
specific word each time you'd otherwise use it."

**Current/future support status:** **Current, narrow** — only when the coach can quote
literal repetition; otherwise treat as unsupported for V1 (no lexical-diversity metric
exists).

---

### TECH-007 — Model Strong Speakers

**Purpose:** Observe phrasing, pacing, and structure from strong communicators.

**When it may be appropriate:** A future guided-imitation practice feature.

**When it should NOT be recommended:** V1 has no reference speaker content or
comparison mechanism.

**Evidence required before recommending:** N/A for V1.

**Example retry instruction:** N/A for V1.

**Current/future support status:** **Future** — no product surface for this in V1.

---

### TECH-008 — Audience Reframing

**Purpose:** Explain the same idea for a specific audience (e.g. explain to a colleague
vs. a child).

**When it may be appropriate:** Interview-practice, presentation-practice, or
explanation-practice modes with an explicit target audience.

**When it should NOT be recommended:** V1's impromptu prompts do not specify an
audience, and SpeakLab has no audience-fit evidence (Coaching Dimension E, "Audience
Fit," is explicitly not supportable from current evidence — see `conclusions.md`
"Coaching dimensions").

**Evidence required before recommending:** N/A for V1 — would require prompts that
specify an audience, which V1 prompts do not.

**Example retry instruction:** N/A for V1.

**Current/future support status:** **Future** — depends on prompt design work outside
M7A's scope.

---

## Summary table

| ID | Name | V1 status | Min evidence bar |
|---|---|---|---|
| TECH-001 | Deliberate Pause | Current | WPM present, meaningfully high |
| TECH-002 | Complete Sentence First | Current | ≥1 quoted fragment |
| TECH-003 | Point → Example → Conclusion | Current | Named structural gap |
| TECH-004 | Replace Filler With Silence | Current, high bar | ≥3 filler detections |
| TECH-005 | Read Aloud | Future | N/A (needs read-aloud mode) |
| TECH-006 | Vocabulary Expansion | Current, narrow | ≥2 quoted literal repeats |
| TECH-007 | Model Strong Speakers | Future | N/A (needs reference content) |
| TECH-008 | Audience Reframing | Future | N/A (needs audience-aware prompts) |

Only TECH-001, TECH-002, TECH-003, TECH-004, and TECH-006 are eligible for the V1
coach. TECH-005/007/008 remain documented placeholders for later modes, per
`docs/requirements.md`'s "Later" list — they must not be selected by the LLM in V1
even if it judges them stylistically relevant, since no supporting evidence pathway
exists for them yet.
