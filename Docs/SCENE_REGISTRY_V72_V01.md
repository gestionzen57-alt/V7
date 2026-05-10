# SCENE REGISTRY V0.1 — PowerFlow V7.2

**Date :** 2026-05-10  
**Statut :** Draft fondateur — prêt intégration mémoire B6  
**Objectif :** Définir les scènes comportementales que PowerFlow doit reconnaître, mémoriser et comparer.  
**Doctrine :** La scène est observée, nommée, mémorisée. Elle ne devient jamais un ordre.

---

## 0. Rôle du Scene Registry

Le Scene Registry est la bibliothèque des formes comportementales PowerFlow.

Il sert à dire au moteur :

```text
Voici les scènes que je veux que tu reconnaisses.
Voici les conditions qui les composent.
Voici les outcomes à observer ensuite.
Voici les risques techniques à exposer.
```

Il ne sert pas à dire :

```text
Quand tu vois cette scène, trade.
Quand tu vois cette scène, bloque.
Quand tu vois cette scène, décide.
```

Le trader reste la couche de décision.

```text
La machine perçoit.
La machine nomme.
La machine mémorise.
La machine compare.

Le trader filtre.
Le trader décide.
```

---

## 1. Principe mémoire B6

B6 Memory Engine ne mémorise pas “tout le marché” comme une vidéo complète.

Il mémorise principalement des **événements structurés**.

Une scène PowerFlow doit donc produire une signature exploitable :

```python
pattern_tuple = (
    scene_id,
    regime,
    session,
    eie_state,
    b4_state,
    b5_direction,
)
```

Puis B6 peut créer :

```text
pattern_hash
occurrences
outcome_distribution
median_bars_to_move
sample_size
technical_risks
```

B6 ne prédit pas.  
B6 dit seulement :

```text
Cette scène a déjà été observée N fois.
Voici ce qui a suivi dans l’historique.
Voici les limites techniques de cette mémoire.
```

---

## 2. Doctrine B4 — Compression réelle vs compression fake

B4 seul peut faire des faux positifs.

Une compression cyclique peut être :

```text
une vraie préparation de mouvement
ou
un bruit de session calme
```

La différence apparaît quand B4 est croisé avec B1, B3, B5 et EIE.

### 2.1 Compression réelle qui aboutit

```text
B4  CYCLE_COMPRESSING  ← cycles se serrent
B1  COMPRESSION        ← HTF confirme régime serré
B5  DIVERGENT_EXTREME  ← les devises s’opposent structurellement
EIE actif              ← zone extrême + élastique chargé TF1+TF5

→ le ressort lâche vraiment
```

Lecture PowerFlow :

```text
Compression organique.
Tension accumulée.
Élastique chargé.
Préparation de relâchement.
```

### 2.2 Compression fake

```text
B4  CYCLE_COMPRESSING  ← cycles se serrent
B1  RANGE              ← HTF dit “pas de flux, consolidation”
B5  NEUTRAL            ← devises sans relation claire
EIE absent             ← pas de zone ni élastique

→ bruit de session calme, rien ne suit
```

Lecture PowerFlow :

```text
Compression de surface.
Pas de champ relationnel.
Pas d’élastique.
Pas de zone active.
Risque de faux positif.
```

### 2.3 Rôle B3 Kalman dans les cassures fake

Pour les cassures fakes, B3 Kalman est central.

```text
B4 COMPRESSING + B3 noise_ratio > 0.35
→ WATCH, qualifier
→ oscillations bruitées, pas structurelles
→ risque de fake augmenté
```

```text
B4 COMPRESSING + B3 noise_ratio < 0.10
→ signal propre
→ compression plus crédible
→ attendre EIE / relation B5 / contexte B1
```

### 2.4 Conclusion doctrine

```text
V7 est anticipatoire parce qu’il perçoit la préparation du mouvement,
pas seulement le mouvement.

B4 voit la respiration.
B1 donne le climat.
B3 donne la propreté cinématique.
B5 donne le champ relationnel.
EIE donne l’élastique et la zone.

La scène naît dans le croisement.
```

---

# 3. Les 10 scènes fondatrices

---

## SCENE 01 — FIRST_DETACHMENT_MICRO

### Définition organique

Première séparation propre du flux sur M1.

Le marché commence à se détacher d’un état neutre ou compressé.  
La naissance est encore fragile, mais perceptible.

### Signature comportementale

```text
Un micro-décrochage apparaît avant la confirmation évidente.
Le mouvement n’est pas encore mature.
Mais quelque chose cesse d’être plat.
```

### Conditions observables

```text
B3 angle_kalman change direction
B3 speed_magnitude augmente
B3 noise_ratio bas ou modéré
B1 regime = COMPRESSION ou TRANSITION ou TENDANCE naissante
B4_state = CYCLE_COMPRESSING ou CYCLE_STABLE
EIE_state = PRE_EXTREME ou ELASTIC_IN_EXTREME possible
```

### Pattern tuple mémoire

```python
(
  "FIRST_DETACHMENT_MICRO",
  regime,
  session,
  eie_state,
  b4_state,
  b5_direction
)
```

### Outcomes à suivre

```text
RELEASE_CONFIRMED
NO_FOLLOW_THROUGH
FAKE_DETACHMENT
SECOND_LEG
COUNTER_BREATH
```

### Risques techniques

```text
M1_NOISE_POSSIBLE
EARLY_MATURITY
RELAY_ABSENT
LOW_SAMPLE_SIZE
```

### Règle anti-limitante

Une alerte précoce ne doit pas être censurée.  
Elle doit être qualifiée.

---

## SCENE 02 — PULLBACK_ABSORBED

### Définition organique

Le prix revient vers une zone active, mais la force opposée ne reprend pas vraiment.

La zone absorbe le retour.  
Le flux ne casse pas.  
L’élastique reste chargé.

### Signature comportementale

```text
Retour apparent.
Mais pas de reprise adverse propre.
Le pullback est avalé.
Le flux peut repartir.
```

### Conditions observables

```text
B1 regime = COMPRESSION, TENDANCE ou TRANSITION
B3 speed baisse puis se stabilise
B3 noise_ratio reste contrôlé
B4_state = CYCLE_COMPRESSING ou CYCLE_STABLE
B5_direction = SYNCHRO ou retour DIVERGENT → SYNCHRO
EIE_state = ELASTIC_IN_EXTREME ou PRE_EXTREME
```

### Pattern tuple mémoire

```python
(
  "PULLBACK_ABSORBED",
  regime,
  session,
  eie_state,
  b4_state,
  b5_direction
)
```

### Outcomes à suivre

```text
RELEASE_CONFIRMED
SECOND_LEG
REJECTION
NO_FOLLOW_THROUGH
ABSORPTION_CONTINUED
```

### Risques techniques

```text
PULLBACK_TOO_SHORT
ZONE_CONTEXT_MISSING
B5_RELATION_UNCLEAR
M1_NOISE_POSSIBLE
```

---

## SCENE 03 — ZONE_BREATH_COMPRESSION

### Définition organique

Une zone respire.

Le prix ne part pas immédiatement.  
Les cycles se contractent.  
Le marché accumule de la tension autour d’un node ou d’une zone active.

### Signature comportementale

```text
La zone inspire / expire.
Les oscillations se serrent.
Le mouvement visible est encore faible,
mais la structure se charge.
```

### Conditions observables

```text
B4_state = CYCLE_COMPRESSING
B1 regime = COMPRESSION ou RANGE_TO_COMPRESSION
B3 noise_ratio faible à modéré
B5_direction ≠ NEUTRAL idéalement
EIE_state actif ou en formation
```

### Compression réelle vs fake

Compression réelle :

```text
B4 CYCLE_COMPRESSING
B1 COMPRESSION
B5 DIVERGENT_EXTREME ou SYNCHRO_STRUCTURAL
EIE actif
B3 noise_ratio < 0.20
```

Compression fake :

```text
B4 CYCLE_COMPRESSING
B1 RANGE
B5 NEUTRAL
EIE absent
B3 noise_ratio > 0.35
```

### Pattern tuple mémoire

```python
(
  "ZONE_BREATH_COMPRESSION",
  regime,
  session,
  eie_state,
  b4_state,
  b5_direction
)
```

### Outcomes à suivre

```text
RELEASE_CONFIRMED
COMPRESSION_CONTINUES
FAKE_COMPRESSION
RANGE_STALL
REJECTION
```

### Risques techniques

```text
B4_FALSE_POSITIVE
B3_NOISE_HIGH
EIE_ABSENT
B5_NEUTRAL_FIELD
SESSION_DEAD_ZONE
```

---

## SCENE 04 — COUNTER_BREATH

### Définition organique

Le flux principal respire à contre-sens sans se retourner.

Ce n’est pas encore une inversion.  
C’est une respiration adverse, souvent nécessaire avant second leg ou relâchement.

### Signature comportementale

```text
Contre-mouvement bref.
La force principale ne disparaît pas.
La respiration adverse teste la structure.
```

### Conditions observables

```text
B1 regime = TENDANCE ou COMPRESSION
B3 angle ralentit ou inverse brièvement
B3 speed_magnitude baisse
B4_state = CYCLE_STABLE ou CYCLE_COMPRESSING
B5 leader/follower reste cohérent
EIE_state reste actif ou préservé
```

### Pattern tuple mémoire

```python
(
  "COUNTER_BREATH",
  regime,
  session,
  eie_state,
  b4_state,
  b5_direction
)
```

### Outcomes à suivre

```text
SECOND_LEG
RELEASE_RESUMED
TRUE_REVERSAL
NO_FOLLOW_THROUGH
ABSORPTION
```

### Risques techniques

```text
REVERSAL_CONFUSION
COUNTER_MOVE_TOO_STRONG
B5_LEADER_LOST
NOISE_RATIO_RISING
```

---

## SCENE 05 — SECOND_LEG_BIRTH

### Définition organique

Naissance d’une deuxième jambe après une première impulsion.

Le marché ne fait pas qu’un spike.  
Il tente une continuation structurée.

### Signature comportementale

```text
Première impulsion.
Respiration ou pause.
Nouvelle accélération.
Le flux cherche sa deuxième jambe.
```

### Conditions observables

```text
B3 speed_magnitude repart après pause
B3 angle_kalman reste orienté
B4_state = CYCLE_EXPANDING ou CYCLE_STABLE
B5_direction confirme ou renforce
B1 regime = TENDANCE ou TRANSITION
B7_state = RESONANT ou LAGGED favorable
```

### Pattern tuple mémoire

```python
(
  "SECOND_LEG_BIRTH",
  regime,
  session,
  eie_state,
  b4_state,
  b5_direction
)
```

### Outcomes à suivre

```text
SECOND_LEG_CONFIRMED
FAILED_SECOND_LEG
OVEREXTENSION
COUNTER_BREATH
REJECTION
```

### Risques techniques

```text
FIRST_LEG_EXHAUSTED
B7_DISSONANT
B5_DIVERGENCE_WEAK
LATE_MATURITY
```

---

## SCENE 06 — PRICE_LAG_CATCH_UP

### Définition organique

Le prix est en retard sur le flux, puis rattrape.

Les forces internes bougent avant que le prix ne reflète pleinement la tension.

### Signature comportementale

```text
La force indique une bascule.
Le prix reste lent.
Puis le prix rattrape brusquement.
```

### Conditions observables

```text
B5 relation change avant le prix
B3 angle_kalman ou speed montre pré-accélération
B4_state = CYCLE_COMPRESSING puis EXPANDING
B1 regime = COMPRESSION ou TRANSITION
B7_state = LAGGED possible
```

### Pattern tuple mémoire

```python
(
  "PRICE_LAG_CATCH_UP",
  regime,
  session,
  eie_state,
  b4_state,
  b5_direction
)
```

### Outcomes à suivre

```text
CATCH_UP_CONFIRMED
LAG_PERSISTS
FALSE_LEAD
RELEASE_CONFIRMED
NO_FOLLOW_THROUGH
```

### Risques techniques

```text
PRICE_STILL_LAGGING
LEADER_SIGNAL_WEAK
B7_LAG_TOO_HIGH
B3_NOISE_HIGH
```

---

## SCENE 07 — SPREAD_FRICTION_FIELD

### Définition organique

Le champ devient frictionnel.

Le mouvement visible peut exister, mais il est rugueux, coûteux, instable ou parasité.

### Signature comportementale

```text
Le flux veut bouger.
Mais le terrain accroche.
Les micro-oscillations deviennent heurtées.
```

### Conditions observables

```text
B3 noise_ratio monte
B3 speed instable
B4_state = CYCLE_NOISY ou compression irrégulière
B5_direction instable
session_context = transition, dead zone, ou friction session
B7+ texture = SESSION_FRICTION ou MM_NOISE
```

### Pattern tuple mémoire

```python
(
  "SPREAD_FRICTION_FIELD",
  regime,
  session,
  eie_state,
  b4_state,
  b5_direction
)
```

### Outcomes à suivre

```text
FRICTION_RESOLVES
FAKE_BREAK
NO_FOLLOW_THROUGH
REJECTION
DELAYED_RELEASE
```

### Risques techniques

```text
SPREAD_FRICTION
MM_NOISE
SESSION_FRICTION
B3_NOISE_HIGH
LOW_SIGNAL_CLEANLINESS
```

---

## SCENE 08 — LEADER_FOLLOWER_IMBALANCE

### Définition organique

Une devise ou un symbole mène, l’autre suit avec retard ou faiblesse.

Le champ n’est pas symétrique.

### Signature comportementale

```text
Un leader tire.
Le follower tarde.
Le déséquilibre crée tension ou rattrapage.
```

### Conditions observables

```text
B5_direction = DIVERGENT ou DIVERGENT_EXTREME
B3 angle leader plus propre que follower
B4 compression sur follower possible
B1 regime = TRANSITION ou TENDANCE
B7_state = LAGGED possible
```

### Pattern tuple mémoire

```python
(
  "LEADER_FOLLOWER_IMBALANCE",
  regime,
  session,
  eie_state,
  b4_state,
  b5_direction
)
```

### Outcomes à suivre

```text
FOLLOWER_CATCH_UP
LEADER_EXHAUSTION
DIVERGENCE_CONTINUES
REVERSION
SECOND_LEG
```

### Risques techniques

```text
LEADER_UNCLEAR
FOLLOWER_NOISE
B5_SAMPLE_LOW
B7_LAGGED_CONTEXT
```

---

## SCENE 09 — NODE_BIRTH

### Définition organique

Naissance d’un node temporel ou comportemental.

Le marché commence à organiser plusieurs dimensions autour d’un même point.

### Signature comportementale

```text
Plusieurs briques convergent.
Un point devient attracteur.
La zone commence à avoir une mémoire locale.
```

### Conditions observables

```text
B1 regime stable ou compression
B4_state = CYCLE_COMPRESSING ou CYCLE_STABLE
B5_direction non neutre
B3 speed faible puis accélération légère
EIE_state = PRE_EXTREME ou ELASTIC_IN_EXTREME
B6 commence à retrouver des patterns similaires
```

### Pattern tuple mémoire

```python
(
  "NODE_BIRTH",
  regime,
  session,
  eie_state,
  b4_state,
  b5_direction
)
```

### Outcomes à suivre

```text
NODE_CONFIRMED
RELEASE_FROM_NODE
NODE_REJECTED
RANGE_STALL
COMPRESSION_CONTINUES
```

### Risques techniques

```text
NODE_TOO_EARLY
LOW_CONVERGENCE
B6_NO_HISTORY
EIE_WEAK
```

---

## SCENE 10 — REPULSION_CLEAN

### Définition organique

Répulsion propre depuis une zone ou un état extrême.

Le flux touche, teste, puis est repoussé sans grande friction.

### Signature comportementale

```text
Contact avec zone.
Absorption brève.
Rejet propre.
Cinématique nette.
```

### Conditions observables

```text
EIE_state = ELASTIC_IN_EXTREME
B3 angle_kalman se retourne proprement
B3 noise_ratio faible
B4_state = CYCLE_STABLE ou CYCLE_EXPANDING après compression
B5_direction confirme la répulsion
B1 regime = COMPRESSION, RANGE ou TRANSITION
```

### Pattern tuple mémoire

```python
(
  "REPULSION_CLEAN",
  regime,
  session,
  eie_state,
  b4_state,
  b5_direction
)
```

### Outcomes à suivre

```text
REJECTION_CONFIRMED
SECOND_LEG
FAKE_REPULSION
ZONE_RETEST
NO_FOLLOW_THROUGH
```

### Risques techniques

```text
RETEST_PROBABLE
B5_CONFIRMATION_WEAK
B3_NOISE_RISING
EIE_CONTEXT_LIMITED
```

---

# 4. Outcomes communs V0.1

Les outcomes doivent rester descriptifs.

Ils ne sont pas des décisions de trade.

```text
RELEASE_CONFIRMED
REJECTION
SECOND_LEG
NO_FOLLOW_THROUGH
FAKE_BREAK
FAKE_COMPRESSION
ABSORPTION_CONTINUED
COUNTER_BREATH
CATCH_UP_CONFIRMED
LAG_PERSISTS
NODE_CONFIRMED
NODE_REJECTED
COMPRESSION_CONTINUES
RANGE_STALL
```

---

# 5. Champs recommandés pour chaque événement mémoire

```json
{
  "scene_id": "PULLBACK_ABSORBED",
  "alert_type": "PULLBACK_ABSORBED",
  "symbol": "GBPUSD",
  "timeframe": 1,
  "timestamp": "2026-05-10T09:42:00Z",

  "regime_context": {
    "regime": "COMPRESSION",
    "confidence": 0.82
  },

  "session_context": {
    "session": "LONDON",
    "phase": "OPEN_EXPANSION"
  },

  "EIE_state": "ELASTIC_IN_EXTREME",
  "B4_state": "CYCLE_COMPRESSING",
  "B5_direction": "DIVERGENT_EXTREME",
  "B3_noise_ratio": 0.08,
  "B7_state": "LAGGED",

  "outcome": "RELEASE_CONFIRMED",
  "bars_to_move": 13,

  "technical_risks": [
    "EARLY_MATURITY",
    "LOW_SAMPLE_SIZE"
  ]
}
```

---

# 6. Règles anti-censure

```text
Une scène précoce doit être transmise.
Une scène fragile doit être qualifiée.
Une scène bruyante doit être exposée avec noise_ratio.
Une scène sans historique doit dire NO_HISTORICAL_DATA.
Une scène rare doit dire SMALL_SAMPLE_SIZE.

Aucune scène ne doit être supprimée parce qu’elle est précoce.
Aucune scène ne doit être transformée en ordre.
```

---

# 7. Priorité d’intégration

## Étape 1 — Documentation

Créer ce fichier :

```text
Docs/2026/2026-05/SCENE_REGISTRY_V72_V01.md
```

## Étape 2 — Mémoire B6

Faire évoluer B6 pour lire :

```text
scene_id
B3_noise_ratio
B7_state
outcome
bars_to_move
```

sans casser le pattern tuple 6D existant.

## Étape 3 — Alert Mapper

P2 doit commencer à enrichir les alertes avec :

```text
scene_id
scene_family
scene_confidence_non_blocking
technical_risks
```

## Étape 4 — Dashboard

Afficher dans le dashboard :

```text
Current Scene
Scene Memory
Scene Outcome Distribution
Scene Technical Risks
```

---

# 8. Phrase finale

```text
Le Scene Registry est la grammaire comportementale de PowerFlow.

Il ne décide pas.
Il ne filtre pas.
Il donne à la mémoire des noms pour reconnaître les formes du flux.

Sans scène, B6 stocke des événements.
Avec les scènes, B6 commence à se souvenir du comportement.
```
