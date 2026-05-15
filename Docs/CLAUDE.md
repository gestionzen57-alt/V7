<!-- POWERFLOW_CURRENT_STATE_START -->
## Current State - updated 2026-05-15T21:01:26.5402470+02:00

- Workspace current-state update for Claude.
- T004 is requalified after expanded USD cohort.
- Global USD-base blockage is invalidated.
- Probable cause for initial USDJPY thin data: feed / EA / capture intermittent or initial setup incomplete.
- Current T004 dispatch status: DIAGNOSED_REQUALIFIED_FEED_CAPTURE_INTERMITTENT.
- No engine/scoring/dashboard/DB patch is justified for T004.
- Canonical current state file: Docs/CURRENT_STATE.md.
- Latest snapshot: Docs/CurrentState/CURRENT_STATE_20260515_210126_T004_REQUALIFIED.md.

<!-- POWERFLOW_CURRENT_STATE_END -->

# PowerFlow V7.6.7 ??? ??tat Central

## Last Session

- Date: 2026-05-15 23:19
- AI: Claude Sonnet 4.5
- Focus: Multi-aspect Session
- Checkpoint: Checkpoints\CHECKPOINT_20260515_231911.md

## Derni??re session

- **Date:** 2026-05-15 10:30
- **IA:** Claude Sonnet 4.5
- **Focus:** Infrastructure Admin & Consolidation
- **Checkpoint:** `Checkpoints/CHECKPOINT_20260515_103000.md`
- **Commit:** `???? Infrastructure automation scripts + Docs/ structure`

---

## ??tat op??rationnel PowerFlow

### ??? Syst??mes LIVE

| Composant | Statut | Version | Notes |
|-----------|--------|---------|-------|
| **Core Engine** | ???? LIVE | V7.6.7 | Scheduler turbo wrapper actif |
| **Dashboard** | ???? LIVE | V7.4 | Terrain panel + time profiles |
| **Capture Bridge** | ???? LIVE | ??? | MT4 ??? SQLite op??rationnel |
| **PowerFlow.db** | ???? OK | 15.6 MB | GBPUSD dense, EURUSD HTF incomplet, USDJPY THIN |
| **P0 Validation** | ???? PASS_STRICT | ??? | 16/16 tests Dashboard OK |
| **Git Sync** | ???? AUTO | ??? | `auto_git_sync.ps1` actif |

### ?????? Points d'attention

- **USDJPY THIN** ??? Data stale/sparse, n??cessite diagnostic (T004)
- **EURUSD HTF** ??? Incomplet mais utilisable
- **pf_normalizer.py** ??? Signature mismatch API /cockpit-state (T003)
- **engine.py legacy** ??? Refonte V6 n??cessaire (T002)

---

## Architecture active

### Modules core PowerFlow

```
pf_*.py                      # Moteur perception flux
????????? pf_engine.py             # [LEGACY V5 - Refonte V6 en attente T002]
????????? pf_normalizer.py         # Normalisation devises vs USD [HOTFIX needed T003]
????????? pf_temporal_nodes.py     # D??tection nodes temporels
????????? pf_zones.py              # Identification zones cl??s
????????? pf_coalitions.py         # Analyse coalitions devises
????????? pf_memory.py             # Syst??me m??moire ??v??nements
????????? pf_battlefield_map.py    # Cartographie terrain
????????? pf_perception_spine_once.py  # Perception spine LIVE
????????? pf_trader_attention_packet_once.py  # Attention trader

dashboard_*.html/.py         # Interface trader
????????? dashboard_live.html      # [LEGACY - utilis?? V7.2.1]
????????? dashboard_v74.html       # CURRENT LIVE (terrain panel)
????????? dashboard_data_normalizer.py
????????? dashboard_v74_contract_check.py

scheduler_*.py               # Orchestration temps r??el
????????? scheduler_powerflow.py   # Orchestrateur principal
????????? scheduler_powerflow_turbo_wrapper.py  # Wrapper turbo LIVE

patch_*.py                   # Patches runtime V7.6+
telegram_*.py                # Alertes Telegram
```

### Base de donn??es

```sql
-- Tables principales
powerflow.db (15.6 MB)
????????? bars_m1, bars_m5, bars_m15, bars_m30, bars_h1, bars_h4  # Historique OHLC
????????? temporal_nodes           # Nodes d??tect??s
????????? scenes                   # Sc??nes H1 (COALITION_PUSH, TREND_CONTINUATION, etc.)
????????? memory_events            # ??v??nements m??moris??s
????????? dashboard_data           # ??tat dashboard JSON
```

---

## Workflow collaboratif 6 IA

### Dispatch par r??le

| IA | R??le | Status | Derni??re activit?? |
|---|---|---|---|
| **Claude Sonnet 4.5** | Chef orchestre, architecture, strat??gie | ???? ACTIVE | T001 Infrastructure automation |
| **GPT-1 Core Engine** | Modules Python `pf_*`, requ??tes SQL | ??? IDLE | pf_perception_spine patched |
| **GPT-2 Dashboard** | Interface HTML/JS, normalizers | ??? IDLE | Dashboard FR Trader V5 stable |
| **GPT-3 Scheduler** | Orchestration temps r??el, Telegram | ??? IDLE | scheduler_powerflow_turbo_wrapper.py |
| **GPT-4 Field Memory** | Analyses GBPUSD, film library | ??? IDLE | ANALYSE_GBPUSD_20260514 |
| **GPT Pro** | Refactoring majeur, probl??mes complexes | ??? IDLE | RAPPORT_V76 |

### Coordination

**Fichier central:** `DISPATCH_STATUS.json`  
**Checkpoints:** `Docs/Checkpoints/`  
**Lexique:** `Docs/LEXIQUE_MASTER.md`

**Workflow:**
1. Claude cr??e t??che ??? JSON mis ?? jour
2. GPT prend t??che ??? statut "in_progress"
3. GPT commit code ??? statut "completed"
4. Claude valide ??? archive

---

## Priorit??s actives

### P0 ??? CRITICAL
- ??? **T001** Infrastructure automation (Claude) ??? 80% complete

### P1 ??? HIGH
- ???? **T002** Refactor `pf_engine.py` V5 ??? V6 (GPT-1) ??? Pending
- ???? **T006** Consolidation `LEXIQUE_MASTER.md` (Claude) ??? In progress

### P2 ??? MEDIUM
- ???? **T003** Fix signature `pf_normalizer.py` (GPT-1) ??? Pending
- ???? **T004** Diagnostic USDJPY thin data (GPT Pro) ??? Pending

### P3 ??? LOW
- ??? **T005** Dashboard FR Trader V5 harmonisation (GPT-2) ??? Completed

**Voir `DISPATCH_STATUS.json` pour d??tails complets.**

---

## Scripts automatisation

### ???? Infrastructure (nouveaux)

| Script | Fonction | Fr??quence |
|--------|----------|-----------|
| `auto_git_sync.ps1` | Commit + push Git intelligent | Apr??s chaque session |
| `auto_checkpoint_claude.ps1` | Checkpoint fin session Claude | Fin session Claude |
| `sync_lexique.ps1` | Consolidation LEXIQUE_MASTER.md | Hebdomadaire |
| `cleanup_backups.ps1` | Nettoyage backups anarchiques | Mensuel |

### ?????? Runtime (existants)

| Script | Fonction |
|--------|----------|
| `run_powerflow_v767_reality_telegram_cycle.ps1` | Cycle complet perception + Telegram |
| `run_trader_perception_stack_once.py` | Stack perception trader |
| `run_powerflow_live_stack_once.py` | Stack live PowerFlow |

---

## Ressources cl??s

### Documentation

- **Lexique unifi??:** `Docs/LEXIQUE_MASTER.md`
- **Grammaire terrain:** `/mnt/project/07_GRAMMAIRE_NODE_ZONE_DRIVER_V767.md`
- **Film library GBPUSD:** `/mnt/project/09_FILM_LIBRARY_GBPUSD_V767_ENRICHED.md`
- **R??gles requalification:** `/mnt/project/10_PACKET_REQUALIFICATION_RULES_V767_ENRICHED.md`
- **Checkpoints:** `Docs/Checkpoints/`

### Liens externes

- **Git:** https://github.com/gestionzen57-alt/V7.git
- **Google Drive:** https://drive.google.com/drive/folders/13n3N2JDUcwf9AXwj7iV9VZkiH9e6bihw
- **Dashboard live:** `http://localhost:8880`

---

## Philosophy PowerFlow

### Concepts centraux

**PowerFlow n'est pas un syst??me d'analyse technique classique.**

PowerFlow est un **moteur de perception du flux** Forex.

**Mission:**
- Voir le flux
- D??tecter l'??v??nement
- Alerter vite
- Laisser le trader filtrer
- Laisser le trader d??cider

**R??les:**
- La machine ??? per??oit, mesure, nomme, alerte
- Le trader ??? filtre, arbitre, agit

### Doctrine centrale

**M1 est central** ??? Microfilm, naissance ??v??nements, inflexion pr??coce  
**Alerter vite** ??? Alerte ??? ordre, c'est une perception transmise  
**Pas de nounou** ??? Pas de rappels g??n??riques risque financier  
**Flux vivant** ??? March?? = organisme en mouvement, pas chandeliers isol??s  
**Comportemental** ??? Force relative, asym??tries, leader/follower  

---

## Lexique rapide

| Terme FR | Traduction | D??finition |
|----------|------------|------------|
| **Tension accumul??e** | Accumulated tension | Force potentielle comprim??e, pr??te ?? rel??cher |
| **??lastique charg??** | Overloaded elastic | Zone ayant accumul?? trop de pression d'un c??t?? |
| **Pullback absorb??** | Absorbed pullback | Repli rencontrant demande/offre imm??diate |
| **Node temporel** | Temporal node | Point pivot o?? plusieurs forces convergent |
| **Force relative** | Relative strength | Comportement devise vs panier USD |
| **Coalition** | Coalition | Devises majeures align??es poussant USD m??me sens |
| **Second leg** | Second leg | 2??me vague apr??s consolidation, souvent plus puissante |

**Lexique complet:** `Docs/LEXIQUE_MASTER.md`

---

## Garde-fous V7.6.7

### ??? INTERDIT

- Modifier `powerflow.db` manuellement
- Casser P0 PASS_STRICT
- Violer Dashboard contract V7.4
- Passer en V7.7 avant stabilit?? confirm??e
- ??diter `CLAUDE.md` manuellement (auto-g??n??r??)

### ??? AUTORIS??

- Extension/consolidation V7.6.7
- Patches runtime dans `patch/`
- Nouveaux modules `pf_*.py` si tests OK
- Documentation `Docs/`
- Scripts automation `scripts/`

---

## Reprise de session Claude

### Prompt minimal

```
PowerFlow V7.6.7 ??? Reprise session

Consulte CLAUDE.md pour contexte complet.
Consulte DISPATCH_STATUS.json pour t??ches actives.

Prochaine priorit??: [indiquer]
```

### Fichiers ?? charger projet Claude

- `00_README_PACK_POWERFLOW_V767_COLLAB.md`
- `01_RAPPORT_COMPLET_POWERFLOW_V767_FIELD_MEMORY.md`
- `03_CURRENT_STATE_POWERFLOW_V767.md`
- `04_DOCTRINE_MANIFESTE_POWERFLOW_V767.md`
- `06_NOMENCLATURE_BRIQUES_CORE_POWERFLOW_V767.md`
- `07_GRAMMAIRE_NODE_ZONE_DRIVER_V767.md`
- `09_FILM_LIBRARY_GBPUSD_V767_ENRICHED.md`
- `10_PACKET_REQUALIFICATION_RULES_V767_ENRICHED.md`
- `12_LEXIQUE_FR_TRADER_POWERFLOW_V767.md`

---

*Document vivant auto-g??n??r?? ??? Ne pas ??diter manuellement*  
*Mis ?? jour automatiquement par `auto_checkpoint_claude.ps1`*  
*Derni??re modification: 2026-05-15 10:30*













### ??? Termin??
- **T005** Dashboard FR Trader V5 harmonisation ??? Completed by GPT-2 Dashboard

<!-- GPT3_SCHEDULER_CURRENT_STATE_BEGIN -->
## GPT-3 Scheduler ??? Current State

Updated: 2026-05-15 20:58:14 +02:00

### Scheduler / Telegram status

- T007 completed: V7.6 Telegram cycle defaults to dry-run.
- T010 completed: Telegram dry-run stdout is UTF-8 safe.
- T011/T012 completed: Core/B8 scheduler scope can be multi-symbol while trader/Telegram tail remains GBPUSD.
- T013B/T013C completed: OVERLAP_SKIP no longer blocks analytical continuation under --continue-on-error.
- T015 completed: B8 FX cohort scope extended and verified on 13 symbols.

### Active B8 / multidevise scope

$coreSymbols

### Architecture note

GBPUSD remains the primary traded/execution symbol.

Do not require dense M1 / tickvolume-per-second data on all cohort pairs. M1/tickvolume-sec is intentionally reserved for GBPUSD to avoid DB growth.

Context symbols are used for coalition, antagonists, gravity, polarity and tempo.

### Recommended next task

T017 ??? make B8 role-aware:

- execution_symbol = GBPUSD
- context_symbols = USD cohort + GBP cohort
- Do not mark B8 degraded only because context symbols lack M1/tickvolume-sec density.
- Add statuses such as:
  - GBPUSD_FULL_STACK_READY
  - USD_INDEX_CONTEXT_READY
  - GBP_INDEX_CONTEXT_READY
  - B8_CONTEXT_READY
  - B8_CONTEXT_DEGRADED

### Guardrails

- No DB modification.
- No Dashboard V7.4 / FR Trader V5 modification.
- No BUY/SELL.
- Telegram stays context transmission only.
- Scheduler orchestrates only.
<!-- GPT3_SCHEDULER_CURRENT_STATE_END -->

<!-- T006-D LEXIQUE MASTER USAGE START -->

## T006-D - Lexique Master usage binding

Status: ACTIVE
Applies from: T006-C / T006-D

### Canonical language sources

- Docs/LEXIQUE_MASTER.md is the active consolidated lexique for PowerFlow trader-facing language.
- Docs/LEXIQUE_MASTER_USAGE_RULES.md defines mandatory usage rules for trader-facing wording.
- LEXIQUE_MASTER source mode: STAGED_V76_V6_WITH_RECREATED_AVENANT.
- AVENANT status: RECREATED_CANDIDATE_NOT_ORIGINAL.

### Mandatory doctrine

- PowerFlow reads market structure; it does not issue guaranteed trading signals.
- PowerFlow qualifies perception; the trader decides.
- PowerFlow must separate observation, qualification, hypothesis, confirmation, invalidation, data limits, and trader decision.
- GBPUSD remains the primary trading surface.
- M1 tickvolume/sec remains GBPUSD-only unless explicitly expanded.
- Multidevise context is used for coalitions, antagonists, gravity, and tempo; it is not a direct trade trigger.
- B8 remains incomplete as a full multicurrency brick until currency-specific tempo is modeled.

### Required trader-facing packet fields

- Film
- Dernier evenement structurel
- Zone active
- Role du mouvement
- Coalitions / antagonistes
- Gravite
- Qualite packet
- Confirmation prix
- Invalidation
- Limites donnees

### Integrity references

- LEXIQUE_MASTER_SHA256: DC4696E565EC9B37AC3D439A852DADB5735F7D1E9FEB398DAEAFBDF91AAB1B2D
- LEXIQUE_MASTER_USAGE_RULES_SHA256: BD830D96A529870A4F6C8229A554EA211A9D7AEA0E2153C7043925AB55ABEA54

<!-- T006-D LEXIQUE MASTER USAGE END -->

