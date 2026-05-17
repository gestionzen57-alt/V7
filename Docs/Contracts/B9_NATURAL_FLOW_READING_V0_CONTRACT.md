# T0107 — B9 Natural Flow Reading V0

Status: `READY_FOR_INSTALL`  
Branch proposal: `feat/t0107-b9-natural-flow-reading-v0`  
Commit proposal: `feat(t0107): add B9 natural flow reading v0`

## Purpose

T0107 lets B9 evolve naturally toward true flow reading.

It adapts generic order-flow / auction-reading principles into PowerFlow B9:

```text
effort vs result
initiative vs response
rotation vs displacement
absorption-like friction
exhaustion-like stress
trap risk
market readability
```

This is not a DeltaRiver clone and does not copy any proprietary method.

It is an adaptation to the B9 raw microfilm model.

## New fields

```text
b9_directional_efficiency
b9_effort_load
b9_effort_result_ratio
b9_flow_intent_state
b9_absorption_like_state
b9_exhaustion_like_state
b9_initiative_response_state
b9_auction_state
b9_trap_risk_state
b9_market_readability_state
b9_natural_flow_reading_fr
```

## Flow intent states

```text
FLOW_DIRECTIONAL_DISPLACEMENT
FLOW_ROTATIONAL
FLOW_BALANCED_AUCTION
FLOW_WEAK_DIRECTIONAL
FLOW_GAPPY_LIMIT
FLOW_UNSTABLE_QUOTE_TEXTURE
FLOW_ARTIFACT
FLOW_MIXED
```

## Absorption-like states

```text
ABSORPTION_LIKE_ROTATIONAL_FRICTION
ABSORPTION_LIKE_EFFORT_WITHOUT_RESULT
ABSORPTION_LIKE_PARTIAL_FRICTION
ABSORPTION_UNREADABLE_ACTIVITY_LIMIT
ABSORPTION_NOT_ENOUGH_RANGE
ABSORPTION_NOT_DETECTED
```

## Exhaustion-like states

```text
EXHAUSTION_LIKE_SPREAD_STRESS
EXHAUSTION_LIKE_FAST_BUT_INEFFICIENT
EXHAUSTION_UNREADABLE_GAPPY_LIMIT
EXHAUSTION_NOT_ENOUGH_RANGE
EXHAUSTION_NOT_DETECTED
```

## Initiative / response states

```text
INITIATIVE_DISPLACEMENT
RESPONSIVE_BALANCING
RESPONSIVE_ROTATION
MIXED_INITIATIVE_RESPONSE
INIT_RESPONSE_NEUTRAL
INIT_RESPONSE_ARTIFACT
```

## Auction states

```text
AUCTION_DIRECTIONAL_ACCEPTANCE
AUCTION_ROTATIONAL_BALANCE
AUCTION_FRICTION_ABSORPTION_LIKE
AUCTION_EXHAUSTION_LIKE
AUCTION_READ_LIMIT_GAPPY
AUCTION_READ_LIMIT_SPREAD
AUCTION_ARTIFACT
AUCTION_MIXED
```

## Trap risk states

```text
TRAP_RISK_HIGH_PROGRESSIVE_ROTATIONAL
TRAP_RISK_HIGH_WEAK_RAW
TRAP_RISK_MEDIUM_EFFORT_WITHOUT_RESULT
TRAP_RISK_MEDIUM_TEXTURE_CAUTION
TRAP_RISK_DATA_TEXTURE_LIMIT
TRAP_RISK_ARTIFACT
TRAP_RISK_LOW
```

## Doctrine

B9 should evolve without being locked by the future external Temporalité brick.

B9 directly reads:

```text
time
density
spread
broker-relative volume visibility
effort vs result
auction texture
trap risk
```

This is interpretation only.

## Forbidden

```text
BUY/SELL
trading recommendation
global Forex volume claim
institutional absorption certainty
copying DeltaRiver proprietary logic
external Temporalité dependency
```

## Phrase de cap

```text
B9 ne cherche pas un signal.
B9 lit le comportement naturel du flux : effort, résultat, friction, rotation, déplacement, piège.
```
