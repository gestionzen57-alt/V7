# T0167 — B9/B6 Auto Realignment Runner V0

## Objectif
Forcer l’alignement entre la scène B9 courante et la requête mémoire B6 afin d’éviter qu’un brief T0148 assemble une scène actuelle avec une ancienne query B6 non alignée.

## Principe
B9 montre la scène courante. B6 compare les films. T0167 fabrique un payload aligné et vérifie que les films comparés appartiennent au contexte mémoire attendu.

## Sorties
- `B9_B6_AUTO_REALIGNMENT_V0.json`
- `B9_B6_ALIGNED_QUERY_PAYLOAD_V0.json`
- `B9_B6_AUTO_REALIGNMENT_V0.md`
- `B9_B6_AUTO_REALIGNMENT_MATCHES_V0.csv`
- `B9_B6_AUTO_REALIGNMENT_RISKS_V0.csv`

## Limites
Read-only. Aucune DB. Aucun dashboard live. Aucun Telegram. Aucune décision d’exécution. Aucune probabilité de résultat.
