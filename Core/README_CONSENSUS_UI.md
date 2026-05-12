# README — CONSENSUS_DIVERGENCE_UI

## Rôle

`CONSENSUS_DIVERGENCE_UI` respecte la dualité PowerFlow :

```text
Legacy / HMM
Rolling / Wavelet
```

Doctrine UI :

```text
Default = consensus synthétique, 1 bloc.
Divergence significative = 2 blocs côte à côte.
Pas de fusion forcée.
Pas de censure de la dualité.
```

## Fichiers

```text
dashboard_consensus_divergence_builder.py
run_consensus_divergence_builder.py
dashboard_live_v7.2.1_consensus.html
install_consensus_ui.ps1
README_CONSENSUS_UI.md
```

## Inputs

Demandés par mission :

```text
output/dashboard_surface/regime_legacy.json
output/dashboard_surface/regime_hmm.json
output/temporal_density_state.json
output/dashboard_surface/wavelet.json
```

Compatibilité PowerFlow MultiSymbol :

si les fichiers exacts n’existent pas, le builder cherche aussi :

```text
output/dashboard_surface/{symbol}/regime_legacy.json
output/dashboard_surface/{symbol}/regime_hmm.json
output/temporal_density_state_{symbol}.json
output/dashboard_surface/{symbol}/wavelet.json
```

## Commande

```powershell
python run_consensus_divergence_builder.py --output output/dashboard_surface/consensus_divergence.json --pretty
```

Avec fallback symbole :

```powershell
python run_consensus_divergence_builder.py --symbol GBPUSD --output output/dashboard_surface/consensus_divergence.json --pretty
```

## Règles Regime

Consensus si :

```text
regime_legacy == regime_hmm
ET
abs(confidence_legacy - confidence_hmm) < 0.15
```

Divergence si :

```text
regime_legacy != regime_hmm
OU
abs(confidence_legacy - confidence_hmm) >= 0.15
```

## Règles Density

Consensus si :

```text
au moins 75% des devises comparables ont le même cycle_state
```

Divergence si :

```text
moins de 75% convergent
```

## Output

```text
output/dashboard_surface/consensus_divergence.json
```

## Dashboard

Ouvrir :

```text
dashboard_live_v7.2.1_consensus.html
```

Ce fichier lit :

```text
output/dashboard_surface/consensus_divergence.json
```

## Installation

```powershell
powershell -ExecutionPolicy Bypass -File .\install_consensus_ui.ps1 -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" -Symbol GBPUSD
```

## Commit

```powershell
git add dashboard_consensus_divergence_builder.py
git add run_consensus_divergence_builder.py
git add dashboard_live_v7.2.1_consensus.html
git add README_CONSENSUS_UI.md
git commit -m "P3: add consensus divergence dashboard builder"
git push
```

Ne pas committer :

```text
output/dashboard_surface/consensus_divergence.json
```

C’est un output runtime.
