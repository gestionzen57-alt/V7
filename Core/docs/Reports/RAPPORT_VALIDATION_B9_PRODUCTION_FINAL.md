# RAPPORT VALIDATION FINALE — Pipeline B9 Production

**Date génération :** 2026-05-19T15:34:51Z  
**Statut global :** ✅ PRODUCTION PIPELINE VALIDÉ  
**Mode Telegram :** OFF / DRY-RUN

---

## 1. Résumé

| Composant | Statut | Détail |
|---|---:|---|
| Flask Server B9+B8 | ✅ | endpoints API |
| B9 Nodes Live | ✅ | count=23 created_during_run=6 |
| Tick Archive | ✅ | count=129203 age_min=-15.544343933333332 |
| Scheduler Runtime | ✅ | created_nodes=6 loops=5 |

---

## 2. Endpoints API

Base URL : `http://localhost:8880`

| Endpoint | Statut |
|---|---:|
| /api/health | ✅ |
| /api/b9-nodes-live | ✅ |
| /api/b8-coalition-context | ✅ |

---

## 3. Nodes B9

Dossier : `C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\output\b9_nodes_live`  
Nombre : `23`

Derniers nodes :

```json
[
  {
    "file": "GBPUSD_20260519T152703.json",
    "node_id": "B9NODE_GBPUSD_COMPAT",
    "symbol": "GBPUSD",
    "verdict": {
      "status": "ok",
      "symbol": "GBPUSD",
      "price_verdict_candidate": "PENDING",
      "price_confirmation": "PENDING",
      "limits": [
        "compatibility facade",
        "price verdict minimal"
      ],
      "verdict": "INCONCLUSIVE",
      "confidence": 0.0
    },
    "mtime_utc": "2026-05-19T15:27:03.937757Z"
  },
  {
    "file": "GBPUSD_20260519T153203.json",
    "node_id": "B9NODE_GBPUSD_COMPAT",
    "symbol": "GBPUSD",
    "verdict": {
      "status": "ok",
      "symbol": "GBPUSD",
      "price_verdict_candidate": "PENDING",
      "price_confirmation": "PENDING",
      "limits": [
        "compatibility facade",
        "price verdict minimal"
      ],
      "verdict": "INCONCLUSIVE",
      "confidence": 0.0
    },
    "mtime_utc": "2026-05-19T15:32:03.374556Z"
  },
  {
    "file": "GBPUSD_20260519T153219.json",
    "node_id": "B9NODE_GBPUSD_COMPAT",
    "symbol": "GBPUSD",
    "verdict": {
      "status": "ok",
      "symbol": "GBPUSD",
      "price_verdict_candidate": "PENDING",
      "price_confirmation": "PENDING",
      "limits": [
        "compatibility facade",
        "price verdict minimal"
      ],
      "verdict": "INCONCLUSIVE",
      "confidence": 0.0
    },
    "mtime_utc": "2026-05-19T15:32:19.151898Z"
  },
  {
    "file": "GBPUSD_20260519T153311.json",
    "node_id": "B9NODE_GBPUSD_COMPAT",
    "symbol": "GBPUSD",
    "verdict": {
      "status": "ok",
      "symbol": "GBPUSD",
      "price_verdict_candidate": "PENDING",
      "price_confirmation": "PENDING",
      "limits": [
        "compatibility facade",
        "price verdict minimal"
      ],
      "verdict": "INCONCLUSIVE",
      "confidence": 0.0
    },
    "mtime_utc": "2026-05-19T15:33:11.642934Z"
  },
  {
    "file": "GBPUSD_20260519T153458.json",
    "node_id": "B9NODE_GBPUSD_COMPAT",
    "symbol": "GBPUSD",
    "verdict": {
      "status": "ok",
      "symbol": "GBPUSD",
      "price_verdict_candidate": "PENDING",
      "price_confirmation": "PENDING",
      "limits": [
        "compatibility facade",
        "price verdict minimal"
      ],
      "verdict": "INCONCLUSIVE",
      "confidence": 0.0
    },
    "mtime_utc": "2026-05-19T15:34:58.710218Z"
  },
  {
    "file": "GBPUSD_20260519T153605.json",
    "node_id": "B9NODE_GBPUSD_COMPAT",
    "symbol": "GBPUSD",
    "verdict": {
      "status": "ok",
      "symbol": "GBPUSD",
      "price_verdict_candidate": "PENDING",
      "price_confirmation": "PENDING",
      "limits": [
        "compatibility facade",
        "price verdict minimal"
      ],
      "verdict": "INCONCLUSIVE",
      "confidence": 0.0
    },
    "mtime_utc": "2026-05-19T15:36:05.113617Z"
  },
  {
    "file": "GBPUSD_20260519T153703.json",
    "node_id": "B9NODE_GBPUSD_COMPAT",
    "symbol": "GBPUSD",
    "verdict": {
      "status": "ok",
      "symbol": "GBPUSD",
      "price_verdict_candidate": "PENDING",
      "price_confirmation": "PENDING",
      "limits": [
        "compatibility facade",
        "price verdict minimal"
      ],
      "verdict": "INCONCLUSIVE",
      "confidence": 0.0
    },
    "mtime_utc": "2026-05-19T15:37:03.252663Z"
  },
  {
    "file": "GBPUSD_20260519T153711.json",
    "node_id": "B9NODE_GBPUSD_COMPAT",
    "symbol": "GBPUSD",
    "verdict": {
      "status": "ok",
      "symbol": "GBPUSD",
      "price_verdict_candidate": "PENDING",
      "price_confirmation": "PENDING",
      "limits": [
        "compatibility facade",
        "price verdict minimal"
      ],
      "verdict": "INCONCLUSIVE",
      "confidence": 0.0
    },
    "mtime_utc": "2026-05-19T15:37:11.548608Z"
  },
  {
    "file": "GBPUSD_20260519T153817.json",
    "node_id": "B9NODE_GBPUSD_COMPAT",
    "symbol": "GBPUSD",
    "verdict": {
      "status": "ok",
      "symbol": "GBPUSD",
      "price_verdict_candidate": "PENDING",
      "price_confirmation": "PENDING",
      "limits": [
        "compatibility facade",
        "price verdict minimal"
      ],
      "verdict": "INCONCLUSIVE",
      "confidence": 0.0
    },
    "mtime_utc": "2026-05-19T15:38:17.524713Z"
  },
  {
    "file": "GBPUSD_20260519T153923.json",
    "node_id": "B9NODE_GBPUSD_COMPAT",
    "symbol": "GBPUSD",
    "verdict": {
      "status": "ok",
      "symbol": "GBPUSD",
      "price_verdict_candidate": "PENDING",
      "price_confirmation": "PENDING",
      "limits": [
        "compatibility facade",
        "price verdict minimal"
      ],
      "verdict": "INCONCLUSIVE",
      "confidence": 0.0
    },
    "mtime_utc": "2026-05-19T15:39:23.470628Z"
  }
]
```

---

## 4. Tick Archive

```json
{
  "ok": true,
  "db_path": "C:\\Users\\User\\Desktop\\ProjetPowerFlow\\IA\\GPT\\Core\\tick_archive.db",
  "table": "tick_stream",
  "symbol_column": "symbol",
  "timestamp_column": "ts_utc",
  "count": 129203,
  "max_timestamp": "2026-05-19T15:50:30.008Z",
  "age_minutes": -15.544343933333332,
  "max_age_minutes": 5.0
}
```

---

## 5. Scheduler Runtime

```json
{
  "ok": true,
  "before_nodes": 17,
  "after_nodes": 23,
  "created_nodes": 6,
  "loops": 5,
  "duration_seconds": 300
}
```

---

## 6. Activation Telegram

Statut : **NON ACTIVÉ**.

Conditions avant activation :
- endpoints OK ;
- node B9 live créée par scheduler ;
- tick archive frais ;
- message Telegram sans BUY/SELL ;
- phrase finale : `⚡ Perception transmise — Trader filtre.`

---

## 7. Verdict

Pipeline B9 validé côté runtime local.

