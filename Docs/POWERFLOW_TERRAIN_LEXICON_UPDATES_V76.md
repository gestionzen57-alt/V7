# POWERFLOW TERRAIN LEXICON UPDATES V7.6

Ce lexique ajoute les termes terrain nécessaires pour que PowerFlow V7.6 cesse de laisser `PAIR_UP`, `PAIR_DOWN`, `HOT` ou `WATCH` porter seuls la lecture cockpit.

| TERM | TYPE | DEFINITION | EXAMPLE | DO_NOT_CONFUSE_WITH | COCKPIT_USAGE |
|---|---|---|---|---|---|
| `film_state` | field | État synthétique du film courant | `LOWER_ZONE_ACTIVE` | raw bias | Première ligne cockpit |
| `last_structural_event` | field | Dernier événement qui structure la lecture suivante | `COUNTER_BREATH_REJECTED` | dernière alerte brute | Ligne mémoire |
| `current_move_role` | field | Rôle du mouvement actuel dans le film | `POST_LOW_REACTION` | direction brute | Champ central |
| `raw_bias` | field | Bias brut moteur conservé pour traçabilité | `PAIR_UP` | décision | Affiché après requalification |
| `qualified_bias` | field | Bias brut reclassé par film, zone et prix | `POST_LOW_COUNTER_BREATH` | signal buy/sell | Message interprétable |
| `packet_quality` | field | Qualité comportementale du packet | `REACTION_NOT_RELEASE` | score de trade | Badge qualité |
| `price_confirmation` | field | Statut de confirmation/invalidation par le prix | `PRICE_PENDING` | entrée/sortie | Badge prix obligatoire |
| `data_visibility` | field | Limites de lecture data | `DATA_PARTIAL` | erreur système silencieuse | Haut cockpit si dégradé |
| `LOW_ZONE_BUILDING` | film_state | Construction d'une base basse sans release validée | Pression basse + compression | release validée | Film courant |
| `LOWER_ZONE_ACTIVE` | film_state | Zone basse active avec retests, reactions, locks | PAIR_UP après lower lock | reversal validé | Contexte dominant |
| `HIGH_ZONE_ACTIVE` | film_state | Zone haute active avec extension/rejet possible | late UP near high | fresh release | Contexte dominant |
| `RANGE_ACTIVE` | film_state | Corridor actif sans acceptation claire | mid-range oscillation | structure directionnelle | Film neutre structuré |
| `LOWER_LOCK` | film_state | Acceptation basse verrouillée | release down + lower acceptance | simple low touch | Lecture future UP=counter-breath |
| `HIGH_ZONE_REJECTION` | film_state/event | Refus d'une extension haute | high test rejected | simple pullback | Requalifie DOWN en unwind |
| `POST_HIGH_UNWIND` | film_state/role | Relâchement après high rejeté | PAIR_DOWN after rejected high | fresh down release | Rôle principal du mouvement |
| `POST_RELEASE_UNWIND` | film_state | Respiration inverse après release validée | DOWN after release UP | release inverse | Film post-release |
| `POST_RELEASE_REBUILD` | film_state | Reconstruction de tension après digestion | pullback absorbed + pressure reload | first birth | Contexte continuation possible |
| `PRE_LONDON_FALSE_BIRTHS` | film_state | Activité pré-London avec naissances non confirmées | B3+B2 active no price acceptance | release validated | Data/phase warning |
| `LOWER_ZONE_RANGE_ACTIVE` | film_state | Range local dans zone basse | lower range with counter-breaths | clean trend | Film local |
| `READING_PARTIAL` | film_state/data | Lecture incomplète par manque de data ou stale packets | M1 missing | no signal | Alerte data visible |
| `UNKNOWN` | generic enum | État non déterminé honnêtement | contradictory data | default neutral | Champ autorisé |
| `RELEASE_UP_VALIDATED` | structural_event | Release UP confirmée par prix/zone/relais | low rebuild -> acceptance higher | PAIR_UP alone | Last event |
| `RELEASE_DOWN_VALIDATED` | structural_event | Release DOWN confirmée par prix/zone/relais | lower lock accepted | PAIR_DOWN alone | Last event |
| `COUNTER_BREATH_REJECTED` | structural_event/role | Respiration inverse rejetée | UP after down release fails | pullback absorbed | Alimente second leg |
| `LOWER_LOCK_CONFIRMED` | structural_event | Zone basse verrouillée | price accepts below zone | spike low | Mémoire structurelle |
| `SECOND_LEG_UP` | structural_event | Deuxième jambe UP après absorption/rebuild | pullback absorbed then continuation | first release | Mémoire de continuation |
| `SECOND_LEG_DOWN` | structural_event | Deuxième jambe DOWN après counter-breath rejeté | lower low after rejected bounce | fresh release | Mémoire de continuation |
| `PULLBACK_ABSORBED` | structural_event/role | Pullback digéré sans invalider release | shallow pullback then continuation | release inverse | Rôle de respiration |
| `FAILED_REINTEGRATION` | structural_event/role | Retour dans zone échoué | attempt above lower lock rejected | acceptance | Renforce lock |
| `FALSE_BIRTH` | structural_event | Naissance détectée mais non validée | B3+B2 no relay/no price | no alert | Qualifier sans censurer |
| `EXHAUSTION` | structural_event/role | Mouvement consommé ou tardif | late high extension rejected | fresh release | Qualité/texture |
| `RELEASE_CANDIDATE` | move_role | Release possible mais non validée | B3+B4+P1 active | release validated | Watch state |
| `RELEASE_VALIDATED` | move_role | Release confirmée par prix | acceptance beyond zone | candidate | Role central |
| `RELEASE_CONSUMED` | move_role | Release déjà mature | late continuation near high | birth | Qualité dégradée |
| `PRESSURE_PENDING` | move_role | Pression sans décision prix | HOT without price move | release | Watch condition |
| `LOCAL_PRESSURE_VALID` | move_role | Pression locale mais pas structurelle | M1 push no M5 relay | full release | Badge tactique |
| `COUNTER_BREATH` | move_role | Respiration inverse post-event | PAIR_UP after down release | reversal | Role principal |
| `POST_RELEASE_PULLBACK` | move_role | Pullback contre release validée | PAIR_DOWN after release UP | release DOWN | Rôle de respiration |
| `SECOND_LOW_TEST` | move_role | Retest bas après lower lock | low retest after release down | new fresh release | Watch bas de zone |
| `POST_LOW_REACTION` | move_role | Réaction après test bas | UP after lower retest | release UP | Rôle réaction |
| `LATE_THIN_BOUNCE` | move_role | Bounce tardif ou peu relayé | session late + thin data | strong reversal | Qualité limitée |
| `REINTEGRATION_ATTEMPT` | move_role | Tentative de retour dans zone | price tries above lower lock | acceptance | Role candidat |
| `LOWER_RANGE_ACTIVE` | zone_status | Zone basse encore travaillée | lower zone oscillation | acceptance above | Badge zone |
| `HIGH_RANGE_ACTIVE` | zone_status | Zone haute encore travaillée | high-zone digestion | clean breakout | Badge zone |
| `ACCEPTANCE_ABOVE_ZONE` | zone_status | Acceptation au-dessus d'une zone | closes above zone | wick above | Confirmation prix/zone |
| `ACCEPTANCE_BELOW_ZONE` | zone_status | Acceptation sous une zone | closes below zone | wick below | Confirmation prix/zone |
| `REJECTION_HIGH` | zone_status | Rejet d'une extension haute | high fails | midrange pullback | Badge zone |
| `REJECTION_LOW` | zone_status | Rejet d'une extension basse | low fails | clean breakdown | Badge zone |
| `RANGE_MID_NOISE` | zone_status | Bruit au milieu de range | oscillation mid corridor | edge test | Avertit faible structure |
| `LTF_ONLY` | propagation_state | Mouvement visible seulement LTF | M1 active, M5 absent | full relay | Badge propagation |
| `LTF_MTF_RELAY` | propagation_state | Relais M1/M5/M15 visible | M1 detachment plus M5 support | isolated M1 | Badge propagation |
| `FAILED_PROPAGATION` | propagation_state | Tentative non relayée | M1 push dies before M5 | rejection price only | Risque technique |
| `RELAY_DEGRADING` | propagation_state | Relais présent puis affaibli | M5 thins after push | stable relay | Texture/qualité |
| `STRUCTURAL_DETACHMENT` | detachment_texture | Détachement frais structurant | clean angle + price acceptance | noisy detachment | Qualité haute |
| `NOISY_DETACHMENT` | detachment_texture | Détachement bruité | high noise ratio M1 | no signal | Risque technique |
| `COUNTER_BREATH_DETACHMENT` | detachment_texture | Détachement inverse post-structure | UP after lower lock | fresh release | Requalification |
| `POST_RELEASE_DETACHMENT` | detachment_texture | Détachement pendant digestion post-release | pullback move | new release | Rôle de phase |
| `LATE_SESSION_DETACHMENT` | detachment_texture | Détachement tardif session | late thin bounce | London ignition | Qualité limitée |
| `EXHAUSTION_DETACHMENT` | detachment_texture | Détachement de fin d'extension | high zone late UP | birth | Consumed warning |
| `REJECTION_DETACHMENT` | detachment_texture | Détachement issu d'un rejet | down after high rejection | fresh release | Texture |
| `FULL_STACK_VISIBLE` | data_visibility | M1/M5/M15/HTF disponibles | complete packet | accuracy guarantee | Badge data |
| `TACTICAL_OK` | data_visibility | Assez de data LTF pour lecture tactique | M1/M5 ok | full stack | Badge data |
| `DATA_PARTIAL` | data_visibility | Données partielles | M1 missing or stale | unknown hidden | Haut cockpit |
| `MICROFILM_MISSING` | data_visibility | M1 absent | no M1 history | no issue | Haut cockpit |
| `PACKETS_STALE` | data_visibility | Packets trop vieux | last alert aged | valid fresh packet | Haut cockpit |
| `HONEST_UNKNOWN` | packet_quality | Confirmation relationnelle/terrain insuffisante | B5/B8 weak | failure | Badge qualité |
| `REACTION_NOT_RELEASE` | packet_quality | Mouvement est réaction, pas release | post-low bounce | release | Badge qualité |
| `FRESH_STRUCTURE` | packet_quality | Structure fraîche validée | release accepted | late push | Badge qualité |
| `DEGRADED` | packet_quality | Qualité analytique dégradée | stale/no relay | invalid trade | Badge qualité |
