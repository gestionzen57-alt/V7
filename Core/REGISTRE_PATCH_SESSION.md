# REGISTRE PATCH SESSION - PowerFlow V7.2.1

**Patch :** Session Overlay V2 + Dashboard Dual Display
**Date :** 2026-05-11
**Statut :** A commiter dans Git
**Mission :** GPT 1 Session Overlay + Dashboard Dual

## 1. Brique - Session Overlay V2

Fichier : pf_session_overlay.py
Runner : run_session_overlay_once.py
Statut : ACTIVE apres deploiement
Methode : SESSION_OVERLAY_V2_UTC
Couche : 1 - moteur pf_*

### Role
Calcule le contexte de session UTC actif pour qualifier les alertes comportementales.

Sessions :
- ASIAN 22:00-08:00 UTC
- LONDON 07:00-16:00 UTC
- NY 12:00-21:00 UTC
- OVERLAP 12:00-16:00 UTC
- DEAD_ZONE 20:00-22:00 UTC

Phases :
- IGNITION
- MID_SESSION
- CLOSING

Bias :
- EXPANSION_EXPECTED
- MAX_VELOCITY_BATTLEFIELD
- COMPRESSION_EXPECTED
- DEAD_ZONE
- ROTATION_EXPECTED

### Lit
Aucune DB. Aucun fichier requis. Horloge UTC ou timestamp fourni en CLI.

### Produit
- output/dashboard_surface/session_context.json
- output/session_context.json

### Depend de
- datetime
- argparse
- json
- pathlib

### Ne depend pas de
- powerflow.db
- capture_bridge.py
- cockpit_*
- dashboard_*
- telegram_*

### Utilise par
- run_session_overlay_once.py
- pf_behavioral_alert_mapper.py apres patch
- dashboard_live.html apres patch

### Limitations
SESSION_TIME_MODEL_STATIC : horaires UTC fixes, jours feries non modelises.
UTC_ONLY : moteur en UTC uniquement.

## 2. Patch - Behavioral Alert Mapper Session Context

Fichier patche : pf_behavioral_alert_mapper.py
Patch utility : patch_behavioral_alert_mapper.py
Statut : ACTIVE apres execution du script deploy
Couche : 1 - mapper pf_*

### Role
Injecte automatiquement session_context dans chaque alerte produite.

### Lit
- pf_session_overlay.get_session_context()
- alertes comportementales en memoire
- output/behavioral_alert_queue.json si enrichment immediat demande

### Produit
Alertes enrichies avec session_context.

### Depend de
- pf_session_overlay.py
- json
- re
- pathlib
- shutil

### Ne depend pas de
- cockpit_*
- dashboard_*
- telegram_*
- powerflow.db en ecriture

### Limitations
MAPPER_PATCH_TEXTUAL : patch non destructif et textuel.
SESSION_CONTEXT_IMPORT_FAILED : risque technique si import impossible.

## 3. Patch - Dashboard Dual Display Hardening

Fichier patch : dashboard_dual_display_patch.html
Fichier cible : dashboard_live.html ou dashboard_live_v7.2*.html
Statut : ACTIVE apres insertion avant body
Couche : 3 - dashboard

### Role
Durcit l'affichage dashboard :
- FRESHNESS visible
- B1 Legacy / B1+ HMM cote a cote
- B4 Rolling / B4+ Wavelet cote a cote
- Session Overlay Card visible
- MISSING DATA explicite
- data-brick / data-method / data-symbol visibles
- timestamp UTC + age_seconds visibles

### Lit
- output/dashboard_surface/session_context.json
- output/dashboard_surface/regime_legacy.json
- output/dashboard_surface/regime_hmm.json
- output/dashboard_surface/temporal_density_state.json
- output/dashboard_surface/wavelet.json
- fallback output/*.json legacy

### Produit
Affichage HTML/CSS/JS.

### Depend de
- fetch API navigateur
- JSON surface output
- HTML/CSS/JS

### Limitations
DASHBOARD_FETCH_PATHS : chemins JSON doivent etre servis par le dashboard.
STALE_BY_TIMESTAMP : freshness depend de timestamp/timestamp_utc.

## 4. Tests

Fichier : test_session_overlay.py

Cas :
- 22:15 UTC = ASIAN / IGNITION
- 07:05 UTC = LONDON / IGNITION
- 13:30 UTC = OVERLAP / MAX_VELOCITY_BATTLEFIELD
- 20:30 UTC = DEAD_ZONE
- session_context injection sur alerte dict
- enrichment queue JSON

## 5. Non-regression

- Ne pas toucher capture_bridge.py.
- Ne pas ecrire dans powerflow.db.
- Ne pas fusionner B1/B1+.
- Ne pas fusionner B4/B4+.
- Ne pas injecter BUY/SELL.
- Ne pas masquer STALE.
- Ne pas masquer MISSING DATA.
- Ne pas importer cockpit_* depuis pf_*.

## 6. Statut documentaire

Ce fichier doit etre commite avec :
- LEXIQUE_PATCH_SESSION.md
- RAPPORT_SESSION_20260511.md

But : permettre au prochain fil Claude de relire directement les termes et briques depuis Git.

