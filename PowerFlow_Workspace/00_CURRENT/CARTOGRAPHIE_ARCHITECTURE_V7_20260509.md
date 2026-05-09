# CARTOGRAPHIE ARCHITECTURE — PowerFlow V7
**Date : 2026-05-09 | Version : V7 | Git : c579afa**

---

## 1. VUE MACRO — COUCHES DU SYSTÈME

```
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 0 — ACQUISITION                                      │
│  capture_bridge.py  ←  MT4 (TCP tick)  →  powerflow.db      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 1 — MOTEUR (pf_*)                                    │
│  Calcul / Analyse / Mémoire / Événements                     │
│  Read-only DB. Aucune dépendance cockpit/dashboard/telegram  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 2 — RUNNERS (run_*)                                  │
│  CLI / Daemons / Orchestrateurs                              │
│  Lisent moteur. Écrivent queues JSON.                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 3 — COCKPIT / DASHBOARD (cockpit_* / dashboard_*)    │
│  Lecture / Synthèse / Affichage                              │
│  Ne modifie jamais la logique moteur                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 4 — TRANSMISSION (telegram_*)                        │
│  Alertes externes — activé après cockpit stable              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 5 — TRADER                                           │
│  Décision finale. Filtre. Arbitre. Accepte.                  │
│  La machine ne décide pas.                                   │
└─────────────────────────────────────────────────────────────┘
```

**Règle fondamentale** : les dépendances vont uniquement vers le bas.
`pf_*` ne connaît jamais `cockpit_*`. `cockpit_*` ne connaît jamais `telegram_*`.
Violation = dépendance circulaire = bug architectural.

---

## 2. CHAÎNE RUNTIME COMPLÈTE V7

```
powerflow.db (force_snapshots — read-only)
    │
    ├──→ B1  pf_regime_engine.py
    │         HTF_CONTEXT_STACK {W, D, H4, H1}
    │         regime_confidence
    │
    ├──→ B3  pf_force_kinematics.py
    │         angle_kalman / speed_kalman / noise_ratio
    │         first_detachment / same_angle_cluster
    │
    │        pf_tension_signature.py
    │         ELASTIC_LOADED / DIRECTIONAL_MOVE / DEAD_CURRENCY
    │
    ├──→ P1  pf_currency_energy_probe.py
    │         elastic_tension_score / energy_state
    │
    ├──→     pf_temporal_node_state.py  (Node V0.8.2)
    │         capture_quality / relay_quality / release_state
    │         kinematics_state / energy_context
    │
    ├──→ B4  pf_temporal_density.py
    │         CYCLE_COMPRESSING / compression_ratio / dominant_period_bars
    │         compression_alert (3+ devises)
    │
    ├──→ B5  pf_spearman_gravity.py
    │         spearman_rho / avg_rho / SYNCHRO / DIVERGENT_EXTREME
    │         MIXED_PROBABILISTE (résout P1.2 MIXED)
    │
    ├──→     pf_confluence_elastic.py
    │         EIE / EWZ / ENZ / ZNE
    │         fractalite (0-3) / elastic_score
    │
    ├──→     pf_confluence_gravity.py
    │         fusion_state / confidence
    │         EIE × B1 × B5 × RG
    │
    ├──→ P4  run_confluence_alert.py  (daemon 5min)
    │         EIE_PERSISTANT → behavioral_alert_queue.json
    │
    ├──→ B2  pf_cascade_engine.py
    │         SEQUENCE_VELOCITY_HIGH / events_count / cascade_building
    │
    ├──→     pf_behavioral_alert_mapper.py  (V7 — regime_context enrichi)
    │         behavioral_alert_queue.json  (append)
    │
    └──→     pf_relational_gravity_bridge.py  (bridge_version=0.1.4)
              pf_orchestral_gravity_v02.py
              → cockpit_agentic_state_v01.py
              → dashboard_sync_agent_v01.py
              → dashboard_live.html
```

---

## 3. INVENTAIRE FICHIERS — COUCHE MOTEUR (pf_*)

| Fichier | Brique | Rôle | Statut |
|---------|--------|------|--------|
| `pf_temporal_node_state.py` | Core | Node engine V0.8.2 — 99KB | ✅ STABLE |
| `pf_regime_engine.py` | B1 | HTF contexte + régime | ✅ V7 |
| `pf_cascade_engine.py` | B2 | Vélocité séquence 5min | ✅ V7 |
| `pf_force_kinematics.py` | B3 | Kalman angle/speed | ✅ V7 |
| `pf_temporal_density.py` | B4 | Cycles autocorrélation | ✅ V7 |
| `pf_spearman_gravity.py` | B5 | Corrélation de rang paires | ✅ V7 |
| `pf_currency_energy_probe.py` | P_NEXT_1 | Énergie + tension élastique | ✅ V7 |
| `pf_behavioral_alert_mapper.py` | P2 | Mapper alertes + regime_context | ✅ V7 |
| `pf_relational_gravity_bridge.py` | P1.2 | RG bridge guard MIXED | ✅ 0.1.4 |
| `pf_orchestral_gravity_v02.py` | Orchestral | Leader/follower multi-TF | ✅ V6 |
| `pf_confluence_elastic.py` | Confluence | EIE + fractalité | ✅ V7 |
| `pf_confluence_gravity.py` | Confluence | Fusion EIE×B1×B5×RG | ✅ V7 |
| `pf_tension_signature.py` | P_NEXT_1 | Micro/macro variance | ✅ V7 |
| `pf_flow_nodes.py` | Core | Fractal nodes | ✅ V6 |
| `pf_personalities.py` | Core | Profils devises | ✅ V6 |
| `pf_zone_dynamics.py` | Core | Dynamique zones | ✅ V6 |

---

## 4. INVENTAIRE FICHIERS — RUNNERS (run_*)

| Fichier | Fréquence | Rôle |
|---------|-----------|------|
| `run_regime_engine_once.py` | On-demand | Snapshot B1 |
| `run_cascade_engine_once.py` | On-demand | Snapshot B2 |
| `run_temporal_density_once.py` | On-demand | Snapshot B4 |
| `run_spearman_gravity_once.py` | On-demand | Snapshot B5 |
| `run_temporal_node_state_once.py` | On-demand | Snapshot Node |
| `run_currency_energy_probe_once.py` | On-demand | Snapshot Energy |
| `run_behavioral_alert_mapper_once.py` | On-demand | Snapshot Mapper |
| `run_confluence_alert.py` | Daemon 5min | EIE → queue |
| `run_confluence_scan.py` | On-demand | Historique EIE |
| `run_orchestral_loop.py` | On-demand | Snapshot Orchestral |
| `run_powerflow_dashboard_refresh_once.py` | On-demand | Refresh cockpit |

---

## 5. INVENTAIRE FICHIERS — LAB (lab_*)

| Fichier | Version | Rôle |
|---------|---------|------|
| `lab_powerflow.py` | V3 | 11 couches — queries exploration |
| `pf_lab_engine.py` | V3 | Moteur lab |
| `lab_elastic.py` | V1.0 | 6 queries EIE |

---

## 6. INVENTAIRE FICHIERS — COCKPIT / DASHBOARD

| Fichier | Version | Rôle | Statut |
|---------|---------|------|--------|
| `cockpit_agentic_state_v01.py` | V7 | Synthèse + regime_block + cascade | ✅ |
| `cockpit_agentic_state_v01_orchestral.py` | V0.1.4 | Orchestral cockpit | ✅ STABLE |
| `dashboard_sync_agent_v01.py` | V7 | Sync dashboard | ✅ |
| `dashboard_server.py` | V7 | Serveur Flask | ✅ |
| `dashboard_live.html` | V7 | Interface live | ✅ |

**VERSIONS REJETÉES** : cockpit_orchestral V0.1.5+ = NO GO

---

## 7. ACQUISITION — COUCHE 0

```
MT4 (MetaTrader 4)
  │
  │  TCP tick data
  │
  ↓
capture_bridge.py     ← NE PAS MODIFIER
  │
  │  INSERT force_snapshots
  │
  ↓
powerflow.db          ← NE PAS ÉCRIRE MANUELLEMENT
  │
  │  Tables principales :
  │  - force_snapshots (tick / barre par TF par devise)
  │  - behavioral_alert_queue (alertes produites)
  │
  └─→ Tout le reste : READ ONLY
```

---

## 8. QUEUES JSON — INTERFACES ENTRE COUCHES

```
output/
├── temporal_node_state.json         ← Node V0.8.2 output
├── behavioral_alert_queue.json      ← Alertes mapper + daemon
├── cockpit_agentic_state_v01.json   ← Synthèse cockpit
├── dashboard_data.json              ← Dashboard sync
├── lab_full_v3.json                 ← Lab sessions
└── cockpit_orchestral_*.json        ← Sessions orchestral
```

Règle : les queues JSON sont des interfaces de lecture entre couches.
Elles ne remplacent pas la DB. Elles ne sont pas persistées sur Git.

---

## 9. LAB ENGINE — 11 COUCHES

```
Couche  1  kinematics       angle / speed / accel / first_detachment
Couche  2  zones            NEUTRAL → RUPTURE
Couche  3  nodes            fractal nodes (TRIPLE_CROSS_CLUSTER...)
Couche  4  turning_points   BIRTH / CONFIRMED / WATCH
Couche  5  orchestra        leader / follower / ORCHESTRAL_COMPRESSION
Couche  6  relational       RG legacy (sans filtre P1.2)
Couche  7  fractal          cohérence LTF/MTF/HTF
Couche  8  relational_gravity  RG direct multi-TF (bypass P1.2)
Couche  9  temporal_density   COMPRESSED / ACTIVE / HOLLOW / DEAD
Couche 10  coalition         blocs devises + battlefield windows
Couche 11  tension_signature  ELASTIC_LOADED / DIRECTIONAL_MOVE
```

Query `full_v3` = couches 1-11 simultanément.

---

## 10. RÈGLES ARCHITECTURALES ABSOLUES

```
COUCHE 0 — ACQUISITION
  ❌ capture_bridge.py : NE PAS MODIFIER
  ❌ powerflow.db : NE PAS ÉCRIRE MANUELLEMENT

COUCHE 1 — MOTEUR
  ❌ pf_* ne doit JAMAIS importer cockpit_* / dashboard_* / telegram_*
  ❌ Pas de Telegram dans pf_*
  ✅ Read-only DB uniquement (uri=?mode=ro)
  ✅ Tests py_compile avant tout commit

COUCHE 3 — COCKPIT
  ✅ Lit uniquement — ne modifie pas la logique moteur
  ✅ Un seul dashboard_server actif
  ✅ dashboard_sync_agent = dernier enrichisseur logique

CROSS-COUCHE
  ❌ Pas de dépendances circulaires
  ❌ Pas de BUY/SELL dans aucune couche
  ✅ 1 feature = 1 commit
  ✅ py_compile + pytest avant merge
```

---

## 11. DIAGRAMME SIMPLIFIÉ (LECTURE RAPIDE)

```
MT4  ──TCP──→  capture_bridge  ──INSERT──→  powerflow.db
                                                  │
                              ┌───────────────────┤
                              │                   │
                    [MOTEUR pf_*]         [LAB lab_*]
                    B1 Regime              Exploration
                    B2 Cascade             historique
                    B3 Kalman              queries
                    B4 Density             session
                    B5 Spearman
                    Confluence
                    Node V0.8.2
                    Mapper V7
                              │
                    [RUNNERS run_*]
                    On-demand / Daemon
                    → queues JSON
                              │
                    [COCKPIT cockpit_*]
                    Synthèse / Affichage
                              │
                    [DASHBOARD dashboard_*]
                    Interface live
                              │
                    [TELEGRAM telegram_*]
                    Alertes externes (futur)
                              │
                           TRADER
                        Décision finale
```

---

*Cartographie PowerFlow V7 — 2026-05-09 — Git c579afa*
