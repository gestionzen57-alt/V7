# LEXIQUE PATCH V7.3.6 — Trader Journal J+1

## TRADER_JOURNAL_J1

Objet journalier de revue et d'apprentissage.

Il fige la perception machine du jour et laisse les champs trader/J+1 à compléter.

## J1_REVIEW_PENDING

État indiquant que la revue du lendemain n'est pas encore remplie.

Ce n'est pas une erreur moteur.

## machine_snapshot

Bloc contenant la perception PowerFlow figée : niveaux, sweeps, intention, prédiction, synthèse multiread.

## trader_fields

Bloc éditable par le trader ou par un futur module d'annotation :

```text
htf_manual_read
zones_seen
rotation_seen
correlation_coalition_seen
trader_prediction_next_session
actual_result_next_session
machine_vs_real
trader_vs_real
lesson
```

## machine_vs_real

Comparaison entre la prédiction machine et le résultat réel J+1.

Exemples futurs :

```text
ALIGNED
PARTIAL
WRONG_DIRECTION
NO_RESOLUTION
```

## trader_vs_real

Comparaison entre la lecture trader manuelle et le résultat réel J+1.

## lesson

Apprentissage extrait du décalage ou de la confirmation.

Exemples :

```text
sweep haut validé par acceptation baissière
live PAIR_UP était piège inverse
B6 a anticipé absorption vendeuse
HTF incomplet a rendu la rotation floue
```
