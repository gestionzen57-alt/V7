# T0155 — B9 Trader Attention Packet V0

## Résumé

T0155 transforme une scène B9 enrichie, un brief live ou un payload candidat en packet d'attention trader.

Le packet expose :

- raison d'attention ;
- état de scène ;
- zone active ;
- node terrain ;
- verdict prix ;
- rôle de scène ;
- contexte mémoire B6 ;
- risques techniques ;
- points à surveiller ensuite.

## Doctrine

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l'effort.  
Le packet attire l'attention du trader, il ne décide pas.

## États

- `B9_TRADER_ATTENTION_PACKET_READY`
- `B9_TRADER_ATTENTION_PACKET_REVIEW_TECHNICAL_RISK`
- `B9_TRADER_ATTENTION_PACKET_REVIEW_NO_MEMORY_MATCH`
- `BLOCKED_RAW_UNAVAILABLE`
- `BLOCKED_FORBIDDEN_LANGUAGE`

## Limites

Read-only. Aucune DB. Aucun dashboard. Aucun Telegram. Aucun ordre directionnel. Aucun taux de réussite.
