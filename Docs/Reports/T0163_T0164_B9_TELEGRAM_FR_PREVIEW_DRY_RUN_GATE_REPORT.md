# T0163/T0164 — B9 Telegram FR Preview + Dry Run Gate

## Status
`READY`

## Objectif
Préparer Telegram maintenant que T0148/T0155/T0156/T0157 sont fonctionnels, mais sans envoi réel.

## Entrées
```text
outputs/b9_telegram_fr_gate_candidate_v0/B9_TELEGRAM_FR_GATE_CANDIDATE_V0.json
outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json
outputs/b9_trader_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json
outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json
```

## Sorties
```text
outputs/b9_telegram_fr_preview_v0/B9_TELEGRAM_FR_PREVIEW_V0.md
outputs/b9_telegram_fr_preview_v0/B9_TELEGRAM_FR_PREVIEW_V0.json
outputs/b9_telegram_fr_preview_v0/B9_TELEGRAM_DRY_RUN_GATE_V0.json
outputs/b9_telegram_fr_preview_v0/B9_TELEGRAM_DRY_RUN_GATE_V0.md
```

## Format message candidat
```text
B9 voit : ...
Zone : ...
État : ...
Mémoire proche : ...
Piège technique : ...
À surveiller : ...
Limite : ...
```

## Interdits
```text
BUY
SELL
achat
vente
entre maintenant
probabilité de réussite
signal gagnant
conseil financier
```

## Contraintes
Aucun envoi Telegram. Aucun module d’envoi. Aucun credential touché. Aucun module `telegram_*` modifié. Read-only. Aucune DB. Aucun dashboard live.

## Doctrine
Le message Telegram réveille l’attention, il ne décide pas.
