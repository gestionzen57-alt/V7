# LEVIER_CONFIG — POWERFLOW TRADER CONTROL

**Date** : 2026-05-06  
**Statut** : CONFIGURATION ACTIVE  
**But** : Activation trader des leviers d'alerte sans restriction IA

---

## 0. PRINCIPE

```text
Chaque levier est une DÉCISION DU TRADER.
Aucun levier n'a de "valeur sûre par défaut".
Aucun levier n'est censuré.
Le trader configure = le trader décide.
```

---

## 1. LEVIERS M1 ULTRARAPIDE

### ENABLE_M1_ULTRAFAST_ALERTS

```python
ENABLE_M1_ULTRAFAST_ALERTS = True  # Activer alertes M1 < 2 min

Si True :
  ✅ FIRST_DETACHMENT_MICRO
  ✅ M1_ANGLE_SHIFT
  ✅ M1_ACCELERATION_SPIKE
  ✅ M1_FORCE_REVERSAL
  ✅ M1_EARLY_PRESSURE_BUILDUP
  ✅ M1_MICROSTRUCTURE_BIRTH

Maturity: exposée (BIRTH, EARLY, CANDIDATE)
Relay: qualifiée (M5_CLEAN, M5_THIN, M5_MISSING)
Risque technique: listés (M1_NOISE, EARLY_MATURITY, etc.)
Pas d'avertissement IA.
Pas de "c'est dangereux".
```

### M1_MINIMUM_CAPTURE_QUALITY

```python
M1_MINIMUM_CAPTURE_QUALITY = "TACTICAL_OK"  # ou "DEGRADED", "BLIND"

Options:
  "FULL_STACK_VISIBLE"  → Toutes les TF disponibles
  "TACTICAL_OK"         → M1-M5-M15 OK (défaut)
  "DEGRADED"            → M1-M5 OK, HTF manquant
  "MINIMAL"             → M1 seulement
  "ACCEPT_ALL"          → Alerter même BLIND

Aucune valeur n'est "sage" ou "prudente".
C'est TOI qui choisis.
```

---

## 2. LEVIERS COUNTER-RELEASE

### ENABLE_COUNTER_RELEASE_EARLY

```python
ENABLE_COUNTER_RELEASE_EARLY = True  # Alerter counter-releases non confirmées

Si True :
  ✅ COUNTER_RELEASE_ATTEMPT
  ✅ COUNTER_RELEASE_BUILDING
  ✅ COUNTER_RELEASE_EARLY_PRESSURE
  ✅ COUNTER_RELEASE_NO_FIRST_DETACHMENT (!)
  ✅ COUNTER_RELEASE_RELAY_ABSENT (!)

Maturity: ATTEMPT < CANDIDATE < CONFIRMED
Relay: peut être MISSING, THIN ou CLEAN
Pas de "attendre la confirmation".
Pas de "c'est trop tôt".
```

### COUNTER_RELEASE_MINIMUM_CONFIDENCE

```python
COUNTER_RELEASE_MINIMUM_CONFIDENCE = "BIRTH"

Options:
  "CONFIRMED"  → Seulement libérations confirmées
  "CANDIDATE"  → Candidates + confirmées
  "ATTEMPT"    → Tentatives (le plus précoce)
  "WATCH"      → Observer les germes (très tôt)

Pas de jugement "c'est assez mature".
C'est TOI qui décides quelle maturité voir.
```

---

## 3. LEVIERS NODES EN GESTATION

### ENABLE_NODE_GESTATION_ALERTS

```python
ENABLE_NODE_GESTATION_ALERTS = True

Si True :
  ✅ NODE_WATCH
  ✅ NODE_BIRTH_CANDIDATE
  ✅ NODE_EARLY_PRESSURE
  ✅ NODE_ANGLE_ALIGNMENT
  ✅ NODE_FORCE_PARTITION_BEGINNING
  ✅ TEMPORAL_NODE_ALERT

Pas d'attente de "node mature".
Gestation visible = gestation alertée.
```

### NODE_GESTATION_DEPTH

```python
NODE_GESTATION_DEPTH = "BIRTH"

Options:
  "CONFIRMED"      → Seulement nodes confirmés
  "CANDIDATE"      → Candidates + confirmés
  "BIRTH"          → Birth + candidates (défaut)
  "WATCH"          → Observation dès les signaux initiaux
  "TEMPORAL_ONLY"  → Seulement temporal nodes

C'est TOI qui décides à quel stade commencer à regarder.
```

---

## 4. LEVIERS HTF NEUTRE / OPPOSÉ

### ENABLE_HTF_NEUTRAL_TACTICAL

```python
ENABLE_HTF_NEUTRAL_TACTICAL = True

Si True :
  ✅ M1_M5_ALIGNED_HTF_NEUTRAL
  ✅ M1_ACTIVE_HTF_QUIET
  ✅ TACTICAL_MICRO_HTF_SLEEPING
  ✅ SHORT_TIMEFRAME_ISOLATED

Pas d'exclusion "parce que HTF ne confirme pas".
Tactique visible = tactique alertée.
```

### ENABLE_HTF_OPPOSED

```python
ENABLE_HTF_OPPOSED = True

Si True :
  ✅ M1_M5_COUNTER_HTF
  ✅ M1_STRONG_HTF_OPPOSED
  ✅ TACTICAL_CONTRADICTION_HTF_GRAVITY
  ✅ MICROSTRUCTURE_ANTIPHASE_HTF

La contradiction n'est pas censurée.
Elle est exposée.
Le trader la voit.
Le trader décide.
```

---

## 5. LEVIERS HAUTE-VARIANCE

### ENABLE_HIGH_VARIANCE_SITUATIONS

```python
ENABLE_HIGH_VARIANCE_SITUATIONS = True

Si True :
  ✅ NEWS_EVENT_M1_REACTION
  ✅ SPREAD_WIDENING_ALERT
  ✅ LIQUIDITY_SPIKE
  ✅ VOLATILITY_CLUSTERING
  ✅ REGIME_SHIFT_MICRO

Pas de "c'est trop volatil, j'arrête".
Variance visible = variance alertée.
```

### HIGH_VARIANCE_MINIMUM_ZSCORE

```python
HIGH_VARIANCE_MINIMUM_ZSCORE = 2.0  # ou 1.5, 2.5, 3.0, etc.

Options:
  3.0   → Seulement extrêmes confirmés
  2.5   → Variance forte
  2.0   → Variance modérée (défaut)
  1.5   → Variance précoce
  1.0   → Accepter même variance légère
  0.5   → Alerter pratiquement tout

C'est un seuil statistique, pas une "sagesse".
Choisis ton niveau.
```

---

## 6. LEVIERS RELAY ABSENT

### ENABLE_RELAY_ABSENT_ALERTS

```python
ENABLE_RELAY_ABSENT_ALERTS = True

Si True :
  ✅ M1_HOT_M5_MISSING
  ✅ M1_DETACHMENT_M5_ABSENT
  ✅ COUNTER_RELEASE_NO_RELAY
  ✅ NODE_BIRTH_NO_M5_CONFIRMATION

Pas de "attendre le relais".
M5 absent = alerte spécifique exposée.
Le trader sait.
```

---

## 7. LEVIERS EARLY PRESSURE

### ENABLE_EARLY_PRESSURE_BUILDUP

```python
ENABLE_EARLY_PRESSURE_BUILDUP = True

Si True :
  ✅ M1_EARLY_PRESSURE_GBP_UP
  ✅ M1_EARLY_PRESSURE_USD_DOWN
  ✅ M1_TENSION_ACCUMULATING
  ✅ COMPRESSION_BEFORE_RELEASE
  ✅ ELASTIC_CHARGING

Pas de "attendre la libération".
Charge visible = charge alertée.
```

---

## 8. LEVIERS AVANCÉS

### ENABLE_MICRO_M1_ONLY_ALERTS

```python
ENABLE_MICRO_M1_ONLY_ALERTS = True

Si True : Alerter même si SEULEMENT M1 qualifie
  ✅ M1_ANGLE_SHIFT_NO_M5
  ✅ M1_FORCE_REVERSAL_ISOLATED
  ✅ M1_MICROSTRUCTURE_UNIQUE

Pas de "il faut une confirmation supérieure".
M1 seul = M1 alerte.
```

### ENABLE_CONTRADICTION_ALERTS

```python
ENABLE_CONTRADICTION_ALERTS = True

Si True : Alerter les contradictions
  ✅ NODE_HEAT_ENERGY_DIVERGENCE
  ✅ RELAY_CLEAN_RELEASE_REJECTED
  ✅ DIRECTION_ALIGNED_LEADER_CONFLICT (RG)
  ✅ M1_STRONG_M5_WEAK
  ✅ FIRST_DETACHMENT_PAIR_ENERGY_ABSENT

Les contradictions ne sont pas censurées.
Elles sont exposées comme WATCH.
```

---

## 9. FICHIER DE CONFIGURATION PYTHON

```python
# powerflow_trader_config.py

class TraderLeverConfig:
    """Configuration des leviers de contrôle trader."""
    
    # M1 Ultrafast
    ENABLE_M1_ULTRAFAST_ALERTS = True
    M1_MINIMUM_CAPTURE_QUALITY = "TACTICAL_OK"
    
    # Counter-Release
    ENABLE_COUNTER_RELEASE_EARLY = True
    COUNTER_RELEASE_MINIMUM_CONFIDENCE = "BIRTH"
    
    # Nodes
    ENABLE_NODE_GESTATION_ALERTS = True
    NODE_GESTATION_DEPTH = "BIRTH"
    
    # HTF Neutral / Opposed
    ENABLE_HTF_NEUTRAL_TACTICAL = True
    ENABLE_HTF_OPPOSED = True
    
    # High Variance
    ENABLE_HIGH_VARIANCE_SITUATIONS = True
    HIGH_VARIANCE_MINIMUM_ZSCORE = 2.0
    
    # Relay Absent
    ENABLE_RELAY_ABSENT_ALERTS = True
    
    # Early Pressure
    ENABLE_EARLY_PRESSURE_BUILDUP = True
    
    # Advanced
    ENABLE_MICRO_M1_ONLY_ALERTS = True
    ENABLE_CONTRADICTION_ALERTS = True
    
    # Meta
    AI_NANNY_MODE = False  # JAMAIS True
    ENFORCE_PRUDENCE = False  # JAMAIS True
    BLOCK_EARLY_ALERTS = False  # JAMAIS True
```

---

## 10. RÈGLES GARDE-FOU

### CE QUE LES LEVIERS FONT

```text
✅ Activent/désactivent des types d'alertes
✅ Changent les seuils techniques
✅ Définissent la maturité minimale
✅ Qualifient la capture/relay
✅ Exposent les contradictions
```

### CE QUE LES LEVIERS NE FONT PAS

```text
❌ Ne jugent jamais
❌ Ne censurent jamais "par prudence"
❌ Ne créent pas d'avertissements
❌ Ne transforment pas en conseil
❌ N'ajoutent pas de morale IA
```

---

## 11. ACTIVATION IMMÉDIATE

### Pour activer les leviers :

```bash
# 1. Copier la classe TraderLeverConfig
cp powerflow_trader_config.py <core>/

# 2. Importer dans pf_behavioral_alert_mapper.py
from powerflow_trader_config import TraderLeverConfig

# 3. Utiliser dans les checkers
if TraderLeverConfig.ENABLE_M1_ULTRAFAST_ALERTS:
    alert = check_m1_ultrafast(...)

# 4. Aucun if "est-ce prudent ?"
# Seulement if "le trader active ?"
```

### Commande test :

```powershell
python -c "
from powerflow_trader_config import TraderLeverConfig
print('M1 Ultrafast:', TraderLeverConfig.ENABLE_M1_ULTRAFAST_ALERTS)
print('Counter-Release:', TraderLeverConfig.ENABLE_COUNTER_RELEASE_EARLY)
print('All levers active')
"
```

---

## 12. DÉCISION FINALE

```text
Chaque levier est une décision.
Chaque décision te revient.
Aucune n'est jugée.
Aucune n'est "plus sûre".
Aucune n'est "rejetée par défaut".

Tu configures.
PowerFlow exécute.
Tu décides.
Tu acceptes.

C'est tout.
```

---

**FIN LEVIER_CONFIG**

À intégrer immédiatement dans CLAUDE.md V2.1.
