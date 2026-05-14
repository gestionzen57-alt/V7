# POWERFLOW V7.6 — ENUMS CANONIQUES ET ALIAS

## 0. Principe

Les enums canoniques sont celles que `terrain_packet_v76_0` doit produire.

Les alias existent seulement pour absorber les anciens livrables ou les sorties intermédiaires des GPT satellites. Ils ne doivent pas devenir des valeurs cockpit principales.

## 1. Alias critiques

| Champ | Alias reçu | Valeur canonique |
|---|---|---|
| `current_zone_status` | `LOWER_ZONE_ACTIVE` | `LOWER_RANGE_ACTIVE` |
| `current_zone_status` | `HIGH_ZONE_ACTIVE` | `HIGH_RANGE_ACTIVE` |
| `current_zone_status` | `ABOVE_ZONE` | `ACCEPTANCE_ABOVE_ZONE` |
| `current_zone_status` | `BELOW_ZONE` | `ACCEPTANCE_BELOW_ZONE` |
| `current_zone_status` | `MID_ZONE` | `RANGE_MID_NOISE` |
| `current_zone_status` | `RANGE_ACTIVE` | `RANGE_MID_NOISE` |
| `data_visibility` | `FULL_STACK_VISIBLE` | `FULL_READING` |
| `data_visibility` | `TACTICAL_OK` | `FULL_READING` |
| `data_visibility` | `DATA_PARTIAL` | `READING_PARTIAL` |
| `data_visibility` | `DATA_BLIND` | `READING_PARTIAL` |
| `data_visibility` | `DATA_UNKNOWN` | `UNKNOWN` |
| `propagation_state` | `PROPAGATION_UNKNOWN` | `UNKNOWN` |
| `detachment_texture` | `TEXTURE_UNKNOWN` | `UNKNOWN` |
| `price_confirmation` | `PRICE_UNKNOWN` | `UNKNOWN` |

## 2. Règle cockpit

Le cockpit doit afficher les valeurs canoniques, pas les alias.

Exemple :

```text
RAW=PAIR_UP -> QUALIFIED=POST_LOW_COUNTER_BREATH | ZONE=LOWER_RANGE_ACTIVE | DATA=READING_PARTIAL
```

## 3. Règle B6 memory

La film library peut conserver des descriptions narratives comme :

```text
DOWN_AFTER_COUNTER_BREATH_REJECTED_QUALIFIES_AS_SECOND_LEG_DOWN_IF_PRICE_BREAKS_LOWER
```

Mais ces descriptions ne doivent pas être écrites directement dans `terrain_packet.qualified_bias`.

B6 memory propose un contexte. La requalification produit l'enum finale.
