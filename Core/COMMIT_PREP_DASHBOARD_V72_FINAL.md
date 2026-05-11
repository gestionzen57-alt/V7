# COMMIT PREP — DASHBOARD V7.2 FINAL

## 1. Pre-commit checks

```powershell
python -m py_compile `
  dashboard_data_normalizer.py `
  dashboard_contract_validator.py `
  dashboard_output_coverage_doctor.py `
  dashboard_hydration_failure_doctor.py

.\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD
.\run_hydration_failure_doctor.ps1 -CorePath .
.\run_dashboard_validate.ps1 -CorePath .
```

Expected:

```text
PASS dashboard contract validation: 0 fail, 0 warn
WARN/failed : 0
```

## 2. Files to add

### Commit A — Dashboard

```powershell
git add dashboard_live_v7.2_final.html
git add dashboard_data_normalizer.py
git add dashboard_contract_validator.py
git add dashboard_output_coverage_doctor.py
git add dashboard_hydration_failure_doctor.py
git add run_dashboard_live_stack.ps1
git add run_dashboard_hydrate_outputs.ps1
git add run_hydration_failure_doctor.ps1
git add run_dashboard_validate.ps1
git add DASHBOARD_V72_FINAL_VALIDATION_REPORT.md
git add DASHBOARD_LIVE_USER_GUIDE.md
git add DASHBOARD_HYDRATION_RUNNER_GUIDE.md
```

Message:

```text
Dashboard: stabilize V7.2 final validation and hydration stack
```

### Commit B — Docs packaging

```powershell
git add POWERFLOW_PACKAGING_STANDARD.md
```

Message:

```text
Docs: add PowerFlow packaging standard
```

### Commit C — Infrastructure

```powershell
git add install_powerflow_pack.ps1
git add cleanup_powerflow_dashboard_artifacts.ps1
```

Message:

```text
Infrastructure: add dashboard install and cleanup tools
```

## 3. Files to exclude

```text
output/
logs/
backups/
__pycache__/
powerflow.db
powerflow.db-shm
powerflow.db-wal
*.bak_*
*_v2.*
*_v3.*
*_v4.*
*_v5.*
*_v6.*
```

## 4. Long commit message

```text
Stabilizes Dashboard V7.2 MAX as final P0 monitoring cockpit:
- Adds stable final HTML delivery
- Adds contract surface validation
- Adds hydration runner with corrected CLI contracts
- Adds dashboard validation helper
- Adds user guide and integration report
- Preserves dual regime and dual density without fusion
- Keeps MISSING / STALE / DEGRADED explicit
- Adds packaging standard and installer/cleanup tooling
```

## 5. Expected status après commit

```text
main clean
origin/main updated
dashboard contract PASS
hydration doctor 0 failed
```

## 6. Follow-up

```text
P0 strict monitoring
Telegram activation after stable window
Future WebSocket bridge
```
