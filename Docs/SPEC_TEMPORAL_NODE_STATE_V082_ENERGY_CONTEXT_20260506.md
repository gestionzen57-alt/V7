# SPEC — TEMPORAL NODE STATE V0.8.2 / V0.8.2.1
# energy_context comme bloc observationnel

Date : 2026-05-06
Statut : SPEC ACTIVE — cible de format validée
Source : temporal_node_state_with_energy_context.json

---

## 1. Principe fondateur

```text
Energy != Direction
Energy != Signal
Node Heat != Currency Energy
Counter Release != Release Confirmed
```

Le bloc `energy_context` est **observationnel uniquement**.

Il ne crée pas d'alerte HOT.
Il ne crée pas de direction tradeable.
Il qualifie le `release_state` déjà calculé par `kinematics_state`.
Il alimente le dashboard, le behavioral mapper et le cockpit.
Il ne commande pas Telegram.

---

## 2. Deux nouveaux blocs dans V0.8.2

### 2.1 `energy_release_alignment`

Bloc de calcul intermédiaire.
Produit par `pf_temporal_node_state.py`.
Résultat de la confrontation entre `kinematics_state` et les snapshots energy multi-TF.

```json
{
  "status": "OK",
  "state": "ENERGY_NEUTRAL_OR_TOO_THIN",
  "secondary_state": null,
  "field_quality": "ENERGY_THIN_OR_MIXED",
  "release_state": "COUNTER_RELEASE_ATTEMPT",
  "release_label": "COUNTER_RELEASE_ATTEMPT_DOWN",
  "first_detachment": "M1_FIRST_DETACHMENT_USD_DOWN",
  "first_detachment_detected": true,
  "relay_quality": "CLEAN",
  "relay_sample_state": "M5_RELAY_CLEAN",
  "tf_votes": {
    "M1": "GBP_USD_WEAK_NEUTRAL",
    "M5": "GBP_USD_WEAK_NEUTRAL",
    "M15": "GBP_USD_WEAK_NEUTRAL"
  },
  "relation": "energy qualifies release_state; energy does not create signal",
  "reasons": [
    "M1:GBP/USD weak-or-neutral",
    "M5:GBP/USD weak-or-neutral",
    "M15:GBP/USD weak-or-neutral",
    "counter_release_attempt_energy_qualified"
  ],
  "energy_snapshots": { ... }
}
```

**Champs clés :**

| Champ | Rôle |
|---|---|
| `state` | État d'alignement energy/release (observationnel) |
| `field_quality` | Qualité du champ energy (`ENERGY_THIN_OR_MIXED`, `STRONG`, ...) |
| `release_state` | Release qualifiée par l'energy (copie qualifiée, pas source primaire) |
| `first_detachment_detected` | Booléen — détachement confirmé M1 |
| `relay_quality` | Qualité M5 relay |
| `tf_votes` | Vote par timeframe sur le champ GBP/USD |
| `reasons` | Explications lisibles du calcul |
| `energy_snapshots` | Données brutes energy par TF (M1/M5/M15) pour base/quote |

**Règle :**
```text
energy_release_alignment.release_state qualifie kinematics_state.release_candidate.release_state.
Il ne le remplace pas.
La source de vérité reste kinematics_state.
```

---

### 2.2 `energy_context`

Bloc de synthèse lisible.
Cible : dashboard, behavioral mapper, cockpit.
Mode toujours `OBSERVATION_ONLY`.

```json
{
  "mode": "OBSERVATION_ONLY",
  "source": "energy_release_alignment/build_currency_energy_state",
  "timeframe": 1,
  "top_currency": "JPY",
  "top_energy_label": null,
  "top_energy_score": 0.5832,
  "base_currency": "GBP",
  "base_energy_label": "ENERGY_WEAK",
  "base_energy_score": 0.1061,
  "quote_currency": "USD",
  "quote_energy_label": "ENERGY_WEAK",
  "quote_energy_score": 0.2403,
  "node_energy_relation": "DIVERGENT",
  "alignment_state": "ENERGY_NEUTRAL_OR_TOO_THIN",
  "secondary_state": "COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY",
  "field_quality": "ENERGY_THIN_OR_MIXED",
  "release_state": "COUNTER_RELEASE_ATTEMPT",
  "release_label": "COUNTER_RELEASE_ATTEMPT_DOWN",
  "first_detachment": "M1_FIRST_DETACHMENT_USD_DOWN",
  "tf_votes": { ... },
  "energy_field_summary": "JPY dominant (ENERGY_MEDIUM, ACCUMULATING). Faibles : USD+CHF+GBP+AUD+CAD.",
  "rules": [
    "Energy != Direction",
    "Energy != Signal",
    "Node Heat != Currency Energy",
    "Energy qualifies release_state; energy does not create signal"
  ]
}
```

**Champs clés :**

| Champ | Rôle |
|---|---|
| `mode` | Toujours `OBSERVATION_ONLY` — jamais signal |
| `top_currency` | Devise avec l'énergie la plus haute dans le champ (peut être hors paire) |
| `base_energy_label` / `quote_energy_label` | Labels energy pour base et quote de la paire |
| `node_energy_relation` | Relation observée entre node dominant et energy (`DIVERGENT`, `ALIGNED`, `NEUTRAL`) |
| `alignment_state` | Qualité de l'alignement energy/release |
| `secondary_state` | État secondaire complémentaire (ex: `COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY`) |
| `field_quality` | Qualité globale du champ (`ENERGY_THIN_OR_MIXED`, `STRONG`, `MIXED`) |
| `release_state` | Copie du release_state qualifié (lecture seule depuis energy_release_alignment) |
| `energy_field_summary` | Texte lisible pour dashboard / cockpit |
| `rules` | Rappel des règles métier encodées |

---

## 3. États valides

### `alignment_state`

```text
ENERGY_STRONGLY_ALIGNED      — energy forte dans le sens du node
ENERGY_PARTIALLY_ALIGNED     — energy partielle / un TF seulement
ENERGY_NEUTRAL_OR_TOO_THIN   — energy trop faible pour qualifier
ENERGY_DIVERGENT             — energy contre le node dominant
ENERGY_MIXED                 — signaux contradictoires entre TF
```

### `node_energy_relation`

```text
ALIGNED     — node dominant + energy dans même sens
DIVERGENT   — node dominant + energy dans sens opposé
NEUTRAL     — pas de signal energy suffisant
UNKNOWN     — energy_context absent ou source manquante
```

### `field_quality`

```text
ENERGY_STRONG          — champ fort, au moins un TF dominant clair
ENERGY_THIN_OR_MIXED   — champ faible ou contradictoire
ENERGY_ABSENT          — aucune donnée energy disponible
```

### `secondary_state` (complémentaire)

```text
COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY   — counter release sans support energy
RELEASE_CANDIDATE_ENERGY_ALIGNED        — candidat release + energy supportante
RELEASE_CONFIRMED_ENERGY_STRONG         — release confirmée + champ fort
ENERGY_CONTRADICTS_DETACHMENT           — energy contre le détachement observé
null                                    — pas d'état secondaire notable
```

---

## 4. `tf_votes` — votes par timeframe

Chaque TF vote sur l'état du couple base/quote dans le champ energy.

```text
GBP_UP_STRONG          — GBP forte, USD faible
GBP_USD_BALANCED       — équilibre relatif
GBP_USD_WEAK_NEUTRAL   — les deux faibles ou neutres
USD_UP_STRONG          — USD forte, GBP faible
GBP_DOWN_USD_UP        — bascule observable
THIN_SAMPLE            — données insuffisantes pour voter
```

Règle :
```text
tf_votes ne produit pas de signal.
tf_votes qualifie la cohérence du champ sur plusieurs TF.
3 votes identiques = champ cohérent.
Votes contradictoires = field_quality = ENERGY_THIN_OR_MIXED.
```

---

## 5. `energy_snapshots` — données brutes par TF

Chaque TF dans `energy_snapshots` contient :

```json
{
  "top_energy": {
    "highest": "JPY",
    "highest_score": 0.5832,
    "high_field": [],
    "in_transition": [],
    "weak_field": ["USD", "CHF", "GBP", "AUD", "CAD"]
  },
  "summary": "...",
  "GBP": {
    "score": 0.1061,
    "label": "ENERGY_WEAK",
    "absorption": "NEUTRAL",
    "zone_state": "NEUTRAL",
    "zone_level": "NORMAL",
    "z_extreme_dir": "NONE",
    "behavioral_zscore": 0.9596,
    "speed_per_min": 0.0933,
    "angle_deg": 5.33,
    "acceleration_raw": 0.3516,
    "role": "RISK"
  },
  "USD": { ... }
}
```

Ces données sont **read-only** pour le behavioral mapper et le cockpit.
Elles servent à construire le `film_steps` et le `node_energy_relation`.
Elles ne créent pas de décision.

---

## 6. Règles de lecture pour le Behavioral Alert Mapper

### Ce que `energy_context` permet de qualifier

```text
NODE_HEAT_ENERGY_DIVERGENCE
  → node_energy_relation = DIVERGENT
  → field_quality != ENERGY_ABSENT

COUNTER_RELEASE_ATTEMPT_ALERT
  → release_state = COUNTER_RELEASE_ATTEMPT
  → secondary_state = COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY

RELEASE_REJECTED_NO_DETACHMENT_ALERT
  → first_detachment_detected = false (depuis energy_release_alignment)

M1_ACTIVE_M5_WEAK
  → tf_votes.M5 = GBP_USD_WEAK_NEUTRAL ou THIN_SAMPLE
```

### Ce que `energy_context` ne permet pas

```text
Créer une alerte HOT seule.
Créer une direction de trade.
Remplacer kinematics_state.release_candidate comme source primaire.
Ignorer les reasons_nok de release_candidate.
Transformer COUNTER_RELEASE_ATTEMPT en RELEASE_CONFIRMED.
```

---

## 7. Règles de lecture pour le Cockpit

Le cockpit lit `energy_context` pour enrichir :

```text
behavioral_summary.node_energy_relation
film_steps  → [ENERGY_CONTEXT] bloc
next_watch_enriched → WATCH_ENERGY_ALIGNMENT si DIVERGENT
dashboard_card BEHAVIORAL → energy_field_summary
```

Il **ne modifie pas** :
```text
cockpit_status
headline
agent_summary.next_watch
```

---

## 8. Cible V0.8.2 — mise à jour `pf_temporal_node_state.py`

### Champs à ajouter dans la sortie JSON

```text
energy_release_alignment   (nouveau bloc de calcul)
energy_context             (nouveau bloc de synthèse)
```

### Position dans le JSON

```text
kinematics_state           (existant)
energy_release_alignment   (nouveau — après kinematics_state)
energy_context             (nouveau — dernier bloc)
```

### Inputs requis pour V0.8.2

```text
temporal_node_state (existant)
currency_energy_state.json (optionnel — si absent, energy_context.mode = ENERGY_ABSENT)
```

### Garde-fous obligatoires

```text
Si currency_energy_state absent → energy_context.mode = ENERGY_ABSENT
Si energy scores tous < 0.15 → field_quality = ENERGY_THIN_OR_MIXED
Si tf_votes contradictoires → field_quality = ENERGY_THIN_OR_MIXED
Si first_detachment_detected = false → release_state ne peut pas être RELEASE_CONFIRMED
Si COUNTER_RELEASE_ATTEMPT → secondary_state = COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY
```

---

## 9. Cible V0.8.2.1 — mise à jour `pf_behavioral_alert_mapper.py`

Le mapper lit `energy_context` depuis `temporal_node_state` directement
(en plus de `currency_energy_state` standalone).

### Ordre de priorité pour les données energy

```text
1. temporal_node_state.energy_context   (si présent et mode != ENERGY_ABSENT)
2. currency_energy_state                (standalone, fallback)
3. Aucune donnée energy                 → checkers energy désactivés silencieusement
```

### Checkers à enrichir avec `energy_context`

```text
NODE_HEAT_ENERGY_DIVERGENCE
  source_fields += ["energy_context.node_energy_relation", "energy_context.field_quality"]
  condition enrichie : node_energy_relation = DIVERGENT

COUNTER_RELEASE_ATTEMPT_ALERT
  source_fields += ["energy_context.secondary_state"]
  reason enrichie si secondary_state = COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY

TIGHT_GRAVITY_CLUSTER_ALERT
  source_fields += ["energy_context.field_quality"]
  note dans reason si field_quality = ENERGY_THIN_OR_MIXED
```

### Film steps à enrichir

```text
[ENERGY_CONTEXT] mode | base_label | quote_label | node_energy_relation | field_quality
```

---

## 10. Exemple d'état V0.8.2 validé (données réelles du fichier)

```text
Contexte :
  Nodes actifs : 4 (2x HOT_NODE, 2x NODE_CONFIRMED)
  Dominant direction : GBP pressure down / USD pressure up
  Release state : COUNTER_RELEASE_ATTEMPT (kinematics)
  First detachment : M1_FIRST_DETACHMENT_USD_DOWN (détecté)
  Relay : CLEAN

Energy context :
  GBP energy : ENERGY_WEAK (0.1061)
  USD energy : ENERGY_WEAK (0.2403)
  Top field : JPY (0.5832 — hors paire)
  tf_votes M1/M5/M15 : GBP_USD_WEAK_NEUTRAL sur tous les TF

Lecture correcte :
  node_energy_relation = DIVERGENT
    → node HOT_NODE (GBP down / USD up) mais USD energy = WEAK
    → pas d'énergie supportant la direction USD up
  secondary_state = COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY
    → counter release attempt sans support energy
  field_quality = ENERGY_THIN_OR_MIXED
    → champ trop faible pour qualifier positivement

Alertes behavioral attendues :
  [WATCH]  COUNTER_RELEASE_ATTEMPT_ALERT — non confirmée, non supportée par energy
  [WATCH]  NODE_HEAT_ENERGY_DIVERGENCE   — HOT_NODE mais USD energy WEAK
  [INFO]   TIGHT_GRAVITY_CLUSTER_ALERT  — si cluster présent

Ce qui n'est PAS produit :
  Aucune alerte HOT depuis energy seule
  Aucun signal directionnel
  Aucune confusion COUNTER_RELEASE = RELEASE_CONFIRMED
```

---

## 11. Critère de réussite V0.8.2

```text
✓ energy_release_alignment présent dans le JSON
✓ energy_context présent avec mode = OBSERVATION_ONLY
✓ energy_context.rules encode les 4 règles métier
✓ node_energy_relation calculé correctement
✓ field_quality calculé correctement depuis tf_votes
✓ secondary_state = COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY quand applicable
✓ energy_context absent → mode = ENERGY_ABSENT, pas d'exception
✓ aucune alerte HOT produite par energy seule
✓ aucune confusion release_state
```

## 11. Critère de réussite V0.8.2.1

```text
✓ behavioral mapper lit energy_context depuis tns si présent
✓ fallback vers currency_energy_state standalone si absent
✓ NODE_HEAT_ENERGY_DIVERGENCE utilise node_energy_relation
✓ COUNTER_RELEASE_ATTEMPT_ALERT enrichi par secondary_state
✓ film_steps contient [ENERGY_CONTEXT] bloc
✓ 28/28 tests existants continuent de passer
```

---

## 12. Phrase de reprise

```text
energy_context observe.
kinematics_state décide de la release.
Le trader filtre.
Le trader décide.
```
