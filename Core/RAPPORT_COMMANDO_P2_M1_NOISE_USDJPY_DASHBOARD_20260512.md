# RAPPORT_COMMANDO_P2_M1_NOISE_USDJPY_DASHBOARD_20260512

## Objectif

Livrer le mode commando suivant :

1. Générer `noise_ratio` pour `M1_CONTEXT_SCORE`.
2. Auditer USDJPY capture stale/thin.
3. Préparer card dashboard M1 Context.

## Livrables

```text
pf_m1_noise_ratio_probe.py
run_m1_noise_ratio_once.py
run_usdjpy_capture_diagnostic_once.py
dashboard_m1_context_card_patch.html
dashboard_inject_m1_context_card.py
test_commando_p2_pipeline.py
install_commando_p2.ps1
README_COMMANDO_P2.md
LEXIQUE_PATCH_M1_NOISE_USDJPY_DASHBOARD.md
REGISTRE_BRIQUES_PATCH_M1_NOISE_USDJPY_DASHBOARD.md
validation_checklist.md
```

## Effet attendu

Avant :

```text
M1_CONTEXT_SCORE = HIGH
intervention_window = IGNITION_NOISY
cause = NOISE_RATIO_MISSING_DEFAULT_0_4
```

Après si bruit faible :

```text
noise_ratio < 0.1
intervention_window = IGNITION_CLEAN
```

Si bruit non faible, PowerFlow reste en qualification :

```text
IGNITION_NOISY
MID_SESSION_NOISY
NOISY_BUT_USABLE
```

## Doctrine

M1 n’est jamais bloqué par le bruit. Il est qualifié.
