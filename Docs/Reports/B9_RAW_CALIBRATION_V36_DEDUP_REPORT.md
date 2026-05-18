# B9 Raw Calibration V3.6 — Lecture raw dedupliquee read-only

**Projet :** PowerFlow / T009 / B9  
**Version :** V3.6  
**Objet :** Lire les ticks raw MT5 en vue dedupliquee sans supprimer la donnee brute.  
**Statut :** Patch technique read-only.

---

## 1. Phrase de cap

```text
La DB garde la verite brute. B9 calibre sur une lecture dedupliquee.
```

---

## 2. Probleme terrain

`tick_archive.db` contient les ticks raw MT5 GBPUSD du 2026-05-11 au 2026-05-15.

Etat des doublons exacts observe :

| Date | Etat |
|---|---:|
| 2026-05-11 | 4 doublons seulement |
| 2026-05-12 | propre |
| 2026-05-13 | 54 722 doublons exacts |
| 2026-05-14 | 65 589 doublons exacts |
| 2026-05-15 | propre |

Les doublons ne doivent pas etre supprimes. Ils appartiennent a la verite brute de capture.
Mais la calibration B9 ne doit pas surponderer une meme empreinte raw dupliquee.

---

## 3. Regle V3.6

La lecture raw utilise des ticks dedupliques :

```sql
SELECT DISTINCT ts_utc, bid, ask, mid, spread
```

Cette lecture est appliquee aux metriques raw :

- `raw_delta_pips` ;
- `raw_range_pips` ;
- densite / dwell proxy ;
- gaps recalcules apres deduplication quand possible.

---

## 4. Champs ajoutes

```json
{
  "raw_dedup_mode": "DISTINCT_TS_BID_ASK_MID_SPREAD",
  "raw_tick_count_raw": 0,
  "raw_tick_count_dedup": 0,
  "raw_duplicate_count": 0,
  "raw_duplicate_ratio": 0.0
}
```

Champs de contexte conserves :

```json
{
  "source_mode": "HISTORICAL_RAW",
  "data_visibility": "MT5_RAW_ALIGNED",
  "broker_relative": true,
  "broker_note_fr": "Lecture raw MT5 broker-relative : texture locale vérifiée, pas footprint global centralisé."
}
```

---

## 5. Lecture B9 attendue

Le raw MT5 sert a verifier la texture locale :

```text
Le proxy M1 raconte la scene.
Le raw MT5 verifie la texture.
```

Avec V3.6, le raw MT5 est lu sans amplification artificielle par doublons exacts.

---

## 6. Limites affichees

La lecture reste :

```text
HISTORICAL_RAW
MT5_RAW_ALIGNED
BROKER_RELATIVE
NO_FOOTPRINT_EXACT_CLAIM
```

B9 ne doit pas affirmer une empreinte globale centralisee a partir d'un broker Forex.

---

## 7. Contraintes

- read-only ;
- aucune ecriture `powerflow.db` ;
- aucune ecriture `tick_archive.db` ;
- aucun dashboard ;
- aucun Telegram ;
- aucun langage decisionnel ;
- aucune fusion B8 ;
- ne pas affirmer une lecture footprint complete au-dela de la preuve raw broker-relative.

---

## 8. Tests V3.6

Tests ajoutes :

```text
test_db_without_duplicates_keeps_same_metrics
test_db_with_exact_duplicates_reduces_raw_tick_count_dedup
test_duplicate_ratio_is_exposed
test_raw_delta_and_range_are_computed_on_deduplicated_ticks
test_read_raw_ticks_sql_distinct
test_calibrate_raw_window_reports_dedup_sql_match
test_no_db_write_statements_in_raw_calibration_module
test_no_decision_language_in_raw_calibration_report
```

---

## 9. Verdict

V3.6 ne modifie pas la memoire raw.

Elle cree une lecture de calibration propre :

```text
brut conserve
lecture dedupliquee
metriques exposees
limites visibles
```
