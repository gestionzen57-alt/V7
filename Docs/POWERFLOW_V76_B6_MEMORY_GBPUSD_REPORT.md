# POWERFLOW V7.6 — B6 FILM MEMORY GBPUSD REPORT

## 0. Mission

Objectif: améliorer le matching B6 pour reconnaître les films GBPUSD calibrés et éviter le retour faible de type:

```text
Mémoire B6 : Inconnu
memory_confidence faible
```

Scope actif:

```text
GBPUSD only
pas de EURUSD
pas de USDJPY
pas de machine learning lourd
matching explicable
si doute -> confidence faible + raison claire
```

## 1. Limite d'exécution

Le repo local Windows n'est pas monté dans cet environnement:

```text
C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
```

Je n'ai donc pas pu inspecter directement les fichiers réels existants:

```text
data\film_memory\gbpusd_v76_film_memory_cards.json
patch\pf_film_memory_reader_once.py
output\dashboard_surface\GBPUSD\terrain_packet.json
```

Livraison effectuée sous forme de patch / fichiers prêts à copier. Le patch est minimal et autonome.

## 2. Principe du patch

Le reader B6 compare le `terrain_packet` courant à des cartes mémoire GBPUSD V7.6.

Champs scorés explicitement:

```text
film_state
last_structural_event
qualified_bias
price_confirmation
propagation_state
detachment_texture
data_visibility
```

Sortie garantie:

```json
{
  "memory_match": "...",
  "memory_confidence": 0.0,
  "memory_reason_fr": "...",
  "similar_historical_days": []
}
```

Le résultat est aussi injecté dans `terrain_packet.json` par défaut sous:

```text
memory_match
memory_confidence
memory_reason_fr
similar_historical_days
b6_film_memory
```

Option disponible:

```powershell
--no-write-back
```

pour produire uniquement `film_memory_match.json`.

## 3. Scoring explicable

Poids utilisés:

| Champ | Poids |
|---|---:|
| film_state | 0.24 |
| last_structural_event | 0.20 |
| qualified_bias | 0.16 |
| price_confirmation | 0.13 |
| propagation_state | 0.11 |
| detachment_texture | 0.10 |
| data_visibility | 0.06 |

Méthode:

```text
1.00 = match exact enum
0.70 = alias terrain contrôlé
0.55 = correspondance partielle explicable
0.00 = inconnu ou non aligné
```

Buckets:

```text
HIGH     >= 0.78
MEDIUM   >= 0.58
LOW      >= 0.35
VERY_LOW <  0.35
```

## 4. Cartes mémoire GBPUSD incluses

Les 7 films calibrés sont intégrés dans:

```text
data/film_memory/gbpusd_v76_film_memory_cards.json
```

| Date | Film |
|---|---|
| 2026-05-06 | RELEASE_UP_FROM_LOW_THEN_HIGH_ZONE_EXHAUSTION |
| 2026-05-07 | LATE_HIGH_REJECTION_WITH_DEEP_UNWIND |
| 2026-05-08 | RELEASE_UP_VALIDATED_CLOSE_NEAR_HIGH |
| 2026-05-11 | RELEASE_UP_FROM_COMPRESSION_THEN_SECOND_LEG_UP_AND_EXHAUSTION |
| 2026-05-12 | LONDON_RELEASE_DOWN_WITH_LOWER_LOCK_AND_LATE_COUNTER_BREATH |
| 2026-05-13 | POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN |
| 2026-05-14 | LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL |

## 5. Résumé PASS/FAIL des 7 films

Test synthétique: chaque carte est transformée en terrain_packet canonique puis passée au reader.

| Date | Attendu | Match obtenu | Confidence | Statut |
|---|---|---|---:|---|
| 2026-05-06 | RELEASE_UP_FROM_LOW_THEN_HIGH_ZONE_EXHAUSTION | RELEASE_UP_FROM_LOW_THEN_HIGH_ZONE_EXHAUSTION | 1.000 | PASS |
| 2026-05-07 | LATE_HIGH_REJECTION_WITH_DEEP_UNWIND | LATE_HIGH_REJECTION_WITH_DEEP_UNWIND | 1.000 | PASS |
| 2026-05-08 | RELEASE_UP_VALIDATED_CLOSE_NEAR_HIGH | RELEASE_UP_VALIDATED_CLOSE_NEAR_HIGH | 1.000 | PASS |
| 2026-05-11 | RELEASE_UP_FROM_COMPRESSION_THEN_SECOND_LEG_UP_AND_EXHAUSTION | RELEASE_UP_FROM_COMPRESSION_THEN_SECOND_LEG_UP_AND_EXHAUSTION | 1.000 | PASS |
| 2026-05-12 | LONDON_RELEASE_DOWN_WITH_LOWER_LOCK_AND_LATE_COUNTER_BREATH | LONDON_RELEASE_DOWN_WITH_LOWER_LOCK_AND_LATE_COUNTER_BREATH | 1.000 | PASS |
| 2026-05-13 | POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN | POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN | 1.000 | PASS |
| 2026-05-14 | LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL | LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL | 1.000 | PASS |

## 6. Test réel terrain_packet

Commande prévue:

```powershell
python .\patch\pf_film_memory_reader_once.py `
  --symbol GBPUSD `
  --packet .\output\dashboard_surface\GBPUSD\terrain_packet.json `
  --cards .\data\film_memory\gbpusd_v76_film_memory_cards.json `
  --out .\output\dashboard_surface\GBPUSD\film_memory_match.json
```

Attendu:

```text
- memory_match != UNKNOWN si le packet ressemble à un des 7 films connus
- memory_confidence HIGH/MEDIUM si les champs terrain sont alignés
- memory_confidence LOW/VERY_LOW si le packet est incomplet
- memory_reason_fr explique les champs alignés et les limites
```

## 7. Tests pytest

Fichier livré:

```text
tests/test_film_memory_matching_v76.py
```

Commande:

```powershell
python -m pytest .\tests\test_film_memory_matching_v76.py -q
```

Résultat local généré dans cet environnement:

```text
4 passed
```

## 8. Risques techniques

| Risque | Qualification | Mitigation |
|---|---|---|
| fichier réel `pf_film_memory_reader_once.py` déjà différent | conflit de patch | copier le fichier livré puis vérifier `git diff` |
| enums terrain divergents localement | confidence basse | aliases contrôlés + `memory_reason_fr` |
| `terrain_packet.json` incomplet | match LOW / VERY_LOW | champs manquants explicités |
| cartes locales déjà enrichies | doublon possible | fusion manuelle recommandée par architecte |
| écriture terrain_packet non désirée | surface output enrichie | utiliser `--no-write-back` |

## 9. Ce que le patch ne fait pas

```text
- ne modifie pas la logique terrain
- ne modifie pas Telegram
- ne touche pas aux tokens
- n'ajoute pas EURUSD/USDJPY
- n'ajoute pas de ML lourd
- ne produit aucun signal de trading
```

## 10. Verdict

Patch prêt pour intégration architecte.

La mémoire B6 devient:

```text
film-aware
GBPUSD only
explicable
faible si doute
utile pour dashboard / Telegram FR sans activer de nouvelle logique Telegram
```

