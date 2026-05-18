# T0142 — B9 Terrain Node Builder V0

## Résumé exécutif

T0142 transforme les moments B9/T009 enrichis en nodes terrain.

Un node terrain est un point de cristallisation où une scène change de rôle : rejet haut, zone basse défendue, pullback absorbé, réintégration échouée, retest échoué, migration de mémoire, palier d’absorption.

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l’effort.  
Un node terrain nomme une cristallisation de scène, pas une décision d’exécution.

## Entrée

```text
samples/b9_terrain_node_builder_v0/sample_t009_sequence_summary_terrain_nodes.json
```

## Sorties

```text
outputs/b9_terrain_node_builder_v0/B9_TERRAIN_NODE_BUILDER_V0.md
outputs/b9_terrain_node_builder_v0/B9_TERRAIN_NODE_BUILDER_V0.json
outputs/b9_terrain_node_builder_v0/B9_TERRAIN_NODES_V0.csv
outputs/b9_terrain_node_builder_v0/B9_TERRAIN_NODE_COUNTS_V0.csv
outputs/b9_terrain_node_builder_v0/B9_TERRAIN_NODE_ENRICHED_SUMMARY_V0.json
outputs/b9_terrain_node_builder_v0/B9_TERRAIN_NODE_BUILDER_MANIFEST.json
outputs/b9_terrain_node_builder_v0/B9_TERRAIN_NODE_BUILDER_V0.zip
```

## Champs produits

```text
node_id
date
time_start
time_end
node_role
origin_zone_id
origin_zone_low
origin_zone_high
origin_zone_center
zone_status_before
zone_status_after
price_verdict
scene_role
retest_result
source_family
summary_recovery_type
source_mode
data_visibility
confidence_cap
proxy_vs_raw_verdict
source_quality_state
node_strength_state
node_memory_relevance
node_reading_fr
technical_limits
```

## Rôles de node couverts

```text
HIGH_REJECTION_NODE
LOWER_ZONE_DEFENDED_NODE
PULLBACK_ABSORBED_NODE
FAILED_REINTEGRATION_NODE
SECOND_LEG_TRIGGER_NODE
HIGH_EXHAUSTION_NODE
RETEST_FAILED_NODE
CENTER_MIGRATION_NODE
ABSORPTION_SHELF_NODE
PROGRESSIVE_REACTION_NODE
PROGRESSIVE_PRESSURE_NODE
ZONE_CONSUMED_NODE
ZONE_REJECTION_NODE
TERRAIN_NODE_REVIEW_REQUIRED
RAW_UNAVAILABLE_NODE_REJECTED
```

## Validation sample

```text
node_count = 6
missing_required_field_counts = {}
forbidden_language_hit_count = 0

role_counts:
ABSORPTION_SHELF_NODE = 1
RETEST_FAILED_NODE = 1
PROGRESSIVE_REACTION_NODE = 1
FAILED_REINTEGRATION_NODE = 1
LOWER_ZONE_DEFENDED_NODE = 1
RAW_UNAVAILABLE_NODE_REJECTED = 1
```

## Tests

```powershell
python -m py_compile pf_t009_terrain_node_builder.py tools\build_t0142_b9_terrain_node_builder.py
python -m pytest tests\test_t0142_b9_terrain_node_builder.py
```

Résultat attendu :

```text
2 passed
```

## Commande CLI

```powershell
python tools\build_t0142_b9_terrain_node_builder.py `
  --sequence-summary-json samples\b9_terrain_node_builder_v0\sample_t009_sequence_summary_terrain_nodes.json `
  --output-dir outputs\b9_terrain_node_builder_v0
```

## Limites

- Read-only.
- Aucune écriture `powerflow.db`.
- Aucune écriture `tick_archive.db`.
- Aucun dashboard.
- Aucun Telegram.
- Aucun ordre directionnel.
- Aucun taux de réussite.
- Une scène proxy reste proxy.
- Un node terrain n’est pas une prédiction.
- `RAW_UNAVAILABLE` est rejeté de la mémoire active.

## Prochain geste

T0143 — B9 Price Verdict Engine V0.
