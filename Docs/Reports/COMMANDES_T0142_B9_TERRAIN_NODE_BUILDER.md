# Commandes T0142 — B9 Terrain Node Builder V0

## Install one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0142_b9_terrain_node_builder.ps1"
```

## Git one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0142_b9_terrain_node_builder.ps1"
```

## Tests manuels

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core
python -m py_compile pf_t009_terrain_node_builder.py tools\build_t0142_b9_terrain_node_builder.py
python -m pytest tests\test_t0142_b9_terrain_node_builder.py
```

## CLI

```powershell
python tools\build_t0142_b9_terrain_node_builder.py `
  --sequence-summary-json samples\b9_terrain_node_builder_v0\sample_t009_sequence_summary_terrain_nodes.json `
  --output-dir outputs\b9_terrain_node_builder_v0
```
