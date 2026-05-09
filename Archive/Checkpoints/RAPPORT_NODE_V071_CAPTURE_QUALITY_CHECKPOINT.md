# Rapport PowerFlow V6 — Node V0.7.1 Capture Quality / Daily Open

**Date de checkpoint :** 2026-05-06  
**Contexte :** ouverture de nouvelle bougie Daily / flux GBPUSD / Node M1 + M15 actif  
**Statut :** VALIDÉ LOCAL — runner réel OK  
**Fichier moteur concerné :** `pf_temporal_node_state.py`  
**Runner de vérité :** `run_temporal_node_state_once.py`

---

## 1. Résumé exécutif

Le patch **Node V0.7.1** est validé.

La séquence de travail a révélé un point critique : la fraîcheur des timeframes ne devait pas être calculée uniquement contre l’horloge système, mais contre le **timeframe vivant le plus récent dans la DB**.

Avant correction, M5 pouvait apparaître `LIVE` alors qu’il était en réalité très en retard par rapport au M1 vivant.

Après correction, PowerFlow détecte correctement :

```text
M1  = LIVE_REFERENCE
M5  = STALE_RELATIVE_TO_LIVE_REFERENCE
M15 = STALE_RELATIVE_TO_LIVE_REFERENCE
relay_tf_available = false
m5_role_capture = M5_RELAY_MISSING_IN_DB
telegram_gating.effective_state = DEGRADED_WATCH
node_context.m5_role = M5_RELAY_MISSING_IN_DB
```

Conclusion : le moteur ne censure pas le node, mais qualifie correctement la capture.

---

## 2. Classification du travail

### Classification principale

```text
TYPE        : PATCH MOTEUR
PRIORITÉ    : P0 / P0.1
VERSION     : Node V0.7.1
DOMAINE     : capture_quality / scene_structure / telegram_gating
RISQUE      : risque analytique de faux HOT si relay TF absent
RÉSOLUTION  : freshness relative au TF vivant
STATUT      : VALIDÉ
```

### Classification PowerFlow

```text
Freshness dit si on peut croire.
Node State dit ce qui se passe.
Angle/Speed dit comment ça bouge.
Density dit si la fenêtre se charge.
Telegram suit la qualité de capture.
```

### Nature de l’événement technique

```text
Événement : DAILY_OPEN_CAPTURE_DESYNC
Cause     : ouverture Daily + trous/retards de capture M5/M15/M30/H1
Symptôme  : wall_clock_age_minutes trompeur
Impact    : HOT_NODE pouvait rester HOT_READY malgré relay TF absent
Correctif : live_reference_tf + relative_age_minutes
```

---

## 3. Problème identifié

Lors de l’ouverture de nouvelle bougie Daily, les timestamps DB montraient :

```text
M1  latest = 2026-05-06T00:04:00+00:00
M5  latest = 2026-05-05T22:00:00+00:00
M15 latest = 2026-05-05T23:15:00+00:00
```

Mais la première version P0 indiquait :

```text
M5 status = LIVE
M5 age_minutes = 0.0
relay_tf_available = true
telegram_gating = HOT_READY
```

C’était faux au sens PowerFlow, car M5 était stale relativement au M1 vivant.

La faille venait du calcul basé sur :

```text
generated_dt - latest_tf_ts
```

au lieu de :

```text
live_reference_ts - latest_tf_ts
```

---

## 4. Correction V0.7.1

### Nouvelle règle

Le moteur calcule maintenant :

```text
live_reference_ts = timestamp le plus récent parmi tous les TF groupés
live_reference_tf = TF correspondant au timestamp le plus récent
relative_age_minutes = live_reference_ts - latest_tf_ts
```

### Règle M5

```text
M5 stale si relative_age_minutes > 10.0
```

Ce seuil correspond à plus de deux bougies M5 de retard.

### Règle autres TF

```text
TF stale si relative_age_minutes > max(10 min, TF_minutes × 3)
```

### Sortie attendue

```json
{
  "live_reference_tf": "M1",
  "tf_freshness": {
    "M1": {
      "status": "LIVE",
      "relative_age_minutes": 0.0
    },
    "M5": {
      "status": "STALE_RELATIVE_TO_LIVE_REFERENCE",
      "relative_age_minutes": 131.0
    }
  },
  "relay_tf_available": false,
  "m5_role_capture": "M5_RELAY_MISSING_IN_DB"
}
```

---

## 5. Résultat validé localement

Commandes exécutées :

```powershell
python -m py_compile .\pf_temporal_node_state.py

python -c "from pf_temporal_node_state import build_temporal_node_state, write_temporal_node_state; print('API_OK', callable(build_temporal_node_state), callable(write_temporal_node_state))"

python .\run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 180 --timeframes 1,5,15,30,60 --visual-htf-story confirmed --out output\temporal_node_state.json --pretty
```

Résultat API :

```text
API_OK True True
```

Résultat runner :

```text
TEMPORAL_NODE_STATE_OK
db_status=TACTICAL_OK
rows_loaded=135
data_age_minutes=0.0
freshness_gate=LIVE_PERCEPTION_OK
telegram_live_allowed=True
active_count=2
highest_level=HOT_NODE
best_interest=NODE_COMPLET_FULL
dominant_direction=GBP pressure down / USD pressure up
structure_label=M1_MICRO_NODE_BIRTH
fractal_state=LTF_BIRTH_INSIDE_VISUAL_HTF_STORY
extended_micro_window=INACTIVE
```

Résultat capture_quality :

```json
{
  "live_reference_tf": "M1",
  "live_reference_timestamp": "2026-05-06T00:11:00Z",
  "tf_freshness": {
    "M1": {
      "status": "LIVE",
      "rows": 124,
      "relative_age_minutes": 0.0,
      "wall_clock_age_minutes": 0.0
    },
    "M5": {
      "status": "STALE_RELATIVE_TO_LIVE_REFERENCE",
      "rows": 1,
      "relative_age_minutes": 131.0,
      "wall_clock_age_minutes": 0.0
    },
    "M15": {
      "status": "STALE_RELATIVE_TO_LIVE_REFERENCE",
      "rows": 8,
      "relative_age_minutes": 56.0,
      "wall_clock_age_minutes": 0.0
    },
    "M30": {
      "status": "STALE_RELATIVE_TO_LIVE_REFERENCE",
      "rows": 1,
      "relative_age_minutes": 161.0,
      "wall_clock_age_minutes": 0.0
    },
    "H1": {
      "status": "STALE_RELATIVE_TO_LIVE_REFERENCE",
      "rows": 1,
      "relative_age_minutes": 191.0,
      "wall_clock_age_minutes": 12.8
    }
  },
  "relay_tf_available": false,
  "m5_role_capture": "M5_RELAY_MISSING_IN_DB"
}
```

Résultat telegram_gating :

```json
{
  "effective_state": "DEGRADED_WATCH",
  "relay_tf_available": false,
  "m5_role": "M5_RELAY_MISSING_IN_DB",
  "live_allowed": true,
  "telegram_mode": "SCALPING",
  "hot_node_count": 1,
  "degraded_reason": "M5_RELAY_MISSING_IN_DB",
  "note": "HOT candidate present but relay TF degraded — monitor only, do not send live"
}
```

Résultat node_context :

```json
{
  "m1_role": "M1_NODE_ACTIVE",
  "m5_role": "M5_RELAY_MISSING_IN_DB",
  "m15_role": "M15_NODE_ACTIVE",
  "htf_role": "VISUAL_HTF_BATTLE_CONFIRMED"
}
```

---

## 6. Interprétation PowerFlow

Le moteur détecte bien une scène chaude :

```text
scene_type        = HOT_SCENE
active_node_count = 2
fractal_depth     = 2
active_tf_list    = M1 + M15
structure_label   = M1_MICRO_NODE_BIRTH
fractal_state     = LTF_BIRTH_INSIDE_VISUAL_HTF_STORY
dominant_direction = GBP pressure down / USD pressure up
```

Mais la capture indique que le relais M5 est manquant/stale :

```text
M5_RELAY_MISSING_IN_DB
relay_tf_available = false
```

Donc Telegram est correctement dégradé :

```text
HOT_NODE perçu
mais HOT_READY refusé
=> DEGRADED_WATCH
```

Ce comportement respecte la doctrine :

```text
Alerter vite.
Qualifier l’alerte.
Ne pas censurer le node.
Ne pas mentir sur la qualité du flux.
```

---

## 7. Lexique / grammaire Lab à ajouter

### LIVE_REFERENCE_TF

Timeframe le plus récent dans la DB, utilisé comme référence vivante pour évaluer les autres TF.

```text
Exemple : M1 devient LIVE_REFERENCE_TF si M1 a le timestamp le plus récent.
```

### LIVE_REFERENCE_TIMESTAMP

Timestamp le plus récent parmi les TF demandés.

```text
Utilisé pour calculer relative_age_minutes.
```

### RELATIVE_FRESHNESS

Fraîcheur d’un TF mesurée contre le TF vivant le plus récent, pas contre l’horloge système.

```text
relative_age_minutes = live_reference_ts - latest_tf_ts
```

### STALE_RELATIVE_TO_LIVE_REFERENCE

État d’un TF qui n’est plus synchronisé avec le TF vivant.

```text
M5 à 22:00 pendant que M1 est à 00:11 = stale relatif.
```

### M5_RELAY_MISSING_IN_DB

Le M5 ne joue plus son rôle de relais tactique dans la DB.

```text
Le moteur peut percevoir M1/M15, mais la scène doit être qualifiée dégradée.
```

### DEGRADED_WATCH

État Telegram effectif lorsqu’un node existe mais que la capture n’est pas complète.

```text
HOT perçu mais relay TF absent/stale.
```

### DAILY_OPEN_CAPTURE_DESYNC

Désynchronisation de capture observée à l’ouverture d’une nouvelle bougie Daily.

```text
Les TF ne se remettent pas forcément à jour en même temps.
```

### WALL_CLOCK_AGE_TRAP

Piège analytique où l’âge calculé contre l’horloge système paraît bon, alors que le TF est stale par rapport au flux DB.

```text
wall_clock_age_minutes peut valoir 0.0 alors que relative_age_minutes vaut 131.0.
```

### RELAY_TF

Timeframe relais entre la micro-naissance et la fenêtre énergétique.

```text
Pour le scalp actuel : M5 = relay_tf.
```

### HOT_SCENE_DEGRADED_BY_CAPTURE

Scène où des nodes chauds existent, mais où la qualité de capture interdit HOT_READY.

```text
HOT_SCENE + relay_tf_available=false => DEGRADED_WATCH.
```

### M1_MICRO_NODE_BIRTH_INSIDE_HTF_STORY

M1 donne la naissance visible dans une histoire HTF confirmée visuellement.

```text
M1 active le microfilm ; HTF donne la gravité.
```

### M15_SOURCE_WITH_M5_RELAY_MISSING

M15 porte une source/pression, M1 exécute, mais M5 ne relaie pas proprement dans la DB.

```text
À classer comme scène exploitable en Lab, mais capture dégradée.
```

---

## 8. Notes Lab — concepts renforcés

### Même node, qualité différente

Un node peut être réel mais sa transmission Telegram doit être qualifiée par la qualité de capture.

```text
Node visible ≠ Telegram HOT_READY automatique.
```

### M1 reste central

M1 a joué le rôle de TF vivant et de microfilm actif.

```text
M1 = naissance / ignition / microfilm.
```

### M5 est le relais tactique

Le M5 n’est pas seulement un timeframe parmi d’autres. Il est le relais entre M1 et M15.

```text
M1 sans M5 = perception possible mais relay dégradé.
```

### M15 reste fenêtre énergétique

Même stale relatif, M15 peut indiquer une source de pression structurelle, mais sa fraîcheur doit être qualifiée.

```text
M15 source node / M1 active / M5 absent = scène partielle.
```

### Daily open est un régime spécial

L’ouverture Daily peut provoquer des désynchronisations de capture multi-TF.

```text
À traiter comme DAILY_OPEN_CAPTURE_DESYNC.
```

---

## 9. Checkpoint technique

### Fichier validé

```text
pf_temporal_node_state.py
```

### API validée

```text
build_temporal_node_state ✅
write_temporal_node_state ✅
```

### Runner validé

```text
run_temporal_node_state_once.py ✅
```

### DB

```text
powerflow.db : lecture seule côté moteur
capture_bridge.py : non touché
```

### Champs JSON validés

```text
capture_quality ✅
scene_structure ✅
direction_windows ✅
telegram_gating ✅
node_context.m5_role corrigé ✅
```

### Comportement validé

```text
HOT_NODE détecté
capture_quality dégrade si M5 stale
telegram_gating = DEGRADED_WATCH
```

---

## 10. Prochaines évolutions proposées

### V0.7.2 — M5_RELAY_THIN_SAMPLE

Quand M5 est live mais avec très peu de rows :

```text
M5 live mais rows < 2 ou 3
=> relay_tf_available = true
=> relay_quality = THIN
=> pas forcément DEGRADED_WATCH
=> mais note technique
```

### V0.7.3 — DAILY_OPEN_TRANSITION

Ajouter une détection de régime :

```text
si live_reference_ts proche de nouvelle bougie Daily
et plusieurs TF supérieurs stale relatifs
=> DAILY_OPEN_TRANSITION
```

### V0.8 — Angle / Speed / Acceleration

À intégrer plus tard, après stabilisation P0 :

```text
angle_state
speed_state
acceleration_state
first_detachment
same_angle_liquidity_accumulation
```

### V0.9 — Density Context

À brancher ensuite :

```text
density_context
window_charged
density_fade
density_release
```

---

## 11. Message synthétique pour l’architecte

```text
Node V0.7.1 validé localement.

Patch P0 opérationnel :
- capture_quality ajouté
- scene_structure ajouté
- direction_windows ajouté
- telegram_gating ajouté
- API build_temporal_node_state/write_temporal_node_state conservée
- runner réel run_temporal_node_state_once.py validé
- capture_bridge.py non touché
- powerflow.db non écrit

Correction importante :
la freshness est désormais calculée relativement au TF vivant le plus récent dans la DB, via live_reference_tf/live_reference_timestamp, et non uniquement via l’horloge système.

Cas daily open validé :
M1 = LIVE_REFERENCE
M5 = STALE_RELATIVE_TO_LIVE_REFERENCE
M15 = STALE_RELATIVE_TO_LIVE_REFERENCE
relay_tf_available = false
m5_role_capture = M5_RELAY_MISSING_IN_DB
telegram_gating = DEGRADED_WATCH
node_context.m5_role = M5_RELAY_MISSING_IN_DB

Conclusion :
le node reste perçu, mais Telegram HOT est qualifié/dégradé lorsque le relais M5 est absent ou stale.
```

---

## 12. Statut final

```text
NODE V0.7.1 — VALIDÉ
P0 CAPTURE QUALITY — VALIDÉ
SCENE STRUCTURE — VALIDÉ
TELEGRAM GATING — VALIDÉ
FRESHNESS RELATIVE — VALIDÉ
CHECKPOINT ARCHITECTE — PRÊT
```
