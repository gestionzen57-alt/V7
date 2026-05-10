# B1 HMM V1.2 — Schema-aware standalone patch

Patch ciblé pour PowerFlow B1 HMM.

## Pourquoi

V1.1 standalone était actif, mais échouait sur :

```text
force_snapshots must expose timestamp/timeframe and GBP/USD force columns
```

Cause : la table `force_snapshots` n'utilise pas forcément `force_gbp` / `force_usd` comme noms de colonnes. V1.2 ajoute une auto-détection robuste du schéma.

## Changements

- `MODEL_VERSION = HMMRegimeV1.2StandaloneSchema`
- `RUNNER_VERSION = HMMRegimeRunnerV1.2StandaloneSchema`
- Aucune dépendance `hmmlearn`
- Auto-détection des colonnes :
  - timestamp : `timestamp`, `ts`, `time`, `datetime`, `snapshot_time`, etc.
  - timeframe : `timeframe`, `tf`, `period`, `tf_minutes`, etc.
  - GBP/USD : `GBP`, `USD`, `gbp`, `usd`, `force_gbp`, `gbp_force`, `gbp_score`, `zscore_gbp`, etc.
- Support fallback schéma long : `timestamp/timeframe/currency/value`.
- Messages d'erreur enrichis avec `available_columns` si le schéma reste introuvable.

## Installation

Dézipper à la racine du repo :

```powershell
C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
```

Puis depuis `Core` :

```powershell
Select-String -Path .\pf_hmm_regime.py -Pattern "hmmlearn"
Select-String -Path .\pf_hmm_regime.py -Pattern "V1.2StandaloneSchema"
Select-String -Path .\run_hmm_regime_once.py -Pattern "V1.2StandaloneSchema"

python -m py_compile pf_hmm_regime.py run_hmm_regime_once.py
python run_hmm_regime_once.py --db powerflow.db --train --predict --pretty
python -m json.tool ..\output\hmm_regime_result.json | Out-Null
Test-Path ..\output\hmm_regime_model.pkl
```

## Résultat attendu

- `hmmlearn` : aucune ligne.
- `V1.2StandaloneSchema` : visible dans les deux fichiers.
- `Test-Path ..\output\hmm_regime_model.pkl` : `True` si entraînement OK.

