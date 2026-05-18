# Force Snapshot V2 Adapted DB Patch

## Objet

Adapter `insert_force_snapshot` dans `db.py` pour supporter le schéma courant de `force_snapshots_v2` :

```text
tf, tf_name, shift, gbp, usd...
```

tout en restant compatible avec l'ancien schéma :

```text
timeframe, force_gbp, force_usd...
```

## Choix technique

Le patch ajoute `insert_force_snapshot_v2_adapted(conn, snapshot)` et redéfinit `insert_force_snapshot(conn, snapshot)` en mode schema-aware.

La fonction inspecte les colonnes réelles via `PRAGMA table_info(force_snapshots_v2)` puis insère uniquement les colonnes existantes.

## Sécurité

- Non bloquant.
- `conn.rollback()` en cas d'erreur.
- `INSERT OR IGNORE` pour V2.
- Compatible `tf`/`timeframe`.
- Compatible `gbp`/`force_gbp`.
