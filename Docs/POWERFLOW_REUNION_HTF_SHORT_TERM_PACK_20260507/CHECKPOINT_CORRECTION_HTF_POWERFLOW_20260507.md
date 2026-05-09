# CHECKPOINT — CORRECTION HTF / COURT TERME POWERFLOW

Date : 2026-05-07  
Statut : DOCTRINE CORRIGÉE

---

# Correction

Le besoin du trader n’est pas :

```text
voir seulement le LTF.
```

Le besoin réel est :

```text
trader court terme à partir d’une lecture HTF W/D/H4/H1.
```

---

# Implication

Les briques récentes restent utiles :

```text
Kinematics
Currency Energy
Relational Gravity
Behavioral Flow
```

Mais elles doivent être replacées dans :

```text
HTF_CONTEXT_STACK
```

---

# Priorité

```text
P0 — corriger lexique / current state
P1 — P1.2 Bridge Guard
P2 — audit runtime
P3 — spec HTF_CONTEXT_STACK
P4 — Behavioral Mapper
```

---

# Interdit

```text
ne pas réduire PowerFlow à M1/M5/M15
```
