# GIT APPLY STEPS — POWERFLOW V7.6 TRADER PLAYBOOKS GBPUSD

```powershell
Set-Location "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"

git status
git checkout -b feature/v76-gbpusd-trader-playbooks

mkdir -p patch schema tests Docs git

git apply .\POWERFLOW_V76_TRADER_PLAYBOOKS_GBPUSD.patch

python -m json.tool .\schema\playbook_labels_fr_v76.json > $env:TEMP\playbook_labels_fr_v76.validated.json
python -m py_compile .\patch\pf_trader_playbook_once.py
python -m pytest .\tests\test_trader_playbook_v76.py -q

python .\patch\pf_trader_playbook_once.py `
  --symbol GBPUSD `
  --input .\output\dashboard_surface\GBPUSD\terrain_packet.json `
  --labels .\schema\playbook_labels_fr_v76.json `
  --output .\output\dashboard_surface\GBPUSD\trader_playbook.json `
  --packet-output .\output\dashboard_surface\GBPUSD\terrain_packet_with_playbook.json

git add patch\pf_trader_playbook_once.py `
        schema\playbook_labels_fr_v76.json `
        tests\test_trader_playbook_v76.py `
        Docs\POWERFLOW_V76_TRADER_PLAYBOOKS_REPORT.md `
        git\COMMIT_MESSAGE_TRADER_PLAYBOOKS_V76.txt `
        git\GIT_APPLY_STEPS_TRADER_PLAYBOOKS_V76.md

git commit -F git\COMMIT_MESSAGE_TRADER_PLAYBOOKS_V76.txt
```

Ne pas push sur main. Push optionnel seulement sur branche feature :

```powershell
git push origin feature/v76-gbpusd-trader-playbooks
```

