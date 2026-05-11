# PowerFlow V7.2 — Dashboard Hydration Runner

But : hydrater les sorties directes qui restent `MISSING` ou `STALE` dans le cockpit, puis relancer automatiquement :

```powershell
.\run_dashboard_live_stack.ps1 -Normalize -Validate -Doctor
```

## Installation

Copier `run_dashboard_hydrate_outputs.ps1` dans `Core/`.

## Commande standard

```powershell
.\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD
```

## Avec serveur après hydratation

```powershell
.\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD -Serve
```

## Lecture

- `MISSING` après hydratation = runner absent, CLI différente, ou brique non productrice de JSON direct.
- `DEGRADED` = payload présent mais timestamp source absent.
- `STALE` = payload horodaté mais ancien.
- `LIVE` = payload horodaté frais.

Le script ne modifie pas `powerflow.db`, n’importe pas de `pf_*`, et ne touche pas aux fichiers moteur.
