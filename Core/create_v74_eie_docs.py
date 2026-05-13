from pathlib import Path

docs = Path("docs/missions/V74_EIE")
docs.mkdir(parents=True, exist_ok=True)

readme = """# Mission V7.4-EIE

## Objectif

Raccorder l'ancienne alerte EIE au socle V7.4.

EIE devient une brique de perception :
- tension elastique
- zone chargee
- fractalite M1/M5/M15
- confluence avec Daily, TopDown, B6, B8, Evidence et Phase

## Commande test dry-run

powershell:
python run_confluence_alert.py --db powerflow.db --symbol GBPUSD --zone-tf 15 --once --dry-run

## Commande Telegram reel

powershell:
python run_confluence_alert.py --db powerflow.db --symbol GBPUSD --zone-tf 15 --once --send

## Sorties attendues

- output/dashboard_surface/GBPUSD/eie_confluence.json
- output/dashboard_surface/GBPUSD/eie_confluence.txt
- output/dashboard_surface/GBPUSD/eie_gravity.json
- output/dashboard_surface/GBPUSD/eie_gravity.txt
- output/dashboard_surface/GBPUSD/eie_telegram_decision.json
- output/dashboard_surface/GBPUSD/eie_telegram_decision.txt
- output/dashboard_surface/eie_alert_queue.json

## Doctrine

EIE detecte.
Evidence Bus articule.
Phase nomme.
Telegram reveille si ACTIVE/HOT et non doublon.
Le trader decide.
"""

checkpoint = """# CHECKPOINT V7.4-EIE

## Etat

Mission preparee.

## A faire

1. Verifier anciens fichiers EIE existants.
2. Adapter pf_confluence_elastic.py au schema force_snapshots_v2.
3. Adapter pf_confluence_gravity.py au contexte V7.4.
4. Ajouter pf_eie_telegram_gate_once.py.
5. Brancher dans run_powerflow_live_stack_once.py.
6. Tester dry-run.
7. Tester Telegram reel.
8. Commit/push.
"""

lexique = """# Lexique V7.4-EIE

## EIE_LOADING
Tension elastique en formation.

## EIE_LOADED
Elasticite chargee.

## EIE_RELEASE_PENDING
Release potentielle proche.

## EIE_CONTEXT_CONFLICT
EIE visible mais contradiction avec B6, B8 ou TopDown.

## TRAP_CONTEXT_ELASTIC_PRESSURE_ALIGNED
EIE aligne avec contexte piege/rejet.
"""

(docs / "README.md").write_text(readme, encoding="utf-8")
(docs / "CHECKPOINT.md").write_text(checkpoint, encoding="utf-8")
(docs / "LEXIQUE_PATCH.md").write_text(lexique, encoding="utf-8")

print("V74_EIE_DOCS_OK")
print(docs)
