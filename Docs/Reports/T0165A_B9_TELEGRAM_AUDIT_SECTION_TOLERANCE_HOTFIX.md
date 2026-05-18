# T0165A — B9 Telegram Preview Audit Board Section Tolerance Hotfix

## Status
`READY`

## Problème corrigé
Le board T0165/T0166 bloquait `BLOCKED_MISSING_SECTIONS` alors que le preview pouvait contenir les sections avec une variante de format :

```text
B9 voit:
B9 voit :
- B9 voit :
```

## Correctif
Détection de section tolérante par regex :

```text
^\s*(?:[-*]\s*)?SECTION\s*:
```

## Autre amélioration
Le CLI devient non-fatal par défaut : il écrit le board même si le statut est bloqué.  
Pour retrouver le comportement strict :

```powershell
-StrictExit
```

## Contraintes
Aucun envoi Telegram. Aucun credential. Aucune DB. Aucun dashboard live.

## Doctrine
Le message Telegram réveille l’attention, il ne décide pas.
