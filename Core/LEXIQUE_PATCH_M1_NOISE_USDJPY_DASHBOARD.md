# LEXIQUE_PATCH_M1_NOISE_USDJPY_DASHBOARD

## M1_NOISE_RATIO_PROBE

Brique qui mesure le bruit relatif du microfilm M1 à partir de `force_snapshots` TF1.

## NOISE_RATIO

Ratio entre l’instabilité résiduelle et la variation brute M1. Sert à qualifier M1, jamais à le censurer.

## NOISE_QUALITY

Label comportemental du bruit :

```text
CLEAN
TACTICAL
NOISY_BUT_USABLE
NOISY
```

## FIRST_DETACHMENT

Indication que le dernier résiduel sort de son enveloppe récente. Naissance possible, pas décision.

## IGNITION_CLEAN

Fenêtre M1 en phase ignition avec bruit faible confirmé et relais propre.

## IGNITION_NOISY

Fenêtre M1 exploitable mais bruit Kalman non propre ou non mesuré.

## USDJPY_CAPTURE_THIN_DIAGNOSTIC

Audit read-only de la présence, fraîcheur et densité USDJPY dans `force_snapshots`.

## M1_CONTEXT_SCORE_CARD

Card dashboard qui expose `m1_score`, `exploitability`, `intervention_window`, `technical_risks`.
