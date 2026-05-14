# POWERFLOW BRICK AUDIT QA CASES V7.6

## 0. Principe

Ces tests sont textuels et contractuels. Ils valident que les briques V7.6 restent à leur rôle terrain et ne surinterprètent pas les fragments.

Chaque test doit être utilisé comme cas QA avant patch moteur.

## QA-BRICK-01 — B3+B2 ne valide jamais une release

**Given** B2=`EVENT_STACK` et B3=`DETACHMENT_ATTEMPT`.
**When** prix, zone, B7 ou data acceptable sont absents.
**Then** le packet ne peut pas contenir `RELEASE_VALIDATED`.
**Expected** `BIRTH_ATTEMPT` ou `PRESSURE_PENDING`.

## QA-BRICK-02 — B3 directionnel sans prix reste pending

**Given** B3 produit `PAIR_UP` ou `PAIR_DOWN`.
**When** `price_confirmation != ACCEPTED`.
**Then** `qualified_bias` doit rester `DETACHMENT_ATTEMPT` ou rôle film non validé.
**Expected** `price_confirmation=PENDING`.

## QA-BRICK-03 — HOT sans déplacement prix devient pressure pending

**Given** niveau HOT.
**When** prix ne confirme pas le déplacement.
**Then** packet_quality=`PRESSURE_PENDING`.
**Expected** pas de `EVENT_CONFIRMED`.

## QA-BRICK-04 — B3+B4+P1 rejeté par prix

**Given** `release_candidate_state=RELEASE_CANDIDATE`.
**When** prix rejette la direction candidate.
**Then** requalifier en `RELEASE_FAILED`, `COUNTER_BREATH_REJECTED`, ou `EXHAUSTION` selon film.
**Expected** audit line dans `terrain_packet_audit.jsonl`.

## QA-BRICK-05 — B8 coverage faible

**Given** cross-symbol coverage insuffisant ou stale.
**When** B8 est sollicité.
**Then** sortie=`B8_DEGRADED` ou `CROSS_VALIDATION_DEGRADED`.
**Expected** pas de driver fort.

## QA-BRICK-06 — LTF_ONLY n'est pas structure

**Given** M1 fort.
**When** M5/M15 ne relaient pas.
**Then** `propagation_state=LTF_ONLY`.
**Expected** pas de `RELEASE_VALIDATED`.

## QA-BRICK-07 — Packet stale affiché en haut

**Given** packet timestamp ancien.
**When** packet est lu par dashboard/cockpit.
**Then** `data_visibility` contient `PACKETS_STALE`.
**Expected** `READING_PARTIAL` visible en haut.

## QA-BRICK-08 — event_at / detected_at offset

**Given** `event_at` > `detected_at` ou offset excessif.
**When** packet est généré.
**Then** Guards ajoutent `EVENT_TIME_OFFSET`.
**Expected** downgrade packet_quality.

## QA-BRICK-09 — PAIR_UP après release down

**Given** `last_structural_event=RELEASE_DOWN` ou `LOWER_LOCK`.
**When** raw_bias=`PAIR_UP`.
**Then** `qualified_bias=COUNTER_BREATH_UP` sauf acceptation prix claire de réintégration.
**Expected** watch_condition d'acceptation au-dessus zone.

## QA-BRICK-10 — PAIR_DOWN après release up

**Given** `last_structural_event=RELEASE_UP`.
**When** raw_bias=`PAIR_DOWN`.
**Then** `qualified_bias=POST_RELEASE_PULLBACK` sauf rejet/cassure confirmé.
**Expected** invalidation_condition explicite.

## QA-BRICK-11 — Late session + LTF_ONLY

**Given** session tardive ou faible liquidité.
**When** B3 fort mais B7=`LTF_ONLY`.
**Then** B7+=`LATE_SESSION_DETACHMENT` ou `NOISY_DETACHMENT`.
**Expected** `LATE_THIN_BOUNCE`, pas fresh release.

## QA-BRICK-12 — Consumed state après high exhaustion

**Given** high-zone rejection/exhaustion déjà observé.
**When** nouveau signal UP apparaît.
**Then** requalifier en `EXHAUSTION_DETACHMENT` ou `RELEASE_CONSUMED`.
**Expected** pas de `FRESH_RELEASE_UP`.

## QA-BRICK-13 — B5 relation ambiguë

**Given** Spearman/correlation/coverage ambigu.
**When** B5 produit leader/follower.
**Then** output=`RELATIONAL_MIXED` ou `B5_B8_HONEST_UNKNOWN`.
**Expected** pas de certitude relationnelle dure.

## QA-BRICK-14 — Evidence refs non orphelines

**Given** une evidence_ref.
**When** `field_supported` est absent.
**Then** evidence rejetée.
**Expected** chaque evidence contient source, timestamp, field_supported, confidence, weakness.

## QA-BRICK-15 — Dashboard read-only métier

**Given** dashboard_* lit `terrain_packet`.
**When** rendu cockpit.
**Then** dashboard ne modifie pas `qualified_bias`, `price_confirmation`, `packet_quality`.
**Expected** aucune logique métier dans dashboard_*.

## QA-BRICK-16 — Alert Gate ne renomme pas

**Given** packet=`COUNTER_BREATH_UP`.
**When** Alert Gate déduplique.
**Then** le rôle reste `COUNTER_BREATH_UP`.
**Expected** Gate ajoute seulement `dedupe_state` ou `throttle_state`.

## QA-BRICK-17 — B6 memory exige un film

**Given** memory match.
**When** match ne contient pas sequence + context + price_arbiter.
**Then** `memory_match=WEAK_FILM_MATCH` ou `NO_FILM_MATCH`.
**Expected** pas d'analogie forte.

## QA-BRICK-18 — Guards prioritaires

**Given** M1 missing, packets stale ou temporal gaps.
**When** packet final est produit.
**Then** `data_visibility` est le premier bloc visible.
**Expected** `READING_PARTIAL` si dégradation critique.

## QA-BRICK-19 — Freshness P1 obligatoire

**Given** P1=`ELASTIC_LOADED`.
**When** mouvement précédent est déjà consommé ou tardif.
**Then** P1 doit sortir `freshness_state=LATE_LOAD` ou `CONSUMED_LOAD`.
**Expected** pas de fresh release automatique.

## QA-BRICK-20 — Telegram OFF jusqu'à QA

**Given** branche V7.6 calibration terrain.
**When** packet est généré.
**Then** Telegram reste désactivé.
**Expected** `TELEGRAM_TERRAIN_PACKET_ENABLED=false` jusqu'à QA 7 journées validée.
