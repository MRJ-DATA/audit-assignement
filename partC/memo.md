# Part C — Decision Memo: Casual Tone for Hindi/Kannada/Tamil/Telugu/Bengali/Marathi

## Recommendation

**Path (c): prompt-engineering only.** This is the main path for
launch. We also set a clear, dated kill criterion. If prompting doesn't
work well enough, we escalate to **path (b)** (a small rewriter model
that runs after the main model). We do not recommend path (a), SFT,
given the constraints below.

## Assumptions (labelled)

1. The base model already speaks all 6 languages well. This is a
   style problem, not a language problem. The complaint is "too
   formal," not "wrong" or "broken."
2. The model's training data likely includes some casual text in these
   languages (social media, forums, casual writing). So prompting
   should be able to bring out that casual style, even without extra
   training.
3. We can only directly check quality for Hindi and Kannada, since
   that's what our reviewer covers. For Tamil, Telugu, Bengali, and
   Marathi, we can only use rough automatic checks (like honorific
   word frequency, sentence length, or use of casual contractions).
   This is a real gap. We treat it as a real gap, not a solved problem.
4. We have no budget for external APIs. So we can't use a paid LLM API
   to generate or judge training data. Any data generation has to run
   on our own A100.

## Why not (a) or (b) as the main path

**Path (a), SFT, changes the model's weights directly.** This is
harder to undo if something goes wrong after launch. It also needs
casual-style example pairs in all 6 languages. We have no reviewer for
4 of those languages, and no budget for external APIs. So the training
data for those 4 languages would ship with **zero human quality check**.
That risks quietly making output worse in languages no one on the team
can verify. We only have 15 working days until launch review. That's
not enough time to build a solid quality check for those 4 languages
another way.

**Path (b), a small (≤1B) rewriter model, is safer.** It doesn't touch
the main model, so it's easy to turn off if needed. But it still needs
a training set and a full train-and-test cycle before it can ship.
That fits better in a longer timeline. Given our 3-week deadline, we
keep it as a funded backup plan, not the main path.

## Back-of-envelope arithmetic

**Reviewer throughput.** The reviewer has 10 hours a week, split across
2 languages. Rating one example for "casualness" takes about 2.5
minutes. That gives us about 240 examples a week in total, or about
120 per language per week. Over a 2-week testing window (leaving 1
week as launch buffer), that's **about 240 reviewed examples per
language** for Hindi and Kannada. That's enough to get a rough sense of
whether a prompt is working. It is not enough for strong statistical
confidence. We should say this clearly in the launch review.

**Compute.** Prompt-engineering needs almost no training compute. So
the A100-80GB we were given for 2 weeks is mostly free under this plan.
We'd use it to run batch generation and scoring for the automatic
checks in the 4 non-reviewed languages. If time allows, we could also
use it to start early prototyping on path (b) as insurance — but we
would not commit to fully building path (b) in this timeline.

**Timeline (15 working days to launch review):**
- Day 1: write 3–5 casual-tone system-prompt versions. Write each one
  natively in its language, not translated from one English prompt —
  casual style markers don't translate directly.
- Days 2–3: generate both baseline and prompted outputs for about
  50–100 stock queries per language.
- Days 4–5: reviewer scores the Hindi/Kannada pilot batch. Automatic
  checks run on the other 4 languages.
- Week 2: pick the best-performing prompt version, refine it, and
  re-test on a larger sample.
- Week 3: final checks, launch review prep, and buffer time for fixes.

## Success metric (numeric threshold)

**At least 70% of sampled Hindi and Kannada responses should score 4
or higher out of 5 on a casualness scale**, as rated by the native
reviewer. We compare this to a baseline score measured on Day 1–2,
which we expect to start well below 40%, given the current complaint
that outputs sound formal and textbook-like. For the 4 non-reviewed
languages, we track the automatic proxy scores as a secondary signal.
These scores are lower-confidence, so they don't gate the launch on
their own.

## Kill criterion

**Check-in point: end of Week 2 (day 10 of 15).** By then, we should
have tried at least 2 rounds of prompt changes. If the best-performing
prompt still hasn't reached at least 50% "casual enough" (score 4+) on
the Hindi/Kannada reviewer sample — in other words, if we're not even
halfway to our 70% target — that's a clear sign prompting alone has
hit its limit. At that point, we do three things: kill path (c) as the
only fix, move to path (b) using the remaining week plus the freed-up
A100 time, and flag a likely 1–2 week delay to launch clearly and
early. It's better to say this early than to ship something that
doesn't work.

## First experiment (Day 1)

Write an early casual-tone prompt natively for Hindi and Kannada. Do a
short, informal 30–60 minute check-in with the reviewer to sanity-check
it — not a full review yet. Then collect about 20 stock user queries
per language. Generate both the current (formal) output and the new
(casual) output for each query. Ask the reviewer to quickly compare the
two side by side and say which sounds more natural. This gives us a
directional signal on day 1, before we commit the full 2-week testing
window to one direction.
