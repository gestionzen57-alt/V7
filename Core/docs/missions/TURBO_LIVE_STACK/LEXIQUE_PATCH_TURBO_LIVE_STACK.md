# LEXIQUE PATCH — TURBO LIVE STACK

## TURBO_LIVE_STACK
Runner composite exécutant le cycle live complet PowerFlow en une seule commande.

## B6_LIVE_FUSION
Fusion entre microstructure proxy B6, Daily Flow Packet, TopDown Reader et Live Decision.

## B6_NO_IMMEDIATE_PRESSURE
État indiquant que la microstructure proxy ne justifie pas de réveil trader immédiat.

## CONFLICT_OR_REINTEGRATION_TEST
Tension entre lecture Daily/TopDown et lecture Live/B6. PowerFlow nomme le conflit sans trancher.

## WAKE_TRADER
Action de transmission indiquant une perception assez chaude pour réveiller l'attention du trader. Ce n'est pas un ordre.

## TELEGRAM_MEMORY_GATE
Gate anti-spam qui empêche la répétition de la même perception pendant une fenêtre de cooldown.