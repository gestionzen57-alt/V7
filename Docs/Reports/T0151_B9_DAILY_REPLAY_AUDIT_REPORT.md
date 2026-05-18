# T0151 — B9 Daily Replay Audit Report V0

## Objectif

Produire un audit quotidien read-only des replays B9 : ce que B9 a bien vu, ce qui reste fragile, où le retest/source/timestamp/mémoire limite la lecture, et quels points doivent devenir fixtures ou corrections futures.

## Doctrine

B9 ne cherche pas le signal. B9 cherche la trace laissée par l’effort.

T0151 ne prédit rien, ne produit aucun ordre et ne calcule aucun taux de réussite.

## Entrées supportées

- `B9_REAL_REPLAY_DAY_RESULTS_V0.csv` issu de T0138.
- `B9_SESSION_REPLAY_SCORECARD_ROWS_V0.csv` issu de T0139.
- `T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv` si disponible.
- Un `t009_sequence_summary*.json` enrichi en fallback.

## Sorties

- `B9_DAILY_REPLAY_AUDIT_REPORT_V0.md`
- `B9_DAILY_REPLAY_AUDIT_REPORT_V0.json`
- `B9_DAILY_REPLAY_AUDIT_ROWS_V0.csv`
- `B9_DAILY_REPLAY_AUDIT_SESSION_COUNTS_V0.csv`
- `B9_DAILY_REPLAY_AUDIT_FRAGILITIES_V0.csv`
- `B9_DAILY_REPLAY_AUDIT_MEMORY_HELPED_V0.csv`
- `B9_DAILY_REPLAY_AUDIT_REPORT_V0.zip`

## États

- `B9_DAILY_REPLAY_AUDIT_PASS`
- `B9_DAILY_REPLAY_AUDIT_PARTIAL`
- `B9_DAILY_REPLAY_AUDIT_BLOCKED`
- `BLOCKED_NO_REPLAY_ROWS`
- `BLOCKED_FORBIDDEN_LANGUAGE`

## Limites

Read-only. Aucune DB. Aucun dashboard. Aucun Telegram. Aucun BUY/SELL. Aucune probabilité de succès.
