# LEXIQUE PATCH — V7.3.4b B6 PARSER HOTFIX

## RELEASED

État B6 indiquant que la tension live proxy est relâchée ou absorbée.  
Ce n'est pas une absence de lecture. C'est une lecture : le flux ne justifie pas un réveil fort.

## SELL_SIDE

Orientation proxy B6 côté vente.  
Normalisation PowerFlow : `PAIR_DOWN`.

## BUY_SIDE

Orientation proxy B6 côté achat.  
Normalisation PowerFlow : `PAIR_UP`.

## PARTIAL_ABSORPTION

Le proxy order-flow lit une absorption partielle.  
Peut signifier que la pression existe mais n'est pas encore suffisamment propre pour réveil fort.

## B6_CONTEXT_SYMBOL_NOT_RUN

B6 n'est pas exécuté sur une paire de contexte.  
Ce n'est pas un problème si B6 est volontairement limité à la paire tradée.
