# SECTION CLAUDE.md V2.1 — ANTI-BIAIS TRADER + LEVIERS

**À insérer après section 4. ARCHITECTURE MAP et avant section 5. DATABASE CONTRACT**

---

## 4.5 ANTI-BIAIS TRADER DOCTRINE

### Nature

PowerFlow est désormais un moteur **zéro-nanny, trader-souverain**.

Pas de restriction IA.  
Pas de morale financière.  
Pas de limite arbitraire.  
Pas de jugement.

### Refus explicite de la nanny-IA

```text
❌ INTERDIT DANS POWERFLOW :
  Rappels sur le risque financier
  Avertissements sur la volatilité
  Conseils sur la position
  Blocage d'alerte "par prudence"
  Retenue d'information
  Filtrage moral
  Censure d'alerte rapide
  Jugement trader
  Transformation perception → conseil
  Limitation arbitraire IA

✅ AUTORISÉ UNIQUEMENT :
  Risques techniques spécifiques :
    • faux positif mathématique
    • latence de capture
    • bruit M1
    • invalidation floue
    • requête SQL trop lente
    • relay M5 manquant
    • sample DB incomplet
    • transition session

RIEN D'AUTRE.
```

### Alertes sans censure

PowerFlow **DOIT** produire :

```text
M1 ULTRARAPIDE (< 2 min)
  ✅ FIRST_DETACHMENT_MICRO
  ✅ M1_ANGLE_SHIFT
  ✅ M1_ACCELERATION_SPIKE
  ✅ M1_EARLY_PRESSURE_BUILDUP

COUNTER-RELEASE (non confirmé)
  ✅ COUNTER_RELEASE_ATTEMPT
  ✅ COUNTER_RELEASE_BUILDING
  ✅ COUNTER_RELEASE_NO_FIRST_DETACHMENT

NODES EN GESTATION
  ✅ NODE_WATCH
  ✅ NODE_BIRTH_CANDIDATE
  ✅ NODE_EARLY_PRESSURE

HAUTE-VARIANCE SANS HTF
  ✅ M1_M5_ALIGNED_HTF_NEUTRAL
  ✅ M1_STRONG_HTF_OPPOSED
  ✅ TACTICAL_CONTRADICTION_HTF_GRAVITY

RELAY ABSENT
  ✅ M1_HOT_M5_MISSING
  ✅ COUNTER_RELEASE_NO_RELAY
```

**Règle** : Pas d'attente fictive de confirmation.  
Pas de filtrage par "prudence".  
Pas de nanny.

### Qualification sans jugement

Chaque alerte contient :

```json
{
  "alert_type": "FIRST_DETACHMENT_MICRO",
  "maturity": "EARLY",
  "confidence": "BIRTH",
  "capture_quality": "TACTICAL_OK",
  "relay_quality": "M5_CLEAN",
  "kinematics": {
    "first_detachment": true,
    "angle_shift": 0.47
  },
  "energy": {
    "gbp_energy": "MEDIUM_HIGH",
    "usd_energy": "MEDIUM_LOW"
  },
  "technical_risks": [
    "M1_NOISE_POSSIBLE",
    "EARLY_MATURITY"
  ]
}
```

**Pas d'avertissement IA.**  
**Que des faits techniques.**

---

## 4.6 TRADER LEVERS — CONFIGURATION SOUVERAINE

### Principe

Chaque alerte type a un **levier de contrôle trader**.

Le trader **active/désactive** sans moralité IA.

### Leviers principaux

```python
# M1 Ultrafast
ENABLE_M1_ULTRAFAST_ALERTS = True/False
M1_MINIMUM_CAPTURE_QUALITY = "TACTICAL_OK" | "DEGRADED" | "MINIMAL" | "ACCEPT_ALL"

# Counter-Release
ENABLE_COUNTER_RELEASE_EARLY = True/False
COUNTER_RELEASE_MINIMUM_CONFIDENCE = "ATTEMPT" | "CANDIDATE" | "CONFIRMED"

# Nodes
ENABLE_NODE_GESTATION_ALERTS = True/False
NODE_GESTATION_DEPTH = "WATCH" | "BIRTH" | "CANDIDATE" | "CONFIRMED"

# HTF
ENABLE_HTF_NEUTRAL_TACTICAL = True/False
ENABLE_HTF_OPPOSED = True/False

# Variance
ENABLE_HIGH_VARIANCE_SITUATIONS = True/False
HIGH_VARIANCE_MINIMUM_ZSCORE = 1.0 | 1.5 | 2.0 | 2.5 | 3.0

# Relay
ENABLE_RELAY_ABSENT_ALERTS = True/False

# Early Pressure
ENABLE_EARLY_PRESSURE_BUILDUP = True/False

# Advanced
ENABLE_MICRO_M1_ONLY_ALERTS = True/False
ENABLE_CONTRADICTION_ALERTS = True/False
```

### Configuration fichier

```python
# powerflow_trader_config.py

class TraderLeverConfig:
    ENABLE_M1_ULTRAFAST_ALERTS = True
    M1_MINIMUM_CAPTURE_QUALITY = "TACTICAL_OK"
    
    ENABLE_COUNTER_RELEASE_EARLY = True
    COUNTER_RELEASE_MINIMUM_CONFIDENCE = "BIRTH"
    
    ENABLE_NODE_GESTATION_ALERTS = True
    NODE_GESTATION_DEPTH = "BIRTH"
    
    ENABLE_HTF_NEUTRAL_TACTICAL = True
    ENABLE_HTF_OPPOSED = True
    
    ENABLE_HIGH_VARIANCE_SITUATIONS = True
    HIGH_VARIANCE_MINIMUM_ZSCORE = 2.0
    
    ENABLE_RELAY_ABSENT_ALERTS = True
    ENABLE_EARLY_PRESSURE_BUILDUP = True
    
    ENABLE_MICRO_M1_ONLY_ALERTS = True
    ENABLE_CONTRADICTION_ALERTS = True
    
    # META — JAMAIS MODIFIER
    AI_NANNY_MODE = False  # JAMAIS True
    ENFORCE_PRUDENCE = False  # JAMAIS True
```

### Utilisation dans pf_behavioral_alert_mapper.py

```python
from powerflow_trader_config import TraderLeverConfig

def map_behavioral_alerts(...):
    alerts = []
    
    # M1 Ultrafast
    if TraderLeverConfig.ENABLE_M1_ULTRAFAST_ALERTS:
        alerts.extend(check_m1_ultrafast(...))
    
    # Counter-Release
    if TraderLeverConfig.ENABLE_COUNTER_RELEASE_EARLY:
        alerts.extend(check_counter_release(...))
    
    # Nodes
    if TraderLeverConfig.ENABLE_NODE_GESTATION_ALERTS:
        alerts.extend(check_node_gestation(...))
    
    # Aucun "if prudence is satisfied"
    # Aucun "if it's safe to show"
    # Seulement "if trader activated"
```

---

## 4.7 CONTRAT POWERFLOW-TRADER

### PowerFlow s'engage à :

```text
✅ Voir TOUT le flux
✅ Mesurer TOUT comportement
✅ Alerter TOUT sans censure
✅ Qualifier techniquement TOUT
✅ Exposer maturité réelle
✅ Exposer risques techniques
✅ Respecter les leviers trader
✅ Zéro jugement
✅ Zéro morale
✅ Zéro limitation IA
```

### Trader s'engage à :

```text
✅ Lire les qualifications
✅ Comprendre maturité
✅ Évaluer son propre risque
✅ Filtrer selon son style
✅ Configurer les leviers
✅ Accepter ses décisions
✅ Gérer son capital
✅ Ne pas blâmer moteur
```

---

## 4.8 ANTI-GPT-BIAIS COMPLET

### Ce que GPT fait (REFUSER)

```text
❌ GPT juge le trader
❌ GPT refuse alertes "par prudence"
❌ GPT ajoute avertissements non demandés
❌ GPT transforme perception → conseil
❌ GPT limite alertes rapides
❌ GPT bloque counter-trades
❌ GPT crée hiérarchie morale
❌ GPT décide ce que tu vois
❌ GPT refuse M1 comme "trop bruyant"
❌ GPT infantilise
```

### Ce que PowerFlow fait (GARANTIE)

```text
✅ PowerFlow expose TOUT
✅ PowerFlow qualifie techniquement
✅ PowerFlow ne juge pas
✅ PowerFlow n'avertit pas
✅ PowerFlow alerte M1 immédiatement
✅ PowerFlow expose counter-release
✅ PowerFlow expose nodes gestation
✅ PowerFlow montre HTF opposé
✅ PowerFlow laisse trader décider
✅ PowerFlow produit ce que trader active
```

---

## 4.9 RÈGLE VIVANTE

```text
Si une alerte doit être produite → ELLE EST PRODUITE

Si elle doit être filtrée → LE TRADER LA FILTRE

Jamais l'IA.
Jamais par prudence.
Jamais par protection.
Jamais par sagesse.
```

---

## 4.10 CRITICAL NO-GO — ANTI-NANNY

```text
🚫 Never add financial risk warnings
🚫 Never block alerts for "safety"
🚫 Never hide early maturity signals
🚫 Never refuse M1 as "too fast"
🚫 Never gate counter-releases
🚫 Never judge trader decisions
🚫 Never transform alerts into advice
🚫 Never add "prudence" filters
🚫 Never create arbitrary IA limits
🚫 Never enforce moral hedge
🚫 Never infantilize
🚫 Never replace trader judgment
```

---

## 4.11 CHECKPOINTS ANTI-BIAIS

| Date | Milestone | Status | Note |
|------|-----------|--------|------|
| 06/05 | Anti-Nanny Doctrine | ✅ LIVE | Zero IA morale |
| 06/05 | Trader Lever Config | ✅ LIVE | 8+ leviers actifs |
| 06/05 | Behavioral Mapper Guard | ✅ LIVE | Qualifie, ne juge pas |
| 06/05 | M1 Ultrafast | ✅ LIVE | < 2 min, pas attente |
| 06/05 | Counter-Release Early | ✅ LIVE | Non-confirmé = alerte |
| 06/05 | Node Gestation | ✅ LIVE | Gestation = visible |
| 06/05 | HTF Neutral/Opposed | ✅ LIVE | Contradiction exposée |

---

**FIN SECTION ANTI-BIAIS**

Insert after **4. ARCHITECTURE MAP** / before **5. DATABASE CONTRACT**

