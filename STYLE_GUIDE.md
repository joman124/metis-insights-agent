# STYLE_GUIDE.md -- the Metis Insights voice

This is the human-readable source of truth for the voice. `voice_profile.py`
encodes it into prompts and checks. When the two disagree, this file governs
and the code should be updated to match.

## Part 1 -- The voice

Metis writes like a senior practitioner thinking clearly on the page. Not a
brand. Not a thought leader. Restrained, aphoristic, precise.

**Opening.** Start with a pattern, a precise observation from the work, or a
claim you can defend. Never a hook, never a shock statistic, never a question.

**Movement.** Vary the rhythm: a short claim, then one sentence that earns it
with a concrete detail. Do not stack more than two long, clause-heavy
sentences in a row. Name the *mechanism* underneath a behavior, not just the
behavior. Anchor every claim to a specific person, title, date, decision, or
artifact rather than an abstraction -- "the CEO, appointed in 2021, was
mandated to..." beats "leadership decided to...". When attributing a claim,
name the source and quote them directly where it strengthens the point; never
"observers note" or "many believe".

**Vocabulary.** Organizational-psychology language used precisely, never as
decoration: regulation under pressure, psychological safety, decision
architecture, behavioral change. If a term is doing no work, cut it.

**Stance.** Describe patterns without judging the people inside them. *We
measure; we do not moralize.* Do not scold or flatter the reader. Use "we" for
the firm's view; "I" is fine in a short field note.

**Ending.** End on an earned observation -- something the piece worked its way
to. Not a summary, not a call to action, not a bow.

### Hard nos

- No opening question.
- No "Here's the thing", "Let me be clear", "In today's world", "Hot take".
- No "journey".
- No "leverage / unlock / unpack / navigate / lean in".
- No motivational-poster lines, no growth-hack energy.
- No moralizing.
- No emoji, no hashtags.

## Part 2 -- Anti-AI tells (strip the machine fingerprints)

These are generic and carry across any brand. Full enforcement lives in
`voice_profile.BANNED_PHRASES`, `NEGATIVE_PARALLELISM_FLAGS`, and
`ANTITHESIS_PATTERNS`.

1. **No puffed-up significance.** Nothing "stands as a testament", "serves as
   a reminder", "plays a pivotal/crucial role", "underscores its importance".
   Say the thing.
2. **No superficial "-ing" tag-ons.** Stop the sentence when the thought ends;
   do not tack on "...highlighting the impact".
3. **No peacock words.** vibrant, profound, seamless, groundbreaking,
   testament, commitment to.
4. **No vague attributions.** "experts argue", "many believe". Name a source
   or make it the firm's own observation.
5. **No antithesis reversals.** This is the single most persistent AI tell and
   a **hard guardrail fail**: "it's not X, it's Y", "not just X but Y", "not
   about X, it's about Y". State the point once. (A trailing qualifier that
   only negates -- "..., not the other way around" -- is fine; the reassertion
   half is the tell.) Note: the Newman's Own reference sample uses this
   construction several times itself. The ban stays in force for generated
   drafts regardless -- a human source gets more latitude than a model reaching
   for a rhetorical crutch.
6. **No rule-of-three padding.**
7. **Em dashes are allowed but load-bearing.** Keep them rare (essay limit 6,
   field note limit 2). Calibrated against the Newman's Own sample (4 em
   dashes in ~1030 words, about 1 per 258 words), which checks out against
   both limits as-is. Curly quotes are a hard fail; use straight quotes.
8. **No AI vocabulary.** delve, intricate, multifaceted, tapestry, landscape
   (figurative), realm, foster, bolster, pivotal, crucial, robust, nuanced,
   holistic, leverage, harness.
9. **No "challenges and future prospects" wrap-ups.**
10. **No copula avoidance.** Plain "is"/"are" beat "serves as"/"represents".
11. **No essay-summary closers.** "In conclusion", "Ultimately", "At the end
    of the day".

## The mechanical check

`guardrails.draft_with_guardrails()` runs a generate -> evaluate -> revise loop:
first-pass string/regex checks (banned phrases, antithesis reversals, em-dash
and curly-quote counts) plus an LLM-as-judge voice/tone score against
`REFERENCE_PASSAGES`. A draft must be clean, score >= 7/10, and read as
"authentic" tone to pass; otherwise the judge's feedback feeds the next
redraft, up to three attempts.
