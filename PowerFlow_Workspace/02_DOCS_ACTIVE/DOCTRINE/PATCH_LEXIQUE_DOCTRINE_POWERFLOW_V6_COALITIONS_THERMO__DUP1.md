# PATCH_LEXIQUE_DOCTRINE_POWERFLOW_V6_COALITIONS_THERMO

**Projet :** PowerFlow V6  
**Document cible :** `LEXIQUE_GRAMMAIRE_COMPORTEMENTS_POWERFLOW.md`  
**Brique concernée :** Coalition / Relation thermodynamique  
**Version :** V0.3  
**Statut :** Patch lexique prêt à intégrer

---

# 1. Doctrine ajoutée — Champ collectif thermodynamique

PowerFlow ne lit plus seulement des devises isolées.

Une devise peut être :

```text
acteur individuel
```

Mais plusieurs devises peuvent former temporairement :

```text
acteur collectif
coalition comportementale
bloc de pression
famille respiratoire
```

Une coalition n’est pas une prédiction.

C’est une famille de forces qui respire ensemble.

Une relation active apparaît quand cette famille rencontre un antagoniste vivant.

Phrase noyau :

```text
Une coalition n’est pas une vérité absolue.
C’est une synchronisation temporaire de tensions, directions et respirations.
```

---

# 2. Chaîne doctrinale mise à jour

Ancienne lecture :

```text
devise
→ force
→ signal
```

Lecture PowerFlow V6 enrichie :

```text
devise
→ anomalie relative
→ respiration de zone
→ mémoire DB
→ coalition temporaire
→ antagoniste potentiel
→ relation active
→ future fenêtre temporelle
```

Chaîne moteur :

```text
pf_personalities.py
→ identité comportementale individuelle

pf_zone_dynamics.py
→ respiration de zone

pf_zone_context_logger.py
→ mémoire DB des diagnostics de zone

pf_coalitions.py
→ agrégats synchronisés de devises

pf_coalition_relations.py
→ rapport coalition vs antagoniste

run_coalition_relations_once.py
→ lecture read-only cockpit-like
```

Frontière importante :

```text
Coalition / Relation ne détecte pas encore un Temporal Node.
Coalition / Relation ne détecte pas encore la fenêtre temporelle active.
Coalition / Relation prépare le champ.
```

---

# 3. Nouveaux concepts fondamentaux

## 3.1 Currency Coalition

**Définition :**  
Groupe temporaire de devises qui présentent une tension comparable, une polarité commune et une direction temporelle compatible.

Condition minimale :

```text
même polarité
+ tension comparable
+ slope compatible
+ curvature compatible
+ respiration dans une fenêtre proche
```

Exemple :

```text
CHF+EUR
HIGH_PRESSURE_COALITION_FOLDING
```

Lecture :

```text
CHF et EUR respirent ensemble depuis le haut.
Elles forment une famille temporaire.
```

---

## 3.2 Acteur collectif

**Définition :**  
Coalition traitée comme un seul acteur de champ.

Exemple :

```text
AUD+CAD
```

peut devenir :

```text
bloc bas en respring
```

Phrase PowerFlow :

```text
AUD+CAD répondent ensemble contre JPY haut.
```

---

## 3.3 Famille respiratoire

**Définition :**  
Groupe de devises qui ne sont pas nécessairement liées par une vérité structurelle durable, mais qui respirent ensemble dans une fenêtre observable.

Exemple :

```text
CHF+EUR sur M1
```

Peut être une famille microfilm temporaire, sans valeur absolue HTF.

---

## 3.4 Antagoniste

**Définition :**  
Devise ou bloc opposé à une coalition, souvent sur polarité inverse et/ou direction contraire.

Exemple :

```text
AUD+CAD vs JPY
```

Ici :

```text
AUD+CAD = coalition basse en respring
JPY     = antagoniste haut qui plie
```

---

## 3.5 Relation active

**Définition :**  
Champ lisible où une coalition rencontre un antagoniste avec une opposition suffisante et un timing exploitable.

Relation active ne veut pas dire signal final.

Cela veut dire :

```text
le champ collectif devient lisible
```

---

## 3.6 Relation faible

**Définition :**  
Opposition partielle ou polarité présente, mais timing insuffisant.

Exemple :

```text
POLARIZED_FIELD_WITH_WEAK_TIMING
```

Lecture :

```text
les pôles existent,
mais la respiration n’est pas assez alignée.
```

---

## 3.7 Coalition forte sans antagoniste

**Définition :**  
Famille de devises très synchronisée, mais sans adversaire suffisamment lisible.

Exemple réel observé :

```text
CHF+EUR
HIGH_PRESSURE_COALITION_FOLDING
cohesion=0.94
antagonists=-
```

Lecture :

```text
la famille est propre,
mais le champ de bataille n’est pas encore complet.
```

---

# 4. Nouveaux états de coalition

## 4.1 LOW_ELASTIC_COALITION_RESPRING

Coalition située bas dans le champ, qui commence à remonter.

Forme :

```text
z_mean négatif
slope positive
tension comparable entre membres
```

Lecture :

```text
bloc bas en réponse / ressort.
```

---

## 4.2 LOW_COALITION_RISING

Coalition basse ou inférieure qui monte, mais sans extrême très chargé.

Lecture :

```text
famille basse en remontée.
```

---

## 4.3 HIGH_PRESSURE_COALITION_FOLDING

Coalition haute qui commence à plier.

Forme :

```text
z_mean positif élevé
slope négative
```

Lecture :

```text
bloc haut qui relâche / plie.
```

---

## 4.4 HIGH_PRESSURE_COALITION_EXPANDING

Coalition haute qui continue d’étendre sa pression.

Forme :

```text
z_mean positif
slope positive
```

Lecture :

```text
bloc haut en expansion.
```

---

## 4.5 HIGH_COALITION_FALLING

Coalition haute ou supérieure qui descend, mais sans forcément être en extrême fort.

Lecture :

```text
famille haute en retour.
```

---

# 5. Nouveaux états relationnels

## 5.1 LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING

Coalition basse en respring contre un antagoniste haut qui plie.

Exemple :

```text
AUD+CAD vs JPY
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
```

Lecture :

```text
le bloc bas répond pendant que l’acteur haut commence à céder.
```

---

## 5.2 HIGH_BLOCK_FOLDING_AGAINST_LOW_RESPRING

Coalition haute qui plie contre un antagoniste bas qui ressort.

Lecture :

```text
le bloc haut perd sa pression pendant que le bas répond.
```

---

## 5.3 POLARIZED_FIELD_WITH_WEAK_TIMING

Polarité présente mais timing faible.

Lecture :

```text
les côtés du champ existent,
mais la fenêtre n’est pas propre.
```

À ne pas afficher comme relation prioritaire en cockpit utile.

---

## 5.4 COALITION_VS_ANTAGONIST_OPPOSITION

Opposition générique entre coalition et antagoniste.

Lecture :

```text
champ opposé détecté,
mais pas encore typé comme respring/folding propre.
```

---

# 6. Nouveaux états de champ

## 6.1 BATTLEFIELD_WINDOW_OPENING

Le champ coalition vs antagoniste devient lisible.

Important :

```text
ce n’est pas encore TEMPORAL_WINDOW_ACTIVE.
```

C’est seulement une ouverture de champ.

---

## 6.2 FIELD_SIDE_SHIFT_ACTIVE

Champ plus avancé : le poids commence à changer de camp.

Lecture :

```text
la coalition prend ou rend la main face à l’antagoniste.
```

---

## 6.3 STRUCTURE_BUILDING

Relation existante, mais encore en construction.

Lecture :

```text
le champ existe,
mais il n’est pas encore assez dense ou assez propre.
```

---

## 6.4 POLARITY_PRESENT_TIMING_WEAK

Les pôles sont visibles, mais le timing reste insuffisant.

Lecture :

```text
ne pas confondre polarité et champ actif.
```

---

## 6.5 WEAK_FIELD_OPPOSITION

Opposition trop faible.

Lecture :

```text
information utile pour mémoire,
mais non prioritaire pour cockpit.
```

---

# 7. Scores ajoutés

## 7.1 Cohesion

Score de synchronisation interne d’une coalition.

Mesure :

```text
proximité des z_basket
+ proximité des slopes
+ proximité des curvatures
+ tags/contextes communs
```

Lecture :

```text
cohesion élevée = famille propre
cohesion basse = regroupement bruité
```

Seuil actuel :

```text
strong_cohesion = 0.75
```

Mode strict :

```text
strong_cohesion = 0.85
```

---

## 7.2 Opposition Score

Score d’opposition de polarité entre coalition et antagoniste.

Mesure :

```text
bloc d’un côté
antagoniste de l’autre
distance au centre
```

---

## 7.3 Timing Score

Score de cohérence temporelle entre coalition et antagoniste.

Mesure :

```text
slope coalition
contre
slope antagoniste
```

Une relation peut être polarisée mais faible si timing score est bas.

---

## 7.4 Field Score

Score global de relation coalition vs antagoniste.

Formule conceptuelle :

```text
field_score = opposition_score + timing_score pondérés
```

Seuil actuel :

```text
min_field_score = 0.45
```

Recommandation :

```text
observation   = 0.45
cockpit utile = 0.60
alerte future = 0.70+
```

---

# 8. Sortie cockpit-like V0.3

Le runner V0.3 sépare la lecture en trois blocs :

```text
RELATIONS ACTIVES
COALITIONS FORTES SANS RELATION ACTIVE
BRUIT / RELATIONS FAIBLES
```

## 8.1 Relations actives

Affiche uniquement les relations utiles :

```text
AUD+CAD vs JPY
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
score=0.57
```

## 8.2 Coalitions fortes

Affiche les familles propres sans antagoniste actif :

```text
CHF+EUR
HIGH_PRESSURE_COALITION_FOLDING
cohesion=0.94
```

## 8.3 Bruit masqué

Masque les relations faibles :

```text
POLARIZED_FIELD_WITH_WEAK_TIMING
score faible
```

---

# 9. Résultats observés à intégrer comme exemples

## 9.1 M1 — Famille microfilm

```text
2026-05-01 23:13
CHF+EUR
HIGH_PRESSURE_COALITION_FOLDING
cohesion=0.94
```

Lecture :

```text
CHF et EUR forment une coalition haute en folding sur microfilm M1.
```

## 9.2 M1 — Coalition haute en expansion

```text
2026-05-01 23:32
GBP+JPY
HIGH_PRESSURE_COALITION_EXPANDING
cohesion=0.90
antagonist=EUR
```

Lecture :

```text
GBP et JPY forment une coalition haute en expansion.
EUR apparaît comme antagoniste potentiel,
mais la relation n’est pas encore active au seuil strict.
```

## 9.3 M15 — Relation active faible/moyenne

```text
2026-05-01 08:15
AUD+CAD vs JPY
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
score=0.57
```

Lecture :

```text
AUD+CAD forment un bloc bas en respring.
JPY agit comme antagoniste haut qui plie.
Le champ est en construction.
```

---

# 10. Règles de non-confusion

## 10.1 Coalition n’est pas Temporal Node

Une coalition peut exister sans node temporel.

```text
coalition = famille qui respire ensemble
node      = événement temporel de convergence / répulsion / cassure
```

## 10.2 Battlefield Window Opening n’est pas Temporal Window Active

```text
BATTLEFIELD_WINDOW_OPENING
= champ relationnel lisible

TEMPORAL_WINDOW_ACTIVE
= future brique multi-paramètres à part
```

## 10.3 Cohesion n’est pas signal

Une forte cohésion ne déclenche rien seule.

Elle dit seulement :

```text
famille propre détectée
```

## 10.4 Antagonist Candidate n’est pas relation active

Un antagoniste potentiel peut exister sans timing suffisant.

Il faut distinguer :

```text
antagonist candidate
relation active
```

---

# 11. Emplacement recommandé dans le lexique principal

À intégrer après les sections :

```text
Acteurs fondamentaux
Leader / Follower
Coalition
Opposition / Relations
```

ou créer une nouvelle section :

```text
1.X — Coalitions thermodynamiques et relations collectives
```

---

# 12. Phrase noyau à ajouter

```text
PowerFlow ne lit pas seulement des devises.
Il lit des familles temporaires de forces.
Une coalition apparaît quand plusieurs devises respirent ensemble.
Une relation active apparaît quand cette famille rencontre un antagoniste vivant.
```

---

# 13. Briques futures liées

À documenter mais ne pas intégrer au moteur actuel :

```text
pf_temporal_window_active.py
→ fenêtre temporelle active

pf_net_energy.py
→ énergie nette

pf_dissipation.py
→ dissipation / annulation

pf_friction.py
→ friction adverse

pf_coalition_context_logger.py
→ mémoire DB des coalitions
```

---

# 14. Statut final

```text
Lexique coalition/relation thermodynamique V0.3 = prêt à intégrer.
```

Fin du patch lexique.
