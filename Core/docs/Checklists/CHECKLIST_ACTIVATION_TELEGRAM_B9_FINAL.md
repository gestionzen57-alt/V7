# CHECKLIST — Activation Telegram B9 après validation production

## Préconditions

- [ ] Flask `/api/health` OK
- [ ] Flask `/api/b9-nodes-live` OK avec nodes
- [ ] Flask `/api/b8-coalition-context` OK ou fail-soft explicite
- [ ] Scheduler runtime 5 min OK
- [ ] Nouvelle node B9 créée pendant le test
- [ ] Tick archive `tick_stream` récent
- [ ] Dashboard visible
- [ ] Panel B9 visible
- [ ] Panel B8 visible
- [ ] Console F12 sans erreur bloquante
- [ ] Rapport final généré

## Contrat Telegram

- [ ] `ENABLE_TELEGRAM=True` seulement après validation
- [ ] token via `TELEGRAM_BOT_TOKEN`
- [ ] chat id via `TELEGRAM_CHAT_ID`
- [ ] aucun BUY/SELL
- [ ] aucune entrée/stop/target automatique
- [ ] phrase finale : `⚡ Perception transmise — Trader filtre.`

## Risques techniques à surveiller

- [ ] node compatibilité minimale `INCONCLUSIVE`
- [ ] tick archive stale
- [ ] endpoint B8 en `READING_PARTIAL`
- [ ] dashboard pas lancé sur le bon port
- [ ] double structure `Core\Core` avant migration
