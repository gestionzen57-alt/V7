# PATCH LEXIQUE — ORCHESTRAL GRAVITY / INFLECTION / EXTREMA

**Date :** 2026-05-07  
**Statut :** À intégrer dans LEXIQUE_GRAMMAIRE PowerFlow V6  
**Source :** Session Claude — briques pf_force_inflection, pf_force_extrema, pf_orchestral_gravity

---

## 1. Inflection / Pliure

### PLIURE
Changement brutal d'angle d'une courbe de force à contresens de sa pente dominante.

```
Une pliure est une courbe qui se PLIE contre son propre momentum.
Pliure ≠ simple variation d'angle.
Pliure = sign flip + delta brutal.
```

### CONTRESENS_PLIURE_UP
La devise était en pente descendante, elle plie brutalement vers le haut.

```
Exemple : GBP angle -38° → +5°  (Δ+44°)
Signal : naissance de rebond possible
```

### CONTRESENS_PLIURE_DOWN
La devise était en pente montante, elle plie brutalement vers le bas.

```
Exemple : CAD angle +19° → -55°  (Δ-74°)
Signal : rupture de tendance, crash possible
```

### SAME_DIRECTION_INFLECTION
Changement d'angle fort dans le même sens (accélération ou décélération).

### Sévérité de pliure

```
MICRO      |Δ| < 20°   — visible, à surveiller
MODERATE   |Δ| 20-35°  — inflexion significative
BRUTAL     |Δ| 35-55°  — pliure forte, événement tactique
EXTREME    |Δ| > 55°   — rupture mécanique, alerter
```

---

## 2. Extrema / Valleys / Peaks

### VALLEY
Minimum local d'une courbe de force : la courbe descend, atteint un creux, remonte.

```
Qualifié si amplitude >= seuil par TF (M15=6.0, H1=8.0)
```

### PEAK
Maximum local d'une courbe de force : la courbe monte, atteint un sommet, redescend.

### AMPLITUDE
Profondeur d'un valley ou hauteur d'un peak par rapport au contexte voisin.

### ASYMÉTRIE D'ENTRÉE/SORTIE
Comparaison de la vitesse d'entrée dans l'extremum vs vitesse de sortie.

```
SLOW_ENTRY_FAST_EXIT   — énergie accumulée, libération explosive
                          Signal fort : probable continuation après le peak/valley
FAST_ENTRY_SLOW_EXIT   — impulsion puis absorption
                          Signal : mouvement amorti, possible compression
BALANCED               — entrée/sortie symétriques, pas d'avantage directionnel
FAST_ENTRY_FAST_EXIT   — passage rapide, peu d'intérêt structurel
```

---

## 3. Orchestral Gravity

### ORCHESTRAL_GRAVITY
Lecture des relations vivantes entre devises : qui mène, qui suit, qui résiste, qui se croise.

```
Orchestral Gravity ≠ signal
Orchestral Gravity ≠ Currency Energy
Orchestral Gravity = carte des rôles et relations à un moment donné
```

### LEADER (orchestral)
Devise avec l'angle le plus fort, se déplaçant en premier.

```
LEADER confirmé = angle fort + ZoneQuality ACCUMULATING ou EARLY_EXTREME
```

### FOLLOWER (orchestral)
Devise se déplaçant dans la même direction que le leader, avec retard ou force moindre.

```
attraction_strength = ratio angle / leader_angle + zone_boost
```

### ANTAGONIST (orchestral)
Devise se déplaçant en direction opposée au leader.

```
ANTAGONIST en RUPTURE = cassure mécanique, pas juste mouvement
```

### LAGGING
Devise attirée par le leader mais trop faible pour être FOLLOWER (ratio < seuil).

### COALITION_UP / COALITION_DOWN
Groupe de devises se déplaçant ensemble dans la même direction.

```
STRONG_SYNCHRO  cohésion >= 0.85 — très alignées
LOOSE_ALLIANCE  cohésion 0.60-0.85 — alignées mais pas parfaites
POLARIZED_FIELD cohésion < 0.60  — divergence interne
```

### CROSSING_ZONE
Deux devises dont les niveaux de force sont proches (distance < 8).

```
CROSSING_IMMINENT  distance < 4  — croisement imminent
CROSSING_ZONE      distance 4-8  — territoire de croisement
CONVERGING         les deux se rapprochent activement
```

### ATTRACTION_STRENGTH
Force d'attraction d'un follower vers son leader.

```
0.0 = aucune attraction
1.0 = pleinement attiré
Composé de : ratio_angle + zone_tension_boost
```

### ZONE_QUALITY (orchestral)
Qualification de la zone comportementale d'une devise.

```
Construit depuis pf_zone_dynamics.
state : ACCUMULATING / LEAKING / RUPTURE / PRE_EXTREME / EARLY_EXTREME / NEUTRAL
tension_score : 0.0 à ~15.0 (charge accumulée)
z_current : z-score comportemental actuel
```

---

## 4. Patterns orchestraux nommés

```
JPY_GRAVITY_PULLING_{X}_{Y}        JPY leader tire d'autres devises vers le haut
JPY_LEADER_ZONE_CONFIRMED          JPY leader + zone ACCUMULATING validée
LEADER_{X}_ACCUMULATING_ZONE       Leader X en zone d'accumulation — fiable
LEADER_{X}_RUPTURE_BREAKOUT        Leader X en rupture — cassure mécanique
ANTAGONIST_{X}_RUPTURE             Antagoniste X en rupture — cassure dans sens opposé
USD_CAD_SYNCHRO_DOWN_COALITION     USD et CAD chutent en synchro forte
GBP_EUR_RECOVERY_WAVE              GBP mène le rebond, EUR suit
CROSSING_IMMINENT_{A}_{B}          Croisement imminent entre A et B
BIPOLAR_FIELD_ACTIVE               Champ bipolaire actif (leaders up vs antagonistes down)
ORCHESTRAL_COMPRESSION             5+ devises neutres — compression avant mouvement
```

---

## 5. Règles de non-confusion

```
PLIURE ≠ simple variation d'angle
PLIURE = contresens brutal (sign flip + delta)

VALLEY ≠ simple baisse
VALLEY = minimum local qualifié avec contexte asymétrique

LEADER orchestral ≠ Currency Energy dominant
LEADER = angle le plus fort MAINTENANT dans cette fenêtre

ATTRACTION ≠ direction
ATTRACTION = relation de tirage entre devises

ORCHESTRAL_GRAVITY ≠ signal
ORCHESTRAL_GRAVITY = carte perceptive multi-devise
```

---

## 6. Chaîne d'intégration

```
force_snapshots (DB)
    ↓
pf_force_inflection.py      → InflectionEvent (pliures)
pf_force_extrema.py         → ExtremaEvent (valleys/peaks)
pf_orchestral_gravity.py    → OrchestraState (rôles/coalitions/patterns)
    ↓
run_orchestral_analysis_once.py  → Markdown ou JSON
    ↓
[FUTUR] cockpit_agentic_state_v01.py → bloc orchestral dans state
[FUTUR] run_orchestral_loop.py       → boucle live
[FUTUR] lab.py                       → queries orchestrales
```
