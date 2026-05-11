# LEXIQUE GRAMMAIRE — PATCH POST-P0 PowerFlow V7.2
**Date : 2026-05-11 | Version : 0.9.1 | Statut : PRODUCTION — TERMES ATTESTÉS P0**

---

## INTRODUCTION

Ce patch ajoute les termes apparus pendant la mission P0 live recovery. Il ne remplace pas le lexique V7.2 existant : il l'étend.

Objectif : nommer précisément les états observés en production, distinguer `PENDING_DATA_WINDOW` d'un vrai FAIL, et éviter les faux négatifs sur `dominant_period_bars = 1` quand le flux est vivant.

---

## SECTION 19 — NOUVEAUX TERMES POST-P0

### LAG1_COMPRESSION

```text
Domaine : B4 Temporal Density
Définition :
  dominant_period_bars = 1
  + variance vivante
  + unique_count élevé
  + Data Quality PASS
  = compression ultra-courte mais réelle.

Distinction :
  LAG1_COMPRESSION ≠ STATIC_SIGNATURE.

Cas vivant :
  dominant_period_bars = 1
  std > 10
  unique_count >= 20
  stale = false
  gaps = 0
  → PASS_ALIVE / LAG1_COMPRESSION

Cas mort :
  dominant_period_bars = 1
  std ≈ 0
  unique_count faible
  données figées
  → STATIC_SIGNATURE

Sémantique :
  Période dominante courte, flux réel compressé, inflexion naissante visible en lag1.
```

### PENDING_DATA_WINDOW

```text
Domaine : P0 Validation / market_open_validator
Définition :
  Briques actives et vivantes
  + fenêtre statistique insuffisante pour PASS strict
  = attente d'accumulation de données fraîches.

N'est pas :
  FAIL moteur
  FAIL stale data
  FAIL static signature

Contexte :
  market_open_validator peut retourner INSUFFICIENT_DATA.
  Si B4/B5/Node respirent, requalification correcte = PENDING_DATA_WINDOW.

Progression naturelle :
  TF1  : 25 → 50 → 100+ rows
  TF5  : 6  → 20 → 50+ rows
  TF15 : 2  → 10 → 30+ rows
```

### PASS_CORE_PARTIAL_STRICT

```text
Domaine : verdict P0 multi-axes
Définition :
  Core perception = PASS
  Dashboard flow  = PASS
  Strict full     = PENDING_DATA_WINDOW

Usage :
  Statut final P0 post-recovery.

Lecture :
  GO perception live, strict statistique en accumulation.
```

### PASS_ALIVE

```text
Domaine : Validateurs / briques critiques
Définition :
  Brique moteur opérationnelle
  + produit des états non figés
  + variance réelle mesurable
  + labels ou rho changeants selon contexte.

Exemples :
  B4 PASS_ALIVE = compression active + dominant_period vivant.
  B5 PASS_ALIVE = rho non figés + divergences présentes.

Opposés :
  STATIC_OUTPUT
  FAIL_MOTEUR
  PASSIVE_WATCH
```

### PASS_ENGINE / SILENT_STATE

```text
Domaine : B7 Fractal Resonance / moteurs d'état
Définition :
  Le moteur fonctionne et produit un état valide.
  L'état peut être SILENT sans que le moteur soit cassé.

Exemple :
  B7_FRACTAL_RESONANCE = PASS_ENGINE / SILENT_STATE
  = moteur opérationnel, pas de résonance actuelle.

Lecture :
  SILENT est un état du flux, pas un échec.
```

### PASS_DRY_RUN

```text
Domaine : runners / daemons
Définition :
  Runner testé en --dry-run.
  Contrat CLI validé.
  Aucun effet persistant écrit.
  Prêt à activation réelle.

Exemple :
  run_confluence_alert.py --dry-run = PASS_DRY_RUN.
```

### ACTIVE_COMPRESSION

```text
Domaine : B4 Temporal Density / dynamique marché
Définition :
  Compression réelle en cours, mesurée simultanément sur plusieurs devises/TF.
  Typiquement 17-19 devises/TF en CYCLE_COMPRESSING.
  compression_ratio proche ou supérieur à 0.93.

Sémantique :
  Signal d'attention marché.
  Pré-rupture possible.
  Accumulation d'énergie.
  Pas une panne.
```

### SPEARMAN_GRAVITY_ACTIVE

```text
Domaine : B5 Spearman Gravity
Définition :
  B5 produit des corrélations vivantes.
  rho non figés, labels alternants, divergences mesurées.

États possibles :
  SYNCHRO
  DIVERGENT
  NEUTRAL
  CODEPENDANT_EXTREME
  DIVERGENT_EXTREME
  MIXED_PROBABILISTE

Sémantique :
  Relation probabiliste réelle entre devises.
  Opposé : SPEARMAN_STATIC.
```

### TAIL_EXTREME

```text
Domaine : B5 Spearman Gravity
Définition :
  Paire en dépendance structurelle extrême.

Critères :
  rho > 0.85  → CODEPENDANT_EXTREME
  rho < -0.85 → DIVERGENT_EXTREME

Sémantique :
  Forte liaison ou forte opposition.
  À surveiller pour changement de phase.
```

### HOT_NODE

```text
Domaine : Temporal Node State
Définition :
  Nœud temporel au niveau prioritaire HOT.

Caractéristiques :
  highest_level = HOT_NODE
  level = HOT
  fractal_state = LTF_NODE_INSIDE_HTF_BATTLE_FIELD
  confluence M1/M5/M15 mesurable

Sémantique :
  Nœud actif majeur.
  Attention immédiate du trader.
```

### M1_MICRO_NODE_BIRTH

```text
Domaine : Temporal Node State / chronologie événementielle
Définition :
  Première détection d'un nœud sur M1.
  État de naissance : BIRTH.
  Relais M5 attendu dans les minutes suivantes.

Sémantique :
  Ignition / inflexion naissante.
  Alerte précoce à exposer, jamais à censurer.
```

### DATA_QUALITY_LTF_PASS

```text
Domaine : Data Quality Guard
Définition :
  Fenêtre LTF propre pour TF1/TF5/TF15.

Critères P0 :
  TF1  >= 25 rows
  TF5  >= 6 rows
  TF15 >= 2 rows
  stale = false
  gaps = 0

Sémantique :
  Capture LTF fiable pour B4/B5/Node.
  Briques autorisées à respirer normalement.
```

---

## SECTION 20 — REDÉFINITIONS POST-P0

### INSUFFICIENT_DATA → PENDING_DATA_WINDOW

```text
Ancien terme : INSUFFICIENT_DATA
Problème : ambigu — peut être lu comme FAIL.

Nouvelle lecture :
  Si briques ALIVE + fenêtre trop courte : PENDING_DATA_WINDOW.
  Si variance zéro / données figées : FAIL_STATIC_SIGNATURE.
  Si donnée ancienne : FAIL_STALE_DATA.

Impact :
  market_open_validator mesure la fenêtre, il ne condamne pas le moteur quand le flux respire.
```

### dominant_period_bars = 1 → LAG1_COMPRESSION ou STATIC_SIGNATURE

```text
Ancienne règle :
  dominant_period_bars = 1 → FAIL.

Nouvelle règle :
  dominant_period_bars = 1
  + variance vivante
  + unique_count élevé
  + Data Quality PASS
  → LAG1_COMPRESSION.

  dominant_period_bars = 1
  + variance quasi nulle
  + répétition morte
  → STATIC_SIGNATURE.

Impact :
  Moins de faux FAIL.
  Distinction propre entre lag1 vivant et signal figé.
```

---

## SECTION 21 — CLARIFICATIONS D'ÉTATS OBSERVÉS

### EIE_NEUTRAL ≠ EIE_STATIC_OUTPUT

```text
EIE_NEUTRAL :
  Zone neutre actuelle, pas de tension élastique active.
  État normal possible.

EIE_STATIC_OUTPUT :
  EIE produit toujours NEUTRAL sans capacité de changement.
  Output figé.
  Panne moteur.
```

### COMPRESSION_ALERT vs CYCLE_COMPRESSING

```text
CYCLE_COMPRESSING :
  État d'une devise sur un TF.

COMPRESSION_ALERT :
  État systémique.
  Plusieurs devises/TF comprimées simultanément.
```

### PASS vs PASS_ALIVE vs PASS_DRY_RUN

```text
PASS :
  État nominal.

PASS_ALIVE :
  État nominal + preuve de vie / variance réelle.

PASS_DRY_RUN :
  Contrat runner validé sans effet persistant.
```

---

## SECTION 22 — TABLEAU RÉCAPITULATIF

| Terme | Domaine | Type | Statut |
|---|---|---|---|
| LAG1_COMPRESSION | B4 | État | PROD |
| PENDING_DATA_WINDOW | P0 Validation | Verdict | PROD |
| PASS_CORE_PARTIAL_STRICT | P0 Validation | Verdict | PROD |
| PASS_ALIVE | Moteur | Verdict | PROD |
| PASS_ENGINE | Moteur | Verdict | PROD |
| PASS_DRY_RUN | Runner | Verdict | PROD |
| ACTIVE_COMPRESSION | Marché | État | PROD |
| SPEARMAN_GRAVITY_ACTIVE | B5 | État | PROD |
| TAIL_EXTREME | B5 | État | PROD |
| HOT_NODE | Node | Priorité | PROD |
| M1_MICRO_NODE_BIRTH | Node | Événement | PROD |
| DATA_QUALITY_LTF_PASS | Guard | Verdict | PROD |

---

## CONSERVATION ORIGINALE

Tous les termes existants de `LEXIQUE_GRAMMAIRE_V7.md` restent valides. Ce patch ajoute les sections post-P0 sans supprimer la grammaire V7.2.

---

*LEXIQUE_GRAMMAIRE_V7_PATCH_POST_P0.md — Version 0.9.1 — 2026-05-11*
