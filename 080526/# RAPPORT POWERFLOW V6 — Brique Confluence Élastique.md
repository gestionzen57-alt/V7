# RAPPORT POWERFLOW V6 — Brique Confluence Élastique
**Date :** 2026-05-08  
**Statut :** ACTIVE_RUNTIME  
**Version brique :** V1.0.0  
**Fichier :** `RAPPORT_POWERFLOW_V6_CONFLUENCE_ELASTIC_20260508.md`

---

## 1. Périmètre de la session

Cette session a construit et validé la **brique Confluence Élastique** de PowerFlow V6.  
La brique détecte les compressions multi-TF (ELASTIC_IN_EXTREME persistant),  
mesure leur gravité fractale, les croise avec Relational Gravity, et alerte en live via Telegram.

---

## 2. Briques produites

### 2.1 `pf_tension_signature.py` (V0.x — existante, non modifiée)
- Calcule la signature de tension par série Z-score par TF.
- Sortie : `TensionSignature(label, score)`.
- Labels : `ELASTIC_LOADED`, `CHARGING`, `NEUTRAL`, `LEAKING`.

### 2.2 `run_confluence_scan.py` (V1.0)
- Lecture historique des snapshots TF5.
- Filtre `--min-persist N` (N × 5 min = persistance minimum EIE).
- Affichage tableau session × devise avec états EIE/EWZ/ZNE.
- Comptage EIE par devise sur la journée.
- Options : `--date`, `--min-persist`, `--zone-tf`, `--summary`.

### 2.3 `run_confluence_alert.py` (V1.0)
- Daemon live — scan toutes les 5 min.
- Détecte ELASTIC_IN_EXTREME persistant (`>= 2 snapshots = 10 min`).
- Calcule fractalité TF15/TF30/TF60 (score 0-3).
- Croise avec `pf_confluence_gravity.py` pour qualification RG.
- Envoie alerte Telegram via `telegram_trader_alert_v01`.
- Anti-spam cooldown 10 min par devise.
- Options : `--once`, `--dry-run`, `--zone-tf`, `--db`, `--env`.

### 2.4 `pf_confluence_gravity.py` (V0.1.0)
- Pont entre EIE persistant et Relational Gravity.
- Lit `output/cockpit_agentic_state_v01.json["relational_gravity"]`.
- Lit `output/relational_gravity_m1/m5/m15_v011.json`.
- Règle P1.2 respectée : si `topline_reliable = false` → descente TF_DETAILS.
- Détecte rôle devise par TF : leader / follower / antagonist / group / outside.
- Sortie `ConfluenceGravityResult` avec `fusion_state` + `confidence`.
- États fusion : `EIE_LEADER_CONFIRMED`, `EIE_FOLLOWER_CONFIRMED`,
  `EIE_ANTAGONIST`, `EIE_WITH_RG_CONFLICT`, `EIE_WITH_RG_PARTIAL`,
  `EIE_WITH_RG_OUTSIDE`, `EIE_NO_RG_DATA`.

---

## 3. Validation live — 2026-05-08

### Scan historique

245 snapshots TF5 — zone TF15
9 moments EIE persistant >= 10 min détectés
Sessions couvertes : ASIA, LON_OPEN, LONDON, PRE_US, US

text

### Distribution EIE par devise
AUD 4x ████
EUR 3x ███
CHF 3x ███
JPY 2x ██
CAD 2x ██
GBP 1x █
USD 1x █
NZD 1x █

text

### Première alerte live reçue
19:35 CEST — Session US
GBP — EIE persistant x2 (10 min)
Telegram ✅ envoyé
Cooldown activé → scan 19:40 : aucun EIE persistant ✅

text

### Observation fractale
Tous TF (15/30/60) : ACCUMULATING sur toutes les devises
→ Champ uniformément tendu en fin de semaine
→ TF60 z > TF30 z > TF15 z sur EUR/GBP/AUD = tension structurelle profonde
→ --zone-tf discriminera en milieu de semaine (TF divergents)

text

---

## 4. Architecture respectée
pf_confluence_gravity.py → lit JSON runtime uniquement
run_confluence_alert.py → appelle telegram_trader_alert_v01 directement
run_confluence_scan.py → lecture DB uniquement
Aucun pf_* ne dépend de cockpit_*
Aucun write dans powerflow.db

text

---

## 5. Fichiers de trace runtime produits
output/confluence_alert_last.json anti-spam cooldown par devise
output/telegram_trader_alert_last.json existant — non modifié

text

---

## 6. P_NEXT réalisés dans cette session

| ID | Mission | Statut |
|----|---------|--------|
| P_NEXT_2 | Fractalité TF15/30/60 dans message Telegram | ✅ DONE |
| P_NEXT_3 | Croiser EIE avec pf_relational_gravity | ✅ DONE |

---

## 7. P_NEXT restants

| ID | Mission | Priorité |
|----|---------|----------|
| P_NEXT_1 | Intégrer tension_signature dans pf_currency_energy_probe | NEXT |
| P_NEXT_4 | Alerter via behavioral_alert_queue quand EIE détecté | NEXT |

---

## 8. Observations de marché

- EIE simultané 4 devises à 10h30 LON_OPEN = nœud institutionnel majeur.
- Pattern AUD/CHF/EUR dominant sur la journée = trio structurel sous tension.
- Session Pre-US 17h30 : USD+CHF+AUD en compression = squeeze avant NY confirmé.
- 22h10 US : AUD EIE isolé = résidu de compression non libéré.