# T0127 — B9 Timestamp Remap Guard V0

## Résumé

T0127 protège B9 contre le bug critique des timestamps shifted/replay.

Il distingue :

```text
time_start_raw / time_end_raw
time_start_real / time_end_real
timestamp_source
timestamp_policy
is_replay_shifted
replay_shift_minutes
```

## États

```text
TIMESTAMP_POLICY_OK
TIMESTAMP_SHIFT_DETECTED
TIMESTAMP_REMAP_REQUIRED
TIMESTAMP_REAL_UNKNOWN
```

## Doctrine

B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Une scène bien lue mais mal horodatée reste techniquement fragile.

## Contraintes

Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.

## Validation sample

```text
moments_checked = 3
timestamp_guard_state = PASS_WITH_SHIFT_DETECTED
TIMESTAMP_SHIFT_DETECTED = 3
missing_required_field_counts = {}
forbidden_language_hits = []
```

## Prochain bloc

T0128 — Native Retest Source Fields / T0111B.
