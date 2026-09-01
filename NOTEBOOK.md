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
