# A1 — Eval Corpus

## What we used

[FLORES-200](https://github.com/facebookresearch/flores), the `dev`
split, for four languages: English (`eng_Latn`), Hindi (`hin_Deva`),
Tamil (`tam_Taml`), Malayalam (`mal_Mlym`).

FLORES-200 was chosen over building a custom corpus because it is a
professionally translated, sentence-aligned, publicly documented
benchmark already used across the MT and multilingual-NLP field — using
it means the "is this actually parallel" question is answered by the
dataset's own provenance rather than something we have to establish
ourselves. This directly replaces `corpus_sample/` from the starter kit,
which we found (see NOTEBOOK.md) is *not* actually parallel — its
English and Hindi lines are drawn from the same topic pool but are not
line-aligned translations of each other.

Raw files: `partA/corpus/raw/{eng_Latn,hin_Deva,tam_Taml,mal_Mlym}.dev`
Prepared files: `partA/corpus/prepared/{eng,hin,tam,mal}.txt`
(produced by `partA/code/prepare_corpus.py`)

## Size

997 sentences per language, all four languages aligned by line number
(line N is the same sentence in all four languages). This is the full
FLORES-200 `dev` split — not subsetted. We verified alignment
programmatically (equal line counts across all four files, no empty
lines) and manually (read line 1 in all four languages and confirmed it
is the same sentence — a story about a Stanford diagnostic-chip
announcement).

Descriptive stats per language (997 lines each):

| lang | avg char length | median char length | avg whitespace-split "words" |
|---|---|---|---|
| eng | 125.6 | 120 | 21.0 |
| hin | 125.8 | 122 | 24.7 |
| tam | 146.6 | 142 | 16.3 |
| mal | 142.5 | 137 | 14.6 |

Note already: English and Hindi have almost identical *character*
length on average (125.6 vs 125.8) for the same sentences, but Hindi's
whitespace-word count is noticeably higher (24.7 vs 21.0) while Tamil
and Malayalam's whitespace-word counts are *lower* than English despite
longer character length. This is an early hint that "words" (via
whitespace splitting) may not mean a comparable unit of meaning across
these languages — directly relevant to A2/A3's denominator question.

## Domain

FLORES-200 sentences are drawn from Wikinews, Wikijunior, and Wikivoyage
articles — general-domain news, educational, and travel writing.
Sentences tend to be moderately long, complete, well-formed written
sentences (not dialogue, not code-mixed, not social-media style, not
short commands).

## Preprocessing

`prepare_corpus.py` performs the minimum necessary to get the raw
FLORES files into a consistent format: strips trailing newlines,
verifies line-count alignment across all four languages, verifies no
empty lines, writes UTF-8 text files with short language codes. It
deliberately does **not** lowercase, strip punctuation, or normalize
Unicode — any such transformation is done explicitly (and separately)
in the fertility measurement code in A2/A3, so that corpus preparation
and metric computation can be audited independently of each other.

## What this corpus cannot tell you

This corpus is general-domain written news/educational/travel text —
it says nothing about fertility on the kind of text a production system
would actually see, e.g. chat-style conversational turns, code-mixed
text (common in real Indic-language usage — mixing English words into
Hindi/Tamil sentences), short commands or queries, informal/social
register, or domain-specific jargon (support tickets, product
descriptions, etc). Fertility is sensitive to text style — chat-style
short sentences and code-mixed text in particular tokenize differently
than clean formal writing — so a routing/cost decision based purely on
this corpus is only as good as the assumption that production traffic
resembles FLORES-style formal writing, which for most real serving
workloads it does not.

Additionally, 997 sentences per language, while far larger than the
10-line toy sample, is still a modest sample by NLP-eval standards.
Per-language averages here should be read as reasonably stable point
estimates, not as tight, low-variance measurements — we report spread
(not just the mean) in A3 for this reason.

Finally, this corpus covers 4 of the many languages a production system
may serve. Fertility patterns for these four languages should not be
assumed to generalize to other Indic (or non-Indic) languages without
separately measuring them.
