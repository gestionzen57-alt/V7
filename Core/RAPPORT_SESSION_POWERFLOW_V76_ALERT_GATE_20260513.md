# RAPPORT SESSION POWERFLOW V7.6 — Legacy → Spine → Alert Gate

Date : 20260513  
Contexte : reprise fil laggé, consolidation PowerFlow V7 autour des détecteurs legacy rapides et des alertes trader pertinentes.

---

## 1. Objectif de la session

Transformer les signaux legacy rapides de PowerFlow, initialement dispersés et peu exploitables pendant le trading, en une chaîne de perception V7 lisible :

```text
legacy fast detectors
    → bus comportemental
    → readers V7
    → perception spine
    → trader attention packet
    → alert gate pertinente
```

Doctrine respectée :

```text
La machine perçoit.
La machine nomme.
La machine alerte.
Le trader filtre.
Le trader décide.
```

Aucune couche ne décide un trade.  
Les alertes sont des réveils d’attention, pas des ordres.

---

## 2. Problème initial

Les alertes legacy remontaient trop brutes :

```text
APPROACH
EXTREME_HIGH / EXTREME_LOW
COMPRESSION
COMPRESSION_BREAK
TIME-COMP LOCK / BREAK
SLINGSHOT
KISS_REJECT
```

Elles étaient vivantes, rapides, parfois utiles, mais pas encore intégrées dans une lecture V7 :

- trop d’alertes isolées ;
- pas de mémoire comportementale courte ;
- pas de distinction claire entre loading / release / acceptance ;
- pas de déduplication trader ;
- pas de message final compact ;
- décalage potentiel entre `event_at` et `detected_at`.

---

## 3. Patch timestamp / TIME-COMP

### 3.1 capture_bridge.py

Le bridge a été patché pour utiliser le timestamp d’événement fourni par la source quand disponible :

```text
server_time
capture_time
bar_close_time
bar_time
```

But : éviter que tous les ticks soient datés à la réception Python.

### 3.2 engine.py — TIME-COMP

Le legacy TIME-COMP a été transformé en preuve TEMPORAL V7 :

```text
legacy_timecomp_events.jsonl
```

Ajouts :

```text
event_at
detected_at
source=legacy_engine
layer=TEMPORAL
event=TIME_COMP_LOCK / TIME_COMP_BREAK
tf_label
price_from
price_to
ticks
technical_risks
```

Résultat validé :

```text
TIME_COMP_LOCK_ACTIVE
locks=15
tfs=M5,M15,M30,H1,H4
acceptance_zone=1.34923
```

---

## 4. Bus legacy comportemental V7

### 4.1 Fichier créé

```text
output/dashboard_surface/<SYMBOL>/legacy_behavioral_events.jsonl
```

### 4.2 Events captés

Mapping principal :

```text
TIME_COMP_LOCK / BREAK       → TEMPORAL
SLINGSHOT                    → TACTICAL_REARM_RELEASE
KISS_REJECT                  → ZONE_REPULSION
COMPRESSION                  → ELASTIC_LOADING_LEGACY
COMPRESSION_BREAK            → ELASTIC_RELEASE_LEGACY
COMPRESSION_SQUEEZE          → PRESSURE_SQUEEZE
APPROACH                     → CROSS_OR_REJECT_IMMINENT
EXTREME_HIGH / EXTREME_LOW   → ZONE_PRESSURE
FAKEOUT                      → TRAP_OR_REINTEGRATION
SUPER_SWITCH                 → FORCE_SWITCH
CONVERGENCE                  → MULTI_TF_CONVERGENCE
CROSS                        → DOMINANCE_CROSS
```

### 4.3 Résultat validé

Exemple GBPUSD :

```text
LEGACY BEHAVIORAL BRIDGE V7 | WATCH | ELASTIC_RELEASE_LEGACY
attention=WATCH_CONTEXT
bias=PAIR_UP
events=44
layers=TEMPORAL,ZONE_REACTION,ENERGY,TACTICAL
event_types=TIME_COMP_LOCK:25, EXTREME_LOW:4, EXTREME_HIGH:2, COMPRESSION:11, COMPRESSION_BREAK:1, APPROACH:1
roles=TEMPORAL_LOCK:25, ZONE_PRESSURE_LOW:4, ZONE_PRESSURE_HIGH:2, ELASTIC_LOADING_LEGACY:11, ELASTIC_RELEASE_LEGACY:1, CROSS_OR_REJECT_IMMINENT:1
```

---

## 5. Readers V7 ajoutés

### 5.1 pf_temporal_compression_reader_once.py

Lit :

```text
legacy_timecomp_events.jsonl
```

Produit :

```text
time_compression_state.json
time_compression_state.txt
```

États principaux :

```text
TIME_COMP_IDLE
TIME_COMP_LOCK_ACTIVE
TIME_COMP_RELEASE_UP
TIME_COMP_RELEASE_DOWN
TIME_COMP_RELEASE_DOWN_LOCKED
```

### 5.2 pf_legacy_behavioral_bridge_once.py

Lit :

```text
legacy_behavioral_events.jsonl
```

Fallback :

```text
legacy_timecomp_events.jsonl
```

Produit :

```text
legacy_behavioral_state.json
legacy_behavioral_state.txt
```

États principaux :

```text
LEGACY_COMPRESSION_LOADING
ELASTIC_RELEASE_LEGACY
FIRST_RELEASE_NOT_YET_ACCEPTED
```

### 5.3 pf_perception_spine_once.py

Lit :

```text
time_compression_state.json
legacy_behavioral_state.json
```

Produit :

```text
perception_spine.json
perception_spine.txt
```

Film validé :

```text
GBPUSD | PERCEPTION SPINE V7.6 TURBO | WATCH | ELASTIC_RELEASE_LEGACY
attention=WATCH_CLOSE
bias=MIXED
evidence=TEMPORAL_LOCK,ELASTIC_RELEASE,ELASTIC_LOADING
main_conflict=MULTI_TF_COMPRESSION_WITHOUT_RELEASE
next_wake=LOCK_ACCEPTANCE_AFTER_RELEASE
```

### 5.4 pf_trader_attention_packet_once.py

Compresse la Spine en message trader court.

Sortie validée :

```text
GBPUSD | WAKE_TRADER_WITH_TECH_RISK | ELASTIC_RELEASE_LEGACY
bias=MIXED score=86.57 next_wake=LOCK_ACCEPTANCE_AFTER_RELEASE
Élastique legacy relâché — attendre acceptation, second leg ou rejet de zone.
Réveil suivant : acceptation post-release.
watch=LOCK_ACCEPTANCE_AFTER_RELEASE | SECOND_LEG | COUNTER_BREATH | ZONE_REJECTION
conflict=FIRST_RELEASE_NOT_YET_ACCEPTED
```

---

## 6. Runner terminal

### 6.1 Fichier

```text
run_trader_perception_stack_once.py
```

### 6.2 Modes validés

Single symbol :

```powershell
python run_trader_perception_stack_once.py --symbol GBPUSD
```

Multi-symbol compact :

```powershell
python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY
```

Détails :

```powershell
python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY --details
```

Table :

```powershell
python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY --table
```

Watch loop :

```powershell
python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY --table --watch-loop --interval 20
```

### 6.3 Table validée

```text
SYMBOL  ATTN  FILM             BIAS       NEXT             SCORE  RISK
------  ----  ---------------  ---------  ---------------  -----  --------
GBPUSD  WAKE  ELASTIC_RELEASE  MIXED      LOCK_ACCEPTANCE  86.6   TIME,GAP
EURUSD  WAKE  ELASTIC_LOADING  MIXED      TIME_BREAK       74.7   TIME,GAP
USDJPY  WAKE  ELASTIC_RELEASE  PAIR_DOWN  LOCK_ACCEPTANCE  87.6   TIME,GAP
SUMMARY | symbols=3 wake=3 watch=0 observe=0
```

---

## 7. Limite constatée : terminal non suffisant en trading

Le scanner terminal est utile pour debug, mais pas suffisant pendant trading réel, car le trader est concentré ailleurs.

Besoin corrigé :

```text
Ne pas regarder un tableau.
Recevoir une alerte seulement quand c’est pertinent.
```

---

## 8. Alert Gate trader

### 8.1 Fichier

```text
pf_trader_attention_alert_gate_once.py
```

### 8.2 Rôle

Lire :

```text
trader_attention_packet.json
```

Puis alerter seulement si :

```text
premier état pertinent
film changé
release détectée
next_wake changé
score jump
loading très dense
cooldown expiré
```

### 8.3 Anti-spam

Fingerprint :

```text
symbol + film + next_wake + bias + conflict
```

État :

```text
trader_attention_alert_state.json
```

Sorties :

```text
trader_attention_last_alert.json
trader_attention_last_alert.txt
trader_attention_alerts.jsonl
```

### 8.4 Alertes initiales validées

```text
GBPUSD → première perception pertinente
EURUSD → première perception pertinente
USDJPY → première perception pertinente
```

Puis :

```text
DEDUP_COOLDOWN
```

La logique anti-spam est validée.

---

## 9. Alert Loop

### 9.1 Fichier

```text
run_trader_alert_loop.py
```

### 9.2 Commande sans Telegram

```powershell
python run_trader_alert_loop.py --symbols GBPUSD,EURUSD,USDJPY --interval 20
```

### 9.3 Commande avec Telegram

```powershell
$env:POWERFLOW_TELEGRAM_BOT_TOKEN="xxx"
$env:POWERFLOW_TELEGRAM_CHAT_ID="xxx"

python run_trader_alert_loop.py --symbols GBPUSD,EURUSD,USDJPY --interval 15 --release-threshold 65 --loading-threshold 74 --send-telegram
```

### 9.4 Bug détecté

Windows PowerShell en CP1252 ne peut pas afficher :

```text
⚡
```

Erreur :

```text
UnicodeEncodeError: 'charmap' codec can't encode character '\u26a1'
```

Fix immédiat :

```powershell
chcp 65001
$env:PYTHONUTF8=1
```

Fix recommandé code :

```text
Remplacer "⚡ PowerFlow" par "POWERFLOW"
```

---

## 10. État actuel du film marché observé

### GBPUSD

```text
WAKE
ELASTIC_RELEASE_LEGACY
bias=MIXED
next_wake=LOCK_ACCEPTANCE_AFTER_RELEASE
conflict=FIRST_RELEASE_NOT_YET_ACCEPTED
```

Lecture :

```text
Élastique legacy relâché.
Attendre acceptation post-release, second leg, counter breath ou rejet de zone.
```

### EURUSD

```text
WAKE
MULTI_TF_ELASTIC_LOADING
bias=MIXED
next_wake=TIME_COMP_BREAK
```

Lecture :

```text
Élastique multi-TF chargé.
Pas encore release.
Prochain réveil : cassure temporelle.
```

### USDJPY

```text
WAKE
ELASTIC_RELEASE_LEGACY
bias=PAIR_DOWN
next_wake=LOCK_ACCEPTANCE_AFTER_RELEASE
```

Lecture :

```text
Release legacy détectée.
Biais directionnel plus clair que GBPUSD.
Attendre acceptation post-release / second leg / rejet.
```

---

## 11. Risques techniques identifiés

```text
EVENT_TIME_AHEAD_OF_DETECTED_AT
```

Le `event_at` est environ 3h devant `detected_at`.  
Probable offset broker/local interprété UTC.

```text
EVIDENCE_BUS_LTF_MTF_COUNTERFLOW_ACTIVE
```

Conflit LTF / MTF détecté, à garder comme information qualitative, pas blocage.

```text
*_TEMPORAL_GAPS
```

Certaines surfaces temporelles incomplètes.

```text
B8_INSUFFICIENT_CROSS_PAIR_COVERAGE
```

Couverture cross-pair B8 insuffisante pour certaines synthèses.

---

## 12. Conclusion session

La session a transformé PowerFlow d’un moteur d’alertes legacy brutes en chaîne de perception trader :

```text
legacy detector
→ evidence bus
→ behavioral bridge
→ perception spine
→ trader packet
→ alert gate
```

Le terminal est maintenant utile pour debug.  
L’Alert Gate devient la couche pertinente pour trading réel.

État global :

```text
CAPTURE_TIMESTAMP_PATCH_OK
LEGACY_TIMECOMP_JSONL_OK
LEGACY_BEHAVIORAL_BUS_OK
TEMPORAL_READER_OK
BEHAVIORAL_BRIDGE_OK
PERCEPTION_SPINE_OK
TRADER_PACKET_OK
ONE_COMMAND_STACK_OK
MULTI_SYMBOL_SCANNER_OK
TABLE_MODE_OK
WATCH_LOOP_OK
ALERT_GATE_OK
DEDUP_COOLDOWN_OK
TELEGRAM_READY_WITH_UTF8_FIX
```
