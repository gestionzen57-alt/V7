# Rapport Mission V7.4-EIE - Confluence Elastique + Telegram

## Objectif

Reintegrer la brique EIE dans le socle PowerFlow recent et la connecter aux couches V7.4 / V7.5.

Couches utilisees :
- Daily Flow Packet
- TopDown Market Reader
- B6 microstructure proxy
- Live Brief
- Telegram dedup memory
- Dashboard surface

EIE ne fonctionne plus comme une alerte isolee.
EIE devient une couche de perception elastique connectee au contexte PowerFlow.

## Chaine actuelle

```text
pf_confluence_elastic.py
-> pf_confluence_gravity.py
-> pf_eie_telegram_gate_once.py
-> run_confluence_alert.py
```

## Commits principaux

```text
a1f83dc Docs: prepare V7.4 EIE integration mission
c60e4c0 V7.4-EIE: add elastic confluence surface
e8460ab V7.4-EIE: add gravity bridge context fusion
eefff8d V7.4-EIE: add telegram gate with dedup memory
d48f136 V7.4-EIE: orchestrate elastic gravity and telegram gate
```

## 1. Elastic Surface

Fichier :

```text
pf_confluence_elastic.py
```

Role :
- lit force_snapshots_v2
- exploite OHLC M1 / M5 / M15
- calcule z-score relatif
- detecte tension elastique
- mesure alignement fractal
- ecrit une surface EIE exploitable

Sorties :

```text
output/dashboard_surface/<SYMBOL>/eie_confluence.json
output/dashboard_surface/<SYMBOL>/eie_confluence.txt
```

Etats EIE :

```text
EIE_IDLE
EIE_LOADING
EIE_LOADED
EIE_OVERSTRETCHED
EIE_RELEASE_PENDING
EIE_DATA_THIN
```

Exemple valide :

```text
GBPUSD | EIE V7.4 | WATCH | EIE_RELEASE_PENDING
state=EIE_RELEASE_PENDING bias=PAIR_DOWN tf=15 score=4.29
fractal=3/3
```

## 2. Gravity Bridge

Fichier :

```text
pf_confluence_gravity.py
```

Role :

```text
EIE
+ Daily Flow Packet
+ TopDown
+ B6
+ Live Brief
= EIE Gravity
```

Sorties :

```text
output/dashboard_surface/<SYMBOL>/eie_gravity.json
output/dashboard_surface/<SYMBOL>/eie_gravity.txt
output/dashboard_surface/eie_gravity_surface.json
```

Syntheses possibles :

```text
EIE_STANDALONE_MONITOR
CONTEXT_READY_EIE_IDLE
EIE_CONTEXT_CONFLICT
TRAP_CONTEXT_ELASTIC_PRESSURE_ALIGNED
ELASTIC_LOADING_WITH_B6_ALIGNMENT
ELASTIC_PRESSURE_IN_REACTION_CONTEXT
```

Exemple valide :

```text
GBPUSD | EIE GRAVITY V7.4 | ACTIVE | TRAP_CONTEXT_ELASTIC_PRESSURE_ALIGNED
state=EIE_RELEASE_PENDING bias=PAIR_DOWN tf=15 score=6.89
```

## 3. Telegram Gate EIE

Fichier :

```text
pf_eie_telegram_gate_once.py
```

Role :
- lit eie_gravity.json
- decide si Telegram doit etre alerte
- applique un seuil minimal
- applique une memoire anti-doublon
- ecrit une decision lisible

Sorties :

```text
output/dashboard_surface/<SYMBOL>/eie_telegram_decision.json
output/dashboard_surface/<SYMBOL>/eie_telegram_decision.txt
output/dashboard_surface/eie_telegram_memory.json
```

Seuil par defaut :

```text
ACTIVE
```

Tests valides :

```text
send=True | NEW_EIE_FAMILY
telegram=WOULD_SEND_DRY_RUN_MARKED

puis deuxieme passage :
send=False | DUPLICATE_EIE_FINGERPRINT_SUPPRESSED
```

## 4. Orchestrateur EIE

Fichier :

```text
run_confluence_alert.py
```

Role actuel :

```text
elastic -> gravity -> telegram gate
```

## Procedure lancement Telegram EIE

### Dry-run standard

```powershell
python run_confluence_alert.py --db powerflow.db --symbol GBPUSD --zone-tf 15 --once --dry-run
```

### Dry-run avec seuil WATCH et memoire marquee

```powershell
python run_confluence_alert.py --db powerflow.db --symbol GBPUSD --zone-tf 15 --once --dry-run --mark-dry-run --min-level WATCH
```

### Telegram reel

Preparer les variables :

```powershell
$env:TELEGRAM_BOT_TOKEN="xxx"
$env:TELEGRAM_CHAT_ID="xxx"
```

Puis lancer :

```powershell
python run_confluence_alert.py --db powerflow.db --symbol GBPUSD --zone-tf 15 --once --send --min-level ACTIVE
```

## Verification des sorties

```powershell
Get-Content output\dashboard_surface\GBPUSD\eie_confluence.txt
Get-Content output\dashboard_surface\GBPUSD\eie_gravity.txt
Get-Content output\dashboard_surface\GBPUSD\eie_telegram_decision.txt
```

## Doctrine

EIE detecte une pression elastique.
EIE ne decide pas.
EIE nomme une perception et reveille le trader quand le contexte le justifie.

La decision reste cote trader.

## Risques techniques

```text
EIE_NOT_LOADED_CURRENTLY
EIE_THIN_SAMPLE
EIE_BAD_CLOSE_SAMPLE
DAILY_LOW_SAMPLE_FOR_ROTATION
WEEKLY_LOW_SAMPLE_FOR_ROTATION
DUPLICATE_EIE_FINGERPRINT_SUPPRESSED
LEVEL_BELOW_EIE_TELEGRAM_THRESHOLD
```

## Etat final

```text
EIE_SURFACE_OK
EIE_GRAVITY_OK
EIE_TELEGRAM_GATE_OK
EIE_DEDUP_MEMORY_OK
EIE_ORCHESTRATOR_OK
```

## Suite logique

Brancher EIE dans :
- run_powerflow_live_stack_once.py
- scheduler_powerflow_turbo_wrapper.py
- dashboard_powerflow_v74.html

But : afficher EIE dans le dashboard et le faire tourner dans le turbo stack global.
