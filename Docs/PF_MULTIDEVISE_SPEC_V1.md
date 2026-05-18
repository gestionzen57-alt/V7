# PF_MULTIDEVISE — ARCHITECTURE SPEC V1

**Version:** 1.0  
**Date:** 18 mai 2026  
**Schema:** MULTIDEVISE_CONTEXT_V1  
**Status:** Production-ready  

---

## 🎯 RESPONSABILITÉ UNIQUE

**Question:** *Quel est le contexte relationnel multi-devises pour une scène locale donnée?*

**Réponse:** Contexte qualifié avec coverage/alignment/baskets/patterns/limits.

**Pas:** Décision GBP fort, signal trade, validation B9.

---

## 📐 ARCHITECTURE 5 LAYERS

```
┌─────────────────────────────────────────────┐
│ LAYER 5: Context Assembly (API)             │
│ MultideviseContextBuilder.build_context()   │
└─────────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────────┐
│ LAYER 4: Quality Assessment                 │
│ Coverage / Alignment / Freshness / Conf cap │
└─────────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────────┐
│ LAYER 3: Pattern Detection                  │
│ Coalition USD-quote / Opposition USD-base   │
└─────────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────────┐
│ LAYER 2: Basket Computation                 │
│ GBP basket / USD basket (counts bruts)      │
└─────────────────────────────────────────────┘
                    ↑
┌─────────────────────────────────────────────┐
│ LAYER 1: Data Access (READ-ONLY)            │
│ force_snapshots_v2 / stale detection        │
└─────────────────────────────────────────────┘
```

---

## 🔧 CONTRAT INPUT

```python
MultideviseContextBuilder(db_path).build_context(
    symbol_local: str,           # Ex: "GBPUSD"
    timestamp_utc: str,          # ISO format: "2026-05-18T10:05:00"
    window_seconds: int = 60     # Fenêtre alignment
)
```

---

## 📊 CONTRAT OUTPUT

```json
{
  "schema_version": "MULTIDEVISE_CONTEXT_V1",
  "symbol_local": "GBPUSD",
  "timestamp_utc": "2026-05-18T10:05:00",
  "computed_at_utc": "2026-05-18T10:05:30",
  
  "coverage": "FULL | PARTIAL | THIN | BLIND",
  "coverage_ratio": 1.0,
  "symbols_available": [...13 symbols...],
  "symbols_missing": [],
  "symbols_stale": [],
  
  "alignment": "ALIGNED | PARTIAL | DEGRADED",
  "aligned_symbols": [...],
  "max_skew_seconds": 15,
  
  "gbp_basket": {
    "currency": "GBP",
    "available_symbols": [...7...],
    "missing_symbols": [],
    "direction_up_count": 5,
    "direction_down_count": 1,
    "direction_neutral_count": 1
  },
  
  "usd_basket": {
    "currency": "USD",
    "available_symbols": [...7...],
    "missing_symbols": [],
    "direction_up_count": 2,
    "direction_down_count": 4,
    "direction_neutral_count": 1
  },
  
  "coalition_usd_quote": {
    "pattern_type": "USD_QUOTE_COALITION",
    "symbols_in_pattern": ["GBPUSD","EURUSD","AUDUSD","NZDUSD"],
    "aligned_count": 4,
    "opposed_count": 0,
    "all_aligned_up": true,
    "all_aligned_down": false,
    "mixed": false
  },
  
  "opposition_usd_base": {
    "pattern_type": "USD_BASE_OPPOSITION",
    "symbols_in_pattern": ["USDJPY","USDCAD","USDCHF"],
    "aligned_count": 3,
    "all_aligned_down": true
  },
  
  "freshness": "LIVE | DELAYED | STALE",
  "confidence_cap": "HIGH | MEDIUM | LOW | NONE",
  
  "explicit_limits": [
    "Stale symbols: USDCHF",
    "Alignment: PARTIAL (skew 85s)"
  ],
  
  "technical_risks": [
    "THIN_COVERAGE",
    "ALIGNMENT_DEGRADED"
  ],
  
  "policy": {
    "b9_annotation_allowed": true,
    "b9_reclassification_allowed": false,
    "db_write_allowed": false,
    "dashboard_auto_update_allowed": false,
    "telegram_auto_send_allowed": false
  }
}
```

---

## 🛡️ DOCTRINE IMMUABLE

### Interdits absolus
```
❌ Decider "GBP_STRENGTH" final (interprétatif)
❌ Decider "USD_WEAKNESS" final (interprétatif)
❌ Reclassifier scène B9
❌ Écriture powerflow.db / tick_archive.db
❌ Auto-update dashboard
❌ Auto-send Telegram
❌ Émettre signal BUY/SELL
❌ Probabilité de succès
```

### Garde-fous techniques
```
✅ SQLite ouvert mode=ro URI
✅ Pas d'import dashboard_* / cockpit_*
✅ Pas d'import telegram_*
✅ Tests bloquent INSERT/UPDATE/DELETE
✅ Policy fields immuables (toujours False)
```

---

## 📐 RÈGLES MÉTIER

### Normalisation directions

**GBP basket (7 paires):**
- GBPxxx (6 paires): up = GBP up
- EURGBP: **inversé** (EURGBP up = GBP weaker vs EUR → compté down)

**USD basket (7 paires):**
- USD quote (EURUSD, GBPUSD, AUDUSD, NZDUSD): up = USD weaker → **inversé**
- USD base (USDJPY, USDCHF, USDCAD): up = USD stronger → gardé

### Coverage thresholds

| State | Ratio | Conditions |
|-------|-------|------------|
| FULL | ≥80% | Tous baskets quasi-complets |
| PARTIAL | 50-79% | Majorité symboles présents |
| THIN | 30-49% | Moitié manquante |
| BLIND | <30% | Trop de manques |

### Confidence cap matrix

| Coverage | Alignment | Freshness | Cap |
|----------|-----------|-----------|-----|
| FULL | ALIGNED | LIVE | HIGH |
| FULL/PARTIAL | ALIGNED/PARTIAL | LIVE | MEDIUM |
| THIN | * | * | LOW |
| BLIND | * | * | NONE |
| * | * | STALE | NONE |

---

## 🔄 MODULES FUSIONNÉS / DÉPLACÉS

### Absorbés dans pf_multidevise.py

| Ancien module | Devenir |
|---------------|---------|
| `pf_coalitions.py` | Layer 3 (PatternDetection) |
| `pf_coalition_relations.py` | Layer 3 (PatternDetection) |
| `pf_b8_data_visibility.py` | Layer 1 + 4 (DataAccess + Quality) |
| `pf_b8_cross_surface_once.py` | Layer 5 (Assembly) |
| `pf_cross_symbol_validation.py` | Layer 4 (Quality) |

### Supprimés (violations doctrine)

| Module | Raison |
|--------|--------|
| `pf_battlefield_flux_cross_symbol.py` | Mélange B9+B8 |
| `pf_pair_driver_context.py` | Interprétatif "driver" |

### Déplacés (autres briques)

| Module | Destination |
|--------|-------------|
| `pf_spearman_gravity.py` | → B5 (corrélation) |
| `pf_relational_gravity_*` | → RG (leader/follower) |

---

## 🧪 TESTS COUVERTURE

**31 tests passent:**

### Doctrine (6 tests)
- test_no_db_write_in_source ✅
- test_db_opened_readonly ✅
- test_no_dashboard_imports ✅
- test_no_telegram_imports ✅
- test_no_forbidden_language ✅
- test_policy_immutable ✅

### Coverage (4 tests)
- test_coverage_full ✅
- test_coverage_partial ✅
- test_coverage_thin ✅
- test_coverage_blind ✅

### Baskets (4 tests)
- test_gbp_basket_all_up ✅
- test_eurgbp_inversion ✅
- test_usd_basket_normalization ✅
- test_basket_missing_symbols ✅

### Patterns (3 tests)
- test_coalition_all_up ✅
- test_coalition_mixed ✅
- test_opposition_all_down ✅

### Quality (7 tests)
- test_alignment_aligned ✅
- test_alignment_degraded ✅
- test_freshness_live ✅
- test_freshness_stale ✅
- test_confidence_high ✅
- test_confidence_none_when_blind ✅
- test_confidence_none_when_stale ✅

### Integration (7 tests)
- test_build_context_full_coverage ✅
- test_build_context_thin_coverage ✅
- test_build_context_baskets_present ✅
- test_build_context_patterns_present ✅
- test_build_context_serializable ✅
- test_build_context_explicit_limits_when_thin ✅
- test_no_data_returns_blind ✅

---

## 🚀 USAGE

### CLI standalone

```bash
python Core/pf_multidevise.py \
  --db Core/powerflow.db \
  --symbol GBPUSD \
  --time "2026-05-18 10:05:00" \
  --window 60 \
  --output outputs/multidevise_context.json
```

### Programmatique (Python)

```python
from pf_multidevise import MultideviseContextBuilder, context_to_dict

with MultideviseContextBuilder("Core/powerflow.db") as builder:
    context = builder.build_context(
        symbol_local="GBPUSD",
        timestamp_utc="2026-05-18T10:05:00",
        window_seconds=60
    )

# Access
print(f"Coverage: {context.coverage.value}")
print(f"GBP up count: {context.gbp_basket.direction_up_count}")
print(f"Coalition aligned: {context.coalition_usd_quote.all_aligned_up}")

# Serialize
output_dict = context_to_dict(context)
```

---

## 🔗 INTÉGRATION B9 / B6

### B9 annotation (autorisé)

```python
# B9 produit scene locale
b9_scene = {...}

# B8 multidevise annote
with MultideviseContextBuilder("Core/powerflow.db") as b:
    md_context = b.build_context(b9_scene['symbol'], b9_scene['timestamp'])

# Enrichi (annotation, pas reclassification)
b9_scene_enriched = {
    **b9_scene,
    'multidevise_context': context_to_dict(md_context)
}
```

### B6 memory payload

```python
# B6 mémorise contexte multidevise avec film
b6_film = {
    'film_signature': '...',
    'b9_scene_local': b9_scene,
    'multidevise_context': {
        'coverage': md_context.coverage.value,
        'gbp_up_count': md_context.gbp_basket.direction_up_count,
        'coalition_aligned': md_context.coalition_usd_quote.all_aligned_up,
        'limits': md_context.explicit_limits
    }
}
```

---

## 📋 ROADMAP V1 → V2

### V1 (cette version)
- ✅ 5 layers architecture
- ✅ Baskets GBP/USD
- ✅ Coalition/opposition patterns
- ✅ Coverage/alignment/freshness
- ✅ Read-only enforcement
- ✅ Tests garde-fous

### V2 (future, si validé terrain)
- ⚪ Métriques temporelles (drift, momentum)
- ⚪ Cross-pair correlations granulaires
- ⚪ Session overlay intégré
- ⚪ Cache multi-call (perf)
- ⚪ API HTTP optionnelle

---

**Spec V1 par Claude — 18 mai 2026**  
**Status:** ✅ Production-ready  
**Tests:** 31/31 PASS  
**Doctrine:** Respectée
