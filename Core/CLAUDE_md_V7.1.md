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

### Voir LEXIQUE_GRAMMAIRE_V7_20260509.md pour documentation complète

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
P0 — Tests marché ouvert lundi
  Valider V7.1 sur capture active
  Vérifier DB fraîche via Data Quality Guard
  Vérifier B4 non figé via Market Open Validator
  Vérifier B5 rho fluctuant via Market Open Validator
  Vérifier EIE non statique si tension réelle
  Vérifier Entropy dynamique
  Vérifier Session Overlay correct selon heure/session
  Vérifier Replay sur fenêtre live puis historique
  Vérifier Film Engine sur session réelle

Commandes prioritaires :
  python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-12 --pretty --output .\output\data_quality_guard.json
  python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-12 --recent-minutes 180 --pretty --output .\output\market_open_validator.json
  python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty
  python .\run_session_overlay_once.py --timestamp now --pretty

P1 — Task Scheduler
  Automatiser le cycle complet toutes les 5 minutes
  Ajouter runners V7.1 au cycle
  Écrire les outputs JSON dans output/
  Garder DB strictement read-only
  Ne pas intégrer cockpit avant validation stable

Cycle candidat :
  1. run_data_quality_guard_once.py
  2. run_market_open_validator_once.py
  3. run_entropy_engine_once.py
  4. run_session_overlay_once.py
  5. run_temporal_node_state_once.py
  6. run_currency_energy_probe_once.py
  7. run_confluence_alert.py --once
  8. run_cascade_engine_once.py
  9. run_powerflow_dashboard_refresh_once.py

P2 — Dashboard Cards
  Ajouter Quality Card
    source : output/data_quality_guard.json
    affiche : rows, stale, gaps, status par TF

  Ajouter Market Validator Card
    source : output/market_open_validator.json
    affiche : B4/B5/EIE PASS/FAIL + risques techniques

  Ajouter Entropy Card
    source : output/entropy_engine.json
    affiche : entropy_state / texture / instabilité

  Ajouter Session Overlay Card
    source : output/session_overlay.json
    affiche : session / phase / minutes_since_open / session_bias

  Ajouter Replay / Film Lab access
    source : output/replay_*.json et output/film_*.json
    usage : analyse historique, pas cockpit live obligatoire
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

Documents PowerFlow à importer dans Workspace/00_CURRENT/ :
  • MANIFESTE_FONDATEUR_POWERFLOW_V7.md
  • CARTOGRAPHIE_ARCHITECTURE_V7_20260509.md
  • LEXIQUE_GRAMMAIRE_V7_20260509.md
  • CURRENT_STATE_V7_20260509.md
  • ROADMAP_V7_20260509.md
  • NOMENCLATURE_V7_20260509.md
  • REGISTRE_BRIQUES_V7_20260509.md
  • ONBOARDING_IA_POWERFLOW_V7.md
  • LEVIERS_NATURELS_V7_20260509.md
```

---

## 12. MÉMOIRE PERSISTANTE — PROTOCOLE

```
DÉBUT SESSION :
  Lire ce CLAUDE.md → contexte complet
  Lire ONBOARDING_IA_POWERFLOW_V7.md si nouveau fil
  Lire CURRENT_STATE_V7 → état du jour précis

FIN SESSION :
  1. Rapport mission (court)
  2. Checkpoint (état concis)
  3. Lexique patch (nouveaux termes)
  4. Mettre à jour CLAUDE.md V7 (section 1 + 10 + 14 + version)
  5. .\git_sync.ps1 "Session [date] [mission]"

NB : CLAUDE.md n'est PAS auto-alimenté.
     Mise à jour manuelle obligatoire.
     C'est intentionnel : valider avant d'intégrer.
```

---

## 13. MULTI-IA WORKFLOW

```
Claude (ce fil)   → Chef d'orchestre / architecte / CLAUDE.md / docs
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
2026-05-09  Documentation suite V7      ✅ 9 documents complets
2026-05-09  V7.1 Phase 1 — Infra & Qualité ✅
            pf_data_quality_guard.py
            run_data_quality_guard_once.py
            pf_market_open_validator.py
            run_market_open_validator_once.py
            DB read-only validée
            gaps / stale / no rows / static outputs exposés

2026-05-09  V7.1 Phase 2 — Entropy & Session Overlay ✅
            pf_entropy_engine.py
            run_entropy_engine_once.py
            pf_session_overlay.py
            run_session_overlay_once.py
            Contexte sessionnel disponible
            Texture / désordre du flux mesurable
            Aucun filtrage trading ajouté

2026-05-09  V7.1 Phase 3 — Replay & Film Engine ✅
            pf_replay_engine.py
            lab_replay.py
            pf_film_engine.py
            lab_film.py
            Replay déterministe depuis force_snapshots
            Timeline minute par minute
            Film comportemental historique prêt pour lab

2026-05-09  V7.1 Sprint 7J clôturé ✅
            Code intégré dans Core/
            Python compile OK
            Git push effectué
            Rapport final créé : reports/POWERFLOW_V7_SPRINT_7J_REPORT.md
            Prochaine étape : tests marché ouvert lundi
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

## 16. DOCUMENTATIONS COMPLÉMENTAIRES (2026-05-09)

### Documents Fondateurs
```
MANIFESTE_FONDATEUR_POWERFLOW_V7.md
  → Vision organique du marché
  → Doctrine anti-censure / anti-nanny
  → Contrat PowerFlow-Trader
  → Document de référence qui prime en cas de contradiction
```

### Documents de Référence Technique
```
CARTOGRAPHIE_ARCHITECTURE_V7_20260509.md
  → Vue macro 5 couches (acquisition → cockpit → trader)
  → Chaîne runtime complète avec injection de contexte
  → Inventaire fichiers par couche
  → Matrice dépendances simplifiée
  → Règles architecturales absolues

REGISTRE_BRIQUES_V7_20260509.md
  → B1 à B5 : rôle, statut, dépendances, limitations
  → Confluence Élastique : EIE / gravity bridge / daemon
  → Node Engine : ce qu'il est (ne pas modifier)
  → Behavioral Mapper : leviers actifs V7
  → Cockpit / RG : rôles et frontières

NOMENCLATURE_V7_20260509.md
  → Préfixes fichiers (capture_*, pf_*, run_*, lab_*, cockpit_*, etc.)
  → Convention briques (B1-B5, P1.2, P_NEXT_*)
  → Structure JSON alerte complète avec exemples
  → Énumérations états (zones, régimes, cycles, corrélation, etc.)
  → Anti-patterns commentés (❌ vs ✅)
  → Convention commits Git
```

### Lexique et Langage
```
LEXIQUE_GRAMMAIRE_V7_20260509.md
  → 15 domaines couverts (flux, cinématique, zones, cycles, régimes, gravité, etc.)
  → 80+ termes avec définitions comportementales
  → Termes interdits (GPT-biais à éviter)
  → Nomenclature fichiers cohérente
  → Lexique vivant — mise à jour après chaque nouveau terme validé
```

### Opération et Onboarding
```
CURRENT_STATE_V7_20260509.md
  → État du jour : pipeline actif, densité DB, dates validations
  → Résolution angle mort V7
  → P0/P1/P2/P3 actions immédiates (12 mai Asian open)
  → Règles runtime absolues

ROADMAP_V7_20260509.md
  → P0 : validation marché ouvert (lundi 12 mai 23h CEST)
  → P1 : Task Scheduler cycle 5min
  → P2 : Lab Engine V2 + Dashboard V7 cards
  → Moyen terme : B1 HMM / B4 Wavelet / Multi-Symbol / Session Memory
  → Horizon V8 : architecture future
  → Règles de priorisation naturelle

ONBOARDING_IA_POWERFLOW_V7.md
  → 5 minutes de lecture obligatoire pour tout nouveau fil IA
  → Règles absolues intégrées
  → Doctrine anti-censure obligatoire
  → Commandes rapides de vérification
  → Documents de référence indexés
```

### Vision et Leviers
```
LEVIERS_NATURELS_V7_20260509.md
  → 6 propositions de valeur issues de ta vision organique
  → Pas des features imposées — extensions naturelles
  → Priorisation naturelle : 1. Session Overlay 2. Film 3. Fractal Resonance 4. Volatility 5. Memory 6. Multi-Symbol
  → Chaque levier avec implémentation naturelle et dépendances claires

  Leviers :
  1. Session Memory Overlay — contexte session (Asian/London/NY) dans alertes
  2. Behavioral Journal / Film Engine — rejouer journée comportementale
  3. Fractal Resonance Detection — quand LTF/MTF/HTF vibrent ensemble
  4. Volatility Texture Engine — nature de la volatilité (structurelle/news/friction/bruit)
  5. Memory Engine (B6) — patterns historiques et fréquences d'occurrence
  6. Multi-Symbol Extension — valider GBP sur tous ses crosses vs pairs
```

---

## 17. PROTOCOLE MISE À JOUR CLAUDE.MD

### Début de session
```
1. Lire CLAUDE.md V7 → contexte complet
2. Lire CURRENT_STATE_V7 → état du jour précis
3. Lire ONBOARDING_IA si nouveau fil
4. Valider que tu comprends la doctrine
```

### Fin de session — mise à jour CLAUDE.md
```
1. Ajouter checkpoint dans section 14 (format : YYYY-MM-DD description ✅)
2. Mettre à jour section 10 (missions queue) si état change
3. Mettre à jour section 6 (DB densité) si de nouvelles données
4. Ajouter nouveaux termes dans section 5 (lexique V7)
5. Modifier version / date / Git commit en haut du fichier
6. git_sync.ps1 avec message descriptif
```

### Règle importante
```
CLAUDE.md n'est PAS auto-alimenté.
Mise à jour manuelle obligatoire après chaque mission.
C'est intentionnel : valider avant d'intégrer.
```

---

## 18. ARCHITECTURE DOCUMENTAIRE COMPLÈTE

```
Niveau 1 — VISION ET DOCTRINE
  ├── MANIFESTE_FONDATEUR (ce que PowerFlow est et n'est pas)
  ├── CLAUDE.md V7 (source of truth absolue)
  └── ONBOARDING_IA (protocole démarrage)

Niveau 2 — RÉFÉRENCE TECHNIQUE
  ├── CARTOGRAPHIE_ARCHITECTURE (vue macro)
  ├── REGISTRE_BRIQUES (brique par brique)
  ├── NOMENCLATURE (conventions)
  └── LEXIQUE_GRAMMAIRE (langage PowerFlow)

Niveau 3 — OPÉRATION
  ├── CURRENT_STATE (état du jour)
  ├── ROADMAP (horizon + priorisation)
  └── LEVIERS_NATURELS (propositions valeur)

Niveau 4 — EXÉCUTION
  └── Code + Runners + Tests
```

---

**END CLAUDE.MD V7**
*Updated 2026-05-09 — Git c579afa — PowerFlow Anticipatoire LIVE*

---

**DOCUMENTATION COMPLETE** :
```
9 documents de référence créés le 2026-05-09.
Intégration CLAUDE.md V7 : sections 16, 17, 18 ajoutées.
Tous les documents téléchargeables et prêts pour PowerFlow_Workspace.
```
