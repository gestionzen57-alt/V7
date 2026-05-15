# GRAMMAIRE & LEXIQUE — Mise à jour PowerFlow V6

**Date :** 2026-05-04  
**Objet :** nouveaux concepts issus de la session nodes / séquences / orchestration fractale / agents  
**Statut :** lexique Lab, non figé définitivement

---

## 1. Doctrine centrale

```text
Les forces préviennent.
Le prix confirme.
Le HTF donne la gravité.
Le LTF donne la naissance.
```

```text
Quand le HTF devient évident, la fenêtre tactique LTF peut déjà être fermée.
```

```text
PowerFlow doit voir le node quand les forces basculent,
pas attendre que le prix ait déjà raconté l’histoire.
```

---

# 2. Temporalité fractale

## FRACTAL_TIME_IMBRICATION

**Définition :**  
Imbrication des timeframes où chaque étage temporel a un rôle spécifique.

```text
H4/H1 = gravité / scène large
M30   = champ de bataille / scène active
M15   = relais / confirmation tactique
M5    = timing tactique
M1    = naissance / microfilm / pré-signal
```

**Phrase :**

```text
Le HTF donne la scène, le LTF donne la fenêtre.
```

---

## HTF_GRAVITY_NODE

**Définition :**  
Node visible sur H4/H1/M30 qui porte la gravité de fond.

**Rôle :**

```text
Qualifier le contexte.
Ne pas forcément donner un timing d’entrée.
```

---

## LTF_PRESIGNAL_BIRTH

**Définition :**  
Pré-signal ou naissance observable sur M1/M5/M15 avant que le HTF ne devienne évident.

**Rôle :**

```text
Détecter la fenêtre jeune.
```

---

## MTF_CONFIRMATION_LATE

**Définition :**  
Confirmation sur timeframe moyen alors que la naissance LTF a déjà eu lieu.

**Exemple :**

```text
M30/H1 confirme une scène,
mais M1/M5 ont déjà donné le départ.
```

---

## WINDOW_ALREADY_CLOSING

**Définition :**  
État où la scène HTF reste valide mais où la fenêtre tactique LTF est déjà avancée ou consommée.

**Phrase cockpit future :**

```text
Scène HTF active, mais fenêtre LTF probablement tardive.
```

---

## HTF_NODE_LTF_WINDOW_CLOSED

**Définition :**  
Cas où le node large est visible sur H4/H1 mais les pré-signaux M1/M5/M15 sont déjà passés.

**Lecture :**

```text
Ne pas chercher le départ.
Chercher respiration, second leg ou absorption.
```

---

# 3. Phases de séquence

## PRE_FIELD

Champ préparatoire avant le node.

Signatures :

```text
compression
extension d’un bloc
déséquilibre haut/bas
prix encore suspendu
```

---

## NODE_BIRTH

Naissance du node.

Signatures :

```text
basculement collectif des forces
bloc montant
bloc descendant
prix encore retenu ou pas encore évident
```

---

## CONFIRMATION_PENDING

Phase entre naissance LTF et validation M5/M15.

---

## CONFIRMED

La structure commence à payer.

Signatures :

```text
M5/M15 suit le node
bid commence à payer
bloc dominant persiste
```

---

## COUNTER_BREATH

Respiration contraire.

Signatures :

```text
bloc opposé rebondit
camp dominant relâche
prix répond peu ou temporairement
```

---

## ABSORPTION

La respiration contraire est absorbée.

Signatures :

```text
camp dominant reprend
prix revient dans le sens de la structure
contre-mouvement échoue
```

---

## SECOND_LEG

Deuxième jambe après respiration ou recharge.

---

## WINDOW_CLOSING

Fenêtre de temps tactique qui se ferme.

Signatures :

```text
HTF toujours visible
LTF déjà avancé
prix a déjà payé une partie importante
```

---

# 4. Nodes et patterns

## RAW_NODE_BIRTH

Détection brute depuis la DB sans interprétation complète.

---

## GRAVITY_RESPRING_NODE

Node où USD/CAD ou bloc pivot/gravity reprend depuis une position basse/comprimée.

---

## CAD_JPY_USD_RESPRING_NODE_AGAINST_RISK_BLOCK_FOLD

Pattern observé sur GBPUSD 2026-05-04, 09:23→09:27.

Structure :

```text
CAD+JPY+USD respring
EUR+GBP+CHF/AUD fold
prix encore retenu
confirmation M5 ensuite
```

---

## POWER_ANGLE_ALERT

Alerte d’angle fort avant ou pendant la cassure prix.

Signatures :

```text
devise dominante accélère
angle de force augmente brutalement
bloc opposé se vide
prix proche d’une cassure ou commence à payer
```

---

## FORCE_ANGLE_BREAK

Cassure d’angle dans les forces.

Différence avec node :

```text
NODE_BIRTH = basculement de régime
FORCE_ANGLE_BREAK = accélération directionnelle lisible
```

---

## PRICE_IMPACT_LEG

Jambe où le prix paie brutalement la structure.

---

## POWER_ANGLE_BREAK_TO_PRICE_IMPACT

Pattern visuel observé sur la séquence 12:45→13:45.

Structure :

```text
angle USD/CAD fort
GBP/EUR/AUD drainent
prix casse
respiration ensuite
```

---

## POST_IMPACT_BREATH

Respiration après une jambe d’impact.

---

## POST_IMPACT_FORCE_PERSISTENCE

Les forces dominantes restent orientées après l’impact, même si le prix respire.

Exemple :

```text
CAD/USD restent porteurs
prix stabilise ou rebondit légèrement
```

---

## PRICE_BREATH_AGAINST_FORCE

Le prix respire contre une structure de force encore active.

---

# 5. Mesures cinématiques

## FORCE_VELOCITY

Variation de force par minute.

```text
force_velocity_per_min = force_delta / minutes
```

---

## FORCE_ANGLE_DEG

Angle géométrique approximatif de la force.

```text
angle = atan(force_velocity_per_min)
```

Ce n’est pas un angle pixel du graphique.  
C’est un proxy mathématique.

---

## FORCE_ACCELERATION

Variation de vitesse entre deux segments.

```text
acceleration = velocity_current - velocity_previous
```

---

## FORCE_ENERGY

Somme des variations absolues des devises.

```text
energy = Σ abs(force_delta)
```

---

## PRICE_LAG

Les forces bougent fortement mais le prix répond peu.

---

## PRICE_PAYING

Le prix commence à suivre la structure.

---

## PIP_VELOCITY

Vitesse du prix en pips par minute.

---

# 6. Agents PowerFlow

## DB_FRESHNESS_AGENT

Mission :

```text
vérifier que la DB voit vraiment
contrôler lignes récentes par timeframe
vérifier colonnes EA
détecter trous temporels
```

---

## SEQUENCE_READER

Mission :

```text
lire le film brut
extraire blocs, deltas, energy, nodes, breaths
```

Ne doit pas surinterpréter.

---

## FORCE_KINEMATICS_AGENT

Mission :

```text
mesurer vitesse, angle, accélération, pips/min
```

---

## FRACTAL_ORCHESTRATOR

Mission :

```text
relier HTF et LTF
dire si la fenêtre est jeune, active, tardive ou fermée
```

Questions clés :

```text
Le pré-signal LTF est-il porté par une gravité HTF ?
Le HTF est-il déjà évident mais LTF tardif ?
Chercher départ, respiration, second leg ou absorption ?
```

---

## NODE_INTERPRETER

Mission :

```text
nommer la scène
classer le comportement
transformer les events en langage Flow
```

---

## LAB_MEMORY_AGENT

Mission :

```text
sauver observation trader
créer fiche Lab
capturer vocabulaire nouveau
préparer hypothèse testable
```

---

## MISSION_BUILDER_AGENT

Mission :

```text
transformer un Lab en mission codable
définir fichier cible, objectif, contraintes, tests
réduire les patchs confus
```

---

## COCKPIT_TRANSLATOR

Mission future :

```text
condense les sorties agents en 3 lignes utiles
ne calcule pas
ne décide pas
```

---

# 7. États de fenêtre

## WINDOW_YOUNG

Pré-signal jeune, opportun pour surveillance tactique.

---

## WINDOW_ACTIVE

Scène en cours, confirmation ou impact en développement.

---

## WINDOW_LATE

Signal déjà avancé. Le HTF confirme mais le timing LTF est moins propre.

---

## WINDOW_CLOSED

La fenêtre de départ est consommée.

---

## WATCH_SECOND_LEG

Ne pas chercher la première cassure.  
Surveiller respiration puis deuxième jambe.

---

## WATCH_ABSORPTION

Surveiller si la respiration est absorbée.

---

# 8. Patterns Lab enregistrés

## LAB_004_USD_CAD_JPY_RESPRING_AGAINST_RISK_BLOCK_FOLD

Séquence :

```text
09:00 → 10:15
Node birth 09:23 → 09:27
Confirmation M5 09:35 → 09:45
Counter breath 09:49 → 09:54
Absorption 10:00 → 10:15
```

---

## LAB_005_USD_CAD_ANGLE_BREAK_WITH_GBP_EUR_DRAIN

Séquence :

```text
12:45 → 13:45 visuel
DB fine absente
M30 confirme seulement l’impact large
```

Pattern :

```text
POWER_ANGLE_BREAK_TO_PRICE_IMPACT
```

---

# 9. Règles à retenir

```text
Ne pas confondre respiration contraire et nouveau node principal.
```

```text
Un node principal doit être lu dans son ordre temporel.
```

```text
M1/M5/M15 donnent les pré-signaux.
M30/H1/H4 donnent la scène.
```

```text
Si HTF confirme mais LTF est déjà passé :
chercher second leg / absorption, pas naissance.
```

```text
La DB Freshness est une condition avant toute analyse automatique.
```

---

# 10. Formules cockpit futures

```text
LTF PRE-SIGNAL — microfilm M1/M5 s’aligne sous gravité HTF.
```

```text
HTF NODE DETECTED — fenêtre LTF probablement avancée.
```

```text
POWER ANGLE ALERT — USD/CAD accélèrent, GBP/EUR/AUD drainent.
```

```text
PRICE IMPACT CONFIRMED — M5 paie la cassure.
```

```text
POST IMPACT BREATH — prix respire, forces dominantes encore actives.
```

```text
WINDOW CLOSING — ne pas chercher départ, surveiller absorption/second leg.
```
