# RAPPORT_COMPLET_BATTLEFIELD_RADAR_V02

**Projet :** PowerFlow V6  
**Brique :** Battlefield Radar  
**Version :** V0.2  
**Statut :** Validée terrain sur `powerflow.db`  
**Objectif :** Donner au cockpit une vue globale des batailles en préparation  
**Nature :** Module read-only, sans décision de fenêtre temporelle active

---

## 1. Intention de la brique

Après la validation des briques :

```text
ZoneDynamics
ZoneContextLogger
Coalitions
CoalitionRelations
```

PowerFlow pouvait déjà voir :

```text
des devises qui respirent ensemble
des coalitions fortes
des relations coalition vs antagoniste
```

Mais le cockpit ne devait pas devenir une liste brute.

Il lui fallait une brique capable de répondre à :

```text
où sont les scènes d’intérêt ?
où une bataille commence-t-elle à se préparer ?
quels champs méritent l’attention du cockpit ?
```

Cette brique est :

```text
pf_battlefield_radar.py
```

---

## 2. Phrase noyau

```text
BattlefieldRadar ne dit pas “la fenêtre est ouverte”.
Il dit “ici, une bataille se prépare”.
```

Cela protège la frontière entre :

```text
scène d’intérêt stratégique
```

et :

```text
fenêtre temporelle active
```

---

## 3. Frontière stricte

`pf_battlefield_radar.py` ne fait pas :

```text
- pas de calcul z_basket
- pas de lecture force_snapshots brute
- pas d’écriture DB
- pas de Telegram
- pas de Temporal Node
- pas de TemporalDensity
- pas de TemporalWindowActive
```

Il fait :

```text
- agrège relations actives
- agrège coalitions fortes
- classe les scènes d’intérêt
- priorise ce qui mérite le cockpit
- produit une phrase synthétique
```

---

## 4. Position architecture

```text
force_snapshots
→ pf_personalities.py
→ pf_zone_dynamics.py
→ pf_zone_context_logger.py
→ zone_diagnostics
→ pf_coalitions.py
→ pf_coalition_relations.py
→ pf_battlefield_radar.py
→ cockpit global
```

Puis plus tard :

```text
pf_battlefield_radar.py
→ pf_temporal_density.py
→ pf_temporal_window_active.py
```

---

## 5. Pourquoi V0.2 était nécessaire

La V0.1 fonctionnait techniquement, mais elle classait trop haut les coalitions fortes seules.

Exemple V0.1 :

```text
Radar: coalition forte à surveiller —
[TF1] CHF+EUR —
COALITION_FIELD_STRONG /
HIGH_PRESSURE_COALITION_FOLDING /
cohesion=0.94
```

Ce n’était pas faux.

Mais ce n’était pas optimal pour le cockpit, car des relations actives existaient plus bas :

```text
TF30 — AUD+GBP vs EUR
TF15 — AUD+CAD vs JPY
TF15 — CAD+GBP vs JPY
TF15 — CHF+GBP vs JPY
```

Une relation active est plus stratégique qu’une coalition isolée, même si son score est plus modéré.

---

## 6. Correction V0.2

La V0.2 apporte :

```text
1. Relations actives en priorité.
2. Coalitions fortes en second niveau.
3. Déduplication des familles répétées.
4. Ajout de strategic_score.
5. Lecture multi-TF plus cockpit.
```

Doctrine de tri :

```text
Relation active moyenne > coalition isolée forte
```

Raison :

```text
relation active = coalition + antagoniste + opposition de champ
coalition forte = famille synchronisée mais bataille incomplète
```

---

## 7. Scores utilisés

### 7.1 field_score

Utilisé pour les relations actives.

Il exprime la force relationnelle :

```text
coalition vs antagoniste
```

### 7.2 cohesion

Utilisé pour les coalitions fortes.

Il exprime la force interne :

```text
les membres respirent-ils ensemble ?
```

### 7.3 strategic_score

Ajout V0.2.

Il sert au tri cockpit.

Principe :

```text
une relation active reçoit une priorité structurelle
une coalition forte reste visible mais après les relations
```

Exemple :

```text
TF30 AUD+GBP vs EUR field=0.60
strategic=1.60

TF1 CHF+EUR cohesion=0.94
strategic=0.98
```

Donc le radar affiche d’abord la bataille relationnelle.

---

## 8. États radar

### 8.1 BATTLE_WATCH

Scène faible ou non prioritaire.

### 8.2 BATTLE_PREPARING

Une bataille est en préparation.

Souvent :

```text
relation active faible
field autour de 0.45–0.55
```

### 8.3 BATTLE_FORMING

La relation devient plus lisible.

Souvent :

```text
field autour de 0.55–0.70
```

### 8.4 BATTLE_PRESSURIZED

Champ plus avancé, pression forte.

À réserver pour la suite.

### 8.5 COALITION_FIELD_WATCH

Coalition faible mais visible.

### 8.6 COALITION_FIELD_VISIBLE

Coalition propre, à surveiller.

### 8.7 COALITION_FIELD_STRONG

Coalition très propre, mais pas forcément bataille complète.

---

## 9. Types de scènes

### 9.1 RELATION_ACTIVE

Scène où une coalition rencontre un antagoniste.

Exemple :

```text
AUD+GBP vs EUR
```

### 9.2 COALITION_STRONG

Famille de devises qui respire ensemble, sans relation active complète.

Exemple :

```text
CHF+EUR
HIGH_PRESSURE_COALITION_FOLDING
```

---

## 10. Résultats terrain validés

Commande :

```bat
python run_battlefield_radar_once.py --db powerflow.db --scan 240
```

Sortie globale :

```text
Radar: bataille relationnelle prioritaire —
[TF30] AUD+GBP vs EUR —
BATTLE_FORMING /
COALITION_VS_ANTAGONIST_OPPOSITION /
field=0.60
```

---

## 11. Top scènes relationnelles

### 11.1 TF30 — AUD+GBP vs EUR

```text
BATTLE_FORMING
COALITION_VS_ANTAGONIST_OPPOSITION
field=0.60
strategic=1.60
```

Lecture :

```text
AUD+GBP forment un bloc collectif.
EUR apparaît comme antagoniste.
Le champ TF30 commence à se former.
```

### 11.2 TF15 — AUD+CAD vs JPY

```text
BATTLE_FORMING
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
field=0.57
strategic=1.57
```

Lecture :

```text
AUD+CAD répondent depuis le bas.
JPY agit comme antagoniste haut.
La bataille M15 se forme.
```

### 11.3 TF15 — CAD+GBP vs JPY

```text
BATTLE_PREPARING
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
field=0.54
strategic=1.54
```

Lecture :

```text
JPY reste antagoniste.
Un autre bloc bas répond.
La répétition autour de JPY devient une scène d’intérêt.
```

### 11.4 TF15 — CHF+GBP vs JPY

```text
BATTLE_PREPARING
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
field=0.52
strategic=1.52
```

Lecture :

```text
Troisième contestation de JPY par un bloc bas.
Le radar aperçoit une scène répétée.
```

---

## 12. Coalitions fortes observées

### 12.1 TF1 — GBP+JPY

```text
COALITION_FIELD_VISIBLE
HIGH_PRESSURE_COALITION_EXPANDING
cohesion=0.90
strategic=1.05
```

Lecture :

```text
Coalition microfilm forte.
Antagoniste potentiel faible ou incomplet.
À surveiller, mais après relations actives.
```

### 12.2 TF1 — CHF+EUR

```text
COALITION_FIELD_STRONG
HIGH_PRESSURE_COALITION_FOLDING
cohesion=0.94
strategic=0.98
```

Lecture :

```text
Famille très propre.
Pas de bataille complète.
```

### 12.3 TF15 — AUD+GBP

```text
COALITION_FIELD_STRONG
HIGH_COALITION_FALLING
cohesion=0.92
strategic=0.98
```

Lecture :

```text
Bloc haut en retour/falling.
Surveillance stratégique.
```

### 12.4 TF15 — AUD+CHF

```text
COALITION_FIELD_VISIBLE
HIGH_COALITION_FALLING
cohesion=0.89
```

Lecture :

```text
Famille haute en descente.
Pas encore bataille relationnelle.
```

---

## 13. Lecture globale de la journée analysée

Le radar voit deux grandes familles de scènes.

### 13.1 Scènes relationnelles

```text
TF30 — AUD+GBP vs EUR
TF15 — plusieurs blocs bas vs JPY
```

Lecture :

```text
Les batailles relationnelles ne sont pas énormes,
mais elles sont plus importantes cockpit que les coalitions seules.
```

### 13.2 Scènes de coalition

```text
TF1 — CHF+EUR / GBP+JPY
TF15 — AUD+GBP / AUD+CHF
TF30 — CHF+JPY / CHF+GBP / CAD+GBP
TF60 — AUD+CHF
```

Lecture :

```text
Le champ contient beaucoup de familles synchronisées,
mais toutes ne deviennent pas batailles complètes.
```

---

## 14. Ce que V0.2 améliore pour cockpit

Avant :

```text
liste brute de familles fortes
```

Après :

```text
vue hiérarchisée :
1. bataille relationnelle prioritaire
2. autres relations actives
3. coalitions fortes à surveiller
```

Le cockpit peut maintenant afficher :

```text
BATAILLE PRIORITAIRE
TF30 AUD+GBP vs EUR

BATAILLES SECONDAIRES
TF15 AUD+CAD vs JPY
TF15 CAD+GBP vs JPY
TF15 CHF+GBP vs JPY

FAMILLES À SURVEILLER
TF1 CHF+EUR
TF1 GBP+JPY
TF15 AUD+GBP
```

---

## 15. Limites connues

### 15.1 Pas encore TemporalDensity

Le radar ne sait pas encore si les scènes se compressent dans le temps.

Il voit :

```text
des scènes
```

mais ne mesure pas encore :

```text
la densité temporelle
la répétition rythmique
l’accélération des événements
```

### 15.2 Pas encore TemporalWindowActive

Le radar ne dit jamais :

```text
fenêtre ouverte
```

Il dit seulement :

```text
bataille en préparation
```

### 15.3 Pas encore résumé narratif multi-TF avancé

V0.2 classe les scènes.

Une future V0.3 pourrait regrouper :

```text
même antagoniste répété
même coalition répétée
même pattern entre TF
```

Exemple futur :

```text
JPY contesté plusieurs fois sur M15 par blocs bas tournants.
```

---

## 16. Commandes de référence

### Test

```bat
python test_pf_battlefield_radar_v02.py
```

### Radar global

```bat
python run_battlefield_radar_once.py --db powerflow.db --scan 240
```

### Radar ciblé

```bat
python run_battlefield_radar_once.py --db powerflow.db --timeframes 1,15,30 --scan 240
```

### JSON cockpit futur

```bat
python run_battlefield_radar_once.py --db powerflow.db --timeframes 1,5,15,30,60 --scan 240 --json
```

---

## 17. Prochaine évolution possible

Pas obligatoire maintenant.

Mais la V0.3 pourrait ajouter :

```text
grouping narratif par antagoniste
grouping narratif par coalition répétée
résumé top 3 cockpit
mode --cockpit
```

Exemple :

```text
JPY est contesté 3 fois sur M15 par des blocs bas différents.
AUD+GBP vs EUR forme la bataille prioritaire TF30.
CHF+EUR reste une coalition microfilm forte mais sans antagoniste.
```

---

## 18. Brique suivante future

Après stabilisation cockpit :

```text
pf_temporal_density.py
```

Rôle :

```text
mesurer compression / extension du temps autour des scènes radar
```

Puis seulement après :

```text
pf_temporal_window_active.py
```

Rôle :

```text
déclarer qu’une fenêtre devient active
```

---

## 19. Verdict final

```text
pf_battlefield_radar.py V0.2 = VALIDÉE
```

Elle donne à PowerFlow une vraie vue globale des batailles en préparation.

Elle ne mélange pas les responsabilités.

Elle prépare naturellement la future densité temporelle.

Fin du rapport.
