# PowerFlow Force Kinematics Report

- DB: `powerflow.db`
- Symbol: `GBPUSD`
- Window: `2026-05-04T12:45:00+00:00` → `2026-05-04T13:45:00+00:00`
- Timeframes: `1,5,15,30,60`

> Angles are force-units/min geometric proxies: `atan(force_velocity_per_min)`.

## TF=1

```text
No rows in this window.
```

## TF=5

```text
No rows in this window.
```

## TF=15

```text
No rows in this window.
```

## TF=30

- Rows: `2`
- Coverage: `2026-05-04T13:00:00+00:00` → `2026-05-04T13:30:00+00:00`
- Segments: `1`

### Segments

| Window | Minutes | Bid | Pips | Fastest up | Fastest down | Energy | Tags |
|---|---:|---:|---:|---|---|---:|---|
| 13:00:00→13:30:00 | 30.0 | 1.35440→1.35455 | 1.50 | CAD:+0.16/m, USD:+0.07/m, CHF:-0.02/m | EUR:-0.11/m, GBP:-0.05/m, JPY:-0.05/m | 15.0 |  |

### Force angles by segment

| Window | GBP | USD | EUR | JPY | CAD | CHF | AUD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 13:00:00→13:30:00  | -3.0 | 3.9 | -6.4 | -2.6 | 9.0 | -1.2 | -2.3 |

## TF=60

- Rows: `1`
- Coverage: `2026-05-04T13:00:00+00:00` → `2026-05-04T13:00:00+00:00`
- Status: `INSUFFICIENT_ROWS_FOR_KINEMATICS`
