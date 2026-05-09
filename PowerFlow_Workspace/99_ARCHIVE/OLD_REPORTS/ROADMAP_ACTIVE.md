# ROADMAP_ACTIVE — POWERFLOW V6

Date : 2026-05-07  
Statut : PRIORITÉS COURTES

---

# P0 — Workspace Memory Sync

Copier ce pack dans :

```text
PowerFlow_Workspace/00_CURRENT
PowerFlow_Workspace/02_DOCS_ACTIVE/LEXIQUE_GRAMMAIRE
PowerFlow_Workspace/04_CHECKPOINTS/2026/2026-05/2026-05-07
PowerFlow_Workspace/05_MISSIONS/MISSION_ACTIVE
```

---

# P1 — Relational Gravity Bridge Guard

Fichier :

```text
pf_relational_gravity_bridge.py
```

Objectif :

```text
champ MIXED = top-level non fiable
```

---

# P2 — Audit Runtime

Tester :

```text
Kinematics
Currency Energy
Relational Gravity probe
Relational Gravity cockpit
```

---

# P3 — Behavioral Mapper

Seulement après P1.2 OK.

Ajouter :

```text
RELATIONAL_GRAVITY_MIXED_INFO
LEADER_CONFLICT_INFO
RELATIONAL_GRAVITY_ALIGNED_ALERT
```

---

# P4 — Dashboard Sync

Seulement après queue stable.

---

# P5 — Telegram

Plus tard.

Condition :

```text
plusieurs scènes validées
pas de top-level ambigu
pas de spam alertes
```
