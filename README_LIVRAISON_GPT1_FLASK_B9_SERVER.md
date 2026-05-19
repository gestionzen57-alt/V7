# LIVRAISON GPT-1 — PowerFlow V7.6.7 B9 Flask Server + B8 Endpoints

## Objet

Créer une surface Flask cockpit locale pour exposer :

- `GET /api/health`
- `GET /api/b9-nodes-live?symbol=GBPUSD&limit=10`
- `GET /api/b8-coalition-context?symbol=GBPUSD`

Port : `8880`

## Fichiers livrés

```text
Core/cockpit_server_b9.py
Core/test_flask_b9_server.py
tests/test_cockpit_server_b9_unit.py
README_LIVRAISON_GPT1_FLASK_B9_SERVER.md
```

## Installation

Depuis `C:\Users\User\Downloads` :

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_b9_gpt1_flask_b9_server.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_b9_gpt1_flask_b9_server.ps1"
```

## Lancement serveur

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python cockpit_server_b9.py
```

## Validation HTTP

Dans un autre terminal :

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
python test_flask_b9_server.py
```

Attendu : `3/3 PASS`.

## Validation unitaire

Depuis la racine repo :

```powershell
python -m pytest tests/test_cockpit_server_b9_unit.py -v
```

## Notes techniques

- Le serveur ne modifie pas la DB.
- La lecture DB est ouverte en mode read-only SQLite.
- Si `powerflow.db`, `bars_h1` ou `output/b9_nodes_live` manquent, l'endpoint répond quand même en `READING_PARTIAL` avec `technical_risks`.
- Aucun `BUY/SELL`.
- Aucun Telegram.
- Aucun moteur modifié.

## Endpoints

### `/api/health`

Retourne statut serveur + disponibilité des surfaces lues.

### `/api/b9-nodes-live`

Lit les fichiers JSON récents depuis :

```text
output/b9_nodes_live
```

Override possible :

```powershell
$env:B9_NODES_DIR="C:\path\to\b9_nodes_live"
```

### `/api/b8-coalition-context`

Lit `bars_h1` dans `powerflow.db` et retourne :

```text
usd_quote
usd_base
gbp_cross
coalitions
data_visibility
technical_risks
```

Override possible :

```powershell
$env:POWERFLOW_DB_PATH="C:\path\to\powerflow.db"
```
