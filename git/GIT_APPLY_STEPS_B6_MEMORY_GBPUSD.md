# GIT APPLY STEPS — POWERFLOW V7.6 B6 FILM MEMORY GBPUSD

## 1. Branche

```powershell
Set-Location "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT"

git status

git checkout -b feature/v76-b6-film-memory-gbpusd
```

## 2. Appliquer le patch

```powershell
git apply .\POWERFLOW_V76_B6_MEMORY_GBPUSD.patch
```

Si `patch\pf_film_memory_reader_once.py` ou `data\film_memory\gbpusd_v76_film_memory_cards.json`
existent déjà avec un contenu différent:

```powershell
# Option architecte: copier les fichiers livrés depuis le zip, puis vérifier le diff
Copy-Item .\_livrable\patch\pf_film_memory_reader_once.py .\patch\pf_film_memory_reader_once.py -Force
Copy-Item .\_livrable\data\film_memory\gbpusd_v76_film_memory_cards.json .\data\film_memory\gbpusd_v76_film_memory_cards.json -Force
```

## 3. Validation JSON

```powershell
python -m json.tool .\data\film_memory\gbpusd_v76_film_memory_cards.json > $env:TEMP\gbpusd_v76_film_memory_cards.validated.json
```

## 4. Tests

```powershell
python -m pytest .\tests\test_film_memory_matching_v76.py -q
```

## 5. Test terrain_packet réel

```powershell
python .\patch\pf_film_memory_reader_once.py `
  --symbol GBPUSD `
  --packet .\output\dashboard_surface\GBPUSD\terrain_packet.json `
  --cards .\data\film_memory\gbpusd_v76_film_memory_cards.json `
  --out .\output\dashboard_surface\GBPUSD\film_memory_match.json
```

## 6. Vérifier sortie

```powershell
Get-Content .\output\dashboard_surface\GBPUSD\film_memory_match.json
Get-Content .\output\dashboard_surface\GBPUSD\terrain_packet.json
```

Attendu:

```text
memory_match
memory_confidence
memory_reason_fr
similar_historical_days
```

## 7. Commit

```powershell
git diff -- data patch tests Docs git

git add data\film_memory\gbpusd_v76_film_memory_cards.json `
        patch\pf_film_memory_reader_once.py `
        tests\test_film_memory_matching_v76.py `
        Docs\POWERFLOW_V76_B6_MEMORY_GBPUSD_REPORT.md `
        git\COMMIT_MESSAGE_B6_MEMORY_GBPUSD.txt `
        git\GIT_APPLY_STEPS_B6_MEMORY_GBPUSD.md

git commit -F git\COMMIT_MESSAGE_B6_MEMORY_GBPUSD.txt
```

## 8. Push optionnel

```powershell
git push origin feature/v76-b6-film-memory-gbpusd
```

Ne pas push si le diff local montre une collision avec une version plus récente du reader B6.

