# POWERFLOW PACKET REQUALIFICATION RULES V7.6 FINAL

## 0. Doctrine

`raw_bias` = ce que les briques ont vu.

`qualified_bias` = ce que cela signifie dans le film.

PowerFlow ne décide pas le trade. PowerFlow ne produit pas d'ordre, ne crée pas de buy/sell, ne fabrique pas de stratégie et ne transforme pas une lecture terrain en instruction d'action.

Contrat V7.6 :

```text
La machine perçoit, mesure, nomme et alerte.
Le trader filtre, arbitre et agit.
```

Le `raw_bias` doit être conservé dans chaque packet pour auditabilité, mais il ne doit jamais être affiché seul comme vérité principale. L'affichage principal doit exposer le film, la zone, le rôle courant, la confirmation prix et la visibilité data.

---

## 1. Ordre strict des règles

La requalification V7.6 doit appliquer les règles dans cet ordre exact :

1. Vérifier `data_visibility`.
2. Vérifier prix / invalidation / stale.
3. Identifier `last_structural_event`.
4. Identifier `current_zone`.
5. Lire `raw_bias`.
6. Appliquer règles de contexte film.
7. Appliquer propagation B7.
8. Appliquer texture B7+.
9. Appliquer mémoire B6.
10. Produire `qualified_bias` + `packet_quality` + `watch_condition` + `invalidation_condition`.

Raison : le packet brut ne suffit pas. Il doit être requalifié par film + zone + prix + propagation + texture + mémoire + guards.

---

## 2. Règles data_visibility

### États officiels

| État | Sens | Effet V7.6 |
|---|---|---|
| `FULL_READING` | Microfilm, packets, prix, propagation, cross-validation disponibles | Lecture complète autorisée. |
| `READING_PARTIAL` | Lecture utilisable mais incomplète | Doit apparaître en haut ; peut limiter `packet_quality`. |
| `MICROFILM_MISSING` | M1 / microfilm absent | Empêche validation dure d'une release micro. |
| `M1_MISSING` | Données M1 absentes ou inutilisables | Force visibilité dégradée. |
| `PACKETS_STALE` | Packets trop vieux pour valider le live | Force visibilité dégradée ; empêche release validée seule. |
| `CROSS_VALIDATION_DEGRADED` | B5/B8 incomplet ou faible couverture | La confirmation relationnelle devient soft. |
| `B8_DEGRADED` | B8 faible, partiel ou non représentatif | Ne doit pas confirmer dur ; expose risque technique. |
| `B5_B8_HONEST_UNKNOWN` | B5/B8 ne sait pas honnêtement | Requalifier en `HONEST_UNKNOWN` si aucune preuve plus forte. |
| `TEMPORAL_GAPS` | Trous temporels dans la séquence | Empêche lecture continue du film. |
| `EVENT_TIME_OFFSET` | Décalage entre event_at et market_time | Exposer risque de lecture décalée. |
| `UNKNOWN` | Visibilité non fournie | Fallback prudent côté technique, jamais vérité complète. |

### Règle dure

Si la data est dégradée, elle doit apparaître en haut du packet et peut limiter `packet_quality`.

Règles d'application :

```text
M1 absent                -> data_visibility=M1_MISSING ou READING_PARTIAL
M1 absent + stale        -> data_visibility=M1_MISSING_PACKETS_STALE
packets stale            -> data_visibility=PACKETS_STALE ou READING_PARTIAL
B8 faible                -> technical_risks += B8_DEGRADED
B5/B8 faible sans prix   -> qualified_bias=HONEST_UNKNOWN possible
event_at offset          -> data_visibility=EVENT_TIME_OFFSET ou technical_risks += EVENT_TIME_OFFSET
```

La visibilité n'annule pas nécessairement le packet. Elle le qualifie. Une lecture partielle peut rester utile si elle dit clairement ce qu'elle ne voit pas.

---

## 3. Règles prix

### États officiels

| État | Sens |
|---|---|
| `PRICE_CONFIRMED` | Prix confirme le rôle du packet. |
| `PRICE_PENDING` | Le prix n'a pas encore tranché. |
| `PRICE_FAILED` | Le prix échoue à confirmer le packet. |
| `PRICE_INVALIDATED` | Le prix contredit explicitement la lecture. |
| `PRICE_ACCEPTED_ABOVE_ZONE` | Acceptation au-dessus de la zone active. |
| `PRICE_ACCEPTED_BELOW_ZONE` | Acceptation sous la zone active. |
| `PRICE_REJECTED_HIGH` | Rejet de zone haute / high rejeté. |
| `PRICE_REJECTED_LOW` | Rejet de zone basse / low rejeté. |
| `PRICE_ABSORBED_PULLBACK` | Pullback absorbé par prix / clôture. |
| `UNKNOWN` | Aucun état prix fiable. |

### Règles obligatoires

```text
PAIR_UP + lower low ensuite = COUNTER_BREATH_FAILED ou PRICE_INVALIDATED
PAIR_DOWN + close high ensuite = PULLBACK_ABSORBED ou FAILED_PRESSURE
HOT sans déplacement prix = PRESSURE_PENDING
HOT après extension = EXHAUSTION_OR_CONSUMED
B3+B4+P1 + rejet prix immédiat = FAILED_RELEASE ou PRESSURE_PENDING
```

Le prix tranche le packet. Une brique ne peut pas valider seule une release si le prix l'a rejetée, si le packet est stale, ou si la zone active contredit la lecture.

---

## 4. Règles raw_bias -> qualified_bias

| RULE_ID | RAW_BIAS | CONTEXT | REQUIRED_CONFIRMATION | QUALIFIED_BIAS | PACKET_QUALITY | PRICE_CONFIRMATION | WATCH | INVALIDATION |
|---|---|---|---|---|---|---|---|---|
| `R_PAIR_UP_AFTER_RELEASE_DOWN_COUNTER_BREATH` | `PAIR_UP` | Après `RELEASE_DOWN_VALIDATED`, `LOWER_LOCK`, `LOWER_PRICE_ACCEPTANCE` | Réintégration prix au-dessus zone ou relais MTF | `POST_RELEASE_COUNTER_BREATH` | `REACTION_NOT_RELEASE` | `PRICE_PENDING` | Acceptation au-dessus zone active | Lower low / rejet sous zone |
| `R_PAIR_UP_AFTER_LOWER_LOW_POST_LOW_REACTION` | `PAIR_UP` | Après lower low ou low retest | Rejet low + maintien au-dessus low | `POST_LOW_COUNTER_BREATH` | `REACTION_NOT_RELEASE` | `PRICE_PENDING` | Reprise au-dessus zone basse | Nouveau lower low |
| `R_PAIR_UP_LATE_SESSION_THIN_BOUNCE` | `PAIR_UP` | Session tardive, relay faible | Besoin acceptance + relay | `LATE_THIN_BOUNCE` | `LOW_QUALITY_REACTION` | `PRICE_PENDING` | Tenue zone + relais | Rejet rapide / stale |
| `R_PAIR_UP_ACCEPTED_ABOVE_ZONE_CONTINUATION` | `PAIR_UP` | Prix accepté au-dessus zone | Close/acceptance au-dessus zone + propagation non failed | `UP_CONTINUATION_ACCEPTED` | `CONTINUATION_ACCEPTED` | `PRICE_ACCEPTED_ABOVE_ZONE` | Maintien au-dessus zone | Réintégration sous zone |
| `R_PAIR_UP_AFTER_HIGH_EXHAUSTION_RISK` | `PAIR_UP` | Après high zone, extension déjà faite | Acceptation forte requise | `HIGH_ZONE_EXHAUSTION_RISK` | `EXHAUSTION_RISK` | `PRICE_PENDING` | Nouveau high accepté | Rejet high / unwind |
| `R_PAIR_DOWN_AFTER_RELEASE_UP_PULLBACK` | `PAIR_DOWN` | Après `RELEASE_UP_VALIDATED` | Rejet ou cassure structurelle pour plus que pullback | `POST_RELEASE_PULLBACK` | `PULLBACK_CONTEXT` | `PRICE_PENDING` | Absorption ou rejet du pullback | Close high / absorption |
| `R_PAIR_DOWN_AFTER_HIGH_REJECTION_UNWIND` | `PAIR_DOWN` | High rejeté / `HIGH_ZONE_REJECTION` | Rejet prix confirmé | `POST_HIGH_UNWIND` | `STRUCTURAL_REACTION` | `PRICE_REJECTED_HIGH` | Continuation unwind | Reprise au-dessus high rejeté |
| `R_PAIR_DOWN_AFTER_COUNTER_BREATH_REJECTED_SECOND_LEG` | `PAIR_DOWN` | Counter-breath rejeté | Lower acceptance / relay non failed | `SECOND_LEG_DOWN` | `STRUCTURAL_CONTINUATION` | `PRICE_CONFIRMED` | Lower acceptance | Réintégration au-dessus zone |
| `R_HOT_WITHOUT_PRICE_PRESSURE_PENDING` | `HOT` | Pas de déplacement prix | Déplacement réel ou acceptance | `PRESSURE_PENDING` | `PRESSURE_NOT_RELEASE` | `PRICE_PENDING` | Déplacement hors zone | Stale / rejet immédiat |
| `R_HOT_AFTER_EXTENSION_CONSUMED` | `HOT` | Après extension / high fait / release consommée | Nouvelle acceptance indépendante | `EXHAUSTION_OR_CONSUMED` | `CONSUMED_OR_LATE` | `PRICE_PENDING` | Acceptance fraîche | Rejet extension |
| `R_HOT_WITH_ACCEPTANCE_EVENT_CONFIRMED` | `HOT` | Prix accepté + zone cohérente | Acceptance + propagation non failed + data acceptable | `EVENT_CONFIRMED` | `CONFIRMED_EVENT` | `PRICE_CONFIRMED` | Surveiller résolution prix | Perte acceptance |
| `R_B5_B8_WEAK_HONEST_UNKNOWN` | `ANY` | B5/B8 faible | Prix ou autre preuve dure requise | `HONEST_UNKNOWN` | `CROSS_VALIDATION_DEGRADED` | `UNKNOWN` | Attendre preuve indépendante | Ne pas valider par B8 seul |
| `R_PACKETS_STALE_READING_PARTIAL` | `ANY` | Packets stale / M1 absent | Refresh data requis | `READING_PARTIAL` | `DATA_LIMITED` | `UNKNOWN` | Rafraîchissement packets / M1 | Packet ancien utilisé comme live |
| `R_B3_B2_EVENT_STACK_NOT_RELEASE` | `B3+B2` | B3+B2 actif seul | B4+P1+prix+B7 requis | `EVENT_STACK` | `EVENT_STACK_NOT_RELEASE` | `PRICE_PENDING` | Confirmation B4/P1/prix | Rejet prix ou bruit M1 |
| `R_B3_B4_P1_RELEASE_CANDIDATE` | `B3+B4+P1` | Détachement + compression + énergie | Prix + zone + B7 requis | `RELEASE_CANDIDATE` | `CANDIDATE_NOT_VALIDATED` | `PRICE_PENDING` | Acceptance prix | Rejet prix immédiat |
| `R_B3_B4_P1_WITH_PRICE_ACCEPTANCE_RELEASE_VALIDATED` | `B3+B4+P1` | Candidate + acceptance | Data acceptable + propagation pas failed | `RELEASE_VALIDATED` | `RELEASE_VALIDATED` | `PRICE_CONFIRMED` | Résolution structurelle | Perte acceptance |
| `R_B3_B4_P1_WITH_PRICE_REJECTION_FAILED_RELEASE` | `B3+B4+P1` | Candidate + rejet immédiat | Aucune validation sans prix | `FAILED_RELEASE` | `FAILED_RELEASE` | `PRICE_FAILED` | Rebuild / pression pending | Continuer à lire comme release |

---

## 5. Règles B3+B2

`B3+B2 = EVENT_STACK / BIRTH_ATTEMPT`.

Jamais `RELEASE_VALIDATED`.

Règles :

```text
B3+B2 actif seul -> EVENT_STACK
B3+B2 + bruit M1 élevé -> EVENT_STACK_NOISY
B3+B2 + B4 absent -> EVENT_STACK_NOT_RELEASE
B3+B2 + prix absent -> EVENT_STACK_NOT_RELEASE
B3+B2 + B4 + P1 -> RELEASE_CANDIDATE seulement
```

B2 empile des événements. B3 lit un détachement. Ensemble, ils signalent une activité. Ils ne prouvent pas que le film a changé.

---

## 6. Règles B3+B4+P1

`B3+B4+P1 = RELEASE_CANDIDATE`.

Devient `RELEASE_VALIDATED` seulement si :

- `price_confirmation` acceptable ;
- `current_zone` cohérente ;
- `propagation_state` pas seulement failed ;
- `data_visibility` acceptable.

Matrice :

```text
B3+B4+P1 + PRICE_ACCEPTED_ABOVE_ZONE + LTF_MTF_RELAY -> RELEASE_VALIDATED
B3+B4+P1 + PRICE_ACCEPTED_BELOW_ZONE + LTF_MTF_RELAY -> RELEASE_VALIDATED
B3+B4+P1 + PRICE_PENDING -> RELEASE_CANDIDATE
B3+B4+P1 + PRICE_FAILED -> FAILED_RELEASE
B3+B4+P1 + FAILED_PROPAGATION -> RELEASE_CANDIDATE_LIMITED
B3+B4+P1 + READING_PARTIAL -> RELEASE_CANDIDATE_DATA_LIMITED
```

---

## 7. Règles B7 propagation

| propagation_state | Effet |
|---|---|
| `LTF_ONLY` | Mouvement local. Peut qualifier une réaction, pas valider seul une release structurelle. |
| `LTF_MTF_RELAY` | Relais M1/M5/M15 : renforce candidate, permet validation si prix et zone confirment. |
| `MTF_HTF_RELAY` | Relais profond : renforce `packet_quality`. |
| `FAILED_PROPAGATION` | Limite fortement : pression locale, false reaction ou failed release. |
| `RELAY_DEGRADING` | Conserve packet mais dégrade qualité. |
| `COUNTERFLOW_AGAINST_STRUCTURE` | Information qualitative : mouvement contre structure, pas blocage automatique. |
| `UNKNOWN` | Ne valide rien seul. |

B7 ne décide pas le film. B7 dit si le mouvement reste local, se propage, se dégrade, ou se fait contre la structure.

---

## 8. Règles B7+ texture

| detachment_texture | Effet |
|---|---|
| `STRUCTURAL_DETACHMENT` | Renforce release candidate si prix confirme. |
| `NOISY_DETACHMENT` | Ajoute risque technique `NOISY_DETACHMENT`; limite qualité. |
| `COUNTER_BREATH_DETACHMENT` | Requalifie direction brute en respiration inverse. |
| `POST_RELEASE_DETACHMENT` | Requalifie en pullback, continuation ou absorption selon prix. |
| `LATE_SESSION_DETACHMENT` | Suspect / thin bounce sauf prix très clair. |
| `EXHAUSTION_DETACHMENT` | Risque consumed/exhaustion. |
| `REJECTION_DETACHMENT` | Favorise unwind / failed release. |
| `FALSE_REACTION_DETACHMENT` | Limite à watch ou reading partial. |
| `UNKNOWN` | Ne renforce rien seul. |

B7+ ne remplace pas le prix. Il donne la texture du détachement.

---

## 9. Règles B6 memory

B6 devient mémoire de films, pas mémoire d'événements isolés.

B6 peut :

- renforcer si le film actuel ressemble à un film calibré et que les preuves live sont cohérentes ;
- limiter si le film ressemble à un faux positif connu ;
- signaler `false_positive_risk` ;
- indiquer `expected_next_behavior`.

B6 ne décide jamais seul.

Sortie B6 attendue :

```json
{
  "memory_match": "LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL",
  "memory_confidence": 0.74,
  "expected_next_behavior": "LOW_RETEST_OR_POST_LOW_REACTION",
  "false_positive_risk": "READING_PARTIAL_CAN_OVERSTATE_COUNTER_BREATH"
}
```

Si B6 contredit prix ou zone, il reste informatif.

---

## 10. terrain_packet_v76_0

Champs obligatoires :

```text
schema_version
symbol
generated_at
market_time
film_state
last_structural_event
last_structural_direction
last_structural_time
current_zone
current_zone_low
current_zone_high
current_zone_status
current_move_role
raw_bias
qualified_bias
packet_quality
price_confirmation
propagation_state
detachment_texture
data_visibility
watch_condition
invalidation_condition
technical_risks
evidence_refs
```

Règle d'affichage :

```text
DATA_VISIBILITY
FILM / LAST_EVENT / ZONE
RAW_BIAS conservé mais secondaire
QUALIFIED_BIAS principal
PRICE_CONFIRMATION obligatoire
WATCH / INVALIDATION sans buy/sell/entry/target/stop
```

---

## 11. Audit log

Format `terrain_packet_audit.jsonl` : un JSON par ligne.

Champs recommandés :

```json
{
  "schema_version": "terrain_packet_audit_v76_0",
  "generated_at": "2026-05-14T12:00:00Z",
  "symbol": "GBPUSD",
  "raw_bias": "PAIR_UP",
  "qualified_bias": "POST_LOW_COUNTER_BREATH",
  "packet_quality": "REACTION_NOT_RELEASE",
  "price_confirmation": "PRICE_PENDING",
  "data_visibility": "M1_MISSING_PACKETS_STALE",
  "rules_fired": ["R_PAIR_UP_AFTER_LOWER_LOW_POST_LOW_REACTION", "R_PACKETS_STALE_READING_PARTIAL"],
  "technical_risks": ["M1_MISSING", "PACKETS_STALE"],
  "evidence_refs": ["film:2026-05-14", "packet:latest"]
}
```

Audit obligatoire pour comprendre pourquoi `qualified_bias` diffère de `raw_bias`.

---

## 12. QA obligatoire

| QA_ID | Scénario | Attendu |
|---|---|---|
| `QA-01` | B3+B2 actif seul | `EVENT_STACK`, pas `RELEASE_VALIDATED`. |
| `QA-02` | B3+B4+P1 + prix accepté | `RELEASE_VALIDATED`. |
| `QA-03` | Release UP puis `PAIR_DOWN` | `POST_RELEASE_PULLBACK`. |
| `QA-04` | Pullback absorbé | `PULLBACK_ABSORBED`. |
| `QA-05` | High rejeté puis DOWN | `POST_HIGH_UNWIND`. |
| `QA-06` | Release DOWN puis `PAIR_UP` | `COUNTER_BREATH_UP` ou `POST_RELEASE_COUNTER_BREATH`. |
| `QA-07` | Counter-breath échoue | `COUNTER_BREATH_REJECTED`. |
| `QA-08` | Après rejet counter-breath | `SECOND_LEG_DOWN`. |
| `QA-09` | HOT sans déplacement | `PRESSURE_PENDING`. |
| `QA-10` | HOT après extension | `EXHAUSTION_OR_CONSUMED`. |
| `QA-11` | B8 coverage faible | `HONEST_UNKNOWN` / `B8_DEGRADED`. |
| `QA-12` | M1 absent/stale | `READING_PARTIAL` en haut ou `M1_MISSING_PACKETS_STALE`. |
| `QA-13` | `event_at` offset | `EVENT_TIME_OFFSET`. |
| `QA-14` | LTF contre MTF | Information qualitative, pas blocage. |

---

## 13. Non-régression V7.6

Interdits :

```text
Ne pas inventer une nouvelle spine.
Ne pas refaire le dashboard.
Ne pas activer Telegram.
Ne pas produire de stratégie de trading.
Ne pas créer buy/sell/entry/exit/target/stop.
Ne pas valider une release depuis un seul événement.
Ne pas afficher PAIR_UP / PAIR_DOWN seul comme lecture principale.
Ne pas masquer data_visibility.
Ne pas ignorer price_confirmation.
Ne pas transformer Alert Gate en moteur sémantique.
```

Ce patch est minimal : il qualifie un packet. Il ne refond pas PowerFlow.
