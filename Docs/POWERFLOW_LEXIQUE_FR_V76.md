# POWERFLOW LEXIQUE FR V7.6

## Doctrine

PowerFlow garde des enums anglaises dans le code pour rester stable, testable et compatible Git.

Mais l’affichage trader, Telegram et les rapports humains doivent parler français.

Règle :
- Code interne : anglais stable.
- Trader / Telegram : français clair.
- Si un terme est inconnu : afficher aussi l’enum brute pour éviter de cacher l’information.

## Champs principaux

| Champ interne | Français trader | Sens |
|---|---|---|
| `film_state` | Film du marché | Contexte global actuel du marché. |
| `last_structural_event` | Dernier événement structurel | Dernier événement important qui change la lecture. |
| `current_zone` | Zone active | Zone de prix actuellement travaillée. |
| `current_zone_status` | Statut de la zone | Ce que le prix fait dans cette zone. |
| `current_move_role` | Rôle du mouvement | À quoi sert le mouvement actuel. |
| `raw_bias` | Signal brut | Ce que les briques voient avant interprétation. |
| `qualified_bias` | Lecture qualifiée | Ce que le signal signifie dans le film. |
| `packet_quality` | Qualité du packet | Fiabilité, maturité ou limite du signal. |
| `price_confirmation` | Confirmation prix | Ce que le prix confirme ou invalide. |
| `propagation_state` | Propagation | Le mouvement reste local ou se propage. |
| `detachment_texture` | Texture du détachement | Nature du mouvement : propre, bruité, tardif, rejeté. |
| `data_visibility` | Visibilité data | Ce que PowerFlow voit ou ne voit pas. |
| `technical_risks` | Risques techniques | Données manquantes, décalages, packets périmés. |
| `watch_condition` | À surveiller | Ce qui doit réveiller l’attention. |
| `invalidation_condition` | Invalidation | Ce qui annule la lecture actuelle. |

## Valeurs fréquentes

| Enum | Français |
|---|---|
| `ACCEPTANCE_ABOVE_ZONE` | Acceptation au-dessus de la zone |
| `ACCEPTANCE_BELOW_ZONE` | Acceptation sous la zone |
| `ACTIVE` | Actif |
| `B5_B8_HONEST_UNKNOWN` | Relationnel inconnu honnête |
| `B8_DEGRADED` | B8 dégradé |
| `CANDIDATE` | Candidat |
| `CONFIRMED` | Confirmé |
| `CONSUMED` | Consommé |
| `CONTINUATION_ACCEPTED` | Continuation acceptée |
| `COUNTERFLOW_AGAINST_STRUCTURE` | Contre-flux contre structure |
| `COUNTER_BREATH` | Contre-souffle |
| `COUNTER_BREATH_DETACHMENT` | Détachement de contre-souffle |
| `COUNTER_BREATH_REJECTED` | Contre-souffle rejeté |
| `DATA_LIMITED` | Data limitée |
| `EVENT_TIME_AHEAD_OF_DETECTED_AT` | Event_at devant detected_at |
| `EVENT_TIME_OFFSET` | Décalage temporel événement |
| `EXHAUSTION` | Épuisement |
| `EXHAUSTION_DETACHMENT` | Détachement d’épuisement |
| `EXHAUSTION_OR_CONSUMED` | Épuisé ou déjà consommé |
| `EXHAUSTION_RISK` | Risque d’épuisement |
| `FAILED_PROPAGATION` | Propagation échouée |
| `FALSE_BIRTH` | Fausse naissance |
| `FALSE_REACTION_DETACHMENT` | Fausse réaction |
| `FRESH` | Frais |
| `FULL_READING` | Lecture complète |
| `HIGH_RANGE_ACTIVE` | Range haut actif |
| `HIGH_ZONE_ACTIVE` | Zone haute active |
| `HIGH_ZONE_EXHAUSTION_RISK` | Risque d’épuisement en zone haute |
| `HIGH_ZONE_REJECTION` | Rejet de zone haute |
| `HONEST_UNKNOWN` | Inconnu honnête |
| `HOT` | Pression chaude |
| `INVALIDATED` | Invalidé |
| `LATE` | Tardif |
| `LATE_SESSION_DETACHMENT` | Détachement tardif |
| `LATE_THIN_BOUNCE` | Rebond tardif fragile |
| `LOWER_LOCK` | Verrouillage bas |
| `LOWER_LOCK_CONFIRMED` | Verrouillage bas confirmé |
| `LOWER_RANGE_ACTIVE` | Range bas actif |
| `LOWER_ZONE_ACTIVE` | Zone basse active |
| `LTF_MTF_RELAY` | Relais petit timeframe vers moyen timeframe |
| `LTF_ONLY` | Local seulement |
| `M1_MISSING` | M1 manquant |
| `MICROFILM_MISSING` | Microfilm manquant |
| `MIXED` | Signal mixte |
| `MTF_HTF_RELAY` | Relais moyen timeframe vers grand timeframe |
| `NEUTRAL` | Neutre |
| `NOISY_DETACHMENT` | Détachement bruité |
| `PACKETS_STALE` | Packets périmés |
| `PAIR_DOWN` | Signal brut baissier |
| `PAIR_UP` | Signal brut haussier |
| `PENDING` | En attente |
| `POST_HIGH_UNWIND` | Déroulement baissier après rejet haut |
| `POST_LOW_COUNTER_BREATH` | Contre-souffle depuis zone basse |
| `POST_LOW_REACTION` | Réaction après bas |
| `POST_RELEASE_COUNTER_BREATH` | Contre-souffle après libération |
| `POST_RELEASE_DETACHMENT` | Détachement post-libération |
| `POST_RELEASE_PULLBACK` | Pullback après libération |
| `POST_RELEASE_REBUILD` | Reconstruction après libération |
| `POST_RELEASE_UNWIND` | Déroulement après libération |
| `PRESSURE_PENDING` | Pression en attente |
| `PRE_LONDON_FALSE_BIRTHS` | Fausses naissances pré-London |
| `PRICE_ABSORBED_PULLBACK` | Pullback absorbé par le prix |
| `PRICE_ACCEPTED_ABOVE_ZONE` | Prix accepté au-dessus de la zone |
| `PRICE_ACCEPTED_BELOW_ZONE` | Prix accepté sous la zone |
| `PRICE_CONFIRMED` | Prix confirmé |
| `PRICE_FAILED` | Prix échoué |
| `PRICE_INVALIDATED` | Prix invalidé |
| `PRICE_PENDING` | Prix en attente |
| `PRICE_REJECTED_HIGH` | Prix rejeté en haut |
| `PRICE_REJECTED_LOW` | Prix rejeté en bas |
| `PULLBACK_ABSORBED` | Pullback absorbé |
| `RANGE_ACTIVE` | Range actif |
| `RANGE_MID_NOISE` | Bruit de milieu de range |
| `REACTION_NOT_RELEASE` | Réaction, pas libération |
| `READING_PARTIAL` | Lecture partielle |
| `REJECTION_DETACHMENT` | Détachement de rejet |
| `REJECTION_HIGH` | Rejet de zone haute |
| `REJECTION_LOW` | Rejet de zone basse |
| `RELAY_DEGRADING` | Relais qui se dégrade |
| `RELEASE_CANDIDATE` | Candidat à la libération |
| `RELEASE_CONSUMED` | Libération consommée |
| `RELEASE_DOWN_VALIDATED` | Libération baissière validée |
| `RELEASE_UP_VALIDATED` | Libération haussière validée |
| `RELEASE_VALIDATED` | Libération validée |
| `SECOND_LEG` | Deuxième jambe |
| `SECOND_LEG_DOWN` | Deuxième jambe baissière |
| `SECOND_LEG_UP` | Deuxième jambe haussière |
| `STRUCTURAL_CONTINUATION` | Continuation structurelle |
| `STRUCTURAL_DETACHMENT` | Détachement structurel |
| `STRUCTURAL_REACTION` | Réaction structurelle |
| `TEMPORAL_GAPS` | Trous temporels |
| `UNKNOWN` | Inconnu |
| `UP_CONTINUATION_ACCEPTED` | Continuation haussière acceptée |
| `WATCH` | À surveiller |

## Exemple Telegram FR

```text
GBPUSD — Rejet de zone haute

Film : Rejet de zone haute
Dernier événement : Rejet de zone haute
Lecture : Signal brut baissier → Déroulement baissier après rejet haut
Qualité : Réaction structurelle
Prix : Prix rejeté en haut
Propagation : Relais petit timeframe vers moyen timeframe
Texture : Détachement de rejet
Data : Lecture partielle
Risques : Décalage temporel événement
À surveiller : price_acceptance_or_rejection_follow_through
Invalidation : opposite_price_acceptance_or_failed_follow_through
```

