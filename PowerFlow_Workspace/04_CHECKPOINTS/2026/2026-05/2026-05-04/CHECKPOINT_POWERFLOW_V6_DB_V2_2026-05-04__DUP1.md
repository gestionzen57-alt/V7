# CHECKPOINT — PowerFlow V6 / DB V2 Extended

Date checkpoint : 2026-05-04  
Contexte : activation de la nouvelle couche `force_snapshots_v2` pour capter les données EA enrichies.

---

## 1. État général

PowerFlow a franchi une étape importante : la base peut maintenant recevoir une couche de données beaucoup plus riche que l’ancien `force_snapshots`.

L’ancienne table reste stable :

```text
force_snapshots = legacy / compatibilité modules existants
```

La nouvelle table devient la sonde complète :

```text
force_snapshots_v2 = EA extended / flux enrichi / future base des agents séquence
```

---

## 2. Patch appliqué

Fichiers patchés :

```text
db.py
capture_bridge.py
```

Fichiers générés/utilisés :

```text
APPLY_EA_EXTENDED_DB_V2_PATCH.py
RUN_APPLY_EA_EXTENDED_DB_V2_PATCH.bat
CHECK_EXTENDED_DB_V2.py
INSPECT_FORCE_SNAPSHOTS_V2.py
```

Backups locaux créés automatiquement :

```text
db_BACKUP_before_ea_v2_*.py
capture_bridge_BACKUP_before_ea_v2_*.py
```

---

## 3. Table ajoutée

Table créée :

```text
force_snapshots_v2
```

Colonnes principales :

```text
created_at
symbol
timeframe

bar_time
bar_close_time
server_time
capture_time
is_closed_bar

bid
ask
mid

spread
spread_points
spread_price
spread_pips

open
high
low
close
tick_volume

pip_range
pip_body
pip_change

force_gbp
force_usd
force_eur
force_jpy
force_cad
force_chf
force_aud
force_nzd
```

---

## 4. Validation DB

La table `force_snapshots_v2` existe et reçoit des lignes.

Validation observée :

```text
force_nzd       OK
open/high/low   OK
close           OK
tick_volume     OK
pip_range       OK
pip_body        OK
pip_change      OK
spread_points   OK
spread_price    OK
spread_pips     OK
bid/ask/mid     OK
bar_time        OK
capture_time    OK
is_closed_bar   OK
```

Exemple observé :

```text
TF60
tick_volume = 8649
pip_range = 34.2
pip_body = 21.0
pip_change = -21.0
force_nzd = 35.6935
```

---

## 5. Statut des timeframes

Dernier état observé :

```text
force_snapshots_v2 reçoit :
TF30
TF60
TF240
TF1440
TF10080
```

Manque encore à valider proprement pour le scalp :

```text
TF1
TF5
TF15
```

Ces TF doivent venir des EA dédiés M1/M5/M15 avec payload extended.

---

## 6. Diagnostic technique

### Ce qui est validé

```text
db.py V2 : OK
insert_force_snapshot legacy + v2 : OK
capture_bridge snapshot extended : OK
force_nzd : OK
OHLC : OK
tick_volume : OK
pips : OK
spread détaillé : OK
```

### Ce qui reste à surveiller

```text
Les EA M1/M5/M15 doivent envoyer leurs données sur le bon port.
Le bridge doit afficher [RAW] tf=1 / tf=5 / tf=15.
force_snapshots_v2 doit afficher TF1 / TF5 / TF15.
```

---

## 7. Correction importante à garder

Dans `capture_bridge.py`, `bid` et `close` doivent rester séparés.

Règle correcte :

```python
bid = raw.get("bid")
close = raw.get("close")
ask = raw.get("ask")
mid = raw.get("mid")
```

À éviter :

```python
bid = raw.get("close", raw.get("bid"))
```

Car cela mélange prix live et clôture bougie.

---

## 8. Orientation expérimentale

L’utilisateur veut tester 3 DB pour déterminer le meilleur réglage de scalping.

Architecture recommandée :

```text
EXP_FAST
DB      : powerflow_fast_300.db
Port    : 55555
Lookback: M1 300 / M5 300 / M15 300
But     : capter très vite les pré-signaux

EXP_FRACTAL
DB      : powerflow_fractal_300_600_900.db
Port    : 55556
Lookback: M1 300 / M5 600 / M15 900
But     : lecture imbriquée temps court → tactique → scène

EXP_DEEP
DB      : powerflow_deep_900.db
Port    : 55557
Lookback: M1 900 / M5 900 / M15 900
But     : champ plus stable, bruit réduit
```

Expérience la plus prometteuse pour la vision PowerFlow :

```text
M1  = naissance
M5  = traduction tactique
M15 = validation de scène
```

Donc :

```text
M1 300 / M5 600 / M15 900
```

---

## 9. Commandes de contrôle utiles

Vérifier les tables :

```powershell
python CHECK_EXTENDED_DB_V2.py
```

Inspecter les TF disponibles :

```powershell
python INSPECT_FORCE_SNAPSHOTS_V2.py
```

Contrôle rapide par DB :

```powershell
python -c "import sqlite3; db='powerflow_fast_300.db'; c=sqlite3.connect(db); cur=c.cursor(); print(db); [print(r) for r in cur.execute('select timeframe,count(*),min(created_at),max(created_at) from force_snapshots_v2 group by timeframe order by timeframe')]; c.close()"
```

---

## 10. Verdict checkpoint

PowerFlow dispose maintenant de la bonne fondation pour analyser :

```text
forces multidevises
NZD
OHLC
tick volume
amplitude pips
corps de bougie
variation pip
spread / friction
temps bougie
temps capture
```

La prochaine étape n’est pas de refaire le cockpit.

La prochaine étape logique est :

```text
Sequence Reader V2 branché sur force_snapshots_v2
```

Objectif :

```text
voir la naissance du node
mesurer les angles
mesurer la vitesse
mesurer l’accélération
comparer M1/M5/M15
détecter pré-signal puis confirmation
```
