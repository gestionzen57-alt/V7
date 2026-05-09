# CARTOGRAPHIE_ARCHITECTURE_TECHNIQUE_POWERFLOW_V6

**Version :** Mise à jour essentielle — 03/05/2026  
**Projet :** PowerFlow V6  
**Objet :** Cartographie synthétique du Core, sans détail inutile.

---

## 1. Architecture centrale

PowerFlow V6 est organisé en trois couches :

```text
capture_* / bridge / db
Acquisition et stockage.

pf_*
Moteurs de lecture mathématique et comportementale.

dashboard_* / cockpit_* / telegram_*
Affichage, lecture, alertes visuelles ou externes.
```

Règle :

```text
pf_* ne dépend pas du dashboard.
dashboard lit pf_*.
La DB est protégée.
```

---

## 2. Dossiers

```text
Core/
├── Archive/       anciennes versions, backups, fichiers archivés
├── db/            scripts DB / init / maintenance éventuelle
├── docs/          documentation centrale
├── output/        rapports générés
└── __pycache__/   cache Python à ignorer
```

---

## 3. Fichiers d’acquisition / base

### capture_bridge.py

Runtime live / pont acquisition.

### db.py

Interface DB.

### powerflow.db

Base SQLite locale.  
Ne pas pousser sur Git par défaut.  
Attention aux fichiers `powerflow.db-shm` et `powerflow.db-wal`.

### models.py / utils.py / system_config.py

Support structurel.

---

## 4. Anciens moteurs / socle historique

### engine.py

Ancien moteur large / socle historique.

### engine_temporal_nodes.py

Ancien moteur temporal nodes.

### pf_core_metrics.py

Métriques cœur.

### pf_engine_scenes.py / pf_engine_orchestrator.py

Chaîne moteur/scènes historique.

### pf_events.py / pf_flow_nodes.py / pf_memory.py / pf_normalizer.py / pf_zones.py

Briques historiques utiles, à conserver mais ne pas mélanger sans nécessité avec les nouvelles briques V6.

---

## 5. Chaîne Personality / Zone

### pf_personalities.py

Profils devises et index comportemental.

Lit :

```text
rôle
tempo
amplitude normale
volatilité
lag
Z-score comportemental
```

### pf_zone_dynamics.py

Analyse des états de zone.

États principaux :

```text
NEUTRAL
PRE_EXTREME
EARLY_EXTREME
ACCUMULATING
LEAKING
RUPTURE
```

### pf_zone_context_logger.py

Journalise les contextes de zone.

### pf_zone_evolution_reader.py

Lit l’évolution dans le temps.

### pf_fractal_zone_stack.py

Empile les lectures multi-timeframes.

### pf_session_zone_reader.py

Lit les profils par session.

### pf_powerflow_zone_brief.py

Produit une synthèse de zone lisible.

---

## 6. Chaîne Coalitions / Relations / Radar

### pf_coalitions.py

Détecte les coalitions de devises.

Prend en compte :

```text
z-score
pente
courbure
tags communs
compatibilité personality
```

### pf_coalition_relations.py

Analyse la relation entre coalition et antagoniste.

### pf_battlefield_radar.py

Transforme coalitions et relations en scènes Cockpit.

Hiérarchie :

```text
RELATION_ACTIVE > COALITION_STRONG > WATCH
```

### pf_battlefield_map.py

Carte globale des champs de bataille et clusters.

---

## 7. Chaîne Temporal Patterns / Thermodynamique

### pf_temporal_density.py

Moteur pur de densité temporelle V0.1.

États :

```text
COMPRESSED
ACTIVE
NEUTRAL
HOLLOW
DEAD
```

Limite actuelle :

```text
mesure l’activité locale,
mais ne modélise pas encore complètement la release power post-compression.
```

### pf_temporal_patterns.py

Patterns temporels.

### pf_temporal_patterns_cockpit.py

Version cockpit des patterns temporels.

Patterns importants :

```text
PULLURE_ABSORPTION_FIELD
EXTREME_BREATHING_FIELD
ANGULAR_ALIGNMENT_NODE
```

### pf_temporal_nodes.py

Brique temporal nodes / standby ou historique selon usage actuel.

---

## 8. Cockpit / Dashboard

### pf_cockpit_field.py

Produit une sortie Cockpit courte :

```text
FIELD
DOMINANT
OPPOSITE/CONTEXT
CONTESTED_WINDOW
BIPOLAR_FOCUS
BIPOLAR_LIST
TEMPORAL_PATTERNS
```

### dashboard_server.py

Génère `dashboard_data.json`.

Lit :

```text
pf_cockpit_field
pf_temporal_density
powerflow.db en read-only
```

Modes :

```text
python dashboard_server.py --once
python dashboard_server.py --loop
python dashboard_server.py --serve
```

### dashboard_live.html

Interface Cockpit V6.

Affiche :

```text
Cockpit Field
Densité Temporelle
Output brut
Statut DB
```

### cockpit_reader.py / cockpit_terminal.py / cockpit_alerts.py

Anciens ou complémentaires cockpit / terminal / alertes.

---

## 9. Telegram

### telegram_v6.py

Brique Telegram historique.

### telegram_timing_v6.py

Timing Telegram.

Statut recommandé :

```text
à ne pas prioriser avant stabilisation des alertes Cockpit visuelles.
```

---

## 10. Runners utiles

```text
run_cockpit_field.py
run_cockpit_field_temporal.py
run_temporal_density.py
run_temporal_patterns_db_scan.py
run_battlefield_map.py
run_battlefield_radar_once.py
run_coalition_relations_once.py
run_zone_evolution_report.py
run_session_zone_report.py
run_fractal_zone_stack_report.py
```

Ces fichiers servent à lancer les briques sans modifier le moteur.

---

## 11. Tests importants

```text
test_pf_personalities_foundation.py
test_pf_personality_zone_bridge.py
test_pf_coalitions_v01.py
test_pf_coalitions_personality_bridge.py
test_pf_coalition_relations_v01.py
test_pf_coalition_relations_personality_bridge.py
test_pf_battlefield_radar_v01.py
test_pf_battlefield_radar_v02.py
test_pf_battlefield_radar_personality_bridge.py
test_zone_dynamics_context_tags.py
test_live_db.py
```

Règle :

```text
Les tests sont la mémoire froide du système.
Ne pas les supprimer sans raison.
```

---

## 12. Fichiers à ignorer / nettoyer

À ignorer ou archiver :

```text
__pycache__/
*.pyc
*.bak
*_v0xx.py
powerflow.db-shm
powerflow.db-wal
temporal_density.txt
output/*.txt
output/*.json
```

Fichiers présents à surveiller :

```text
pf_temporal_patterns_cockpit.py.bak
pf_zone_context_logger_v011.py
pf_zone_dynamics_v022_context_tags.py
run_*_v02.py
run_*_v03.py
```

Ces fichiers peuvent être archivés si la version principale est validée.

---

## 13. Cartographie fonctionnelle cible

```text
DB / force_snapshots
        ↓
pf_personalities
        ↓
pf_zone_dynamics
        ↓
pf_zone_context_logger / pf_zone_evolution_reader
        ↓
pf_fractal_zone_stack / pf_session_zone_reader
        ↓
pf_coalitions / pf_coalition_relations
        ↓
pf_battlefield_radar / pf_battlefield_map
        ↓
pf_cockpit_field
        ↓
dashboard_server
        ↓
dashboard_live.html
```

Temporal Density et Temporal Patterns se branchent en parallèle dans le Cockpit :

```text
pf_temporal_density
pf_temporal_patterns_cockpit
        ↓
pf_cockpit_field / dashboard_server
```

---

## 14. Priorités architecture

```text
1. Préserver la séparation pf_* / dashboard.
2. Garder la DB en lecture seule pour le dashboard.
3. Ne pas mélanger Telegram avec la logique moteur.
4. Ne pas coder les alertes avant stabilisation du vocabulaire.
5. Garder une cartographie simple et maintenable.
```

---

## 15. Synthèse

PowerFlow V6 Core contient déjà les briques nécessaires pour lire :

```text
personnalités
zones
coalitions
relations
battlefield
densité temporelle
patterns temporels
champ cockpit
```

La prochaine étape n’est pas d’empiler du code, mais de stabiliser :

```text
la fenêtre temporelle
la gate
la release power
la permission HTF
la lecture fractale
```
