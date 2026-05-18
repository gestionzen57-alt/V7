# DELTARIVER → POWERFLOW B9 — COMPARAISON V1 / V2

**Projet :** PowerFlow V7.6.7 / T009 Battlefield Flux  
**Date :** 2026-05-16  
**Fichiers comparés :**

```text
V1 : Docs/Reports/DELTARIVER_TO_POWERFLOW_B9_MAPPING.md initial
V2 : Docs/Reports/DELTARIVER_TO_POWERFLOW_B9_MAPPING.md enrichi transcriptions
```

---

## 1. Résumé court

```text
V1 = cartographie initiale utile.
V2 = base de spécification B9.
```

La V1 reposait surtout sur les sources publiques DeltaRiver disponibles et le handoff T009/B9. Elle posait les concepts généraux : clusters, delta, absorption, imbalance, trap, profil local, raw tick vs M1 proxy.

La V2 intègre six transcriptions vidéo fournies par l'utilisateur. Elle ajoute une vraie grammaire de lecture : effort/résultat, fuel/brake, delta sans progression, mouvement comme squelette, POC/VAH/VAL comme mémoire de zone, wick rejection, projection decay, squeeze→break→retest, event→moment gate.

---

## 2. Ce que V1 faisait bien

```text
- Positionner B9 comme Microfilm Battlefield Memory.
- Séparer B9 de B8.
- Refuser la copie de DeltaRiver.
- Lister les concepts footprint utiles.
- Séparer raw tick et M1_BAR_PROXY.
- Identifier les markers T009 existants.
```

V1 était suffisante pour ouvrir le sujet.

---

## 3. Ce que V1 ne pouvait pas encore faire

```text
- Détailler la logique effort/résultat.
- Expliquer fuel vs brake.
- Formaliser braking bar / impulse bar.
- Décrire delta zero-cross et delta sans progression.
- Traduire POC / VAH / VAL en zone_center / zone_high / zone_low.
- Ajouter movement skeleton / projection decay / wick ratio.
- Créer un gate event→moment.
- Proposer une priorité Sequence Summarizer.
```

---

## 4. Apports majeurs de V2

### 4.1 Effort / résultat

```text
effort = volume / delta / pression / densité
résultat = déplacement / clôture / migration centre / renouvellement extrême
```

### 4.2 Volume comme fuel ou brake

```text
volume haut + déplacement haut = fuel / impulse
volume haut + déplacement faible = brake / absorption
```

### 4.3 Zone mémoire

```text
POC → zone_center
VAH → zone_high
VAL → zone_low
```

### 4.4 Event → moment

```text
event brut + contexte + résultat prix + data visibility = moment B9
```

### 4.5 Nouveaux risques techniques

```text
NORMALIZATION_WINDOW_DRIFT
M1_PROXY_OVERCLAIM
SINGLE_BAR_FALSE_POSITIVE
BROKER_FEED_BIAS
RETEST_TOO_FAST_FOR_M1_PROXY
```

---

## 5. Nouveaux markers V2

```text
B9_EFFORT_RESULT_ALIGNMENT
B9_VOLUME_AS_FUEL
B9_VOLUME_AS_BRAKE
B9_WICK_CLUSTER_REJECTION
B9_DELTA_ZERO_CROSS_IN_ZONE
B9_SQUEEZE_TO_LEVEL
B9_BREAK_RETEST_ESCAPE
B9_PROJECTION_DECAY
B9_MOVEMENT_SKELETON
B9_VISIBLE_WINDOW_RELATIVITY
B9_SYMBOL_SPECIFIC_CALIBRATION
```

---

## 6. Nouveaux moments T009 proposés V2

```text
T009_MOMENT_BREAK_RETEST
T009_MOMENT_BREAK_RETEST_FAILED
T009_MOMENT_RETURN_TO_POC
T009_MOMENT_VALUE_AREA_BREAK
T009_MOMENT_VALUE_AREA_REINTEGRATION
T009_MOMENT_LEVEL_INTERACTION
T009_MOMENT_RETEST_HOLDS_STRUCTURE
T009_MOMENT_STRUCTURE_PRESERVED
T009_MOMENT_BATTLE_LEVEL_CONFIRMED
T009_MOMENT_WICK_VOLUME_REJECTION
T009_MOMENT_PROJECTION_DECAY
T009_MOMENT_RETRACE_STRESS
T009_MOMENT_EFFORT_WITHOUT_RESULT
```

---

## 7. Verdict

```text
La V2 remplace la V1.
La V1 reste l'historique initial.
La V2 est le document à transmettre à Claude / architecte.
```

Prochain geste recommandé :

```text
Coder seulement un Sequence Summarizer V0 read-only.
Pas de gros module.
Pas de croisement B8 prématuré.
```
