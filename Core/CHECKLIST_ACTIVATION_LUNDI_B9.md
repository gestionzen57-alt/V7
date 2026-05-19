# CHECKLIST ACTIVATION LUNDI — PowerFlow B9

## Préconditions marché

- [ ] Marché ouvert.
- [ ] Flux GBPUSD actif.
- [ ] EA / capture T009 actif si utilisé.
- [ ] Bridge ticks -> DB actif.
- [ ] `powerflow.db` détectée.
- [ ] `output/b9_nodes_live` existe.

## Phase 1 — Serveur Flask B9/B8

Terminal 1 :

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python cockpit_server_b9.py
```

Terminal 2 :

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python test_b9_final_end_to_end.py
```

Succès :

- [ ] `/api/health` 200.
- [ ] `/api/b9-nodes-live` 200.
- [ ] `/api/b8-coalition-context` 200.

## Phase 2 — Dashboard

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"
python -m http.server 8000
```

Ouvrir :

```text
http://localhost:8000/Core/dashboard_powerflow_v74.html
```

Vérifier :

- [ ] Panel B9 visible.
- [ ] Panel B8 visible.
- [ ] Polling sans erreur console.
- [ ] F12 : 0 erreur JavaScript.
- [ ] `READING_PARTIAL` visible si data absente.

## Phase 3 — Runtime DRY-RUN 10 min

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python test_b9_runtime_10min_dryrun.py
```

Succès :

- [ ] 10 minutes complètes.
- [ ] 0 erreur.
- [ ] >= 1 node créé.
- [ ] JSON visible dans `output/b9_nodes_live`.

## Phase 4 — Telegram progressif

Avant activation :

- [ ] `TELEGRAM_BOT_TOKEN` configuré.
- [ ] `TELEGRAM_CHAT_ID` configuré.
- [ ] DRY-RUN validé.
- [ ] Message test sans BUY/SELL.
- [ ] Message termine par `⚡ Perception transmise — Trader filtre.`

Lancer l'aide :

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python activate_telegram_b9_monday.py
```

## Risques techniques à surveiller

```text
NO_RECENT_B9_NODE_FOR_SYMBOL
BARS_H1_TABLE_MISSING
DASHBOARD_FILE_MISSING
FLASK_SERVER_UNREACHABLE
NO_B9_NODE_CREATED_DURING_DRYRUN
TELEGRAM_ENV_MISSING
RUNTIME_IMPORT_ERROR
```

## Règle finale

```text
Alerte = perception transmise.
Requalification = meilleure lecture du film.
Telegram = réveil intelligent.
Décision = trader.
```
