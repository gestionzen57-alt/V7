# LEXIQUE PATCH — SIGNAL_ADAPTIVE_PROFILE

## SIGNAL_ADAPTIVE_PROFILE

Brique PowerFlow qui qualifie l’exploitabilité tactique d’un symbole selon la santé data disponible par timeframe.

## FULL_STACK_SIGNAL_READY

Tous les étages nécessaires sont présents : M1, M5, M15, M30, H1, H4, D1.  
Ce mode indique une perception tactique et structurelle plus complète.

## M1_TACTICAL_THIN_HTF

M1 est vivant et M5 est présent, mais le contexte HTF reste mince.  
Le flux M1 peut être perçu et alerté, mais la structure supérieure n’est pas encore pleine.

## M1_ONLY_NO_RELAY

M1 est vivant mais M5 ne donne pas encore de relais suffisant.  
Alerte possible mais qualifiée comme dégradée.

## DATA_NOT_READY

La donnée n’est pas suffisante pour produire un profil signal exploitable.

## ALLOW_M1_QUALIFIED

Permission perceptive : M1 peut parler avec qualification.  
Ce n’est pas une instruction de trade.

## ALLOW_M1_DEGRADED

Permission perceptive dégradée : M1 visible mais relais absent ou faible.

## HTF_STRUCTURE_WEAK_DO_NOT_BLOCK_M1

Risque technique indiquant que la structure HTF est faible, mais ne doit pas censurer M1.

## SIGNAL_PERMISSION

Champ de sortie qui indique le niveau de permission perceptive du moteur.
