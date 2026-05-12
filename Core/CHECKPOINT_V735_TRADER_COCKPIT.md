# CHECKPOINT V7.3.5 — TRADER COCKPIT

## État

V7.3.5 crée une page frontale trader séparée de l'audit technique.

## Nouveaux fichiers

- `pf_trader_cockpit_once.py`
- `dashboard_trader_cockpit.html`
- `patch_scheduler_turbo_trader_cockpit_v735.py`

## Sorties

- `output/dashboard_surface/trader_cockpit.json`
- `output/dashboard_surface/trader_cockpit.txt`

## Commande test

```powershell
python pf_trader_cockpit_once.py --symbols GBPUSD,EURUSD,USDJPY --trade-symbol GBPUSD --pretty
```

## Page à ouvrir

```text
http://localhost:8787/dashboard_trader_cockpit.html
```

## Rôle

Le trader cockpit affiche :

- action : `WATCH`, `WATCH_ATTENTION`, `WAKE_TRADER`
- synthèse multi-read
- lecture humaine courte
- HTF / Daily / Live / B6
- scénarios de surveillance
- risques techniques utiles

## À ne pas confondre

- `dashboard_live_v7_2_final.html` = audit technique / salle machine
- `dashboard_trader_cockpit.html` = cockpit trader / frontal opérationnel

## Validation attendue

Le trader doit comprendre la situation en 5 secondes.

## Suite logique

1. Installer V7.3.5.
2. Ouvrir `dashboard_trader_cockpit.html` au lieu de l'audit V7.2.
3. Patcher scheduler si la page est validée.
4. Ensuite seulement : nettoyer l'ancienne entrée dashboard ou ajouter un bouton officiel cockpit/audit.
