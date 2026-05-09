# PATCH LEXIQUE — Confluence Élastique
**Date :** 2026-05-08  
**Domaine :** Confluence / Tension / Fractalité / Gravity Bridge  
**Fichier :** `PATCH_LEXIQUE_CONFLUENCE_ELASTIC_POWERFLOW_V6_20260508.md`  
**Intégrer dans :** `02_LEXIQUE_GRAMMAIRE_POWERFLOW_V6_ACTIF.md` — Section 11

---

## Nouveaux termes — Section 11 (PATCH)
ELASTIC_IN_EXTREME (EIE)
Devise simultanément :
- en zone active (ACCUMULATING / EXTREME / EARLY_EXTREME / LEAKING)
- avec élastique chargé sur TF1 ET TF5
État de compression maximale multi-couche.
Abréviation affichage : EIE⚡

ELASTIC_WEAK_ZONE (EWZ)
Élastique chargé sur 1 seul TF + zone active.
Compression partielle — tension présente mais non multi-TF.

ELASTIC_NO_ZONE (ENZ)
Élastique chargé sur 2+ TF mais zone non active.
Tension élastique sans ancrage de zone.

ZONE_NO_ELASTIC (ZNE)
Zone active mais aucun élastique chargé.
Zone vivante mais non comprimée.

EIE_PERSISTANT
EIE détecté sur N snapshots consécutifs (N × TF_interval = durée).
Seuil minimum PowerFlow : 2 snapshots = 10 min sur TF5.
Qualification : naissant (1) / confirmé (2+) / établi (3+).

FRACTALITÉ (score 0-3)
Nombre de TF simultanément en zone active (ZONE_ACTIVE_STATES)
parmi [TF15, TF30, TF60].
0 = compression isolée
1 = compression partielle
2 = compression alignée
3 = FULL ALIGN — compression structurelle profonde

Représentation : ███ 3/3 FULL ALIGN ⚡

FRACTAL_ALIGN_WINDOW
Fenêtre temporelle où TF60 > TF30 > TF15 en z_score ET
tous en ZONE_ACTIVE_STATES.
Moment de convergence HTF → MTF → LTF.
Condition nécessaire (pas suffisante) pour ignition.

text

---

## Nouveaux termes — Section : Confluence Gravity Bridge
CONFLUENCE_GRAVITY_BRIDGE
Pont entre signal EIE persistant + fractalité
et structure relationnelle Relational Gravity.
Fichier : pf_confluence_gravity.py

FUSION_STATE (confluence gravity)
État résultant de la fusion EIE × Relational Gravity.

EIE_LEADER_CONFIRMED
Devise EIE est leader RG sur TF fiables.
Confidence : HIGH.

EIE_FOLLOWER_CONFIRMED
Devise EIE est follower du groupe RG dominant.
Confidence : MEDIUM.

EIE_ANTAGONIST
Devise EIE est antagoniste du flux RG.
Confidence : WATCH.
Lecture : compression contre le groupe dominant.

EIE_WITH_RG_CONFLICT
EIE actif mais champ RG conflictuel (topline_reliable=false).
Confidence : WATCH.

EIE_WITH_RG_PARTIAL
EIE actif, RG partiellement alignée (2/3 TF cohérents).
Confidence : WATCH.

EIE_WITH_RG_OUTSIDE
Devise EIE hors groupe RG sur tous les TF.
Confidence : LOW.

EIE_NO_RG_DATA
JSON Relational Gravity indisponibles.
Confidence : LOW.

READ_MODE (confluence gravity)
TOPLINE : topline_reliable=true, lecture directe bridge.
TF_DETAILS : topline_reliable=false, descente dans tf_details.
NO_DATA : JSON manquants.

ROLES_BY_TF
Dictionnaire {TF: role} pour la devise EIE.
role ∈ {leader, follower, antagonist, group_member, outside}

text

---

## Nouveaux termes — Section : Confluence Scan
CONFLUENCE_SCAN
Lecture rétrospective des snapshots DB sur une journée.
Filtre par persistance EIE minimum et session.
Outil : run_confluence_scan.py

SNAPSHOT_CONFLUENCE
Photo de l'état de toutes les devises à un instant T.
État par devise : EIE / ENZ / EWZ / ZNE / NOTHING.

SESSION_EIE_COUNT
Nombre de fois qu'une devise atteint EIE persistant sur la journée.
Indicateur de devise sous tension récurrente.

text

---

## Règles d'usage
FRACTALITÉ ≠ signal.
FRACTALITÉ = qualification de la profondeur de la compression.

EIE_PERSISTANT ≠ ordre.
EIE_PERSISTANT = perception d'une compression qualifiée transmise.

CONFLUENCE_GRAVITY_BRIDGE respecte P1.2 :
Si topline_reliable=false → pas de lecture dominant_leader comme vérité.
Descente obligatoire dans TF_DETAILS.

FRACTAL_ALIGN_WINDOW + EIE_PERSISTANT + EIE_LEADER_CONFIRMED
= combinaison de plus haute qualité perceptive.
Le trader décide s'il y a trade.