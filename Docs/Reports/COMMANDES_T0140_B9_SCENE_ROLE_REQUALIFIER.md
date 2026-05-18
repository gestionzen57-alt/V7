# COMMANDES — T0140 B9 Scene Role Requalifier V0

## Installer

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0140_b9_scene_role_requalifier.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0140_b9_scene_role_requalifier.ps1"
```

## CLI directe

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core
python tools\build_t0140_b9_scene_role_requalifier.py --sequence-summary-json samples\b9_scene_role_requalifier_v0\sample_t009_sequence_summary_scene_roles.json --output-dir outputs\b9_scene_role_requalifier_v0
```

## Tests

```powershell
python -m py_compile pf_t009_scene_role_requalifier.py tools\build_t0140_b9_scene_role_requalifier.py
python -m pytest tests\test_t0140_b9_scene_role_requalifier.py
```
