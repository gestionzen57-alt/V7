# T0137M3 — B9 Lexique FR Trader

## Résumé mission

Mission parallèle 3 exécutée : consolidation d'un lexique français trader B9 sous forme de table :

```text
ENUM_TECHNIQUE -> Français trader -> exemple de phrase B9 -> interdits de formulation
```

Le livrable est documentaire. Il ne modifie aucun moteur, aucune base, aucun dashboard et aucun canal externe.

## Branche proposée

```text
feat/t0137m3-b9-lexique-fr-trader
```

## Fichiers livrés

```text
Docs/LEXIQUE_FR_TRADER_B9_T0137M3.md
Docs/Reports/T0137M3_B9_LEXIQUE_FR_TRADER_REPORT.md
Docs/Reports/MESSAGE_CLAUDE_T0137M3_B9_LEXIQUE_FR_TRADER.md
```

## Sources lues dans le pack

```text
00_START_HERE/00_START_HERE_B9_MAX_WORKSPACE_HANDOFF.md
01_CONTEXT_CORE/01_B9_MAX_CONTEXT_MASTER.md
02_ROADMAP_AND_STATUS/00_CURRENT_STATUS_T0113_T0136.md
02_ROADMAP_AND_STATUS/01_ROADMAP_B9_MAX_V2_T0137_T0157.md
03_MISSION_PROMPTS_PARALLEL/03_MISSION_LEXIQUE_FR_TRADER_B9.md
05_SOURCE_DOCS/12_LEXIQUE_FR_TRADER_POWERFLOW_V767.md
05_SOURCE_DOCS/MISSION_B9_SEQUENCE_SUMMARIZER_V0_1_V1_V2_V3.md
05_SOURCE_DOCS/DELTARIVER_TO_POWERFLOW_B9_WORKSPACE_REPORT_AUDIO.md
05_SOURCE_DOCS/ANALYSE_T009_B9_GBPUSD_20260515_JOURNEE_COMPLETE.md
06_REPORTS_AND_MESSAGES/T0129_B9_EFFORT_RESULT_PROGRESS_SCORER_REPORT.md
06_REPORTS_AND_MESSAGES/T0130_B9_CENTER_PATH_INTERNAL_FILM_REPORT.md
06_REPORTS_AND_MESSAGES/T0134_B9_FRENCH_TRADER_SCENE_REPORT_REPORT.md
06_REPORTS_AND_MESSAGES/T0135_B9_LIVE_SCENE_RECOGNITION_LOOP_REPORT.md
06_REPORTS_AND_MESSAGES/T0136_B9_LIVE_RECOGNITION_RUNTIME_VALIDATION_REPORT.md
```

Aucun `Docs/LEXIQUE_MASTER.md` n'a été trouvé dans le ZIP fourni.

## Points consolidés

### Priorités couvertes

```text
EFFORT_WITHOUT_RESULT       -> effort sans résultat
PROGRESSIVE_WAVE            -> vague progressive
CORRECTIVE_BREATH           -> respiration corrective
CENTER_MIGRATION_DOWN       -> centre de gravité qui descend
RETEST_FAILED               -> retest échoué
FAILED_REINTEGRATION        -> réintégration échouée
PULLBACK_ABSORBED           -> pullback absorbé
ZONE_DEFENDED               -> zone défendue
ZONE_CONSUMED               -> zone consommée
MEMORY_SHIFTED              -> mémoire déplacée
SOURCE_PROXY                -> source proxy
RAW_NUANCED / NUANCED_BY_RAW -> raw nuancé
```

### Enrichissements utiles ajoutés

```text
ABSORPTION_WITH_PROGRESS
ABSORPTION_WITHOUT_PROGRESS
FAILED_DISPLACEMENT
CENTER_LOCKED
STAIR_STEP_PROGRESS_UP / DOWN
ROUND_TRIP_NO_PROGRESS
SPIKE_AND_RETRACE
RETEST_PENDING / RETEST_ACCEPTED
MEMORY_NOT_SHIFTED
FORCE_SNAPSHOT_DERIVED
M1_BAR_PROXY
RAW_UNAVAILABLE
CENTER_PATH_* visibility states
READING_PARTIAL
MICROFILM_MISSING
PACKETS_STALE
HONEST_UNKNOWN
SOURCE_QUALITY_HARD_GATE
```

## Doctrine respectée

- B9 lit la trace laissée par l'effort.
- L'absorption n'est pas transformée en direction.
- La mémoire déplacée est séparée du simple mouvement.
- Les formulations restent descriptives.
- Les sources proxy restent proxy.
- Le raw nuancé ne devient pas une confirmation dure.
- Aucun ordre d'exécution.
- Aucun taux de réussite.
- Aucune écriture `powerflow.db`.
- Aucune écriture `tick_archive.db`.
- Aucun dashboard.
- Aucun Telegram.

## Validation prévue dans les scripts

Le script d'installation :

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0137m3_b9_lexique_fr_trader.ps1"
```

fait automatiquement :

```text
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core
extraction du ZIP depuis Downloads
recherche récursive des fichiers par nom
copie dans Docs/ et Docs/Reports/
py_compile probe documentaire
python -m pytest -q
validation présence des enums prioritaires
```

Le script Git :

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0137m3_b9_lexique_fr_trader.ps1"
```

fait automatiquement :

```text
switch/création branche feat/t0137m3-b9-lexique-fr-trader
python -m pytest -q
validation présence des fichiers et enums
git add uniquement les 3 livrables exacts
commit propre
push origin
affichage lien PR GitHub
```

## Limites / blockers

- Le Core local n'est pas accessible depuis ce workspace : les tests projet réels seront exécutés chez l'utilisateur par les scripts.
- Livrable documentaire uniquement : aucun runner, aucun CLI métier et aucun moteur modifié.
- `Docs/LEXIQUE_MASTER.md` absent du ZIP fourni ; le lexique s'appuie donc sur `12_LEXIQUE_FR_TRADER_POWERFLOW_V767.md` et les rapports disponibles.

## Prochain geste attendu côté architecte

1. Installer le pack.
2. Lire `Docs/LEXIQUE_FR_TRADER_B9_T0137M3.md`.
3. Vérifier si ce lexique doit devenir une section de `LEXIQUE_MASTER.md` ou rester un document B9 spécialisé.
4. Après validation, intégrer les formulations dans les futurs rapports B9/T0134/T0135/T0155.
