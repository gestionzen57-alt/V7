# README — FLOW_ONTOLOGY_V0

## Mission

Créer une ontologie formelle des comportements détectables par PowerFlow.

PowerFlow ne détecte pas des figures chartistes.
PowerFlow nomme des comportements de flux :

```text
INFLEXION
COMPRESSION
RELEASE
ABSORPTION
TENSION
ROTATION
STRUCTURE
```

## Fichiers

```text
FLOW_ONTOLOGY_V0.md
pf_flow_ontology_validator.py
run_flow_ontology_validator.py
install_ontology.ps1
README_ONTOLOGY.md
```

## Installation

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core

Expand-Archive `
  -Path "C:\Users\User\Downloads\P4_FLOW_ONTOLOGY.zip" `
  -DestinationPath ".\_p4_flow_ontology" `
  -Force

cd .\_p4_flow_ontology

powershell -ExecutionPolicy Bypass -File .\install_ontology.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
```

## Commande manuelle

```powershell
python run_flow_ontology_validator.py --queue output/behavioral_alert_queue.json --output output/flow_ontology_report.json --pretty
```

## Output

```json
{
  "timestamp_utc": "2026-05-11T22:10:00Z",
  "alerts_by_category": {
    "INFLEXION": 3,
    "COMPRESSION": 5,
    "RELEASE": 1,
    "ABSORPTION": 0,
    "TENSION": 2,
    "ROTATION": 0,
    "STRUCTURE": 4
  },
  "ontology_coverage": 0.87
}
```

Le rapport contient aussi :

```text
alerts_total
alerts_classified
alerts_unmapped
classified_alerts
unmapped_alerts
technical_risks
```

## Subtilité

Une alerte non classée n’est pas un échec moteur.

Elle devient :

```text
ONTOLOGY_UNMAPPED_ALERT
```

Cela indique que l’ontologie doit être enrichie.

## Commit

```powershell
git add docs/FLOW_ONTOLOGY_V0.md
git add pf_flow_ontology_validator.py
git add run_flow_ontology_validator.py
git add README_ONTOLOGY.md

git commit -m "P4: add flow ontology validator"
git push
```

Ne pas committer :

```text
output/flow_ontology_report.json
```

C’est un output runtime.

## Contraintes

```text
Pas de BUY/SELL
Pas de DB write
Pas de décision de trade
Ontologie = nommer le flux
Trader = arbitre
```
