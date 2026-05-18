# B8 CROSS SYMBOL CONTEXT CONTRACT

**Projet :** PowerFlow / B8 / Cross-Symbol Context  
**Objet :** contrat JSON minimal entre B8 et les autres briques  
**Statut :** V0 documentaire, pret audit  

---

## 0. Principe

B8 ne decide pas. B8 contextualise.

```text
B8 dit si la scene locale est soutenue, contredite ou non verifiable par les devises autour.
```

B8 doit toujours exposer :

```text
state
driver
coverage
aligned_symbols
missing_symbols
stale_symbols
limits
technical_risks
```

---

## 1. Objet JSON cible

```json
{
  "symbol": "GBPUSD",
  "timestamp_utc": "2026-05-15T10:23:00Z",
  "cross_symbol_context": {
    "state": "CONFIRMED | OPPOSED | MIXED | HONEST_UNKNOWN | CROSS_VALIDATION_DEGRADED",
    "driver": "GBP_STRENGTH | USD_WEAKNESS | MIXED_DRIVER | UNKNOWN_DRIVER",
    "coverage": "FULL | PARTIAL | THIN | BLIND",
    "aligned_symbols": ["GBPUSD", "GBPJPY", "EURUSD", "USDJPY"],
    "missing_symbols": [],
    "stale_symbols": [],
    "time_alignment": {
      "aligned": true,
      "max_gap_seconds": 0,
      "risk": "NONE | B8_TIME_ALIGNMENT_RISK"
    },
    "evidence": [
      {
        "symbol": "GBPJPY",
        "role": "GBP_CROSS",
        "state": "ALIGNED | OPPOSED | MIXED | STALE | MISSING",
        "score": 0.0,
        "limits": []
      }
    ],
    "limits": [],
    "technical_risks": []
  }
}
```

---

## 2. Etats `state`

| State | Sens |
|---|---|
| `CONFIRMED` | les crosses disponibles soutiennent la scene locale |
| `OPPOSED` | les crosses disponibles contredisent la scene locale |
| `MIXED` | certaines devises soutiennent, d'autres contredisent |
| `HONEST_UNKNOWN` | couverture insuffisante pour conclure |
| `CROSS_VALIDATION_DEGRADED` | donnees presentes mais trop stale / thin / desalignes |

---

## 3. Drivers

| Driver | Sens |
|---|---|
| `GBP_STRENGTH` | GBP semble porter la paire sur plusieurs crosses disponibles |
| `USD_WEAKNESS` | USD semble porter le mouvement par faiblesse relative |
| `EUR_STRENGTH` | EUR semble moteur si paire EUR concernee |
| `JPY_WEAKNESS` | JPY semble moteur si crosses JPY alignes |
| `MIXED_DRIVER` | driver non unique ou contradictoire |
| `UNKNOWN_DRIVER` | driver non verifiable |

Regle :

```text
Si coverage = THIN ou BLIND, driver doit etre UNKNOWN_DRIVER ou MIXED_DRIVER.
```

---

## 4. Coverage

| Coverage | Regle indicative |
|---|---|
| `FULL` | base + quote ont plusieurs crosses frais et alignes |
| `PARTIAL` | au moins un cote dispose de crosses exploitables |
| `THIN` | trop peu de crosses pour driver fiable |
| `BLIND` | aucune validation cross-symbol utile |

---

## 5. Limites obligatoires

B8 doit exposer les limites suivantes si elles existent :

```text
B8_TIME_ALIGNMENT_RISK
CROSS_VALIDATION_DEGRADED
MISSING_GBP_CROSSES
MISSING_USD_CROSSES
STALE_SYMBOLS
THIN_COVERAGE
B5_RG_UNAVAILABLE
HONEST_UNKNOWN
```

---

## 6. Contrat avec B9

B9 produit la scene locale. B8 annexe :

```json
{
  "b9_scene_id": "SCENE_001",
  "b9_parent_scene": "base -> reaction -> projection -> judgment",
  "cross_symbol_context": {
    "state": "MIXED",
    "driver": "UNKNOWN_DRIVER",
    "coverage": "PARTIAL"
  }
}
```

Regle :

```text
B8 ne reclassifie pas B9.
B8 annexe un contexte.
```

---

## 7. Contrat avec B6

B6 stocke un film enrichi :

```json
{
  "film_signature": "BASE_REACTION_PROJECTION_REJECTION",
  "b8_context_state": "OPPOSED",
  "b8_driver": "UNKNOWN_DRIVER",
  "b8_coverage": "THIN",
  "false_positive_risks": [
    "CROSS_VALIDATION_DEGRADED",
    "B8_TIME_ALIGNMENT_RISK"
  ],
  "historical_question": "A-t-on deja vu une scene locale rejetee avec contexte B8 oppose ou degrade ?"
}
```

B6 compare. B6 ne predit pas. B6 ne decide pas.

---

## 8. Interdits

B8 ne doit pas produire :

```text
ordre directionnel
execution automatique
confirmation dure avec coverage faible
certitude driver sans symbols alignes
fusion prematuree avec B9
import dashboard ou telegram depuis pf_*
```

---

## 9. Exemple prudent

```json
{
  "symbol": "GBPUSD",
  "timestamp_utc": "2026-05-15T10:23:00Z",
  "cross_symbol_context": {
    "state": "HONEST_UNKNOWN",
    "driver": "UNKNOWN_DRIVER",
    "coverage": "THIN",
    "aligned_symbols": ["GBPUSD"],
    "missing_symbols": ["GBPJPY", "GBPCHF", "GBPCAD", "USDCHF", "USDCAD"],
    "stale_symbols": [],
    "time_alignment": {
      "aligned": false,
      "max_gap_seconds": null,
      "risk": "B8_TIME_ALIGNMENT_RISK"
    },
    "evidence": [],
    "limits": ["THIN_COVERAGE", "HONEST_UNKNOWN"],
    "technical_risks": ["CROSS_VALIDATION_DEGRADED"]
  }
}
```

---

## 10. Phrase de verrouillage

```text
B8 ne decide pas.
B8 dit si la scene locale est soutenue, contredite ou non verifiable par les devises autour.
```

