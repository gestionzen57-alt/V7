# RAPPORT — TENSION SIGNATURE — POWERFLOW V6
Date : 2026-05-08
Session : Perplexity / PowerFlow Space
Statut : CODEX_READY — briques actives et testées sur DB réelle

---

## 1. Contexte

Session de construction de la brique pf_tension_signature.py.
Point de départ : document GPT contenant des idées académiques non codables.
Extraction : 3 idées concrètes retenues sur l'ensemble du document.
Résultat : 1 brique indépendante + 2 run_ opérationnels.

---

## 2. Briques construites

### pf_tension_signature.py — V0.1.2
Mission : distinguer élastique chargé / devise morte / mouvement directionnel.
Dépendances : stdlib Python uniquement. Zéro import pf_*.
Input : List[float | None] — série brute de force (force_snapshots_v2)
Output : TensionSignature(score, label, micro_var, macro_var, n_bars, note)

Labels :
  ELASTIC_LOADED    score > 2.5   — plate en macro, agitée en micro
  DEAD_CURRENCY     0.35-2.5      — inactive ou en pause
  DIRECTIONAL_MOVE  score < 0.35  — tendance directionnelle
  INSUFFICIENT_DATA n < 6 barres

Constantes calibrées sur force_snapshots_v2 (échelle ~0-100) :
  ELASTIC_THRESHOLD    = 2.5
  DIRECTIONAL_THRESHOLD = 0.35
  DEAD_ABS_THRESHOLD   = 1.0
  MAX_SCORE            = 50.0
  MIN_BARS             = 6

### run_tension_signature_once.py — V0.1.3
Mission : test unitaire sur DB réelle.
Features :
  --tf N        timeframe (default 5)
  --bars N      nombre de barres (default 20)
  --before TS   replay à un moment précis (format ISO UTC)
  --cross       cross-TF check ELASTIC_LOADED sur TF1/TF5/TF15
  --json        sortie JSON brute

### run_confluence_once.py — V0.2.0
Mission : croiser tension signature cross-TF avec zone live calculée à la volée.
Features :
  --before TS   replay
  --zone-tf N   TF de référence pour la zone (default 15)
  --json        sortie JSON brute

Confluence labels (ordre de priorité) :
  ELASTIC_IN_EXTREME   TF1+TF5 ELASTIC + zone ACCUMULATING/EXTREME  ⚡
  ELASTIC_NO_ZONE      TF1+TF5 ELASTIC sans zone active
  ELASTIC_WEAK_ZONE    TF1 ou TF5 ELASTIC + zone active
  ZONE_NO_ELASTIC      zone active sans compression micro
  NOTHING              rien de notable

---

## 3. DB — schéma utilisé

Table principale : force_snapshots_v2
Colonnes force : force_gbp, force_usd, force_eur, force_jpy,
                 force_cad, force_chf, force_aud, force_nzd
Timestamp : created_at (format ISO UTC : 2026-05-07T20:50:00+00:00)
Timeframe : timeframe (1, 5, 15, 30, 60, 240, 1440, 10080)

Données disponibles depuis : 2026-05-06T00:00:00+00:00
TF1 : 2930 lignes | TF5 : 582 | TF15 : 195 | TF30 : 98 | TF60 : 49

Table zone_diagnostics : NON utilisée (données figées du 02/05, test unique).
Zone calculée à la volée via pf_zone_dynamics.analyze_zone_dynamics().

---

## 4. Validations terrain

### Test replay 2026-05-07T20:50:00+00:00
CHF TF1 = ELASTIC_LOADED score 2.62 — confirmé graphique :
CHF en compression micro pendant la chute vers zone basse 25.

### Test maintenant 2026-05-08T00:04 UTC
JPY ELASTIC_IN_EXTREME — TF1=7.41 TF5=4.75 TF15=ACCUMULATING z=76.78
CAD ELASTIC_IN_EXTREME — TF1=17.62 TF5=50.00 TF15=ACCUMULATING z=46.98
Confirmé sur TF15 et TF30.

---

## 5. Observations et limites

- MAX_SCORE = 50.0 nécessaire : valeurs aberrantes ponctuelles font exploser le ratio
- zone_diagnostics non fiable pour le replay — zone calculée live est plus robuste
- Cross-TF MULTI_TF_ELASTIC = compression multi-échelle confirmée = signal fort
- TF15 zone est fractale — visible aussi sur TF30, cohérence confirmée

---

## 6. Prochaines étapes suggérées

P_NEXT_1 : Intégrer tension_signature dans pf_currency_energy_probe
           comme composante supplémentaire du score énergie.

P_NEXT_2 : Ajouter paramètre --before avec fenêtre glissante pour
           backtester sur une journée complète.

P_NEXT_3 : Croiser ELASTIC_IN_EXTREME avec pf_relational_gravity
           pour qualifier la direction de la compression.

P_NEXT_4 : Alerter via behavioral_alert_queue quand
           ELASTIC_IN_EXTREME détecté en live.