# 05 — CORE INVENTORY REPORT INITIAL

Date : 2026-05-05  
Statut : INVENTAIRE INITIAL basé sur le listing PowerShell fourni  
But : transformer le bazar en carte sans déplacer les fichiers

---

# 1. Verdict rapide

Le core contient plusieurs générations superposées :

```text
V6 Foundation
Zone / Personality / Battlefield
Temporal / Nodes
Agentic Core
DB V2 Extended
Cockpit / Dashboard
Telegram ancien
Telegram Agentic
Runners / tests / rapports
Backups
Legacy moteur
```

Conclusion :

```text
Ne pas nettoyer à la main.
D’abord classer.
Ensuite isoler.
Enfin patcher.
```

---

# 2. Dossiers

```text
Archive     = déjà présent, utile pour legacy / backups / rapports
db          = couche DB ou migrations
docs        = documentation interne historique
output      = sorties live / JSON / txt
__pycache__ = cache Python, non stratégique
```

---

# 3. ACTIVE_RUNTIME

```text
capture_bridge.py
db.py
models.py
system_config.py
utils.py
powerflow.db
```

Risque :

```text
à ne pas casser
à tester avant modification
```

---

# 4. BACKUP_KEEP

```text
capture_bridge_BACKUP_before_ea_v2_20260504_174432.py
db_BACKUP_before_ea_v2_20260504_174432.py
dashboard_live old.html
```

Action :

```text
conserver
déplacer plus tard dans Archive/backups si besoin
```

---

# 5. DB V2 / Schema Tools

```text
APPLY_EA_EXTENDED_DB_V2_PATCH.py
RUN_APPLY_EA_EXTENDED_DB_V2_PATCH.bat
CHECK_EXTENDED_DB_V2.py
CHECK_DB_SCHEMA_POWERFLOW.py
FIND_EXTENDED_EA_SCHEMA.py
INSPECT_FORCE_SNAPSHOTS_V2.py
check_db.py
test_live_db.py
```

Action :

```text
garder
documenter comme outils DB
ne pas relancer patch DB sans backup et intention claire
```

---

# 6. ACTIVE_AGENTIC_CORE

```text
pf_db_vision_guard.py
pf_flow_event_extractor.py
pf_flow_event_extractor_v02_extended.py
pf_scene_namer.py
pf_fractal_window_engine.py
cockpit_agentic_state_v01.py
run_db_vision_guard_once.py
run_flow_event_extractor_once.py
run_flow_event_extractor_v02_extended_once.py
run_fractal_window_once.py
run_scene_report_once.py
run_cockpit_agentic_state_once.py
run_powerflow_4_agents_runtime_once.py
run_powerflow_4_agents_service_once.py
```

Observation :

```text
C’est une chaîne récente et importante.
Elle doit être stabilisée avant de refaire l’interface.
```

---

# 7. ACTIVE_TELEGRAM_AGENTIC

```text
telegram_agentic_nodes_v01.py
run_telegram_agentic_nodes_once.py
RUN_TELEGRAM_AGENTIC_NODES_LOOP.ps1
```

Observation :

```text
Telegram Nodes existe déjà.
Donc la restriction “ne pas activer Telegram Nodes” est obsolète.
```

Action :

```text
auditer
ajouter modes OFF / WATCH / SCALPING / HOT_ONLY
anti-spam
read-only state
```

---

# 8. TEMPORAL_NODES_ACTIVE_LAB

```text
pf_temporal_nodes.py
engine_temporal_nodes.py
pf_bipolar_node_alert.py
pf_temporal_density.py
pf_temporal_patterns.py
pf_temporal_patterns_cockpit.py
run_temporal_density.py
run_temporal_patterns_db_scan.py
run_temporal_patterns_smoke.py
run_cockpit_field_temporal.py
temporal_density.txt
```

Observation :

```text
TemporalDensity existe déjà.
Temporal Patterns existent déjà.
La famille temporelle n’est pas future abstraite : elle est présente dans le core.
```

Action P0 :

```text
auditer dépendances
identifier sorties existantes
produire temporal_node_state.json
ne pas brancher dans capture_bridge.py
```

---

# 9. ACTIVE_ZONE_BATTLEFIELD

```text
pf_personalities.py
pf_zone_dynamics.py
pf_zone_context_logger.py
pf_zone_evolution_reader.py
pf_fractal_zone_stack.py
pf_session_zone_reader.py
pf_powerflow_zone_brief.py
pf_battlefield_map.py
pf_battlefield_radar.py
pf_battlefield_radar_v02.py
pf_coalitions.py
pf_coalition_relations.py
pf_cockpit_field.py
```

Observation :

```text
Fondation forte.
Doublon battlefield_radar / v02 à clarifier.
```

---

# 10. Kinematics / Sequence / Labs

```text
pf_force_kinematics.py
run_force_kinematics_once.py
analyze_powerflow_from_0600_today.py
report_0600_now.md
pf_sequence_reader.py
run_sequence_reader_once.py
sequence_0900_1015.md
kinematics_1200_1430_m30_h1.md
kinematics_1245_1345.md
fractal_window_lab004.txt
scene_report_lab004.txt
```

Action :

```text
classer comme lab / analyse / preuves
ne pas supprimer
utile pour signatures
```

---

# 11. LEGACY_KEEP moteur

```text
engine.py
pf_core_metrics.py
pf_engine_orchestrator.py
pf_engine_scenes.py
pf_events.py
pf_flow_nodes.py
pf_memory.py
pf_normalizer.py
pf_relations.py
pf_zones.py
```

Action :

```text
ne pas supprimer
ne pas refondre maintenant
cartographier dépendances
utiliser comme historique ou moteur utile
```

---

# 12. Dashboard / Cockpit

```text
dashboard_live.html
dashboard_server.py
dashboard_data.json
cockpit_reader.py
cockpit_alerts.py
cockpit_terminal.py
dashboard_agentic_core_panel_snippet.html
cockpit_field.txt
```

Action :

```text
ne pas refaire tout de suite
brancher d’abord un state propre
```

---

# 13. Telegram Legacy

```text
telegram_v6.py
telegram_timing_v6.py
GUIDE_DASHBOARD_TELEGRAM_TIMING.md
```

Action :

```text
garder
comparer avec telegram_agentic_nodes_v01.py
éviter doublon de logique Telegram
```

---

# 14. Tests

```text
test_pf_personalities_foundation.py
test_pf_personality_zone_bridge.py
test_pf_battlefield_radar_personality_bridge.py
test_pf_battlefield_radar_v01.py
test_pf_battlefield_radar_v02.py
test_pf_coalitions_personality_bridge.py
test_pf_coalitions_v01.py
test_pf_coalition_relations_personality_bridge.py
test_pf_coalition_relations_v01.py
test_run_coalition_relations_once_v01.py
test_run_coalition_relations_once_v02.py
test_run_coalition_relations_once_v03.py
test_zone_dynamics_context_tags.py
```

Action :

```text
garder
utiliser pour validation post-nettoyage
```

---

# 15. Doublons / versions à clarifier

```text
pf_battlefield_radar.py / pf_battlefield_radar_v02.py
run_battlefield_radar_once.py / run_battlefield_radar_once_v02.py
pf_zone_context_logger.py / pf_zone_context_logger_v011.py
run_zone_context_logger_once.py / run_zone_context_logger_once_v011.py
pf_zone_dynamics.py / pf_zone_dynamics_v022_context_tags.py
run_coalition_relations_once.py / v02 / v03
weekly_scan_gbpusd.txt / v02 / v03
run_weekly_agent_scan.py / v02 / v03
```

Action :

```text
ne pas supprimer avant test
classer ACTIVE vs LEGACY après exécution des runners
```

---

# 16. Action suivante

P0 recommandé :

```text
1. Auditer temporal family.
2. Auditer telegram_agentic_nodes_v01.py.
3. Identifier si cockpit_agentic_state_v01.py contient déjà temporal_nodes.
4. Créer ou stabiliser output/temporal_node_state.json.
5. Ajouter Telegram Node Mode.
```
