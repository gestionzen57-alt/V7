# REGISTRE_BRIQUES_PATCH_M1_NOISE_USDJPY_DASHBOARD

## Brique — P2_M1_NOISE_RATIO_PROBE

```text
Fichier : pf_m1_noise_ratio_probe.py
Runner  : run_m1_noise_ratio_once.py
Output  : output/force_kinematics_state.json
DB      : read-only
Statut  : livré
```

## Brique — USDJPY_CAPTURE_THIN_DIAGNOSTIC

```text
Fichier : run_usdjpy_capture_diagnostic_once.py
Output  : output/usdjpy_capture_thin_diagnostic.json
DB      : read-only
Statut  : livré
```

## Brique — M1_CONTEXT_DASHBOARD_CARD

```text
Fichier : dashboard_m1_context_card_patch.html
Inject  : dashboard_inject_m1_context_card.py
Source  : output/dashboard_surface/m1_context_score.json
Statut  : livré
```

## Test — COMMANDO_P2_PIPELINE

```text
Fichier : test_commando_p2_pipeline.py
Rôle    : py_compile + noise + m1 context + normalizer + USDJPY diag
Statut  : livré
```

## Interdits

```text
Pas de BUY/SELL
Pas d’écriture DB
Pas de censure M1
Pas de fusion cross-symbol avec per-symbol
```
