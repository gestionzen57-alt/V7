# CHECKPOINT — PF Zone Dynamique Contextuelle

**Projet : PowerFlow V6 / ORION**  
**Sujet : Zones dynamiques, pullures, profils, fractalité, session**  
**Date : 2026-05-02**

---

## 1. Point d’arrêt actuel

Nous avons identifié que `pf_zone_dynamics.py` ne doit pas être traité comme un simple détecteur de seuils. C’est une brique de perception.

Son rôle actuel :

```text
Lire la respiration d’une devise en zone extrême.
Mesurer les pullures / pullbacks.
Classer la zone en ACCUMULATING, LEAKING, RUPTURE, NEUTRAL.
Calculer une tension accumulée.
```

Patch déjà fait :

```text
Ajout de PRE_EXTREME entre |Z| = 1.5 et |Z| = 2.0.
Ajout d’une tension partielle avec absorption_factor = 0.5.
```

---

## 2. Décision importante

Ne pas coder plus loin à la va-vite.

Motif : les zones dynamiques sont contextuelles. Il faut d’abord stabiliser la perception, le vocabulaire et les hypothèses.

Règle :

```text
Nommer avant de coder.
Observer avant de figer.
Mesurer avant de croire.
```

---

## 3. Notions ajoutées / à retenir

### `PRE_EXTREME`

Zone d’approche avant extrême dur.

```text
1.5 <= |Z| < 2.0
```

### `PULLURE`

Micro-respiration dans une zone. Si elle est refusée, elle charge l’élastique.

### `FRACTAL_ZONE_STACK`

Empilement de zones dynamiques sur plusieurs timeframes.

Exemple :

```text
GBP M5  : LOW_ZONE_WORK
GBP M15 : PRE_CROSS_WINDOW / PRE_EXTREME
GBP H1  : SESSION_LOW_RANK_PRESSURE
```

### `SESSION_CARRIED_TENSION`

Tension portée par une session précédente.

Exemple :

```text
GBP dernier depuis Asia.
London travaille la liquidité sur M5/M15.
Pré-US ouvre une fenêtre de rotation.
H1 commence à changer de courbe.
```

### `SESSION_RANK_MEMORY`

Mémoire du rang d’une devise pendant une session.

Loi :

```text
Une devise peut être neutre en valeur, mais extrême en rôle de session.
```

### `PRICE_WALL_FIELD`

Mur comportemental : prix bloqué pendant que les forces travaillent.

### `DISORDER_FIELD`

Champ actif mais non structuré. À nommer, pas à forcer en signal.

### `EQUILIBRIUM_FIELD`

Antagoniste énergétique de la zone extrême. Peut être mort ou vivant.

---

## 4. Architecture future pressentie

Ne pas tout mettre dans `pf_zone_dynamics.py`.

Architecture candidate :

```text
pf_zone_dynamics.py
→ respiration / pullures / tension sur une TF

pf_calibration_profiles.py
→ profils SHORT / MEDIUM / LONG + devise + session

pf_session_context.py
→ mémoire Asia / London / US, rangs, début/fin de session

pf_fractal_zone_stack.py
→ empilement de zones multi-TF

pf_zone_scene_engine.py
→ transformation en scène PowerFlow / ORION
```

---

## 5. Profils à créer plus tard

### SHORT

```text
M1 / M5
naissance
microfilm
release rapide
pièges locaux
```

### MEDIUM

```text
M15 / M30
scénario tactique
fenêtre de cross
préparation rotation
```

### LONG

```text
H1 / H4 / D1
gravité
mémoire de session
ancrage structurel
changement de courbe
```

---

## 6. Hypothèses à tester avec plus de DB

```text
1. PRE_EXTREME précède-t-il souvent EXTREME ?
2. PRE_EXTREME + pullures absorbées donne-t-il une meilleure lecture que PRE_EXTREME seul ?
3. Une devise dernière depuis Asia peut-elle charger même avec Z moyen ?
4. FRACTAL_ZONE_STACK précède-t-il mieux les rotations que M5 seul ?
5. London construit-elle souvent la liquidité avant une fenêtre pré-US ?
6. H1_CURVE_TURN confirme-t-il les releases M5/M15 ?
7. DISORDER_FIELD évite-t-il de forcer des faux signaux ?
8. PRICE_WALL_FIELD devient-il testable quand bid/spread/prix sont présents ?
```

---

## 7. Points techniques à surveiller

DB actuelle utile pour calibrage froid mais encore limitée.

À surveiller :

```text
plus de données multi-jours
plus de H4/D1
présence réelle de bid/spread
qualité des timestamps
session tagging
rang des devises par session
```

---

## 8. Phrase de reprise

Reprendre avec cette phrase :

```text
On repart de `pf_zone_dynamics.py` comme brique de respiration locale,
mais on ne code pas encore la couche complète.
On formalise d’abord les profils SHORT/MEDIUM/LONG,
la mémoire de session,
et l’empilement fractal des zones.
```

---

## 9. Prochaine action recommandée

Créer une fiche Lab pour :

```text
LAB_ZONE_001_FRACTAL_ZONE_STACK
```

et une deuxième pour :

```text
LAB_ZONE_002_SESSION_CARRIED_TENSION
```

Objectif : recueillir observations, exemples DB, captures futures et vocabulaire avant patch moteur.
