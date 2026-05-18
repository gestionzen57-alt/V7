# T0169 — B9 Reality Board Surface Adapter Candidate V0

## Objectif

Transformer les artefacts Reality Board / panel candidat / payload T0156 en surface adapter JSON/MD stable.

Le module ne modifie aucun cockpit. Il prépare une surface lisible par un futur dashboard.

## Entrées

- `outputs/b9_reality_board_read_model_v01/B9_REALITY_BOARD_READ_MODEL_V01.json`
- `outputs/b9_reality_board_scene_panel_candidate_v01/B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V01.json`
- `outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json`
- `outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json` optionnel

## Sorties

- `B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json`
- `B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.md`
- `B9_REALITY_BOARD_SURFACE_CARDS_V0.csv`
- `B9_REALITY_BOARD_SURFACE_TECHNICAL_RISKS_V0.csv`
- `B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_MANIFEST.json`
- `B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.zip`

## Doctrine

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l'effort.  
Le dashboard affiche, il ne décide pas.

## Contraintes

Read-only. Aucune DB. Aucun dashboard live. Aucun Telegram. Aucun ordre directionnel. Aucun taux de réussite.


## V2 hotfix

Le builder `tools/build_t0169_b9_reality_board_surface_adapter_candidate.py` inclut désormais le hotfix `sys.path` racine avant l'import du module `pf_t009_reality_board_surface_adapter_candidate`. Cela évite `ModuleNotFoundError` lorsque le builder est lancé depuis `tools/`.
