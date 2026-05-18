# T0159 — B9 French Event Display Contract V0

## Résumé exécutif

T0159 crée une couche de traduction FR trader pour les événements B9/B6 utilisés par dashboard, Reality Board et Telegram preview.

Le moteur garde les enums techniques anglais pour les tests et la stabilité. Les surfaces affichent un libellé et une phrase en français trader.

## Doctrine

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l'effort.  
B6 compare les films.  
L'affichage transmet une lecture, pas une décision.

## Catégories couvertes

- scene_state
- scene_transition
- scene_role
- price_verdict
- terrain_node
- memory_confidence_ladder
- false_positive_context
- source_quality_gate
- telegram_gate_state
- reality_board_payload_state

## Sorties

- `B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json`
- `B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.csv`
- `B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.md`
- `B9_FRENCH_EVENT_DISPLAY_EXAMPLES_V0.json`
- `B9_FRENCH_EVENT_DISPLAY_CONTRACT_MANIFEST.json`
- `B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.zip`

## Limites

Read-only. Aucune DB. Aucun dashboard live. Aucun envoi Telegram. Aucun ordre directionnel. Aucun taux de réussite.
