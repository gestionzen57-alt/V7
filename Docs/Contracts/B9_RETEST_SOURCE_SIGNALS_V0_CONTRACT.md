# T0109 — B9 Retest Source Signals V0

Status: `READY_FOR_INSTALL`  
Branch proposal: `feat/t0109-b9-retest-source-signals-v0`  
Commit proposal: `feat(t0109): add B9 retest source signals v0`

## Purpose

T0109 gives T0108 better retest material.

T0108 can classify retest states, but if the original B9 summary does not expose retest source details, many scenes remain `RETEST_NOT_VISIBLE`.

T0109 adds source-derived retest fields.

## Added fields

```text
b9_retest_source_status
b9_retest_touch_count_proxy
b9_retest_delay_proxy_seconds
b9_retest_source_visibility
b9_retest_source_evidence_score
b9_retest_source_signal_state
b9_retest_source_readiness
b9_retest_source_reading_fr
```

## Source status

```text
RETEST_SOURCE_ACCEPTED_EXPLICIT
RETEST_SOURCE_REJECTED_EXPLICIT
RETEST_SOURCE_PENDING_EXPLICIT
RETEST_SOURCE_ACCEPTED_INFERRED
RETEST_SOURCE_REJECTED_INFERRED
RETEST_SOURCE_FRICTION_INFERRED
RETEST_SOURCE_PENDING_INFERRED
RETEST_SOURCE_NOT_VISIBLE
```

## Visibility

```text
RETEST_VISIBILITY_HIGH
RETEST_VISIBILITY_MEDIUM
RETEST_VISIBILITY_LOW_RAW_ONLY
RETEST_VISIBILITY_UNKNOWN
```

## Signal state

This is not a trading signal. It is a scene-evidence signal.

```text
RETEST_SIGNAL_ACCEPTANCE_EVIDENCE
RETEST_SIGNAL_REJECTION_EVIDENCE
RETEST_SIGNAL_PENDING_EVIDENCE
RETEST_SIGNAL_FRICTION_EVIDENCE
RETEST_SIGNAL_ROTATIONAL_CONTEXT
RETEST_SIGNAL_TRAP_RISK_CONTEXT
RETEST_SIGNAL_NOT_VISIBLE
```

## Readiness

```text
RETEST_CONTEXT_STRONG
RETEST_CONTEXT_USABLE
RETEST_CONTEXT_WEAK
RETEST_CONTEXT_NOT_VISIBLE
RETEST_CONTEXT_LIMITED_BY_TEXTURE
```

## Doctrine

T0109 does not predict.

It tells B9 how visible the retest evidence is from:

```text
explicit retest_status
zone_memory
touch count
last_tested / last_seen
raw texture
T0108 natural retest state
```

## Constraints

- read-only DB;
- no `powerflow.db` write;
- no `tick_archive.db` write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no B8 fusion;
- no external Temporalité dependency;
- no global Forex volume claim.

## Phrase de cap

```text
B9 ne doit pas deviner le retest si les champs source sont muets.
T0109 rend visible la qualité de preuve du retest.
```
