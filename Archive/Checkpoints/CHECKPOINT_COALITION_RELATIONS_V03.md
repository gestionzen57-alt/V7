# CHECKPOINT_COALITION_RELATIONS_V03

**Projet :** PowerFlow V6  
**Brique :** Coalition / Relation thermodynamique  
**Version validée :** V0.3  
**Statut :** VALIDÉE — lecture propre, read-only, cockpit-like

---

## 1. Résumé court

La brique coalition/relation est maintenant opérationnelle.

Elle permet de passer de :

```text
devise isolée
→ respiration de zone
→ coalition temporaire
→ relation coalition vs antagoniste
```

à une lecture plus organique :

```text
CHF+EUR respirent ensemble depuis le haut
GBP+JPY forment une coalition haute en expansion
AUD+CAD répondent contre JPY haut sur M15
```

La brique ne détecte pas encore la fenêtre temporelle active.  
Elle prépare seulement le champ de bataille.

---

## 2. Fichiers validés

```text
pf_coalitions.py
test_pf_coalitions_v01.py

pf_coalition_relations.py
test_pf_coalition_relations_v01.py

pf_zone_context_logger.py         V0.1.1 actif
run_zone_context_logger_once.py   V0.1.1 actif

run_coalition_relations_once.py   V0.3 actif
test_run_coalition_relations_once_v03.py
```

---

## 3. Pipeline actif

```text
force_snapshots
→ run_zone_context_logger_once.py
→ zone_diagnostics

zone_diagnostics
→ run_coalition_relations_once.py
→ vectors devise
→ pf_coalitions.py
→ pf_coalition_relations.py
→ lecture cockpit-like
```

---

## 4. Commandes Windows validées

### Logger zone context

```bat
python run_zone_context_logger_once.py --db powerflow.db --replace --summary
```

Sortie attendue validée :

```text
OK logged/kept 35 zone diagnostics into powerflow.db [mode=basket]
```

### Dernier état M1

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

### Mode strict cockpit

```bat
python run_coalition_relations_once.py --db powerflow.db --timeframe 1 --scan 240 --min-field-score 0.60 --strong-cohesion 0.85
```

---

## 5. Résultats observés

### Dernier M1 — 23:56

```text
Aucun champ coalition utile au seuil courant.
```

Lecture :

```text
Le moteur ne force pas une coalition artificielle.
Il y a du mouvement individuel, mais pas de famille nette.
```

### Scan M1

Coalitions fortes détectées :

```text
23:13 — CHF+EUR
HIGH_PRESSURE_COALITION_FOLDING
cohesion=0.94

23:32 — GBP+JPY
HIGH_PRESSURE_COALITION_EXPANDING
cohesion=0.90
antagonist=EUR
```

Lecture :

```text
M1 montre des familles microfilm.
Pas encore forcément un champ de bataille actif.
```

### Scan M15

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
Plusieurs coalitions basses répondent contre lui.
Le champ M15 produit des relations actives faibles/moyennes.
```

---

## 6. Seuils actuels

```text
min_field_score = 0.45
strong_cohesion = 0.75
```

Recommandation :

```text
mode observation   : min_field_score 0.45
mode cockpit utile : min_field_score 0.60
mode alerte future : min_field_score 0.70+
```

---

## 7. Frontières verrouillées

Cette brique :

```text
- lit les diagnostics existants
- reconstruit slope / curvature depuis z_current historique
- détecte coalitions
- qualifie coalition vs antagoniste
- affiche relation active / coalition forte / bruit masqué
```

Elle ne fait pas :

```text
- pas de calcul force_snapshots brut
- pas de décision de trading
- pas de Telegram
- pas d’écriture DB
- pas de temporal node
- pas de fenêtre temporelle active
- pas d’énergie nette
- pas de dissipation / friction
```

---

## 8. Briques futures

À ne pas mélanger maintenant :

```text
pf_temporal_window_active.py
→ future fenêtre temporelle active

pf_net_energy.py
→ énergie nette

pf_dissipation.py
→ dissipation / annulation

pf_friction.py
→ friction adverse

pf_coalition_context_logger.py
→ mémoire DB des coalitions, plus tard seulement
```

---

## 9. Verdict

```text
Brique coalition/relation thermodynamique V0.3 = VALIDÉE
```

Elle transforme la perception PowerFlow :

```text
devises individuelles
→ familles temporaires
→ champ coalition vs antagoniste
```

Fin du checkpoint.
