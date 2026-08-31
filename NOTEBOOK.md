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
