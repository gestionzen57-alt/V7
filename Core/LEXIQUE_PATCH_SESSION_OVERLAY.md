# Lexique Patch — Session Overlay + Freshness Dashboard

Termes à intégrer dans `LEXIQUE_GRAMMAIRE`.

## SESSION_CONTEXT
Objet JSON injecté dans chaque alerte comportementale. Il décrit la session active, la phase, les minutes depuis ouverture et le biais comportemental. Qualificateur uniquement, jamais filtre.

## SESSION_BIAS
Biais comportemental de session : `EXPANSION_EXPECTED`, `COMPRESSION_EXPECTED`, `ROTATION`, `MAX_VELOCITY_BATTLEFIELD`, `DEAD_ZONE`.

## EXPANSION_EXPECTED
Contexte où le flux peut naturellement libérer une tension plus vite, notamment London ignition ou overlap.

## COMPRESSION_EXPECTED
Contexte où la respiration lente ou le resserrement sont dominants, notamment Asian mid-session.

## MAX_VELOCITY_BATTLEFIELD
État de chevauchement London/NY 12:00-16:00 UTC. Zone de vélocité maximale potentielle. Qualifie, ne décide pas.

## DEAD_ZONE
État temporel 20:00-22:00 UTC. Donne une signature de faible lisibilité ou transition, sans censurer l'alerte.

## MINUTES_SINCE_OPEN
Nombre entier de minutes depuis l'ouverture de la session active ou du bloc temporel actif. Toujours >= 0.

## LONDON_IGNITION
Phase London 07:00-07:45 UTC. Biais `EXPANSION_EXPECTED`.

## NY_IGNITION
Phase NY 12:00-12:45 UTC. Biais par défaut `EXPANSION_EXPECTED`, requalifiable plus tard par contexte HTF.

## ASIAN_TO_LONDON_HANDOVER
Fenêtre de passage Asian closing vers London pre-open/open. Zone de changement de respiration.

## FRESHNESS
État de fraîcheur d'une donnée dashboard : `FRESH`, `AGING`, `STALE`, `MISSING`.

## DATA_BRICK
Attribut HTML traçant la brique source d'un bloc dashboard.

## STALE_DISPLAY
Affichage visuel rouge/grisé pour données périmées. Interdit d'afficher du stale sans signal.

## MISSING_DATA_STATE
État explicite quand la source JSON est absente, vide ou invalide. Interdit de laisser un bloc vide silencieux.

## DUAL_DISPLAY
Affichage simultané de deux méthodes indépendantes sans fusion.

## DUAL_ROW
Rangée dashboard côte à côte pour dual perception : Legacy/HMM ou Rolling/Wavelet.
