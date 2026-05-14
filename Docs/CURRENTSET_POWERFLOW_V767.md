# CURRENTSET — POWERFLOW V7.6.7

Date : 2026-05-15  
Nom : `POWERFLOW_V767_REALITY_BOARD_TELEGRAM_FINAL`  
HEAD : `ef632ff`  
Statut : **stable**

---

## Version active

```text
PowerFlow V7.6.7
Reality Board + FR final + Telegram primary
```

---

## Git

```text
branch: main
head: ef632ff
remote: origin/main
status: clean après restauration runtime
```

---

## Fichiers essentiels

### Reality Board

```text
patch/pf_reality_board_state_once.py
schema/reality_board_v767.schema.json
schema/reality_board_labels_fr_v767.json
output/dashboard_surface/GBPUSD/reality_board_state.json
```

### Dashboard

```text
dashboard_v76_terrain_panel.js
Core/dashboard_v76_terrain_panel.js
```

### Telegram primary

```text
patch/pf_telegram_reality_board_v767.py
run_powerflow_v767_reality_telegram_cycle.ps1
Docs/README_POWERFLOW_V767_REALITY_TELEGRAM.md
```

### Tests

```text
tests/test_v767_final_fr_labels.py
tests/test_v767_reality_board_cycle_binding.py
tests/test_v767_reality_board_telegram_primary.py
```

---

## Lexique actif

```text
DATA FIRST -> LECTURE TERRAIN
REALITY BOARD -> RÉALITÉ MARCHÉ
ALIGNED_OR_PARTIAL -> alignement partiel
LATE_HIGH_REJECTION_WITH_DEEP_UNWIND -> high tardif rejeté puis unwind profond
READING_PARTIAL -> lecture partielle
HIGH_ZONE_EXHAUSTION_RISK -> risque d’épuisement en zone haute
```

---

## Profils temporels

```text
HTF = Analyse
MTF = Plan
LTF = Action
```

---

## Commandes utiles

```powershell
python patch\pf_reality_board_state_once.py --symbol GBPUSD
python patch\pf_telegram_reality_board_v767.py --symbol GBPUSD --mode dry-run
.\run_powerflow_v767_reality_telegram_cycle.ps1 -RunCoreScheduler -TelegramMode dry-run
```

---

## État fonctionnel

```text
Reality Board dashboard : OK
FR final display : OK
B6 memory : OK
Session alignment : OK
HTF / MTF / LTF : OK
Telegram Reality primary : OK
Dry-run : OK
Git main : OK
```

---

## Risques techniques restants

```text
legacy Telegram encore bavard
live Telegram à valider après dry-run
multi-symbol Reality Board non finalisé
dashboard_data.json runtime à exclure des commits
```

---

## Phrase de reprise

Reprendre depuis V7.6.7 final.  
Reality Board est la surface principale de lecture.  
Telegram primary transmet la perception terrain concise.  
B6/session/HTF-MTF-LTF sont articulés.  
Prochain chantier logique : silence legacy Telegram / V7.6.8.
