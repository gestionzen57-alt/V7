# POWERFLOW BRICK AUDIT TERRAIN V7.6 FINAL

## 0. Doctrine

Les briques voient.
La grammaire nomme.
Le prix arbitre.
B7 juge la propagation.
B7+ juge la texture.
B6 compare aux films.
Guards disent si PowerFlow est aveugle.
Le packet réveille le trader sans décider.

Doctrine opérationnelle V7.6 : une brique ne valide jamais seule un film. Elle apporte une preuve partielle, datée, qualifiée, et révisable par le prix, la zone, la propagation, la texture et la visibilité data.

```text
RAW EVENT -> TERRAIN ROLE -> PRICE ARBITER -> PACKET QUALITY -> TRADER ATTENTION
```

## 1. Diagnostic général

PowerFlow V7.5 possède assez de briques pour percevoir des fragments : empilement, détachement, compression, énergie, gravité relationnelle, mémoire, propagation, texture, guards, evidence et packet. Le problème V7.6 n'est pas l'absence de capteurs. Le problème est la surinterprétation de certains capteurs en rôle de film.

### Briques utiles

- **B2** est utile pour détecter l'empilement d'événements.
- **B3** est utile pour détecter une tentative de détachement.
- **B4** est utile pour détecter compression, respiration ou densité temporelle.
- **P1** est utile pour détecter charge, énergie et élastique.
- **B5/B8** sont utiles comme contexte relationnel si la couverture est suffisante.
- **B6** est critique si transformé en mémoire de films, pas mémoire d'événements isolés.
- **B7** est critique pour distinguer LTF local vs propagation réelle.
- **B7+** est critique pour dire si le détachement est structurel, bruité, tardif, rejeté, post-release ou counter-breath.
- **Guards** sont prioritaires si PowerFlow voit mal.

### Briques surinterprétées

- **B2+B3** est parfois traité comme naissance. C'est faux. C'est un `EVENT_STACK` ou `BIRTH_ATTEMPT`.
- **B3+B4+P1** est parfois traité comme release validée. C'est faux sans prix accepté, zone cohérente, propagation B7 et data acceptable.
- **HOT** est parfois traité comme majeur. C'est faux : HOT peut être `PRESSURE_PENDING`, `LATE_THIN_BOUNCE`, `POST_LOW_REACTION`, `EXHAUSTION_OR_CONSUMED`.
- **PAIR_UP / PAIR_DOWN** est trop brut : il faut requalifier par le film courant.

### Briques trop nerveuses

- **B2** déclenche vite et peut empiler du bruit.
- **B3** est sensible aux micro-décrochages M1.
- **Alert Gate** peut donner une impression de certitude si la déduplication masque la faiblesse des preuves.
- **Evidence Bus** peut devenir bruit si chaque preuve n'indique pas clairement quel champ elle supporte.

### Briques à réduire à des états cockpit simples

- **B7** doit sortir des états simples : `LTF_ONLY`, `LTF_MTF_RELAY`, `MTF_HTF_RELAY`, `FAILED_PROPAGATION`, `RELAY_DEGRADING`, `COUNTERFLOW_AGAINST_STRUCTURE`, `UNKNOWN`.
- **B7+** doit sortir des textures terrain simples : `STRUCTURAL_DETACHMENT`, `NOISY_DETACHMENT`, `COUNTER_BREATH_DETACHMENT`, `POST_RELEASE_DETACHMENT`, `LATE_SESSION_DETACHMENT`, `EXHAUSTION_DETACHMENT`, `REJECTION_DETACHMENT`, `FALSE_REACTION_DETACHMENT`, `UNKNOWN`.
- **Guards** doivent apparaître en haut du packet : si la lecture est partielle, tout le reste descend en fiabilité.

## 2. Tableau global

| BRICK | RAW ROLE | TERRAIN ROLE V7.6 | CURRENT RISK | MUST NOT DO | OUTPUT FIELD | QA RULE |
|---|---|---|---|---|---|---|
| B2 event stack | Empilement d'événements | Détecter densité d'événements récents | Assimilé à naissance | Ne jamais valider une release | `event_stack_state` | B2 seul ou B2+B3 ne valide jamais `RELEASE_VALIDATED` |
| B3 detachment | Décrochage angulaire / birth attempt | Détecter tentative de détachement | Trop directionnel | Ne pas décider direction structurelle sans prix | `detachment_state`, `current_move_role` support | B3 doit être crosscheck par B7+, prix, zone |
| B4 compression | Compression / respiration | Détecter densité temporelle et contraction | Contexte faible | Ne pas confondre compression et release | `compression_state` | Compression seule = `PRESSURE_PENDING` max |
| P1 energy | Charge / énergie / elastic load | Détecter élastique chargé, fraîcheur, consommation | P1 valide trop | Ne pas valider seul | `energy_state`, `freshness_state` | P1 seul ne valide rien sans prix + propagation |
| B3+B4+P1 | Convergence tensionnelle | `RELEASE_CANDIDATE` | Survalidation | Ne jamais produire `RELEASE_VALIDATED` seul | `release_candidate_state` | Devient validé seulement avec prix + zone + B7 + data |
| B5 relational gravity | Relation devises | Contexte leader/follower si assez robuste | Fausse certitude | Ne pas forcer une relation si coverage faible | `relational_context` | Coverage faible => `B5_B8_HONEST_UNKNOWN` |
| B8 cross-symbol | Validation cross-symbol | Valider ou dégrader driver GBP/USD | Couverture insuffisante | Ne pas conclure vrai GBP strength si crosses absents | `cross_validation_state` | Coverage faible => `B8_DEGRADED` |
| B6 memory | Mémoire historique | Mémoire de films et séquences | Trop événementiel | Ne pas prédire outcome | `memory_match` | B6 fournit analogie, invalidation et faux positifs passés |
| B7 propagation | Propagation multi-TF | Dire local / relay / failed | Trop théorique | Ne pas décider le trade ni la release seul | `propagation_state` | `LTF_ONLY` ne vaut pas structure |
| B7+ texture | Texture détachement | Qualifier la nature du décrochage | Flou | Ne pas produire direction brute | `detachment_texture` | Texture `NOISY` ou `FALSE_REACTION` bloque validation release |
| Guards | Data/session/entropy | Dire si PowerFlow voit assez | Trop bas dashboard | Ne pas masquer une lecture aveugle | `data_visibility`, `session_context`, `entropy_state` | Si degraded, afficher en haut et downgrade packet |
| Time Profiles | LTF/MTF/HTF | Articuler temporalité | Découplage film | Ne pas remplacer B7 | `time_profile_state` | LTF fort + MTF absent = `LTF_ONLY` |
| Evidence Bus | Références de preuves | Support traçable champ par champ | Empilement de bruit | Ne pas accumuler sans champ supporté | `evidence_refs` | Chaque evidence doit supporter un champ nommé |
| Perception Spine actuelle | Synthèse | Synthèse non souveraine | Contredire terrain | Ne pas inventer sémantique | `spine_summary` | Spine ne contredit jamais `terrain_packet` |
| Trader Packet | Surface trader | Lecture qualifiée | Trop brut | Ne pas transformer en conseil | `terrain_packet` | Packet contient rôle, qualité, invalidation, watch |
| Alert Gate | Déduplication | Filtrer répétitions, pas sens | Invention sémantique | Ne pas renommer le rôle | `alert_gate_state` | Gate conserve sémantique fournie par terrain packet |
| Dashboard | Visualisation | Afficher lecture qualifiée | Cosmétique avant perception | Ne pas modifier vérité métier | `dashboard_surface` | Dashboard lit, ne décide pas |
| Telegram | Transmission | OFF V7.6 | Prématuré | Ne pas activer avant QA | `telegram_enabled=false` | Telegram flag OFF jusqu'à QA validée |

## 3. Audit B2

### Rôle terrain

B2 est un capteur d'empilement : il signale que plusieurs événements viennent de se produire dans une fenêtre courte. Son rôle V7.6 est `EVENT_STACK`.

### Problème actuel

B2 est trop assimilé à une naissance. Une séquence d'événements rapprochés peut être un vrai début, mais aussi :

- une agitation M1 ;
- une réaction tardive ;
- une fausse naissance pré-London ;
- une absorption ;
- une micro-cascade post-release ;
- une réaction à packet stale.

### Règle

```text
B2 + B3 != RELEASE_VALIDATED
```

B2+B3 peut produire seulement :

```text
EVENT_STACK
BIRTH_ATTEMPT
PRESSURE_PENDING
```

### Sortie recommandée

```json
{
  "event_stack_state": "EVENT_STACK",
  "birth_attempt": true,
  "event_count_window": 3,
  "window_minutes": 5,
  "technical_risks": ["FALSE_BIRTH_POSSIBLE"]
}
```

### QA

Si B3+B2 apparaît sans prix accepté, sans zone cohérente, sans B7 relay et sans data acceptable, la sortie finale ne peut pas être `RELEASE_VALIDATED`.

## 4. Audit B3

### Rôle terrain

B3 détecte une tentative de détachement : angle, vitesse, accélération, rupture relative d'une devise ou paire par rapport au flux récent.

### Problème actuel

B3 est trop directionnel. Il dit souvent `ça part`, alors que le film peut dire :

- counter-breath ;
- réaction post-low ;
- extension tardive ;
- exhaustion ;
- false reaction ;
- noisy detachment ;
- rejection detachment.

### Crosschecks obligatoires

B3 doit être qualifié par :

- B7+ texture ;
- prix accepté ou rejeté ;
- zone actuelle ;
- dernier événement structurel ;
- propagation B7 ;
- data visibility.

### Sorties possibles

```text
DETACHMENT_ATTEMPT
STRUCTURAL_DETACHMENT
NOISY_DETACHMENT
COUNTER_BREATH_DETACHMENT
POST_RELEASE_DETACHMENT
LATE_SESSION_DETACHMENT
EXHAUSTION_DETACHMENT
REJECTION_DETACHMENT
FALSE_REACTION_DETACHMENT
UNKNOWN
```

### Règle terrain

B3 supporte `current_move_role`, mais ne décide pas `release_validation`.

## 5. Audit B4 + P1

### Rôle B4

B4 détecte compression, expansion, respiration et densité temporelle. Il mesure si les oscillations se resserrent, s'étirent ou deviennent chaotiques.

### Rôle P1

P1 détecte l'énergie, la charge élastique, la vitalité et la tension micro/macro.

### Problème commun

B4+P1 peut donner une impression de charge réelle, mais ne sait pas seul si cette charge est :

```text
FRESH
LATE
CONSUMED
REJECTED
POST_RELEASE
COUNTER_BREATH
NOISY
```

### Règle freshness

P1 doit produire ou supporter un `freshness_state` :

```text
FRESH_LOAD
ACTIVE_LOAD
LATE_LOAD
CONSUMED_LOAD
REJECTED_LOAD
UNKNOWN
```

### Must not do

P1 ne doit pas valider seul une release. B4 ne doit pas confondre compression et cassure.

### Sortie recommandée

```json
{
  "compression_state": "CYCLE_COMPRESSING",
  "energy_state": "ELASTIC_LOADED",
  "freshness_state": "FRESH_LOAD",
  "technical_risks": []
}
```

## 6. Audit B3+B4+P1

Point central V7.6 : cette combinaison est puissante, mais elle produit uniquement `RELEASE_CANDIDATE`.

### Conditions pour `RELEASE_CANDIDATE`

```text
B3 detachment attempt
+B4 compression or compression release context
+P1 elastic/energy load
```

### Conditions pour `RELEASE_VALIDATED`

Elle devient `RELEASE_VALIDATED` uniquement avec :

- prix accepté ;
- zone cohérente ;
- propagation B7 suffisante ;
- data_visibility acceptable.

### Contrat strict

```text
B3+B4+P1 = RELEASE_CANDIDATE
B3+B4+P1+PRICE+ZONE+B7+DATA = RELEASE_VALIDATED
```

### États de sortie

```text
NO_RELEASE
PRESSURE_PENDING
RELEASE_CANDIDATE
RELEASE_VALIDATED
RELEASE_FAILED
RELEASE_CONSUMED
UNKNOWN
```

### QA

Un test doit échouer si un packet final contient `RELEASE_VALIDATED` sans `price_confirmation=ACCEPTED`, `propagation_state in [LTF_MTF_RELAY, MTF_HTF_RELAY]` et `data_visibility` non dégradée.

## 7. Audit B5/B8

### Rôle B5

B5 apporte un contexte relationnel : leader, follower, antagonist, coalition, divergence, synchro.

### Rôle B8

B8 apporte une validation cross-symbol : le mouvement est-il GBP réel, USD faible, mixte, ou inconnu ?

### Problème actuel

La couverture insuffisante peut produire une fausse certitude. Si les crosses ou paires nécessaires ne sont pas disponibles, B8 ne peut pas conclure.

### États requis

```text
RELATIONAL_CONFIRMED
RELATIONAL_MIXED
RELATIONAL_DEGRADED
B5_B8_HONEST_UNKNOWN
CROSS_VALIDATION_CONFIRMED
CROSS_VALIDATION_DEGRADED
B8_DEGRADED
UNKNOWN
```

### Règle

Coverage insuffisant = `HONEST_UNKNOWN`.

### Must not do

- Ne pas forcer `GBP_STRENGTH` avec GBPUSD seul.
- Ne pas forcer `USD_WEAKNESS` sans panier/crosses.
- Ne pas afficher une confiance relationnelle si l'univers de devises est incomplet.

## 8. Audit B6

B6 doit devenir mémoire de films. Il ne doit plus mémoriser seulement des événements isolés.

### Champs obligatoires

```text
FILM_PATTERN
SEQUENCE
TRIGGER
CONTEXT
PRICE_ARBITER
OUTCOME
INVALIDATION
NEXT_EXPECTED_BEHAVIOR
FALSE_POSITIVE
```

### Structure recommandée

```json
{
  "memory_match": {
    "film_pattern": "POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN",
    "sequence": ["LOWER_ACCEPTANCE", "COUNTER_BREATH_UP", "REJECTION", "SECOND_LEG_DOWN"],
    "trigger": "COUNTER_BREATH_REJECTED",
    "context": {
      "session": "LONDON",
      "zone": "LOWER_ZONE",
      "last_structural_event": "RELEASE_DOWN"
    },
    "price_arbiter": "LOWER_LOW_AFTER_COUNTER_BREATH",
    "outcome": "SECOND_LEG_DOWN",
    "invalidation": "ACCEPTANCE_ABOVE_COUNTER_BREATH_HIGH",
    "next_expected_behavior": "LOW_RETEST_OR_SECOND_LEG",
    "false_positive": "LTF_ONLY_COUNTER_BREATH_MISREAD_AS_RELEASE_UP"
  }
}
```

### Règle

B6 compare. B6 ne prédit pas. B6 expose les films analogues, les invalidations connues et les faux positifs passés.

## 9. Audit B7

B7 doit être réduit à une lecture de propagation simple.

### États autorisés

```text
LTF_ONLY
LTF_MTF_RELAY
MTF_HTF_RELAY
FAILED_PROPAGATION
RELAY_DEGRADING
COUNTERFLOW_AGAINST_STRUCTURE
UNKNOWN
```

### Rôle terrain

B7 répond uniquement :

```text
Le mouvement reste-t-il local ?
Se propage-t-il M5/M15/M30 ?
La propagation se dégrade-t-elle ?
Est-il contre la structure précédente ?
```

### Must not do

- Ne pas créer un score global abstrait.
- Ne pas valider un trade.
- Ne pas décider `RELEASE_VALIDATED` sans prix et zone.

### QA

`LTF_ONLY` ne peut pas valider une structure. Il peut réveiller le trader comme naissance locale ou microfilm, mais le packet doit rester `CANDIDATE`, `WATCH`, `PRESSURE_PENDING` ou `READING_PARTIAL` selon data.

## 10. Audit B7+

B7+ doit être réduit à une texture terrain du détachement.

### États autorisés

```text
STRUCTURAL_DETACHMENT
NOISY_DETACHMENT
COUNTER_BREATH_DETACHMENT
POST_RELEASE_DETACHMENT
LATE_SESSION_DETACHMENT
EXHAUSTION_DETACHMENT
REJECTION_DETACHMENT
FALSE_REACTION_DETACHMENT
UNKNOWN
```

### Rôle terrain

B7+ répond :

```text
Quel type de détachement est-ce dans le film ?
```

### Règles

- `STRUCTURAL_DETACHMENT` peut soutenir `RELEASE_CANDIDATE` puis `RELEASE_VALIDATED` si prix+zone+B7+data valident.
- `NOISY_DETACHMENT` garde le packet en `WATCH` ou `READING_PARTIAL`.
- `COUNTER_BREATH_DETACHMENT` requalifie `PAIR_UP` après release down.
- `POST_RELEASE_DETACHMENT` requalifie pullback, continuation ou réaction selon prix.
- `EXHAUSTION_DETACHMENT` empêche de lire une extension tardive comme naissance fraîche.
- `FALSE_REACTION_DETACHMENT` doit alimenter le registre de faux positifs B6.

## 11. Audit Guards

Data visibility doit être visible en haut. Si PowerFlow est aveugle, le packet doit le dire avant tout le reste.

### États obligatoires

```text
FULL_READING
READING_PARTIAL
MICROFILM_MISSING
M1_MISSING
PACKETS_STALE
CROSS_VALIDATION_DEGRADED
B8_DEGRADED
B5_B8_HONEST_UNKNOWN
TEMPORAL_GAPS
EVENT_TIME_OFFSET
UNKNOWN
```

### Rôle terrain

Les Guards qualifient la capacité de perception :

- données M1 présentes ou non ;
- packets frais ou stale ;
- cross-validation disponible ou dégradée ;
- décalage entre `event_at` et `detected_at` ;
- trous temporels ;
- entropy/saturation.

### Règle dashboard

Si un guard est dégradé, il doit apparaître en haut du dashboard et en haut du `terrain_packet`.

### QA

Aucun packet ne doit afficher une lecture forte si `data_visibility` contient `READING_PARTIAL`, `MICROFILM_MISSING`, `M1_MISSING`, `PACKETS_STALE` sans le signaler explicitement.

## 12. Audit Evidence Bus

Evidence Bus doit conserver des `evidence_refs` sans empiler du bruit.

### Chaque evidence doit avoir

```text
source
timestamp
field_supported
confidence
weakness
```

### Exemple

```json
{
  "source": "pf_force_kinematics",
  "timestamp": "2026-05-13T09:17:00Z",
  "field_supported": "detachment_state",
  "confidence": 0.74,
  "weakness": "M5_RELAY_THIN"
}
```

### Règle

Une preuve ne doit pas être ajoutée si elle ne supporte aucun champ du packet. Le bus ne doit pas être une liste brute d'événements ; il doit être un graphe minimal de support champ -> preuve.

## 13. Audit Spine / Trader Packet / Alert Gate

### Perception Spine actuelle

La spine peut synthétiser. Elle ne doit pas contredire `terrain_packet`.

Règle :

```text
terrain_packet > spine_summary > dashboard_surface
```

La spine ne doit pas inventer une sémantique si la grammaire terrain n'a pas produit le rôle.

### Trader Packet

Trader Packet affiche la lecture qualifiée :

```text
film_state
last_structural_event
current_zone
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
memory_match
evidence_refs
```

### Alert Gate

Alert Gate déduplique mais n'invente pas la sémantique.

Il peut :

- éviter répétition ;
- throttler ;
- fusionner messages identiques ;
- marquer stale/repeated.

Il ne peut pas :

- transformer `COUNTER_BREATH` en `RELEASE`;
- masquer `READING_PARTIAL`;
- créer `HOT` sémantique sans preuve terrain.

## 14. Audit Dashboard / Telegram

### Dashboard

Le dashboard est stable. En V7.6, il doit recevoir seulement des ajouts minimaux :

```text
qualified_bias
data_visibility
price_confirmation
propagation_state
detachment_texture
packet_quality
```

Règle : dashboard lit, ne décide pas. Aucune vérité métier ne doit vivre dans `dashboard_*`.

### Telegram

Telegram reste feature flag OFF.

```text
TELEGRAM_TERRAIN_PACKET_ENABLED=false
```

Activation seulement après QA sur les 7 journées GBPUSD et stabilisation du `terrain_packet`.

## 15. Recommandations patch minimal

Ne pas créer une nouvelle spine. Ne pas refaire le dashboard. Ne pas activer Telegram.

### Points de branchement recommandés

```text
pf_terrain_context_once.py
pf_packet_requalification_once.py
pf_film_memory_reader_once.py
terrain_packet.json
terrain_packet_audit.jsonl
```

### Contrats d'intégration

#### pf_terrain_context_once.py

Produit le contexte minimal :

```text
last_structural_event
current_zone
session_context
data_visibility
```

#### pf_packet_requalification_once.py

Lit les outputs des briques et requalifie :

```text
raw_bias -> qualified_bias
raw_event -> current_move_role
B3+B4+P1 -> release_candidate_state
```

#### pf_film_memory_reader_once.py

Lit B6 film library et ajoute :

```text
memory_match
known_false_positive
next_expected_behavior
invalidation_reference
```

#### terrain_packet.json

Surface compacte pour cockpit :

```json
{
  "film_state": "LOWER_ZONE_RANGE_ACTIVE",
  "last_structural_event": "COUNTER_BREATH_REJECTED",
  "current_zone": "LOWER_ZONE",
  "current_move_role": "POST_LOW_REACTION",
  "raw_bias": "PAIR_UP",
  "qualified_bias": "POST_LOW_COUNTER_BREATH",
  "packet_quality": "REACTION_NOT_RELEASE",
  "price_confirmation": "PENDING",
  "propagation_state": "LTF_ONLY",
  "detachment_texture": "COUNTER_BREATH_DETACHMENT",
  "data_visibility": ["READING_PARTIAL", "M1_MISSING", "PACKETS_STALE"],
  "watch_condition": "ACCEPTANCE_ABOVE_RANGE_HIGH",
  "invalidation_condition": "LOW_RETEST_FAILURE",
  "memory_match": "LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL",
  "evidence_refs": []
}
```

#### terrain_packet_audit.jsonl

Trace ligne par ligne :

```json
{"timestamp":"2026-05-14T09:31:00Z","field":"qualified_bias","value":"POST_LOW_COUNTER_BREATH","supported_by":["B3","B7+","B6"],"weakness":["M1_MISSING"]}
```

### Patch minimal accepté

- Ajouter les contrats docs.
- Ajouter QA textuelle.
- Ne pas coder la logique finale isolée.
- Ne pas activer Telegram.
