# CHECKPOINT POWERFLOW V7.6 — 20260513

## État court

```text
PowerFlow V7.6 dispose maintenant d’une chaîne live exploitable :
legacy fast detectors → V7 behavioral bus → perception spine → trader attention packet → alert gate.
```

---

## Fichiers nouveaux / modifiés

### Patchs appliqués

```text
capture_bridge.py
engine.py
scheduler_powerflow_turbo_wrapper.py       # patch tenté, attention ancienne erreur indentation puis fix partiel
pf_perception_spine_once.py
pf_trader_attention_packet_once.py
run_trader_perception_stack_once.py
```

### Nouveaux modules

```text
pf_temporal_compression_reader_once.py
pf_legacy_behavioral_bridge_once.py
pf_perception_spine_once.py
pf_trader_attention_packet_once.py
pf_trader_attention_alert_gate_once.py
run_trader_perception_stack_once.py
run_trader_alert_loop.py
```

### Patchers utilisés / à conserver en archive

```text
patch_engine_timecomp_v7_fix.py
patch_engine_legacy_behavioral_bus_v7.py
patch_scheduler_perception_spine_v76_fix.py
patch_perception_spine_v76_fix.py
patch_trader_attention_packet_v76_b.py
patch_run_trader_perception_stack_v76_c.py
```

---

## Pipeline live actuel

```text
capture_bridge.py
    ↓
engine.py
    ↓
legacy_timecomp_events.jsonl
legacy_behavioral_events.jsonl
    ↓
pf_temporal_compression_reader_once.py
pf_legacy_behavioral_bridge_once.py
    ↓
pf_perception_spine_once.py
    ↓
pf_trader_attention_packet_once.py
    ↓
pf_trader_attention_alert_gate_once.py
```

---

## Commandes validées

### Stack single symbol

```powershell
python run_trader_perception_stack_once.py --symbol GBPUSD
```

### Stack multi-symbol

```powershell
python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY
```

### Table scanner

```powershell
python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY --table
```

### Watch loop terminal

```powershell
python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY --table --watch-loop --interval 20
```

### Alert gate one-shot

```powershell
python pf_trader_attention_alert_gate_once.py --symbols GBPUSD,EURUSD,USDJPY --pretty
```

### Alert loop

```powershell
python run_trader_alert_loop.py --symbols GBPUSD,EURUSD,USDJPY --interval 20
```

### Alert loop Telegram

```powershell
chcp 65001
$env:PYTHONUTF8=1
$env:POWERFLOW_TELEGRAM_BOT_TOKEN="xxx"
$env:POWERFLOW_TELEGRAM_CHAT_ID="xxx"

python run_trader_alert_loop.py --symbols GBPUSD,EURUSD,USDJPY --interval 15 --release-threshold 65 --loading-threshold 74 --send-telegram
```

---

## Outputs live

### Par symbole

```text
output/dashboard_surface/<SYMBOL>/legacy_timecomp_events.jsonl
output/dashboard_surface/<SYMBOL>/legacy_behavioral_events.jsonl
output/dashboard_surface/<SYMBOL>/time_compression_state.json
output/dashboard_surface/<SYMBOL>/time_compression_state.txt
output/dashboard_surface/<SYMBOL>/legacy_behavioral_state.json
output/dashboard_surface/<SYMBOL>/legacy_behavioral_state.txt
output/dashboard_surface/<SYMBOL>/trader_attention_packet.json
output/dashboard_surface/<SYMBOL>/trader_attention_packet.txt
output/dashboard_surface/<SYMBOL>/trader_attention_alert_state.json
output/dashboard_surface/<SYMBOL>/trader_attention_last_alert.json
output/dashboard_surface/<SYMBOL>/trader_attention_last_alert.txt
```

### Global

```text
output/dashboard_surface/perception_spine.json
output/dashboard_surface/perception_spine.txt
output/dashboard_surface/trader_attention_alerts.jsonl
```

---

## État fonctionnel validé

```text
TIME_COMP bridge écrit bien les locks/breaks.
legacy_behavioral_events.jsonl écrit bien les events legacy.
legacy_behavioral_bridge lit et synthétise.
perception_spine lit correctement les champs du bridge.
trader_attention_packet compresse le message.
runner multi-symbol fonctionne.
table mode fonctionne.
watch-loop fonctionne.
alert gate déclenche puis déduplique.
```

---

## Dernier état de marché observé

```text
GBPUSD | WAKE | ELASTIC_RELEASE_LEGACY | MIXED | next=LOCK_ACCEPTANCE_AFTER_RELEASE
EURUSD | WAKE | MULTI_TF_ELASTIC_LOADING | MIXED | next=TIME_COMP_BREAK
USDJPY | WAKE | ELASTIC_RELEASE_LEGACY | PAIR_DOWN | next=LOCK_ACCEPTANCE_AFTER_RELEASE
```

---

## Bug ouvert

### Encodage Windows

Symptôme :

```text
UnicodeEncodeError: cannot encode ⚡ in cp1252
```

Fix immédiat :

```powershell
chcp 65001
$env:PYTHONUTF8=1
```

Fix recommandé :

```text
Dans pf_trader_attention_alert_gate_once.py :
remplacer "⚡ PowerFlow" par "POWERFLOW"
```

---

## Prochaine étape recommandée

1. Patch permanent encodage-safe du gate.
2. Brancher Telegram sur l’Alert Gate, pas sur les alertes legacy brutes.
3. Ajouter `alert_level` plus fin :
   - INFO
   - WATCH
   - WAKE
   - WAKE_STRONG
4. Ajouter age/freshness dans alert gate pour éviter d’alerter sur packet trop vieux.
5. Stabiliser scheduler seulement après validation de la boucle d’alerte.
