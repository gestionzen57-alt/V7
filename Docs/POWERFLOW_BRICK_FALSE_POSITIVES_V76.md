# POWERFLOW BRICK FALSE POSITIVES V7.6

## 0. Principe

Un faux positif PowerFlow V7.6 n'est pas seulement un signal qui ne bouge pas. C'est surtout un événement mal nommé dans le film.

```text
Le problème n'est pas toujours que PowerFlow voit faux.
Le problème est souvent que PowerFlow voit juste mais nomme faux.
```

## 1. Faux positifs critiques

| ID | Faux positif | Symptôme | Cause | Requalification attendue | Test QA |
|---|---|---|---|---|---|
| FP-01 | B3+B2 false birth | B3+B2 déclenche naissance | Event stack assimilé à birth | `EVENT_STACK` ou `BIRTH_ATTEMPT` | QA-BRICK-01 |
| FP-02 | B3 directionnel sans prix | `PAIR_UP/DOWN` fort sans acceptation prix | Détachement lu comme direction structurelle | `DETACHMENT_ATTEMPT`, `PRICE_PENDING` | QA-BRICK-02 |
| FP-03 | HOT sans déplacement prix | HOT visible mais prix ne confirme pas | Score événementiel sans arbitre prix | `PRESSURE_PENDING` | QA-BRICK-03 |
| FP-04 | B3+B4+P1 rejeté par prix | Candidate release puis rejet | Pas de price arbiter | `RELEASE_FAILED` ou `COUNTER_BREATH_REJECTED` | QA-BRICK-04 |
| FP-05 | B8 coverage faible | Cross validation affichée comme confirmée | Crosses manquants/stale | `B8_DEGRADED`, `HONEST_UNKNOWN` | QA-BRICK-05 |
| FP-06 | LTF_ONLY pris pour structure | M1 bouge mais M5/M15 absents | Propagation non vérifiée | `LTF_ONLY`, `WATCH`, `RELEASE_CANDIDATE` max | QA-BRICK-06 |
| FP-07 | Stale packet pris pour live | Packet ancien affiché comme actuel | freshness non visible | `PACKETS_STALE`, `READING_PARTIAL` | QA-BRICK-07 |
| FP-08 | event_at devant detected_at | Chronologie incohérente | offset temporel | `EVENT_TIME_OFFSET`, downgrade packet | QA-BRICK-08 |
| FP-09 | Counter-breath lu comme release inverse | PAIR_UP après release down | Oubli last_structural_event | `COUNTER_BREATH_UP` | QA-BRICK-09 |
| FP-10 | Pullback lu comme reversal | PAIR_DOWN après release up | Oubli contexte post-release | `POST_RELEASE_PULLBACK` | QA-BRICK-10 |
| FP-11 | Late bounce lu comme naissance | Session tardive + faible propagation | Session context absent | `LATE_THIN_BOUNCE` | QA-BRICK-11 |
| FP-12 | Exhaustion lu comme continuation | Extension après high déjà consommé | Absence consumed state | `EXHAUSTION_DETACHMENT`, `RELEASE_CONSUMED` | QA-BRICK-12 |
| FP-13 | B5 relation forcée | Leader/follower affiché malgré rho ambigu | Coverage ou corr faible | `RELATIONAL_MIXED` ou `HONEST_UNKNOWN` | QA-BRICK-13 |
| FP-14 | Evidence spam | Beaucoup de refs mais aucun champ supporté | Evidence Bus non contraint | Supprimer refs orphelines | QA-BRICK-14 |
| FP-15 | Dashboard décide | dashboard_* modifie qualified_bias | Logique métier au mauvais endroit | Déplacer vers pf_packet_requalification | QA-BRICK-15 |
| FP-16 | Alert Gate renomme le signal | Gate transforme WATCH en HOT sémantique | Déduplication confondue avec sens | Gate conserve rôle reçu | QA-BRICK-16 |
| FP-17 | B6 événement isolé | Mémoire match sur signal unique | Pas de film pattern | `NO_FILM_MATCH` ou film faible | QA-BRICK-17 |
| FP-18 | Data degraded masquée | Lecture forte malgré M1 manquant | Guards invisibles | `READING_PARTIAL` en haut | QA-BRICK-18 |
| FP-19 | Fresh load faux | P1 fort mais après extension | Freshness absent | `CONSUMED_LOAD` ou `LATE_LOAD` | QA-BRICK-19 |
| FP-20 | Telegram prématuré | Alerte envoyée avant QA terrain | Feature flag mal gardé | `TELEGRAM_OFF_UNTIL_QA` | QA-BRICK-20 |

## 2. Détails par faux positif

### FP-01 — B3+B2 false birth

- **Symptôme** : B3 détecte un détachement et B2 détecte une cascade ; le packet affiche naissance ou release.
- **Cause** : confusion entre empilement d'événements et validation structurelle.
- **Requalification attendue** : `EVENT_STACK`, `BIRTH_ATTEMPT`, `FALSE_BIRTH_POSSIBLE`.
- **Test QA** : aucun `RELEASE_VALIDATED` ne peut sortir sans prix, zone, B7, data.

### FP-02 — B3 directionnel sans prix

- **Symptôme** : `PAIR_UP` ou `PAIR_DOWN` fort, mais le prix n'accepte pas la zone.
- **Cause** : angle lu comme décision de film.
- **Requalification attendue** : `DETACHMENT_ATTEMPT`, `PRICE_CONFIRMATION=PENDING`.
- **Test QA** : si `price_confirmation != ACCEPTED`, pas de release validée.

### FP-03 — HOT sans déplacement prix

- **Symptôme** : HOT affiché mais prix plat ou contradictoire.
- **Cause** : alerte événementielle sans arbitre prix.
- **Requalification attendue** : `PRESSURE_PENDING`.
- **Test QA** : HOT sans déplacement prix doit rester attente, pas validation.

### FP-04 — B3+B4+P1 rejeté par prix

- **Symptôme** : compression + énergie + détachement puis rejet prix.
- **Cause** : release candidate promue trop tôt.
- **Requalification attendue** : `RELEASE_FAILED`, `COUNTER_BREATH_REJECTED`, ou `EXHAUSTION` selon film.
- **Test QA** : prix contraire après candidate doit invalider ou reclasser.

### FP-05 — B8 coverage faible

- **Symptôme** : cross-symbol validation affichée alors que crosses absents/stale.
- **Cause** : absence de coverage guard.
- **Requalification attendue** : `B8_DEGRADED`, `CROSS_VALIDATION_DEGRADED`, `HONEST_UNKNOWN`.
- **Test QA** : coverage faible interdit driver fort.

### FP-06 — LTF_ONLY pris pour structure

- **Symptôme** : M1 bouge fort mais M5/M15 ne relaient pas.
- **Cause** : propagation B7 absente ou ignorée.
- **Requalification attendue** : `LTF_ONLY`, `WATCH`, `LOCAL_PRESSURE_VALID` ou `RELEASE_CANDIDATE` max.
- **Test QA** : `LTF_ONLY` ne peut pas valider une structure.

### FP-07 — Stale packet pris pour live

- **Symptôme** : lecture affichée comme active mais timestamp ancien.
- **Cause** : packet freshness non exposée.
- **Requalification attendue** : `PACKETS_STALE`, `READING_PARTIAL`.
- **Test QA** : stale doit être visible en haut.

### FP-08 — event_at devant detected_at

- **Symptôme** : chronologie impossible ou latence excessive.
- **Cause** : offset non contrôlé.
- **Requalification attendue** : `EVENT_TIME_OFFSET`, audit line obligatoire.
- **Test QA** : event_at > detected_at ou offset trop haut downgrade packet.

### FP-09 — Counter-breath lu comme release inverse

- **Symptôme** : PAIR_UP après release down/lower lock affiché comme fresh release up.
- **Cause** : oubli du dernier événement structurel.
- **Requalification attendue** : `COUNTER_BREATH_UP` jusqu'à acceptation prix.
- **Test QA** : last_structural_event release down bloque fresh release up sans réintégration.

### FP-10 — Pullback lu comme reversal

- **Symptôme** : PAIR_DOWN après release up affiché comme fresh down.
- **Cause** : contexte post-release absent.
- **Requalification attendue** : `POST_RELEASE_PULLBACK` jusqu'à rupture/rejet confirmé.
- **Test QA** : pullback post-release ne devient reversal qu'après price rejection/zone break.

### FP-11 — Late bounce lu comme naissance

- **Symptôme** : fin de session, faible relais, signal affiché comme fresh.
- **Cause** : session context absent.
- **Requalification attendue** : `LATE_THIN_BOUNCE`.
- **Test QA** : session tardive + LTF_ONLY => pas fresh release.

### FP-12 — Exhaustion lu comme continuation

- **Symptôme** : extension après zone haute déjà travaillée.
- **Cause** : état `CONSUMED` absent.
- **Requalification attendue** : `EXHAUSTION_DETACHMENT`, `RELEASE_CONSUMED`.
- **Test QA** : après high rejection ou high exhaustion, UP tardif devient suspect/consumed.

### FP-13 — B5 relation forcée

- **Symptôme** : leader/follower affiché avec corr faible ou ambiguë.
- **Cause** : B5 force une structure relationnelle.
- **Requalification attendue** : `RELATIONAL_MIXED`, `B5_B8_HONEST_UNKNOWN`.
- **Test QA** : corr/coverage insuffisant => honest unknown.

### FP-14 — Evidence spam

- **Symptôme** : evidence_refs longs mais non exploitables.
- **Cause** : preuves non liées aux champs.
- **Requalification attendue** : evidence rejetée si `field_supported` absent.
- **Test QA** : chaque evidence doit supporter un champ.

### FP-15 — Dashboard décide

- **Symptôme** : dashboard_* modifie un rôle.
- **Cause** : fuite logique métier vers affichage.
- **Requalification attendue** : logique déplacée dans `pf_*`.
- **Test QA** : dashboard read-only sur sémantique.

### FP-16 — Alert Gate renomme le signal

- **Symptôme** : Gate change WATCH/INFO en HOT ou renomme le rôle.
- **Cause** : déduplication confondue avec interprétation.
- **Requalification attendue** : Gate conserve le rôle, ajoute seulement état de transmission.
- **Test QA** : Gate n'écrit pas `qualified_bias`.

### FP-17 — B6 événement isolé

- **Symptôme** : mémoire match basé sur un seul signal.
- **Cause** : B6 pas encore film memory.
- **Requalification attendue** : `NO_FILM_MATCH` ou `WEAK_FILM_MATCH`.
- **Test QA** : memory match exige sequence + context + price_arbiter.

### FP-18 — Data degraded masquée

- **Symptôme** : lecture forte malgré M1 absent/stale.
- **Cause** : Guards non priorisés.
- **Requalification attendue** : `READING_PARTIAL` en haut.
- **Test QA** : degraded visibility doit être premier bloc packet.

### FP-19 — Fresh load faux

- **Symptôme** : P1 fort après mouvement déjà consommé.
- **Cause** : freshness_state absent.
- **Requalification attendue** : `CONSUMED_LOAD` ou `LATE_LOAD`.
- **Test QA** : P1 doit exposer freshness.

### FP-20 — Telegram prématuré

- **Symptôme** : transmission live avant QA V7.6.
- **Cause** : feature flag non verrouillé.
- **Requalification attendue** : `TELEGRAM_OFF_UNTIL_QA`.
- **Test QA** : flag Telegram false par défaut.
