# CLAUDE.md V7 — PowerFlow Anticipatoire
**Date : 2026-05-09 | Git : c579afa | Status : PRODUCTION**

---

## 0. DOCTRINE HTF — TA VISION CORRECTE

```
HTF  W/D/H4    = Analyse stratégique / régime / contexte primaire
MTF  H1/30/15  = Fenêtre temporelle / plan / scénario
LTF  15/5/1    = Intervention chirurgicale / ignition / exécution
```

**Anti-nanny** : zéro conseil financier. Risques techniques uniquement.
**Anti-GPT-biais** : zéro censure d'alerte. Trader filtre. Trader décide.

**Hiérarchie** :
```
W       régime lent / mémoire profonde / biais fond
D       cycle / respiration mère / fenêtre supérieure
H4      gravité structurelle / zone de bataille
H1      traducteur intraday H4→M15
M30     fenêtre énergétique / scénario court
M15     battle window / transition MTF-LTF
M5      relais tactique / confirmation
M1      microfilm / ignition / first detachment
```

---

## 1. BRIQUES V7 VALIDÉES

### Core Runtime (NE PAS TOUCHER)
```
capture_bridge.py              ← bridge MT4 live
powerflow.db                   ← mémoire SQLite
pf_temporal_node_state.py      ← 99KB — node engine
pf_behavioral_alert_mapper.py  ← V7 regime_context
```

### Briques V7 Nouvelles
```
B1  pf_regime_engine.py         ✅ HTF_CONTEXT_STACK heuristique
B2  pf_cascade_engine.py        ✅ SEQUENCE_VELOCITY fenêtre 5min
B3  pf_force_kinematics.py      ✅ Kalman Q=0.01 R=0.10
B4  pf_temporal_density.py      ✅ autocorrélation rolling / cycles
B5  pf_spearman_gravity.py      ✅ Spearman rolling toutes paires
```

### Briques V6 Validées (inchangées)
```
P1.2  pf_relational_gravity_bridge.py   ✅ MIXED guard bridge_version=0.1.4
P2    pf_behavioral_alert_mapper.py     ✅ guard-aware
P_NEXT_1  pf_currency_energy_probe.py  ✅ elastic_tension_score
P_NEXT_4  run_confluence_alert.py       ✅ EIE → behavioral_queue
Orchestral  pf_orchestral_gravity_v02.py ✅
Confluence  run_confluence_alert.py     ✅ daemon 5min
Cockpit V7  cockpit_agentic_state_v01.py ✅ regime + cascade
```

---

## 2. ANGLE MORT CRITIQUE RÉSOLU V7

```
AVANT V6 : FIRST_DETACHMENT compression = FIRST_DETACHMENT expansion
           → même alerte, deux réalités opposées

APRÈS V7 : regime_context dans chaque alerte
           FIRST_DETACHMENT + COMPRESSION → HOT
           FIRST_DETACHMENT + RANGE       → WATCH
           FIRST_DETACHMENT + TENDANCE    → INFO
```

---

## 3. CHAÎNE RUNTIME V7

```
force_snapshots (DB read-only)
    ↓
B1  pf_regime_engine.py          HTF_CONTEXT_STACK
    ↓
B3  pf_force_kinematics.py       Kalman angle/speed/noise_ratio
    ↓
    pf_tension_signature.py      elastic signature
    ↓
P1  pf_currency_energy_probe.py  elastic_tension_score
    ↓
    pf_temporal_node_state.py    node V0.8.2
    ↓
B4  pf_temporal_density.py       CYCLE_COMPRESSING
    ↓
B5  pf_spearman_gravity.py       Spearman pairs / MIXED résolu
    ↓
P4  run_confluence_alert.py      EIE → behavioral_queue (append)
    ↓
B2  pf_cascade_engine.py         SEQUENCE_VELOCITY
    ↓
    pf_behavioral_alert_mapper.py  V7 regime_context enrichi
    ↓
    cockpit_agentic_state_v01.py   regime_block + cascade_block
    ↓
    dashboard_sync_agent_v01.py
    ↓
    dashboard_live.html
```

---

## 4. NOUVELLES ALERTES V7

```
REGIME_COMPRESSION_ACTIVE      B1  HOT   HTF en compression
REGIME_TENDANCE_CONFIRMED      B1  INFO  Flux directionnel établi
CASCADE_BUILDING_ALERT         B2  HOT   3+ HOT en 5 min
SEQUENCE_VELOCITY_HIGH         B2  HOT   Cascade en formation
CYCLE_COMPRESSING_ALERT        B4  WATCH Oscillations compriment
CODEPENDANT_EXTREME            B5  WATCH Co-dépendance paire extrême
DIVERGENT_EXTREME              B5  WATCH Opposition structurelle forte
ELASTIC_COMPONENT_ACTIVE       P1  WATCH Tension élastique dans energy
EIE_LEADER_CONFIRMED           P4  HOT   EIE + leader RG confirmé
HTF_CONTEXT_STACK_LIVE         B1  INFO  Contexte HTF disponible
```

---

## 5. LEXIQUE V7 (TERMES NOUVEAUX)

### B1 — Regime Engine
```
HTF_CONTEXT_STACK     W/D/H4/H1 contexte complet en JSON
REGIME_COMPRESSION    Marché serré / explosion possible
REGIME_TENDANCE       Flux directionnel établi
REGIME_RANGE          Pas de flux / consolidation
REGIME_TRANSITION     Changement de régime en cours
regime_confidence     Probabilité du régime (0.0-1.0)
```

### B2 — Cascade Engine
```
SEQUENCE_VELOCITY_HIGH    3+ HOT dans fenêtre 5min
SEQUENCE_VELOCITY_MEDIUM  2 HOT dans fenêtre 5min
SEQUENCE_VELOCITY_LOW     0-1 HOT (normal)
cascade_building          bool — cascade en formation
events_count              nombre événements HOT fenêtre active
```

### B4 — Temporal Density
```
CYCLE_COMPRESSING     Oscillations se compriment → rupture possible
CYCLE_EXPANDING       Oscillations s'allongent → pullback
CYCLE_STABLE          Fréquence stable → range
CYCLE_NOISY           Pas de cycle dominant → transition
compression_ratio     0.0-1.0 (1.0 = compression max)
dominant_period_bars  Période dominante en barres
autocorr_peak         Force du signal autocorrélation
compression_alert     true si 3+ devises simultanément COMPRESSING
FRACTAL_ALIGN_WINDOW  TF60>TF30>TF15 tous en CYCLE_COMPRESSING
```

### B5 — Spearman Gravity
```
SYNCHRO              rho > 0.70 — devises bougent ensemble
DIVERGENT            rho < -0.50 — devises bougent en sens opposé
NEUTRAL              relation faible
CODEPENDANT_EXTREME  rho > 0.85 — co-dépendance aux extrema
DIVERGENT_EXTREME    rho < -0.85 — opposition structurelle forte
MIXED_PROBABILISTE   Relation mixte mesurée par avg_rho (pas heuristique)
spearman_rho         Corrélation de rang -1.0 à +1.0
avg_rho              Moyenne rho multi-TF (résout MIXED)
```

### Confluence Élastique (V6 — rappel)
```
ELASTIC_IN_EXTREME   EIE — zone active + élastique chargé TF1+TF5
EIE_PERSISTANT       EIE sur 2+ snapshots consécutifs (>= 10min)
FRACTALITÉ (0-3)     TF15/30/60 simultanément en zone active
EIE_LEADER_CONFIRMED Devise EIE est leader RG sur TF fiables
```

---

## 6. DB DENSITÉ (2026-05-09)

```
TF1    : 6930 rows — 0 gaps sur 200 derniers → B4 fiable
TF5    : 1382 rows
TF15   :  465 rows
TF30   :  257 rows
TF60   :  133 rows
TF240  :   39 rows — peu de données (B1 HTF moins fiable)
TF1440 :   11 rows — B1 HMM: attendre > 50 rows (~3 semaines)
```

---

## 7. RUNNERS — COMMANDES

```powershell
# B1 Regime
python run_regime_engine_once.py --db powerflow.db --pretty

# B2 Cascade
python run_cascade_engine_once.py

# B4 Temporal Density
python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty

# B5 Spearman
python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty

# Temporal Nodes (V6)
python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 180 --timeframes 1,5,15,30,60 --pretty

# Currency Energy M1/M5/M15
python run_currency_energy_probe_once.py --db powerflow.db --symbol GBPUSD --timeframe 1 --bars 50 --pretty

# Behavioral Mapper
python run_behavioral_alert_mapper_once.py --temporal output\temporal_node_state.json --pretty --summary

# Confluence Alert (daemon)
python run_confluence_alert.py --once --dry-run

# Orchestral Loop
python run_orchestral_loop.py --db powerflow.db --symbol GBPUSD --tfs "1,5,15,30" --once --pretty

# Dashboard refresh
python run_powerflow_dashboard_refresh_once.py --db powerflow.db --symbol GBPUSD --pretty

# Git sync (1 commande)
.\git_sync.ps1 "Message commit"
```

---

## 8. FICHIERS STABLES (NE PAS MODIFIER)

```
capture_bridge.py
powerflow.db
pf_temporal_node_state.py
pf_relational_gravity_bridge.py  (P1.2 validé bridge_version=0.1.4)
cockpit_agentic_state_v01_orchestral.py  V0.1.4 UNIQUEMENT

VERSIONS REJETÉES :
cockpit_agentic_state_v01_orchestral.py V0.1.5+ = NO GO
```

---

## 9. CRITICAL RULES

```
❌ Ne pas modifier capture_bridge.py
❌ Ne pas écrire dans powerflow.db
❌ Ne pas importer cockpit_* dans pf_*
❌ Ne pas créer de dépendances circulaires
❌ Ne pas transformer une alerte en BUY/SELL
❌ cockpit_orchestral V0.1.5+ = NO GO
❌ Ajouter des features avant que les tests passent

✅ Read-only DB (uri=?mode=ro)
✅ Tests d'abord (py_compile + pytest)
✅ 1 feature = 1 commit
✅ Rapport + Checkpoint après chaque mission
✅ git_sync.ps1 après chaque mission
✅ Doctrine anti-nanny : alerter vite, qualifier, pas censurer
```

---

## 10. MISSIONS QUEUE

```
IMMÉDIAT (lundi 12 mai) :
  Valider B4/B5 sur marché ouvert (Asian open 23h CEST)
  Task Scheduler : cycle complet toutes les 5 min

COURT TERME :
  Lab Engine V2 : 6 queries trading (B4+B5+regime nourriront)
  Dashboard V7 : cards B1 + B4 + B5

MOYEN TERME :
  B1 HMM upgrade : quand TF1440 > 50 rows (~3 semaines)
  B4 Wavelet Morlet : si densité TF5 reste propre
  Telegram V7 : alertes regime + cascade (après cockpit stable)
```

---

## 11. ORGANISATION WORKSPACE

```
C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\
├─ Core\              ← CODE ACTIF (source of truth)
├─ PowerFlow_Workspace\00_CURRENT\  ← docs admin
├─ Archive_20260509\  ← 40 fichiers archivés proprement
└─ git_sync.ps1       ← 1 commande = commit + push

Git : https://github.com/gestionzen57-alt/V7.git
Branche : main
Dernier commit : c579afa — V7: B4+B5
```

---

## 12. MÉMOIRE PERSISTANTE — PROTOCOLE

```
DÉBUT SESSION :
  Lire ce CLAUDE.md → contexte complet

FIN SESSION :
  1. Rapport mission (court)
  2. Checkpoint (état concis)
  3. Lexique patch (nouveaux termes)
  4. Mettre à jour CLAUDE.md V7 (section 1 + 10)
  5. .\git_sync.ps1 "Session [date] [mission]"

NB : CLAUDE.md n'est PAS auto-alimenté.
     Mise à jour manuelle obligatoire.
     C'est intentionnel : valider avant d'intégrer.
```

---

## 13. MULTI-IA WORKFLOW

```
Claude (ce fil)   → Chef d'orchestre / architecte / CLAUDE.md
Claude Code       → Exécution / tests / commits
GPT Pro 1         → Algo / infrastructure / cleanup
GPT Pro 2         → ML / automation / docs
Perplexity        → Recherche / validation externe

Après mardi 12 mai :
  GPT Pro → FIN
  Claude Max → Chef d'orchestre unique
```

---

## 14. CHECKPOINTS RÉCENTS

```
2026-05-08  Confluence Élastique V1.0    ✅
2026-05-08  pf_tension_signature.py      ✅
2026-05-08  run_confluence_scan.py       ✅
2026-05-08  pf_confluence_gravity.py     ✅
2026-05-09  B3 Kalman Kinematics         ✅ pf_force_kinematics.py
2026-05-09  B1 Regime Engine             ✅ pf_regime_engine.py
2026-05-09  B2 Sequence Velocity         ✅ pf_cascade_engine.py
2026-05-09  P_NEXT_1 elastic energy      ✅ pf_currency_energy_probe.py
2026-05-09  P_NEXT_4 EIE queue          ✅ run_confluence_alert.py
2026-05-09  Cockpit V7 intégré          ✅ cockpit_agentic_state_v01.py
2026-05-09  B4 Temporal Density         ✅ pf_temporal_density.py
2026-05-09  B5 Spearman Gravity         ✅ pf_spearman_gravity.py
2026-05-09  Git V7 propre               ✅ c579afa main
2026-05-09  Cleanup Core 40 fichiers    ✅ Archive_20260509
2026-05-09  git_sync.ps1                ✅
2026-05-09  CLAUDE.md V7                ✅ ce fichier
```

---

## 15. VERDICT

```
PowerFlow V7 = MOTEUR DE PERCEPTION ANTICIPATOIRE

La machine perçoit maintenant :
  → Dans quel régime HTF (B1 Regime)
  → Comment ça bouge vraiment sans bruit (B3 Kalman)
  → Si les événements s'amplifient (B2 Cascade)
  → Si les cycles se compriment avant rupture (B4 Density)
  → Comment les devises sont vraiment liées (B5 Spearman)
  → Compression élastique multi-TF qualifiée (Confluence EIE)
  → Énergie qualifiée avec tension élastique (P_NEXT_1)

Le trader reçoit une perception contextualisée et qualifiée.
Le trader filtre.
Le trader décide.

Pas de nanny. Pas de BUY/SELL. Pas de conseil.
Perception pure. Transparence technique. Souveraineté trader.
```

---

**END CLAUDE.MD V7**
*Updated 2026-05-09 — Git c579afa — PowerFlow Anticipatoire LIVE*
