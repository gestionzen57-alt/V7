# CHECKPOINT CORE CLEANUP — PowerFlow V6

Date : 2026-05-02  
Statut : CHECKPOINT DE REPRISE APRÈS CLASSIFICATION

---

## 1. État général

PowerFlow V6 n’est pas en refonte.

Il est en phase de :

```text
classification
nettoyage
protection des briques vivantes
rassemblement des fondations
```

Phrase de reprise :

```text
On nettoie le core sans casser les modules vivants.
```

---

## 2. Documents posés

Documents de fondation établis :

```text
PERSONALITY_ZONE_FOUNDATION.md
CORE_CLASSIFICATION.md
CHECKPOINT_CORE_CLEANUP.md
```

Rôle de `PERSONALITY_ZONE_FOUNDATION.md` :

```text
fixer la priorité Personality → Zone Dynamics
mettre TemporalDensity / TemporalWindowActive en stand-by cahier des charges
préparer le test de jonction personality → zone
```

Rôle de `CORE_CLASSIFICATION.md` :

```text
classer les fichiers core
séparer actif / legacy / lab / futur / archive
préparer le ménage sans casser les imports
```

---

## 3. Décision prioritaire verrouillée

Priorité immédiate :

```text
pf_personalities.py
→ pf_zone_dynamics.py
```

Objectif :

```text
rassembler les deux briques vitales
vérifier leur contrat mathématique
tester que l’Index Comportemental alimente correctement Zone Dynamics
```

Phrase noyau :

```text
Personality mesure la tension.
Zone Dynamics nomme l’état du champ.
```

---

## 4. Briques en stand-by assumé

Ne pas coder maintenant :

```text
pf_temporal_density.py
TemporalWindowActive
```

Statut :

```text
CAHIER_DES_CHARGES_FUTUR
```

Raison :

```text
briques majeures mais dépendantes de Personality + Zone Dynamics
```

Ne pas brancher maintenant :

```text
pf_temporal_nodes.py
engine_temporal_nodes.py
pf_bipolar_node_alert.py
Telegram NODE_COMPLET_FULL
Telegram NODE_REPULSION
```

Statut :

```text
LAB_STANDBY_NODE_ALERTS
```

Raison :

```text
grammaire Node pas encore assez finalisée
pas assez stabilisée par le Lab
```

---

## 5. Noyau à ne pas casser

Fichiers à préserver :

```text
capture_bridge.py
db.py
models.py
system_config.py
utils.py
powerflow.db
```

Règle :

```text
ne pas déplacer
ne pas patcher sans raison claire
ne pas brancher de nouvelle logique live dedans
```

Point critique :

```text
capture_bridge.py reste le lanceur vivant.
Ne pas brancher pf_temporal_nodes dans capture_bridge.py maintenant.
```

---

## 6. Chaîne Zone → Cockpit validée mais non prioritaire immédiate

Chaîne existante :

```text
pf_zone_context_logger.py
→ pf_zone_evolution_reader.py
→ pf_fractal_zone_stack.py
→ pf_session_zone_reader.py
→ pf_powerflow_zone_brief.py
→ pf_battlefield_map.py
→ pf_cockpit_field.py
```

Runners :

```text
run_zone_context_logger_once.py
run_zone_context_logger_history.py
run_zone_evolution_report.py
run_fractal_zone_stack_report.py
run_session_zone_report.py
run_powerflow_zone_brief.py
run_battlefield_map.py
run_cockpit_field.py
```

Statut :

```text
VALIDÉE
À GARDER
À NE PAS MÉLANGER TROP VITE AVEC LE DASHBOARD LEGACY
```

Commande de référence :

```powershell
python run_cockpit_field.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --recent-minutes 180 --max-gap-minutes 90 --cluster-gap-minutes 60 --cluster-mode side --max-lines 6 --out cockpit_field.txt
```

---

## 7. Chaîne Radar validée

Fichiers :

```text
pf_coalitions.py
pf_coalition_relations.py
pf_battlefield_radar.py
run_coalition_relations_once.py
run_battlefield_radar_once.py
```

Statut :

```text
VALIDÉE TERRAIN
À GARDER
À RELIER PLUS TARD AU COCKPIT
```

Phrase noyau :

```text
BattlefieldRadar ne dit pas “la fenêtre est ouverte”.
Il dit “ici, une bataille se prépare”.
```

---

## 8. Dashboard / cockpit legacy

Fichiers concernés :

```text
dashboard_server.py
dashboard_live.html
dashboard_data.json
START.py
launcher.py
cockpit_alerts.py
cockpit_reader.py
cockpit_terminal.py
telegram_v6.py
telegram_timing_v6.py
```

Statut :

```text
COCKPIT_PROTOTYPE_LEGACY
À GARDER
INTERFACE À REVOIR PLUS TARD
```

Décision :

```text
le dashboard actuel ne contient pas encore tous les nouveaux éléments
ne pas le refondre avant consolidation Personality + Zone
```

Phrase future :

```text
L’ancien dashboard affichait les signaux.
Le nouveau dashboard doit afficher les fenêtres potentielles en préparation.
```

---

## 9. Test de jonction validé

Nom :

```text
test_pf_personality_zone_bridge.py
```

Mission :

```text
enchaîner pf_personalities + pf_zone_dynamics
sur toutes les devises disponibles dans powerflow.db
```

Sorties attendues par devise :

```text
Z actuel
État de zone
Barres en extrême
Pullbacks
Pullbacks absorbés
Tension score
Note diagnostic
```

Résultat validé :

```text
Devises tested       : 7
Z-series OK          : 7
Zone diagnostics OK  : 7
Failures             : 0

VERDICT: OK - Personality feeds Zone Dynamics
```

Important :

```text
ce test est read-only
ce n’est pas une alerte
ce n’est pas un module cockpit
ce n’est pas Telegram
```

---

## 10. Ménage réalisé — première passe

Dossiers créés :

```text
Archive/backups
Archive/patches
Archive/reports
Archive/extracts
Archive/quarantine
docs
```

Déplacé vers `Archive/backups` :

```text
*_BACKUP_*.py
*_BACKUP_before_*.py
```

Déplacé vers `Archive/patches` :

```text
*.patch
PATCH_NOTE_*.md
PF_*_NOTES.md
INSTALL_runtime_patch_*.bat
TEST_REPORT_*.txt
```

Déplacé vers `Archive/reports` :

```text
*_report.txt
*_test_output.txt
battlefield_map_day.txt
battlefield_map_recent.txt
powerflow_zone_brief*.txt
session_zone_report.txt
zone_evolution_report*.txt
fractal_zone_stack_report.txt
```

Déplacé vers `Archive/extracts` :

```text
extract_*.json
mini.json
powerflow_extraction.json
```

Déplacé vers `Archive/quarantine` :

```text
Copy-Item
py
desktop.ini
test.db
```

Aucun `.py` actif n’a été déplacé.

---

## 11. Fichiers gardés temporairement en racine

```text
cockpit_field.txt
```

Raison :

```text
peut encore être lu par le cockpit 
```

Plus tard, option :

```text
output/cockpit_field.txt
```

---

## 12. Interdictions temporaires

Ne pas faire maintenant :

```text
brancher pf_temporal_nodes dans capture_bridge.py
brancher Telegram NODE_COMPLET_FULL
brancher Telegram NODE_REPULSION
coder pf_temporal_density.py
coder TemporalWindowActive
refondre dashboard_live.html
réorganiser les .py actifs en sous-dossiers
supprimer les backups
```

---

## 13. Reprise opérationnelle conseillée

Étape 1 : validation cockpit field.

```powershell
python run_cockpit_field.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --recent-minutes 180 --max-gap-minutes 90 --cluster-gap-minutes 60 --cluster-mode side --max-lines 6 --out cockpit_field.txt
```

Étape 2 : validation radar.

```powershell
python run_battlefield_radar_once.py --db powerflow.db --scan 240
```

Étape 3 : validation Personality → Zone.

```powershell
python test_pf_personality_zone_bridge.py --db powerflow.db --symbol GBPUSD --tf 5 --bars 200 --lookback 20
```

Étape 4 : seulement après, décider quoi afficher dans Dashboard V2.

---

## 14. Vision Dashboard V2 — notée mais différée

Objectif futur :

```text
vue globale des fenêtres temporelles potentielles en préparation
```

Le Dashboard V2 devra lire :

```text
leaders
derniers acteurs
profils courts / moyens / longs
scènes radar
coalitions / antagonistes
zones en accumulation / fuite / rupture
champs bipolaires
```

Mais :

```text
pas avant consolidation Personality + Zone
```

---

## 15. Verdict 

```text
Le code existe.
Les organes existent.
La priorité est de les faire parler proprement.
```

Action prioritaire :

```text
nettoyer le core
puis tester Personality → Zone Dynamics
```

Action interdite :

```text
ouvrir une fenêtre temporelle active trop tôt
```

Phrase finale :

```text
Avant de faire parler le Cockpit,
on vérifie que les organes internes parlent la même langue.
```

Fin du checkpoint.
