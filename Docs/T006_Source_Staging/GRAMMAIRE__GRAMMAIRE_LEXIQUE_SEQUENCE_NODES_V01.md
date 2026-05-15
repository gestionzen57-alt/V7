# GRAMMAIRE & LEXIQUE — PowerFlow V6 — Nodes, Séquences, Agents

**Date :** 2026-05-04  
**Objet :** Formaliser le vocabulaire issu de l’analyse séquence GBPUSD 2026-05-04  
**But :** Préparer l’automatisation de la lecture de séquences sans coder trop tôt  
**Doctrine :**

```text
PowerFlow doit voir le node quand les forces basculent,
pas attendre que le prix ait déjà raconté l’histoire.
```

---

# 1. Grammaire générale d’une séquence

## PRE_FIELD

**Définition :**  
Champ préparatoire avant la naissance visible d’un node.

**Signatures possibles :**

```text
bloc haut en extension
bloc bas comprimé
devises pivot/refuge en position anormale
prix encore calme ou suspendu
```

**Rôle :**

```text
Préparer le contexte.
Ce n’est pas encore l’alerte principale.
```

**Exemple :**

```text
AUD haut + JPY haut
USD/CAD bas
prix encore élevé
```

---

## NODE_BIRTH

**Définition :**  
Naissance du node. Moment où les forces basculent brutalement de façon collective.

**Règle clé :**

```text
Le node peut naître avant que le prix bouge fortement.
```

**Signatures :**

```text
un bloc monte ensemble
un bloc opposé tombe ensemble
énergie forte
synchronisation courte
prix encore retenu
```

**Exemple :**

```text
CAD+JPY+USD respring
EUR+GBP+CHF fold
bid presque stable
```

---

## CONFIRMATION_LEG

**Définition :**  
Jambe de confirmation après la naissance du node.

**Signatures :**

```text
le même camp continue sur TF supérieur
le prix commence à payer
la synchronisation s’étend de M1 vers M5/M15
```

**Rôle :**

```text
Valider que le node n’était pas seulement un choc microfilm.
```

---

## COUNTER_BREATH

**Définition :**  
Respiration contraire après confirmation.

**Signatures :**

```text
le camp opposé rebondit
le camp dominant relâche
prix rend peu ou temporairement
```

**Règle :**

```text
Une respiration contraire n’invalide pas la structure.
Il faut voir si elle paie en prix.
```

---

## ABSORPTION

**Définition :**  
Moment où une respiration contraire est absorbée.

**Signatures :**

```text
le camp dominant reprend
le prix reprend la direction de la structure
la respiration précédente perd son effet
```

**Rôle :**

```text
Confirmer que la structure principale reste active.
```

---

## STRUCTURE_PAYING

**Définition :**  
Moment où le prix commence à raconter ce que les forces ont déjà montré.

**Phrase Flow :**

```text
Le prix paie la structure.
```

**Important :**

```text
PowerFlow ne doit pas attendre cette phase pour voir la naissance.
```

---

# 2. Lexique des nodes

## RAW_NODE_BIRTH

**Définition :**  
Détection brute d’une naissance de node depuis les données force_snapshots.

**Sans interprétation complète.**

**Exemple :**

```text
UP_BLOCK = CAD+JPY+USD
DOWN_BLOCK = EUR+GBP+CHF
force_energy élevée
bid_delta faible
```

---

## GRAVITY_RESPRING_NODE

**Définition :**  
Node où les devises de gravité/pivot ou assimilées reprennent fortement depuis une position basse ou comprimée.

**Exemple :**

```text
USD+CAD respring
```

**Extension possible :**

```text
JPY rejoint le mouvement comme refuge response.
```

---

## CAD_JPY_USD_RESPRING_NODE_AGAINST_RISK_BLOCK_FOLD

**Définition :**  
Pattern observé sur GBPUSD le 2026-05-04.

**Structure :**

```text
CAD + JPY + USD montent brutalement
EUR + GBP + AUD/CHF se replient
prix encore retenu à la naissance
confirmation M5 ensuite
```

**Famille :**

```text
GRAVITY_RESPRING_NODE
RISK_BLOCK_FOLD
```

---

## PRICE_LAG_AT_NODE_BIRTH

**Définition :**  
Décalage entre l’inversion des forces et le mouvement prix.

**Règle :**

```text
Quand les forces basculent mais que le prix ne bouge pas encore,
PowerFlow doit suspecter une naissance de node.
```

**Utilité :**

```text
Alerter plus tôt.
```

---

## M5_CONFIRMATION_LEG

**Définition :**  
Confirmation d’un node M1 par une poursuite cohérente sur M5.

**Signatures :**

```text
même camp dominant
prix commence à payer
bloc opposé continue de se vider
```

---

## BREATH_ABSORBED

**Définition :**  
Respiration opposée qui ne casse pas la structure.

**Signatures :**

```text
rebond des forces opposées
réponse prix faible
reprise du camp dominant ensuite
```

---

# 3. Lexique des blocs

## UP_BLOCK

**Définition :**  
Groupe de devises qui montent ensemble sur une fenêtre courte.

**Exemple :**

```text
CAD+JPY+USD
```

---

## DOWN_BLOCK

**Définition :**  
Groupe de devises qui tombent ensemble sur une fenêtre courte.

**Exemple :**

```text
EUR+GBP+CHF
```

---

## RISK_BLOCK

**Définition :**  
Bloc composé majoritairement de devises de rôle RISK.

**Exemples :**

```text
EUR+GBP+AUD
EUR+GBP
AUD+GBP
```

---

## REFUGE_BLOCK

**Définition :**  
Bloc composé majoritairement de devises REFUGE.

**Exemples :**

```text
JPY+CHF
```

---

## PIVOT_BLOCK

**Définition :**  
Bloc dominé par des devises pivot ou gravitationnelles.

**Exemples :**

```text
USD+CAD
```

---

## MIXED_GRAVITY_BLOCK

**Définition :**  
Bloc composé de pivot + refuge.

**Exemple :**

```text
USD+CAD+JPY
```

**Lecture :**

```text
Ce bloc peut reprendre le champ contre un bloc risk.
```

---

# 4. Lexique des mouvements

## RESPRING

**Définition :**  
Remontée brusque d’une devise ou d’un bloc depuis une zone basse/comprimée.

**Exemple :**

```text
CAD +18.5 depuis bas
```

---

## FOLD

**Définition :**  
Pliage / vidange d’une devise ou d’un bloc depuis une zone haute ou intermédiaire.

**Exemple :**

```text
EUR -23.2
GBP -20.1
CHF -17.1
```

---

## FORCE_ENERGY

**Définition :**  
Énergie brute d’une fenêtre, souvent approximée par la somme des variations absolues des devises.

**Utilité :**

```text
Repérer les fenêtres où quelque chose se passe vraiment.
```

---

## SYNC_RESPRING

**Définition :**  
Plusieurs devises remontent ensemble sur une fenêtre courte.

**Exemple :**

```text
CAD+JPY+USD montent ensemble.
```

---

## SYNC_FOLD

**Définition :**  
Plusieurs devises tombent ensemble sur une fenêtre courte.

**Exemple :**

```text
EUR+GBP+CHF tombent ensemble.
```

---

## OPPOSITE_BLOCK_ROTATION

**Définition :**  
Rotation simultanée entre un bloc montant et un bloc descendant.

**Phrase :**

```text
Un camp reprend le champ pendant que l’autre se vide.
```

---

# 5. Lexique prix / force

## PRICE_LAG

**Définition :**  
Le prix ne suit pas immédiatement le basculement des forces.

**Lecture :**

```text
Le champ se prépare.
Le prix n’a pas encore raconté l’histoire.
```

---

## WEAK_PRICE_RESPONSE

**Définition :**  
Les forces bougent fortement, mais le prix répond peu.

**Interprétation possible :**

```text
absorption
contre-force
liquidité
structure plus large qui retient
```

---

## PRICE_PAYS_STRUCTURE

**Définition :**  
Le prix finit par suivre le node détecté dans les forces.

**Exemple :**

```text
Node M1 09:23–09:27
prix paie sur M5 09:35–09:45
```

---

# 6. Lexique agentique

## SEQUENCE_READER

**Définition :**  
Agent qui lit la DB et extrait les événements bruts.

**Mission :**

```text
mesurer
extraire
classer froidement
ne pas interpréter trop loin
```

**Entrées :**

```text
force_snapshots
symbol
timeframes
start/end
```

**Sorties :**

```text
windows
up_block
down_block
energy
bid_delta
raw_event
```

---

## NODE_INTERPRETER

**Définition :**  
Agent qui transforme les événements bruts en langage Flow.

**Mission :**

```text
nommer le node
identifier phase
identifier acteurs
connecter pré-field / confirmation / breath / absorption
```

---

## COCKPIT_TRANSLATOR

**Définition :**  
Agent qui traduit l’interprétation en phrase courte cockpit.

**Mission :**

```text
réduire la charge mentale
ne pas tout afficher
ne pas noyer le trader
```

**Exemple :**

```text
NODE NAISSANT — CAD+JPY+USD reprennent contre EUR+GBP+CHF. Prix encore retenu.
```

---

## LAB_TRANSLATOR

**Définition :**  
Agent qui transforme une observation trader ou séquence DB en fiche Lab.

**Mission :**

```text
sauver la mémoire
nommer les comportements
préparer validation future
```

---

# 7. Règles d’alerte proposées

## NODE_BIRTH_FAST

**Définition :**  
Alerte rapide quand les forces basculent collectivement.

**Préconditions :**

```text
bloc haut / bloc bas
compression ou extension préalable
énergie forte
rotation opposée
```

**Trigger :**

```text
UP_BLOCK fort
DOWN_BLOCK fort
price_lag présent
```

**Phrase cockpit :**

```text
NODE NAISSANT — forces basculent, prix encore retenu.
```

---

## NODE_CONFIRMATION_M5

**Définition :**  
Alerte quand le node M1 est confirmé par M5.

**Préconditions :**

```text
node birth M1 détecté
même camp dominant sur M5
bid commence à payer
```

**Phrase cockpit :**

```text
NODE CONFIRMÉ M5 — structure commence à payer.
```

---

## COUNTER_BREATH_ALERT

**Définition :**  
Alerte respiration contraire.

**Préconditions :**

```text
après confirmation
bloc opposé rebondit
camp dominant relâche
```

**Phrase cockpit :**

```text
RESPIRATION CONTRAIRE — surveiller absorption ou invalidation.
```

---

## BREATH_ABSORBED_ALERT

**Définition :**  
Alerte quand la respiration contraire est absorbée.

**Préconditions :**

```text
counter breath détecté
prix ne paie pas beaucoup contre la structure
camp dominant reprend
```

**Phrase cockpit :**

```text
RESPIRATION ABSORBÉE — structure reprend.
```

---

# 8. Séquence type apprise

## Pattern

```text
USD_CAD_JPY_RESPRING_AGAINST_RISK_BLOCK_FOLD
```

## Phases

```text
PRE_FIELD:
AUD_HIGH_EXTENSION_WITH_USD_CAD_LOW_COMPRESSION

NODE_BIRTH:
CAD_JPY_USD_RESPRING_NODE_AGAINST_RISK_BLOCK_FOLD

CONFIRMATION:
POST_NODE_GRAVITY_CONFIRMATION_LEG

BREATH:
COUNTER_FORCE_BREATH_WITH_WEAK_PRICE_RESPONSE

ABSORPTION:
BREATH_ABSORBED_BY_USD_CAD_GRAVITY
```

## Règle stratégique

```text
Le node est visible dans les forces avant d’être évident sur le prix.
```

---

# 9. Ce que la DB doit apprendre ensuite

Quand le nouveau schéma EA sera persisté, enrichir les nodes avec :

```text
OHLC
tick_volume
pip_range
pip_body
pip_change
spread_points
spread_price
spread_pips
ask
mid
bar_time
bar_close_time
server_time
capture_time
is_closed_bar
NZD
```

Nouvelles classes futures :

```text
NODE_BIRTH_FORCE_ONLY
NODE_BIRTH_WITH_PRICE_LAG
NODE_BIRTH_WITH_CANDLE_BODY
NODE_BIRTH_WITH_VOLUME
NODE_BIRTH_WITH_SPREAD_FRICTION
NODE_CONFIRMED_BY_CLOSED_BAR
```

---

# 10. Doctrine finale

```text
Un node n’est pas un signal isolé.
C’est une fenêtre où les forces changent de régime.
```

```text
Le prix confirme.
Les forces préviennent.
```

```text
PowerFlow doit lire le basculement du champ,
puis seulement ensuite vérifier si le prix paie.
```

```text
Le trader ne doit pas lire sept devises.
PowerFlow doit compresser le champ en une phrase utile.
```
