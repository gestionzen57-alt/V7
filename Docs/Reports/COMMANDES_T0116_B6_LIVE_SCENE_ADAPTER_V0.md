# Commandes T0116 — B6 Live Scene Adapter V0

## Install one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0116_b6_live_scene_adapter_v0.ps1"
```

## Git one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0116_b6_live_scene_adapter_v0.ps1"
```

## CLI adapter seul

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core

python tools\build_t0116_b6_live_scene_adapter_v0.py `
  --input-json samples\b6_live_scene_adapter_v0\sample_b9_live_scene_v0.json `
  --output-dir outputs\b6_live_scene_adapter_v0
```

## Adapter puis query T0115

```powershell
python tools\build_t0115_b6_similarity_query_v0.py `
  --similarity-index outputs\b6_similarity_index_v0\B6_SIMILARITY_INDEX_V0.json `
  --query-json outputs\b6_live_scene_adapter_v0\B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json `
  --output-dir outputs\b6_live_scene_adapter_v0_t0115_query_validation `
  --top-k 5
```
