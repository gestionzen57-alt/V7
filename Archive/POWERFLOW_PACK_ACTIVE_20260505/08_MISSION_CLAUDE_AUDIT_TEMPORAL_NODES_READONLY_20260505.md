# 08 — MISSION CLAUDE 01 — AUDIT TEMPORAL NODES READ-ONLY

Date : 2026-05-05  
Statut : MISSION CIBLÉE POUR WORKSPACE CLAUDE

---

# CONTEXTE

Tu travailles sur PowerFlow V6.

PowerFlow est une extension algorithmique de perception du trader.  
Ce n’est pas une nounou, pas une tour de contrôle, pas un robot BUY/SELL.

Règles :
- capture_* écrit la DB ;
- pf_* calcule ;
- cockpit_* lit ;
- telegram_* transmet ;
- le trader décide ;
- les Temporal Nodes sont centraux, pas à enterrer.

Objectif actuel :

```text
rendre les Temporal Nodes visibles et alertables progressivement
sans casser l’architecture
```

---

# MISSION

Auditer les fichiers :

```text
pf_temporal_nodes.py
engine_temporal_nodes.py
pf_bipolar_node_alert.py
pf_temporal_density.py
pf_temporal_patterns.py
pf_temporal_patterns_cockpit.py
telegram_agentic_nodes_v01.py
```

---

# OBJECTIFS

Produire un rapport court :

```text
TEMPORAL_NODES_AUDIT_REPORT.md
```

Le rapport doit contenir :

```text
1. rôle de chaque fichier
2. fonctions principales
3. inputs
4. outputs
5. dépendances
6. écrit DB ou read-only ?
7. peut alimenter node_state.json ?
8. risques techniques
9. patch minimal recommandé
```

---

# INTERDITS

```text
ne pas modifier capture_bridge.py
ne pas modifier powerflow.db
ne pas refactor global
ne pas supprimer de fichier
ne pas brancher Telegram directement depuis pf_*
ne pas transformer Temporal Node Alert en TemporalWindowActive
```

---

# SORTIE ATTENDUE

Proposition d’une brique :

```text
pf_temporal_node_state.py
```

ou adaptation read-only existante.

Sortie cible :

```text
output/temporal_node_state.json
```

---

# FORMAT DE RÉPONSE

Répondre en 5 blocs :

```text
1. INVENTAIRE TEMPORAL
2. CE QUI EST DÉJÀ UTILISABLE
3. CE QUI EST RISQUÉ
4. PATCH MINIMAL RECOMMANDÉ
5. TESTS À LANCER
```

---

# CRITÈRE DE RÉUSSITE

La mission réussit si elle permet de décider :

```text
quel fichier lire
quel fichier garder
quel fichier patcher
comment produire temporal_node_state.json
comment préparer Telegram Node Mode
```
