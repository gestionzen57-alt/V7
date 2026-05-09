# CONTRAT D'INTÉGRATION — Personality → ZoneDynamics

## Objectif

Ce contrat verrouille la séparation entre `pf_personalities.py` et `pf_zone_dynamics.py`.

La règle est simple :

```text
Personality mesure l'identité comportementale de l'acteur.
ZoneDynamics lit la respiration de la zone.
```

## Frontière stricte

### `pf_personalities.py`

Responsabilité :

```text
- Calculer z_basket par devise
- Calculer z_pair pour les duels directs
- Mesurer slope / curvature
- Qualifier la phase individuelle
- Qualifier la qualité comportementale
- Préparer leader/follower candidat
```

Il ne doit pas :

```text
- Décider ACCUMULATING / LEAKING / RUPTURE
- Écrire en DB
- Alerter Telegram
- Dépendre du Cockpit
```

### `pf_zone_dynamics.py`

Responsabilité :

```text
- Lire une série de Z-score
- Détecter PRE_EXTREME / EXTREME / POST_ZONE
- Lire la respiration : ACCUMULATING / LEAKING / RUPTURE / DISORDER_FIELD
- Calculer tension_score
- Calculer context_score
- Produire contextual_tags + context_tags
```

Il ne doit pas :

```text
- Calculer z_basket depuis les forces brutes
- Décider les coalitions
- Écrire en DB
- Alerter Telegram
```

## Entrée attendue depuis Personality

Exemple minimal :

```python
usd_z_basket_series = [
    row["currencies"]["USD"]["z_basket"]
    for row in personality_history
]
```

Puis :

```python
from pf_zone_dynamics import analyze_zone_dynamics

usd_zone = analyze_zone_dynamics(
    usd_z_basket_series,
    timeframe=1,
    currency="USD",
    session_phase="LONDON",
    rank_position=1,
    rank_total=8,
    rank_duration_bars=25,
    price_wall=False,
)
```

## Sortie attendue ZoneDynamics

```python
{
    "state": "ACCUMULATING",
    "zone_level": "EXTREME",
    "z_current": 2.41,
    "z_extreme_dir": "HIGH",
    "bars_in_extreme": 9,
    "absorption_factor": 1.5,
    "tension_score": 8.34,
    "context_score": 9.18,
    "contextual_tags": ["LOCAL_ZONE_WORK", "M1_SPECIAL_MICROFILM", "CURRENCY_USD"],
    "context_tags": ["LOCAL_ZONE_WORK", "M1_SPECIAL_MICROFILM", "CURRENCY_USD"]
}
```

## Chaînage moteur propre

```text
force_snapshots
→ pf_personalities.py
→ z_basket_series par devise
→ pf_zone_dynamics.py
→ diagnostics respiratoires
→ pf_zone_context_logger.py
→ mémoire DB
→ pf_coalitions.py
→ agrégats de devises synchronisées
→ pf_temporal_nodes.py
→ fenêtre temporelle / node
→ cockpit_*
```

## Règle d'or

```text
Pas de fusion prématurée.
Pas de module monstre.
Chaque brique garde sa responsabilité.
```

## Prochaine brique mémorielle

`pf_zone_context_logger.py` devra seulement prendre les diagnostics `ZoneDiagnosis.to_dict()` et les écrire en SQLite.

Table cible probable :

```sql
CREATE TABLE IF NOT EXISTS zone_context_diagnostics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    currency TEXT NOT NULL,
    timeframe TEXT,
    state TEXT,
    zone_level TEXT,
    z_current REAL,
    z_extreme_dir TEXT,
    bars_in_extreme INTEGER,
    absorption_factor REAL,
    tension_score REAL,
    context_score REAL,
    profile_name TEXT,
    profile_horizon TEXT,
    session_phase TEXT,
    context_tags_json TEXT,
    note TEXT
);
```
