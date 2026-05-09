# PowerFlow DB Sequence Report — 06:00 → now

- DB: `powerflow.db`
- Symbol: `GBPUSD`
- DB global range: `2026-04-26T00:00:00+00:00` → `2026-05-04T15:00:00+00:00` (3324 rows for symbol)
- Analysis window: `2026-05-04T06:00:00+00:00` → `2026-05-04T15:00:00+00:00`
- Rows loaded in window: `278`

> Lecture: timestamps DB/broker. Si ton broker est H+1, convertir selon ton repère visuel.

## 1. Coverage by timeframe

- TF=1   rows=200  2026-05-04T08:03:00+00:00 → 2026-05-04T12:20:00+00:00 bid_delta=-0.00250
- TF=5   rows=40   2026-05-04T07:55:00+00:00 → 2026-05-04T11:10:00+00:00 bid_delta=-0.00251
- TF=15  rows=13   2026-05-04T08:00:00+00:00 → 2026-05-04T11:00:00+00:00 bid_delta=-0.00243
- TF=30  rows=16   2026-05-04T07:30:00+00:00 → 2026-05-04T15:00:00+00:00 bid_delta=-0.00279
- TF=60  rows=8    2026-05-04T07:00:00+00:00 → 2026-05-04T14:00:00+00:00 bid_delta=-0.00467
- TF=240 rows=1    2026-05-04T08:00:00+00:00 → 2026-05-04T08:00:00+00:00 bid_delta=NA

## 2. Force deltas by timeframe

### TF=1

| Devise | Start | End | Delta | Min | Max | Range | Std |
|---|---:|---:|---:|---:|---:|---:|---:|
| JPY | 60.63 | 84.99 | +24.36 | 20.68 | 84.99 | 64.31 | 15.02 |
| CAD | 35.14 | 52.02 | +16.88 | 19.81 | 91.61 | 71.80 | 18.93 |
| CHF | 49.95 | 63.66 | +13.71 | 19.01 | 68.18 | 49.17 | 12.38 |
| USD | 38.67 | 43.48 | +4.81 | 21.23 | 92.20 | 70.97 | 15.11 |
| AUD | 42.71 | 34.29 | -8.42 | 8.73 | 80.48 | 71.76 | 17.41 |
| EUR | 45.29 | 36.83 | -8.46 | 19.05 | 86.88 | 67.83 | 15.82 |
| GBP | 50.45 | 26.41 | -24.04 | 11.75 | 76.02 | 64.27 | 13.45 |

### TF=5

| Devise | Start | End | Delta | Min | Max | Range | Std |
|---|---:|---:|---:|---:|---:|---:|---:|
| JPY | 33.80 | 60.15 | +26.35 | 33.80 | 63.11 | 29.31 | 8.74 |
| AUD | 35.61 | 49.02 | +13.41 | 25.81 | 61.12 | 35.30 | 10.16 |
| USD | 69.41 | 72.56 | +3.15 | 48.37 | 75.06 | 26.69 | 8.83 |
| EUR | 37.30 | 25.22 | -12.07 | 25.22 | 76.91 | 51.69 | 15.12 |
| CAD | 72.18 | 53.67 | -18.50 | 44.23 | 72.18 | 27.94 | 6.77 |
| GBP | 46.77 | 23.96 | -22.81 | 22.67 | 74.00 | 51.32 | 18.08 |
| CHF | 46.02 | 12.30 | -33.72 | 12.30 | 65.90 | 53.59 | 17.67 |

### TF=15

| Devise | Start | End | Delta | Min | Max | Range | Std |
|---|---:|---:|---:|---:|---:|---:|---:|
| USD | 33.97 | 66.74 | +32.77 | 33.97 | 66.74 | 32.77 | 11.53 |
| CAD | 33.76 | 54.70 | +20.94 | 33.76 | 54.70 | 20.94 | 6.81 |
| EUR | 49.24 | 62.40 | +13.17 | 47.98 | 67.48 | 19.50 | 7.67 |
| GBP | 51.70 | 40.33 | -11.37 | 40.33 | 62.76 | 22.43 | 6.18 |
| JPY | 68.20 | 54.45 | -13.75 | 51.08 | 68.72 | 17.64 | 6.66 |
| AUD | 31.24 | 17.37 | -13.86 | 17.37 | 31.24 | 13.86 | 4.75 |
| CHF | 42.09 | 26.80 | -15.29 | 26.80 | 46.36 | 19.56 | 5.50 |

### TF=30

| Devise | Start | End | Delta | Min | Max | Range | Std |
|---|---:|---:|---:|---:|---:|---:|---:|
| CAD | 49.49 | 64.67 | +15.18 | 43.23 | 66.48 | 23.25 | 8.12 |
| USD | 59.69 | 72.11 | +12.42 | 49.02 | 72.52 | 23.50 | 8.16 |
| EUR | 40.22 | 44.09 | +3.87 | 40.22 | 61.28 | 21.06 | 6.39 |
| JPY | 55.25 | 48.72 | -6.53 | 48.72 | 57.83 | 9.11 | 2.68 |
| AUD | 37.59 | 27.33 | -10.26 | 23.84 | 37.59 | 13.75 | 3.88 |
| GBP | 50.76 | 40.40 | -10.36 | 35.00 | 58.85 | 23.85 | 8.78 |
| CHF | 40.06 | 19.77 | -20.28 | 17.74 | 40.06 | 22.31 | 8.52 |

### TF=60

| Devise | Start | End | Delta | Min | Max | Range | Std |
|---|---:|---:|---:|---:|---:|---:|---:|
| USD | 67.59 | 76.44 | +8.85 | 67.59 | 76.44 | 8.85 | 3.23 |
| JPY | 35.85 | 41.33 | +5.48 | 35.85 | 42.37 | 6.52 | 1.98 |
| CAD | 51.19 | 55.94 | +4.75 | 44.86 | 55.94 | 11.08 | 3.67 |
| GBP | 28.57 | 32.81 | +4.24 | 28.57 | 40.48 | 11.91 | 3.75 |
| EUR | 55.93 | 57.43 | +1.50 | 53.95 | 60.83 | 6.88 | 2.46 |
| CHF | 46.92 | 20.83 | -26.08 | 20.83 | 46.92 | 26.08 | 8.62 |
| AUD | 72.86 | 36.52 | -36.33 | 36.52 | 72.86 | 36.33 | 11.24 |

### TF=240

| Devise | Start | End | Delta | Min | Max | Range | Std |
|---|---:|---:|---:|---:|---:|---:|---:|
| GBP | 42.31 | 42.31 | +0.00 | 42.31 | 42.31 | 0.00 | 0.00 |
| USD | 33.65 | 33.65 | +0.00 | 33.65 | 33.65 | 0.00 | 0.00 |
| EUR | 36.54 | 36.54 | +0.00 | 36.54 | 36.54 | 0.00 | 0.00 |
| JPY | 73.76 | 73.76 | +0.00 | 73.76 | 73.76 | 0.00 | 0.00 |
| CAD | 39.26 | 39.26 | +0.00 | 39.26 | 39.26 | 0.00 | 0.00 |
| CHF | 72.78 | 72.78 | +0.00 | 72.78 | 72.78 | 0.00 | 0.00 |
| AUD | 54.71 | 54.71 | +0.00 | 54.71 | 54.71 | 0.00 | 0.00 |

## 3. Timeline snapshots

- `2026-05-04T08:03:00+00:00` TF=1 bid=1.35865 | TOP: JPY:60.6, GBP:50.5, CHF:49.9 | LOW: CAD:35.1, USD:38.7, AUD:42.7 | HIGH_BLOCK_JPY | LOW_BLOCK_CAD+USD
- `2026-05-04T08:03:00+00:00` TF=1 bid=1.35865 | TOP: JPY:60.6, GBP:50.5, CHF:49.9 | LOW: CAD:35.1, USD:38.7, AUD:42.7 | HIGH_BLOCK_JPY | LOW_BLOCK_CAD+USD
- `2026-05-04T08:03:00+00:00` TF=1 bid=1.35865 | TOP: JPY:60.6, GBP:50.5, CHF:49.9 | LOW: CAD:35.1, USD:38.7, AUD:42.7 | HIGH_BLOCK_JPY | LOW_BLOCK_CAD+USD
- `2026-05-04T08:03:00+00:00` TF=1 bid=1.35865 | TOP: JPY:60.6, GBP:50.5, CHF:49.9 | LOW: CAD:35.1, USD:38.7, AUD:42.7 | HIGH_BLOCK_JPY | LOW_BLOCK_CAD+USD
- `2026-05-04T08:03:00+00:00` TF=1 bid=1.35865 | TOP: JPY:60.6, GBP:50.5, CHF:49.9 | LOW: CAD:35.1, USD:38.7, AUD:42.7 | HIGH_BLOCK_JPY | LOW_BLOCK_CAD+USD
- `2026-05-04T08:30:00+00:00` TF=1 bid=1.35872 | TOP: USD:60.4, JPY:57.4, CAD:54.2 | LOW: AUD:22.5, CHF:39.9, EUR:42.2 | HIGH_BLOCK_USD | LOW_BLOCK_AUD+CHF | AUD_LOW_PRESSURE | RISING_USD+CAD | FALLING_AUD+CHF
- `2026-05-04T09:00:00+00:00` TF=1 bid=1.35913 | TOP: AUD:80.2, JPY:66.9, CHF:53.5 | LOW: CAD:23.4, USD:28.7, GBP:44.3 | HIGH_BLOCK_AUD+JPY | LOW_BLOCK_CAD+USD | JPY_REFUGE_HIGH | RISING_AUD+CHF+JPY | FALLING_USD+CAD+GBP
- `2026-05-04T09:30:00+00:00` TF=1 bid=1.35971 | TOP: CAD:66.0, JPY:60.8, USD:50.9 | LOW: EUR:36.9, CHF:37.2, GBP:40.2 | HIGH_BLOCK_CAD+JPY | LOW_BLOCK_EUR+CHF | CAD_GRAVITY_HIGH | RISING_CAD+USD | FALLING_AUD+CHF+EUR
- `2026-05-04T10:00:00+00:00` TF=1 bid=1.35801 | TOP: AUD:60.1, EUR:53.6, CHF:49.3 | LOW: GBP:43.1, USD:43.5, JPY:47.0 | HIGH_BLOCK_AUD | RISING_AUD+EUR+CHF | FALLING_CAD+JPY
- `2026-05-04T10:30:00+00:00` TF=1 bid=1.35712 | TOP: JPY:76.6, USD:55.7, AUD:50.0 | LOW: CHF:19.0, CAD:23.0, EUR:27.7 | HIGH_BLOCK_JPY | LOW_BLOCK_CHF+CAD+EUR | JPY_REFUGE_HIGH | CHF_LOW_PRESSURE | RISING_JPY+USD | FALLING_CHF+EUR+CAD
- `2026-05-04T11:00:00+00:00` TF=1 bid=1.35649 | TOP: GBP:69.1, CHF:61.7, AUD:59.4 | LOW: USD:38.3, JPY:39.6, EUR:44.9 | HIGH_BLOCK_GBP+CHF | LOW_BLOCK_USD+JPY | RISING_CHF+CAD+GBP | FALLING_JPY+USD
- `2026-05-04T11:21:00+00:00` TF=1 bid=1.35601 | TOP: EUR:75.4, CHF:66.4, CAD:65.1 | LOW: JPY:20.7, USD:42.2, GBP:46.5 | HIGH_BLOCK_EUR+CHF+CAD | LOW_BLOCK_JPY | CAD_GRAVITY_HIGH | EUR_HIGH_PRESSURE | RISING_EUR+CAD | FALLING_GBP+JPY
- `2026-05-04T12:20:00+00:00` TF=1 bid=1.35615 | TOP: JPY:85.0, CHF:63.7, CAD:52.0 | LOW: GBP:26.4, AUD:34.3, EUR:36.8 | HIGH_BLOCK_JPY+CHF | LOW_BLOCK_GBP+AUD+EUR | JPY_REFUGE_HIGH | GBP_LOW_PRESSURE | RISING_JPY | FALLING_EUR+AUD+GBP
- `2026-05-04T12:20:00+00:00` TF=1 bid=1.35615 | TOP: JPY:85.0, CHF:63.7, CAD:52.0 | LOW: GBP:26.4, AUD:34.3, EUR:36.8 | HIGH_BLOCK_JPY+CHF | LOW_BLOCK_GBP+AUD+EUR | JPY_REFUGE_HIGH | GBP_LOW_PRESSURE
- `2026-05-04T12:20:00+00:00` TF=1 bid=1.35615 | TOP: JPY:85.0, CHF:63.7, CAD:52.0 | LOW: GBP:26.4, AUD:34.3, EUR:36.8 | HIGH_BLOCK_JPY+CHF | LOW_BLOCK_GBP+AUD+EUR | JPY_REFUGE_HIGH | GBP_LOW_PRESSURE
- `2026-05-04T12:20:00+00:00` TF=1 bid=1.35615 | TOP: JPY:85.0, CHF:63.7, CAD:52.0 | LOW: GBP:26.4, AUD:34.3, EUR:36.8 | HIGH_BLOCK_JPY+CHF | LOW_BLOCK_GBP+AUD+EUR | JPY_REFUGE_HIGH | GBP_LOW_PRESSURE
- `2026-05-04T12:20:00+00:00` TF=1 bid=1.35615 | TOP: JPY:85.0, CHF:63.7, CAD:52.0 | LOW: GBP:26.4, AUD:34.3, EUR:36.8 | HIGH_BLOCK_JPY+CHF | LOW_BLOCK_GBP+AUD+EUR | JPY_REFUGE_HIGH | GBP_LOW_PRESSURE
- `2026-05-04T12:20:00+00:00` TF=1 bid=1.35615 | TOP: JPY:85.0, CHF:63.7, CAD:52.0 | LOW: GBP:26.4, AUD:34.3, EUR:36.8 | HIGH_BLOCK_JPY+CHF | LOW_BLOCK_GBP+AUD+EUR | JPY_REFUGE_HIGH | GBP_LOW_PRESSURE
- `2026-05-04T12:20:00+00:00` TF=1 bid=1.35615 | TOP: JPY:85.0, CHF:63.7, CAD:52.0 | LOW: GBP:26.4, AUD:34.3, EUR:36.8 | HIGH_BLOCK_JPY+CHF | LOW_BLOCK_GBP+AUD+EUR | JPY_REFUGE_HIGH | GBP_LOW_PRESSURE

## 4. Strongest rotation windows

### TF=1 strongest ~5m moves
- `2026-05-04T09:50:00+00:00` → `2026-05-04T09:53:00+00:00` energy=124.3 | UP: EUR+22.6, CHF+17.2, AUD+16.8 | DOWN: CAD-24.7, USD-24.4, JPY+2.7 | bid 1.35815 → 1.35834
- `2026-05-04T09:24:00+00:00` → `2026-05-04T09:27:00+00:00` energy=119.9 | UP: CAD+18.5, JPY+17.7, USD+10.4 | DOWN: EUR-23.2, GBP-20.1, CHF-17.1 | bid 1.35962 → 1.35955
- `2026-05-04T09:51:00+00:00` → `2026-05-04T09:54:00+00:00` energy=114.9 | UP: AUD+24.8, CHF+14.9, GBP+14.5 | DOWN: USD-22.9, CAD-22.2, JPY+2.1 | bid 1.35809 → 1.35814
- `2026-05-04T09:49:00+00:00` → `2026-05-04T09:52:00+00:00` energy=110.8 | UP: EUR+26.8, CHF+17.5, GBP+10.8 | DOWN: CAD-23.7, USD-20.5, JPY+3.5 | bid 1.35793 → 1.35837
- `2026-05-04T09:23:00+00:00` → `2026-05-04T09:26:00+00:00` energy=96.8 | UP: CAD+16.1, JPY+15.8, USD+10.4 | DOWN: EUR-21.3, GBP-19.1, AUD-11.0 | bid 1.35962 → 1.35948

### TF=5 strongest ~15m moves
- `2026-05-04T07:55:00+00:00` → `2026-05-04T08:05:00+00:00` energy=67.5 | UP: EUR+15.8, JPY+11.5, AUD+10.2 | DOWN: CAD-13.5, USD-12.0, CHF+1.3 | bid 1.35879 → 1.35874
- `2026-05-04T09:35:00+00:00` → `2026-05-04T09:45:00+00:00` energy=58.3 | UP: USD+10.2, CAD+7.8, JPY+2.1 | DOWN: AUD-15.0, GBP-14.0, CHF-6.5 | bid 1.35885 → 1.35793
- `2026-05-04T09:40:00+00:00` → `2026-05-04T09:50:00+00:00` energy=51.2 | UP: USD+8.4, CAD+6.6, JPY+3.3 | DOWN: GBP-13.6, AUD-12.1, CHF-5.3 | bid 1.35838 → 1.35814
- `2026-05-04T09:30:00+00:00` → `2026-05-04T09:40:00+00:00` energy=45.8 | UP: USD+7.8, CAD+5.0, JPY+1.4 | DOWN: GBP-12.5, AUD-12.2, CHF-6.3 | bid 1.35924 → 1.35838
- `2026-05-04T09:55:00+00:00` → `2026-05-04T10:05:00+00:00` energy=36.2 | UP: CAD+5.9, USD+4.6, JPY+0.7 | DOWN: CHF-9.4, GBP-7.2, AUD-4.4 | bid 1.35806 → 1.35739

### TF=15 strongest ~15m moves
- `2026-05-04T09:30:00+00:00` → `2026-05-04T09:45:00+00:00` energy=23.5 | UP: USD+5.0, EUR+4.6, CAD+4.0 | DOWN: AUD-5.3, JPY-2.2, GBP-1.5 | bid 1.35838 → 1.35806
- `2026-05-04T10:30:00+00:00` → `2026-05-04T10:45:00+00:00` energy=22.1 | UP: USD+3.9, JPY+1.7, CAD+1.0 | DOWN: CHF-7.0, GBP-4.7, AUD-2.1 | bid 1.35669 → 1.35665
- `2026-05-04T10:00:00+00:00` → `2026-05-04T10:15:00+00:00` energy=20.9 | UP: USD+5.7, CAD+5.2, EUR+1.2 | DOWN: GBP-4.2, JPY-2.0, CHF-1.4 | bid 1.35759 → 1.35690
- `2026-05-04T10:45:00+00:00` → `2026-05-04T11:00:00+00:00` energy=19.8 | UP: USD+2.8, CAD+1.7, JPY+1.5 | DOWN: CHF-4.9, GBP-4.5, EUR-3.4 | bid 1.35665 → 1.35628
- `2026-05-04T09:45:00+00:00` → `2026-05-04T10:00:00+00:00` energy=19.6 | UP: USD+7.2, EUR+2.7, CAD+1.7 | DOWN: AUD-3.2, GBP-2.5, JPY-2.0 | bid 1.35806 → 1.35759

### TF=30 strongest ~30m moves
- `2026-05-04T07:30:00+00:00` → `2026-05-04T08:00:00+00:00` energy=33.1 | UP: EUR+11.3, GBP+3.6, JPY+1.2 | DOWN: USD-8.3, CAD-4.5, CHF-2.2 | bid 1.35879 → 1.35869
- `2026-05-04T10:30:00+00:00` → `2026-05-04T11:00:00+00:00` energy=29.4 | UP: USD+5.2, CAD+3.3, JPY+1.0 | DOWN: CHF-9.4, GBP-7.0, AUD-3.1 | bid 1.35665 → 1.35615
- `2026-05-04T10:00:00+00:00` → `2026-05-04T10:30:00+00:00` energy=16.3 | UP: USD+3.9, EUR+2.2, CAD+1.1 | DOWN: CHF-3.7, AUD-2.8, GBP-2.5 | bid 1.35690 → 1.35665
- `2026-05-04T13:00:00+00:00` → `2026-05-04T13:30:00+00:00` energy=15.0 | UP: CAD+4.7, USD+2.1, CHF-0.6 | DOWN: EUR-3.4, GBP-1.6, JPY-1.4 | bid 1.35440 → 1.35455
- `2026-05-04T12:30:00+00:00` → `2026-05-04T13:00:00+00:00` energy=14.0 | UP: CAD+3.5, USD+2.5, JPY-0.4 | DOWN: EUR-3.3, GBP-2.0, AUD-1.3 | bid 1.35591 → 1.35440

### TF=60 strongest ~60m moves
- `2026-05-04T07:00:00+00:00` → `2026-05-04T08:00:00+00:00` energy=45.6 | UP: GBP+9.1, JPY+5.1, USD+0.0 | DOWN: AUD-16.5, CHF-7.5, CAD-5.3 | bid 1.35879 → 1.35924
- `2026-05-04T10:00:00+00:00` → `2026-05-04T11:00:00+00:00` energy=24.8 | UP: EUR+2.8, USD+2.6, CAD+2.2 | DOWN: CHF-7.9, AUD-7.0, GBP-1.7 | bid 1.35665 → 1.35609
- `2026-05-04T12:00:00+00:00` → `2026-05-04T13:00:00+00:00` energy=13.7 | UP: CAD+3.9, USD+1.8, EUR-0.5 | DOWN: CHF-2.6, GBP-2.4, AUD-2.1 | bid 1.35591 → 1.35455
- `2026-05-04T13:00:00+00:00` → `2026-05-04T14:00:00+00:00` energy=13.6 | UP: CAD+2.7, USD+2.0, JPY-0.3 | DOWN: EUR-2.9, AUD-2.4, CHF-2.0 | bid 1.35455 → 1.35412
- `2026-05-04T09:00:00+00:00` → `2026-05-04T10:00:00+00:00` energy=11.2 | UP: EUR+2.4, USD+1.1, CAD+1.0 | DOWN: AUD-4.1, CHF-1.4, JPY+0.3 | bid 1.35806 → 1.35665

## 5. PowerFlow reading

### What PowerFlow can see with the current DB schema

- Forces by currency: YES
- Bid movement: YES
- Multi-timeframe force alignment: YES
- Coalition blocks high/low: YES
- Leader/follower deltas: YES, approximated from force changes
- OHLC candle respiration: NO, not persisted in this DB
- tick_volume activity: NO, not persisted in this DB
- pips/body/range/spread friction: NO, not persisted in this DB
- NZD: NO, not persisted in this DB

### Suggested Flow classification

Use the strongest rotation windows above to name the sequence. Typical labels:

```text
HIGH_BLOCK_EXTENSION
RISK_BLOCK_FOLDING
USD_GRAVITY_RETAKE
CAD_RESPRING_FROM_LOW
JPY_REFUGE_RESPONSE
LATE_CHF_RESPONSE
CENTER_REBALANCE_FIELD
```

## 6. Next tactical step

If one window is confirmed visually, rerun a narrower scan around it, for example:

```powershell
python analyze_powerflow_from_0600_today.py --start 2026-05-04T09:00:00+00:00 --end 2026-05-04T09:45:00+00:00 --out sequence_0900_0945.md
```
