# PATCH_LEXIQUE_DOCTRINE_POWERFLOW_V6_BATTLEFIELD_RADAR_V02

**Projet :** PowerFlow V6  
**Brique :** Battlefield Radar  
**Version :** V0.2  
**Statut :** Patch lexique/doctrine prêt à intégrer

---

## 1. Nouveau concept : Battlefield Radar

**Définition :**  
Brique cockpit qui agrège les coalitions et relations actives pour repérer les scènes d’intérêt stratégique.

Phrase noyau :

```text
BattlefieldRadar ne dit pas “la fenêtre est ouverte”.
Il dit “ici, une bataille se prépare”.
```

---

## 2. Place dans la grammaire PowerFlow

```text
acteur individuel
→ respiration de zone
→ coalition
→ relation coalition vs antagoniste
→ scène d’intérêt radar
→ densité temporelle future
→ fenêtre active future
```

---

## 3. Scène d’intérêt stratégique

**Définition :**  
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

---

## 4. BATAILLE EN PRÉPARATION

**Définition :**  
Une coalition rencontre ou commence à rencontrer un antagoniste.

Exemple :

```text
AUD+CAD vs JPY
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
```

Lecture :

```text
un bloc bas répond contre un antagoniste haut.
```

---

## 5. Relation active prioritaire

Doctrine V0.2 :

```text
Relation active moyenne > coalition isolée forte
```

Raison :

```text
relation active = coalition + antagoniste + opposition de champ
coalition forte = famille synchronisée mais bataille incomplète
```

---

## 6. Coalition forte à surveiller

**Définition :**  
Famille synchronisée qui mérite attention cockpit, mais dont l’antagoniste est absent ou pas assez propre.

Exemple :

```text
CHF+EUR
HIGH_PRESSURE_COALITION_FOLDING
cohesion=0.94
```

Lecture :

```text
famille très propre,
mais bataille incomplète.
```

---

## 7. États BattlefieldRadar

```text
BATTLE_WATCH
BATTLE_PREPARING
BATTLE_FORMING
BATTLE_PRESSURIZED
COALITION_FIELD_WATCH
COALITION_FIELD_VISIBLE
COALITION_FIELD_STRONG
```

---

## 8. Types de scènes

```text
RELATION_ACTIVE
COALITION_STRONG
```

---

## 9. Strategic Score

**Définition :**  
Score de tri cockpit propre au radar.

Il ne remplace pas :

```text
field_score
cohesion
context_score
```

Il sert seulement à classer les scènes dans le cockpit.

Règle :

```text
relations actives d’abord
coalitions fortes ensuite
```

---

## 10. Exemple intégré

```text
TF30 AUD+GBP vs EUR
BATTLE_FORMING
field=0.60
```

Lecture :

```text
bataille relationnelle prioritaire.
AUD+GBP forment un bloc.
EUR agit comme antagoniste.
```

---

## 11. Exemple coalition seule

```text
TF1 CHF+EUR
COALITION_FIELD_STRONG
HIGH_PRESSURE_COALITION_FOLDING
cohesion=0.94
```

Lecture :

```text
coalition très forte,
mais sans relation active complète.
```

---

## 12. Règles de non-confusion

```text
BattlefieldRadar ≠ TemporalDensity
BattlefieldRadar ≠ TemporalWindowActive
Scène d’intérêt ≠ signal
Coalition forte ≠ bataille complète
Relation active ≠ fenêtre ouverte
```

---

## 13. Phrase à ajouter au lexique

```text
Le radar de champ ne prédit pas.
Il hiérarchise les scènes où PowerFlow doit regarder.
```

---

## 14. Suite future

```text
pf_temporal_density.py
→ mesurera si les scènes radar se compressent dans le temps

pf_temporal_window_active.py
→ déclarera plus tard une fenêtre active
```

Fin du patch lexique.
