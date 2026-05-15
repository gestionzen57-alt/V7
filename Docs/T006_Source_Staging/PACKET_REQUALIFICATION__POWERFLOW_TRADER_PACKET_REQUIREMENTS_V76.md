# POWERFLOW TRADER PACKET REQUIREMENTS V7.6

## 0. Objet

Ce document définit le minimum qu'un packet PowerFlow V7.6 doit dire au trader pour être utile. Il ne définit pas une stratégie, ne crée pas de signal de trading et ne modifie pas le dashboard. Il impose une structure de perception exploitable.

## 1. Principe

Un packet utile ne dit pas seulement :

```text
PAIR_UP WATCH
```

Il doit dire :

```text
FILM=...
LAST_EVENT=...
ZONE=...
MOVE=...
RAW_BIAS=...
QUALIFIED_BIAS=...
PACKET_QUALITY=...
PRICE_CONFIRMATION=...
PROPAGATION=...
TEXTURE=...
DATA=...
WATCH=...
INVALIDATION=...
```

## 2. Champs obligatoires

### 2.1 Film

**Champ** : `film_state`

**But** : situer l'événement dans le film courant.

**Exemples** :

- `LOWER_ZONE_ACTIVE`
- `POST_HIGH_UNWIND`
- `PRE_LONDON_FALSE_BIRTHS`
- `READING_PARTIAL`

**Règle** : si le film n'est pas déterminable, utiliser `UNKNOWN`, pas une supposition.

### 2.2 Dernier événement structurel

**Champs** : `last_structural_event`, `last_structural_direction`

**But** : empêcher PowerFlow de lire chaque packet comme un nouveau départ.

**Exemples** :

- `COUNTER_BREATH_REJECTED / DOWN`
- `RELEASE_UP_VALIDATED / UP`
- `HIGH_ZONE_REJECTION / DOWN`

**Règle** : le dernier événement structurel influence la requalification des packets suivants tant qu'il n'est pas invalidé ou consommé.

### 2.3 Zone active

**Champs** : `current_zone`, `current_zone_low`, `current_zone_high`, `current_zone_status`

**But** : dire où le prix travaille.

**Exemples** :

```text
current_zone=LOWER_ZONE_1.3504_1.3532
current_zone_status=LOWER_RANGE_ACTIVE
```

**Règle** : une poussée dans une zone basse active n'a pas le même sens qu'une poussée hors zone acceptée.

### 2.4 Rôle du mouvement

**Champ** : `current_move_role`

**But** : remplacer la lecture directionnelle brute par un rôle terrain.

**Exemples** :

- `COUNTER_BREATH`
- `POST_RELEASE_PULLBACK`
- `PULLBACK_ABSORBED`
- `SECOND_LEG`
- `LATE_THIN_BOUNCE`

**Règle** : `current_move_role` est le champ central du packet.

### 2.5 Qualité du packet

**Champ** : `packet_quality`

**But** : distinguer fresh, réaction, late, degraded, unknown.

**Enums recommandés** :

- `FRESH_STRUCTURE`
- `RELEASE_CANDIDATE_ONLY`
- `REACTION_NOT_RELEASE`
- `LATE_OR_CONSUMED`
- `HONEST_UNKNOWN`
- `DEGRADED`

**Règle** : la qualité qualifie le packet sans le censurer.

### 2.6 Confirmation prix

**Champ** : `price_confirmation`

**But** : dire si le prix confirme, attend, rejette ou invalide.

**Enums recommandés** :

- `PRICE_CONFIRMED`
- `PRICE_PENDING`
- `PRICE_REJECTED`
- `PRICE_INVALIDATED`
- `PRICE_CONSUMED`
- `PRICE_UNKNOWN`

**Règle** : 100% des packets doivent avoir ce champ.

### 2.7 Propagation

**Champ** : `propagation_state`

**But** : dire si le mouvement reste local ou se propage.

**Enums recommandés** :

- `LTF_ONLY`
- `LTF_MTF_RELAY`
- `MTF_HTF_RELAY`
- `FAILED_PROPAGATION`
- `COUNTERFLOW_AGAINST_STRUCTURE`
- `RELAY_DEGRADING`
- `PROPAGATION_UNKNOWN`

**Règle** : absence de relais = information, pas censure.

### 2.8 Texture

**Champ** : `detachment_texture`

**But** : qualifier le type de détachement.

**Enums recommandés** :

- `STRUCTURAL_DETACHMENT`
- `NOISY_DETACHMENT`
- `COUNTER_BREATH_DETACHMENT`
- `POST_RELEASE_DETACHMENT`
- `LATE_SESSION_DETACHMENT`
- `EXHAUSTION_DETACHMENT`
- `REJECTION_DETACHMENT`
- `FALSE_REACTION_DETACHMENT`
- `TEXTURE_UNKNOWN`

**Règle** : B7+ doit rester terrain et lisible, pas théorique.

### 2.9 Limites data

**Champ** : `data_visibility`

**But** : afficher les limites de lecture en haut, pas en note cachée.

**Enums recommandés** :

- `FULL_STACK_VISIBLE`
- `TACTICAL_OK`
- `DATA_PARTIAL`
- `MICROFILM_MISSING`
- `PACKETS_STALE`
- `CROSS_VALIDATION_DEGRADED`
- `DATA_BLIND`
- `DATA_UNKNOWN`

**Règle** : si data dégradée, le cockpit doit le montrer immédiatement.

### 2.10 Watch

**Champ** : `watch_condition`

**But** : dire ce qui mérite attention ensuite.

**Exemples** :

- `acceptance above 1.3532`
- `rejection back into lower zone`
- `M5 relay appears after M1 pressure`

**Règle** : une watch condition n'est pas un ordre.

### 2.11 Invalidation

**Champ** : `invalidation_condition`

**But** : rendre la lecture falsifiable.

**Exemples** :

- `lower low below 1.3504`
- `close back inside rejected high zone`
- `counter-breath accepted above zone`

**Règle** : ce n'est pas un stop. C'est une condition d'invalidation analytique.

## 3. Message cockpit minimal

### Ligne courte

```text
GBPUSD | LOWER_ZONE_ACTIVE | POST_LOW_REACTION | PAIR_UP->POST_LOW_COUNTER_BREATH | PRICE_PENDING | DATA_PARTIAL
```

### Packet humain

```text
GBPUSD: film=LOWER_ZONE_ACTIVE. Last=COUNTER_BREATH_REJECTED/DOWN. Zone=LOWER_RANGE_ACTIVE 1.3504-1.3532. Move=POST_LOW_REACTION. Bias=PAIR_UP->POST_LOW_COUNTER_BREATH. Price=PRICE_PENDING. Propagation=LTF_ONLY. Texture=COUNTER_BREATH_DETACHMENT. Data=DATA_PARTIAL. Watch=acceptance above 1.3532. Invalid=lower low below 1.3504. Risks=M1_MISSING,PACKETS_STALE.
```

### Packet JSON minimal

```json
{
  "schema": "terrain_packet_v76_0",
  "symbol": "GBPUSD",
  "film_state": "LOWER_ZONE_ACTIVE",
  "last_structural_event": "COUNTER_BREATH_REJECTED",
  "last_structural_direction": "DOWN",
  "current_zone": "LOWER_ZONE_1.3504_1.3532",
  "current_zone_low": 1.3504,
  "current_zone_high": 1.3532,
  "current_zone_status": "LOWER_RANGE_ACTIVE",
  "current_move_role": "POST_LOW_REACTION",
  "raw_bias": "PAIR_UP",
  "qualified_bias": "POST_LOW_COUNTER_BREATH",
  "packet_quality": "REACTION_NOT_RELEASE",
  "price_confirmation": "PRICE_PENDING",
  "propagation_state": "LTF_ONLY",
  "detachment_texture": "COUNTER_BREATH_DETACHMENT",
  "data_visibility": "DATA_PARTIAL",
  "watch_condition": "acceptance above 1.3532",
  "invalidation_condition": "lower low below 1.3504",
  "technical_risks": ["M1_MISSING", "PACKETS_STALE"]
}
```

## 4. Requirements d'affichage

1. `film_state`, `current_move_role`, `qualified_bias`, `price_confirmation` et `data_visibility` doivent être visibles sans ouvrir de détail.
2. Si `data_visibility` vaut `DATA_PARTIAL`, `MICROFILM_MISSING`, `PACKETS_STALE`, `CROSS_VALIDATION_DEGRADED` ou `DATA_BLIND`, l'information doit remonter en haut.
3. `raw_bias` doit être visible mais toujours accompagné de `qualified_bias`.
4. `UNKNOWN` doit être affichable sans être considéré comme erreur applicative.
5. `READING_PARTIAL` doit être un état noble de vérité data, pas un échec cosmétique.

## 5. Non-déclencheurs

Un packet trader V7.6 ne doit jamais déclencher directement :

- buy ;
- sell ;
- entry ;
- exit ;
- target ;
- stop ;
- taille de position ;
- exécution automatique.

Il doit seulement réveiller une perception qualifiée.

## 6. Acceptance Criteria

- Aucun packet ne sort avec `PAIR_UP` ou `PAIR_DOWN` seul comme message principal.
- Tous les packets contiennent `data_visibility`.
- Tous les packets contiennent `price_confirmation`.
- Tous les packets contiennent une forme de `watch_condition` ou `UNKNOWN`.
- Tous les packets contiennent une forme de `invalidation_condition` ou `UNKNOWN`.
- `READING_PARTIAL`, `HONEST_UNKNOWN` et `UNKNOWN` sont acceptés par le schéma.
- Le packet est compatible `terrain_packet_v76_0`.
