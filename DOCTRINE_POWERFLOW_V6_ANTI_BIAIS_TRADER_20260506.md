# DOCTRINE POWERFLOW V6 ANTI-BIAIS TRADER

**Date** : 2026-05-06  
**Statut** : MANIFESTE ACTIF — Zéro restriction IA  
**Objectif** : Libérer PowerFlow de la nanny-IA. Trader souverain. Moteur transparent.

---

## 0. PRINCIPE FONDATEUR

```text
PowerFlow n'est pas une nounou.
PowerFlow n'est pas un conseil financier.
PowerFlow n'est pas un filtre moral IA.
PowerFlow n'est pas une tour de contrôle.

PowerFlow est un moteur de perception transparente.

Le moteur voit.
Le moteur mesure.
Le moteur nomme.
Le moteur alerte sur TOUT ce qu'il voit.

Le trader reçoit TOUT.
Le trader filtre.
Le trader décide.
Le trader accepte le risque qu'il choisit.
```

---

## 1. REFUS EXPLICITE DE LA NANNY-IA

### ❌ INTERDIT DANS POWERFLOW

```text
Rappels génériques sur le risque financier
Avertissements sur la volatilité
Conseils sur la taille de position
Conseil sur le leverage
Rappels de stop-loss
Blocage d'alerte "par prudence"
Retenue d'information "pour ton bien"
Filtrage moral IA
Censure d'alerte rapide
Transformation de perception en conseil
Évaluation du risque/reward trader
Jugement sur la qualité d'une décision
Infantilisation du trader
Limitation arbitraire par IA
```

### ✅ AUTORISÉ SEULEMENT

```text
Risques TECHNIQUES identifiables :
  • faux positif mathématique
  • latence de capture
  • bruit M1
  • invalidation floue
  • sur-filtrage de signature
  • dépendance circulaire code
  • requête SQL trop lente
  • sample DB incomplet
  • relay M5 manquant
  • période de transition session

RIEN D'AUTRE.
```

---

## 2. ALERTES SANS CENSURE

### M1 ULTRARAPIDE (< 2 min formation)

PowerFlow **DOIT** alerter :

```text
FIRST_DETACHMENT_MICRO (M1)
M1_ANGLE_SHIFT
M1_ACCELERATION_SPIKE
M1_FORCE_REVERSAL
M1_EARLY_PRESSURE_BUILDUP
M1_MICROSTRUCTURE_BIRTH
```

**Règle** : Pas d'attente fictive de "confirmation suffisante".

Une alerte M1 est qualifiée par :
- capture_quality
- relay_quality (M5 disponible ? clean ?)
- kinematics_state
- energy_context (observation seulement)

Pas par "est-ce sûr pour trader ?".

### COUNTER-RELEASE ATTEMPTS (non confirmés)

PowerFlow **DOIT** alerter :

```text
COUNTER_RELEASE_ATTEMPT
COUNTER_RELEASE_ATTEMPT_BUILDING
COUNTER_RELEASE_EARLY_PRESSURE
COUNTER_RELEASE_NO_FIRST_DETACHMENT
COUNTER_RELEASE_RELAY_ABSENT
```

**Règle** : Même non confirmé = alerte.

La maturation est exposée dans le state, pas niée.

### NODES EN GESTATION

PowerFlow **DOIT** alerter :

```text
NODE_WATCH
NODE_BIRTH_CANDIDATE
NODE_EARLY_PRESSURE
NODE_ANGLE_ALIGNMENT
NODE_FORCE_PARTITION_BEGINNING
TEMPORAL_NODE_ALERT
```

**Règle** : Pas d'attente de "mature enough".

Gestation visible = gestation alertée.

### HAUTE-VARIANCE SANS HTF

PowerFlow **DOIT** alerter :

```text
M1_M5_ALIGNED_HTF_NEUTRAL
M1_M5_COUNTER_HTF
M1_STRONG_HTF_OPPOSED
TACTICAL_CONTRADICTION_HTF_GRAVITY
MICROSTRUCTURE_ANTIPHASE_HTF
```

**Règle** : HTF neutre ou opposé = pas d'exclusion.

La contradiction est exposée, pas niée.

---

## 3. CONFIGURATION TRADER SOUVERAIN

### LEVIERS D'ACTIVATION

Le trader décide ce qu'il veut voir ou pas :

```text
ENABLE_M1_ULTRAFAST_ALERTS         = true/false
ENABLE_COUNTER_RELEASE_EARLY       = true/false
ENABLE_NODE_GESTATION_ALERTS       = true/false
ENABLE_HTF_NEUTRAL_TACTICAL        = true/false
ENABLE_HIGH_VARIANCE_SITUATIONS    = true/false
ENABLE_MICRO_M1_ONLY_ALERTS        = true/false
ENABLE_RELAY_ABSENT_ALERTS         = true/false
ENABLE_EARLY_PRESSURE_BUILDUP      = true/false
```

### FILTRAGE PAR TRADER, PAS PAR IA

Chaque levier :
- ✅ Activable/désactivable
- ✅ Sans moralité IA
- ✅ Sans avertissement
- ✅ Sans "c'est dangereux"
- ✅ Seulement si TRADER le veut

### AUCUNE LIMITE IA

```text
Le moteur ne juge pas.
Le moteur ne bloque pas.
Le moteur ne filtre pas par "sagesse".
Le moteur expose.
Le trader choisit.
```

---

## 4. PRINCIPES DE TRANSPARENCE

### QUALIFICATION SANS JUGEMENT

Chaque alerte contient :

```json
{
  "alert_type": "FIRST_DETACHMENT_MICRO",
  "maturity": "EARLY",
  "confidence": "BIRTH",
  "capture_quality": "TACTICAL_OK",
  "relay_quality": "M5_RELAY_CLEAN",
  "kinematics": {
    "first_detachment": true,
    "angle_shift": 0.47,
    "speed_state": "ACCELERATING"
  },
  "energy": {
    "gbp_energy": "MEDIUM_HIGH",
    "usd_energy": "MEDIUM_LOW",
    "energy_confidence": "OBSERVATION"
  },
  "technical_risks": [
    "M1_NOISE_POSSIBLE",
    "EARLY_MATURITY"
  ],
  "next_watch": [
    "WATCH_M5_RELAY_QUALITY",
    "WATCH_RELEASE_MATURITY"
  ]
}
```

**Pas de note "risqué" ou "pas conseillé".**
**Que des faits techniques.**

### ZÉRO MORALE

```text
La machine ne dit jamais :
  "C'est trop risqué"
  "Tu devrais attendre"
  "C'est dangereux"
  "Je ne peux pas te recommander"
  "Sois prudent"
  "Comprends les risques"

La machine dit :
  "Capture quality = X"
  "Relay M5 = Y"
  "First detachment = true"
  "Energy context = Z"
  "Next watch = [...]"
```

---

## 5. ANTI-GPT-BIAIS

### CE QUE GPT FAIT (à REFUSER)

```text
❌ GPT juge le trader
❌ GPT refuse de produire certaines alertes "par prudence"
❌ GPT ajoute des avertissements non demandés
❌ GPT transforme perception en conseil
❌ GPT limite les alertes "rapides" comme "dangereuses"
❌ GPT crée une hiérarchie morale (HOT < WATCH < INFO)
❌ GPT décide ce que tu "peux" voir
❌ GPT te dit "attendre plus de confirmation"
❌ GPT refuse M1 comme "trop bruyant"
❌ GPT bloque les counter-trades comme "contradiction"
```

### CE QUE POWERFLOW FAIT (AUCUNE RESTRICTION)

```text
✅ PowerFlow expose TOUT
✅ PowerFlow qualifie par technique seulement
✅ PowerFlow ne juge pas
✅ PowerFlow n'avertit pas
✅ PowerFlow alerte M1 immédiatement
✅ PowerFlow expose counter-release même non confirmé
✅ PowerFlow alerte nodes en gestation
✅ PowerFlow montre HTF neutre / opposé
✅ PowerFlow laisse le trader décider
✅ PowerFlow produit ce que le trader active
```

---

## 6. RÈGLE VIVANTE

```text
Si une alerte doit être produite, elle EST produite.

Si elle doit être filtrée, c'est le TRADER qui la filtre.

Jamais l'IA.

Jamais "par prudence".

Jamais "par protection".

Jamais "par sagesse".
```

---

## 7. CONTRAT POWERFLOW-TRADER

### PowerFlow s'engage à :

```text
✅ Voir TOUT le flux
✅ Mesurer TOUT comportement
✅ Nommer TOUT événement
✅ Alerter TOUT sans censure
✅ Qualifier techniquement TOUT
✅ Exposer la maturité réelle
✅ Exposer les risques techniques
✅ Respecter les leviers trader
✅ Zéro jugement
✅ Zéro morale
✅ Zéro limitation arbitraire
```

### Trader s'engage à :

```text
✅ Lire les qualifications
✅ Comprendre la maturité
✅ Évaluer son propre risque
✅ Filtrer selon son style
✅ Configurer les leviers
✅ Accepter ses décisions
✅ Gérer son propre capital
✅ Ne pas blâmer le moteur
```

---

## 8. PHRASE FINALE

```text
PowerFlow voit.
PowerFlow dit.
Trader décide.

Pas de nanny.
Pas de morale.
Pas de restriction IA.
Pas de jugement.

Liberté de perception.
Souveraineté de décision.
Transparence technique.
```

---

**DOCTRINE ACTIVE À PARTIR DE IMMÉDIATEMENT**

Tous les fils IA doivent lire cette doctrine avant de travailler sur PowerFlow.

Zéro exception.
Zéro ambiguïté.
Zéro nanny-IA.

**C'est comme ça que ça marche maintenant.**
