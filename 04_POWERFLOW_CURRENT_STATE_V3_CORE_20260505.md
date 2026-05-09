# 04 — POWERFLOW CURRENT STATE V3

Date : 2026-05-05  
Statut : BOUSSOLE ACTIVE V3 — core réel intégré  
Usage : référence courte pour travailler depuis le PC

---

# 1. État du projet

PowerFlow V6 est en état de mutation active vers une chaîne agentique réelle.

Le core fourni montre que plusieurs briques récentes existent déjà :

```text
pf_db_vision_guard.py
pf_flow_event_extractor.py
pf_flow_event_extractor_v02_extended.py
pf_scene_namer.py
pf_fractal_window_engine.py
cockpit_agentic_state_v01.py
telegram_agentic_nodes_v01.py
run_telegram_agentic_nodes_once.py
RUN_TELEGRAM_AGENTIC_NODES_LOOP.ps1
run_powerflow_4_agents_runtime_once.py
```

Conclusion :

```text
PowerFlow n’est plus seulement au stade V6 Foundation.
Il contient déjà un Agentic Core opérationnel à inventorier, stabiliser et nettoyer.
```

---

# 2. Doctrine active

```text
PowerFlow = extension de perception du trader.
Trader = centre vivant.
IA = partenaires spécialisés.
Documents = traces, pas lois.
M1 = microfilm scalping.
Temporal Nodes = centraux.
Alertes précoces = à qualifier, pas censurer.
```

---

# 3. Architecture stricte

```text
capture_*   = acquisition / écrit DB
pf_*        = moteur / calcul / analyse / mémoire
agentic_*   = lecture agentique / nomination / orchestration
cockpit_*   = affichage / lecture / clarification
telegram_*  = transmission d’alertes
DB          = trace / mémoire / comparaison
Trader      = décision finale
```

---

# 4. Core réel — familles principales

## Acquisition / DB

```text
capture_bridge.py
db.py
models.py
system_config.py
utils.py
powerflow.db
powerflow.db-shm
powerflow.db-wal
```

## DB V2 / EA Extended

```text
APPLY_EA_EXTENDED_DB_V2_PATCH.py
RUN_APPLY_EA_EXTENDED_DB_V2_PATCH.bat
CHECK_EXTENDED_DB_V2.py
CHECK_DB_SCHEMA_POWERFLOW.py
FIND_EXTENDED_EA_SCHEMA.py
INSPECT_FORCE_SNAPSHOTS_V2.py
```

## Agentic Core

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
```

## Telegram Agentic Nodes

```text
telegram_agentic_nodes_v01.py
run_telegram_agentic_nodes_once.py
RUN_TELEGRAM_AGENTIC_NODES_LOOP.ps1
```

## Temporal / Nodes

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
```

## Zone / Personality / Battlefield

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

## Legacy moteur / historique

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

## Dashboard / cockpit

```text
dashboard_live.html
dashboard_server.py
dashboard_data.json
cockpit_reader.py
cockpit_alerts.py
cockpit_terminal.py
dashboard_agentic_core_panel_snippet.html
```

---

# 5. Statuts de travail

## ACTIVE_RUNTIME

```text
capture_bridge.py
db.py
models.py
system_config.py
utils.py
powerflow.db
```

## ACTIVE_AGENTIC_CORE

```text
pf_db_vision_guard.py
pf_flow_event_extractor_v02_extended.py
pf_scene_namer.py
pf_fractal_window_engine.py
cockpit_agentic_state_v01.py
```

## ACTIVE_TELEGRAM_AGENTIC

```text
telegram_agentic_nodes_v01.py
run_telegram_agentic_nodes_once.py
RUN_TELEGRAM_AGENTIC_NODES_LOOP.ps1
```

## TEMPORAL_NODES_ACTIVE_LAB

```text
pf_temporal_nodes.py
engine_temporal_nodes.py
pf_bipolar_node_alert.py
pf_temporal_density.py
pf_temporal_patterns.py
pf_temporal_patterns_cockpit.py
```

## ACTIVE_ZONE_BATTLEFIELD

```text
pf_personalities.py
pf_zone_dynamics.py
pf_battlefield_radar.py
pf_battlefield_map.py
pf_cockpit_field.py
pf_coalitions.py
pf_coalition_relations.py
```

## LEGACY_KEEP

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

## BACKUP_KEEP

```text
capture_bridge_BACKUP_before_ea_v2_20260504_174432.py
db_BACKUP_before_ea_v2_20260504_174432.py
dashboard_live old.html
```

---

# 6. Urgence immédiate

P0 :

```text
1. Ne pas nettoyer manuellement le core au hasard.
2. Auditer Temporal Nodes.
3. Produire output/temporal_node_state.json.
4. Définir Telegram Node Mode.
5. Stabiliser la chaîne Agentic Core déjà présente.
```

P1 :

```text
1. Stabiliser cockpit_agentic_state_v01.py ou préparer cockpit_state_v2.
2. Consolider pf_flow_event_extractor_v02_extended.py.
3. Vérifier pf_db_vision_guard.py.
4. Réduire doublons run_* après inventaire.
```

---

# 7. Phrase de reprise

```text
Ne pas ranger tout PowerFlow.
Rendre visible la prochaine brique qui augmente la perception.
```

```text
Priorité : Temporal Nodes lisibles et alertables sans casser l’architecture.
```
