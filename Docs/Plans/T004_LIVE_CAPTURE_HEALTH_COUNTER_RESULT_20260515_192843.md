# T004-G Live Capture Health Counter

Date: 2026-05-15T17:28:43Z

## Result

- DB: Core/powerflow.db
- Duration seconds: 30
- Status: NO_LIVE_DELTA_CAPTURE_INACTIVE_OR_IDLE

## Symbol deltas

- USDJPY: 0
- GBPUSD: 0
- EURUSD: 0

## Recommendations

- No symbol row deltas during the window. Capture may be stopped, market/feed idle, or DB writes are not active.
- Do not change engine/scoring logic based on this check alone; this is capture health evidence.

## Table deltas

### context_htf

- USDJPY: 0
- GBPUSD: 0
- EURUSD: 0

### flow_packets

- USDJPY: 0
- GBPUSD: 0
- EURUSD: 0

### force_snapshots

- USDJPY: 0
- GBPUSD: 0
- EURUSD: 0

### force_snapshots_v2

- USDJPY: 0
- GBPUSD: 0
- EURUSD: 0

### nodes_v6

- USDJPY: 0
- GBPUSD: 0
- EURUSD: 0

### signals

- USDJPY: 0
- GBPUSD: 0
- EURUSD: 0

### sqlite_sequence

- USDJPY: 0
- GBPUSD: 0
- EURUSD: 0

### zone_diagnostics

- USDJPY: 0
- GBPUSD: 0
- EURUSD: 0


## Runtime behavior

- DB opened read-only twice.
- No runtime wiring.
- No dashboard files touched.
- This script only compares before/after counts.

## Next action

If references move and USDJPY does not, fix source/routing/allowlist before engine changes.
If no symbols move, rerun while capture/market feed is active.

