# MISSION DASHBOARD — Agentic Core Panel V0.1

## Décision

Ne pas refondre brutalement `dashboard_live.html`.

Ajouter un pont stable :

```text
4 agents runtime
→ cockpit_agentic_state_v01.json
→ dashboard Agentic Core Panel
```

## Agents connectés

```text
DBVisionGuard
FlowEventExtractor
SceneNamer
FractalWindowEngine
```

## Fichiers à ajouter

```text
cockpit_agentic_state_v01.py
run_cockpit_agentic_state_once.py
dashboard_agentic_core_panel_snippet.html
```

## Commande JSON

```powershell
python run_cockpit_agentic_state_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --visual-htf-story confirmed --out output/cockpit_agentic_state_v01.json --pretty
```

## Intégration dashboard

Insérer le contenu de :

```text
dashboard_agentic_core_panel_snippet.html
```

dans `dashboard_live.html`, sous `COCKPIT FIELD` ou juste avant `DENSITE TEMPORELLE`.

## Règle

```text
Le dashboard lit le JSON.
Il n’appelle pas les agents.
Il n’écrit pas la DB.
```

## Prochaine étape après validation

Créer un refresh automatique côté Windows :

```powershell
while ($true) {
  python run_cockpit_agentic_state_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --visual-htf-story confirmed --out output/cockpit_agentic_state_v01.json
  Start-Sleep -Seconds 15
}
```
