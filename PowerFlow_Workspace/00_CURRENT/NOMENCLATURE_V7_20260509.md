# NOMENCLATURE — PowerFlow V7
**Conventions de nommage, structure et code**
*Date : 2026-05-09 | Version : V7*

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

## 2. CONVENTION BRIQUES

Format : `B{N}` pour les briques V7 nouvelles.

```
B1  pf_regime_engine.py       HTF context
B2  pf_cascade_engine.py      Sequence velocity
B3  pf_force_kinematics.py    Kalman kinematics
B4  pf_temporal_density.py    Cycle density
B5  pf_spearman_gravity.py    Spearman gravity
```

Format : `P{N}.{sous}` pour les patches et bridges.

```
P1.2  pf_relational_gravity_bridge.py   RG bridge guard
P2    pf_behavioral_alert_mapper.py     Alert mapper
P_NEXT_1  pf_currency_energy_probe.py  Energy probe
P_NEXT_4  run_confluence_alert.py      EIE daemon
```

---

## 3. CONVENTION RUNNERS

```
run_{module}_once.py      → exécution unique, CLI, snapshot
run_{module}_loop.py      → boucle continue, daemon
run_{module}_scan.py      → scan historique, batch

Exemples :
  run_regime_engine_once.py
  run_confluence_alert.py    (daemon — exception au nommage _loop)
  run_confluence_scan.py
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

### Structure JSON d'une alerte
```json
{
  "alert_type": "FIRST_DETACHMENT_MICRO",
  "level": "HOT",
  "maturity": "EARLY",
  "capture_quality": "TACTICAL_OK",
  "relay_quality": "M5_RELAY_CLEAN",
  "regime_context": {
    "regime": "COMPRESSION",
    "confidence": 0.82
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
    "WATCH_RELEASE_MATURITY"
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

### Régimes
```
REGIME_COMPRESSION
REGIME_TENDANCE
REGIME_RANGE
REGIME_TRANSITION
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

---

## 6. CONVENTION VERSIONS

Format : `V{MAJOR}.{MINOR}.{PATCH}` ou simplement `V{MAJOR}` pour les versions majeures.

```
V7           → version majeure courante
V0.1.4       → version mineure cockpit orchestral
V0.8.2       → version node engine
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
output/temporal_node_state.json        → Node output
output/behavioral_alert_queue.json     → Alertes (append only)
output/cockpit_agentic_state_v01.json  → Synthèse cockpit
output/dashboard_data.json             → Dashboard sync
output/lab_*.json                      → Lab sessions (non Git)
```

Règle : les fichiers `output/` ne sont pas committés sur Git.
Ils sont des interfaces temporaires entre couches.

---

## 9. CONVENTION COMMITS GIT

```
Format : "{SCOPE}: {description courte}"

Exemples :
  "V7: B4 temporal density validated"
  "B5: spearman gravity - MIXED resolved"
  "Confluence: EIE daemon V2.0 - P_NEXT_4"
  "Fix: B1 regime confidence threshold"
  "Refactor: pf_kinematics Kalman params"

Règle : 1 feature = 1 commit
        py_compile avant tout commit
        .\git_sync.ps1 "Message" → commit + push automatique
```

---

## 10. ANTI-PATTERNS — CE QU'ON N'ÉCRIT PAS

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
```

```python
# ✅ Qualification sans jugement
alert = {
    "alert_type": "FIRST_DETACHMENT_MICRO",
    "level": "HOT",
    "maturity": "EARLY",
    "technical_risks": ["M1_NOISE_POSSIBLE"],
    "regime_context": regime_ctx
}

# ✅ Constante nommée et documentée
COMPRESSION_THRESHOLD = 0.65  # ratio autocorr rolling 20 barres — calibré TF5

# ✅ Read-only DB
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
```

---

*Nomenclature PowerFlow V7 — 2026-05-09 — Référence vivante*
