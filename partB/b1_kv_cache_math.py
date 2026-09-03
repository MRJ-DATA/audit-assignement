#!/usr/bin/env python3
"""
b1_kv_cache_math.py -- B1: KV-cache bytes/token and max concurrent
4096-token sequences, from model_spec.md alone. Then check the
prediction against bench_log.csv.

Kept simple and re-runnable so the numbers can be re-derived live in
the defense session if asked, or modified on the spot (e.g. "what if
gpu_memory_utilization were 0.85 instead?").
"""

GiB = 1024**3

# --- from model_spec.md ---
layers = 28
kv_heads = 8       # GQA -- KV heads, not the 24 query heads
head_dim = 128
bytes_per_elem = 2  # fp16

total_gpu_mem_gib = 24
util = 0.92
params = 4.2e9
non_kv_overhead_gib = 1.6
seq_len = 4096  # max_model_len


def kv_bytes_per_token():
    return 2 * layers * kv_heads * head_dim * bytes_per_elem


def max_concurrent_sequences(seq_len=seq_len, util=util,
                              non_kv_overhead_gib=non_kv_overhead_gib):
    usable_gib = total_gpu_mem_gib * util
    weight_gib = (params * 2) / GiB
    kv_budget_gib = usable_gib - weight_gib - non_kv_overhead_gib

    bytes_per_seq = kv_bytes_per_token() * seq_len
    gib_per_seq = bytes_per_seq / GiB

    return kv_budget_gib / gib_per_seq, kv_budget_gib, gib_per_seq


if __name__ == "__main__":
    kv_bpt = kv_bytes_per_token()
    print(f"KV bytes/token = {kv_bpt} ({kv_bpt/1024} KiB)")

    max_seqs, budget, per_seq = max_concurrent_sequences()
    print(f"KV cache budget = {budget:.4f} GiB")
    print(f"bytes per {seq_len}-token sequence = {per_seq} GiB")
    print(f"max concurrent sequences = {max_seqs:.2f} -> floor {int(max_seqs)}")
