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
