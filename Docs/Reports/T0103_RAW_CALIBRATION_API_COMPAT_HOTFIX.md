# T0103 Raw Calibration API Compatibility Hotfix V4

Status: READY_FOR_INSTALL
Branch proposal: `fix/t0103-raw-calibration-api-compat-v4`
Commit proposal: `fix(t0103): restore raw calibration runner api compatibility`

## Problem

T0103 found B9 summaries, but raw calibration failed because `run_t009_raw_calibration_once.py` imports `RawCalibrationConfig` while the V3.6 calibration module no longer exposed it.

Previous V2/V3 installers failed only in their helper script generation / smoke loader, not in the diagnosis.

## Fix V4

V4 removes the Python helper entirely.

The install script itself:

1. appends `RawCalibrationConfig` to `pf_t009_raw_calibration.py` if missing;
2. patches `RUN_T0103_WEEKLY_RAW_CALIBRATION_V36.ps1` to fail fast after Python errors;
3. overwrites the compatibility pytest with a normal import-based test;
4. validates import compatibility with `python -c`;
5. runs pytest.

## Constraints

- read-only
- no `powerflow.db` write
- no `tick_archive.db` write
- no dashboard
- no Telegram
- no BUY/SELL
- no B8 fusion

## Phrase de cap

Le runner doit échouer fort si la calibration échoue. Un rapport vide n’est pas une validation.
