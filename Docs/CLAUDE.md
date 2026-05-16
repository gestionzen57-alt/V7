# PowerFlow V7.6.7 — État Central

**[Mis à jour : 2026-05-15 14:30 par Claude Sonnet 4.5]**

---

## 🎯 Dernière session

- **Date:** 2026-05-15 14:30
- **IA:** Claude Sonnet 4.5
- **Focus:** Point complet post-GPT + B8 multidevises 13 symboles
- **Checkpoint:** `Checkpoints/CHECKPOINT_20260515_143000.md`
- **Git dernier commit:** `5d05912` feat(scheduler): extend B8 FX cohort scope

---

## ✅ État opérationnel PowerFlow

### Systèmes LIVE

| Composant | Statut | Version | Notes |
|-----------|--------|---------|-------|
| **Core Engine** | 🟢 LIVE | V7.6.7 | Scheduler turbo wrapper actif |
| **Dashboard** | 🟢 LIVE | V7.5 FR | Labels trader français appliqués |
| **Capture Bridge** | 🟢 LIVE | — | MT4 → SQLite opérationnel |
| **PowerFlow.db** | 🟢 OK | 15.6 MB | GBPUSD dense M1, 13 symboles B8 champ |
| **P0 Validation** | 🟢 PASS_STRICT | — | 16/16 tests Dashboard OK |
| **Git Sync** | 🟢 AUTO | — | `auto_git_sync.ps1` actif |
| **Session Overlay V2** | 🟢 LIVE | — | Contexte UTC injecté alertes |
| **B8 Multidevises** | 🟢 LIVE | 13 symboles | FX cohort étendu validé |

### Points d'attention résolus

- ✅ **T003 pf_normalizer.py** → RÉSOLU (wrapper compatibilité appliqué)
- ✅ **T004 USDJPY THIN** → DIAGNOSTIQUÉ (pas bug PowerFlow, feed/EA/capture intermittent)
- ✅ **T005 Dashboard FR** → RÉSOLU (labels trader français V5)
- ✅ **T007 Session Overlay V2** → LIVE (contexte session UTC actif)
- ✅ **T008 Scheduler Telegram** → RÉSOLU (dry-run sécurisé, B8 13 symboles)
- ✅ **T013C Overlap skip** → RÉSOLU (filtré --continue-on-error)
- ✅ **T015 B8 FX cohort** → RÉSOLU (13 symboles validés)
- 🔄 **T002 engine.py refactor** → 80% (detached core validé, intégration pending)

---

## 📊 Workflow collaboratif 6 IA

### État des tâches (DISPATCH_STATUS.json)

| Tâche | Titre | Priorité | Assigné | Statut | Progrès |
|-------|-------|----------|---------|--------|---------|
| **T001** | Infrastructure automation | P0 | Claude | 🔄 IN_PROGRESS | 80% |
| **T002** | Refactor engine V5→V6 | P1 | GPT-1 | 🔄 IN_PROGRESS | 80% |
| **T003** | Fix pf_normalizer signature | P2 | GPT-1 | ✅ COMPLETED | 100% |
| **T004** | Diagnostic USDJPY thin | P2 | GPT-1 | ✅ DIAGNOSED | 100% |
| **T005** | Dashboard FR trader | P3 | GPT-2 | ✅ COMPLETED | 100% |
| **T006** | Consolidation LEXIQUE | P1 | Claude | ⚪ PENDING | 0% |
| **T007** | Session Overlay V2 | P1 | GPT-2 | ✅ COMPLETED | 100% |
| **T008** | Scheduler Telegram + B8 | P1 | GPT-3 | ✅ COMPLETED | 100% |
| **T013C** | Overlap skip filtré | P2 | GPT-3 | ✅ COMPLETED | 100% |
| **T015** | B8 FX cohort 13 symboles | P1 | GPT-3 | ✅ COMPLETED | 100% |

**Taux de complétion global** : 70% (7/10 tâches complètes)

### Dispatch par rôle

| IA | Rôle | Status | Tâches actives | Tâches complètes |
|---|---|---|---|---|
| **Claude Sonnet 4.5** | Chef orchestre, architecture | 🟢 ACTIVE | T001, T006 | — |
| **GPT-1 Core Engine** | Modules `pf_*`, SQL | ⚪ IDLE | T002 | T003, T004 |
| **GPT-2 Dashboard** | Interface HTML/JS | ⚪ IDLE | — | T005, T007 |
| **GPT-3 Scheduler** | Orchestration, Telegram, B8 | ⚪ IDLE | — | T008, T013C, T015 |
| **GPT-4 Field Memory** | Analyses GBPUSD, films | ⚪ IDLE | — | — |
| **GPT Pro** | Comité experts, refactoring | ⚪ STANDBY | — | — |

---

## 🌍 B8 MULTIDEVISES — Scope 13 Symboles FX Cohort

### Statut

**✅ LIVE** — Validé commit `5d05912`

### Scope B8 validé (13 symboles)

**USD-quote (coalition EUR/GBP/AUD/NZD push USD)** :
- GBPUSD (exécution principale)
- EURUSD
- AUDUSD
- NZDUSD

**USD-base (antagonistes USD push devises)** :
- USDJPY
- USDCAD
- USDCHF

**GBP cross (champ GBP multidevise)** :
- EURGBP
- GBPJPY
- GBPAUD
- GBPCAD
- GBPCHF
- GBPNZD

### Doctrine multidevises PowerFlow

**GBPUSD** :
```
Rôle : Lecture principale / exécution / M1 dense / Telegram / trader
Data : M1 dense actif
Usage : Scalping / décision immédiate / alertes trader
```

**Autres 12 paires** :
```
Rôle : Champ multidevise / coalition / antagonistes / gravité
Data : PAS M1 dense — M5/M15/M30/H1 seulement
Usage : Contexte relatif / leader/follower / force comparative
```

**Rationale** :
```
Éviter gonflement DB anarchique.
M1 dense = coût DB élevé.
GBPUSD suffit pour scalping exécution.
Autres paires = lecture champ, pas exécution M1.
```

### Validation B8

**DB validation** : ✅ DB voit 13 symboles  
**Surface folders** : ✅ Core/output/dashboard_surface/{13 symboles}  
**Aggregate outputs** : ✅ B8/multiread contient 13 symboles  
**Telegram/trader** : ✅ Reste GBPUSD seulement  

### Outputs B8

**Fichiers générés** :
```
Core/output/dashboard_surface/b8_multiread_surface.json
Core/output/dashboard_surface/b8_coalition_context.json
Core/output/dashboard_surface/b8_antagonist_map.json
Core/output/dashboard_surface/b8_gravity_field.json
```

**Par symbole** :
```
Core/output/dashboard_surface/{symbol}/
├── behavioral_context.json
├── force_snapshot.json
└── temporal_context.json
```

---

## 🏆 Tâches complètes récentes (détails Git)

### ✅ T003 — pf_normalizer signature hotfix

**Commits** :
- `b201c09` hotfix signature `detect_tf_alignment`
- `4116986` checkpoint repair

**Livrable** : Wrapper compatibilité, ancienne implémentation préservée

**Statut** : CLÔTURÉ

---

### ✅ T004 — Diagnostic USDJPY complet (15 phases)

**Audit exemplaire GPT-1** — 28 commits, 15 phases investigation

**Verdict final** (`870dc1b`) :
```
GLOBAL_USD_BASE_BLOCKAGE_INVALIDATED
DIAGNOSED_REQUALIFIED_FEED_CAPTURE_INTERMITTENT
NOT_A_POWERFLOW_BUG
```

**Action PowerFlow** : AUCUNE — issue côté MT4 feed/EA/capture

**Statut** : CLÔTURÉ

---

### ✅ T005 — Dashboard FR trader labels

**Commits** : `a684746` → `2aac215` (6 commits)

**Livrable** :
- Labels français trader V5
- `dashboard_fr_trader_labels.js`
- `patch_dashboard_fr_trader.ps1`

**Statut** : CLÔTURÉ

---

### ✅ T007 — Session Overlay V2

**Livrable GPT-2** :
- `Core/pf_session_overlay.py` ✅
- `output/session_context.json` ✅

**Sessions UTC** :
- ASIAN 22:00-08:00
- LONDON 07:00-16:00
- NY 12:00-21:00
- OVERLAP 12:00-16:00
- DEAD_ZONE 20:00-22:00

**Statut** : LIVE

---

### ✅ T008 — Scheduler Telegram safety + B8 multidevises

**Commits** :
- `c0d3aee` default Telegram dry-run
- `54cabdb` decode dry-run stdout UTF-8
- `968cae2` filter overlap skip (T013C)
- `5d05912` extend B8 FX cohort scope (T015)

**Livrable** :
- Telegram dry-run par défaut ✅
- UTF-8 decode corrigé ✅
- OVERLAP_SKIP filtré ✅
- B8 scope 13 symboles ✅

**Statut** : CLÔTURÉ

---

### ✅ T013C — Overlap skip filtré

**Commit** : `968cae2` filter overlap skip from turbo failures

**Livrable** : OVERLAP_SKIP ne remonte plus comme erreur turbo

**Statut** : CLÔTURÉ (intégré T008)

---

### ✅ T015 — B8 FX cohort 13 symboles

**Commit** : `5d05912` feat: extend B8 FX cohort scope

**Livrable** :
- 13 symboles FX cohort validés
- DB voit 13 symboles
- Surface folders 13 symboles
- Aggregate outputs multiread 13 symboles

**Statut** : CLÔTURÉ

---

## 🔄 Tâches en cours (détails)

### T002 — Refactor engine V5→V6 (80% GPT-1)

**Approche sécurisée exemplaire** :

**Livrables détachés validés** :
- `pf_engine_v6_adapter.py` ✅
- `pf_engine_v6_core.py` ✅ (23 tests pass)
- Contrats JSON ✅

**Prochaine étape** :
- Intégration runtime live
- Tests backward compatibility

**Blockers** : Aucun technique

---

### T001 — Infrastructure automation (80% Claude)

**Livrable attendu** :
- `auto_git_sync.ps1` ✅
- `auto_checkpoint_claude.ps1` ✅
- `sync_lexique.ps1` (pending)
- `cleanup_backups.ps1` (pending)

**Prochaine étape** : Finaliser scripts lexique + cleanup

**Blockers** : Aucun

---

## 🎯 Priorités actives

### P0 — CRITICAL
- 🔄 **T001** Infrastructure automation (Claude) — 80%

### P1 — HIGH
- 🔄 **T002** Refactor engine V5→V6 (GPT-1) — 80%
- ⚪ **T006** Consolidation LEXIQUE_MASTER.md (Claude) — Pending T001

### P2-P3 — MEDIUM/LOW
- ✅ Toutes complètes

---

## 📋 Prochaines priorités

1. **T001** — Finaliser infrastructure automation (Claude)
2. **T002** — Intégrer pf_engine_v6_core en runtime (GPT-1)
3. **T006** — Consolider LEXIQUE_MASTER.md (Claude)
4. **GPT Pro** — Réunion comité experts (après consolidation)

**Blockers globaux** :
- T001 incomplete → bloque T006
- T002 integration runtime → attente validation backward compatibility

---

## 🔧 Scripts automatisation

### Infrastructure (nouveaux)

| Script | Fonction | Statut | Fréquence |
|--------|----------|--------|-----------|
| `auto_git_sync.ps1` | Commit + push Git intelligent | ✅ ACTIF | Après session |
| `auto_checkpoint_claude.ps1` | Checkpoint fin session Claude | ✅ ACTIF | Fin session |
| `sync_lexique.ps1` | Consolidation LEXIQUE_MASTER.md | 🔄 PENDING | Hebdomadaire |
| `cleanup_backups.ps1` | Nettoyage backups anarchiques | 🔄 PENDING | Mensuel |

### Runtime (existants)

| Script | Fonction | Statut |
|--------|----------|--------|
| `run_powerflow_v767_reality_telegram_cycle.ps1` | Cycle complet perception + Telegram | ✅ ACTIF |
| `run_trader_perception_stack_once.py` | Stack perception trader | ✅ ACTIF |
| `run_session_overlay_once.py` | Session context UTC | 🟢 NEW LIVE |
| `scheduler_powerflow_turbo_wrapper.py` | Scheduler B8 13 symboles | 🟢 PATCHED LIVE |

---

## 📚 Architecture active

### Modules core PowerFlow

```
pf_*.py                      # Moteur perception flux
├── engine.py                # [LEGACY 283 lignes — cible T002]
├── pf_engine_v6_adapter.py  # [NEW T002] Adapter boundary
├── pf_engine_v6_core.py     # [NEW T002] Detached core (23 tests)
├── pf_normalizer.py         # [PATCHED T003] Wrapper compatibilité
├── pf_session_overlay.py    # [NEW T007] Session context UTC
├── pf_temporal_nodes.py     # Détection nodes temporels
├── pf_zones.py              # Identification zones clés
├── pf_coalitions.py         # Analyse coalitions devises
├── pf_memory.py             # Système mémoire événements
├── pf_battlefield_map.py    # Cartographie terrain
├── pf_perception_spine_once.py  # Perception spine LIVE
└── pf_trader_attention_packet_once.py  # Attention trader

dashboard_*.html/.py         # Interface trader
├── dashboard_v74.html       # [PATCHED T005] Labels FR V5
├── dashboard_data_normalizer.py
└── dashboard_v74_contract_check.py

scheduler_*.py               # Orchestration temps réel
├── scheduler_powerflow.py   # Orchestrateur principal
└── scheduler_powerflow_turbo_wrapper.py  # [PATCHED T008/T015] B8 13 symboles

b8_*.py                      # B8 multidevises (intégré V7.3)
├── b8_multiread_surface.py  # Lecture 13 symboles
├── b8_coalition_context.py  # Coalition devises
├── b8_antagonist_map.py     # Antagonistes USD
└── b8_gravity_field.py      # Champ gravité relatif
```

### Base de données

```sql
-- Tables principales
powerflow.db (15.6 MB) — Chemin actif : Core/powerflow.db

-- GBPUSD (exécution principale)
├── bars_m1 (GBPUSD dense)
├── bars_m5, bars_m15, bars_m30, bars_h1, bars_h4 (GBPUSD complet)
├── flow_packets (GBPUSD actif)
├── force_snapshots_v2 (GBPUSD actif)

-- 12 autres paires (champ multidevise)
├── bars_m5, bars_m15, bars_m30, bars_h1, bars_h4 (PAS M1 dense)

-- Contexte global
├── temporal_nodes           # Nodes détectés
├── scenes                   # Scènes H1
├── memory_events            # Événements mémorisés
└── dashboard_data           # État dashboard JSON
```

**Densité symboles** :
- **GBPUSD** : 36059 rows (DENSE M1) — exécution principale
- **EURUSD** : 5361 rows (OK HTF champ)
- **USDJPY** : 4060 rows (THIN — feed intermittent, champ seulement)
- **Autres 10 paires** : Champ multidevise (pas M1 dense)

**Doctrine data** :
```
M1 dense = GBPUSD seulement (scalping exécution)
M5/M15/M30/H1 = 13 symboles (contexte champ)
Éviter gonflement DB : pas M1 dense partout
```

---

## 🎓 Ressources clés

### Documentation

- **Lexique unifié:** `Docs/LEXIQUE_MASTER.md` (consolidation T006 pending)
- **Grammaire terrain:** `/mnt/project/07_GRAMMAIRE_NODE_ZONE_DRIVER_V767.md`
- **Film library GBPUSD:** `/mnt/project/09_FILM_LIBRARY_GBPUSD_V767_ENRICHED.md`
- **Règles requalification:** `/mnt/project/10_PACKET_REQUALIFICATION_RULES_V767_ENRICHED.md`
- **Checkpoints:** `Docs/Checkpoints/`
- **Dispatch central:** `DISPATCH_STATUS.json` (mis à jour 2026-05-15 14:30)

### Liens externes

- **Git:** https://github.com/gestionzen57-alt/V7.git
- **Dernier commit:** `5d05912` feat(scheduler): extend B8 FX cohort scope
- **Google Drive:** https://drive.google.com/drive/folders/13n3N2JDUcwf9AXwj7iV9VZkiH9e6bihw
- **Dashboard live:** `http://localhost:8880`

---

## 💡 Philosophy PowerFlow

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

**M1 est central** — Microfilm GBPUSD, naissance événements, inflexion précoce  
**Alerter vite** — Alerte ≠ ordre, c'est une perception transmise  
**Pas de nounou** — Pas de rappels génériques risque financier  
**Flux vivant** — Marché = organisme en mouvement, pas chandeliers isolés  
**Comportemental** — Force relative, asymétries, leader/follower  
**Multidevises** — GBPUSD exécution, autres paires champ contextuel  

---

## 📖 Lexique rapide

| Terme FR | Traduction | Définition |
|----------|------------|------------|
| **Tension accumulée** | Accumulated tension | Force potentielle comprimée, prête à relâcher |
| **Élastique chargé** | Overloaded elastic | Zone ayant accumulé trop de pression d'un côté |
| **Pullback absorbé** | Absorbed pullback | Repli rencontrant demande/offre immédiate |
| **Node temporel** | Temporal node | Point pivot où plusieurs forces convergent |
| **Force relative** | Relative strength | Comportement devise vs panier USD |
| **Coalition** | Coalition | Devises majeures alignées poussant USD même sens |
| **Antagoniste** | Antagonist | Devise opposée à coalition (USD-base vs USD-quote) |
| **Champ multidevise** | Multi-currency field | Contexte 13 symboles FX cohort |
| **Second leg** | Second leg | 2ème vague après consolidation, souvent plus puissante |

**Lexique complet:** `Docs/LEXIQUE_MASTER.md` (consolidation T006 pending)

---

## 🛡️ Garde-fous V7.6.7

### ❌ INTERDIT

- Modifier `powerflow.db` manuellement
- Casser P0 PASS_STRICT
- Violer Dashboard contract V7.5
- Passer en V7.7 avant stabilité confirmée V7.6.7
- Éditer `CLAUDE.md` manuellement (auto-généré)
- Éditer `DISPATCH_STATUS.json` sans coordination
- Activer M1 dense sur autres paires que GBPUSD

### ✅ AUTORISÉ

- Extension/consolidation V7.6.7
- Patches runtime dans `patch/`
- Nouveaux modules `pf_*.py` si tests OK
- Documentation `Docs/`
- Scripts automation `scripts/`
- Mise à jour `DISPATCH_STATUS.json` via workflow formel
- Extension scope B8 multidevises (pas M1 dense)

---

## 🚀 Stratégie GPT Pro — Comité d'Experts

### Timing optimal

**APRÈS consolidation V7.6.7** :

**Pré-requis** :
1. ✅ Git sync complet → **FAIT (5d05912)**
2. ✅ DISPATCH_STATUS.json créé → **FAIT**
3. ✅ B8 multidevises 13 symboles → **VALIDÉ**
4. 🔄 T001 Infrastructure automation 100% → **PENDING (80%)**
5. 🔄 Tests runtime T002 → **PENDING**
6. 🔄 CLAUDE.md mis à jour → **EN COURS**

**Mission Comité GPT Pro** :
```
Challenge architectural avant implémentation V7.7
↓
1. Audit briques existantes (B2/B3/B4/P1/B5/B6/B7/B8)
2. Validation grammaire terrain
3. Exploitation film library GBPUSD
4. Exploitation B8 multidevises 13 symboles
5. Règles requalification packets
6. Plan minimal patch (pas de refonte)
7. Identification risques techniques
8. Roadmap V7.7 optimisée
```

**Input** : Pack complet V7.6.7 (17 docs) + DISPATCH_STATUS.json  
**Prompt** : `13_PROMPT_REUNION_COMITE_EXPERTS_GPT_PRO_V767.md`  
**Output attendu** :
- Audit architectural brutal
- Briques à exploiter/fusionner/abandonner
- Exploitation B8 FX cohort 13 symboles
- Plan patch minimal V7.7
- Ordre implémentation
- Critères succès/arrêt

**Statut** : ⚪ **STANDBY** — Attente finalisation T001 + tests runtime T002

---

## 📝 Reprise de session Claude

### Prompt minimal

```
PowerFlow V7.6.7 — Reprise session

Consulte CLAUDE.md pour contexte complet.
Consulte DISPATCH_STATUS.json pour tâches actives.

B8 multidevises 13 symboles LIVE.
Doctrine : GBPUSD exécution / autres champ.

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
- `DISPATCH_STATUS.json` (mis à jour 14:30)

---

## ⚠️ Risques identifiés

### Medium

**T002 integration runtime** peut révéler edge cases non couverts par tests detached

**Mitigation** : Approche adapter boundary + golden tick cases en place

### Low

**B8 scope 13 symboles** peut générer volume DB supérieur à prévu

**Mitigation** : Doctrine multidevises — M1 dense GBPUSD seulement, autres = champ HTF

---

## 🏅 Notes qualité

- **GPT-3 B8 multidevises** — Extension 13 symboles FX cohort validée, doctrine GBPUSD exécution / autres champ respectée
- **GPT-1 audit T004 exemplaire** — 15 phases, invalidation hypothèse rigoureuse
- **T002 approche sécurisée** — contract-freeze → adapter → detached core validée
- **T007 Session Overlay V2** — LIVE, contexte session UTC injecté alertes
- **Git history propre** — commits structurés, checkpoints systématiques

---

*Document vivant auto-généré — Ne pas éditer manuellement*  
*Mis à jour automatiquement par `auto_checkpoint_claude.ps1`*  
*Dernière modification: 2026-05-15 14:30*  
*Git HEAD: 5d05912 feat(scheduler): extend B8 FX cohort scope*  
*B8 Multidevises: 13 symboles FX cohort LIVE*
