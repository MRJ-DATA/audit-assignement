#!/usr/bin/env python3
"""
b3_goodput_math.py -- B3: verify the reported_tok_s misreading and
compute honest goodput for the batch-24 long-prompt row, two
independent ways.

Re-runnable against the actual bench_log.csv so numbers can be
re-derived live in the defense session.
"""

import csv


def verify_reported_tok_s_formula(csv_path):
    """Test hypothesis: reported_tok_s = num_requests*(prompt_len+gen_len)/wall_clock_s"""
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))

    print(f"{'batch':<6}{'prompt':<8}{'gen':<6}{'reported':<12}{'predicted':<12}{'match?'}")
    all_match = True
    for r in rows:
        nr, pl, gl = int(r['num_requests']), int(r['prompt_len']), int(r['gen_len'])
        wc, reported = float(r['wall_clock_s']), float(r['reported_tok_s'])
        predicted = nr * (pl + gl) / wc
        match = abs(predicted - reported) < 0.5
        all_match &= match
        print(f"{r['batch_size']:<6}{pl:<8}{gl:<6}{reported:<12}{predicted:<12.2f}"
              f"{'YES' if match else 'no'}")
    print(f"\nAll rows match hypothesis: {all_match}")
    return rows


def batch24_goodput(rows):
    """Compute honest goodput for the batch=24, prompt=3584 row, two ways."""
    row = next(r for r in rows
               if r['batch_size'] == '24' and r['prompt_len'] == '3584')
    nr = int(row['num_requests'])
    gl = int(row['gen_len'])
    wc = float(row['wall_clock_s'])
    itl = float(row['itl_ms_p50'])
    reported = float(row['reported_tok_s'])

    method1 = nr * gl / wc
    method2 = nr * (1000 / itl)

    print(f"\nbatch-24 row: reported_tok_s = {reported}")
    print(f"Method 1 (gen tokens / wall clock): {method1:.2f} tok/s")
    print(f"Method 2 (via itl_ms_p50):          {method2:.2f} tok/s")
    print(f"Overstatement factor: {reported/method1:.1f}x - {reported/method2:.1f}x")


if __name__ == "__main__":
    rows = verify_reported_tok_s_formula("../starter_kit/bench_log.csv")
    batch24_goodput(rows)
