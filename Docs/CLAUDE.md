# PowerFlow V7.6.7 — État Central

**[Généré auto : 2026-05-15 10:30]**

---

## Dernière session

- **Date:** 2026-05-15 10:30
- **IA:** Claude Sonnet 4.5
- **Focus:** Infrastructure Admin & Consolidation
- **Checkpoint:** `Checkpoints/CHECKPOINT_20260515_103000.md`
- **Commit:** `📋 Infrastructure automation scripts + Docs/ structure`

---

## État opérationnel PowerFlow

### ✅ Systèmes LIVE

| Composant | Statut | Version | Notes |
|-----------|--------|---------|-------|
| **Core Engine** | 🟢 LIVE | V7.6.7 | Scheduler turbo wrapper actif |
| **Dashboard** | 🟢 LIVE | V7.4 | Terrain panel + time profiles |
| **Capture Bridge** | 🟢 LIVE | — | MT4 → SQLite opérationnel |
| **PowerFlow.db** | 🟢 OK | 15.6 MB | GBPUSD dense, EURUSD HTF incomplet, USDJPY THIN |
| **P0 Validation** | 🟢 PASS_STRICT | — | 16/16 tests Dashboard OK |
| **Git Sync** | 🟢 AUTO | — | `auto_git_sync.ps1` actif |

### ⚠️ Points d'attention

- **USDJPY THIN** → Data stale/sparse, nécessite diagnostic (T004)
- **EURUSD HTF** → Incomplet mais utilisable
- **pf_normalizer.py** → Signature mismatch API /cockpit-state (T003)
- **engine.py legacy** → Refonte V6 nécessaire (T002)

---

## Architecture active

### Modules core PowerFlow

```
pf_*.py                      # Moteur perception flux
├── pf_engine.py             # [LEGACY V5 - Refonte V6 en attente T002]
├── pf_normalizer.py         # Normalisation devises vs USD [HOTFIX needed T003]
├── pf_temporal_nodes.py     # Détection nodes temporels
├── pf_zones.py              # Identification zones clés
├── pf_coalitions.py         # Analyse coalitions devises
├── pf_memory.py             # Système mémoire événements
├── pf_battlefield_map.py    # Cartographie terrain
├── pf_perception_spine_once.py  # Perception spine LIVE
└── pf_trader_attention_packet_once.py  # Attention trader

dashboard_*.html/.py         # Interface trader
├── dashboard_live.html      # [LEGACY - utilisé V7.2.1]
├── dashboard_v74.html       # CURRENT LIVE (terrain panel)
├── dashboard_data_normalizer.py
└── dashboard_v74_contract_check.py

scheduler_*.py               # Orchestration temps réel
├── scheduler_powerflow.py   # Orchestrateur principal
└── scheduler_powerflow_turbo_wrapper.py  # Wrapper turbo LIVE

patch_*.py                   # Patches runtime V7.6+
telegram_*.py                # Alertes Telegram
```

### Base de données

```sql
-- Tables principales
powerflow.db (15.6 MB)
├── bars_m1, bars_m5, bars_m15, bars_m30, bars_h1, bars_h4  # Historique OHLC
├── temporal_nodes           # Nodes détectés
├── scenes                   # Scènes H1 (COALITION_PUSH, TREND_CONTINUATION, etc.)
├── memory_events            # Événements mémorisés
└── dashboard_data           # État dashboard JSON
```

---

## Workflow collaboratif 6 IA

### Dispatch par rôle

| IA | Rôle | Status | Dernière activité |
|---|---|---|---|
| **Claude Sonnet 4.5** | Chef orchestre, architecture, stratégie | 🟢 ACTIVE | T001 Infrastructure automation |
| **GPT-1 Core Engine** | Modules Python `pf_*`, requêtes SQL | ⚪ IDLE | pf_perception_spine patched |
| **GPT-2 Dashboard** | Interface HTML/JS, normalizers | ⚪ IDLE | dashboard_v74.html live |
| **GPT-3 Scheduler** | Orchestration temps réel, Telegram | ⚪ IDLE | scheduler turbo wrapper |
| **GPT-4 Field Memory** | Analyses GBPUSD, film library | ⚪ IDLE | ANALYSE_GBPUSD_20260514 |
| **GPT Pro** | Refactoring majeur, problèmes complexes | ⚪ IDLE | RAPPORT_V76 |

### Coordination

**Fichier central:** `DISPATCH_STATUS.json`  
**Checkpoints:** `Docs/Checkpoints/`  
**Lexique:** `Docs/LEXIQUE_MASTER.md`

**Workflow:**
1. Claude crée tâche → JSON mis à jour
2. GPT prend tâche → statut "in_progress"
3. GPT commit code → statut "completed"
4. Claude valide → archive

---

## Priorités actives

### P0 — CRITICAL
- ✅ **T001** Infrastructure automation (Claude) — 80% complete

### P1 — HIGH
- 🔄 **T002** Refactor `pf_engine.py` V5 → V6 (GPT-1) — Pending
- 🔄 **T006** Consolidation `LEXIQUE_MASTER.md` (Claude) — In progress

### P2 — MEDIUM
- 🔄 **T003** Fix signature `pf_normalizer.py` (GPT-1) — Pending
- 🔄 **T004** Diagnostic USDJPY thin data (GPT Pro) — Pending

### P3 — LOW
- 🔄 **T005** Dashboard V7.4 → V7.5 harmonisation (GPT-2) — Pending

**Voir `DISPATCH_STATUS.json` pour détails complets.**

---

## Scripts automatisation

### 🔧 Infrastructure (nouveaux)

| Script | Fonction | Fréquence |
|--------|----------|-----------|
| `auto_git_sync.ps1` | Commit + push Git intelligent | Après chaque session |
| `auto_checkpoint_claude.ps1` | Checkpoint fin session Claude | Fin session Claude |
| `sync_lexique.ps1` | Consolidation LEXIQUE_MASTER.md | Hebdomadaire |
| `cleanup_backups.ps1` | Nettoyage backups anarchiques | Mensuel |

### ▶️ Runtime (existants)

| Script | Fonction |
|--------|----------|
| `run_powerflow_v767_reality_telegram_cycle.ps1` | Cycle complet perception + Telegram |
| `run_trader_perception_stack_once.py` | Stack perception trader |
| `run_powerflow_live_stack_once.py` | Stack live PowerFlow |

---

## Ressources clés

### Documentation

- **Lexique unifié:** `Docs/LEXIQUE_MASTER.md`
- **Grammaire terrain:** `/mnt/project/07_GRAMMAIRE_NODE_ZONE_DRIVER_V767.md`
- **Film library GBPUSD:** `/mnt/project/09_FILM_LIBRARY_GBPUSD_V767_ENRICHED.md`
- **Règles requalification:** `/mnt/project/10_PACKET_REQUALIFICATION_RULES_V767_ENRICHED.md`
- **Checkpoints:** `Docs/Checkpoints/`

### Liens externes

- **Git:** https://github.com/gestionzen57-alt/V7.git
- **Google Drive:** https://drive.google.com/drive/folders/13n3N2JDUcwf9AXwj7iV9VZkiH9e6bihw
- **Dashboard live:** `http://localhost:8880`

---

## Philosophy PowerFlow

### Concepts centraux

**PowerFlow n'est pas un système d'analyse technique classique.**

PowerFlow est un **moteur de perception du flux** Forex.

**Mission:**
- Voir le flux
- Détecter l'événement
- Alerter vite
- Laisser le trader filtrer
- Laisser le trader décider

**Rôles:**
- La machine → perçoit, mesure, nomme, alerte
- Le trader → filtre, arbitre, agit

### Doctrine centrale

**M1 est central** — Microfilm, naissance événements, inflexion précoce  
**Alerter vite** — Alerte ≠ ordre, c'est une perception transmise  
**Pas de nounou** — Pas de rappels génériques risque financier  
**Flux vivant** — Marché = organisme en mouvement, pas chandeliers isolés  
**Comportemental** — Force relative, asymétries, leader/follower  

---

## Lexique rapide

| Terme FR | Traduction | Définition |
|----------|------------|------------|
| **Tension accumulée** | Accumulated tension | Force potentielle comprimée, prête à relâcher |
| **Élastique chargé** | Overloaded elastic | Zone ayant accumulé trop de pression d'un côté |
| **Pullback absorbé** | Absorbed pullback | Repli rencontrant demande/offre immédiate |
| **Node temporel** | Temporal node | Point pivot où plusieurs forces convergent |
| **Force relative** | Relative strength | Comportement devise vs panier USD |
| **Coalition** | Coalition | Devises majeures alignées poussant USD même sens |
| **Second leg** | Second leg | 2ème vague après consolidation, souvent plus puissante |

**Lexique complet:** `Docs/LEXIQUE_MASTER.md`

---

## Garde-fous V7.6.7

### ❌ INTERDIT

- Modifier `powerflow.db` manuellement
- Casser P0 PASS_STRICT
- Violer Dashboard contract V7.4
- Passer en V7.7 avant stabilité confirmée
- Éditer `CLAUDE.md` manuellement (auto-généré)

### ✅ AUTORISÉ

- Extension/consolidation V7.6.7
- Patches runtime dans `patch/`
- Nouveaux modules `pf_*.py` si tests OK
- Documentation `Docs/`
- Scripts automation `scripts/`

---

## Reprise de session Claude

### Prompt minimal

```
PowerFlow V7.6.7 — Reprise session

Consulte CLAUDE.md pour contexte complet.
Consulte DISPATCH_STATUS.json pour tâches actives.

Prochaine priorité: [indiquer]
```

### Fichiers à charger projet Claude

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

*Document vivant auto-généré — Ne pas éditer manuellement*  
*Mis à jour automatiquement par `auto_checkpoint_claude.ps1`*  
*Dernière modification: 2026-05-15 10:30*
