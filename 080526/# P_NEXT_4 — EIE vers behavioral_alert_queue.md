# P_NEXT_4 — EIE vers behavioral_alert_queue
**Date :** 2026-05-08  
**Priorité :** NEXT (lundi 11/05)  
**Fichiers cibles :** `run_confluence_alert.py`, `pf_behavioral_alert_mapper.py`

---

## Objectif

Quand `run_confluence_alert.py` détecte un EIE persistant,
écrire un événement structuré dans `behavioral_alert_queue.json`.

---

## Format événement

```json
{
  "type": "ELASTIC_IN_EXTREME",
  "level": "HOT",
  "currency": "GBP",
  "eie_persist": 2,
  "fractal_score": 3,
  "fractal_label": "FULL_ALIGN",
  "fusion_state": "EIE_LEADER_CONFIRMED",
  "confidence": "HIGH",
  "zone_state": "ACCUMULATING",
  "zone_z": 36.13,
  "zone_dir": "HIGH",
  "session": "US",
  "timestamp": "2026-05-08T17:35:00+00:00",
  "source": "run_confluence_alert"
}
```

## Implémentation dans run_confluence_alert.py

```python
def write_eie_to_behavioral_queue(
    currency: str,
    data: dict,
    persist_count: int,
    session: str,
    cg,
    queue_path: Path = Path("output/behavioral_alert_queue.json"),
) -> None:
    event = {
        "type": "ELASTIC_IN_EXTREME",
        "level": "HOT" if cg.confidence == "HIGH" else "WATCH",
        "currency": currency,
        "eie_persist": persist_count,
        "fractal_score": data["fractal_score"],
        "fractal_label": _fractal_label(data["fractal_score"]),
        "fusion_state": cg.fusion_state,
        "confidence": cg.confidence,
        "zone_state": data["zone_state"],
        "zone_z": round(data["zone_z"], 2),
        "zone_dir": data["zone_dir"],
        "session": session,
        "timestamp": iso_now(),
        "source": "run_confluence_alert",
    }

    existing = []
    if queue_path.exists():
        try:
            existing = json.loads(queue_path.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []

    existing.append(event)
    if len(existing) > 200:
        existing = existing[-200:]

    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
```

## Lecture dans pf_behavioral_alert_mapper.py

```python
EIE_EVENT_FRESHNESS_SECONDS = 600  # 10 min

def _read_eie_events(queue_path: Path) -> list:
    if not queue_path.exists():
        return []
    try:
        events = json.loads(queue_path.read_text(encoding="utf-8"))
        now = datetime.now(timezone.utc)
        fresh = []
        for e in events:
            if e.get("type") != "ELASTIC_IN_EXTREME":
                continue
            ts = parse_iso_datetime(e.get("timestamp"))
            if ts and (now - ts).total_seconds() < EIE_EVENT_FRESHNESS_SECONDS:
                fresh.append(e)
        return fresh
    except Exception:
        return []
```

## Règles
run_confluence_alert écrit en append — ne supprime jamais.
pf_behavioral_alert_mapper lit la queue — ne l'écrit pas.
behavioral_alert_queue.json : mémoire courte — max 200 événements.
EIE dans la queue = événement comportemental. Pas un ordre.

text

## Risques techniques
Crash entre détection et write
→ try/except autour du write — ne pas crasher le daemon

Double événement si cooldown non respecté dans la queue
→ filtrer les doublons (currency, timestamp > T-10min) à la lecture

Queue qui grossit indéfiniment
→ trim automatique 200 événements à chaque write