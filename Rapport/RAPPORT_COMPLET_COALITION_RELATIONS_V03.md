# RAPPORT_COMPLET_COALITION_RELATIONS_V03

**Projet :** PowerFlow V6  
**Brique :** Coalition / Relation thermodynamique  
**Version finalisée :** V0.3  
**Statut :** Validée en environnement Windows/Core avec `powerflow.db`  
**Nature :** Lecture read-only du champ collectif des devises

---

## 1. Intention de la brique

Cette brique est née d’une idée centrale :

```text
Deux devises qui possèdent une tension équivalente,
qui prennent la même direction dans le temps,
et qui réagissent ensemble,
peuvent former un agrégat comportemental.
```

PowerFlow ne doit donc pas seulement lire :

```text
GBP
EUR
USD
JPY
```

Il doit pouvoir lire :

```text
GBP+EUR
CHF+EUR
AUD+CAD
GBP+JPY
```

comme des acteurs collectifs temporaires.

C’est une évolution thermodynamique majeure :

```text
devise isolée
→ anomalie relative
→ respiration de zone
→ coalition temporaire
→ antagoniste potentiel
→ champ de bataille
```

---

## 2. Doctrine respectée

La brique respecte la séparation V6 :

```text
pf_personalities.py
= identité comportementale individuelle

pf_zone_dynamics.py
= respiration de zone

pf_zone_context_logger.py
= mémoire DB des diagnostics de zone

pf_coalitions.py
= agrégats de devises synchronisées

pf_coalition_relations.py
= opposition coalition vs antagoniste

run_coalition_relations_once.py
= lecture read-only cockpit-like
```

La brique ne décide pas.  
Elle ne déclenche pas Telegram.  
Elle ne détecte pas encore de temporal node.  
Elle ne remplace pas la future fenêtre temporelle active.

---

## 3. Architecture validée

### 3.1 Pipeline global

```text
force_snapshots
→ run_zone_context_logger_once.py
→ zone_diagnostics
→ run_coalition_relations_once.py
→ vectors devise
→ pf_coalitions.py
→ pf_coalition_relations.py
→ lecture cockpit-like
```

### 3.2 Mémoire DB

La table `zone_diagnostics` contient :

```text
currency
timeframe
state
zone_level
z_current
bars_in_extreme
tension_score
context_score
context_tags_json
raw_diagnosis_json
```

Cette mémoire permet de reconstruire le film du Z-score par devise.

---

## 4. Correction importante : mode basket

Le logger initial ne loggait que 6 devises :

```text
GBP, EUR, JPY, CAD, CHF, AUD
```

La V0.1.1 a ajouté USD et activé le mode basket.

Sortie validée :

```text
OK logged/kept 35 zone diagnostics into powerflow.db [mode=basket]
```

Ce point est vital parce que USD doit être lu comme acteur :

```text
USD vs panier
```

et non comme absence de mesure.

---

## 5. Correction importante : pente temporelle

Le runner V0.1 utilisait `depth_slope`.

Problème :

```text
depth_slope = pente des profondeurs de pullback
```

Ce n’est pas :

```text
slope du Z-score devise
```

Résultat observé :

```text
slope=+0.0000
curv=+0.0000
```

pour toutes les devises.

La V0.2 a corrigé cela en reconstruisant :

```text
slope = z_current(t) - z_current(t-1)
curvature = slope(t) - slope(t-1)
```

depuis l’historique `zone_diagnostics`.

Résultat : les vectors deviennent vivants.

Exemple réel M1 :

```text
AUD z=-0.106 slope=-0.1567 curv=+0.0362
CAD z=+0.768 slope=-0.1603 curv=-0.0794
CHF z=-0.424 slope=-0.1383 curv=-0.0319
EUR z=+0.776 slope=+0.0247 curv=-0.0144
GBP z=+1.421 slope=+0.2397 curv=+0.0490
JPY z=-1.962 slope=+0.0455 curv=+0.0905
```

---

## 6. Finalisation V0.3 : séparation de la lecture

La V0.3 a séparé le rendu en trois zones :

```text
RELATIONS ACTIVES
COALITIONS FORTES SANS RELATION ACTIVE
BRUIT / RELATIONS FAIBLES
```

Objectif :

```text
ne pas mélanger un vrai champ coalition vs antagoniste
avec une simple famille synchronisée
ou une relation faible/timing mou.
```

### 6.1 Relations actives

Une relation active demande :

```text
coalition propre
antagoniste détecté
opposition de polarité
timing cohérent
field_score >= seuil
```

### 6.2 Coalitions fortes

Une coalition forte peut exister sans antagoniste clair.

Exemple :

```text
CHF+EUR HIGH_PRESSURE_COALITION_FOLDING cohesion=0.94
```

Ce n’est pas une relation active.  
C’est une famille comportementale forte.

### 6.3 Bruit masqué

Les relations faibles sont masquées dans le scan.

Exemple de bruit utile mais non prioritaire :

```text
POLARIZED_FIELD_WITH_WEAK_TIMING
score faible
```

---

## 7. Résultats réels observés

### 7.1 Dernier état M1 — 23:56

Commande :

```bat
python run_coalition_relations_once.py --db powerflow.db --timeframe 1 --vectors
```

Résultat :

```text
Aucun champ coalition utile au seuil courant.
```

Lecture :

```text
Le moteur ne force pas de coalition artificielle.
Le dernier instant contient des mouvements individuels,
mais pas de famille synchronisée assez propre.
```

C’est un bon comportement.

---

### 7.2 Scan M1

Commande :

```bat
python run_coalition_relations_once.py --db powerflow.db --timeframe 1 --scan 240
```

Coalitions fortes détectées :

```text
23:13 — CHF+EUR
HIGH_PRESSURE_COALITION_FOLDING
cohesion=0.94

23:32 — GBP+JPY
HIGH_PRESSURE_COALITION_EXPANDING
cohesion=0.90
antagonist=EUR

23:12 — CHF+EUR
HIGH_PRESSURE_COALITION_FOLDING
cohesion=0.83

23:08 — CHF+EUR
HIGH_PRESSURE_COALITION_FOLDING
cohesion=0.82

23:33 — GBP+JPY
HIGH_PRESSURE_COALITION_EXPANDING
cohesion=0.80
antagonist=EUR
```

Lecture :

```text
M1 détecte des familles microfilm.
CHF+EUR est une coalition haute qui plie.
GBP+JPY est une coalition haute en expansion.
Mais l’antagoniste n’est pas encore assez propre pour qualifier une relation active.
```

---

### 7.3 Scan M15

Commande :

```bat
python run_coalition_relations_once.py --db powerflow.db --timeframe 15 --scan 120
```

Relations actives détectées :

```text
08:15 — AUD+CAD vs JPY
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
score=0.57

08:30 — CAD+GBP vs JPY
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
score=0.54

09:15 — CHF+GBP vs JPY
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
score=0.52
```

Lecture :

```text
JPY agit comme antagoniste haut.
Plusieurs coalitions basses commencent à respirer contre lui.
Le champ M15 contient une série de relations actives faibles/moyennes.
```

C’est important : M15 agit ici comme champ intermédiaire / pont.

---

## 8. Seuils actuels

Seuils V0.3 :

```text
min_field_score = 0.45
strong_cohesion = 0.75
```

Interprétation recommandée :

```text
mode observation   : min_field_score 0.45
mode cockpit utile : min_field_score 0.60
mode alerte future : min_field_score 0.70+
```

Commande stricte testée :

```bat
python run_coalition_relations_once.py --db powerflow.db --timeframe 1 --scan 240 --min-field-score 0.60 --strong-cohesion 0.85
```

Résultat :

```text
RELATIONS ACTIVES
- aucune

COALITIONS FORTES
23:13 CHF+EUR cohesion=0.94
23:32 GBP+JPY cohesion=0.90

BRUIT MASQUÉ
relations faibles masquées: 1
```

Lecture :

```text
Le mode strict nettoie bien le bruit.
Il conserve seulement les familles les plus propres.
```

---

## 9. Vocabulaire créé / stabilisé

### 9.1 Coalitions

```text
LOW_ELASTIC_COALITION_RESPRING
HIGH_PRESSURE_COALITION_FOLDING
HIGH_PRESSURE_COALITION_EXPANDING
HIGH_COALITION_FALLING
LOW_COALITION_RISING
```

### 9.2 Relations

```text
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
HIGH_BLOCK_FOLDING_AGAINST_LOW_RESPRING
POLARIZED_FIELD_WITH_WEAK_TIMING
COALITION_VS_ANTAGONIST_OPPOSITION
```

### 9.3 États de champ

```text
FIELD_SIDE_SHIFT_ACTIVE
BATTLEFIELD_WINDOW_OPENING
STRUCTURE_BUILDING
POLARITY_PRESENT_TIMING_WEAK
WEAK_FIELD_OPPOSITION
```

---

## 10. Ce que cette brique apporte à PowerFlow

Avant :

```text
JPY haut
AUD bas
CAD bas
```

Après :

```text
AUD+CAD forment un bloc bas en respring contre JPY haut qui plie.
```

Avant :

```text
CHF bouge
EUR bouge
```

Après :

```text
CHF+EUR forment une coalition haute en folding microfilm.
```

Ce changement est énorme parce que PowerFlow commence à lire :

```text
acteur collectif
bloc de pression
antagoniste
champ de bataille
```

et pas seulement des courbes isolées.

---

## 11. Limites connues

### 11.1 Pas encore fenêtre temporelle active

Cette brique ne dit pas :

```text
la fenêtre temporelle est officiellement ouverte
```

Elle dit seulement :

```text
la structure du champ devient lisible
```

La future brique devra analyser :

```text
durée
répétition
alignement multi-TF
densité temporelle
persistance relationnelle
succession de coalitions
```

### 11.2 Pas encore énergie nette

Cette brique ne calcule pas encore :

```text
raw_energy - dissipation - friction
```

Elle prépare les acteurs collectifs pour le faire plus tard.

### 11.3 Pas encore logger coalition

Les coalitions ne sont pas encore stockées en DB.

Pour l’instant :

```text
zone_diagnostics = mémoire
coalitions = lecture read-only
```

Un futur `pf_coalition_context_logger.py` pourra mémoriser les coalitions si nécessaire.

---

## 12. Commandes de référence

### Logger basket

```bat
python run_zone_context_logger_once.py --db powerflow.db --replace --summary
```

### Dernier M1

```bat
python run_coalition_relations_once.py --db powerflow.db --timeframe 1 --vectors
```

### Scan M1

```bat
python run_coalition_relations_once.py --db powerflow.db --timeframe 1 --scan 240
```

### Scan M15

```bat
python run_coalition_relations_once.py --db powerflow.db --timeframe 15 --scan 120
```

### Scan strict

```bat
python run_coalition_relations_once.py --db powerflow.db --timeframe 1 --scan 240 --min-field-score 0.60 --strong-cohesion 0.85
```

### JSON pour analyse future

```bat
python run_coalition_relations_once.py --db powerflow.db --timeframe 15 --scan 120 --json
```

---

## 13. Verdict final

```text
Brique coalition/relation thermodynamique V0.3 = VALIDÉE
```

Elle permet maintenant à PowerFlow de voir :

```text
des familles de devises
des blocs synchronisés
des antagonistes potentiels
des relations actives faibles/moyennes
des coalitions fortes sans antagoniste
```

Elle constitue une fondation vitale pour :

```text
fenêtre temporelle active
énergie nette
dissipation
friction
lecture cockpit avancée
```

---

## 14. Phrase noyau

```text
Une coalition n’est pas une prédiction.
C’est une famille de forces qui respire ensemble.
Une relation active apparaît quand cette famille rencontre un antagoniste vivant.
```

Fin du rapport.
