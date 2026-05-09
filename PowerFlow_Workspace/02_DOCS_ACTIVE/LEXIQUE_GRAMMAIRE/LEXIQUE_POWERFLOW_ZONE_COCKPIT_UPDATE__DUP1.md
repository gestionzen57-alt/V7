# LEXIQUE POWERFLOW — Mise à jour Zone Dynamics / Battlefield / Cockpit

Date : 2026-05-02  
Portée : vocabulaire ajouté ou consolidé pendant la construction de la chaîne Zone → Cockpit.

---

## 1. États de zone

### NEUTRAL

État neutre.  
Aucune tension suffisante ou zone active clairement nommable.

---

### PRE_EXTREME

Zone d’approche d’un extrême.

Définition :

```text
La devise approche une zone haute ou basse significative,
mais n’est pas encore dans une charge mature.
```

Utilité :

```text
pré-zone
préparation
surveillance
```

---

### EARLY_EXTREME

Extrême naissant.

Définition :

```text
La devise est déjà dans une zone extrême ou quasi extrême,
mais la zone n’a pas encore assez de maturité pour être ACCUMULATING.
```

Pourquoi c’est important :

```text
PowerFlow ne noie plus les extrêmes jeunes dans NEUTRAL.
Il voit la naissance du champ.
```

---

### ACCUMULATING

Zone en accumulation.

Définition :

```text
La devise reste dans une zone extrême ou pré-extrême
avec une tension qui se construit dans le temps.
```

Lecture :

```text
énergie stockée
élastique chargé
zone travaillée
```

---

### LEAKING

Fuite de zone.

Définition :

```text
La zone commence à perdre son absorption.
La tension n’est pas encore forcément cassée,
mais l’énergie commence à fuir.
```

Lecture :

```text
première perte de contrôle
pré-rupture
début de libération
```

---

### RUPTURE

Rupture de zone.

Définition :

```text
La zone a libéré ou cassé sa structure précédente.
```

Lecture :

```text
release
cassure comportementale
changement de phase
```

---

## 2. Niveaux de zone

### NORMAL

Zone non extrême.

### PRE_EXTREME

Zone d’approche.

### EXTREME

Zone extrême dynamique.

### POST_ZONE

Après-zone.  
Souvent liée à `LEAKING` ou `RUPTURE`.

---

## 3. Film de zone

### Zone Event

Un diagnostic isolé dans `zone_diagnostics`.

Exemple :

```text
JPY M1 ACCUMULATING EXTREME
```

---

### Zone Sequence

Suite d’événements sur une même devise, même timeframe, même direction.

Exemple :

```text
PRE_EXTREME → ACCUMULATING → PRE_EXTREME → LEAKING → RUPTURE
```

Lecture :

```text
la zone devient un film
```

---

### Zone Evolution Score

Score d’importance d’une séquence de zone.

Il tient compte de :

```text
contexte
tension
durée
états traversés
rupture/fuite
```

---

## 4. Fractal Zone Stack

### FRACTAL_ZONE_STACK

Détection d’une même devise travaillée sur plusieurs timeframes.

Critères :

```text
même devise
même direction HIGH/LOW
proximité ou chevauchement temporel
TF supérieur porteur
TF inférieur relais
```

---

### HTF_ANCHORED_ZONE

Zone portée par un timeframe supérieur.

Exemple :

```text
H1 porte
M30 structure
M15 relaie
```

---

### HTF_ANCHORED_RELEASE_STACK

Stack fractal avec release.

Exemple :

```text
AUD LOW M15/M30/H1
H1 anchor
M30 scenario
M15 trigger
RUPTURE présente
```

---

### SCENARIO_ANCHORED_ZONE

Zone portée par M30/M15.

Lecture :

```text
scénario intermédiaire actif
```

---

### M15_SCENARIO_WITH_M5_RELAY

M15 porte le scénario, M5 relaie tactiquement.

---

### SHORT_FRACTAL_RELEASE

Release courte sur M1/M5.

Lecture :

```text
microfilm + release tactique
```

---

## 5. Sessions

### ASIA_SEED

Asia pose ou porte une tension initiale.

---

### LONDON_OPEN_FORGE

London Open concentre ou travaille la zone.

---

### LONDON_FORGE

London façonne le champ de bataille.

---

### US_RELEASE

US libère ou commence à libérer la tension.

---

### LATE_US_MICROFILM

Late US montre surtout du microfilm M1/M5.

---

### SESSION_CARRIED_TENSION

Tension portée entre plusieurs sessions.

Exemple :

```text
ASIA → LONDON_OPEN
```

---

### FULL_DAY_CARRY

Champ porté sur une grande partie de la journée.

---

### SESSION_RELEASE

Release détectée dans une session.

---

## 6. Brief Cockpit

### STRATEGIC_RELEASE_WINDOW

Fenêtre de release stratégique.

Critères typiques :

```text
plusieurs TF
présence HTF
release / rupture visible
```

---

### ZONE_RELEASE_WINDOW

Fenêtre de release plus tactique.

Souvent :

```text
M1/M5
court terme
microfilm actif
```

---

### HTF_BATTLEFIELD_PREPARATION

Préparation portée par M15/M30/H1.

---

### SCENARIO_BATTLEFIELD

Champ de bataille de scénario, souvent M15/M30.

---

### MICROFILM_BATTLEFIELD

Champ court M1/M5.

Lecture :

```text
naissance
microstructure
release locale
```

---

### LOCAL_ACCUMULATION_FIELD

Accumulation locale sur un seul timeframe.

---

### LOCAL_RELEASE_FIELD

À ajouter bientôt.

Définition proposée :

```text
Une seule TF montre LEAKING ou RUPTURE.
```

Ce label évitera :

```text
LOCAL_ACCUMULATION_FIELD | release
```

---

## 7. Battlefield Map

### BATTLEFIELD_MAP

Carte globale des zones Cockpit.

Elle répond :

```text
qui pousse haut ?
qui travaille bas ?
qui libère ?
qui prépare ?
qui est bipolaire ?
où est la fenêtre contestée ?
```

---

### HIGH_COALITION

Ensemble de devises travaillant côté HIGH dans la même fenêtre.

---

### LOW_COALITION

Ensemble de devises travaillant côté LOW dans la même fenêtre.

---

### TACTICAL_RELEASE_BATTLEFIELD

Champ de release tactique.

Exemple :

```text
CAD HIGH / GBP HIGH release M1/M5
```

---

### HTF_PREPARATION_FIELD

Champ de préparation porté par des timeframes supérieurs.

Exemple :

```text
EUR LOW M15/M30
GBP LOW M15/M30/H1
CAD LOW M30/H1
```

---

### GLOBAL_RELEASE_BATTLEFIELD

Ancien comportement V0.1 qui mélangeait trop HIGH et LOW.

À utiliser avec prudence.  
Préférer maintenant :

```text
cluster-mode side
```

---

### CONTESTED_WINDOW

Fenêtre où une coalition HIGH et une coalition LOW coexistent.

---

### CONTESTED_RELEASE_WINDOW

Fenêtre contestée avec release d’un côté.

---

### BIPOLAR_CONTESTED_RELEASE_WINDOW

Fenêtre contestée où au moins une devise existe en HIGH et LOW.

---

## 8. Bipolar Currency Fields

### BIPOLAR_CURRENCY_FIELD

Une même devise apparaît des deux côtés du champ.

Définition :

```text
la devise a une bataille HIGH
et une bataille LOW
dans la même fenêtre temporelle
```

Ce n’est pas une erreur.  
C’est une contestation interne.

---

### INTERNAL_ROTATION_CONTEST

Conflit interne pouvant préparer une rotation.

---

### MICRO_VS_HTF_ROTATION_CONTEST

Microfilm contre scénario/HTF.

Exemple :

```text
EUR HIGH prep M1/M5
vs
EUR LOW prep M15/M30
```

Lecture :

```text
micro haut contre scène basse
rotation interne potentielle
```

---

### HIGH_RELEASE_VS_LOW_HTF_PREP

Release haute court terme contre préparation basse HTF.

Exemple :

```text
GBP HIGH release M1/M5
vs
GBP LOW prep M15/M30/H1
```

Lecture :

```text
la devise libère haut maintenant,
mais reste travaillée bas sur TF supérieur
```

---

### LOW_RELEASE_VS_HIGH_HTF_PREP

Inverse du précédent.

---

### DOUBLE_SIDE_RELEASE_CONTEST

La devise libère des deux côtés.  
Cas rare, probablement très chaotique ou transitionnel.

---

## 9. Cockpit Field

### COCKPIT FIELD

Vue finale ultra-courte.

Elle affiche :

```text
FIELD
DOMINANT
OPPOSITE/CONTEXT
CONTESTED_WINDOW
BIPOLAR_FOCUS
BIPOLAR_LIST
```

---

### FIELD

Champ dominant actuel.

Exemple :

```text
TACTICAL_RELEASE_BATTLEFIELD | session=LATE_US
```

---

### DOMINANT

Camp dominant ou actif.

Exemple :

```text
release=CAD HIGH/GBP HIGH
prep=EUR HIGH/CHF HIGH/AUD HIGH/JPY HIGH
```

---

### OPPOSITE/CONTEXT

Camp opposé ou contexte supérieur.

Exemple :

```text
EUR LOW/GBP LOW/CHF LOW/CAD LOW/JPY LOW
```

---

### BIPOLAR_FOCUS

Devise bipolaire principale.

Exemple :

```text
EUR | MICRO_VS_HTF_ROTATION_CONTEST
HIGH_TF=M1,M5 vs LOW_TF=M15,M30
```

---

### BIPOLAR_LIST

Résumé compact des devises bipolaires.

Exemple :

```text
EUR:PREPH/PREPL
GBP:RELH/PREPL
CAD:RELH/PREPL
CHF:PREPH/PREPL
```

Signification :

```text
PREPH = préparation HIGH
PREPL = préparation LOW
RELH  = release HIGH
RELL  = release LOW
```

---

## 10. Lecture actuelle validée

Dernier Cockpit Field validé :

```text
FIELD: TACTICAL_RELEASE_BATTLEFIELD | session=LATE_US
DOMINANT: CAD/GBP release HIGH M1/M5
OPPOSITE/CONTEXT: EUR/GBP/CHF/CAD/JPY LOW prep
BIPOLAR_FOCUS: EUR MICRO_VS_HTF_ROTATION_CONTEST
BIPOLAR_LIST: EUR, GBP, CAD, CHF
```

Phrase :

```text
Late US : champ tactique haut actif.
CAD/GBP libèrent haut en M1/M5.
EUR est bipolaire : micro haut contre scénario bas M15/M30.
GBP/CAD sont aussi en release haute contre préparation basse.
Fenêtre contestée ouverte.
```

---

## 11. Termes à surveiller / approfondir

### Fenêtre temporelle

Zone de temps où plusieurs modules convergent :

```text
zone
film
fractal
session
battlefield
bipolaire
```

---

### Champ contesté

Plusieurs forces opposées existent dans la même fenêtre.

---

### Rotation interne

Une devise est tirée par deux lectures opposées :

```text
micro haut
vs
HTF bas
```

ou inversement.

---

### Coalition

Plusieurs devises poussent dans la même direction comportementale.

---

### Release courte

Libération M1/M5.

---

### Release stratégique

Libération avec M15/M30/H1 impliqués.

---

### HTF porteur

Un timeframe supérieur garde la mémoire du champ.

---

## 12. Résumé doctrinal

PowerFlow doit apprendre à dire :

```text
ce n’est pas juste un signal
c’est une scène
dans une session
sur plusieurs timeframes
avec des coalitions
et parfois une devise bipolaire
```

Le Cockpit ne doit pas tout afficher.  
Il doit afficher le champ utile.
