# RAPPORT — V7.3.4b B6 PARSER HOTFIX

## Problème observé

B6 écrivait correctement dans le `.txt` :

```text
state=RELEASED level=INFO tension=32.2 delta=-375.6886
direction=SELL_SIDE absorption=PARTIAL_ABSORPTION imbalance=SELL_DOMINANT alerts=0
```

Mais le normalizer V7.3.4 ne lisait pas ces lignes fallback. Résultat :

```text
B6_STATE_UNKNOWN
bias=UNKNOWN
```

## Correction

Le normalizer B6 lit maintenant :

- `state`
- `level`
- `tension`
- `delta`
- `direction`
- `absorption`
- `imbalance`
- `alerts`

depuis le texte B6 si le JSON n'expose pas ces champs.

## Correction de grammaire directionnelle

- `SHORT_ACCUMULATION` => `PAIR_DOWN`
- `LONG_ACCUMULATION` => `PAIR_UP`
- `SELL_SIDE` / `SELL_DOMINANT` => `PAIR_DOWN`
- `BUY_SIDE` / `BUY_DOMINANT` => `PAIR_UP`

## Doctrine B6

B6 reste une lecture parallèle complète du flux live.  
Les limites de proxy order-flow sont informatives, pas bloquantes.
