# T0166 — B9 Live Data Freshness Guard V0

## Objectif
Qualifier la fraîcheur technique des sources live avant affichage Reality Board, Dashboard ou Telegram preview.

## États
- `LIVE_FRESH`
- `LIVE_STALE`
- `DB_EMPTY`
- `DB_MISSING`
- `TABLE_MISSING`
- `PROXY_ONLY`
- `RAW_TEXTURE_MISSING`
- `SOURCE_LIVE_UNQUALIFIED`
- `LIVE_FRESH_WITH_LIMITS`
- `LIVE_STALE_WITH_MEMORY_CONTEXT`

## Sources inspectées
- `powerflow.db` / `force_snapshots_v2`
- `tick_archive.db` / `tick_stream`
- latest scene candidate B9 si disponible

## Doctrine
B9 ne cherche pas le signal. B9 cherche la trace laissée par l’effort.
Ce guard ne décide pas. Il qualifie la source.

## Limites
Read-only. Aucune DB write. Aucun dashboard live. Aucun Telegram. Aucun ordre directionnel. Aucun taux de réussite.
