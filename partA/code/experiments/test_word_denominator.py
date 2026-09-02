#!/usr/bin/env python3
"""
test_word_denominator.py -- A2 Finding candidate: is "whitespace-split
word count" a fair, comparable unit across English/Hindi/Tamil/Malayalam?

The concern: fertility.py's `words = line.split(" ")` treats a
whitespace-delimited chunk as "one word" for every language. But this
denominator is only meaningful cross-lingually if it holds a roughly
constant amount of MEANING constant across languages. Whitespace
segmentation conventions differ a lot: Tamil and Malayalam are
agglutinative (a single whitespace-delimited "word" can bundle what
would be several separate English words worth of meaning -- postpositions,
case markers, etc. glued onto the stem). If so, a language could look
artificially "cheap" (low fertility) not because its tokenizer is more
efficient, but because its whitespace-word denominator is silently
counting bigger units to begin with.

This script does NOT need a real tokenizer -- it's a corpus-only check:
does whitespace-word count per sentence track the same underlying
content across languages, using the fact that all 4 corpora are
sentence-aligned (line N = same meaning in all 4 languages).

RUN THIS LOCALLY OR IN THE SANDBOX -- no tokenizer/network needed.
"""

import statistics


def load(path):
    with open(path, encoding="utf-8") as f:
        return [l.rstrip("\n") for l in f]


def main():
    langs = {
        "eng": "../../corpus/prepared/eng.txt",
        "hin": "../../corpus/prepared/hin.txt",
        "tam": "../../corpus/prepared/tam.txt",
        "mal": "../../corpus/prepared/mal.txt",
    }

    word_counts = {}
    for code, path in langs.items():
        lines = load(path)
        word_counts[code] = [len(l.split(" ")) for l in lines]

    n = len(word_counts["eng"])
    print(f"n = {n} aligned sentences (same content, line-by-line, across all 4 languages)\n")

    print(f"{'lang':<6}{'avg whitespace-words/sentence':>32}{'ratio vs eng':>15}")
    print("-" * 55)
    eng_avg = statistics.mean(word_counts["eng"])
    for code in langs:
        avg = statistics.mean(word_counts[code])
        print(f"{code:<6}{avg:>32.2f}{avg/eng_avg:>15.3f}")

    print()
    print("If whitespace-word counted a comparable UNIT OF MEANING across")
    print("languages, we'd expect these ratios to cluster near 1.0 for a")
    print("sentence-aligned corpus (same content -> similar word count).")
    print("Large deviations suggest 'word' is not a stable cross-lingual unit,")
    print("meaning tokens/word is comparing different things per language")
    print("before a single token is even counted.")

    # also: per-sentence correlation -- does a sentence with more
    # English words also have more Tamil/Malayalam/Hindi words?
    print()
    print("Per-sentence correlation of word count with English (Pearson r):")
    import math
    def pearson(xs, ys):
        n = len(xs)
        mx, my = sum(xs)/n, sum(ys)/n
        cov = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
        sx = math.sqrt(sum((x-mx)**2 for x in xs))
        sy = math.sqrt(sum((y-my)**2 for y in ys))
        return cov / (sx*sy)

    for code in langs:
        if code == "eng":
            continue
        r = pearson(word_counts["eng"], word_counts[code])
        print(f"  eng vs {code}: r = {r:.3f}")


if __name__ == "__main__":
    main()
