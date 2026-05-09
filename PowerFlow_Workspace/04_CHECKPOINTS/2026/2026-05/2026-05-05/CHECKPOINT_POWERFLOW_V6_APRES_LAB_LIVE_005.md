# CHECKPOINT — POWERFLOW V6 — APRÈS LAB LIVE 005

## Statut

```text
LAB LIVE 005 terminé.
Rapport complet créé.
Lexique à intégrer créé.
Node V0.6 validé.
Node V0.7 nécessaire.
```

## Découverte principale

```text
Le node n’est pas un cross.
Le node est une fenêtre d’énergie.
Le même angle crée le range.
Le premier détachement crée l’ignition.
```

## Brique centrale

```text
M1_ALIGNMENT_IGNITION_INSIDE_M5_LOADED_FIELD
```

## État technique

```text
M5 récupéré après correction EA.
M1 / M15 / M30 / H1 ont été stale pendant le Lab.
Capture multi-timeframe à stabiliser avant validation mathématique sérieuse.
```

## Priorité P0

```text
Stabiliser la capture :
- M1 live
- M5 live
- M15 live
- M30/H1 cohérents
```

Commande de contrôle :

```powershell
python .\check_tf_counts.py
```

## Priorité P1

Créer ou étendre :

```text
pf_force_acceleration_probe.py
```

Champs requis :

```text
force
speed
angle
acceleration
angle_cluster
tight_gravity_cluster
first_detachment
relative_freshness
price_break_context
```

## Priorité P2

Temporal Node V0.7 :

```text
angle_state
gravity_state
microstructure_state
acceleration_state
release_state
direction_conflict
visual_node_tf
db_trigger_tf
stale_timeframes
next_watch enrichi
```

## Phrase de reprise

```text
On reprend après LAB LIVE 005 :
le node est une fenêtre d’énergie,
le M1 allume,
le M5 déclenche,
le M15 porte,
le HTF donne le poids,
et il faut maintenant coder angle/gravity/acceleration/first_detachment.
```
