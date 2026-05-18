# B6 Similarity Query Result V0

## Doctrine

```text
B6 ne prédit pas.
B6 compare des films.
Une similarité est un contexte de reconnaissance, jamais une probabilité de succès.
```

## Query scene

- query_id: `B6Q_PRECOMPUTED_B6FC_20260505_1413_BDE6E508`
- film_id: `B6FC_20260505_1413_BDE6E508`
- date: `2026-05-05`
- session: `LONDON_NY_OVERLAP`
- memory_family: `DIRECTIONAL_PROGRESS_MEMORY`
- source_family: `FORCE_SNAPSHOT_DERIVED`
- raw_agreement: `CONFIRMED_BY_RAW`
- source_quality_state: `SOURCE_QUALITY_USABLE`

## Similar films

| rank | film_id | date | session | family | score | raw agreement | reason |
|---:|---|---|---|---|---:|---|---|
| 1 | `B6FC_20260514_1903_E8F0918A` | 2026-05-14 | NY_AFTERNOON | DIRECTIONAL_PROGRESS_MEMORY | 0.778821 | CONFIRMED_BY_RAW | Film proche par comparaison 4D intra-famille: force principale=judgment_clarity 1.00; écart principal=base_motion 0.46. Lecture de similarité uniquement, sans prédiction. |
| 2 | `B6FC_20260513_0200_5821F72C` | 2026-05-13 | ASIAN_SESSION | DIRECTIONAL_PROGRESS_MEMORY | 0.764655 | CONFIRMED_BY_RAW | Film proche par comparaison 4D intra-famille: force principale=judgment_clarity 0.97; écart principal=base_motion 0.46. Lecture de similarité uniquement, sans prédiction. |
| 3 | `B6FC_20260513_0700_C66F0CA0` | 2026-05-13 | ASIA_LONDON_HANDOVER | DIRECTIONAL_PROGRESS_MEMORY | 0.755217 | CONFIRMED_BY_RAW | Film proche par comparaison 4D intra-famille: force principale=judgment_clarity 0.97; écart principal=base_motion 0.46. Lecture de similarité uniquement, sans prédiction. |
| 4 | `B6FC_20260513_1700_10F2213C` | 2026-05-13 | NY_AFTERNOON | DIRECTIONAL_PROGRESS_MEMORY | 0.741605 | CONFIRMED_BY_RAW | Film proche par comparaison 4D intra-famille: force principale=judgment_clarity 0.97; écart principal=base_motion 0.41. Lecture de similarité uniquement, sans prédiction. |
| 5 | `B6FC_20260512_1037_3A1AF089` | 2026-05-12 | LONDON_IGNITION | DIRECTIONAL_PROGRESS_MEMORY | 0.740596 | CONFIRMED_BY_RAW | Film proche par comparaison 4D intra-famille: force principale=judgment_clarity 1.00; écart principal=base_motion 0.46. Lecture de similarité uniquement, sans prédiction. |

## Integrity checks

```json
{
  "read_only": true,
  "db_write": false,
  "dashboard": false,
  "telegram": false,
  "buy_sell_language": false,
  "probability_of_success": false,
  "low_trust_in_results": false,
  "raw_unavailable_in_results": false,
  "cross_family_match_count": 0
}
```

## Technical limits

- Result loaded from T0114 precomputed film_similarity_index.
- Similarity is recognition context only, not a prediction.
