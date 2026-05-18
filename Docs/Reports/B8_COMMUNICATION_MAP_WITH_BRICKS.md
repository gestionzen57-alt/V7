# B8 COMMUNICATION MAP WITH BRICKS

**Projet :** PowerFlow / B8 / Multi-devises FX  
**Objet :** cartographie des communications entre B8 et les autres briques  
**Statut :** contrat documentaire V0  

---

## 0. Principe

B8 ne decide pas. B8 contextualise.

```text
B8 dit si la scene locale est soutenue, contredite ou non verifiable par les devises autour.
```

B8 doit rester separe de B9, B6, B7 et des surfaces. Il peut fournir une preuve au packet final, mais ne doit pas devenir une autorite centrale.

---

## 1. Carte generale

```text
capture_* / powerflow.db
        |
        v
force_snapshots_v2 / outputs force
        |
        v
B8 cross-symbol context
        |
        +--> B5 / Spearman / RG : mesures relationnelles
        +--> B9 : contexte externe de scene locale
        +--> B6 : contexte historisable de film
        +--> B7 : distinction propagation TF vs propagation devises
        +--> Evidence Bus : preuve contextualisee
        +--> Trader Packet futur : resume lisible
```

---

## 2. B8 ↔ capture / DB

### Role

B8 consomme des snapshots multi-symboles.

### Questions

```text
Quels symboles sont captures ?
La capture est-elle simultanee ?
Quels timeframes existent ?
Quels snapshots sont stale ?
```

### Contrat attendu

```json
{
  "coverage": "FULL | PARTIAL | THIN | BLIND",
  "aligned_symbols": [],
  "missing_symbols": [],
  "stale_symbols": [],
  "time_alignment_risk": false
}
```

### Risques

```text
B8_TIME_ALIGNMENT_RISK
CROSS_VALIDATION_DEGRADED
HONEST_UNKNOWN
```

---

## 3. B8 ↔ B5 / Spearman / Relational Gravity

### Separation

```text
B5 / RG mesure la relation.
B8 qualifie la validation cross-symbol.
```

### Exemple

B5 peut dire :

```text
GBPUSD et GBPJPY sont synchrones.
```

B8 doit transformer en contexte :

```text
GBP_STRENGTH possible, mais coverage GBP crosses partiel.
```

### Interdit

```text
B5 rho eleve = confirmation directe.
```

### Attendu

```json
{
  "relational_evidence": {
    "rho_context": "AVAILABLE | MISSING | DEGRADED",
    "leader_follower_context": "AVAILABLE | UNKNOWN",
    "limits": []
  }
}
```

---

## 4. B8 ↔ B9 Sequence Summarizer

### Separation stricte

```text
B9 = scene locale.
B8 = contexte multi-devises.
```

B9 doit continuer a produire :

```text
moments
parent_scene
zone_memory
effort_role
retest_status
memory_state
source_profile
```

B8 peut ajouter :

```json
{
  "cross_symbol_context": {
    "state": "CONFIRMED | OPPOSED | MIXED | HONEST_UNKNOWN | CROSS_VALIDATION_DEGRADED",
    "driver": "GBP_STRENGTH | USD_WEAKNESS | MIXED_DRIVER | UNKNOWN_DRIVER",
    "coverage": "FULL | PARTIAL | THIN | BLIND",
    "limits": []
  }
}
```

### Exemple de lecture correcte

```text
B9 : la zone haute est rejetee et la memoire migre plus bas.
B8 : les crosses GBP sont partiels ; le driver GBP n'est pas verifiable.
Lecture : scene locale valide, contexte multi-devises degrade.
```

### Interdit

```text
B8 ne doit pas convertir une scene B9 en ordre.
B8 ne doit pas forcer un moment B9.
B8 ne doit pas masquer une scene B9 faute de coverage.
```

---

## 5. B8 ↔ B6 Film Memory

B6 doit memoriser des films, y compris les pieges.

### Objet historisable

```json
{
  "film_signature": "BASE_REACTION_PROJECTION_REJECTION",
  "b8_context_state": "OPPOSED",
  "b8_driver": "UNKNOWN_DRIVER",
  "b8_coverage": "THIN",
  "trap_memory": "scene locale forte mais coalition non verifiable",
  "limits": ["CROSS_VALIDATION_DEGRADED"]
}
```

### Questions B6

```text
A-t-on deja vu ce film B9 avec B8 oppose ?
Qu'est-ce qui avait confirme ?
Qu'est-ce qui avait invalide ?
Quel piege avait ete cache par la couverture faible ?
```

### Interdit

```text
B6 ne predit pas.
B6 ne decide pas.
B6 ne transforme pas B8 en certitude.
```

---

## 6. B8 ↔ B7 / B7+

### Separation

```text
B7 = propagation multi-timeframe.
B8 = propagation multi-devises.
B7+ = texture du detachement.
```

### Exemple

```text
B9 voit une vague progressive locale.
B7 dit : propagation M1 -> M5 absente.
B8 dit : cross-symbol context mixed.
B7+ dit : texture tardive / friction.
```

Le packet final peut dire :

```text
scene locale lisible, mais propagation TF absente et contexte B8 mixte.
```

Pas de conclusion automatique.

---

## 7. B8 ↔ Evidence Bus

B8 doit entrer dans l'evidence bus comme preuve contextualisee.

### Format propose

```json
{
  "evidence_type": "B8_CROSS_SYMBOL_CONTEXT",
  "state": "CONFIRMED | OPPOSED | MIXED | HONEST_UNKNOWN | CROSS_VALIDATION_DEGRADED",
  "driver": "GBP_STRENGTH | USD_WEAKNESS | MIXED_DRIVER | UNKNOWN_DRIVER",
  "coverage": "FULL | PARTIAL | THIN | BLIND",
  "technical_risks": ["B8_TIME_ALIGNMENT_RISK"],
  "limits": []
}
```

### Regle

Evidence Bus expose. Il ne tranche pas.

---

## 8. B8 ↔ cockpit / dashboard / telegram

A ce stade, cockpit/dashboard/telegram doivent rester consommateurs futurs.

```text
Aucune dependance de pf_* vers dashboard_*.
Aucune dependance de pf_* vers telegram_*.
Aucune mutation de surface dans cet audit.
```

Sortie future autorisee :

```text
B8: contexte multi-devises MIXED / coverage PARTIAL / driver UNKNOWN
```

Sortie interdite :

```text
instruction directionnelle
certitude forte avec coverage faible
```

---

## 9. Communication cible finale

```text
B9 raconte : ce qui se passe localement.
B8 contextualise : qui semble porter ou contredire la scene.
B7 situe : est-ce que cela se propage dans les timeframes.
B6 memorise : a-t-on deja vu ce film et quel piege existait.
Evidence Bus expose : preuves + limites.
Trader filtre.
```

