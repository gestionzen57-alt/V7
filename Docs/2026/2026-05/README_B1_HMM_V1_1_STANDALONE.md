# B1 HMM Regime V1.1 — Standalone hotfix

## Pourquoi ce patch

`hmmlearn` ne fournit pas de wheel CPython 3.14 Windows au moment du test. Pip tente donc une compilation locale, qui échoue souvent sans toolchain C complète.

Ce patch supprime la dépendance `hmmlearn` et remplace le moteur par un Gaussian HMM autonome en `numpy`.

## Fichiers

```text
Core/pf_hmm_regime.py
Core/run_hmm_regime_once.py
```

## Installation dépendance minimale

```powershell
python -m pip install numpy
```

## Validation

Depuis `Core` :

```powershell
python -m py_compile pf_hmm_regime.py run_hmm_regime_once.py
python run_hmm_regime_once.py --db powerflow.db --train --predict --pretty
python -m json.tool ..\output\hmm_regime_result.json | Out-Null
```

## Stabilité

```powershell
python run_hmm_regime_once.py --db powerflow.db --predict --pretty
Copy-Item ..\output\hmm_regime_result.json ..\output\hmm_regime_run1.json
python run_hmm_regime_once.py --db powerflow.db --predict --pretty
Copy-Item ..\output\hmm_regime_result.json ..\output\hmm_regime_run2.json
python run_hmm_regime_once.py --db powerflow.db --predict --pretty
Copy-Item ..\output\hmm_regime_result.json ..\output\hmm_regime_run3.json

python -c "import json; files=['../output/hmm_regime_run1.json','../output/hmm_regime_run2.json','../output/hmm_regime_run3.json']; data=[json.load(open(f, encoding='utf-8')) for f in files]; assert all(d.get('valid') for d in data), 'One run invalid'; assert len(set(d['prediction']['regime'] for d in data))==1, 'Regime differs'; print('HMM STABLE')"
```

## Commit

```powershell
git add Core\pf_hmm_regime.py Core\run_hmm_regime_once.py
git commit -m "B1: HMM Gaussian regime upgrade"
git push
```
