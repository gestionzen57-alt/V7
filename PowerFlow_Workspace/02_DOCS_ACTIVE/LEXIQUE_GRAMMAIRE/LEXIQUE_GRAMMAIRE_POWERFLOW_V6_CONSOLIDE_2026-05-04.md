# LEXIQUE & GRAMMAIRE POWERFLOW V6 — CONSOLIDATION

**Date de consolidation :** 2026-05-04  
**Statut :** fichier de référence consolidé — lexique vivant  
**Objet :** regrouper les derniers lexiques, patches de grammaire, ajouts Zone/Cockpit, Sequence Nodes, Battlefield Radar, Coalitions et Agents.

---

## 0. Sources consolidées

Ce fichier regroupe et déduplique les contenus issus des documents récents suivants :

```text
LEXIQUE_GRAMMAIRE_COMPORTEMENTS_POWERFLOW.md
LEXIQUE_POWERFLOW_ZONE_COCKPIT_UPDATE.md
PATCH_LEXIQUE_DOCTRINE_POWERFLOW_V6_BATTLEFIELD_RADAR_V02.md
DOCTRINE_ADDENDUM_POWERFLOW_V6_COALITIONS_THERMO.md
GRAMMAIRE_LEXIQUE_SEQUENCE_NODES_V01.md
GRAMMAIRE_LEXIQUE_POWERFLOW_V6_UPDATE_2026-05-04.md
CHECKPOINT_SEQUENCE_NODE_READER_V01.md
RAPPORT_SESSION_POWERFLOW_V6_2026-05-04.md
CHECKPOINT_POWERFLOW_V6_2026-05-04.md
```

Ce document ne remplace pas l’observation vivante. Il sert de socle propre pour éviter que le vocabulaire PowerFlow se disperse entre plusieurs sessions.

---

# 1. Doctrine centrale PowerFlow V6

PowerFlow V6 n’est pas une analyse technique classique.

PowerFlow lit :

```text
le flux
la tension
les comportements relatifs
les zones chargées
les pullbacks absorbés
les pullures
les coalitions
les antagonistes
les rotations
les nodes temporels
les fenêtres potentielles
les scènes fractales
```

PowerFlow ne donne pas de BUY/SELL.

PowerFlow produit des états :

```text
WATCH
WINDOW_OPENING
WINDOW_YOUNG
WINDOW_ACTIVE
WINDOW_LATE
WINDOW_CLOSED
ARMED
DANGER
DATA_BLIND
```

Phrase noyau :

```text
Les forces préviennent.
Le prix confirme.
Le HTF donne la gravité.
Le LTF donne la naissance.
```

Autre phrase centrale :

```text
PowerFlow doit voir le node quand les forces basculent,
pas attendre que le prix ait déjà raconté l’histoire.
```

Règle absolue :

```text
Un événement géométrique sans tension préalable n’est que du bruit.
```

---

# 2. Lexique vivant : principe

Le lexique PowerFlow est vivant.

Il sert à stabiliser le langage après observation.

Règle de travail :

```text
Observer librement.
Nommer.
Documenter.
Comparer.
Attendre répétition.
Formaliser.
Coder seulement ensuite.
```

Mais les briques de lecture brute peuvent être codées avant les lois définitives, si elles restent mesurantes et non prédictives.

---

# 3. Grammaire fractale des timeframes

## WEEKLY_PROFILE

Décor très large, mémoire des zones et champ de rotation supérieur.

## DAILY_REBALANCE_PREPARATION

Champ daily où les forces préparent une redistribution.

## H4_STRUCTURAL_RECOMPOSITION_FIELD

Champ H4 où les grandes forces se recomposent sans forcément valider encore une direction exploitable.

## H1_TEMPORAL_EXPANSION_WINDOW

Fenêtre H1 où le marché laisse assez d’espace pour qu’un scénario inférieur puisse se développer.

## M30_TEMPORAL_EXPANSION_GATE

Porte temporelle. Moment où une compression supérieure peut devenir expansion sur M15/M5.

## M15_BATTLE_SCENE

Scène de bataille. Le M15 montre la construction du scénario.

## M5_TACTICAL_RELEASE

Le M5 montre la libération tactique, la confirmation ou la fabrication de la jambe.

## M1_MICRO_RECHARGE

Le M1 montre la naissance, le microfilm, la couture micro, les petites recharges et les réponses rapides.

## FRACTAL_TIME_IMBRICATION

Imbrication des timeframes où chaque étage temporel porte une fonction.

```text
H4/H1 = gravité / scène large
M30   = champ de bataille / scène active
M15   = relais / confirmation tactique
M5    = timing tactique
M1    = naissance / microfilm / pré-signal
```

Phrase :

```text
Le HTF donne la scène.
Le LTF donne la fenêtre.
```

## HTF_GRAVITY_NODE

Node visible sur H4/H1/M30 qui porte la gravité de fond.

Rôle :

```text
Qualifier le contexte.
Ne pas forcément donner le timing d’entrée.
```

## LTF_PRESIGNAL_BIRTH

Pré-signal ou naissance observable sur M1/M5/M15 avant que le HTF ne devienne évident.

Rôle :

```text
Détecter la fenêtre jeune.
```

## MTF_CONFIRMATION_LATE

Confirmation sur timeframe moyen alors que la naissance LTF a déjà eu lieu.

Exemple :

```text
M30/H1 confirme une scène,
mais M1/M5 ont déjà donné le départ.
```

## WINDOW_ALREADY_CLOSING

État où la scène HTF reste valide mais où la fenêtre tactique LTF est déjà avancée ou consommée.

Phrase cockpit future :

```text
Scène HTF active, mais fenêtre LTF probablement tardive.
```

## HTF_NODE_LTF_WINDOW_CLOSED

Cas où le node large est visible sur H4/H1 mais où les pré-signaux M1/M5/M15 sont déjà passés.

Lecture :

```text
Ne pas chercher le départ.
Chercher respiration, second leg ou absorption.
```

---

# 4. États de zone

## NEUTRAL

État neutre.

```text
Aucune tension suffisante.
Aucune zone active clairement nommable.
```

## PRE_EXTREME

Zone d’approche d’un extrême.

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

## EARLY_EXTREME

Extrême naissant.

```text
La devise est déjà dans une zone extrême ou quasi extrême,
mais la zone n’a pas encore assez de maturité pour être ACCUMULATING.
```

Importance :

```text
PowerFlow ne noie plus les extrêmes jeunes dans NEUTRAL.
Il voit la naissance du champ.
```

## ACCUMULATING

Zone en accumulation.

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

## LEAKING

Fuite de zone.

```text
La zone commence à perdre son absorption.
La tension n’est pas forcément cassée,
mais l’énergie commence à fuir.
```

Lecture :

```text
première perte de contrôle
pré-rupture
début de libération
```

## RUPTURE

Rupture de zone.

```text
La zone a libéré ou cassé sa structure précédente.
```

Lecture :

```text
release
cassure comportementale
changement de phase
```

## NORMAL

Zone non extrême.

## EXTREME

Zone extrême dynamique.

## POST_ZONE

Après-zone, souvent liée à LEAKING ou RUPTURE.

---

# 5. Film de zone

## Zone Event

Diagnostic isolé dans `zone_diagnostics`.

Exemple :

```text
JPY M1 ACCUMULATING EXTREME
```

## Zone Sequence

Suite d’événements sur une même devise, même timeframe, même direction.

Exemple :

```text
PRE_EXTREME → ACCUMULATING → PRE_EXTREME → LEAKING → RUPTURE
```

Lecture :

```text
La zone devient un film.
```

## Zone Evolution Score

Score d’importance d’une séquence de zone.

Il tient compte de :

```text
contexte
tension
durée
états traversés
rupture
fuite
```

## FRACTAL_ZONE_STACK

Détection d’une même devise travaillée sur plusieurs timeframes.

Critères :

```text
même devise
même direction HIGH/LOW
proximité ou chevauchement temporel
timeframe supérieur porteur
timeframe inférieur relais
```

## HTF_ANCHORED_ZONE

Zone portée par un timeframe supérieur.

Exemple :

```text
H1 porte
M30 structure
M15 relaie
```

## HTF_ANCHORED_RELEASE_STACK

Stack fractal avec release.

Exemple :

```text
AUD LOW M15/M30/H1
H1 anchor
M30 scenario
M15 trigger
RUPTURE présente
```

## SCENARIO_ANCHORED_ZONE

Zone portée par M30/M15.

Lecture :

```text
scénario intermédiaire actif
```

## M15_SCENARIO_WITH_M5_RELAY

M15 porte le scénario, M5 relaie tactiquement.

## SHORT_FRACTAL_RELEASE

Release courte sur M1/M5.

Lecture :

```text
microfilm + release tactique
```

---

# 6. Sessions

## ASIA_SEED

Asia pose ou porte une tension initiale.

## LONDON_OPEN_FORGE

London Open concentre ou travaille la zone.

## LONDON_FORGE

London façonne le champ de bataille.

## US_RELEASE

US libère ou commence à libérer la tension.

## LATE_US_MICROFILM

Late US montre surtout du microfilm M1/M5.

## SESSION_CARRIED_TENSION

Tension portée entre plusieurs sessions.

Exemple :

```text
ASIA → LONDON_OPEN
```

## FULL_DAY_CARRY

Champ porté sur une grande partie de la journée.

## SESSION_RELEASE

Release détectée dans une session.

---

# 7. Termes thermodynamiques

## COMPRESSED

Tension maximale, énergie concentrée.

Attention : l’état COMPRESSED peut avoir existé avant que le dashboard observe la release.

## ACTIVE

Devise ou champ vivant, mouvement présent.

## NEUTRAL

Activité moyenne, ni compression forte ni vide.

## HOLLOW

Marché creux, peu de matière, tendance vide.

## DEAD

Aucune activité mesurable utile.

## ÉLASTIQUE CHARGÉ

Une devise reste tendue dans une zone extrême, absorbe les respirations et garde une tension exploitable.

Lecture :

```text
la zone encaisse
la tension reste chargée
une libération potentielle se prépare
```

## TENSION_SCORE

Score de charge comportementale d’une zone.

Ne doit pas être confondu avec une alerte.

## PULLURE

Micro-respiration dans une zone.

Exemples :

```text
Pullure absorbée   : -2.60 → -2.35 → -2.70
Pullure qui fuit   : -2.70 → -2.40 → -2.20
Pullure de rupture : -2.50 → -2.10 → -1.60
```

## PULLURE_ABSORPTION_FIELD

Pattern où une devise encaisse plusieurs pullures ou pullbacks successifs sans céder.

## EXTREME_BREATHING_FIELD

Respiration en zone extrême, sans release immédiate.

---

# 8. Fenêtres temporelles

## TEMPORAL_EXPANSION_WINDOW

Fenêtre où les timeframes supérieurs donnent assez d’espace, de respiration ou de conflit non résolu pour permettre une expansion sur les timeframes inférieurs.

## HTF_EXPANSION_PERMISSION

État où H1/H4/Daily ne valident pas forcément une direction, mais laissent une permission de scénario aux timeframes inférieurs.

## TEMPORAL_EXPANSION_GATE

Moment ou zone où un timeframe supérieur valide qu’une compression peut devenir expansion sur les timeframes inférieurs.

## WINDOW_PREPARING

Fenêtre en préparation. Les forces se regroupent, mais la release n’est pas encore claire.

## WINDOW_GATE_OPEN

La porte temporelle est ouverte. La compression peut payer.

## WINDOW_EXPANDING

La fenêtre est en expansion active.

## WINDOW_PAID

La fenêtre a déjà payé une grande partie de son énergie.

## WINDOW_REBALANCING

Phase de rebalancement après release.

## WINDOW_YOUNG

Pré-signal jeune, opportun pour surveillance tactique.

## WINDOW_ACTIVE

Scène en cours, confirmation ou impact en développement.

## WINDOW_LATE

Signal déjà avancé. Le HTF confirme mais le timing LTF est moins propre.

## WINDOW_CLOSED

La fenêtre de départ est consommée.

## WINDOW_CLOSING

Fenêtre de temps tactique qui se ferme.

Signatures :

```text
HTF toujours visible
LTF déjà avancé
prix a déjà payé une partie importante
```

## WATCH_SECOND_LEG

Ne pas chercher la première cassure.

Surveiller respiration puis deuxième jambe.

## WATCH_ABSORPTION

Surveiller si la respiration est absorbée.

---

# 9. Phases de séquence

## PRE_FIELD

Champ préparatoire avant la naissance visible d’un node.

Signatures possibles :

```text
bloc haut en extension
bloc bas comprimé
devises pivot/refuge en position anormale
prix calme ou suspendu
```

## NODE_BIRTH

Naissance du node.

Moment où les forces basculent brutalement de façon collective.

Règle clé :

```text
Le node peut naître avant que le prix bouge fortement.
```

Signatures :

```text
un bloc monte ensemble
un bloc opposé tombe ensemble
énergie forte
synchronisation courte
prix encore retenu
```

## CONFIRMATION_PENDING

Phase entre naissance LTF et validation M5/M15.

## CONFIRMATION_LEG

Jambe de confirmation après la naissance du node.

Signatures :

```text
le même camp continue sur TF supérieur
le prix commence à payer
la synchronisation s’étend de M1 vers M5/M15
```

## CONFIRMED

La structure commence à payer.

Signatures :

```text
M5/M15 suit le node
bid commence à payer
bloc dominant persiste
```

## COUNTER_BREATH

Respiration contraire après confirmation.

Signatures :

```text
le camp opposé rebondit
le camp dominant relâche
prix rend peu ou temporairement
```

Règle :

```text
Une respiration contraire n’invalide pas la structure.
Il faut voir si elle paie en prix.
```

## ABSORPTION

Moment où une respiration contraire est absorbée.

Signatures :

```text
le camp dominant reprend
le prix reprend la direction de la structure
la respiration précédente perd son effet
```

## SECOND_LEG

Deuxième jambe après respiration ou recharge.

## STRUCTURE_PAYING

Moment où le prix commence à raconter ce que les forces ont déjà montré.

Phrase Flow :

```text
Le prix paie la structure.
```

Important :

```text
PowerFlow ne doit pas attendre cette phase pour voir la naissance.
```

---

# 10. Nodes et patterns

## RAW_NODE_BIRTH

Détection brute d’une naissance de node depuis les données `force_snapshots`.

Sans interprétation complète.

## NODE_BIRTH_FAST

Alerte rapide quand les forces basculent collectivement.

Préconditions :

```text
bloc haut / bloc bas
compression ou extension préalable
énergie forte
rotation opposée
```

Trigger :

```text
UP_BLOCK fort
DOWN_BLOCK fort
PRICE_LAG présent
```

Phrase cockpit :

```text
NODE NAISSANT — forces basculent, prix encore retenu.
```

## GRAVITY_RESPRING_NODE

Node où les devises de gravité/pivot ou assimilées reprennent fortement depuis une position basse ou comprimée.

Exemple :

```text
USD + CAD respring
```

Extension possible :

```text
JPY rejoint le mouvement comme refuge response.
```

## CAD_JPY_USD_RESPRING_NODE_AGAINST_RISK_BLOCK_FOLD

Pattern observé sur GBPUSD le 2026-05-04.

Structure :

```text
CAD + JPY + USD montent brutalement
EUR + GBP + AUD/CHF se replient
prix encore retenu à la naissance
confirmation M5 ensuite
```

Famille :

```text
GRAVITY_RESPRING_NODE
RISK_BLOCK_FOLD
```

## PRICE_LAG_AT_NODE_BIRTH

Décalage entre l’inversion des forces et le mouvement prix.

Règle :

```text
Quand les forces basculent mais que le prix ne bouge pas encore,
PowerFlow doit suspecter une naissance de node.
```

## M5_CONFIRMATION_LEG

Confirmation d’un node M1 par une poursuite cohérente sur M5.

Signatures :

```text
même camp dominant
prix commence à payer
bloc opposé continue de se vider
```

## BREATH_ABSORBED

Respiration opposée qui ne casse pas la structure.

Signatures :

```text
rebond des forces opposées
réponse prix faible
reprise du camp dominant ensuite
```

## POWER_ANGLE_ALERT

Alerte d’angle fort avant ou pendant la cassure prix.

Signatures :

```text
devise dominante accélère
angle de force augmente brutalement
bloc opposé se vide
prix proche d’une cassure ou commence à payer
```

## FORCE_ANGLE_BREAK

Cassure d’angle dans les forces.

Différence avec node :

```text
NODE_BIRTH = basculement de régime
FORCE_ANGLE_BREAK = accélération directionnelle lisible
```

## PRICE_IMPACT_LEG

Jambe où le prix paie brutalement la structure.

## POWER_ANGLE_BREAK_TO_PRICE_IMPACT

Pattern visuel observé sur la séquence 12:45 → 13:45.

Structure :

```text
angle USD/CAD fort
GBP/EUR/AUD drainent
prix casse
respiration ensuite
```

## POST_IMPACT_BREATH

Respiration après une jambe d’impact.

## POST_IMPACT_FORCE_PERSISTENCE

Les forces dominantes restent orientées après l’impact, même si le prix respire.

Exemple :

```text
CAD/USD restent porteurs
prix stabilise ou rebondit légèrement
```

## PRICE_BREATH_AGAINST_FORCE

Le prix respire contre une structure de force encore active.

---

# 11. Blocs, coalitions et mouvements

## UP_BLOCK

Groupe de devises qui montent ensemble sur une fenêtre courte.

Exemple :

```text
CAD + JPY + USD
```

## DOWN_BLOCK

Groupe de devises qui tombent ensemble sur une fenêtre courte.

Exemple :

```text
EUR + GBP + CHF
```

## RISK_BLOCK

Bloc composé majoritairement de devises de rôle RISK.

Exemples :

```text
EUR + GBP + AUD
EUR + GBP
AUD + GBP
```

## REFUGE_BLOCK

Bloc composé majoritairement de devises REFUGE.

Exemple :

```text
JPY + CHF
```

## PIVOT_BLOCK

Bloc dominé par des devises pivot ou gravitationnelles.

Exemple :

```text
USD + CAD
```

## MIXED_GRAVITY_BLOCK

Bloc composé de pivot + refuge.

Exemple :

```text
USD + CAD + JPY
```

Lecture :

```text
Ce bloc peut reprendre le champ contre un bloc risk.
```

## RESPRING

Remontée brusque d’une devise ou d’un bloc depuis une zone basse ou comprimée.

## FOLD

Pliage / vidange d’une devise ou d’un bloc depuis une zone haute ou intermédiaire.

## SYNC_RESPRING

Plusieurs devises remontent ensemble sur une fenêtre courte.

## SYNC_FOLD

Plusieurs devises tombent ensemble sur une fenêtre courte.

## OPPOSITE_BLOCK_ROTATION

Rotation simultanée entre un bloc montant et un bloc descendant.

Phrase :

```text
Un camp reprend le champ pendant que l’autre se vide.
```

## COALITION

Famille temporaire de devises avançant avec cohérence commune.

Une coalition apparaît quand plusieurs devises :

```text
ont une tension comparable
partagent une polarité
prennent une direction proche
respirent ensemble dans le temps
```

Phrase :

```text
Une coalition n’est pas une prédiction.
C’est une famille de forces qui respire ensemble.
```

## RELATION_ACTIVE

Scène où une coalition rencontre un antagoniste clair.

Formule :

```text
devise isolée
→ anomalie relative
→ respiration de zone
→ coalition temporaire
→ antagoniste
→ relation active
→ future fenêtre temporelle
```

## ANTAGONISTE

Devise ou coalition qui travaille en face.

Lecture :

```text
opposition de champ
force contraire
camp adverse
```

## HIGH_COALITION

Ensemble de devises travaillant côté HIGH dans la même fenêtre.

## LOW_COALITION

Ensemble de devises travaillant côté LOW dans la même fenêtre.

---

# 12. Prix / force

## PRICE_LAG

Le prix ne suit pas immédiatement le basculement des forces.

Lecture :

```text
Le champ se prépare.
Le prix n’a pas encore raconté l’histoire.
```

## WEAK_PRICE_RESPONSE

Les forces bougent fortement, mais le prix répond peu.

Interprétations possibles :

```text
absorption
contre-force
liquidité
structure plus large qui retient
```

## PRICE_PAYS_STRUCTURE

Le prix finit par suivre le node détecté dans les forces.

Exemple :

```text
Node M1 09:23–09:27
prix paie sur M5 09:35–09:45
```

## PRICE_PAYING

Le prix commence à suivre la structure.

## PIP_VELOCITY

Vitesse du prix en pips par minute.

## PIP_RANGE

Amplitude en pips sur la fenêtre ou la bougie.

## PIP_BODY

Corps de bougie exprimé en pips.

## PIP_CHANGE

Variation nette du prix sur une fenêtre.

---

# 13. Mesures cinématiques

## FORCE_VELOCITY

Variation de force par minute.

```text
force_velocity_per_min = force_delta / minutes
```

## FORCE_ANGLE_DEG

Angle géométrique approximatif de la force.

```text
angle = atan(force_velocity_per_min)
```

Ce n’est pas un angle pixel du graphique. C’est un proxy mathématique.

## FORCE_ACCELERATION

Variation de vitesse entre deux segments.

```text
acceleration = velocity_current - velocity_previous
```

## FORCE_ENERGY

Énergie brute d’une fenêtre, souvent approximée par la somme des variations absolues des devises.

```text
energy = Σ abs(force_delta)
```

Utilité :

```text
Repérer les fenêtres où quelque chose se passe vraiment.
```

## THERMAL_NET_ENERGY

Énergie nette.

Formule conceptuelle :

```text
thermal_net_energy = énergie brute - dissipation - friction
```

## DISSIPATION

Énergie qui se vide sans libération exploitable.

## FRICTION

Résistance ou bloqueur de libération.

## ENTROPY / DISORDER_FIELD

Champ actif mais désordonné, non structuré.

Règle :

```text
Nommer, ne pas forcer en signal.
```

---

# 14. Battlefield Radar

## BATTLEFIELD_RADAR

Brique qui agrège coalitions et relations actives pour repérer les scènes d’intérêt stratégique.

Phrase noyau :

```text
BattlefieldRadar ne dit pas “la fenêtre est ouverte”.
Il dit “ici, une bataille se prépare”.
```

Place dans la grammaire :

```text
acteur individuel
→ respiration de zone
→ coalition
→ relation coalition vs antagoniste
→ scène d’intérêt radar
→ densité temporelle future
→ fenêtre active future
```

## SCÈNE D’INTÉRÊT STRATÉGIQUE

Zone temporelle où PowerFlow aperçoit une structure collective utile pour le cockpit.

Elle peut être :

```text
relation active
coalition forte
champ en préparation
```

Mais elle n’est pas encore :

```text
TemporalWindowActive
```

## BATAILLE_EN_PRÉPARATION

Une coalition rencontre ou commence à rencontrer un antagoniste.

Exemple :

```text
AUD+CAD vs JPY
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
```

Lecture :

```text
un bloc bas répond contre un antagoniste haut
```

## RELATION_ACTIVE_PRIORITAIRE

Doctrine V0.2 :

```text
Relation active moyenne > coalition isolée forte
```

Raison :

```text
relation active = coalition + antagoniste + opposition de champ
coalition forte = famille synchronisée mais bataille incomplète
```

## COALITION_FORTE_À_SURVEILLER

Famille synchronisée qui mérite attention cockpit, mais dont l’antagoniste est absent ou pas assez propre.

## États BattlefieldRadar

```text
BATTLE_WATCH
BATTLE_PREPARING
BATTLE_FORMING
BATTLE_PRESSURIZED
COALITION_FIELD_WATCH
COALITION_FIELD_VISIBLE
COALITION_FIELD_STRONG
```

## Types de scènes

```text
RELATION_ACTIVE
COALITION_STRONG
```

## STRATEGIC_SCORE

Score de tri cockpit propre au radar.

Il ne remplace pas :

```text
field_score
cohesion
context_score
```

Il sert à classer les scènes dans le cockpit.

Règle :

```text
relations actives d’abord
coalitions fortes ensuite
```

---

# 15. Battlefield Map et Cockpit Field

## BATTLEFIELD_MAP

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

## TACTICAL_RELEASE_BATTLEFIELD

Champ de release tactique.

Exemple :

```text
CAD HIGH / GBP HIGH release M1/M5
```

## HTF_PREPARATION_FIELD

Champ de préparation porté par des timeframes supérieurs.

Exemple :

```text
EUR LOW M15/M30
GBP LOW M15/M30/H1
CAD LOW M30/H1
```

## GLOBAL_RELEASE_BATTLEFIELD

Ancien comportement V0.1 qui mélangeait trop HIGH et LOW.

À utiliser avec prudence.

Préférer :

```text
cluster-mode side
```

## CONTESTED_WINDOW

Fenêtre où une coalition HIGH et une coalition LOW coexistent.

## CONTESTED_RELEASE_WINDOW

Fenêtre contestée avec release d’un côté.

## BIPOLAR_CONTESTED_RELEASE_WINDOW

Fenêtre contestée où au moins une devise existe en HIGH et LOW.

## BIPOLAR_CURRENCY_FIELD

Une même devise apparaît des deux côtés du champ.

Définition :

```text
la devise a une bataille HIGH
et une bataille LOW
dans la même fenêtre temporelle
```

Ce n’est pas une erreur. C’est une contestation interne.

## INTERNAL_ROTATION_CONTEST

Conflit interne pouvant préparer une rotation.

## MICRO_VS_HTF_ROTATION_CONTEST

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

## HIGH_RELEASE_VS_LOW_HTF_PREP

Release haute court terme contre préparation basse HTF.

## LOW_RELEASE_VS_HIGH_HTF_PREP

Release basse court terme contre préparation haute HTF.

## DOUBLE_SIDE_RELEASE_CONTEST

La devise libère des deux côtés.

Cas rare, probablement chaotique ou transitionnel.

## COCKPIT_FIELD

Vue finale ultra-courte.

Elle affiche :

```text
FIELD
DOMINANT
OPPOSITE / CONTEXT
CONTESTED_WINDOW
BIPOLAR_FOCUS
BIPOLAR_LIST
```

## FIELD

Champ dominant actuel.

Exemple :

```text
TACTICAL_RELEASE_BATTLEFIELD | session=LATE_US
```

## DOMINANT

Camp dominant ou actif.

## OPPOSITE / CONTEXT

Camp opposé ou contexte supérieur.

## BIPOLAR_FOCUS

Devise bipolaire principale.

## BIPOLAR_LIST

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

# 16. Agents PowerFlow

## DB_FRESHNESS_AGENT / DBVisionGuard

Mission :

```text
vérifier que la DB voit vraiment
contrôler lignes récentes par timeframe
vérifier colonnes EA
détecter trous temporels
détecter DATA_BLIND
```

Contrôles prioritaires :

```text
M1/M5/M15/M30/H1/H4 présents
dernière ligne par TF
trous temporels
colonnes EA Extended
NZD
OHLC
volume
pips
spread
is_closed_bar
```

## SEQUENCE_READER

Agent qui lit la DB et extrait les événements bruts.

Mission :

```text
mesurer
extraire
classer froidement
ne pas interpréter trop loin
```

Entrées :

```text
force_snapshots
symbol
timeframes
start/end
```

Sorties :

```text
windows
up_block
down_block
energy
bid_delta
raw_event
phase
```

## FLOW_EVENT_EXTRACTOR

Nom recommandé pour fusionner SequenceReader + features cinématiques.

Mission :

```text
lire les snapshots
calculer deltas + blocs + énergie + vitesse + angle
sortir des événements bruts ordonnés
```

Sorties :

```text
PRE_FIELD
NODE_BIRTH
CONFIRMATION
COUNTER_BREATH
ABSORPTION
SECOND_LEG
WINDOW_CLOSING
```

## FORCE_KINEMATICS_AGENT

Mission :

```text
mesurer vitesse
angle
accélération
pips/min
force energy
price lag
```

Statut recommandé :

```text
module mathématique interne plutôt qu’agent autonome au début
```

## FRACTAL_ORCHESTRATOR / FractalWindowEngine

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

## NODE_INTERPRETER / SceneNamer

Mission :

```text
nommer la scène
classer le comportement
transformer les events en langage Flow
```

Règle :

```text
Il nomme.
Il ne recalcule pas.
```

## COCKPIT_TRANSLATOR

Mission future :

```text
condense les sorties agents en 3 lignes utiles
ne calcule pas
ne décide pas
```

## COCKPIT_STATE_EMITTER

Brique recommandée avant interface.

Mission :

```text
écrire un cockpit_state_v2.json stable
```

## LAB_MEMORY_AGENT

Mission :

```text
sauver observation trader
créer fiche Lab
capturer vocabulaire nouveau
préparer hypothèse testable
```

## LAB_TRANSLATOR

Agent qui transforme une observation trader ou séquence DB en fiche Lab.

Mission :

```text
sauver la mémoire
nommer les comportements
préparer validation future
```

## MISSION_BUILDER_AGENT

Mission :

```text
transformer un Lab en mission codable
définir fichier cible, objectif, contraintes, tests
réduire les patchs confus
```

Format attendu :

```text
MISSION
FICHIER CIBLE
OBJECTIF
CONTRAINTES
INPUTS
OUTPUTS
TESTS
ROLLBACK
```

---

# 17. Alertes proposées

## NODE_BIRTH_FAST

Alerte rapide quand les forces basculent collectivement.

Phrase cockpit :

```text
NODE NAISSANT — forces basculent, prix encore retenu.
```

## NODE_CONFIRMATION_M5

Alerte quand le node M1 est confirmé par M5.

Préconditions :

```text
node birth M1 détecté
même camp dominant sur M5
bid commence à payer
```

Phrase cockpit :

```text
NODE CONFIRMÉ M5 — structure commence à payer.
```

## COUNTER_BREATH_ALERT

Alerte respiration contraire.

Préconditions :

```text
après confirmation
bloc opposé rebondit
camp dominant relâche
```

Phrase cockpit :

```text
RESPIRATION CONTRAIRE — surveiller absorption ou invalidation.
```

## BREATH_ABSORBED_ALERT

Alerte quand la respiration contraire est absorbée.

Préconditions :

```text
counter breath détecté
prix ne paie pas beaucoup contre la structure
camp dominant reprend
```

Phrase cockpit :

```text
RESPIRATION ABSORBÉE — structure reprend.
```

---

# 18. Patterns Lab enregistrés

## LAB_004_USD_CAD_JPY_RESPRING_AGAINST_RISK_BLOCK_FOLD

Séquence :

```text
GBPUSD
2026-05-04
09:00 → 10:15
```

Découpage :

```text
PRE_FIELD        09:00 → 09:20
NODE_BIRTH       09:23 → 09:27
CONFIRMATION     09:30 → 09:45
COUNTER_BREATH   09:49 → 09:54
ABSORPTION       10:00 → 10:15
```

Structure :

```text
CAD+JPY+USD respring
EUR+GBP+CHF/AUD fold
prix encore retenu
confirmation M5 ensuite
```

Pattern compact :

```text
GRAVITY_RESPRING_NODE
```

## LAB_005_USD_CAD_ANGLE_BREAK_WITH_GBP_EUR_DRAIN

Séquence :

```text
GBPUSD
2026-05-04
12:45 → 13:45 visuel
```

État :

```text
DB fine absente sur M1/M5/M15
M30 confirme seulement l’impact large
```

Pattern :

```text
POWER_ANGLE_BREAK_TO_PRICE_IMPACT
```

Structure :

```text
angle USD/CAD fort
GBP/EUR/AUD drainent
prix casse
respiration ensuite
```

---

# 19. DB et données attendues

La DB actuelle sait exploiter :

```text
created_at
symbol
timeframe
bid
spread
force_gbp
force_usd
force_eur
force_jpy
force_cad
force_chf
force_aud
```

La DB Extended doit ajouter :

```text
force_nzd
open
high
low
close
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
```

Nouvelles classes futures possibles :

```text
NODE_BIRTH_FORCE_ONLY
NODE_BIRTH_WITH_PRICE_LAG
NODE_BIRTH_WITH_CANDLE_BODY
NODE_BIRTH_WITH_VOLUME
NODE_BIRTH_WITH_SPREAD_FRICTION
NODE_CONFIRMED_BY_CLOSED_BAR
```

Règle :

```text
Si M1/M5/M15 manquent, PowerFlow est aveugle tactiquement.
Si H1/H4 manquent, PowerFlow manque la gravité.
```

---

# 20. Règles de non-confusion

```text
Z-score ≠ signal
Zone state ≠ alerte
Scène d’intérêt ≠ signal
Coalition forte ≠ bataille complète
Relation active ≠ fenêtre ouverte
BattlefieldRadar ≠ TemporalDensity
BattlefieldRadar ≠ TemporalWindowActive
TemporalDensity ≠ TemporalWindowActive
Cockpit Field ≠ Telegram
M1 ≠ décision seule
Node ≠ simple croisement
Cross géométrique sans tension ≠ signal
Respiration contraire ≠ nouveau node principal
HTF confirmation tardive ≠ naissance LTF
```

---

# 21. Règles de lecture

## Règle 1

```text
Un timeframe supérieur ne donne pas toujours la direction.
Parfois il donne l’espace.
```

## Règle 2

```text
La compression n’est pas toujours le moment visible.
La release peut être visible après coup.
```

## Règle 3

```text
M30 ouvre la porte.
M15 porte la scène.
M5 montre la release.
M1 montre la recharge.
```

## Règle 4

```text
Une devise peut ne pas être dominante HTF,
mais avoir une permission d’expansion.
```

## Règle 5

```text
La densité locale ne suffit pas.
Il faut la mémoire de compression.
```

## Règle 6

```text
Le node principal doit être lu dans son ordre temporel.
```

## Règle 7

```text
Si HTF confirme mais LTF est déjà passé :
chercher second leg / absorption, pas naissance.
```

## Règle 8

```text
La DB Freshness est une condition avant toute analyse automatique.
```

---

# 22. Formules cockpit futures

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

```text
NODE NAISSANT — forces basculent, prix encore retenu.
```

```text
RESPIRATION ABSORBÉE — structure reprend.
```

---

# 23. Chaîne agentique recommandée

Circuit chaud :

```text
capture_bridge.py / EA Extended
        ↓
powerflow.db
        ↓
DBVisionGuard
        ↓
FlowEventExtractor
        ↓
FractalWindowEngine
        ↓
SceneNamer
        ↓
cockpit_state_v2.json
        ↓
Cockpit / Telegram / Dashboard plus tard
```

Circuit froid :

```text
screens + ressenti trader
        ↓
LabMemory
        ↓
MissionBuilder
        ↓
TestRunner
        ↓
Checkpoint
```

Priorités recommandées :

```text
P0 — DBVisionGuard
P1 — FlowEventExtractor
P2 — FractalWindowEngine
P3 — SceneNamer
P4 — cockpit_state_v2.json spec
P5 — LabMemory
P6 — MissionBuilder
P7 — Cockpit UI plus tard
```

---

# 24. Verdict doctrinal final

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

```text
La DB ouvre les yeux.
L’extracteur lit le choc.
Le fractal situe la fenêtre.
Le namer donne le mot juste.
Le cockpit affiche seulement l’essentiel.
```

---

# 25. À faire après intégration de ce lexique

```text
1. Déposer ce fichier dans Docs.
2. Le déclarer comme lexique consolidé officiel.
3. Archiver les anciens patches lexique comme sources historiques.
4. Créer la spec DBVisionGuard.
5. Créer la spec FlowEventExtractor V0.1.
6. Ne pas lancer le cockpit final avant cockpit_state_v2.json.
```

Fin du fichier consolidé.
