# T0107A — B9 Natural Flow Gappy Threshold Hotfix

Status: `READY_FOR_INSTALL`  
Branch proposal: `fix/t0107-b9-natural-flow-gappy-threshold`  
Commit proposal: `fix(t0107): soften gappy threshold in natural flow reading`

## Problem

T0107 installed, but two tests failed:

```text
test_directional_flow_can_be_detected
test_rotation_is_not_forced_into_directional_truth
```

Both failures returned:

```text
FLOW_GAPPY_LIMIT
```

## Cause

T0105 marks `RAW_ACTIVITY_GAPPY` when `raw_gap_max_ms >= 10000`.

That is useful as a texture flag, but too strict as a hard flow intent override.

In the unit tests, a normal synthetic 60-second microfilm contains a 20-second gap. T0107 treated this as a hard unreadable state and blocked directional/rotational reading.

## Fix

T0107A keeps `RAW_ACTIVITY_GAPPY` visible but only turns it into `FLOW_GAPPY_LIMIT` when it is materially harmful:

```text
raw_gap_max_ms >= 60000
or raw_tick_density_per_minute <= 3
or raw_tick_count_dedup <= 3
or long microfilm + substantial gap
```

Moderate gappiness remains visible through:

```text
TRAP_RISK_MEDIUM_TEXTURE_CAUTION
b9_factor_flags
raw_activity_profile
```

but it no longer erases effort/result reading.

## Constraints

- read-only DB;
- no `powerflow.db` write;
- no `tick_archive.db` write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no external Temporalité dependency;
- no global Forex volume claim.

## Phrase de cap

```text
Un gap raw est une limite de texture.
Il ne doit pas effacer automatiquement la lecture effort/résultat.
```
