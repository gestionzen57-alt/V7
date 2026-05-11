# PowerFlow V7.2 — MultiSymbol Extension Integration Guide

## Statut de base lu

`CLAUDE.md` indique que PowerFlow V7.2 est en `P0 PASS_STRICT`, commit final `50428c3`, branche `main`, avec dashboard hydraté 16/16 et contract 0 fail / 0 warn.

Le pack respecte les frontières PowerFlow:
- `pf_*` = moteur read-only, aucun cockpit/dashboard/telegram import.
- `run_*` = runners CLI et écriture JSON.
- `dashboard_*` = affichage uniquement.
- `capture_bridge.py` et `powerflow.db` intouchables.

## Accès Git vérifié

- URL demandée: `https://github.com/gestionzen57-alt/V7.git`
- Accès web GitHub: OK, dépôt public visible, branche `main`, dossier `Core` visible.
- Accès `git ls-remote` depuis le conteneur: échec DNS local `Could not resolve host: github.com`.
- Conséquence: livraison ZIP autonome + script de déploiement. Aucun push réel n'a été effectué depuis cet environnement.

## Audit GBPUSD / symbol scope

Audit réalisé sur les fichiers accessibles via GitHub raw et sur les documents V7.2 fournis.

### Hardcodes ou defaults GBPUSD observés

| Fichier | Constat | Patch livré |
|---|---|---|
| `run_temporal_node_state_once.py` | `--symbol default="GBPUSD"`, output legacy `output/temporal_node_state.json` | `PATCHED_RUNNERS/run_temporal_node_state_once.py` |
| `run_currency_energy_probe_once.py` | `--symbol default="GBPUSD"`, output legacy `output/currency_energy_state.json` | `PATCHED_RUNNERS/run_currency_energy_probe_once.py` |
| `run_regime_engine_once.py` | `--symbol default="GBPUSD"`, output optionnel non namespacé | `PATCHED_RUNNERS/run_regime_engine_once.py` |
| `run_powerflow_dashboard_refresh_once.py` | `DEFAULT_SYMBOL = "GBPUSD"` | appelé en scheduler comme step dashboard; pas remplacé pour éviter de casser le dashboard validé |

### Runners sans `--symbol` observés

| Fichier | Risque technique | Patch livré |
|---|---|---|
| `run_temporal_density_once.py` | B4 lit toutes les lignes TF sans scope symbol si module non patché | runner + `PATCHED_MODULES/pf_temporal_density.py` |
| `run_spearman_gravity_once.py` | B5 lit toutes les lignes TF sans scope symbol si module non patché | runner + `PATCHED_MODULES/pf_spearman_gravity.py` |
| `run_behavioral_alert_mapper_once.py` | paths non namespacés, mélange possible des queues | `PATCHED_RUNNERS/run_behavioral_alert_mapper_once.py` |

### Modules pf_* explicitement paramétriques

`pf_regime_engine.compute_regime(db_path, symbol, ...)` et `pf_currency_energy_probe.build_currency_energy_state(..., symbol="GBPUSD", ...)` acceptent déjà `symbol`; les patches runners exploitent ce paramètre et changent les chemins output.

### Modules pf_* patchés par le pack

- `PATCHED_MODULES/pf_temporal_density.py`: ajoute `symbol` à `_fetch_series`, `compute_temporal_density`, `compute_temporal_density_multi`; SQL filtré par `UPPER(symbol)=?`.
- `PATCHED_MODULES/pf_spearman_gravity.py`: ajoute `symbol` à `_fetch_two_series`, `compute_spearman_pair`, `compute_spearman_all_pairs`; SQL filtré par `UPPER(symbol)=?`.

## Convention output livrée

Par symbole:

```text
output/dashboard_surface/{symbol}/regime_legacy.json
output/dashboard_surface/{symbol}/regime_hmm.json       # lu par dashboard si présent
output/dashboard_surface/{symbol}/energy.json
output/dashboard_surface/{symbol}/cascade.json          # lu par dashboard si présent
output/dashboard_surface/{symbol}/node.json
output/temporal_density_state_{symbol}.json
output/spearman_gravity_state_{symbol}.json
output/behavioral_alert_queue_{symbol}.json
```

Cross-symbol séparé:

```text
output/dashboard_surface/cross_validation.json
```

Compatibilité GBPUSD:

Les runners patchés écrivent aussi les alias legacy pour `GBPUSD` quand le symbole est `GBPUSD`, par exemple `output/temporal_density_state.json` et `output/behavioral_alert_queue.json`.

## Installation rapide

Depuis le dossier extrait du ZIP:

```powershell
.\git_deploy_multisymbol.ps1 -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
```

Déploiement manuel minimal:

```powershell
Copy-Item .\pf_cross_symbol_validation.py Core\ -Force
Copy-Item .\run_cross_symbol_validation_once.py Core\ -Force
Copy-Item .\scheduler_powerflow.py Core\ -Force
Copy-Item .\scheduler_config.json Core\ -Force
Copy-Item .\setup_windows_task_scheduler.ps1 Core\ -Force
Copy-Item .\PATCHED_RUNNERS\*.py Core\ -Force
Copy-Item .\PATCHED_MODULES\*.py Core\ -Force
```

## Tests one-shot

```powershell
cd Core
python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --pretty
python run_currency_energy_probe_once.py --db powerflow.db --symbol EURUSD --pretty
python run_temporal_density_once.py --db powerflow.db --symbol USDJPY --pretty --summary
python run_spearman_gravity_once.py --db powerflow.db --symbol XAUUSD --pretty --summary
python run_cross_symbol_validation_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty
python scheduler_powerflow.py --once --symbols GBPUSD
```

## Scheduler Windows

```powershell
.\setup_windows_task_scheduler.ps1 -Action enable -CorePath .
.\setup_windows_task_scheduler.ps1 -Action status
.\setup_windows_task_scheduler.ps1 -Action disable
```

## Risques techniques résiduels

- `EUR_DIVERGENT` est mieux qualifié avec `EURGBP` ou `GBPEUR`; avec `GBPUSD+EURUSD+USDJPY`, le moteur peut inférer mais marque `EUR_DIVERGENCE_INFERRED_WITHOUT_EURGBP_DIRECT_CROSS`.
- `GBP_STRENGTH_GENUINE` est plus fiable avec au moins un second cross GBP (`GBPJPY`, `EURGBP`, etc.).
- `XAUUSD` dépend de la présence d'une colonne `force_xau` ou `xau`; sinon le module signale `BASE_FORCE_COLUMN_MISSING_XAU`.
- `run_powerflow_dashboard_refresh_once.py` reste volontairement non patché pour ne pas casser le dashboard PASS_STRICT; le patch HTML multi-symbol lit directement les JSON namespacés.

## Interdits maintenus

- Jamais de DB write dans `pf_*`.
- Jamais de BUY/SELL dans les outputs.
- Jamais de fusion cross-symbol avec résultat par symbole.
- Jamais de logique différente par symbole: le symbole est paramètre.
- `GBPUSD` reste l'alias principal validé et conserve les sorties legacy.
