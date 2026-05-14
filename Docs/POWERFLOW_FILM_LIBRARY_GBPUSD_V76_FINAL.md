# POWERFLOW FILM LIBRARY GBPUSD V7.6 FINAL

## 0. Doctrine

La film library sert à reconnaître des séquences et outcomes.
Elle ne décide pas le trade.
Elle aide B6 à comparer le film courant aux films déjà vus.

PowerFlow V7.6 doit mémoriser des films, pas seulement des événements isolés. Un packet brut n'est utile que s'il est requalifié par le film courant, la zone active, le prix, la propagation et la visibilité data.

## 1. Tableau global des journées

| DATE | FILM_NAME | DOMINANT_STRUCTURE | KEY_EVENT | PRICE_ARBITER | EXPECTED_REQUALIFICATION | DATA_LIMITS | QA_TARGET |
|---|---|---|---|---|---|---|---|
| 2026-05-06 | `RELEASE_UP_FROM_LOW_THEN_HIGH_ZONE_EXHAUSTION` | Low-zone build puis high-zone consumed | Release UP validée puis exhaustion | Acceptation UP initiale, puis rejet/consommation high-zone | `PAIR_UP` tardif -> `CONSUMED` / `EXHAUSTION_RISK`; `PAIR_DOWN` -> `POST_RELEASE_UNWIND` | Prix + zone + propagation requis | `QA-FILM-20260506` |
| 2026-05-07 | `LATE_HIGH_REJECTION_WITH_DEEP_UNWIND` | High tardif rejeté | `HIGH_ZONE_REJECTION` | Rejet du high puis acceptation plus basse | `PAIR_DOWN` -> `POST_HIGH_UNWIND` / `DEEP_POST_HIGH_UNWIND` | Distinguer pullback normal vs rejet de zone haute | `QA-FILM-20260507` |
| 2026-05-08 | `RELEASE_UP_VALIDATED_CLOSE_NEAR_HIGH` | Release UP acceptée jusqu'à close | Pullback absorbé | Prix accepte plus haut et clôture proche high | `PAIR_UP` -> `RELEASE_UP_VALIDATED` / `UP_CONTINUATION_ACCEPTED` | Ne pas valider sans prix + propagation | `QA-FILM-20260508` |
| 2026-05-11 | `RELEASE_UP_FROM_COMPRESSION_THEN_SECOND_LEG_UP_AND_EXHAUSTION` | Compression, false births, release, second leg, exhaustion | `B3+B2` false births puis release UP | False births invalidés, release validée par acceptation | `B3+B2` -> `EVENT_STACK`; second leg -> `SECOND_LEG_UP`; late UP -> `EXHAUSTION` | Session / timing obligatoires | `QA-FILM-20260511` |
| 2026-05-12 | `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK_AND_LATE_COUNTER_BREATH` | Release down + lower lock | `LOWER_LOCK` | Prix accepte lower zone; UP inverse reste réaction | `PAIR_UP` -> `COUNTER_BREATH_UP` par défaut après release down | last_structural_event indispensable | `QA-FILM-20260512` |
| 2026-05-13 | `POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN` | Counter-breath rejeté puis second leg down | `COUNTER_BREATH_REJECTED` | Rejet UP puis lower low | `PAIR_DOWN` -> `SECOND_LEG_DOWN`; `PAIR_UP` tardif -> `POST_LOW_COUNTER_BREATH` / `LATE_THIN_BOUNCE` | Prix doit trancher rejet vs réintégration | `QA-FILM-20260513` |
| 2026-05-14 | `LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL` | Lower-zone range + lecture partielle | `READING_PARTIAL` | Confirmation pending si M1 absent / packets stale | `PAIR_UP` -> `POST_LOW_REACTION` ou `COUNTER_BREATH`; packet -> `DEGRADED` | `M1_MISSING`, `PACKETS_STALE`, `MICROFILM_MISSING` visibles | `QA-FILM-20260514` |

## 2. Film card — 2026-05-06

Date : 2026-05-06
Film name : `RELEASE_UP_FROM_LOW_THEN_HIGH_ZONE_EXHAUSTION`
Contexte : Low-zone building, release UP validée, puis high-zone exhaustion.
Dernier événement structurel : `RELEASE_UP_VALIDATED_THEN_HIGH_ZONE_EXHAUSTION`
Zone active : Low zone au départ, high zone consommée ensuite.
Mouvement dominant : UP initial validé, puis unwind post-extension.
Rôle du mouvement : Release fraîche puis signal UP tardif consommé.
Packets détectés : `PAIR_UP`, `HOT`, puis `PAIR_DOWN` / unwind.
Confirmation prix : acceptation plus haute au moment de la release; après high-zone, absence d'acceptation supplémentaire ou rejet = consommation.
Invalidation prix : `PAIR_UP` tardif invalidé si lower close / rejet high-zone / perte acceptation.
Ce que PowerFlow doit comprendre : UP validé puis signaux UP tardifs reclassés `CONSUMED` / `EXHAUSTION_RISK`.
Ce que PowerFlow doit éviter : appeler un nouveau `PAIR_UP` frais après high déjà fait.
Règle candidate : après `RELEASE_UP_VALIDATED`, si high-zone active puis extension consommée, `PAIR_UP` devient `UP_CONSUMED` ou `HIGH_ZONE_EXHAUSTION`.
QA attendue : `QA-FILM-20260506`.
Memory signature : `LOW_ZONE_BUILDING -> RELEASE_UP_VALIDATED -> HIGH_ZONE_EXHAUSTION -> POST_RELEASE_UNWIND`.
Next expected behavior : surveiller rejet high-zone ou unwind post-release, pas fresh release automatique.
False positive risk : late `PAIR_UP`, HOT après extension, B3/B2 tardif surinterprété.

## 3. Film card — 2026-05-07

Date : 2026-05-07
Film name : `LATE_HIGH_REJECTION_WITH_DEEP_UNWIND`
Contexte : Rebuild post-release, extension UP tardive, high-zone rejection, unwind profond.
Dernier événement structurel : `HIGH_ZONE_REJECTION`.
Zone active : High zone rejetée.
Mouvement dominant : Deep unwind après rejet.
Rôle du mouvement : `POST_HIGH_UNWIND`, pas `PAIR_DOWN` générique.
Packets détectés : late `PAIR_UP`, `HOT`, `PAIR_DOWN`.
Confirmation prix : rejet du high, acceptation progressive plus basse.
Invalidation prix : `POST_HIGH_UNWIND` invalidé seulement si réintégration high-zone acceptée.
Ce que PowerFlow doit comprendre : après high tardif rejeté, DOWN = unwind structurel.
Ce que PowerFlow doit éviter : traiter `PAIR_DOWN` comme une naissance indépendante du contexte.
Règle candidate : `HIGH_ZONE_REJECTION + PAIR_DOWN + lower acceptance -> POST_HIGH_UNWIND`.
QA attendue : `QA-FILM-20260507`.
Memory signature : `POST_RELEASE_REBUILD -> LATE_UP_EXTENSION -> HIGH_ZONE_REJECTION -> DEEP_POST_HIGH_UNWIND`.
Next expected behavior : continuation unwind tant que le prix ne réintègre pas la high zone.
False positive risk : `HOT` sans déplacement prix, late UP pris pour continuation.

## 4. Film card — 2026-05-08

Date : 2026-05-08
Film name : `RELEASE_UP_VALIDATED_CLOSE_NEAR_HIGH`
Contexte : Low-zone rebuild, release UP validée, pullback absorbé, continuation acceptée.
Dernier événement structurel : `RELEASE_UP_VALIDATED`.
Zone active : Low-zone rebuild vers acceptation supérieure.
Mouvement dominant : Continuation UP acceptée.
Rôle du mouvement : release validée puis pullback absorbé.
Packets détectés : `PAIR_UP`, pullback `PAIR_DOWN`, continuation `PAIR_UP`.
Confirmation prix : prix accepte plus haut, pullback ne casse pas la structure, close near high.
Invalidation prix : pullback devient invalidant si close basse et perte d'acceptation.
Ce que PowerFlow doit comprendre : release validée = prix + zone + propagation + pullback absorbé.
Ce que PowerFlow doit éviter : considérer tout `PAIR_DOWN` post-release comme reversal.
Règle candidate : `RELEASE_UP_VALIDATED + pullback held + close near high -> UP_CONTINUATION_ACCEPTED`.
QA attendue : `QA-FILM-20260508`.
Memory signature : `LOW_ZONE_REBUILD -> RELEASE_UP_VALIDATED -> PULLBACK_ABSORBED -> CONTINUATION_UP -> CLOSE_NEAR_HIGH`.
Next expected behavior : continuation acceptée tant que le prix confirme au-dessus de la zone de pullback.
False positive risk : release validée sans prix, pullback absorbé non reconnu.

## 5. Film card — 2026-05-11

Date : 2026-05-11
Film name : `RELEASE_UP_FROM_COMPRESSION_THEN_SECOND_LEG_UP_AND_EXHAUSTION`
Contexte : Pré-London false births, compression, release UP, pullback, second leg, exhaustion.
Dernier événement structurel : `SECOND_LEG_UP_THEN_HIGH_ZONE_EXHAUSTION`.
Zone active : compression puis high-zone consommée.
Mouvement dominant : UP en deux jambes puis exhaustion.
Rôle du mouvement : false births avant validation, release, second leg, exhaustion.
Packets détectés : `B3+B2`, `B4`, `P1`, `PAIR_UP`, `PAIR_DOWN`, `HOT`.
Confirmation prix : false births non confirmés; release validée uniquement si prix accepte + propagation.
Invalidation prix : `B3+B2` sans prix = `EVENT_STACK`; late UP après second leg = consumed.
Ce que PowerFlow doit comprendre : `B3+B2` seul = `EVENT_STACK`, pas naissance validée.
Ce que PowerFlow doit éviter : valider une birth pré-London sans prix + B7.
Règle candidate : `B3+B2 -> EVENT_STACK`; `B3+B4+P1+price+B7 -> RELEASE_CANDIDATE/VALIDATED`.
QA attendue : `QA-FILM-20260511`.
Memory signature : `PRE_LONDON_FALSE_BIRTHS -> MIDDAY_RELEASE_UP -> POST_RELEASE_PULLBACK -> SECOND_LEG_UP -> HIGH_ZONE_EXHAUSTION -> LATE_UNWIND`.
Next expected behavior : second leg possible après pullback absorbé, puis exhaustion si high-zone consommée.
False positive risk : false birth, LTF_ONLY surinterprété, late second-leg UP survalidé.

## 6. Film card — 2026-05-12

Date : 2026-05-12
Film name : `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK_AND_LATE_COUNTER_BREATH`
Contexte : Asia high failure, London release down, lower price acceptance, counter-breath tardif.
Dernier événement structurel : `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK`.
Zone active : lower zone acceptée / locked.
Mouvement dominant : DOWN release puis counter-breath UP.
Rôle du mouvement : `PAIR_UP` après release down = counter-breath par défaut.
Packets détectés : `PAIR_DOWN`, `LOWER_LOCK`, `PAIR_UP`, `HOT` éventuel.
Confirmation prix : lower acceptance confirme release down; UP inverse doit réintégrer pour changer de rôle.
Invalidation prix : `COUNTER_BREATH_UP` invalidé si rejet et second low test.
Ce que PowerFlow doit comprendre : last structural event domine la lecture suivante.
Ce que PowerFlow doit éviter : transformer une réaction UP en fresh release UP.
Règle candidate : après `RELEASE_DOWN_VALIDATED`, tout `PAIR_UP` devient `COUNTER_BREATH_UP` tant que le prix ne réintègre pas.
QA attendue : `QA-FILM-20260512`.
Memory signature : `ASIA_HIGH_FAILURE -> LONDON_RELEASE_DOWN -> LOWER_PRICE_ACCEPTANCE -> POST_RELEASE_COUNTER_BREATH -> SECOND_LOW_TEST -> LATE_COUNTER_BOUNCE`.
Next expected behavior : second low test ou counter-breath tardif selon acceptation prix.
False positive risk : PAIR_UP brut, post-low reaction confondue avec nouvelle phase.

## 7. Film card — 2026-05-13

Date : 2026-05-13
Film name : `POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN`
Contexte : lower acceptance, counter-breath UP, rejet, second leg down, lower low.
Dernier événement structurel : `COUNTER_BREATH_REJECTED`.
Zone active : lower acceptance puis lower low.
Mouvement dominant : second leg down après rejet.
Rôle du mouvement : rejet du counter-breath devient carburant du second leg.
Packets détectés : `PAIR_UP`, `PAIR_DOWN`, `HOT`, low retest.
Confirmation prix : UP rejeté, lower low confirme second leg.
Invalidation prix : second leg invalidé si réintégration supérieure acceptée.
Ce que PowerFlow doit comprendre : `PAIR_DOWN` après counter-breath rejeté = `SECOND_LEG_DOWN`.
Ce que PowerFlow doit éviter : lire le second leg comme simple PAIR_DOWN générique.
Règle candidate : `COUNTER_BREATH_REJECTED + lower acceptance/lower low -> SECOND_LEG_DOWN`.
QA attendue : `QA-FILM-20260513`.
Memory signature : `POST_RELEASE_LOWER_ACCEPTANCE -> LONDON_COUNTER_BREATH_UP -> COUNTER_BREATH_REJECTED -> SECOND_LEG_DOWN -> LOWER_LOW -> POST_LOW_COUNTER_BREATH -> LATE_THIN_BOUNCE`.
Next expected behavior : lower low puis post-low reaction / late thin bounce possible.
False positive risk : late bounce surinterprété, rejection non reconnue.

## 8. Film card — 2026-05-14

Date : 2026-05-14
Film name : `LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL`
Contexte : lower-zone range, counter-breath UP, rejet, low retest, post-low reaction avec visibilité partielle.
Dernier événement structurel : `COUNTER_BREATH_REJECTED_IN_LOWER_ZONE_RANGE`.
Zone active : `LOWER_ZONE_RANGE_ACTIVE`.
Mouvement dominant : range lower-zone + réactions.
Rôle du mouvement : `POST_LOW_REACTION`, pas fresh release sans acceptation.
Packets détectés : `PAIR_UP`, `PAIR_DOWN`, stale packets, M1 missing.
Confirmation prix : pending si données partielles; validation seulement par cassure/reintégration propre.
Invalidation prix : packet invalidé si prix contredit la direction brute ou si stale trop élevé.
Ce que PowerFlow doit comprendre : `READING_PARTIAL` doit être visible en haut si M1 manque / packets stale.
Ce que PowerFlow doit éviter : masquer les limites data ou survalider une lecture aveugle.
Règle candidate : `M1_MISSING OR PACKETS_STALE -> READING_PARTIAL + DEGRADED_PACKET`.
QA attendue : `QA-FILM-20260514`.
Memory signature : `LOWER_ZONE_RANGE_ACTIVE -> COUNTER_BREATH_UP -> COUNTER_BREATH_REJECTED -> LOW_RETEST -> POST_LOW_REACTION`.
Next expected behavior : attendre arbitrage prix entre réintégration et cassure basse; ne pas durcir sans data.
False positive risk : stale packet, B8 faible, LTF_ONLY surinterprété.

## 9. Patterns récurrents

| Pattern | Signature | Conditions | Piège | Requalification attendue | Champs terrain_packet concernés |
|---|---|---|---|---|---|
| release candidate validée | `B3+B4+P1+price+B7` | zone active cohérente, prix accepte, propagation non dégradée | valider avec B3+B2 seul | `RELEASE_VALIDATED` | `film_state`, `price_confirmation`, `propagation_state`, `packet_quality` |
| false birth | `B3+B2` sans prix / sans propagation | souvent pré-session ou compression instable | naissance fictive | `EVENT_STACK` / `FALSE_BIRTH` | `packet_quality`, `data_visibility`, `watch_condition` |
| high rejection | high-zone actif puis prix rejette | extension tardive ou high déjà fait | lire DOWN comme signal neuf | `HIGH_ZONE_REJECTION` puis `POST_HIGH_UNWIND` | `current_zone`, `last_structural_event`, `qualified_bias` |
| lower lock | release down + lower acceptance | prix accepte lower zone | lire UP comme fresh release | `LOWER_LOCK` | `current_zone`, `price_confirmation`, `last_structural_event` |
| counter-breath | réaction inverse après release | direction inverse sans réintégration acceptée | confondre réaction et nouvelle phase | `COUNTER_BREATH_UP/DOWN` | `current_move_role`, `qualified_bias`, `invalidation_condition` |
| counter-breath rejected | counter-breath échoue | rejet prix + retour dans structure dominante | ne pas détecter carburant second leg | `COUNTER_BREATH_REJECTED` | `last_structural_event`, `price_confirmation` |
| second leg | reprise après pullback/counter-breath rejeté | prix confirme continuation / lower low / higher continuation | `PAIR_DOWN/UP` brut | `SECOND_LEG_UP/DOWN` | `current_move_role`, `qualified_bias`, `watch_condition` |
| pullback absorbed | pullback post-release qui ne casse pas | prix tient zone et reprend | lire comme reversal | `PULLBACK_ABSORBED` | `price_confirmation`, `packet_quality`, `current_zone` |
| late thin bounce | réaction tardive faible | session tardive, data faible, zone déjà travaillée | survalider en release | `LATE_THIN_BOUNCE` | `session_context`, `data_visibility`, `packet_quality` |
| exhaustion / consumed | signal après extension/high done | high-zone active, absence d'acceptation nouvelle | fresh release tardive | `EXHAUSTION` / `CONSUMED` | `is_event_consumed`, `current_zone`, `qualified_bias` |
| reading partial | M1 absent / packets stale / coverage faible | visibilité data dégradée | cacher l'aveuglement | `READING_PARTIAL` | `data_visibility`, `packet_quality`, `watch_condition` |

## 10. Pièges récurrents

- `B3+B2` trop nerveux : doit produire `EVENT_STACK`, pas naissance validée.
- `PAIR_UP` après release down : counter-breath par défaut tant que le prix ne réintègre pas.
- `HOT` sans déplacement prix : `PRESSURE_PENDING`, pas événement confirmé.
- `LTF_ONLY` surinterprété : propagation absente = packet local / watch.
- Stale packet : reclasser `READING_PARTIAL` ou `DEGRADED`.
- B8 faible : `HONEST_UNKNOWN`, pas confirmation dure.
- High zone déjà consommée : `PAIR_UP` tardif = `CONSUMED` / `EXHAUSTION_RISK`.
- Late bounce : informer, ne pas transformer en release sans prix + propagation.

## 11. Usage par B6

B6 doit mémoriser les films sous forme comparable :

| Champ B6 | Usage |
|---|---|
| `FILM_PATTERN` | Nom stable du film ou pattern dominant. |
| `SEQUENCE` | Chaîne ordonnée des états terrain. |
| `TRIGGER` | Événement ou combinaison initiale qui déclenche l'attention. |
| `CONTEXT` | Session, zone, dernier événement structurel, phase du film. |
| `PRICE_ARBITER` | Ce que le prix doit confirmer, invalider ou laisser pending. |
| `OUTCOME` | Outcome observé du film calibré. |
| `INVALIDATION` | Condition qui aurait cassé la lecture. |
| `NEXT_EXPECTED_BEHAVIOR` | Comportement suivant attendu comme hypothèse de film, pas ordre. |
| `FALSE_POSITIVE` | Piège récurrent observé. |

B6 ne doit jamais produire de recommandation de trading. Il doit seulement comparer : film courant vs films calibrés.

## 12. Acceptance Criteria

- Chaque journée a une memory card complète.
- Chaque journée mappe vers au moins une règle QA.
- Aucune journée ne produit une recommandation de trade.
- `data_visibility` est présente.
- `price_confirmation` est présente.
- Les films sont compatibles `terrain_packet_v76_0`.
- `PAIR_UP`, `PAIR_DOWN`, `HOT`, `B3+B2`, `B3+B4+P1` sont toujours requalifiés par film + zone + prix + propagation + data.
- Les cas `READING_PARTIAL`, `MICROFILM_MISSING`, `PACKETS_STALE`, `HONEST_UNKNOWN` sont visibles quand requis.
