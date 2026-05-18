# T0132 — B9 Session Phase Overlay V0

## Résumé

T0132 ajoute une couche session/phase aux moments B9.

Une scène B9 n'a pas la même texture selon qu'elle apparaît en Asian, London, Overlap, NY ou Dead Zone.

## Doctrine

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l'effort.  
Le contexte de session qualifie la scène, il ne décide pas.

## Champs ajoutés

- b9_session_overlay_version
- b9_session
- b9_session_phase
- b9_minutes_since_session_open
- b9_session_bias
- b9_session_context_source
- b9_session_reading_fr
- b9_session_limits

## États

- ASIAN
- LONDON
- OVERLAP
- NY
- DEAD_ZONE
- SESSION_UNKNOWN

## Limites

Read-only. Aucune écriture DB. Aucun dashboard. Aucun Telegram. Aucun BUY/SELL. Aucune probabilité de succès.
