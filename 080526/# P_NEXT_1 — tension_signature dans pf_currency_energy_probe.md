# P_NEXT_1 — tension_signature dans pf_currency_energy_probe
**Date :** 2026-05-08  
  
**Fichier cible :** `pf_currency_energy_probe.py`

---

## Objectif

Ajouter `elastic_tension_score` comme composante supplémentaire du score Currency Energy.
Energy doit le voir — pas pour créer un signal, mais pour qualifier le champ.

---

## Composante à ajouter

```python
from pf_tension_signature import compute_tension_signature

series_tf5 = fetch_series(db_path, force_col, timeframe=5, bars=50)
sig = compute_tension_signature(series_tf5)

elastic_tension_score = sig.score
elastic_tension_label = sig.label
```

## Pondération suggérée
Composantes existantes :
force_position ~0.20
behavioral_zscore ~0.20
zone_tension ~0.15
speed_score ~0.10
angle_score ~0.10
acceleration_score ~0.10
persistence_score ~0.10
basket_deviation ~0.05

Ajout :
elastic_tension_score 0.10-0.15
→ réduire proportionnellement les autres
→ ne pas dépasser 0.15 pour ne pas surpondérer microfilm

text

## Règles
elastic_tension_score qualifie — ne crée pas release_state.
Si label = "ELASTIC_LOADED" → energy_context += "ELASTIC_COMPONENT_ACTIVE"
Si label = "LEAKING" → energy_context += "ELASTIC_COMPONENT_LEAKING"
Energy ≠ signal. Energy qualifie.

text

## Output attendu

```json
{
  "elastic_tension_score": 0.73,
  "elastic_tension_label": "ELASTIC_LOADED",
  "energy_score": 0.82,
  "energy_label": "HIGH",
  "energy_context": ["ZONE_ACTIVE", "ELASTIC_COMPONENT_ACTIVE"]
}
```

## Risques techniques
Série TF5 trop courte (< 20 bars)
→ guard : si len(series) < 20 → elastic_tension_score = 0.0

Double-comptage avec zone_tension existante
→ vérifier que les deux ne lisent pas la même série

Régression sur energy_score existant
→ tester avant/après sur snapshot 2026-05-08