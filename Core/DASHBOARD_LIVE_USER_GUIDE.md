# DASHBOARD LIVE USER GUIDE — PowerFlow V7.2

## 1. Accès

Depuis `Core/` :

```powershell
.\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD -Serve
```

Puis ouvrir :

```text
http://localhost:8787/dashboard_live_v7.2_final.html
```

## 2. Commande de refresh avant lecture

```powershell
.\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD
```

Cette commande hydrate les sorties directes, normalise la surface, valide le contrat et génère les rapports doctor.

## 3. Les 7 sections

### Régime HTF

Affiche B1 Legacy et B1+ HMM côte à côte.

Lecture :
- `Legacy` = heuristique robuste.
- `HMM` = probabiliste.
- Divergence = information, jamais erreur.

### Cinématique

Affiche B3 Kalman :
- angle
- speed
- noise_ratio
- first_detachment
- clusters

### Densité temporelle

Affiche B4 Rolling et B4+ Wavelet côte à côte :
- cycle_state
- compression_ratio
- wavelet_power
- dominant_scale

Aucune densité finale unique.

### Gravité relationnelle

Affiche B5 Spearman :
- paires
- rho
- avg_rho
- SYNCHRO / DIVERGENT / CODEPENDANT_EXTREME / MIXED_PROBABILISTE

### Résonance fractale

Affiche B7 :
- RESONANT / LAGGED / DISSONANT / SILENT
- resonant_tfs
- lag_tfs
- score

### Texture volatilité

Affiche B7+ :
- STRUCTURAL
- NEWS_SPIKE
- SESSION_FRICTION
- MM_NOISE
- micro_macro_ratio
- pattern_consistency
- spread state si disponible

### Cascade / Entropy / Session / Data quality / Memory

Affiche :
- event_rate
- events_count
- cascade_building
- duplication_ratio
- burst_score
- shannon_entropy
- session active
- phase
- stale/gaps/no_rows
- pattern hash
- occurrence_count
- outcome_distribution

## 4. États de fraîcheur

```text
LIVE      = donnée fraîche et lisible
STALE     = donnée existante mais trop ancienne
DEGRADED  = payload utile mais timestamp source absent ou incomplet
MISSING   = brique absente ou non produite
ERROR     = JSON illisible, fetch impossible, ou contrat cassé
```

## 5. Monitorer P0

États attendus :

```text
P0 Core Perception  : PASS
P0 Dashboard Flow   : PASS
P0 LTF Data Quality : PASS
P0 Strict Full      : PENDING_DATA_WINDOW tant que fenêtre statistique courte
```

`PENDING_DATA_WINDOW` n’est pas un fail moteur.

## 6. Troubleshooting

### Dashboard vide

Relancer :

```powershell
.\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD
```

### Contract fail

Lire :

```powershell
Get-Content .\output\DASHBOARD_CONTRACT_VALIDATION.md
```

### Runner failed

Lire :

```powershell
.\run_hydration_failure_doctor.ps1 -CorePath .
```

### Source en MISSING

Lire :

```powershell
Get-Content .\output\DASHBOARD_OUTPUT_COVERAGE_DOCTOR.md
```

### JSON avec BOM

Réécrire en UTF-8 sans BOM via `.NET UTF8Encoding($false)`.

## 7. Règle finale

Le dashboard n’est pas un décideur. Il montre ce que la machine perçoit, ce qui manque, ce qui diverge, et ce qui respire.
