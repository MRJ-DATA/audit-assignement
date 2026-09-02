# NOTEBOOK.md

Chronological log of this audit. Entries are added in the order things
actually happened, including dead ends and revisions. Nothing here is
cleaned up after the fact.

Format per entry:

```
## [YYYY-MM-DD HH:MM] <short title>
**Hypothesis / question:**
**What I did (exact command):**
**Result:**
**Interpretation / next step:**
```

---

## [setup] Repo skeleton created

Set up the submission structure per the assignment spec:

```
your-submission/
  NOTEBOOK.md
  AI_USAGE.md
  partA/
    corpus/     <- A1 eval corpus + prep scripts
    code/       <- corrected fertility measurement code
    results/    <- output tables / numbers
  partB/
  partC/memo.md
  starter_kit/  <- original files as given, untouched, for reference
```

Copied the four given artifacts (`fertility.py`, `REPORT_v0.md`,
`model_spec.md`, `bench_log.csv`, `corpus_sample/`) into `starter_kit/`
unmodified, so the audit always has an untouched baseline to diff
against.

**Next step:** A1 — build a real multilingual eval corpus. The given
`corpus_sample/` (10 English + 10 Hindi lines) is explicitly called out
in the assignment as a smoke-test toy, not something to draw conclusions
from.

---

## [A1] Checked whether given corpus_sample is actually parallel

**Hypothesis:** the assignment describes corpus_sample as "parallel,
line-by-line" -- verify before trusting it.

**What I did:** lined up eng_sample.txt and hin_sample.txt side by side
(`paste -d'|' eng_sample.txt hin_sample.txt`) and read each pair.

**Result:** NOT parallel. e.g. line 5 English = "The train arrived
exactly on time." but line 5 Hindi = "क्या तुमने खाना खा लिया?" (Have you
eaten?). The train sentence is actually Hindi line 6. Both files clearly
draw from the same topic pool (Bengaluru, Mysuru, trains, cricket, tea)
but lines are shuffled independently per language, not aligned.

**Interpretation:** this is a real, demonstrable data quality problem in
the starter kit, separate from anything in fertility.py. Any per-line
comparison logic run against this file pair would be comparing token
counts of unrelated sentences. Worth citing as a finding in A2, and
strong motivation for A1 sourcing a properly-aligned real corpus instead.

---

## [A1] Attempted to fetch FLORES-200 directly in the analysis sandbox

**Hypothesis:** could pull FLORES-200 (eng/hin/tam/mal) directly via
github.com or raw.githubusercontent.com, since those are the only
outbound domains this sandbox allows.

**What I did:** `curl -sI` against facebookresearch/flores on GitHub,
then `GET /repos/.../git/trees/main?recursive=1` via the GitHub API on a
mirror fork, looking for committed data files under flores200/.

**Result:** dead end. The FLORES-200 GitHub repos contain only code and
docs -- the actual sentence data is distributed as a separate archive
hosted on Facebook's file servers (fbaipublicfiles.com) and mirrored on
HuggingFace (huggingface.co). Neither host is in this sandbox's allowed
outbound domain list, so the data itself is unreachable from here.

**Interpretation / next step:** downloading FLORES-200 has to happen on
a machine with unrestricted internet access (i.e. locally), not in this
analysis environment. Plan: download dev split for eng_Latn, hin_Deva,
tam_Taml, mal_Mlym locally, commit the four raw files into
partA/corpus/raw/, then continue the corpus-prep work against those.

---

## [A1] FLORES-200 download, attempt 2 (curl + tinyurl on Windows)

**What happened:** `curl.exe -L -o flores200.tar.gz "https://tinyurl.com/flores200dataset"`
downloaded successfully per curl's own output, but the resulting file
was only ~10KB and `tar` failed with "Unrecognized archive format" --
almost certainly curl saved a landing/redirect HTML page rather than the
real archive (common with shortlinks that go through an interstitial
page rather than a direct redirect).

**Fix:** opened the tinyurl link directly in a browser instead of curl.
Browser followed the real redirect chain and downloaded the actual
archive (flores200_dataset.tar.gz, ~25.6MB).

**Verification, once uploaded:**
```
tar -tzf flores200.tar.gz | wc -l        -> 414 entries (dev/ + devtest/, ~200 langs each)
ls flores200_dataset/dev/ | grep -E "eng_Latn|hin_Deva|tam_Taml|mal_Mlym"
  -> all 4 present
wc -l on each of the 4 .dev files -> 997 lines, every file, identical count
sed -n '1p' on each of the 4 files -> same sentence (Stanford diagnostic
  chip story) in all 4 languages, confirmed by reading
```

**Interpretation:** this is a real, correctly parallel corpus -- 997
matched sentence pairs across eng/hin/tam/mal, a very different
situation from the shuffled corpus_sample given in the starter kit.
Copied eng_Latn.dev, hin_Deva.dev, tam_Taml.dev, mal_Mlym.dev into
partA/corpus/raw/ as the base to build the A1 eval set from.

**Next step:** decide sample size (997 is the full dev split -- probably
want to subset it and document why), write the corpus-prep script, and
write the "what this corpus can't tell you" paragraph A1 requires.

---

## [A1] Decision: sample size

**Decision:** use the full 997-line FLORES-200 dev split for all 4
languages, no subsetting.

**Reasoning:** tokenizing ~1000 short sentences with 2 tokenizers is
computationally trivial (seconds), so subsetting buys no real speed. A
subset would need its own justification (why N and not the full set),
which is an extra thing to defend for no real benefit. Using the full
official split is the more defensible, simpler choice, and gives more
stable fertility averages (less noise from any single sentence).

---

## [A1] Wrote and ran partA/code/prepare_corpus.py

**What it does:** loads the 4 raw FLORES-200 .dev files, verifies all 4
have identical line counts (i.e. still aligned) and no empty lines,
writes them out under corpus/prepared/{eng,hin,tam,mal}.txt with short
codes. Deliberately does NOT lowercase or otherwise transform the text
-- that logic belongs in the measurement script (A2/A3), not corpus
prep, so each step is independently auditable.

**First run: crashed.**
```
FileNotFoundError: .../partA/code/corpus/raw/eng_Latn.dev
```
Bug in my own path logic: script lives in partA/code/, but I wrote
`pathlib.Path(__file__).parent / "corpus"`, which resolves to
partA/code/corpus/ instead of partA/corpus/. Fixed by using
`.parent.parent` instead of `.parent`.

**Second run: succeeded.**
```
eng: 997 lines loaded from eng_Latn.dev
hin: 997 lines loaded from hin_Deva.dev
tam: 997 lines loaded from tam_Taml.dev
mal: 997 lines loaded from mal_Mlym.dev
All 4 languages aligned at 997 lines. OK.
```
Spot-checked line 1 of all 4 prepared files by eye -- same sentence
(Stanford diagnostic chip story) in all 4 languages, matches the raw
files. corpus/prepared/{eng,hin,tam,mal}.txt now ready to use as the A1
eval corpus.

**Next step:** write up A1's required documentation (corpus size,
domain, preprocessing, "what this corpus can't tell you" paragraph).

---

## [A2] Confirmed: this sandbox cannot run real tokenizers

**What I did:** `pip install tiktoken --break-system-packages`, then
`tiktoken.get_encoding("gpt2")`.

**Result:**
```
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url:
https://openaipublic.blob.core.windows.net/gpt-2/encodings/main/vocab.bpe
```
Same root cause as the FLORES-200 download problem: this analysis
sandbox only allows outbound requests to a fixed allowlist of domains
(github.com, pypi.org, npmjs.com, etc). `pip install tiktoken` succeeds
(pypi.org is allowed) but tiktoken fetches its actual vocab file at
*runtime* from a different host not on the allowlist, so encoding calls
fail. Same problem will apply to any HuggingFace tokenizer
(`AutoTokenizer.from_pretrained`), since huggingface.co isn't allowed
either.

**Interpretation / next step:** all experiment scripts for A2/A3 will be
written here (pure Python logic, no network needed to write code), but
must be *run* locally, where normal internet access lets pip-installed
tokenizer libraries fetch their vocab/model files. Workflow going
forward: write scripts here -> run locally -> paste/upload output back
-> interpret and write up together.

---

## [A2] Finding 1: unused random.seed -- looks suspicious, actually fine

**Hypothesis:** random.seed(1337) is set but random is never called
elsewhere -- probably dead code, but worth verifying it doesn't
silently affect anything before dismissing it.

**What I did:** made fertility_no_random.py, identical to the original
except import random / random.seed(1337) removed. Ran both versions'
analyze() against the same 3 sentences with an identical fake
deterministic encoder (fine for this test -- claim is about random's
effect specifically, not about real fertility numbers).

**Result:** byte-identical output, both fertility and tok/char, with
random present vs removed. IDENTICAL: True.

**Interpretation:** confirmed dead code, zero effect. This is the
"looks suspicious but is fine" finding A2 asks for. Logged as Finding 1
in partA/findings.md.

**Next step:** move to the lowercasing claim (line 60) -- differential
effect on cased vs uncased scripts. This one needs a real tokenizer to
measure properly, so will need to be run locally.

---

## [A2] Finding 2: lowercasing bug, run locally with real tiktoken

**Hypothesis:** lowercasing before tokenizing is a no-op for Hindi (no
case in Devanagari) but changes English tokenization, since GPT-2's
vocab is case-sensitive. Guessed this would make English fertility go
DOWN (assumed lowercase = simpler/more common tokens) and thus make the
Hindi/English ratio look artificially LARGER than true.

**What I did:** wrote test_lowercasing_effect.py, ran locally (pip
install tiktoken; local machine has normal internet access, unlike this
sandbox). Computed fertility with vs without the lowercase step, full
997-sentence eng/hin corpus, real gpt2 tokenizer.

**Result (real numbers, not simulated):**
```
English WITH lowercasing: 1.2825   WITHOUT: 1.2367   (+3.71%)
Hindi   WITH lowercasing: 7.8088   WITHOUT: 7.8081   (+0.01%, ~noise)
Ratio   WITH lowercasing: 6.089x   WITHOUT: 6.314x    (-3.57%)
```

**This CONTRADICTS my initial hypothesis on direction.** English
fertility went UP (worse) when lowercased, not down. So lowercasing
actually makes the reported Hindi/English gap SMALLER than the true gap,
not larger as I first guessed. Good reminder of why the evidence rule
exists -- my intuition about direction was wrong, and only running the
real numbers caught it.

**Interpretation:** real, measurable, differential bug (English +3.71%,
Hindi ~0%), but small relative to the ~6x headline gap -- a real
contributor, not the dominant explanation for the report's number.
Logged as Finding 2 in partA/findings.md.

**Next step:** the whitespace-word denominator itself -- likely the
conceptual bug A2 is looking for. Also want to check the empty-string
-from-double-space issue and per-line-vs-pooled averaging.

---

## [A2] Finding 3: whitespace-word denominator is not cross-lingually fair

**Hypothesis:** "words" via split(" ") might not mean the same amount
of content in agglutinative languages (Tamil, Malayalam) vs English/
Hindi. If true, this would be the conceptual bug A2 asks for.

**What I did:** wrote test_word_denominator.py, ran directly in sandbox
(no tokenizer needed -- corpus-only check). Used the fact that all 4 A1
corpora are sentence-aligned to compare whitespace-word counts for
IDENTICAL content across languages.

**Result:**
```
eng: 21.02 avg words/sentence (baseline)
hin: 24.71 (1.176x eng)
tam: 16.28 (0.775x eng)
mal: 14.55 (0.692x eng)
correlations with eng: hin r=0.895, tam r=0.858, mal r=0.842
```

**Interpretation:** confirmed -- for the same content, Malayalam and
Tamil pack meaning into visibly fewer whitespace-"words" than English,
while Hindi uses visibly more. This directly biases tokens/word: Tamil/
Malayalam fertility is understated, Hindi's is overstated, purely from
denominator choice, independent of any tokenizer behavior. This is the
conceptual bug -- logged as Finding 3 in partA/findings.md. Confidence
high: this doesn't depend on tokenizer correctness at all, just on
corpus alignment, which we already verified in A1.

**Next step:** check the double-space -> empty-word issue, and the
per-line-average vs pooled-average question. Then move to A3 (corrected
analysis with proper denominators).
