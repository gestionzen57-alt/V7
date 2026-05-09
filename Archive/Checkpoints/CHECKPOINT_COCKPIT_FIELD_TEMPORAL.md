# CHECKPOINT_COCKPIT_FIELD_TEMPORAL.md

Date checkpoint : 2026-05-02 23:22 UTC  
Projet : PowerFlow V6   
Brique : Cockpit Field + Temporal Patterns  
Statut : **VALIDÉ EN CORE**

---

## 1. Objectif du checkpoint

Ce checkpoint fige l'intégration réussie du bloc `TEMPORAL_PATTERNS` dans le cockpit principal PowerFlow.

L'objectif était de ne plus avoir seulement une carte des batailles structurelles, mais un cockpit capable de lire simultanément :

```text
BATTLEFIELD MAP
+
BIPOLAR FIELD
+
TEMPORAL PATTERNS
```

Le cockpit doit maintenant percevoir les zones d'intérêt stratégiques temporelles où une fenêtre peut s'ouvrir, avec lecture des batailles en préparation, releases tactiques, contradictions micro/HTF, respirations, pullures absorbées, densité temporelle et alignements angulaires.

---

## 2. Commande validée

Commande exécutée avec succès dans le Core :

```powershell
python run_cockpit_field.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --recent-minutes 180 --max-gap-minutes 90 --cluster-gap-minutes 60 --cluster-mode side --max-lines 6 --out cockpit_field.txt
```

Résultat :

```text
OK wrote cockpit field: cockpit_field.txt
```

---

## 3. Sortie cockpit validée

Sortie validée :

```text
COCKPIT FIELD
========================================================================
FIELD: TACTICAL_RELEASE_BATTLEFIELD | session=LATE_US | score=257.063
DOMINANT: TACTICAL_RELEASE_BATTLEFIELD: release=CAD HIGH/GBP HIGH | prep=EUR HIGH/CHF HIGH/AUD HIGH/JPY HIGH | HIGH=CAD/GBP/EUR/CHF/AUD/JPY | LOW=-
OPPOSITE/CONTEXT: HTF_PREPARATION_FIELD: prep=EUR LOW/GBP LOW/CHF LOW/CAD LOW/JPY LOW | HIGH=- | LOW=EUR/GBP/CHF/CAD/JPY
CONTESTED_WINDOW: HIGH=CAD/GBP/EUR/CHF/AUD/JPY vs LOW=EUR/GBP/CHF/CAD/JPY | BIPOLAR_CONTESTED_RELEASE_WINDOW
BIPOLAR_FOCUS: EUR | MICRO_VS_HTF_ROTATION_CONTEST | HIGH_TF=M1,M5 vs LOW_TF=M15,M30
BIPOLAR_LIST: EUR:PREPH/PREPL | GBP:RELH/PREPL | CAD:RELH/PREPL | CHF:PREPH/PREPL

TEMPORAL_PATTERNS:
BREATHING: USD M1 LOW PULLURE_ABSORPTION_FIELD score=12.595 energy=5.745 pullures=7 comp=209 | 2026-05-01T21:41:00+00:00 -> 2026-05-01T22:01:00+00:00
PULLURE: USD M1 LOW score=12.595 pullures=7 energy=5.745 | 2026-05-01T21:41:00+00:00 -> 2026-05-01T22:01:00+00:00
DENSITY: EUR M30 TEMPORAL_DENSITY_FIELD score=5.679 density=4.379 cutoff=2.882 | 2026-05-01T23:00:00+00:00
ANGLE: CHF,EUR,GBP M1 ANGULAR_ALIGNMENT_NODE score=9.180 angle=-78.22 q=0.843 changes=1 | 2026-05-01T21:30:00+00:00
TEMPORAL_TARGETS: USD/M1/LOW/PULLURE_ABSORPTION_FIELD/score=12.59 | CHF/M1/HIGH/PULLURE_ABSORPTION_FIELD/score=11.88 | AUD/M1/LOW/EXTREME_BREATHING_FIELD/score=10.24 | EUR/M1/HIGH/EXTREME_BREATHING_FIELD/score=9.58 | JPY/M5/HIGH/EXTREME_BREATHING_FIELD/score=9.45 | CHF,EUR,GBP/M1/ANGLE/score=9.18
TEMPORAL_ROWS: M1=181 | M5=37 | M15=13 | M30=7 | H1=4
```

---

## 4. Fichiers validés

Fichiers Core impliqués :

```text
run_cockpit_field.py
pf_cockpit_field.py
pf_temporal_patterns_cockpit.py
pf_temporal_patterns.py
pf_battlefield_map.py
```

Rôle de chaque fichier :

| Fichier | Rôle |
|---|---|
| `run_cockpit_field.py` | Runner wrapper du cockpit principal |
| `pf_cockpit_field.py` | Moteur de synthèse cockpit |
| `pf_temporal_patterns_cockpit.py` | Plug-in cockpit pour respiration / pullures / densité / angle |
| `pf_temporal_patterns.py` | Détecteurs mathématiques temporal patterns |
| `pf_battlefield_map.py` | Carte globale des batailles, coalitions, contests, bipolar fields |

---

## 5. Corrections effectuées

### 5.1 Correction `pf_cockpit_field.py`

Problème rencontré :

```text
SyntaxError: from __future__ imports must occur at the beginning of the file
```

Cause :

```python
from pf_temporal_patterns_cockpit import build_temporal_patterns_cockpit
from __future__ import annotations
```

Correction :

```python
from __future__ import annotations

import argparse
...
from pf_temporal_patterns_cockpit import build_temporal_patterns_cockpit
```

### 5.2 Correction `pf_temporal_patterns_cockpit.py`

Problème rencontré :

```text
SyntaxError: from __future__ imports must occur at the beginning of the file
```

Cause probable :

```python
from pf_temporal_patterns_cockpit import build_temporal_patterns_cockpit
from __future__ import annotations
```

Correction :
- suppression de l'auto-import parasite ;
- repositionnement de `from __future__ import annotations` juste après le docstring.

---

## 6. Architecture validée

Architecture actuelle :

```text
force_snapshots
      ↓
pf_temporal_patterns.py
      ↓
pf_temporal_patterns_cockpit.py
      ↓
pf_cockpit_field.py
      ↓
run_cockpit_field.py
      ↓
cockpit_field.txt
```

Le flux reste propre :

```text
Acquisition DB
→ Calcul mathématique
→ Synthèse cockpit
→ Affichage texte compact
```

Aucune écriture DB n'est réalisée par le bloc `TEMPORAL_PATTERNS`.

---

## 7. Lecture validée du cockpit

Le cockpit voit :

```text
FIELD = TACTICAL_RELEASE_BATTLEFIELD
```

Cela indique une release visible côté micro/tactique.

Il voit aussi :

```text
OPPOSITE/CONTEXT = HTF_PREPARATION_FIELD
```

Cela indique une scène HTF opposée ou porteuse en préparation.

Le focus bipolaire validé :

```text
EUR | MICRO_VS_HTF_ROTATION_CONTEST | HIGH_TF=M1,M5 vs LOW_TF=M15,M30
```

Lecture PowerFlow :

```text
Microfilm HIGH en release
contre
préparation HTF LOW
```

C'est une lecture conforme à la doctrine fractale PowerFlow :
- M1/M5 = microfilm / naissance / release locale ;
- M15/M30/H1 = scénario / champ de bataille supérieur ;
- le cockpit ne tranche pas, il expose la tension et la contradiction.

---

## 8. Temporal Patterns validé

Bloc validé :

```text
BREATHING: USD M1 LOW PULLURE_ABSORPTION_FIELD
PULLURE: USD M1 LOW
DENSITY: EUR M30 TEMPORAL_DENSITY_FIELD
ANGLE: CHF,EUR,GBP M1 ANGULAR_ALIGNMENT_NODE
```

Lecture PowerFlow :

```text
USD absorbe en bas sur M1.
EUR porte une densité temporelle M30.
CHF/EUR/GBP changent d'angle ensemble en M1.
La scène est contestée entre release tactique et préparation HTF.
```

---

## 9. Nouveaux éléments consolidés

### 9.1 `TEMPORAL_PATTERNS`

Bloc cockpit qui condense :
- respiration de zone extrême ;
- pullures absorbées ;
- densité temporelle ;
- alignement angulaire.

### 9.2 `PULLURE_ABSORPTION_FIELD`

Zone où la devise tente de sortir d'un champ extrême ou semi-extrême, mais où les tentatives sont absorbées.

Signature :
- pullures > 0 ;
- compressions internes élevées ;
- énergie maintenue ;
- champ encore actif.

### 9.3 `TEMPORAL_DENSITY_FIELD`

Champ où la vitesse de variation par barre est élevée.

Formule de base :

```text
densité = somme(abs(delta_force)) / fenêtre
```

Rôle :
- distinguer les compressions rapides des phases lentes ;
- signaler les zones où le flux accélère ;
- capter les micro-inflexions sans lissage retardateur.

### 9.4 `ANGULAR_ALIGNMENT_NODE`

Node où plusieurs devises prennent un angle commun ou proche.

Rôle :
- détecter une convergence d'intention ;
- repérer les changements d'inclinaison collectifs ;
- enrichir le cockpit avec une lecture de synchronisation.

### 9.5 `SAME_ANGLE_INTENTION_NODE`

Version plus forte de l'alignement angulaire :
- qualité élevée ;
- changements de direction simultanés ;
- plusieurs devises alignées.

### 9.6 `MICRO_VS_HTF_ROTATION_CONTEST`

Conflit fractal :
- microfilm M1/M5 pousse dans un sens ;
- scène M15/M30/H1 prépare ou porte l'autre côté.

C'est un concept clé pour la lecture PowerFlow.

---

## 10. Doctrine validée

La brique respecte la doctrine PowerFlow :

```text
Voir vite.
Calculer la tension.
Nommer le champ.
Ne pas retenir l'information.
Ne pas transformer le cockpit en usine à bruit.
```

Le cockpit n'est pas un conseiller.
Il est un champ de perception.

---

## 11. Statut technique

```text
run_cockpit_field.py                OK
pf_cockpit_field.py                 OK
pf_temporal_patterns_cockpit.py     OK
pf_temporal_patterns.py             OK
cockpit_field.txt                   OK
```

Verdict :

```text
COCKPIT FIELD + TEMPORAL PATTERNS = VALIDÉ
```

---
