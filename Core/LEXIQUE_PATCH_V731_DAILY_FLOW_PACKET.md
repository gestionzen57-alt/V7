# LEXIQUE PATCH — V7.3.1 DAILY_FLOW_PACKET

## DAILY_FLOW_PACKET

Lecture synthétique quotidienne qui relie :

- niveaux
- rejet
- sweep
- intention
- HTF / MTF / LTF
- comparaison trader-machine

Ce n'est pas un signal de trade. C'est une fiche de perception.

## JOURNAL_LEVELS

Bloc structuré contenant :

- high_of_day
- low_of_day
- open
- close
- close_position
- previous_day_high
- previous_day_low

## CLOSE_POSITION

Position de la clôture dans le range courant :

- HIGH_THIRD
- MIDDLE_THIRD
- LOW_THIRD
- UNKNOWN

## TESTED_LEVEL

Niveau touché ou traversé par le prix.

## REJECTED_LEVEL

Niveau traversé puis réintégré ou rejeté selon close / high / low.

## SWEEP_CANDIDATE

Balayage candidat de liquidité :

- HIGH_SWEEP_REJECTED
- LOW_SWEEP_REJECTED

## INTENT_DETECTED

Lecture organique proposée :

- SHORT_ACCUMULATION_OR_DISTRIBUTION_TRAP
- LONG_ACCUMULATION_OR_STOP_HUNT
- DUAL_SWEEP_TRAP_OR_ROTATION
- BUY_PRESSURE_OR_HIGH_ACCEPTANCE
- SELL_PRESSURE_OR_LOW_ACCEPTANCE
- REACTION_ZONE_WAIT_FOR_REJECTION_OR_ACCEPTANCE
- BALANCED_INSIDE_RANGE_OR_PREP

## TRADER_COMPARISON_NOTES

Champs dédiés à l'écart entre ce que V7 voit et ce que le trader voit.
