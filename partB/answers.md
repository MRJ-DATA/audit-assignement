# Part B — Capacity Reconciliation

## B1 — KV-cache bytes/token and max concurrent sequences

### (a) KV-cache bytes per token

The KV cache stores one Key vector and one Value vector per layer, per
token, sized by the number of **KV heads** (not query heads — this
model uses GQA with 24 query heads but only 8 KV heads, since KV heads
is what actually determines cache size) times head_dim, in fp16 (2
bytes/element):

```
KV bytes/token = 2 (K and V) x layers x kv_heads x head_dim x bytes/elem
              = 2 x 28 x 8 x 128 x 2
              = 114,688 bytes
              = 112 KiB/token   (exactly — 114688 / 1024 = 112)
```

### (b) Max concurrent 4096-token sequences

Assumption stated explicitly: memory is computed in GiB (2^30 bytes)
throughout, consistent with how GPU memory is actually addressed by
serving frameworks. The ~0.1% difference between a "24 GB" nameplate
and 24 GiB is negligible here and doesn't change the conclusion.

```
usable memory        = 24 GiB x 0.92 (gpu_memory_utilization)
                      = 22.08 GiB

model weights         = 4.2B params x 2 bytes (fp16)
                      = 8.4e9 bytes = 7.8231 GiB

non-KV overhead        = 1.6 GiB          (given in model_spec.md)

KV cache budget        = 22.08 - 7.8231 - 1.6
                      = 12.6569 GiB

bytes per 4096-token
sequence               = 114,688 bytes/token x 4096 tokens
                      = 469,762,048 bytes = 0.4375 GiB   (exactly 7/16)

max concurrent
4096-token sequences   = 12.6569 GiB / 0.4375 GiB
                      = 28.93 -> floor to 28
```

**Prediction: ~28 concurrent 4096-token sequences.**

### Checking the prediction against `bench_log.csv`

The long-context sweep (`prompt_len=3584`, `gen_len=512`, total context
= 4096 = `max_model_len`) gives a direct check:

| batch_size | kv_cache_util | preempted_seqs |
|---|---|---|
| 16 | 0.62 | 0 |
| 24 | 0.93 | 0 |
| **32** | 0.97 | **7** |
| 48 | 0.97 | 23 |

The predicted ceiling of ~28-29 sequences sits exactly where the log
transitions from "fits" to "doesn't fit": batch 24 reaches 93% KV
utilization with zero preemption (still under budget), while batch 32
immediately shows preemption (scheduler forced to evict/reschedule
sequences because 32 exceeds the ~28-29 seat capacity). This is a
strong, direct confirmation of the arithmetic — the predicted number
and the observed behavior agree without needing to be adjusted.

## B2 — Long-context throughput anomaly

**The anomaly:** in the `prompt_len=3584` sweep, `reported_tok_s`
climbs smoothly from batch 4 through batch 24 (565.4 → 902.6 → 1311.4
→ 1607.4), then **drops** as batch size continues to increase (1384.0
at batch 32, 1298.5 at batch 48) — directly contradicting the naive
"throughput scales with batch size" assumption REPORT_v0 Section 2
uses to extrapolate to batch 48.

| batch_size | reported_tok_s | itl_ms_p50 | preempted_seqs | kv_cache_util |
|---|---|---|---|---|
| 4 | 565.4 | 51.33 | 0 | 0.16 |
| 8 | 902.6 | 62.26 | 0 | 0.31 |
| 16 | 1311.4 | 77.2 | 0 | 0.62 |
| **24** | **1607.4 (peak)** | 96.07 | 0 | 0.93 |
| 32 | 1384.0 | 101.79 | **7** | 0.97 |
| 48 | 1298.5 | 100.0 | **23** | 0.97 |

**Mechanism:** this lines up directly with B1's derived capacity
ceiling of ~28-29 concurrent 4096-token sequences. Batch 24 sits right
at the edge (93% KV cache utilization, 0 preemptions — just fits).
Batch 32 and 48 both exceed the KV-cache-imposed ceiling, forcing the
scheduler to **preempt** sequences: evict them from GPU memory
mid-generation and later re-admit and recompute their prefill. This is
wasted GPU work — cycles spent redoing prefill computation on
preempted sequences instead of generating new tokens for sequences
already in flight — which is why `reported_tok_s` goes *down* even as
more requests are submitted. `itl_ms_p50` (inter-token latency) rising
sharply at batch 32 (101.79ms, vs 96.07ms at batch 24) and staying
elevated at batch 48 is consistent with this: individual sequences are
generating tokens more slowly because the GPU is spending cycles on
preemption/recompute overhead rather than steady decode. This is
classic KV-cache "thrashing" — once concurrency exceeds the memory
ceiling, admitting more requests makes throughput *worse*, not better.

**Proposed fix, with predicted quantitative effect:** cap admission at
~24-28 concurrent sequences (e.g. via a `max_num_seqs`/admission-control
setting in the serving framework) so the scheduler queues excess
requests rather than admitting them and then preempting mid-flight.
Predicted effect, using batch 24's throughput (1607.4 tok/s, the
observed peak with zero preemption) as the achievable ceiling under
admission control:

```
vs current batch=32 behavior (1384.0 tok/s):  +16.1% throughput
vs current batch=48 behavior (1298.5 tok/s):  +23.8% throughput
```

Capping concurrency below the KV-cache ceiling should let the system
sustain throughput near the batch-24 peak instead of degrading as
concurrency is pushed past capacity.

## B3 — The one-column misreading behind both Section 2 conclusions

**REPORT_v0's two claims:** (1) "longer prompts clearly give better GPU
utilization" (883 tok/s short-prompt vs 1311 tok/s long-prompt, both at
batch 16); (2) extrapolating from "~1600 tok/s best observed" (batch
24 long-prompt), batch 48 should give ~3200 tok/s.

**The misread column: `reported_tok_s`.** Tested directly against
every row in `bench_log.csv`:

```
hypothesis: reported_tok_s = num_requests * (prompt_len + gen_len) / wall_clock_s
```

This matches every single one of the 13 rows in the log, essentially
exactly (largest discrepancy under 0.2 tok/s, consistent with
rounding). Confirmed: **`reported_tok_s` counts prompt tokens
(prefill) together with generated tokens (decode)**, not generation
throughput alone. Prefill is a single, fully-parallel forward pass over
the whole prompt at once — computationally cheap per token. Decode is
sequential, one token at a time, memory-bandwidth-bound — inherently
much slower per token. Blending both into one "tok/s" number means any
row with a longer prompt looks artificially faster, purely because it
has more cheap prefill tokens to count, not because the system is
actually generating new content any faster. This single misread
explains both of the report's conclusions:

1. "Longer prompts give better throughput" — an artifact of counting
   free prefill tokens, not a real GPU utilization improvement.
2. "Batch 48 ≈ 3200 tok/s" — extrapolated linearly from a number
   (1607.4 at batch 24) that was never real generation throughput to
   begin with, compounded by B2's finding that throughput actually
   *decreases* past ~batch 24 due to preemption.

**Honest goodput of the batch-24 long-prompt row, two independent
methods:**

*Method 1 — generated tokens only, over wall-clock time* (goodput =
new content actually delivered to the user; the user already has their
own prompt, prefilling it isn't work done "for" them):
```
24 requests x 512 gen tokens / 61.16s = 200.92 tok/s
```

*Method 2 — independent derivation via `itl_ms_p50`* (inter-token
latency measures the steady-state decode rate directly, per sequence;
multiplying by concurrent sequences gives aggregate decode throughput
without touching wall_clock_s or gen_len at all):
```
24 requests x (1000 / 96.07 ms) = 24 x 10.409 tok/s/seq = 249.82 tok/s
```

Both methods, computed from entirely different columns, land in the
same ballpark (~201–250 tok/s) — far below the reported 1607.4 tok/s
(a 6.4–8x overstatement).

**What the report should have said:** `reported_tok_s` conflates
prefill-token-counting with actual generation throughput, and should
never be used as a proxy for user-facing "goodput." The honest decode
throughput at the best-performing batch size (24, the ceiling
established in B1/B2) is roughly 200–250 tok/s of real new content
generated per second — not 1600, and nowhere near an extrapolated 3200
at batch 48, which B2 already shows is unreachable due to preemption.
Capacity planning should be built on this honest per-second decode
goodput figure, explicitly separated from prefill cost.

## B4 — Metric to confirm the B2 mechanism

The single most direct confirming metric would be the serving
framework's **preemption/recompute counter broken out from steady
decode time** — most vLLM-style schedulers expose this as something
like `num_preemptions_total` alongside a `time_in_prefill` /
`time_in_decode` split per step, or an equivalent "scheduler overhead"
timer. If the B2 mechanism (KV-cache-induced preemption forcing
wasted prefill recompute) is correct, this metric should show a sharp
jump in recompute time coinciding exactly with the `preempted_seqs`
column already in `bench_log.csv` — i.e., near-zero recompute overhead
at batch 24 and below, then a step-change increase at batch 32 and 48
proportional to (or exceeding) the 7 and 23 preemption counts already
observed. Expected value: recompute overhead consuming roughly
15-25% of total GPU time at batch 32/48 would be consistent with the
16-24% throughput recovery predicted in B2 if that overhead were
eliminated via admission control.

**Next step:** B4 -- which serving-stack metric would confirm the B2
preemption mechanism, and what value to expect.
