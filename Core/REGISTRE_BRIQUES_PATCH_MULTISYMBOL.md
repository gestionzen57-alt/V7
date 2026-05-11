# REGISTRE BRIQUES PATCH MULTISYMBOL — PowerFlow V7.2

## B8 — CROSS SYMBOL VALIDATION

```text
Fichier    : pf_cross_symbol_validation.py
Runner     : run_cross_symbol_validation_once.py
Statut     : PATCH LIVRÉ
Rôle       : distinguer force propre devise vs faiblesse dominante devise opposée
Lit        : powerflow.db / force_snapshots en read-only
Produit    : output/dashboard_surface/cross_validation.json
DB write   : JAMAIS
Décision   : JAMAIS
```

### Output principal

```json
{
  "cross_validation": {
    "gbp_true_strength": "STRONG | MODERATE | WEAK | UNKNOWN",
    "usd_true_strength": "STRONG | MODERATE | WEAK | UNKNOWN",
    "eur_true_strength": "STRONG | MODERATE | WEAK | UNKNOWN",
    "jpy_true_strength": "STRONG | MODERATE | WEAK | UNKNOWN",
    "driver": "USD_WEAKNESS_DOMINANT | GBP_STRENGTH_GENUINE | EUR_DIVERGENT | JPY_SAFE_HAVEN | MIXED",
    "confidence": 0.0,
    "symbols_used": [],
    "technical_risks": [],
    "timestamp": "ISO8601"
  }
}
```

## PATCHED MODULES

### B4 — pf_temporal_density.py

Ajout `symbol` dans le flux de calcul. Le SQL devient `WHERE UPPER(symbol)=? AND timeframe=?`.

### B5 — pf_spearman_gravity.py

Ajout `symbol` dans le flux de calcul. Toutes les corrélations sont par symbole, pas globales DB.

## PATCHED RUNNERS

| Runner | Nouveau paramètre | Output |
|---|---|---|
| `run_temporal_node_state_once.py` | `--symbol` | `output/dashboard_surface/{symbol}/node.json` |
| `run_currency_energy_probe_once.py` | `--symbol` | `output/dashboard_surface/{symbol}/energy.json` |
| `run_regime_engine_once.py` | `--symbol` | `output/dashboard_surface/{symbol}/regime_legacy.json` |
| `run_temporal_density_once.py` | `--symbol` | `output/temporal_density_state_{symbol}.json` |
| `run_spearman_gravity_once.py` | `--symbol` | `output/spearman_gravity_state_{symbol}.json` |
| `run_behavioral_alert_mapper_once.py` | `--symbol` | `output/behavioral_alert_queue_{symbol}.json` |

## SCHEDULER

```text
Fichier : scheduler_powerflow.py
Config  : scheduler_config.json
Cycle   : par symbole puis cross-validation une fois
Guard   : lock logs/scheduler_powerflow.lock
Log     : logs/scheduler.log
```

## CONTRAINTES

- Cross-validation jamais fusionnée avec output par symbole.
- Alias legacy GBPUSD maintenus pour ne pas casser P0 PASS_STRICT.
- Aucun BUY/SELL.
- Aucun DB write dans `pf_*`.
- Aucun import cockpit/dashboard/telegram dans `pf_*`.
