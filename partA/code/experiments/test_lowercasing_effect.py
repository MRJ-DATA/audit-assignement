#!/usr/bin/env python3
"""
test_lowercasing_effect.py -- A2 Finding candidate: does line.lower()
differentially affect English vs Indic-script fertility?

RUN THIS LOCALLY (needs real tiktoken, which needs internet access to
fetch its vocab file -- this sandbox's network is restricted and can't
reach openaipublic.blob.core.windows.net).

    pip install tiktoken
    python test_lowercasing_effect.py

Prints results to stdout -- paste the output back into the conversation
so we can interpret it together and add it to partA/findings.md.
"""

import tiktoken

enc = tiktoken.get_encoding("gpt2")


def fertility(lines, lowercase):
    """Same logic as fertility.py's analyze(), isolating ONLY the
    lowercase step so we can toggle it on/off and see the effect."""
    per_line = []
    for line in lines:
        if lowercase:
            line = line.lower()
        tokens = enc.encode(line)
        words = line.split(" ")
        per_line.append(len(tokens) / len(words))
    return sum(per_line) / len(per_line)


def main():
    with open("../../corpus/prepared/eng.txt", encoding="utf-8") as f:
        eng_lines = [l.rstrip("\n") for l in f]
    with open("../../corpus/prepared/hin.txt", encoding="utf-8") as f:
        hin_lines = [l.rstrip("\n") for l in f]

    eng_with_lower = fertility(eng_lines, lowercase=True)
    eng_no_lower = fertility(eng_lines, lowercase=False)
    hin_with_lower = fertility(hin_lines, lowercase=True)
    hin_no_lower = fertility(hin_lines, lowercase=False)

    print(f"English fertility WITH  lowercasing: {eng_with_lower:.4f}")
    print(f"English fertility WITHOUT lowercasing: {eng_no_lower:.4f}")
    eng_delta_pct = (eng_with_lower - eng_no_lower) / eng_no_lower * 100
    print(f"  -> lowercasing changes English fertility by {eng_delta_pct:+.2f}%")
    print()
    print(f"Hindi fertility WITH  lowercasing: {hin_with_lower:.4f}")
    print(f"Hindi fertility WITHOUT lowercasing: {hin_no_lower:.4f}")
    hin_delta_pct = (hin_with_lower - hin_no_lower) / hin_no_lower * 100
    print(f"  -> lowercasing changes Hindi fertility by {hin_delta_pct:+.2f}%")
    print()

    ratio_with_lower = hin_with_lower / eng_with_lower
    ratio_no_lower = hin_no_lower / eng_no_lower
    print(f"Hindi/English fertility ratio WITH  lowercasing (as report does it): {ratio_with_lower:.3f}x")
    print(f"Hindi/English fertility ratio WITHOUT lowercasing: {ratio_no_lower:.3f}x")
    ratio_delta_pct = (ratio_with_lower - ratio_no_lower) / ratio_no_lower * 100
    print(f"  -> lowercasing changes the REPORTED RATIO by {ratio_delta_pct:+.2f}%")


if __name__ == "__main__":
    main()
