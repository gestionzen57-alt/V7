# T0169 — B9 Dashboard Surfaces Recovery

## Mission

Rendre les surfaces dashboard B9 disponibles sans activer le cockpit live.

## Fichier vérifié / livré

```text
tools/build_t0169_b9_reality_board_surface_adapter_candidate.py
```

## Outputs régénérés

```text
outputs/b9_reality_board_read_model_v01/B9_REALITY_BOARD_READ_MODEL_V01.json
outputs/b9_reality_board_scene_panel_candidate_v01/B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V01.json
outputs/b9_reality_board_surface_adapter_candidate_v0/B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json
```

## Doctrine

```text
Le dashboard affiche.
B9 qualifie.
Le trader décide.
Comparer n'est pas prédire.
Une surface partielle doit dire qu'elle est partielle.
```

## Fonction

Le builder cherche récursivement les outputs B9 disponibles, notamment :

```text
B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json
B9_MARKET_COMPARE_BOARD_V0.json
T0167_B9_B6_REALIGNMENT outputs
B9_TRADER_ATTENTION_PACKET_V0.json
B9_LIVE_BRIEF_ONCE_V0.json
B9_HUMAN_TERRAIN_SYNTHESIS_V0.json
B9_MEMORY_CONFIDENCE_LADDER outputs
B9_FALSE_POSITIVE_MEMORY_EXPLAINER outputs
```

Si une entrée manque, le builder n'invente pas. Il écrit `missing_inputs`, `technical_limits` et `display_readiness=PARTIAL`.

## Contraintes

- Ne modifie pas le cockpit live.
- Ne touche aucune DB.
- Aucun Telegram.
- Aucune décision automatique.
- Aucun conseil de trading.
- Le dashboard affiche, il ne décide pas.
