# T0141 — B9 Zone Memory Object Builder V0

## Résumé

T0141 transforme les moments B9/T009 en objets mémoire de zone.

Une zone mémoire n'est pas une ligne de trading. C'est une trace comportementale que B9 peut réutiliser pour comparer des scènes.

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Une zone mémoire est une trace comportementale, pas une décision d'exécution.
```

## Champs produits

```text
zone_id
date
first_seen
last_tested
zone_low
zone_high
zone_center
zone_width_pips
test_count
accepted_count
rejected_count
defended_count
consumed_count
pending_count
fresh
consumed
zone_memory_state
dominant_scene_role
source_family
summary_recovery_type
source_mode
data_visibility
confidence_cap
proxy_vs_raw_verdict
source_quality_state
zone_memory_reading_fr
technical_limits
```

## États produits

```text
ZONE_MEMORY_ACCEPTED
ZONE_MEMORY_REJECTED
ZONE_MEMORY_DEFENDED
ZONE_MEMORY_CONSUMED
ZONE_MEMORY_PENDING
ZONE_MEMORY_REVIEW_REQUIRED
```

## Règles analytiques

- `RAW_UNAVAILABLE` est exclu des objets mémoire actifs.
- Une zone proxy ne devient jamais une vérité raw.
- `NUANCED_BY_RAW` reste nuancé.
- Une zone mémoire ne donne aucun ordre.
- Une zone consommée reste une trace historique, pas une zone active dure.

## Commande CLI

```powershell
python tools\build_t0141_b9_zone_memory_object_builder.py --sequence-summary-json samples\b9_zone_memory_object_builder_v0\sample_t009_sequence_summary_zone_memory.json --output-dir outputs\b9_zone_memory_object_builder_v0
```

## Tests

```powershell
python -m py_compile pf_t009_zone_memory_object_builder.py tools\build_t0141_b9_zone_memory_object_builder.py
python -m pytest tests\test_t0141_b9_zone_memory_object_builder.py
```

## Limites

Read-only. Aucune écriture `powerflow.db`. Aucune écriture `tick_archive.db`. Aucun dashboard. Aucun Telegram. Aucun ordre directionnel. Aucune statistique de réussite.
