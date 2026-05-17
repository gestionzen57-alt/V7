# T0112 — B9 Proxy/Raw Agreement & Source Quality Score

## Status

`READY`

## Problem

After T0103C, provenance is visible in aggregate outputs. The next missing layer is a source-aware score that says whether a proxy scene is:

- confirmed by raw;
- nuanced by raw;
- raw unavailable;
- source-limited by timeframe fallback;
- usable as a B6 memory candidate.

## Added fields

```text
t0112_proxy_raw_version
proxy_raw_agreement_state
proxy_raw_agreement_score
source_quality_score
source_quality_state
raw_unavailable_penalty
source_timeframe_penalty
b6_memory_candidate_score
b6_memory_candidate_state
t0112_reason_flags
```

## Rules

- `RAW_UNAVAILABLE` is penalized and cannot be a B6 keep candidate.
- `M1_BAR_PROXY` is stronger than TF fallback, but still capped.
- `TF5_BAR_PROXY` / `TF30_BAR_PROXY` are useful but get source timeframe penalty.
- `FORCE_SNAPSHOT_DERIVED` remains proxy-derived and must not be presented as recovered history.
- No decision language.

## Constraints

- no `powerflow.db` write;
- no `tick_archive.db` write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no global FX volume claim.

## Phrase de cap

Raw MT5 donne la texture.  
Le proxy donne une scène reconstruite.  
T0112 mesure l'accord entre les deux sans transformer B9 en système de signal.
