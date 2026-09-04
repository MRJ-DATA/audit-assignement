# AI_USAGE.md

Honest account of where AI (Claude) helped and where it misled, added to
as the work progresses. This is not a marketing summary — mistakes and
overreach by the AI go here too.

## Setup phase

- Used Claude to scaffold the repo directory structure and the
  NOTEBOOK.md / AI_USAGE.md templates. Low-risk, mechanical, verified
  by hand.

## A1 — corpus construction

- Claude recommended FLORES-200 and initially tried to fetch it
  directly in its own sandboxed environment. This failed silently at
  first (a tinyurl redirect got saved as a small HTML page instead of
  the real archive, and curl reported "success" while doing so) — the
  small file size was the tell. Had to download the real archive
  myself, in a browser, and upload it back. Claude correctly diagnosed
  the failure once it saw the file size, but didn't catch it from the
  first curl output alone.
- The corpus-prep script Claude wrote had a real bug on first run (a
  wrong relative path, since the script's location and the data's
  location weren't accounted for correctly) — caught immediately by
  the script crashing, not by careful review beforehand. Fixed in one
  line.
- Claude caught, correctly, that the starter kit's own sample corpus
  (`corpus_sample/`) was not actually parallel, despite being described
  as parallel in the assignment — this was verified by directly reading
  the misaligned lines, not just asserted.

## A2 — script/metric audit

- Claude's initial guess about the *direction* of the lowercasing bug
  (Finding 2) was wrong. It hypothesized lowercasing would make the
  Hindi/English ratio look artificially *larger* (worse); the real
  measured result was the opposite — lowercasing made the ratio look
  artificially *smaller*. Only running the actual numbers (locally,
  since tiktoken can't run in Claude's sandbox) caught this. Kept in
  NOTEBOOK.md as a real dead end, not smoothed over.
- I pushed back on Claude's first framing of the lowercasing finding
  ("is this really a bug?"), since the code does execute correctly —
  no crash, no logic error in the narrow sense. Claude's revised
  framing (fails its own stated purpose + doesn't match production
  input distribution) is more precise and is what's now in
  findings.md — worth being able to defend both versions of this
  argument, since a similar challenge could come up live.
- I chose not to include one of Claude's proposed findings (a minor
  double-space/empty-word bug) in the final submission. Not a Claude
  mistake — a scope/priority call I made, and Claude removed it
  cleanly from findings.md and the experiments folder on request.

## A3 — corrected analysis

- Claude designed the tokenizer/denominator experiment, but (as with
  A2) couldn't run it directly — tiktoken and HuggingFace tokenizers
  need to download vocab/model files from hosts not reachable from
  Claude's sandbox. All real numbers in A3 came from running Claude's
  script on my own machine and pasting output back.
- The tok/byte finding (that it's distorted in the *opposite* direction
  from tok/word, due to UTF-8 byte-width differences between scripts)
  was not something Claude planned to look for in advance — it noticed
  the sub-1.0 ratios while writing up the results table and reasoned
  out the UTF-8 explanation afterward. The mechanism is plausible and
  consistent with the numbers, but I have not independently verified it
  at the byte level myself — worth double-checking before stating it as
  fact in the defense.

## B1–B4 — capacity reconciliation

- This part is pure arithmetic and log-reading, so Claude could run
  everything directly and I could check every number by re-running the
  same scripts myself. B3 in particular (the reported_tok_s formula) was
  verified against all 13 rows of the log exactly, not just the 2 rows
  the original report cited — this was Claude's suggestion, and it's
  the strongest single piece of evidence in the whole submission because
  of that exhaustive check.
- Claude made an explicit unit assumption (GiB vs GB) in B1 and stated
  it openly rather than hiding it — worth remembering this is a
  stated assumption, not a given fact, if challenged in the defense.

## C — decision memo

- The recommendation (prompt-engineering as primary path, with a dated
  kill criterion escalating to a rewriter model) is Claude's reasoning,
  laid out explicitly step by step when I asked "why is (c) okay?"
  before I accepted it. The assignment itself says there's no single
  right answer here — this is a defensible judgment call built on
  stated assumptions and arithmetic, not a fact to be taken on faith.
- At my request, Claude rewrote the memo for simpler sentence structure
  without changing content — a readability pass, not a substance
  change; I compared before/after to confirm nothing was altered beyond
  wording.

## Overall

Claude wrote most of the code, calculations, and prose in this
submission. The point of the defense session is that I need to be able
to re-derive every number and defend every claim myself, live — so
treat this file as a map of exactly which claims I've stress-tested
myself (lowercasing direction, the reported_tok_s formula) versus which
ones I'm relying on Claude's reasoning for and should re-verify before
the defense (the tok/byte UTF-8 mechanism in A3, in particular).
