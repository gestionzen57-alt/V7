# POWERFLOW TERRAIN GRAMMAR V7.6 FINAL

## 0. Doctrine

PowerFlow observe, nomme, qualifie et réveille.
PowerFlow ne décide pas le trade.

La machine perçoit le flux, mesure les tensions, nomme les événements et transmet une lecture exploitable. Le trader filtre, arbitre et agit.

V7.6 ne crée pas une nouvelle spine. V7.6 impose une grammaire terrain minimale pour empêcher les packets bruts de devenir la lecture principale.

## 1. Problème à résoudre

Les lectures `PAIR_UP`, `PAIR_DOWN`, `HOT` et `WATCH` sont trop pauvres parce qu'elles décrivent une direction ou une intensité brute sans expliquer le rôle de l'événement dans le film courant.

Un `PAIR_UP` peut être :

- une release fraîche ;
- une continuation acceptée ;
- un counter-breath après release down ;
- une réaction post-low ;
- un late thin bounce ;
- une exhaustion près d'une high zone.

Un `PAIR_DOWN` peut être :

- une release fraîche ;
- un pullback post-release up ;
- un post-high unwind ;
- un second leg down ;
- un retest de lower lock ;
- une pression locale non propagée.

La grammaire V7.6 remplace donc la direction brute comme message principal par une lecture structurée : film, zone, dernier événement structurel, rôle du mouvement, qualité, confirmation prix, propagation, texture et visibilité data.

## 2. Grammaire cockpit minimale

Tout packet terrain V7.6 doit contenir les champs suivants.

| Champ | Définition | Rôle |
|---|---|---|
| `film_state` | État du film de marché courant | Situe le contexte global immédiat |
| `last_structural_event` | Dernier événement structurel reconnu | Donne la mémoire courte dominante |
| `last_structural_direction` | Direction de ce dernier événement : `UP`, `DOWN`, `MIXED`, `NONE`, `UNKNOWN` | Évite de lire chaque packet comme un nouveau départ |
| `current_zone` | Nom ou identifiant lisible de la zone active | Localise la zone travaillée |
| `current_zone_status` | Statut de zone normalisé | Dit si le prix accepte, rejette ou respire dans la zone |
| `current_move_role` | Rôle du mouvement actuel dans le film | Remplace la lecture brute comme sens principal |
| `raw_bias` | Bias brut hérité du moteur | Conservé comme donnée, jamais dominant |
| `qualified_bias` | Requalification terrain du bias brut | Lecture exploitable du packet |
| `packet_quality` | Qualité comportementale du packet | Évite de confondre signal frais et réaction tardive |
| `price_confirmation` | Statut de confirmation/invalidation par le prix | Le prix tranche le packet |
| `propagation_state` | Propagation multi-TF ou absence de relais | Sépare mouvement local et mouvement relayé |
| `detachment_texture` | Texture du détachement | Qualifie frais, bruité, tardif, rejeté, post-release |
| `data_visibility` | Qualité de visibilité data | Fait apparaître l'aveuglement au lieu de le masquer |
| `watch_condition` | Condition concrète à surveiller | Réveille l'attention sans ordre |
| `invalidation_condition` | Condition qui invalide la lecture | Rend la lecture falsifiable |
| `technical_risks` | Risques techniques ou analytiques | Bruit M1, stale packets, relay absent, SQL latency, etc. |

## 3. Définition de `film_state`

### LOW_ZONE_BUILDING

**Définition terrain** : le marché construit une base basse, avec pression ou compression près de la zone basse, sans release validée.

**Ce que le trader doit comprendre** : la zone basse travaille ; une release peut naître, mais elle n'est pas validée par défaut.

**PowerFlow ne doit pas conclure** : ne pas transformer une poussée UP isolée en release validée.

**Phrase cockpit** : `GBPUSD | LOW_ZONE_BUILDING | pressure near low zone | release not validated`

### LOWER_ZONE_ACTIVE

**Définition terrain** : le prix évolue dans ou près d'une zone basse active, avec retests, locks, réactions ou tentatives de réintégration.

**Ce que le trader doit comprendre** : les mouvements inverses sont souvent des réactions ou counter-breaths tant que l'acceptation prix n'est pas visible.

**PowerFlow ne doit pas conclure** : ne pas lire `PAIR_UP` comme nouvelle structure tant que la zone basse n'est pas quittée proprement.

**Phrase cockpit** : `GBPUSD | LOWER_ZONE_ACTIVE | reaction/counter-breath possible | price must accept above zone`

### HIGH_ZONE_ACTIVE

**Définition terrain** : le prix évolue dans ou près d'une zone haute active, avec extension, exhaustion, rejet ou digestion.

**Ce que le trader doit comprendre** : les nouveaux packets UP peuvent être tardifs ou consommés.

**PowerFlow ne doit pas conclure** : ne pas assimiler un nouveau `PAIR_UP` proche du high à une release fraîche.

**Phrase cockpit** : `GBPUSD | HIGH_ZONE_ACTIVE | UP may be late/consumed | monitor rejection or acceptance`

### RANGE_ACTIVE

**Définition terrain** : le marché respire dans un corridor sans acceptation claire au-dessus ou en dessous.

**Ce que le trader doit comprendre** : les packets directionnels doivent être requalifiés comme pression locale, test de bord ou bruit de milieu de range.

**PowerFlow ne doit pas conclure** : ne pas produire une lecture directionnelle principale sans prix et propagation.

**Phrase cockpit** : `GBPUSD | RANGE_ACTIVE | directional packet requires boundary acceptance`

### LOWER_LOCK

**Définition terrain** : une release down ou une acceptation sous zone a verrouillé une structure basse.

**Ce que le trader doit comprendre** : les remontées suivantes sont d'abord des counter-breaths ou tentatives de réintégration.

**PowerFlow ne doit pas conclure** : ne pas considérer une remontée comme reversal structurel sans acceptation prix.

**Phrase cockpit** : `GBPUSD | LOWER_LOCK | PAIR_UP defaults to counter-breath until acceptance`

### HIGH_ZONE_REJECTION

**Définition terrain** : une zone haute a refusé l'extension ; le prix a rejeté ou échoué à accepter plus haut.

**Ce que le trader doit comprendre** : les `PAIR_DOWN` suivants sont souvent du post-high unwind, pas une simple direction brute.

**PowerFlow ne doit pas conclure** : ne pas appeler tout DOWN une release fraîche.

**Phrase cockpit** : `GBPUSD | HIGH_ZONE_REJECTION | DOWN reads as post-high unwind`

### POST_HIGH_UNWIND

**Définition terrain** : phase de relâchement après rejet ou exhaustion haute.

**Ce que le trader doit comprendre** : le mouvement peut être une digestion structurelle de la high zone rejetée.

**PowerFlow ne doit pas conclure** : ne pas ignorer le high rejeté précédent.

**Phrase cockpit** : `GBPUSD | POST_HIGH_UNWIND | active unwind after rejected high`

### POST_RELEASE_UNWIND

**Définition terrain** : après une release validée, le marché relâche, corrige ou respire contre la release.

**Ce que le trader doit comprendre** : le mouvement inverse n'est pas automatiquement une nouvelle phase ; il peut être pullback ou respiration.

**PowerFlow ne doit pas conclure** : ne pas classer un pullback comme release inverse sans invalidation prix.

**Phrase cockpit** : `GBPUSD | POST_RELEASE_UNWIND | inverse packet treated as pullback until invalidation`

### POST_RELEASE_REBUILD

**Définition terrain** : après release et digestion, le marché reconstruit une tension compatible avec continuation ou second leg.

**Ce que le trader doit comprendre** : il faut lire la qualité de rebuild : absorption, compression, propagation.

**PowerFlow ne doit pas conclure** : ne pas valider second leg sans prix.

**Phrase cockpit** : `GBPUSD | POST_RELEASE_REBUILD | watch absorption and relay`

### PRE_LONDON_FALSE_BIRTHS

**Définition terrain** : avant London ou autour d'une transition, plusieurs détachements apparents naissent sans acceptation ni relais.

**Ce que le trader doit comprendre** : B3+B2 peut signaler de l'activité, pas une naissance validée.

**PowerFlow ne doit pas conclure** : ne pas promouvoir `EVENT_STACK` en `BIRTH_VALIDATED`.

**Phrase cockpit** : `GBPUSD | PRE_LONDON_FALSE_BIRTHS | event stack active, release not validated`

### LOWER_ZONE_RANGE_ACTIVE

**Définition terrain** : range local installé dans une zone basse, avec counter-breaths, rejets et retests.

**Ce que le trader doit comprendre** : un UP dans ce contexte est souvent réaction post-low ou counter-breath ; un DOWN peut être retest ou second low test.

**PowerFlow ne doit pas conclure** : ne pas annoncer une phase directionnelle propre sans sortie de range.

**Phrase cockpit** : `GBPUSD | LOWER_ZONE_RANGE_ACTIVE | post-low reaction inside lower range`

### READING_PARTIAL

**Définition terrain** : la visibilité est insuffisante : M1 manquant, packets stale, cross-validation faible, relais absent ou données incomplètes.

**Ce que le trader doit comprendre** : la machine voit partiellement ; la lecture doit être utilisée comme perception dégradée.

**PowerFlow ne doit pas conclure** : ne pas masquer l'incertitude sous un état propre.

**Phrase cockpit** : `GBPUSD | READING_PARTIAL | M1 missing / packets stale | no full film`

### UNKNOWN

**Définition terrain** : aucun film_state propre n'est déductible avec les données actuelles.

**Ce que le trader doit comprendre** : l'absence de certitude est explicitée.

**PowerFlow ne doit pas conclure** : ne pas choisir un état par défaut pour remplir l'écran.

**Phrase cockpit** : `GBPUSD | UNKNOWN | insufficient evidence for film state`

## 4. Définition de `last_structural_event`

### RELEASE_UP_VALIDATED

**Définition** : libération haussière validée par combinaison comportementale et acceptation prix.

**Conditions observables** : B3+B4+P1 actif, prix accepte plus haut, pullback absorbé ou relais B7 visible.

**Effet sur futurs packets** : `PAIR_DOWN` devient par défaut `POST_RELEASE_PULLBACK` jusqu'à invalidation.

**Erreur à éviter** : valider une release UP avec B3+B2 seul.

### RELEASE_DOWN_VALIDATED

**Définition** : libération baissière validée par pression, acceptation sous zone et relais suffisant.

**Conditions observables** : rupture ou acceptation sous zone, lower lock, propagation LTF->MTF ou maintien prix.

**Effet sur futurs packets** : `PAIR_UP` devient par défaut `COUNTER_BREATH` ou `REINTEGRATION_ATTEMPT`.

**Erreur à éviter** : ignorer le lower lock et lire chaque UP comme reversal.

### COUNTER_BREATH_REJECTED

**Définition** : mouvement inverse post-release échoue et se fait rejeter par le prix ou la zone.

**Conditions observables** : poussée inverse, absence d'acceptation, rejet, retour vers zone structurelle précédente.

**Effet sur futurs packets** : alimente `SECOND_LEG` dans la direction structurelle précédente.

**Erreur à éviter** : considérer le counter-breath comme nouvelle release.

### HIGH_ZONE_REJECTION

**Définition** : extension haute refusée par le prix.

**Conditions observables** : high non accepté, clôtures faibles après test, texture exhaustion/rejection.

**Effet sur futurs packets** : `PAIR_DOWN` devient `POST_HIGH_UNWIND` par défaut.

**Erreur à éviter** : lire le DOWN comme signal isolé sans mémoire de high rejeté.

### LOWER_LOCK_CONFIRMED

**Définition** : zone basse verrouillée après acceptation inférieure.

**Conditions observables** : lower low, maintien sous ancien support de zone, retest échoué ou acceptation below.

**Effet sur futurs packets** : UP = counter-breath / reintegration attempt ; DOWN = retest / second leg selon prix.

**Erreur à éviter** : supprimer la mémoire de lock dès le premier bounce.

### SECOND_LEG_UP

**Définition** : deuxième jambe haussière après release, pullback absorbé ou rebuild.

**Conditions observables** : release UP antérieure, pullback non invalidant, nouvelle acceptation plus haute.

**Effet sur futurs packets** : UP tardif proche high peut devenir `RELEASE_CONSUMED` ou `EXHAUSTION`.

**Erreur à éviter** : confondre second leg et première release.

### SECOND_LEG_DOWN

**Définition** : deuxième jambe baissière après release down ou counter-breath rejeté.

**Conditions observables** : lower lock, counter-breath rejeté, nouveau test bas ou lower low.

**Effet sur futurs packets** : UP suivant = `POST_LOW_REACTION` ou `LATE_THIN_BOUNCE` selon data/session.

**Erreur à éviter** : traiter le second leg comme simple `PAIR_DOWN`.

### PULLBACK_ABSORBED

**Définition** : respiration inverse contenue sans invalidation de la release précédente.

**Conditions observables** : pullback limité, prix réaccepte dans la direction de la release, compression ou tension se recharge.

**Effet sur futurs packets** : favorise `SECOND_LEG` ou continuation si propagation revient.

**Erreur à éviter** : appeler le pullback une release inverse.

### FAILED_REINTEGRATION

**Définition** : tentative de retour dans une zone échoue après rupture ou lock.

**Conditions observables** : prix tente de réintégrer, échoue, clôture à nouveau hors zone.

**Effet sur futurs packets** : renforce le scénario de continuation ou second leg dans le sens du lock.

**Erreur à éviter** : valider réintégration sur simple mèche ou micro-push.

### FALSE_BIRTH

**Définition** : signal de naissance détecté par activité ou détachement mais non confirmé par prix, zone ou relais.

**Conditions observables** : B3+B2 actif, absence d'acceptation prix, relais manquant, retour rapide dans range.

**Effet sur futurs packets** : abaisse la confiance structurelle de signaux similaires proches dans le temps.

**Erreur à éviter** : censurer l'alerte ; elle doit être qualifiée, pas supprimée.

### EXHAUSTION

**Définition** : mouvement mature ou consommé, souvent proche zone extrême, avec faible continuation utile.

**Conditions observables** : extension tardive, high/low zone, texture late/exhaustion, propagation qui se dégrade.

**Effet sur futurs packets** : packets dans même direction = `RELEASE_CONSUMED` ou `LATE_THIN_BOUNCE` selon sens.

**Erreur à éviter** : appeler toute force tardive une release fraîche.

### UNKNOWN

**Définition** : aucun événement structurel fiable n'est identifié.

**Conditions observables** : données insuffisantes, signaux contradictoires, absence de prix exploitable.

**Effet sur futurs packets** : requalification prudente analytiquement : `HONEST_UNKNOWN`, `READING_PARTIAL`.

**Erreur à éviter** : inventer un dernier événement pour éviter le vide.

## 5. Définition de `current_move_role`

### RELEASE_CANDIDATE

**Signification terrain** : conditions de release partiellement visibles, mais validation incomplète.

**Statut trader** : attention réveillée, pas conclusion de release.

**Confirmation prix** : acceptation au-dessus/sous la zone dans le sens du mouvement.

**Invalidation prix** : retour dans range, rejet de zone, absence de continuation après event stack.

### RELEASE_VALIDATED

**Signification terrain** : release acceptée par prix, zone et relais minimal.

**Statut trader** : événement structurel reconnu.

**Confirmation prix** : closes acceptées dans le sens de la release ou pullback absorbé.

**Invalidation prix** : réintégration nette de la zone rompue ou rejet complet.

### RELEASE_CONSUMED

**Signification terrain** : release vraie mais déjà mature, extension tardive ou énergie consommée.

**Statut trader** : ne pas lire comme naissance fraîche.

**Confirmation prix** : incapacité à accepter plus loin malgré nouveaux packets directionnels.

**Invalidation prix** : nouvelle acceptation propre et propagation renouvelée.

### PRESSURE_PENDING

**Signification terrain** : pression détectée mais pas encore tranchée par le prix.

**Statut trader** : surveillance active.

**Confirmation prix** : cassure/acceptation de zone ou propagation.

**Invalidation prix** : absorption inverse ou retour au milieu de range.

### LOCAL_PRESSURE_VALID

**Signification terrain** : pression valide localement mais sans preuve de structure supérieure.

**Statut trader** : information tactique, pas film complet.

**Confirmation prix** : maintien local ou micro-acceptation.

**Invalidation prix** : disparition rapide ou absence de relais.

### COUNTER_BREATH

**Signification terrain** : respiration inverse après événement structurel opposé.

**Statut trader** : réaction à qualifier, pas reversal par défaut.

**Confirmation prix** : acceptation au-delà de la zone de réintégration.

**Invalidation prix** : rejet et reprise dans le sens structurel précédent.

### COUNTER_BREATH_REJECTED

**Signification terrain** : respiration inverse échouée.

**Statut trader** : carburant possible du second leg.

**Confirmation prix** : rejet clair, retour vers lock/high-low précédent.

**Invalidation prix** : acceptation inverse après second test.

### POST_RELEASE_PULLBACK

**Signification terrain** : respiration contre une release validée.

**Statut trader** : ne pas confondre avec release opposée.

**Confirmation prix** : pullback contenu sans cassure de la zone clé.

**Invalidation prix** : rupture de la zone d'origine ou failed continuation.

### PULLBACK_ABSORBED

**Signification terrain** : pullback digéré ; le flux reprend dans le sens initial.

**Statut trader** : structure précédente encore vivante.

**Confirmation prix** : reprise et acceptation dans le sens initial.

**Invalidation prix** : nouveau rejet ou retour sous/au-dessus de la zone absorbée.

### SECOND_LEG

**Signification terrain** : mouvement de continuation après release + pullback/counter-breath rejeté.

**Statut trader** : lecture de continuité structurelle.

**Confirmation prix** : nouveau high/low accepté ou retest réussi.

**Invalidation prix** : échec à dépasser la zone précédente, rejection texture.

### SECOND_LOW_TEST

**Signification terrain** : retest du bas après lower lock ou release down.

**Statut trader** : test de maintien de la pression basse.

**Confirmation prix** : lower low ou acceptation basse.

**Invalidation prix** : réaction post-low acceptée au-dessus de la zone.

### POST_LOW_REACTION

**Signification terrain** : réaction après test bas, souvent UP mais pas release par défaut.

**Statut trader** : réaction à observer.

**Confirmation prix** : acceptation au-dessus de zone basse.

**Invalidation prix** : retour sous low ou rejet du bounce.

### LATE_THIN_BOUNCE

**Signification terrain** : bounce tardif, souvent faible en data, session ou propagation.

**Statut trader** : information de réaction, qualité limitée.

**Confirmation prix** : acceptation durable malgré contexte tardif.

**Invalidation prix** : rejet rapide ou packets stale.

### REINTEGRATION_ATTEMPT

**Signification terrain** : tentative de retour dans une zone après rupture/lock.

**Statut trader** : tentative, pas acceptation.

**Confirmation prix** : closes acceptées dans la zone ou au-delà.

**Invalidation prix** : rejet à la borne de réintégration.

### FAILED_REINTEGRATION

**Signification terrain** : tentative de réintégration refusée.

**Statut trader** : structure de rupture/lock renforcée.

**Confirmation prix** : rejet + retour hors zone.

**Invalidation prix** : deuxième tentative acceptée.

### EXHAUSTION

**Signification terrain** : mouvement avancé, dégradé ou consommé.

**Statut trader** : éviter lecture birth/release fraîche.

**Confirmation prix** : incapacité à accepter extension, rejet, propagation en dégradation.

**Invalidation prix** : nouveau relais propre et acceptation de continuation.

### POST_HIGH_UNWIND

**Signification terrain** : relâchement après high rejeté ou extension consommée.

**Statut trader** : DOWN requalifié par le film.

**Confirmation prix** : closes faibles après rejet high.

**Invalidation prix** : réacceptation au-dessus high/zone.

### UNKNOWN

**Signification terrain** : rôle non déductible.

**Statut trader** : incertitude explicite.

**Confirmation prix** : non applicable tant que rôle absent.

**Invalidation prix** : non applicable ; exiger meilleure donnée.

## 6. Zones actives

### Champs zone

- `current_zone` : libellé humain de zone active, exemple `LOWER_ZONE_1.3504_1.3532` ou `UNKNOWN`.
- `current_zone_low` : borne basse numérique si disponible.
- `current_zone_high` : borne haute numérique si disponible.
- `current_zone_status` : enum normalisé.

### Statuts de zone

| Statut | Définition |
|---|---|
| `LOWER_RANGE_ACTIVE` | Zone basse active, prix encore dans le travail de bas de range |
| `HIGH_RANGE_ACTIVE` | Zone haute active, extension/rejet/digestion autour du haut |
| `ACCEPTANCE_ABOVE_ZONE` | Prix accepte au-dessus de la zone surveillée |
| `ACCEPTANCE_BELOW_ZONE` | Prix accepte sous la zone surveillée |
| `REJECTION_HIGH` | Refus de zone haute ou extension supérieure |
| `REJECTION_LOW` | Refus de zone basse ou échec à accepter plus bas |
| `RANGE_MID_NOISE` | Mouvement au milieu du range, peu structurant |
| `UNKNOWN` | Zone non déterminée ou bornes indisponibles |

## 7. Grammaire de phrase cockpit

### Ligne courte dashboard

Format :

```text
{symbol} | {film_state} | {current_move_role} | {raw_bias}->{qualified_bias} | {price_confirmation} | {data_visibility}
```

Exemple :

```text
GBPUSD | LOWER_ZONE_ACTIVE | POST_LOW_REACTION | PAIR_UP->POST_LOW_COUNTER_BREATH | PRICE_PENDING | DATA_PARTIAL
```

### Packet humain texte

Format :

```text
{symbol}: film={film_state}. Last={last_structural_event}/{last_structural_direction}. Zone={current_zone_status} {current_zone}. Move={current_move_role}. Bias={raw_bias}->{qualified_bias}. Price={price_confirmation}. Propagation={propagation_state}. Texture={detachment_texture}. Data={data_visibility}. Watch={watch_condition}. Invalid={invalidation_condition}. Risks={technical_risks}.
```

### Packet JSON

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
  "watch_condition": "acceptance above 1.3532 or rejection back into lower zone",
  "invalidation_condition": "lower low below 1.3504",
  "technical_risks": ["M1_MISSING", "PACKETS_STALE"]
}
```

### Alerte future Telegram dormante

Format dormant seulement. Ne pas activer Telegram en V7.6.

```text
PF V7.6 | {symbol}
FILM: {film_state}
MOVE: {current_move_role}
BIAS: {raw_bias}->{qualified_bias}
PRICE: {price_confirmation}
DATA: {data_visibility}
WATCH: {watch_condition}
INVALID: {invalidation_condition}
```

## 8. Règles de non-surinterprétation

1. `B3+B2 = EVENT_STACK`, pas naissance validée.
2. `B3+B4+P1 = RELEASE_CANDIDATE`, pas `RELEASE_VALIDATED`.
3. Aucun événement isolé ne valide une release.
4. La data dégradée doit apparaître en haut de lecture.
5. `raw_bias` est conservé mais jamais dominant.
6. `UNKNOWN` vaut mieux qu'une fausse certitude.
7. `READING_PARTIAL` doit être produit quand le microfilm ou les packets sont insuffisants.
8. Le prix tranche : un packet invalidé par le prix doit être reclassé.
9. Le dernier événement structurel domine la lecture suivante tant qu'il n'est pas invalidé ou consommé.
10. Une alerte précoce doit être qualifiée, pas censurée.

## 9. Mapping trader

| Champ | Sert au trader à | Affichage | Ne doit pas déclencher |
|---|---|---|---|
| `film_state` | comprendre le contexte | première ligne | ordre directionnel |
| `last_structural_event` | garder la mémoire du film | première ou seconde ligne | prédiction mécanique |
| `last_structural_direction` | comprendre l'inertie structurelle | compact avec last event | buy/sell |
| `current_zone` | situer le prix | cockpit détail | niveau d'entrée |
| `current_zone_status` | savoir si zone accepte/rejette | ligne courte | décision automatique |
| `current_move_role` | lire le rôle du mouvement | champ central | signal autonome |
| `raw_bias` | conserver trace moteur | après rôle qualifié | message principal seul |
| `qualified_bias` | comprendre le bias requalifié | champ central | ordre |
| `packet_quality` | estimer fraîcheur/qualité | badge qualité | filtre moral |
| `price_confirmation` | voir confirmation/invalidation | badge prix | exécution |
| `propagation_state` | voir relais multi-TF | badge propagation | certitude forcée |
| `detachment_texture` | lire texture du mouvement | détail packet | score abstrait |
| `data_visibility` | voir limites de lecture | haut de cockpit si dégradé | masquage |
| `watch_condition` | savoir quoi observer | phrase courte | ordre de trade |
| `invalidation_condition` | savoir ce qui casse la lecture | phrase courte | stop/target |
| `technical_risks` | connaître les risques analytiques | liste compacte | avertissement financier |

## 10. Acceptance Criteria

- Zéro message principal ne doit être constitué seulement de `PAIR_UP` ou `PAIR_DOWN`.
- 100% des packets terrain ont `data_visibility`.
- 100% des packets terrain ont `price_confirmation`.
- `UNKNOWN`, `HONEST_UNKNOWN` et `READING_PARTIAL` sont disponibles et autorisés.
- Compatible `terrain_packet_v76_0`.
- `raw_bias` existe mais ne domine jamais la phrase cockpit.
- Les packets dégradés affichent la dégradation en haut.
- La grammaire ne crée pas de buy/sell/entry/exit/target/stop.
- La grammaire ne crée pas de nouveau score abstrait.
- La grammaire est intégrable sans refonte dashboard ni Telegram.
