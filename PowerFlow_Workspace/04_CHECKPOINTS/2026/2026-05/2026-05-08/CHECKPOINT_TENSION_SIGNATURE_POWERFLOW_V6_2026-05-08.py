# CHECKPOINT — TENSION SIGNATURE — POWERFLOW V6
Date : 2026-05-08 — 00h07 CEST
Session : Perplexity PowerFlow Space
Sujet : Construction brique pf_tension_signature + run_ confluence

---

## État au checkpoint

### Briques livrées et testées
pf_tension_signature.py       V0.1.2   ACTIVE — testée sur DB réelle
run_tension_signature_once.py V0.1.3   ACTIVE — cross-TF + replay opérationnels
run_confluence_once.py        V0.2.0   ACTIVE — zone calculée live pf_zone_dynamics

### Dépendances
pf_tension_signature  → stdlib uniquement
run_tension_signature → pf_tension_signature
run_confluence        → pf_tension_signature + pf_zone_dynamics

### DB
force_snapshots_v2 — données depuis 2026-05-06 — live
zone_diagnostics   — NON utilisée (données figées 02/05)

---

## Ce qui a été validé terrain

CHF ELASTIC_LOADED TF1 à 20h50 UTC le 07/05 — confirmé graphique
JPY + CAD ELASTIC_IN_EXTREME en live à 00h04 UTC le 08/05 — TF15 + TF30
Pattern fractal compression multi-échelle — cohérent avec lecture orchestrale

---

## Ce qui reste à faire

[ ] P_NEXT_1 — intégrer tension_signature dans pf_currency_energy_probe
[ ] P_NEXT_2 — backtester sur journée complète avec fenêtre glissante
[ ] P_NEXT_3 — croiser ELASTIC_IN_EXTREME avec relational_gravity (direction)
[ ] P_NEXT_4 — brancher alerte dans behavioral_alert_queue

---

## Contexte session

Point de départ : document GPT académique sur physique computationnelle.
Ce qui a été retenu : tension_signature (micro/macro var) uniquement.
Le reste (Hilbert, DBSCAN, tenseurs 4x4) = décoration non codable en live.

Doctrine respectée :
- Brique indépendante, zéro dépendance pf_*
- Testable immédiatement sur powerflow.db
- Alerter vite, laisser le trader décider
- M1/TF1 central — cross-TF confirme, pas remplace

---

## Commandes utiles

# Live maintenant
python run_confluence_once.py
python run_confluence_once.py --zone-tf 30

# Replay
python run_confluence_once.py --before "2026-05-07T17:50:00+00:00"

# Cross-TF seul
python run_tension_signature_once.py --cross
python run_tension_signature_once.py --cross --before "2026-05-07T20:50:00+00:00"