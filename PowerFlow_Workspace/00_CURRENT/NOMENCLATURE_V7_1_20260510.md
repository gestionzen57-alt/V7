# NOMENCLATURE — PowerFlow V7.1
**Conventions de nommage, structure et code**
*Date : 2026-05-10 | Version : V7.1 | Statut : PRODUCTION + B1 HMM + B7 Fractal*

---

## 1. PRÉFIXES FICHIERS

| Préfixe | Couche | Rôle | Exemples |
|---------|--------|------|---------|
| `capture_` | 0 — Acquisition | Bridge MT4 / Insertion DB | `capture_bridge.py` |
| `pf_` | 1 — Moteur | Calcul / Analyse / Events | `pf_regime_engine.py` |
| `run_` | 2 — Runners | CLI / Daemons | `run_regime_engine_once.py` |
| `lab_` | Lab | Exploration / Requêtes historiques | `lab_powerflow.py` |
| `cockpit_` | 3 — Cockpit | Synthèse / Lecture | `cockpit_agentic_state_v01.py` |
| `dashboard_` | 3 — Dashboard | Serveur / HTML | `dashboard_server.py` |
| `telegram_` | 4 — Transmission | Alertes Telegram | `telegram_alert_agent.py` |

---

## 2. CONVENTION BRIQUES V7.1

Format : `B{N}` pour les briques majeures.

```
B1  pf_regime_engine.py       HTF context (heuristique)
B1+ pf_hmm_regime.py          HTF context (HMM Gaussian) — NOUVEAU
B2  pf_cascade_engine.py      Sequence velocity
B3  pf_force_kinematics.py    Kalman kinematics
B4  pf_temporal_density.py    Cycle density
B5  pf_spearman_gravity.py    Spearman gravity
B6  [Futur] pf_memory_engine.py      Memory engine (horizon)
B7  pf_fractal_resonance.py   Fractal resonance detection — NOUVEAU
B7+ [Futur] pf_fractal_resonance_v02.py  Timestamp-aligned (horizon)
```

Format : `P{N}.{sous}` pour les patches et bridges.

```
P1.2  pf_relational_gravity_bridge.py   RG bridge guard
P2    pf_behavioral_alert_mapper.py     Alert mapper
P_NEXT_1  pf_currency_energy_probe.py  Energy probe
P_NEXT_4  run_confluence_alert.py      EIE daemon
```

Format : `V{N}` pour les versions V7.1 validation/guards.

```
V7.1  pf_data_quality_guard.py          Data quality monitoring
V7.1  pf_market_open_validator.py       Market open validation
V7.1  pf_entropy_engine.py              Alert entropy detection
V7.1  pf_session_overlay.py             Session context injection
V7.1  pf_replay_engine.py               Deterministic replay
V7.1  pf_film_engine.py                 Behavioral timeline
```

---

## 3. CONVENTION RUNNERS

```
run_{module}_once.py      → exécution unique, CLI, snapshot
run_{module}_loop.py      → boucle continue, daemon
run_{module}_scan.py      → scan historique, batch

Exemples :
  run_regime_engine_once.py
  run_hmm_regime_once.py               (NEW B1 HMM)
  run_confluence_alert.py              (daemon — exception au nommage _loop)
  run_confluence_scan.py
  run_fractal_resonance_once.py        (NEW B7)
  run_data_quality_guard_once.py       (NEW V7.1)
  run_market_open_validator_once.py    (NEW V7.1)
  run_powerflow_cycle_once.py          (NEW — orchestrateur 9 steps)
```

---

## 4. CONVENTION ALERTES

### Type d'alerte
```
CAPS_UNDERSCORE toujours.
Format : {OBJET}_{COMPORTEMENT}_{MODIFICATEUR_OPTIONNEL}

Exemples :
  FIRST_DETACHMENT_MICRO
  CASCADE_BUILDING_ALERT
  REGIME_COMPRESSION_ACTIVE
  CYCLE_COMPRESSING_ALERT
  EIE_LEADER_CONFIRMED
  SEQUENCE_VELOCITY_HIGH
  FRACTAL_RESONANCE_ACTIVE     (NEW B7)
  FRACTAL_LAGGED_WINDOW        (NEW B7)
```

### Niveau d'alerte
```
HOT    → priorité maximale, contexte confirmé
WATCH  → signal présent, contexte partiel
INFO   → information contextuelle
```

### Maturité
```
BIRTH      → naissance — première signature
EARLY      → signal en cours de formation
CANDIDATE  → signal qualifié, non encore confirmé
CONFIRMED  → signal pleinement confirmé
```

### Structure JSON d'une alerte enrichie V7.1
```json
{
  "alert_type": "FIRST_DETACHMENT_MICRO",
  "level": "HOT",
  "maturity": "EARLY",
  "capture_quality": "TACTICAL_OK",
  "relay_quality": "M5_RELAY_CLEAN",
  "regime_context": {
    "regime": "COMPRESSION",
    "confidence": 0.82,
    "method": "hmm_gaussian_standalone",
    "probability_map": {
      "COMPRESSION": 0.82,
      "TENDANCE": 0.15,
      "RANGE": 0.03
    }
  },
  "fractal_resonance_context": {
    "resonance_state": "RESONANT",
    "resonance_score": 0.84,
    "resonant_tfs": [1, 5, 15],
    "avg_signed_correlation": 0.75
  },
  "kinematics": {
    "first_detachment": true,
    "angle_kalman": 0.47,
    "speed_state": "ACCELERATING",
    "noise_ratio": 0.08
  },
  "technical_risks": [
    "EARLY_MATURITY",
    "M1_NOISE_POSSIBLE"
  ],
  "next_watch": [
    "WATCH_M5_RELAY_QUALITY",
    "WATCH_RELEASE_MATURITY",
    "WATCH_FRACTAL_STATE"
  ],
  "timestamp": "2026-05-12T23:14:02+00:00"
}
```

---

## 5. CONVENTION ÉTATS / ENUMS

### Zones
```
NEUTRAL
PRE_EXTREME
EARLY_EXTREME
ACCUMULATING
LEAKING
RUPTURE
```

### Régimes (B1 / B1 HMM)
```
REGIME_COMPRESSION
REGIME_TENDANCE
REGIME_RANGE
REGIME_TRANSITION
```

### Régimes HMM (NEW B1+)
```
COMPRESSION        état caché HMM
TENDANCE           état caché HMM
RANGE              état caché HMM
```

### Cycles (B4)
```
CYCLE_COMPRESSING
CYCLE_EXPANDING
CYCLE_STABLE
CYCLE_NOISY
```

### Corrélation (B5)
```
CODEPENDANT_EXTREME    rho > 0.85
SYNCHRO                rho > 0.70
NEUTRAL                -0.50 ≤ rho ≤ 0.70
DIVERGENT              rho < -0.50
DIVERGENT_EXTREME      rho < -0.85
MIXED_PROBABILISTE     avg_rho faible mais mesurable
```

### Résonance Fractale (NEW B7)
```
RESONANT           rho > 0.80 entre paires adjacentes
LAGGED             rho > 0.60 avec décalages visibles
DISSONANT          rho > 0.30 mais pas cohésion nette
SILENT             rho < 0.30 ou pas vibration positive
INVERSE_RESONANCE  avg_signed_correlation < 0 (paires en contre-phase)
```

### Capture quality
```
FULL_STACK_VISIBLE     Toutes TF disponibles
TACTICAL_OK            M1-M5-M15 OK
DEGRADED               M1-M5 OK, HTF manquant
MINIMAL                M1 seulement
BLIND                  Aucune TF fiable
```

### Relay quality
```
M5_RELAY_CLEAN
M5_THIN
M5_MISSING
```

### Vélocité cascade (B2)
```
SEQUENCE_VELOCITY_HIGH    3+ HOT / 5min
SEQUENCE_VELOCITY_MEDIUM  2 HOT / 5min
SEQUENCE_VELOCITY_LOW     0-1 HOT / 5min
```

### Entropy (NEW V7.1)
```
NORMAL_ALERT_FLOW              pas de saturation
BURST_ACTIVE                   concentration rapide alertes
SATURATED_DUPLICATE_BURST      saturation + doublons massifs
```

### Session (NEW V7.1)
```
ASIAN
LONDON
NY
OVERLAP
DEAD
```

### Session Phase (NEW V7.1)
```
PRE_OPEN
IGNITION
MID_SESSION
CLOSING
```

---

## 6. CONVENTION VERSIONS

Format : `V{MAJOR}.{MINOR}.{PATCH}` ou simplement `V{MAJOR}` pour les versions majeures.

```
V7           → version majeure V7 (legacy)
V7.1         → version majeure V7.1 (production actuelle)
V7.2         → horizon V7.2 (post-P0)

V0.1.4       → version mineure cockpit orchestral
V0.8.2       → version node engine
V1.2         → HMMRegimeV1.2StandaloneSchema (B1 HMM)
V0.1         → B7 Fractal Resonance (bar-tail alignment)
V0.2         → B7 Fractal Resonance (timestamp-aligned) — horizon

bridge_version=0.1.4  → version bridge RG
```

---

## 7. CONVENTION DB

```
Table principale   : force_snapshots
Colonnes clés      : symbol, timeframe, timestamp, {currencies}
Mode d'accès       : READ ONLY via uri=?mode=ro
Insertion          : uniquement via capture_bridge.py

Tables secondaires :
  behavioral_alert_queue  (alertes produites par mapper + daemon)
```

---

## 8. CONVENTION QUEUES JSON

```
output/temporal_node_state.json           → Node output
output/behavioral_alert_queue.json        → Alertes (append only)
output/cockpit_agentic_state_v01.json     → Synthèse cockpit
output/dashboard_data.json                → Dashboard sync
output/fractal_resonance.json             → B7 snapshot
output/hmm_regime_result.json             → B1 HMM snapshot
output/hmm_regime_model.pkl               → B1 HMM model (sérialisé)
output/data_quality_guard.json            → V7.1 quality guard
output/market_open_validator.json         → V7.1 market validator
output/entropy_engine.json                → V7.1 entropy
output/session_overlay.json               → V7.1 session context
output/cycle_report.json                  → Orchestrateur report
output/lab_*.json                         → Lab sessions (non Git)
```

Règle : les fichiers `output/` ne sont pas committés sur Git.
Ils sont des interfaces temporaires entre couches.
Exception : `*.pkl` models (sérialisés) peuvent être versionnés post-décision.

---

## 9. CONVENTION COMMITS GIT

```
Format : "{SCOPE}: {description courte}"

Exemples :
  "V7: B4 temporal density validated"
  "B5: spearman gravity - MIXED resolved"
  "Confluence: EIE daemon V2.0 - P_NEXT_4"
  "B1: HMM Gaussian regime upgrade"           (NEW — 2026-05-10)
  "B7: Fractal Resonance Detection"           (NEW — 2026-05-10)
  "V7.1: add full powerflow cycle orchestrator"
  "Dashboard: add V7.1 live guard cards"
  "Fix: B1 regime confidence threshold"
  "Refactor: pf_kinematics Kalman params"

Règle : 1 feature = 1 commit
        py_compile avant tout commit
        .\git_sync.ps1 "Message" → commit + push automatique
```

---

## 10. COMMANDES VALIDÉES V7.1

### B1 HMM Regime
```powershell
python -m py_compile pf_hmm_regime.py
python run_hmm_regime_once.py --db powerflow.db --train --predict --pretty
python run_hmm_regime_once.py --db powerflow.db --predict --pretty
python -m json.tool ..\output\hmm_regime_result.json | Out-Null
```

### B7 Fractal Resonance
```powershell
python -m py_compile pf_fractal_resonance.py
python run_fractal_resonance_once.py --db powerflow.db --symbol GBPUSD --tfs 1,5,15,30,60 --pretty
python -m json.tool .\output\fractal_resonance.json | Out-Null
```

### V7.1 Guards
```powershell
python run_data_quality_guard_once.py --db powerflow.db --since 2026-05-10 --pretty
python run_market_open_validator_once.py --db powerflow.db --since 2026-05-10 --recent-minutes 180 --pretty
python run_entropy_engine_once.py --db powerflow.db --symbol GBPUSD --pretty
python run_session_overlay_dashboard_once.py --timestamp now --pretty
```

### Orchestrateur
```powershell
python run_powerflow_cycle_once.py --db powerflow.db --symbol GBPUSD
python run_powerflow_cycle_once.py --db powerflow.db --symbol GBPUSD --dry-run
```

---

## 11. ANTI-PATTERNS — CE QU'ON N'ÉCRIT PAS

```python
# ❌ Jugement dans le code
if signal.is_risky():
    return None  # "trop risqué"

# ❌ Filtrage par prudence IA
if confidence < 0.8:
    alert_level = "WATCH"  # forcer WATCH par peur

# ❌ BUY/SELL dans les alertes
alert = {"type": "BUY", "target": 1.2550}

# ❌ Hardcoding non documenté
threshold = 0.65  # pourquoi 0.65 ? mystère

# ❌ Import circulaire
# dans pf_regime_engine.py :
from cockpit_agentic_state_v01 import get_state  # INTERDIT

# ❌ Écriture DB
conn.execute("INSERT INTO force_snapshots ...")  # dans pf_* = INTERDIT

# ❌ HMM qui retient une alerte
if hmm_confidence < 0.60:
    return None  # INTERDIT — qualifie, ne filtre pas

# ❌ B7 qui censure M1 parce que SILENT
if resonance_state == "SILENT":
    skip_alert = True  # INTERDIT — qualifie, ne bloque pas
```

```python
# ✅ Qualification sans jugement
alert = {
    "alert_type": "FIRST_DETACHMENT_MICRO",
    "level": "HOT",
    "maturity": "EARLY",
    "technical_risks": ["M1_NOISE_POSSIBLE"],
    "regime_context": {
        "regime": "COMPRESSION",
        "confidence": 0.82,
        "method": "hmm_gaussian_standalone"
    },
    "fractal_resonance_context": {
        "resonance_state": "SILENT",
        "resonance_score": 0.0,
        "avg_signed_correlation": -0.517481,
        "technical_risks": ["SILENT_HTF", "LAGGED_MULTIPLE_TF"]
    }
}

# ✅ Constante nommée et documentée
COMPRESSION_THRESHOLD = 0.65  # ratio autocorr rolling 20 barres — calibré TF5
HMM_CONFIDENCE_THRESHOLD = 0.60  # seuil qualitatif, non-bloquant
FRACTAL_RESONANCE_THRESHOLD_RESONANT = 0.80  # pour classification

# ✅ Read-only DB
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

# ✅ HMM qualifie sans censure
regime_context = {
    "regime": prediction["regime"],
    "confidence": prediction["confidence"],
    "method": "hmm_gaussian_standalone",
    "probability_map": prediction["probability_map"],
    "technical_risks": technical_risks if technical_risks else None
}
# alerte continue, HMM enrichit seulement

# ✅ B7 qualifie sans filtrer
fractal_context = {
    "resonance_state": resonance_state,
    "resonance_score": resonance_score,
    "avg_signed_correlation": avg_signed_correlation,
    "expected_amplification": expected_amplification,
    "technical_risks": technical_risks
}
# alerte sort, B7 ajoute la dimension fractale
```

---

## 12. CHECKLIST BRIQUES V7.1

| Brique | Moteur | Runner | Statut | Git |
|--------|--------|--------|--------|-----|
| B1 (heuristique) | pf_regime_engine.py | run_regime_engine_once.py | ✅ | V7 |
| B1+ HMM | pf_hmm_regime.py | run_hmm_regime_once.py | ✅ NOUVEAU | e1e175f |
| B2 | pf_cascade_engine.py | run_cascade_engine_once.py | ✅ | V7 |
| B3 | pf_force_kinematics.py | — | ✅ | V7 |
| B4 | pf_temporal_density.py | run_temporal_density_once.py | ✅ | V7 |
| B5 | pf_spearman_gravity.py | run_spearman_gravity_once.py | ✅ | V7 |
| B7 | pf_fractal_resonance.py | run_fractal_resonance_once.py | ✅ NOUVEAU | 8c467c4 |
| V7.1 Quality | pf_data_quality_guard.py | run_data_quality_guard_once.py | ✅ | V7.1 |
| V7.1 Validator | pf_market_open_validator.py | run_market_open_validator_once.py | ✅ | V7.1 |
| V7.1 Entropy | pf_entropy_engine.py | run_entropy_engine_once.py | ✅ | V7.1 |
| V7.1 Session | pf_session_overlay.py | run_session_overlay_dashboard_once.py | ✅ | V7.1 |
| V7.1 Replay | pf_replay_engine.py | — | ✅ | V7.1 |
| V7.1 Film | pf_film_engine.py | — | ✅ | V7.1 |
| Orchestrateur | — | run_powerflow_cycle_once.py | ✅ | V7.1 |

---

## 13. FICHIERS STABLES — NE PAS TOUCHER

```
capture_bridge.py
powerflow.db
pf_temporal_node_state.py              (99KB — stable)
pf_relational_gravity_bridge.py        (bridge_version=0.1.4)
cockpit_agentic_state_v01_orchestral.py (V0.1.4 UNIQUEMENT)
```

---

## 14. MATRICE DÉPENDANCES SIMPLIFIÉE V7.1

```
                          B1  B1+ B2  B3  B4  B5  B7  Node Mapper Cockpit
capture_bridge → DB       -   -   -   -   -   -   -    -     -      -
DB            →           ✓   ✓   -   ✓   ✓   ✓   ✓    ✓     -      -
B1            →           -   -   -   -   -   -   -    -     ✓      ✓
B1+ HMM       →           -   -   -   -   -   -   -    -     ✓      ✓
B2            →           -   -   -   -   -   -   -    -     -      ✓
B3            →           -   -   -   -   -   -   -    ✓     -      -
B4            →           -   -   -   -   -   -   -    -     -      ✓
B5            →           -   -   -   -   -   -   -    -     ✓      ✓
B7            →           -   -   -   -   -   -   -    -     -      ✓
Node          →           -   -   -   -   -   -   -    -     ✓      -
Mapper        → queue     ✓   ✓   ✓   -   -   -   -    -     -      -
RG bridge     →           -   -   -   -   -   -   -    -     -      ✓
Confluence    → queue     -   -   -   -   -   -   -    -     -      ✓
```

---

## 15. RÈGLES ABSOLUES V7.1

### Règles Couche Moteur (pf_*)
```
❌ pf_* ne connaît JAMAIS cockpit_* / dashboard_* / telegram_*
❌ Pas de dépendances circulaires
❌ Pas de BUY/SELL
❌ Pas de censure d'alerte par IA nanny
❌ HMM qualifie, ne filtre pas
❌ B7 qualifie, ne bloque pas
✅ Read-only DB systématique
✅ Tests py_compile avant commit
✅ 1 feature = 1 commit
```

### Règles Architecture
```
✅ M1 n'est jamais censuré "parce que c'est rapide"
✅ Risques techniques seulement, pas de conseil financier
✅ Maturité toujours exposée, jamais cachée
✅ Trader filtre. Machine alerte.
```

---

## 16. CHECKPOINT NOMENCLATURE V7.1

```
2026-05-10 — Nomenclature V7.1 complète
B1 HMM intégrée (pf_hmm_regime.py, run_hmm_regime_once.py)
B7 Fractal intégrée (pf_fractal_resonance.py, run_fractal_resonance_once.py)
V7.1 Guards intégrées (5 nouvelles couches)
Orchestrateur intégré (run_powerflow_cycle_once.py)
Conventions étendues pour HMM, Fractal, Entropy, Session
JSON output enrichis
Commandes validées
Git commits référencés
Architecture stricte maintenue
Doctrine PowerFlow appliquée
```

---

*Nomenclature PowerFlow V7.1 — 2026-05-10 — Référence vivante + B1 HMM + B7 Fractal*
