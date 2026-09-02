# A2 — Script & Metric Audit

Each finding below follows the evidence rule: claim, isolated
experiment, measured effect, one-sentence conclusion. Experiment scripts
and raw output live in `partA/code/experiments/`.

---

## Finding 1 (looks suspicious, but is FINE): unused `random` import/seed

**Claim:** `fertility.py` imports `random` and calls `random.seed(1337)`
at module load time (lines 21, 25), but `random` is never called
anywhere else in the script. This looks like leftover debug code and
raises the question of whether it silently affects output (e.g. if some
downstream library call depends on global random state) -- but on
inspection, nothing in `analyze()` or `main()` uses randomness, so it
should be inert.

**Experiment:** created `fertility_no_random.py`, an exact copy of the
original with only the `import random` line and the `random.seed(1337)`
line removed. Ran both versions' `analyze()` function against the same
3 test sentences (2 English, 1 Hindi) using an identical deterministic
fake encoder (not a real tokenizer -- irrelevant for this specific test,
since the claim being tested is about `random`'s effect, not about
actual fertility values). See `experiments/run_random_test.py` and
`experiments/random_test_output.txt`.

**Result:**
```
original (with unused random.seed):     (8.26984126984127, 1.5333333333333332)
no_random (random import/seed removed): (8.26984126984127, 1.5333333333333332)
IDENTICAL: True
```

**Conclusion:** the `random` import and seed are dead code with zero
measurable effect on output -- flagging this as a "bug" without this
test would itself be an unverified claim (and A2 explicitly penalizes
that). It's a code-cleanliness nit (dead code should probably be
removed so a future reader doesn't wonder if it matters), but it is not
a correctness bug.

---

## Finding 2 (CODE BUG): lowercasing differentially distorts the
English/Hindi ratio

**Claim:** `analyze()` calls `line.lower()` (line 60) before tokenizing,
justified in a comment as `# lowercase so casing doesn't add noise to
the comparison`. Two separate problems, not one:

1. **It fails its own stated goal.** The comment's premise is that
   lowercasing removes noise neutrally. Our evidence (below) shows it
   does not act neutrally -- it measurably changes English fertility
   while leaving Hindi essentially untouched, i.e. it *introduces*
   asymmetric noise rather than removing it. A step whose entire
   justification is "makes the comparison fairer," but which is
   measurably unfair in one specific direction, doesn't do what its own
   comment claims.
2. **Even where neutral, it wouldn't match the thing being estimated.**
   The report's goal is to estimate real production serving cost.
   Production traffic is not lowercased before being sent to a
   tokenizer -- real requests keep natural capitalization. So this step
   doesn't just risk asymmetry; even in the hypothetical case where it
   *were* perfectly symmetric across languages, it would still be
   measuring a different (artificial) input distribution than what the
   system will actually see in production.

This is not a "computes exactly what it says but the wrong thing"
conceptual bug in the A2 sense (that's Finding 3) -- it's closer to a
correctness bug against the code's own documented intent, confirmed by
direct measurement rather than by an unverified suspicion. Note also
that Devanagari has no case distinction, so lowercasing is a no-op for
Hindi by construction (there is nothing to lowercase); the interesting
question is only what it does to English, and to the ratio.

**Experiment:** `experiments/test_lowercasing_effect.py`, run locally
with real tiktoken (gpt2 encoding) against the full A1 corpus (997
sentences, eng vs hin). Computed fertility with lowercasing (matching
the original script) vs without, for both languages, and compared the
resulting ratio.

**Result** (997 sentences, gpt2 tokenizer):
```
English fertility WITH  lowercasing: 1.2825
English fertility WITHOUT lowercasing: 1.2367   (+3.71% from lowercasing)

Hindi fertility WITH  lowercasing: 7.8088
Hindi fertility WITHOUT lowercasing: 7.8081     (+0.01% from lowercasing, ~noise)

Hindi/English ratio WITH  lowercasing (as report does it): 6.089x
Hindi/English ratio WITHOUT lowercasing:                   6.314x
  -> lowercasing changes the reported ratio by -3.57%
```

**Direction and magnitude:** lowercasing inflates English's fertility by
~3.7% while leaving Hindi essentially untouched (~0%), which makes the
reported Hindi/English disparity ~3.6% *smaller* than the true
(no-lowercasing) comparison. Likely mechanism (plausible, not directly
verified at the token level): GPT-2's vocabulary, trained on naturally-
cased English text, has more efficient tokens for capitalized proper
nouns and sentence-initial words than for their lowercased forms, so
stripping case pushes English text into less efficient tokenization.

**Conclusion:** real, measured, directional bug -- fails its own
documented purpose (asymmetric, not noise-neutral) and doesn't match
production input distribution even where it is close to neutral. Fix:
don't lowercase before tokenizing at all; if casing sensitivity is a
genuine concern, it needs to be handled in a way that's verified
symmetric across languages, not just assumed to be. Effect size here
(~3.6% on the ratio) is real but small relative to the ~6x headline gap
-- a genuine contributor, not the dominant source of the report's
overstated number.

---

## Finding 3 (CONCEPTUAL BUG): whitespace-word count is not a fair
cross-lingual denominator

**Claim:** `fertility.py` computes `words = line.split(" ")` and uses
`len(words)` as the denominator for every language uniformly (line 62,
64). This is not a code bug -- the code does exactly what it says, it
counts whitespace-delimited chunks correctly. The problem is that
"whitespace-delimited chunk" does not correspond to the same amount of
meaning in every language. Tamil and Malayalam are agglutinative
languages where postpositions, case markers, and other grammatical
elements that English expresses as separate words are commonly glued
onto the stem as a single whitespace-delimited unit. If a language's
"words" routinely bundle more meaning per word than English's do,
tokens/word will understate its true fertility -- not because its
tokenizer is more efficient, but because the denominator itself is
bigger to begin with.

**Experiment:** `experiments/test_word_denominator.py`. Uses the fact
that all 4 A1 corpora are sentence-aligned (line N = identical content
in all 4 languages) to directly compare whitespace-word counts for the
*same meaning* across languages -- no tokenizer needed for this check,
only the corpus. Computed average whitespace-words/sentence per
language, and Pearson correlation of per-sentence word count against
English as a sanity check.

**Result** (997 aligned sentences):
```
lang    avg whitespace-words/sentence   ratio vs eng
eng                            21.02            1.000
hin                             24.71            1.176
tam                             16.28            0.775
mal                             14.55            0.692

Per-sentence correlation with English word count (Pearson r):
  eng vs hin: r = 0.895
  eng vs tam: r = 0.858
  eng vs mal: r = 0.842
```

**Direction and magnitude:** for identical content, Malayalam averages
only 69.2% as many whitespace-words as English, and Tamil 77.5%, while
Hindi averages 117.6% as many. That's roughly a 70-percentage-point
spread in what "one word" means across these four languages for the
same underlying sentence. Consequence for the tokens/word metric:
Tamil and Malayalam's reported fertility is systematically UNDERSTATED
relative to true cost-per-meaning (smaller true "word count" inflates
the denominator less than it should), while Hindi's is systematically
OVERSTATED relative to true cost-per-meaning (larger denominator here
than the content actually warrants). The correlations (r=0.84-0.90)
confirm word counts do track sentence length reasonably within a
language, but that doesn't rescue cross-language comparability --
the average ratios show a real, structural, language-dependent skew.

**Conclusion:** this is the conceptual bug A2 is looking for -- the code
computes exactly what it says (tokens per whitespace-delimited word),
but that is not the right thing to compute for a fair cross-language
serving-cost comparison. A denominator that holds actual content/meaning
constant across languages (e.g. tokens per parallel sentence, since the
corpus is aligned; or tokens per grapheme cluster/UTF-8 byte, which are
at least well-defined independent of morphology) is needed instead. This
will be addressed properly in A3.

---

(more findings added as each is investigated)
