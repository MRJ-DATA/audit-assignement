#!/usr/bin/env python3
"""
prepare_corpus.py -- A1 eval corpus preparation

Builds the real multilingual eval corpus from raw FLORES-200 dev-split
files, replacing the toy corpus_sample/ given in the starter kit.

Input:  partA/corpus/raw/{eng_Latn,hin_Deva,tam_Taml,mal_Mlym}.dev
        (997 parallel sentences each, one sentence per line, aligned
        by line number across all four files)

Output: partA/corpus/prepared/{eng,hin,tam,mal}.txt
        (same content, renamed to short language codes, UTF-8, one
        sentence per line, no other transformation)

This script deliberately does NOT lowercase, strip punctuation, or
otherwise "clean" the text beyond stripping trailing newlines/whitespace
and verifying line-count alignment. Any normalization for fertility
measurement purposes happens later, in the measurement script itself
(partA/code/), not here -- corpus prep and metric computation are kept
separate so each step can be audited independently.
"""

import pathlib

# this script lives in partA/code/, corpus data lives in partA/corpus/
RAW_DIR = pathlib.Path(__file__).parent.parent / "corpus" / "raw"
OUT_DIR = pathlib.Path(__file__).parent.parent / "corpus" / "prepared"

# FLORES-200 filename -> short code used throughout this submission
LANGS = {
    "eng_Latn": "eng",
    "hin_Deva": "hin",
    "tam_Taml": "tam",
    "mal_Mlym": "mal",
}


def load(path: pathlib.Path) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    corpora = {}
    for flores_name, code in LANGS.items():
        lines = load(RAW_DIR / f"{flores_name}.dev")
        corpora[code] = lines
        print(f"{code}: {len(lines)} lines loaded from {flores_name}.dev")

    # verify alignment: every language must have the same line count,
    # since FLORES-200 lines are matched by index across languages
    counts = {code: len(lines) for code, lines in corpora.items()}
    assert len(set(counts.values())) == 1, (
        f"Line count mismatch across languages -- corpus is NOT aligned: {counts}"
    )
    n = next(iter(counts.values()))
    print(f"\nAll {len(corpora)} languages aligned at {n} lines. OK.")

    # spot-check: confirm no empty lines survived
    for code, lines in corpora.items():
        empties = sum(1 for l in lines if l.strip() == "")
        assert empties == 0, f"{code} has {empties} empty lines"

    # write prepared files
    for code, lines in corpora.items():
        out_path = OUT_DIR / f"{code}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"wrote {out_path} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
