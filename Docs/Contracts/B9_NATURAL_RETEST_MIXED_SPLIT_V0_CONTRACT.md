# T0108 — B9 Natural Retest & FLOW_MIXED Split V0

Status: `READY_FOR_INSTALL`  
Branch proposal: `feat/t0108-b9-natural-retest-mixed-split-v0`  
Commit proposal: `feat(t0108): add B9 natural retest and mixed split v0`

## Purpose

T0108 stabilizes the next natural B9 reading step:

1. split `FLOW_MIXED`;
2. add a natural retest reading;
3. convert the combined context into a clearer B9 microfilm state.

This is direct B9 evolution, not B6 Lab, and not the external Temporalité brick.

## New fields

```text
b9_retest_mixed_split_version
b9_mixed_split_state
b9_retest_natural_state
b9_retest_quality_state
b9_context_resolution_state
b9_retest_mixed_reading_fr
```

## FLOW_MIXED split states

```text
MIXED_SPLIT_NOT_MIXED
MIXED_SPLIT_READ_LIMIT
MIXED_SPLIT_TRAP_RISK
MIXED_SPLIT_FRICTION
MIXED_SPLIT_STRESS
MIXED_SPLIT_BALANCED_AUCTION
MIXED_SPLIT_TRANSITION
MIXED_SPLIT_DIGESTION
MIXED_SPLIT_CONTEXT
MIXED_SPLIT_ARTIFACT
```

## Retest natural states

```text
RETEST_ACCEPTED
RETEST_ACCEPTED_WITH_FRICTION
RETEST_REJECTED_OR_FAILED
RETEST_PENDING_AFTER_DISPLACEMENT
RETEST_PENDING_TEXTURE
RETEST_PENDING_TRAP_RISK
RETEST_ABSORPTION_LIKE
RETEST_ROTATIONAL_BALANCE
RETEST_NOT_VISIBLE_DIRECTIONAL_FLOW
RETEST_NOT_VISIBLE
RETEST_UNREADABLE_TEXTURE
RETEST_ARTIFACT
```

## Context resolution

```text
CONTEXT_DIRECTIONAL_ACCEPTANCE
CONTEXT_ROTATIONAL_BALANCE
CONTEXT_RETEST_ACCEPTANCE
CONTEXT_RETEST_REJECTION
CONTEXT_TRAP_RISK
CONTEXT_READ_LIMIT
CONTEXT_DIGESTION
CONTEXT_TRANSITION
CONTEXT_MIXED
CONTEXT_ARTIFACT
```

## Doctrine

T0108 does not produce a signal.

It gives B9 a clearer language for:

```text
mixed flow
digestion
transition
retest accepted
retest rejected
retest absorbed-like
trap risk
read-limit
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
FLOW_MIXED ne doit pas rester un sac fourre-tout.
B9 doit dire si le mélange est digestion, transition, friction, piège ou limite de lecture.
```
