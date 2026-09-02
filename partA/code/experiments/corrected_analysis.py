#!/usr/bin/env python3
"""
corrected_analysis.py -- A3: corrected cross-language fertility analysis

Fixes applied vs the original fertility.py (see partA/findings.md):
  - no lowercasing (Finding 2)
  - no whitespace-word denominator used as the primary metric (Finding 3)
  - uses .split() not .split(" ") where word count is reported at all
    (avoids the empty-string issue from double-spaces)

Two tokenizers:
  - gpt2       (what the original report used, tiktoken)
  - muril      (google/muril-base-cased, Indic-aware, HuggingFace)

Three denominators, none of which rely on "word":
  - tokens per SENTENCE   (corpus is aligned -> directly comparable:
                             "how many tokens to say the same thing")
  - tokens per UTF-8 BYTE  (well-defined regardless of script;
                             also maps to real network/storage cost)
  - tokens per GRAPHEME CLUSTER (visual character -- NOT the same as
                             len(string), which counts Unicode codepoints;
                             Devanagari/Tamil/Malayalam often need
                             multiple codepoints per visual character)

RUN THIS LOCALLY:
    pip install tiktoken transformers regex
    python corrected_analysis.py

Prints a full results table + ratios vs English for every
(tokenizer, denominator) combination. Paste the full output back for
interpretation and write-up.
"""

import regex  # pip install regex -- provides \X (extended grapheme cluster)


LANGS = ["eng", "hin", "tam", "mal"]


def load_corpus():
    corpus = {}
    for code in LANGS:
        with open(f"../../corpus/prepared/{code}.txt", encoding="utf-8") as f:
            corpus[code] = [l.rstrip("\n") for l in f]
    return corpus


def get_tokenizers():
    tokenizers = {}

    import tiktoken
    enc = tiktoken.get_encoding("gpt2")
    tokenizers["gpt2"] = enc.encode

    from transformers import AutoTokenizer
    muril = AutoTokenizer.from_pretrained("google/muril-base-cased")
    tokenizers["muril"] = lambda s: muril.encode(s, add_special_tokens=False)

    return tokenizers


def grapheme_count(s):
    return len(regex.findall(r"\X", s))


def byte_count(s):
    return len(s.encode("utf-8"))


def main():
    corpus = load_corpus()
    tokenizers = get_tokenizers()

    n_sentences = len(corpus["eng"])
    assert all(len(corpus[c]) == n_sentences for c in LANGS), "corpus misaligned!"

    # precompute denominator totals per language (tokenizer-independent)
    denom_totals = {}
    for code in LANGS:
        lines = corpus[code]
        denom_totals[code] = {
            "sentence": n_sentences,
            "byte": sum(byte_count(l) for l in lines),
            "grapheme": sum(grapheme_count(l) for l in lines),
        }

    results = {}  # results[tokenizer][lang] = total_tokens
    for tok_name, encode in tokenizers.items():
        results[tok_name] = {}
        for code in LANGS:
            total_tokens = sum(len(encode(l)) for l in corpus[code])
            results[tok_name][code] = total_tokens
            print(f"[{tok_name}] {code}: {total_tokens} total tokens "
                  f"over {n_sentences} sentences")

    print("\n" + "=" * 90)
    print("FULL RESULTS TABLE: tokens per denominator unit, by tokenizer x language")
    print("=" * 90)

    for tok_name in tokenizers:
        print(f"\n--- tokenizer: {tok_name} ---")
        print(f"{'lang':<6}{'tok/sentence':>16}{'tok/byte':>14}{'tok/grapheme':>16}")
        print("-" * 52)
        for code in LANGS:
            total_tok = results[tok_name][code]
            per_sentence = total_tok / denom_totals[code]["sentence"]
            per_byte = total_tok / denom_totals[code]["byte"]
            per_grapheme = total_tok / denom_totals[code]["grapheme"]
            print(f"{code:<6}{per_sentence:>16.3f}{per_byte:>14.4f}{per_grapheme:>16.4f}")

    print("\n" + "=" * 90)
    print("RATIOS vs ENGLISH (>1 means MORE tokens needed than English for same content)")
    print("=" * 90)

    for tok_name in tokenizers:
        print(f"\n--- tokenizer: {tok_name} ---")
        print(f"{'lang':<6}{'sentence ratio':>18}{'byte ratio':>14}{'grapheme ratio':>18}")
        print("-" * 56)
        eng_tok = results[tok_name]["eng"]
        eng_per_sentence = eng_tok / denom_totals["eng"]["sentence"]
        eng_per_byte = eng_tok / denom_totals["eng"]["byte"]
        eng_per_grapheme = eng_tok / denom_totals["eng"]["grapheme"]
        for code in LANGS:
            total_tok = results[tok_name][code]
            per_sentence = total_tok / denom_totals[code]["sentence"]
            per_byte = total_tok / denom_totals[code]["byte"]
            per_grapheme = total_tok / denom_totals[code]["grapheme"]
            print(f"{code:<6}"
                  f"{per_sentence/eng_per_sentence:>18.3f}"
                  f"{per_byte/eng_per_byte:>14.3f}"
                  f"{per_grapheme/eng_per_grapheme:>18.3f}")


if __name__ == "__main__":
    main()
