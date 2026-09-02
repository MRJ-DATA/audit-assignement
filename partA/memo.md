# A4 — Recommendation Memo

**To:** Leadership
**Re:** Corrected tokenizer fertility findings, Indic-language routing
**Status:** supersedes Section 1 of REPORT_v0.md

## Corrected headline numbers

The original report's number (Hindi = 5.89x English fertility, "budget
6x cost") was measured with GPT-2 — a tokenizer whose training data was
overwhelmingly English — and used a denominator (whitespace-split
"word") that is not comparable across languages. Corrected, on a
997-sentence aligned multilingual corpus (English/Hindi/Tamil/
Malayalam), holding actual content constant (tokens per parallel
sentence):

| tokenizer | Hindi | Tamil | Malayalam |
|---|---|---|---|
| gpt2 (original choice) | 7.4x | 15.4x | 15.1x |
| MuRIL (Indic-aware) | 1.17x | 1.05x | 1.17x |

**The original report's number was not just imprecise — it was
measuring the cost of a tokenizer choice, not a property of the
languages.** With GPT-2, the disparity is worse than reported, and
Tamil/Malayalam (never tested by the intern) are far worse still. With
an Indic-aware tokenizer, the disparity nearly disappears: 5–17%
overhead, not 500–1400%.

## Recommendation

**Do not budget 6x serving cost for Hindi.** Instead: route
Hindi/Tamil/Malayalam (and likely other Indic-language) traffic to a
model using an Indic-aware tokenizer (e.g. MuRIL-family or equivalent)
rather than an English-centric one. This is directionally the same
recommendation as the original report ("specialized Indic
tokenizer/model"), but the justification and the magnitude are
different: the specialized tokenizer isn't a hedge against an inherent
6x cost, it is the fix that removes nearly all of the measured
disparity. Budget for roughly 5–20% overhead on Indic traffic under a
correctly-chosen tokenizer, not 6x.

## Biggest caveat

This is measured on FLORES-200 dev — formal, general-domain written
text (news/educational/travel style). Production traffic is likely
more conversational, may include code-mixing (English words embedded
in Hindi/Tamil/Malayalam text, common in real usage), and may skew
toward shorter queries. Fertility is sensitive to register and
code-mixing in ways this corpus cannot capture. The corrected ratios
above should be treated as a reasonable estimate under the *right*
tokenizer, not an exact production number.

## Metric to monitor in production

**Actual tokens-per-request, by language, measured continuously against
this analysis's predicted ratios (~1.05–1.2x for Hindi/Tamil/Malayalam
vs English under an Indic-aware tokenizer).** If observed production
ratios drift materially above this range, it's a signal that either
(a) production traffic differs from this analysis's corpus assumptions
(e.g. heavier code-mixing than expected), or (b) the deployed tokenizer
isn't performing as measured here — either way, a concrete trigger to
re-run this audit rather than let a stale assumption drive capacity
planning silently.
