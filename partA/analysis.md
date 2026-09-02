# A3 — Corrected Analysis

Full output: `results/corrected_analysis_output.txt`
Script: `code/experiments/corrected_analysis.py`
Corpus: A1's 997-sentence aligned FLORES-200 subset (eng/hin/tam/mal)

Fixes applied relative to the original `fertility.py`, per A2's findings:
no lowercasing (Finding 2), no whitespace-word denominator used as the
primary metric (Finding 3).

## Results

**Tokenizer: gpt2** (what the original report used)

| lang | tok/sentence | ratio vs eng | tok/byte | ratio vs eng | tok/grapheme | ratio vs eng |
|---|---|---|---|---|---|---|
| eng | 25.82 | 1.00 | 0.2055 | 1.00 | 0.2056 | 1.00 |
| hin | 192.18 | 7.44 | 0.5945 | 2.89 | 2.3247 | 11.31 |
| tam | 398.36 | 15.43 | 0.9959 | 4.85 | 4.2043 | 20.45 |
| mal | 390.79 | 15.14 | 0.9955 | 4.85 | 5.1520 | 25.06 |

**Tokenizer: MuRIL** (`google/muril-base-cased`, Indic-aware)

| lang | tok/sentence | ratio vs eng | tok/byte | ratio vs eng | tok/grapheme | ratio vs eng |
|---|---|---|---|---|---|---|
| eng | 26.44 | 1.00 | 0.2104 | 1.00 | 0.2106 | 1.00 |
| hin | 30.82 | 1.17 | 0.0954 | 0.45 | 0.3729 | 1.77 |
| tam | 27.88 | 1.05 | 0.0697 | 0.33 | 0.2942 | 1.40 |
| mal | 30.98 | 1.17 | 0.0789 | 0.38 | 0.4084 | 1.94 |

## Interpretation

**Tokenizer choice, not the code bugs from A2, is the dominant source
of error in the original report.** The original report's headline
number (Hindi is 5.89x English) is actually an *understatement* of how
bad GPT-2 is for Indic scripts once measured properly and extended to
Tamil/Malayalam, which the intern never tested: by sentence, GPT-2
needs 7.4x more tokens for Hindi, and a striking 15.1-15.4x more for
Tamil and Malayalam. Tamil's tok/byte ratio under GPT-2 is 0.9959 --
essentially one token per raw UTF-8 byte -- which indicates GPT-2 is
falling back to near-byte-level fragmentation for Tamil, consistent
with a tokenizer whose training data contained little to no Tamil text
and therefore never learned efficient Tamil subword units.

Switching to an Indic-aware tokenizer (MuRIL) closes almost all of this
gap: by sentence, Hindi/Tamil/Malayalam need only 5-17% more tokens
than English, not 6-15x. This is the single most consequential finding
of this audit -- it says the original report's "budget 6x serving cost
for Hindi" conclusion is not simply imprecise, it is measuring the cost
of a *tokenizer choice*, not an inherent property of the languages.

**A caution about `tok/byte`: it is also a distorted denominator, in
the opposite direction from `tok/word`.** Under MuRIL, all three Indic
languages show byte ratios *below* 1.0 (0.33-0.45x English) -- they
look cheaper than English by this metric. This is not because MuRIL is
unusually efficient for these languages; it's because Devanagari,
Tamil, and Malayalam characters are encoded as 3 bytes each in UTF-8,
versus 1 byte for English ASCII characters. So `tok/byte` is skewed by
script encoding density, the same way `tok/word` (A2 Finding 3) was
skewed by morphological word-density -- just pulling the ratio in the
opposite direction. Neither `tok/word` nor `tok/byte` holds the actual
quantity that matters -- content/meaning -- constant across languages.

**`tok/sentence`, computed on a sentence-aligned parallel corpus, is
the only one of the three denominators tested that directly holds
content constant.** Line N is the same meaning in all four languages by
construction (verified in A1), so tokens/sentence directly answers "how
many tokens does it cost to say the same thing" -- which is the
question that actually drives serving cost for equivalent traffic.
`tok/grapheme` is a reasonable secondary/diagnostic metric (useful for
understanding *why* a gap exists at the script level) but is not
itself a clean proxy for cost, since visual-character density is also
an artifact of orthographic convention (e.g. combining vowel signs in
Brahmic scripts), not of the amount of content conveyed.

## Which single number should drive the routing/cost decision?

**Tokens per (content-equivalent) request, measured with the tokenizer
actually used by the production model** -- approximated here by
tokens/sentence on an aligned corpus. This is the one number, among
those tested, that holds the thing that actually matters (amount of
content/meaning conveyed) constant across languages, and it maps
directly to what leadership actually needs to know: how many tokens
will an equivalent unit of user-facing work cost per language.

This number is only meaningful paired with an explicit statement of
*which tokenizer* it was measured with -- as shown above, the tokenizer
choice changes this number by roughly an order of magnitude (7-15x
under gpt2 vs ~1.05-1.2x under MuRIL). Reporting a fertility ratio
without naming the tokenizer, as the original report effectively did
(the number was tokenizer-specific but presented as if it were a
language property), is itself part of what went wrong.

## Caveat carried over from A1

These ratios are measured on FLORES-200 dev (Wikinews/Wikijunior/
Wikivoyage-style formal written text, 997 sentences). Production
traffic composition (conversational, code-mixed, short queries, etc.)
may show different ratios; see A1's corpus README for the full caveat.
