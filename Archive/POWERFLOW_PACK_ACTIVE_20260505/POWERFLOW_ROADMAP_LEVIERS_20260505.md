# POWERFLOW_ROADMAP_LEVIERS_20260505.md

Date : 2026-05-05  
Statut : ROADMAP À LEVIER — version trader actif  
Objectif : prioriser seulement ce qui augmente la perception ou réduit la charge mentale.

---

# 0. Principe

Tu trades en même temps.

Donc la roadmap doit éviter :
- les grosses refontes ;
- les longs tunnels de documentation ;
- les agents inutiles ;
- les modules abstraits ;
- les interfaces lourdes ;
- les patchs qui n'aident pas le live.

Règle :

```text
Le nécessaire d'abord.
Le puissant ensuite.
Le confortable plus tard.
```

---

# 1. P0 — Boussole et nettoyage de contexte

## Objectif

Ne plus perdre d'énergie à se battre contre les anciens documents.

## Actions

```text
1. Valider CURRENT_STATE V2.
2. Mettre en legacy les restrictions anciennes.
3. Utiliser la classification :
   ACTIVE / À ASSOUPLIR / LEGACY / À SUPPRIMER.
4. Ne plus traiter les anciens docs comme lois.
```

## Levier

```text
Moins de confusion.
Moins de contradiction entre IA.
Moins de charge mentale.
```

---

# 2. P0 — Inventaire du répertoire core

## Objectif

Savoir ce qui existe vraiment dans le core.

## Quand

Dès que le répertoire core est fourni.

## Classification des fichiers

```text
ACTIVE_RUNTIME
ACTIVE_ENGINE
ACTIVE_COCKPIT
ACTIVE_TELEGRAM
ACTIVE_AGENTIC
LAB_ACTIVE
LAB_STANDBY
LEGACY_KEEP
QUARANTINE
UNKNOWN
```

## Sortie attendue

```text
CORE_INVENTORY_REPORT.md
```

Contenu :

```text
fichier
statut
rôle
risque
dépendances
à garder / tester / isoler / archiver
```

## Levier

```text
Le bazar devient une carte.
Pas besoin de ranger tout de suite.
D'abord comprendre.
```

---

# 3. P0 — Temporal Nodes Active Lab

## Objectif

Sortir les Temporal Nodes du faux standby restrictif.

## Pourquoi urgent

Tu veux être alerté des nodes.
Les nodes sont un organe nerveux de PowerFlow.

## Actions

```text
1. Auditer pf_temporal_nodes.py.
2. Auditer engine_temporal_nodes.py.
3. Auditer pf_bipolar_node_alert.py.
4. Identifier les events déjà calculables.
5. Créer une sortie read-only :
   node_state.json
   ou temporal_nodes_state.json.
```

## Interdits

```text
ne pas brancher brutalement dans capture_bridge.py
ne pas mélanger avec TemporalWindowActive
ne pas envoyer Telegram sans filtre
ne pas modifier DB sans spec
```

## Sortie minimale

```json
{
  "generated_at": "...",
  "symbol": "GBPUSD",
  "timeframe": "M1",
  "nodes": [
    {
      "level": "NODE_BIRTH",
      "family": "TEMPORAL_NODE",
      "confidence": "early",
      "direction_bias": "GBP pressure up / USD pressure down",
      "reason": "force shift + angle change + price lag",
      "telegram_allowed": true
    }
  ]
}
```

## Levier

```text
Tu récupères les alertes nodes sans casser le moteur.
```

---

# 4. P0 — Politique Telegram Nodes

## Objectif

Telegram doit s'adapter au trader, pas l'inverse.

## Modes recommandés

```text
TELEGRAM_NODE_MODE=OFF
TELEGRAM_NODE_MODE=WATCH
TELEGRAM_NODE_MODE=SCALPING
TELEGRAM_NODE_MODE=HOT_ONLY
```

## WATCH

```text
NODE_WATCH
NODE_BIRTH
NODE_REPULSION_CANDIDATE
```

## SCALPING

```text
FAST_NODE_BIRTH
NODE_BIRTH
NODE_REPULSION
NODE_ABSORPTION
SECOND_LEG_NODE
```

## HOT_ONLY

```text
HOT_NODE
NODE_CONFIRMED
```

## Levier

```text
Le trader choisit le niveau de bruit utile.
Le système ne censure plus par défaut.
```

---

# 5. P1 — FlowEventExtractor V0.2 ou équivalent

## Objectif

Mieux nommer les événements vivants.

## Events prioritaires

```text
FAST_BIRTH_ALERT
NODE_BIRTH
COUNTER_BREATH
ABSORPTION
WATCH_SECOND_LEG
PRICE_LAG_THEN_CATCHUP
SPREAD_FRICTION_FIELD
```

## Signature minimale FAST_BIRTH_ALERT

```text
M1 force shift
angle change
price lag
devise antagoniste active
spread non destructeur
pip_range ou volume en expansion si disponible
```

## Levier

```text
PowerFlow passe de simple lecture de champ à lecture d'événements actionnables.
```

---

# 6. P1 — Cockpit State V2 minimal

## Objectif

Une seule vérité lisible par dashboard, Telegram et IA.

## Structure minimale

```json
{
  "meta": {},
  "db_vision": {},
  "current_scene": {},
  "temporal_nodes": {},
  "flow_events": [],
  "fractal_context": {},
  "telegram": {},
  "next_watch": {}
}
```

## Levier

```text
Moins de vérité dispersée.
Moins de recalcul.
Moins de confusion cockpit / Telegram.
```

---

# 7. P1 — DBVisionGuard / Freshness Guard

## Objectif

Savoir si PowerFlow voit vraiment.

## Sorties utiles

```text
DATA_BLIND
DATA_STALE
TACTICAL_PARTIAL
TACTICAL_OK
HTF_MISSING
FULL_STACK_VISIBLE
```

## Levier

```text
Évite les lectures fortes sur données faibles.
Risque technique, pas prudence trading.
```

---

# 8. P2 — Dashboard V2

## Condition

À faire seulement après Cockpit State V2 stable.

## Objectif

Afficher moins, mais mieux.

## Éléments utiles

```text
scène dominante
node actif
next watch
mode Telegram
M1/M5/M15 tactical stack
HTF gravity
```

## Levier

```text
Réduction de charge mentale en live.
```

---

# 9. P2 — TemporalDensity micro-spec

## Objectif

Mesurer la densité temporelle sans créer un monstre.

## À faire seulement après

```text
Temporal Nodes lisibles
FlowEvents stables
Cockpit State minimal
```

## Levier

```text
Prépare TemporalWindowActive sans le précipiter.
```

---

# 10. P3 — TemporalWindowActive

## Statut

Future brique.
Pas urgence.

## Condition

```text
nodes propres
densité lisible
fractal context
event maturity
telegram policy
```

## Règle

```text
On peut alerter les nodes avant de déclarer une TemporalWindowActive.
```

---

# 11. Roadmap synthétique

```text
P0. Current State V2
P0. Core Inventory
P0. Temporal Nodes Active Lab
P0. Telegram Node Policy
P1. FlowEventExtractor V0.2
P1. Cockpit State V2 minimal
P1. DBVisionGuard / Freshness
P2. Dashboard V2
P2. TemporalDensity micro-spec
P3. TemporalWindowActive
```

---

# 12. Décision architecte

Urgence réelle :

```text
1. Ne plus perdre le contexte.
2. Retrouver les Temporal Nodes.
3. Les rendre lisibles read-only.
4. Pouvoir t'alerter sans casser l'architecture.
5. Nettoyer le core par inventaire, pas par panique.
```

Phrase finale :

```text
Le plus gros levier maintenant n'est pas de coder plus.
C'est de rendre visibles les bonnes briques sans agrandir le bazar.
```
