# CHECKPOINT — RUNTIME KINEMATICS / ENERGY / RELATIONAL GRAVITY

Date : 2026-05-06  
Statut : À compléter après exécution locale des tests DB  
Mission : tester si les briques Kinematics et Relational Gravity sont opérationnelles dans le Core actuel.

## État officiel attendu

```text
Node V0.7.1 validé : capture_quality / relative freshness
Node V0.7.2 validé : relay_quality M5 missing / thin / clean
Node V0.7.3 validé : session_transition / Daily Open Transition
Node V0.8-B validé : kinematics_state
Node V0.8.1 validé : release_state typé
Node V0.8.2 validé : energy_release_alignment
Currency Energy V0.1 validée en observation
Behavioral Flow Dashboard Live validé
Relational Gravity V0.1 validé standalone
Relational Gravity V0.1.1 delta filter validé
Relational Gravity P1.1 Cockpit Bridge validé runtime
Chantier actif : P1.2 Relational Gravity Bridge Guard avant P2 Behavioral Mapper
```

## Critère critique P1.2

Si :

```text
cross_tf_state = RELATIONAL_GRAVITY_MIXED
dominant_leader = devise claire
dominant_antagonist contient aussi ce leader
```

Alors :

```text
P1.2 OBLIGATOIRE
P2 Behavioral Mapper BLOQUÉ
```

Règle attendue après P1.2 :

```text
MIXED => dominant_leader = MIXED
MIXED => leader_consistency = CONFLICT
MIXED => topline_reliable = false
dominant_leader jamais présent dans dominant_antagonist
tf_details intacts
```

## Verdict à remplir après tests

```text
Kinematics opérationnel : GO / NO GO
Currency Energy opérationnel : GO / NO GO
Relational Gravity probe opérationnel : GO / NO GO
Relational Gravity bridge opérationnel : GO / NO GO
P1.2 nécessaire : oui / non
P2 Behavioral Mapper autorisé : oui / non
```
