# POWERFLOW PACKAGING STANDARD — V7.2

## But
Les prochains packs doivent s’installer sans polluer `Core/`.
Le ZIP est extrait dans `.powerflow_packs/<nom_du_pack>/`, les docs vont dans `docs/packs/<nom_du_pack>/`, et seuls les fichiers runtime canoniques sont copiés à la racine.

## Commande standard

```powershell
.\install_powerflow_pack.ps1 `
  -ZipPath .\POWERFLOW_V72_DASHBOARD_SURFACE_V6_20260511.zip `
  -CorePath . `
  -ArchiveOldDashboardArtifacts `
  -RunDashboardStack
```

Pour lancer le serveur directement :

```powershell
.\install_powerflow_pack.ps1 `
  -ZipPath .\POWERFLOW_V72_DASHBOARD_SURFACE_V6_20260511.zip `
  -CorePath . `
  -ArchiveOldDashboardArtifacts `
  -RunDashboardStack `
  -Serve
```

## Fichiers canoniques conservés à la racine Core

```text
dashboard_live_v7.2_final.html
dashboard_data_normalizer.py
dashboard_contract_validator.py
dashboard_output_coverage_doctor.py
run_dashboard_live_stack.ps1
```

## Fichiers versionnés archivés

Les fichiers comme `dashboard_live_v7.2_max_v6.html`, `dashboard_data_normalizer_v04.py`, `dashboard_contract_validator_v5.py`, etc. restent dans :

```text
.powerflow_packs/<pack>/
tools/dashboard/
docs/packs/<pack>/
backups/packs/<timestamp>/
```

## Règles

- Ne jamais toucher `capture_bridge.py`.
- Ne jamais écrire manuellement dans `powerflow.db`.
- Ne jamais remplacer un fichier sans backup.
- Le dashboard lit une surface contractuelle, pas directement la DB.
- Les scripts utilitaires doivent avoir un nom canonique stable à la racine.
- Les itérations versionnées doivent rester hors racine pour garder `Core/` lisible.
