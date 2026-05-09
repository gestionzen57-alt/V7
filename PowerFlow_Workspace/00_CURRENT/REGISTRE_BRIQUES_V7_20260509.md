# REGISTRE BRIQUES ET DÉPENDANCES — PowerFlow V7
**Date : 2026-05-09 | Version : V7 | Git : c579afa**

---

## RÈGLE FONDAMENTALE

```
pf_* ne dépend JAMAIS de cockpit_* / dashboard_* / telegram_*
cockpit_* lit pf_* et queues JSON — ne modifie pas la logique moteur
Pas de dépendances circulaires
```

---

## B1 — REGIME ENGINE

```
Fichier    : pf_regime_engine.py
Runner     : run_regime_engine_once.py
Statut     : ✅ V7 VALIDÉ

Rôle :
  Détecte le régime HTF actuel
  Produit HTF_CONTEXT_STACK W/D/H4/H1

Lit :
  force_snapshots (DB read-only)
  TF : 240, 1440, 10080

Produit :
  {
    "regime": "COMPRESSION | TENDANCE | RANGE | TRANSITION",
    "confidence": 0.0-1.0,
    "htf_context_stack": {W, D, H4, H1}
  }

Dépend de :
  db.py (connexion)
  pf_personalities.py (profils devises)

Utilisé par :
  pf_behavioral_alert_mapper.py (injecte regime_context dans alertes)
  pf_confluence_gravity.py (fusion EIE × B1)

Limitations :
  TF1440 : seulement 11 rows — heuristique, pas HMM
  TF240  : 39 rows — résultats partiels
  HMM upgrade quand TF1440 ≥ 50 rows
```

---

## B2 — CASCADE ENGINE

```
Fichier    : pf_cascade_engine.py
Runner     : run_cascade_engine_once.py
Statut     : ✅ V7 VALIDÉ

Rôle :
  Compte les événements HOT dans fenêtre 5min
  Détecte si une séquence s'amplifie

Lit :
  behavioral_alert_queue.json (JSON, pas DB)

Produit :
  {
    "cascade_state": "SEQUENCE_VELOCITY_HIGH | MEDIUM | LOW",
    "events_count": int,
    "cascade_building": bool
  }

Dépend de :
  behavioral_alert_queue.json

Limitations :
  Weekend : events_count=0 (queue vide). Normal.
```

---

## B3 — KALMAN KINEMATICS

```
Fichier    : pf_force_kinematics.py
Statut     : ✅ V7 VALIDÉ

Rôle :
  Remplace fenêtres fixes par filtre Kalman adaptatif
  Angle/speed propres séparant signal du bruit

Paramètres :
  Q = 0.01 (bruit processus — s'adapte aux vrais changements)
  R = 0.10 (bruit mesure — filtre snapshots bruts)

Produit :
  {
    "angle_kalman": float,
    "speed_kalman": float,
    "noise_ratio": float,   # 0=propre, >0.3=bruit
    "first_detachment": bool,
    "same_angle_cluster": [...],
    "tight_gravity_cluster": [...]
  }

Dépend de :
  force_snapshots (DB read-only)

Utilisé par :
  pf_temporal_node_state.py
  pf_currency_energy_probe.py
```

---

## B4 — TEMPORAL DENSITY

```
Fichier    : pf_temporal_density.py
Runner     : run_temporal_density_once.py
Statut     : ✅ V7 VALIDÉ

Rôle :
  Détecte si les oscillations de force se compriment dans le temps
  Autocorrélation rolling
  Pré-signal de rupture avant M1

Produit par devise et TF :
  {
    "cycle_state": "CYCLE_COMPRESSING | EXPANDING | STABLE | NOISY",
    "compression_ratio": 0.0-1.0,
    "dominant_period_bars": int,
    "autocorr_peak": float
  }

Produit global :
  {
    "compression_alert": bool  # true si 3+ devises COMPRESSING
  }

Dépend de :
  force_snapshots (DB read-only)

Limitations :
  Weekend : dominant_period=1 partout (séries statiques). Normal.
  TF30/60 : B4 partiel (peu de données)
```

---

## B5 — SPEARMAN GRAVITY

```
Fichier    : pf_spearman_gravity.py
Runner     : run_spearman_gravity_once.py
Statut     : ✅ V7 VALIDÉ

Rôle :
  Corrélation de rang Spearman rolling toutes paires de devises
  Résout le problème MIXED de RG V6

Produit par paire :
  {
    "pair": "GBP_USD",
    "spearman_rho": float,  # -1.0 à +1.0
    "direction": "SYNCHRO | DIVERGENT | NEUTRAL",
    "tail_signal": "CODEPENDANT_EXTREME | DIVERGENT_EXTREME | MIXED_PROBABILISTE"
  }

Produit multi-TF :
  {
    "avg_rho": float  # résout MIXED heuristique
  }

Dépend de :
  force_snapshots (DB read-only)

Utilisé par :
  pf_confluence_gravity.py (fusion)
  pf_behavioral_alert_mapper.py (context paire)
```

---

## CONFLUENCE ÉLASTIQUE

```
Fichiers   : pf_confluence_elastic.py
             pf_confluence_gravity.py
Runners    : run_confluence_alert.py (daemon 5min)
             run_confluence_scan.py (historique)
Labs       : lab_elastic.py (6 queries)
Statut     : ✅ V7 VALIDÉ

Rôle elastic :
  Zone z-score TF15 + élastique TF1+TF5 + fractalité TF15/30/60
  États : EIE / EWZ / ENZ / ZNE

Rôle gravity :
  Fusionne EIE × B1 × B5 × RG
  Produit fusion_state + confidence

Rôle daemon (P_NEXT_4) :
  Scan 5min
  EIE persistant ≥ 2 snapshots → behavioral_alert_queue.json
  Cooldown 10min par devise

Dépend de :
  force_snapshots (DB read-only)
  pf_relational_gravity_bridge.py
  pf_regime_engine.py (B1)
  pf_spearman_gravity.py (B5)
```

---

## NODE ENGINE

```
Fichier    : pf_temporal_node_state.py
Statut     : ✅ STABLE V0.8.2 — NE PAS MODIFIER (99KB)

Rôle :
  Cœur de l'analyse comportementale
  Produit : capture_quality / relay_quality / release_state
            kinematics_state / energy_context / session_transition

Produit :
  temporal_node_state.json

Dépend de :
  force_snapshots (DB read-only)
  pf_force_kinematics.py (B3)
  pf_currency_energy_probe.py
  pf_personalities.py
  pf_zone_dynamics.py

Utilisé par :
  pf_behavioral_alert_mapper.py
```

---

## BEHAVIORAL ALERT MAPPER

```
Fichier    : pf_behavioral_alert_mapper.py
Runner     : run_behavioral_alert_mapper_once.py
Statut     : ✅ V7 — regime_context enrichi

Rôle :
  Transforme temporal_node_state.json en alertes qualifiées
  Injecte regime_context (B1) dans chaque alerte
  Respecte TraderLeverConfig (8+ leviers)

Lit :
  temporal_node_state.json
  regime_context depuis B1

Produit :
  behavioral_alert_queue.json (append)

Dépend de :
  powerflow_trader_config.py (TraderLeverConfig)
  pf_regime_engine.py (B1)

Leviers actifs :
  ENABLE_M1_ULTRAFAST_ALERTS        = True
  ENABLE_COUNTER_RELEASE_EARLY      = True
  ENABLE_NODE_GESTATION_ALERTS      = True
  ENABLE_HTF_NEUTRAL_TACTICAL       = True
  ENABLE_HTF_OPPOSED                = True
  ENABLE_HIGH_VARIANCE_SITUATIONS   = True
  ENABLE_RELAY_ABSENT_ALERTS        = True
  ENABLE_EARLY_PRESSURE_BUILDUP     = True
  ENABLE_MICRO_M1_ONLY_ALERTS       = True
  ENABLE_CONTRADICTION_ALERTS       = True
  AI_NANNY_MODE = False (JAMAIS True)
```

---

## RELATIONAL GRAVITY

```
Fichiers   : pf_relational_gravity_probe.py
             pf_relational_gravity_bridge.py  (bridge_version=0.1.4)
Runner     : run_relational_gravity_probe_once.py
Statut     : ✅ P1.2 VALIDÉ — NE PAS MODIFIER LE BRIDGE

Rôle :
  Mesure relations entre devises multi-TF
  Leader / follower / antagoniste / coalitions

Problème P1.2 résolu par :
  MIXED guard dans le bridge (topline_reliable / TF_DETAILS)
  B5 Spearman pour mesure probabiliste (avg_rho)

Dépend de :
  force_snapshots (DB read-only)

Ne doit pas :
  Faire de DB read dans cockpit
  Intégrer Telegram direct
```

---

## ORCHESTRAL GRAVITY

```
Fichier    : pf_orchestral_gravity_v02.py
Cockpit    : cockpit_agentic_state_v01_orchestral.py V0.1.4
Runner     : run_orchestral_loop.py
Statut     : ✅ V6 VALIDÉ — V0.1.4 UNIQUEMENT (V0.1.5+ = NO GO)

Rôle :
  Vision multi-devise multi-TF simultanée
  Leader / followers / antagonists / coalitions / crossings
  ORCHESTRAL_COMPRESSION

Produit :
  orchestral_gravity.json (dans cockpit state)
```

---

## COCKPIT

```
Fichier    : cockpit_agentic_state_v01.py
Statut     : ✅ V7 — regime_block + cascade_block

Rôle :
  Synthèse de tous les blocs
  Produit cockpit_agentic_state_v01.json

Lit (sans écrire) :
  temporal_node_state.json
  behavioral_alert_queue.json
  RG bridge
  Orchestral bridge
  B1 regime
  B2 cascade

NE DOIT PAS :
  Calculer la logique moteur
  Modifier behavioral_alert_queue.json
  Importer depuis pf_* directement (via bridges uniquement)
```

---

## DÉPENDANCES COMMUNES (pf_* partagés)

```
db.py                   → connexion SQLite (read-only systématique)
pf_personalities.py     → profils comportementaux devises
pf_zone_dynamics.py     → dynamique des zones
pf_flow_nodes.py        → fractal nodes
powerflow_trader_config.py → TraderLeverConfig (8+ leviers)
```

---

## MATRICE DÉPENDANCES SIMPLIFIÉE

```
                        B1  B2  B3  B4  B5  Node  Mapper  RG  Cockpit
capture_bridge  →  DB   -   -   -   -   -    -      -     -     -
DB              →       ✓   -   ✓   ✓   ✓    ✓      -     ✓     -
B1 (regime)     →       -   -   -   -   -    -      ✓     -     ✓
B2 (cascade)    →       -   -   -   -   -    -      -     -     ✓
B3 (kalman)     →       -   -   -   -   -    ✓      -     -     -
B4 (density)    →       -   -   -   -   -    -      -     -     ✓
B5 (spearman)   →       -   -   -   -   -    -      ✓     -     ✓
Node            →       -   -   -   -   -    -      ✓     -     -
Mapper          →  queue  ✓  -   -   -   -    -      -     -     -
RG bridge       →       -   -   -   -   -    -      -     -     ✓
Confluence      →       -   -   -   -   -    -     queue  -     ✓
```

---

*Registre PowerFlow V7 — 2026-05-09 — Mise à jour après chaque brique*
