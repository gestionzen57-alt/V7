# DELTARIVER → POWERFLOW B9 MAPPING — V2.1

**Projet :** PowerFlow V7.6.7 / T009 Battlefield Flux / B9 Microfilm Battlefield Memory  
**Version :** V2.1  
**Date :** 2026-05-16  
**Statut :** Livrable documentaire prêt pour architecte  
**Nature :** Transposition conceptuelle DeltaRiver → PowerFlow B9, sans copie de logique propriétaire, sans signal BUY/SELL, sans modification moteur.

---

## 0. Résumé exécutif

La V2.1 consolide les six transcriptions complètes DeltaRiver fournies par l'utilisateur et les transpose en langage PowerFlow B9.

La conclusion centrale est simple :

```text
DeltaRiver ne donne pas seulement des clusters.
DeltaRiver impose une philosophie de lecture :
prix d'abord, contexte ensuite, volume/delta comme preuves,
retest comme juge, rôle du signal selon la scène.
```

Pour PowerFlow, cela donne :

```text
B9 ne doit pas détecter plus d'events.
B9 doit transformer les events en moments lisibles.
```

Le cap B9 reste :

```text
tick → bucket → event → moment → zone mémoire → scène
```

B9 lit :

- où le flux pousse ;
- où il est absorbé ;
- où il respire ;
- où il s'essouffle ;
- où il piège ;
- où il accepte ;
- où il refuse ;
- où le centre de gravité migre.

---

## 1. Sources intégrées

### Sources PowerFlow

- `T009_B9_HANDOFF_WORKSPACES_20260516.md`
- Doctrine PowerFlow V7.6.7 / trader souverain
- Architecture T009 actuelle : Battlefield Flux, M1 proxy, tick archive cible

### Sources DeltaRiver fournies par l'utilisateur

- Webinar 1 — Patterns of price movement in the DeltaRiver terminal
- Webinar 2 — Cluster analysis in the DeltaRiver terminal
- Webinar 3 — Price Action in DeltaRiver
- Webinar 4 — Configuring the DeltaRiver terminal for medium term trading
- Webinar 5 — Analysis logic in the DeltaRiver terminal
- Webinar 6 — Surfing the waves of price movement and indicators

### Méthode de transposition

Chaque concept est classé selon :

```text
fait transcript → interprétation microstructure → transposition PowerFlow → marker B9/T009 → raw tick ou proxy M1
```

---

## 2. Philosophie DeltaRiver traduite pour PowerFlow

### 2.1 Le prix est la rivière

DeltaRiver part toujours du prix. Les clusters ne remplacent pas le prix ; ils l'expliquent.

PowerFlow doit garder la même hiérarchie :

```text
prix = trace visible
volume = effort / fuel / brake
delta = déséquilibre relatif
cluster = empreinte locale
profil = mémoire de zone
mèche = tentative / rejet / absorption
retest = vérité de la zone
```

### 2.2 Ne pas lire un signal, lire une situation

Phrase directrice :

```text
Ne lis pas un signal.
Lis une situation de marché.
```

La situation se compose de :

```text
1. D'où vient le prix ?
2. Quelle zone mémoire touche-t-il ?
3. Quel effort apparaît ?
4. Quel résultat produit cet effort ?
5. Le centre migre-t-il ?
6. La zone accepte-t-elle ou rejette-t-elle ?
7. Le retest confirme-t-il ou piège-t-il ?
8. Le mouvement progresse-t-il ou s'essouffle-t-il ?
```

### 2.3 Le cluster est une preuve, pas un ordre

Un cluster seul peut être du bruit, surtout sur petit timeframe et selon la qualité du broker.

```text
cluster seul = bruit possible
cluster + niveau = preuve
cluster + niveau + réaction prix = moment
cluster + niveau + réaction + retest = scène
```

### 2.4 Le volume est fuel ou brake

Un gros volume n'est pas directionnel par nature.

```text
volume haut + déplacement haut = fuel / impulsion
volume haut + déplacement faible = brake / absorption
volume haut + mèche + retour = rejet / piège possible
volume haut + centre qui migre = absorption qui avance
```

### 2.5 Effort → résultat → progrès

C'est la clé B9.

```text
effort = volume / delta / activité
résultat = mouvement réel du prix
progrès = update d'extrême ou cassure utile
```

Lecture :

```text
forte pression + pas de déplacement = absorption / barrière
forte pression + déplacement sans extrême = correction / réaction
forte pression + déplacement + extrême = vague progressive
```

### 2.6 Les niveaux sont des mémoires

POC, VAH, VAL, accumulation, cluster frais, retest : tout cela devient une mémoire de zone.

PowerFlow doit traduire :

```text
POC → zone_center
VAH → zone_high
VAL → zone_low
fresh volume → mémoire non retestée
retest → interrogation de la mémoire
break + retest → validation ou piège
```

---

## 3. Modèle B9 cible

### 3.1 Entités

```text
Bucket   = tranche temps/prix issue des ticks ou pseudo-ticks
Event    = preuve brute locale
Moment   = event contextualisé par zone + réaction + structure
Scene    = suite cohérente de moments
Memory   = zone ayant laissé une conséquence ou un comportement répété
```

### 3.2 Champs minimaux pour un moment B9

```json
{
  "moment_type": "T009_MOMENT_*",
  "time_start": "...",
  "time_end": "...",
  "symbol": "GBPUSD",
  "zone_low": 0.0,
  "zone_high": 0.0,
  "zone_center": 0.0,
  "event_count": 0,
  "dominant_event_type": "...",
  "avg_dwell_score": 0.0,
  "avg_failed_displacement_score": 0.0,
  "avg_compression_score": 0.0,
  "avg_pressure_score": 0.0,
  "migration_direction": "UP | DOWN | STABLE | UNKNOWN",
  "source_mode": "ONTICK_RAW | HISTORICAL_RAW | TIMER_1S_SAMPLE | M1_BAR_PROXY",
  "data_visibility": "RAW | RECONSTRUCTED | PARTIAL",
  "confidence_cap": 0.0,
  "reading": "phrase trader courte",
  "outcome": "accepted | rejected | pending | failed | consumed | unknown",
  "limitations": ["..."]
}
```

### 3.3 Gate event → moment

Un event devient moment seulement si au moins deux dimensions contextuelles sont présentes :

```text
zone / niveau
réaction prix
migration centre
retest
structure préservée ou cassée
projection / momentum
pression ou delta
qualité source suffisante
```

---

## 4. Concepts DeltaRiver → PowerFlow B9

### 4.1 Cluster

**Description :** activité sur une unité de temps et un niveau de prix.  
**Mesure :** volume/tick activity par price bucket.  
**Preuve observable :** cluster dense, distribution intra-bar, niveau local.  
**Équivalent PowerFlow :** bucket d'activité locale.  
**Marker B9 :** `B9_CLUSTER_EVIDENCE`, `B9_LOCAL_CLUSTER_LEVEL`.  
**Raw tick :** oui pour lecture précise.  
**M1 proxy :** partiel via high/low/close, tick_volume, dwell.  
**Risque :** faux détail si broker tick quality faible.

### 4.2 Delta

**Description :** différence relative achats/ventes de marché, broker-relative sur Forex.  
**Mesure :** buy activity - sell activity.  
**Preuve observable :** delta positif/négatif, delta vertical, delta horizontal.  
**Équivalent PowerFlow :** pression relative locale.  
**Marker B9 :** `B9_DELTA_PRESSURE_RELATIVE`, `B9_VERTICAL_DELTA_FUEL`.  
**Raw tick :** oui.  
**M1 proxy :** non ou très partiel.  
**Risque :** feed broker, volume non centralisé, delta synthétique.

### 4.3 Effort / résultat / progrès

**Description :** le volume doit produire un résultat ; le progrès est une mise à jour d'extrême ou de zone clé.  
**Mesure :** effort vs déplacement vs extrême update.  
**Preuve observable :** volume fort avec ou sans déplacement.  
**Équivalent PowerFlow :** test de rôle du volume.  
**Marker B9 :** `B9_EFFORT_RESULT_PROGRESS`.  
**T009 moment :** `T009_MOMENT_EFFORT_WITHOUT_RESULT`, `T009_MOMENT_PROGRESSIVE_WAVE`, `T009_MOMENT_CORRECTIVE_WAVE`.  
**Raw tick :** idéal.  
**M1 proxy :** oui partiel.  
**Risque :** confondre réaction et progrès.

### 4.4 Absorption / barrière limite inférée

**Description :** achats marché sans progression haussière ou ventes marché sans progression baissière.  
**Mesure :** pression forte + failed displacement + dwell.  
**Preuve observable :** delta fort dans un sens, clôture sans progrès.  
**Équivalent PowerFlow :** absorption / mur / push against wall.  
**Marker B9 :** `B9_MARKET_BUY_ABSORBED_BY_LIMIT_SELL`, `B9_MARKET_SELL_ABSORBED_BY_LIMIT_BUY`, `B9_PUSH_AGAINST_WALL`.  
**T009 moment :** `T009_MOMENT_IMBALANCE_ABSORBED`, `T009_MOMENT_ABSORPTION_SHELF`.  
**Raw tick :** oui pour confiance forte.  
**M1 proxy :** partiel via failed displacement + close position.  
**Risque :** limite inférée, non observée directement.

### 4.5 Braking bar / pushing bar

**Description :** distribution du volume dans la bougie qualifie propulsion ou freinage.  
**Mesure :** localisation du volume max : ouverture, clôture, mèche.  
**Preuve observable :** volume en mèche / près clôture / près ouverture.  
**Équivalent PowerFlow :** impulse vs brake.  
**Marker B9 :** `B9_PUSHING_BAR`, `B9_BRAKING_BAR`, `B9_TAIL_CLUSTER_AMPLIFIER`.  
**T009 moment :** `T009_MOMENT_IMBALANCE_PUSH`, `T009_MOMENT_FLOW_BRAKE`.  
**Raw tick :** oui.  
**M1 proxy :** partiel via OHLC + wick ratio.  
**Risque :** pattern isolé hors contexte.

### 4.6 POC / VAH / VAL

**Description :** profil local d'une accumulation ; POC centre, VAH borne haute, VAL borne basse.  
**Mesure :** distribution horizontale d'activité.  
**Preuve observable :** zone d'accumulation + réaction.  
**Équivalent PowerFlow :** zone mémoire.  
**Marker B9 :** `B9_LOCAL_POC_PROXY`, `B9_VALUE_AREA_PROXY`, `B9_VOLUME_MEMORY_ZONE`.  
**T009 moment :** `T009_MOMENT_RETURN_TO_POC`, `T009_MOMENT_VALUE_AREA_BREAK`, `T009_MOMENT_VALUE_AREA_REINTEGRATION`.  
**Raw tick :** oui pour vrai profil.  
**M1 proxy :** partiel par densité bucket.  
**Risque :** zone trop grossière en M1.

### 4.7 Breakout / retest / trap

**Description :** un break n'est pas jugé au break, mais au retest.  
**Mesure :** sortie de zone, retour, acceptation ou réintégration.  
**Preuve observable :** break + retest tenu ou échoué.  
**Équivalent PowerFlow :** acceptation / rejet / trap.  
**Marker B9 :** `B9_BREAKOUT_PENDING_RETEST`, `B9_TRUE_BREAK_AFTER_RETEST`, `B9_FALSE_BREAK_REINTEGRATION`.  
**T009 moment :** `T009_MOMENT_BREAK_RETEST`, `T009_MOMENT_BREAK_RETEST_FAILED`, `T009_MOMENT_TRAP_CANDIDATE`.  
**Raw tick :** non obligatoire.  
**M1 proxy :** oui.  
**Risque :** retest trop rapide pour M1 proxy.

### 4.8 Retest causal / acteurs piégés

**Description :** le retest peut venir de sorties à breakeven, profit taking, ou participants coincés.  
**Mesure :** retour vers zone + delta inverse + activité de sortie.  
**Preuve observable :** retour vers volume, delta qui change, pression opposée.  
**Équivalent PowerFlow :** retest causé par flux piégé.  
**Marker B9 :** `B9_TRAPPED_PARTICIPANTS_RETEST`, `B9_BREAKEVEN_EXIT_FLOW`, `B9_PROFIT_TAKING_RETEST`.  
**T009 moment :** `T009_MOMENT_RETEST_BY_TRAPPED_FLOW`.  
**Raw tick :** oui pour lecture forte.  
**M1 proxy :** partiel.  
**Risque :** causalité inférée.

### 4.9 Price action comme force / faiblesse

**Description :** price action n'est pas figure de chandelier ; c'est grammaire de force/faiblesse.  
**Mesure :** angle, projection, mèche, extrême update, structure break.  
**Preuve observable :** pente qui s'adoucit, projection qui diminue, mèche opposée.  
**Équivalent PowerFlow :** cinématique locale.  
**Marker B9 :** `B9_PRICE_ACTION_AS_MOVEMENT_READING`, `B9_FORCE_WEAKNESS_GRAMMAR`.  
**T009 moment :** `T009_MOMENT_MOMENTUM_DECAY`, `T009_MOMENT_PROJECTION_DECAY`, `T009_MOMENT_SHADOW_WEAKNESS`.  
**Raw tick :** non.  
**M1 proxy :** oui.  
**Risque :** mauvais découpage de vague.

### 4.10 Squelette du mouvement

**Description :** retirer le bruit visuel pour lire direction, bornes, momentum.  
**Mesure :** extrêmes, close path, range, slope.  
**Preuve observable :** centre monte/descend, structure claire.  
**Équivalent PowerFlow :** scene spine.  
**Marker B9 :** `B9_MOVEMENT_SKELETON`, `B9_SCENE_SPINE`, `B9_NOISE_REDUCED_EXTREMES`.  
**Raw tick :** non.  
**M1 proxy :** oui.  
**Risque :** simplification excessive.

### 4.11 Delta dominance / fenêtre visible

**Description :** DeltaRiver normalise parfois par la zone visible ; les couleurs changent au zoom.  
**Mesure :** dominance locale relative.  
**Preuve observable :** recalcul des dominances selon fenêtre.  
**Équivalent PowerFlow :** score scope explicite.  
**Marker B9 :** `B9_VISIBLE_WINDOW_RELATIVITY`, `B9_LOCAL_NORMALIZATION_WINDOW`.  
**Raw tick :** non.  
**M1 proxy :** oui si score_scope exposé.  
**Risque :** scores non comparables entre fenêtres.

### 4.12 Waves / progressive vs corrective

**Description :** vague = mouvement d'un extrême vers un autre ; son rôle dépend du progrès.  
**Mesure :** volume, delta, amplitude, extrême update.  
**Preuve observable :** mouvement avec ou sans progrès.  
**Équivalent PowerFlow :** classification de vague.  
**Marker B9 :** `B9_PROGRESSIVE_WAVE`, `B9_CORRECTIVE_WAVE`.  
**T009 moment :** `T009_MOMENT_PROGRESSIVE_WAVE`, `T009_MOMENT_CORRECTIVE_WAVE`.  
**Raw tick :** non obligatoire.  
**M1 proxy :** oui.  
**Risque :** mauvais seuil de vague.

### 4.13 Range / sideways par touches

**Description :** un latéral se valide par bornes et touches répétées.  
**Mesure :** range high/low + touch_count.  
**Preuve observable :** trois touches / réaction aux bornes.  
**Équivalent PowerFlow :** battle range.  
**Marker B9 :** `B9_SIDEWAYS_RANGE_BY_TOUCHES`, `B9_THREE_TOUCH_BATTLE_RANGE`.  
**T009 moment :** `T009_MOMENT_RANGE_ESTABLISHED`, `T009_MOMENT_RANGE_BOUNDARY_REACTION`.  
**Raw tick :** non.  
**M1 proxy :** oui.  
**Risque :** range trop court.

### 4.14 Ombre / wick > 50 %

**Description :** mèche large sur retracement ou zone = zone à inspecter au microscope.  
**Mesure :** wick_ratio.  
**Preuve observable :** mèche > 0.5 du range + réaction.  
**Équivalent PowerFlow :** rejet / absorption candidate.  
**Marker B9 :** `B9_WICK_OVER_50_MICROSCOPE`.  
**T009 moment :** `T009_MOMENT_WICK_OVER_50_REJECTION`.  
**Raw tick :** idéal pour savoir ce qu'il y a dans la mèche.  
**M1 proxy :** oui partiel.  
**Risque :** mèche news / spread.

---

## 5. Nouveaux markers B9 V2.1

```text
B9_PRICE_ACTION_AS_MOVEMENT_READING
B9_FORCE_WEAKNESS_GRAMMAR
B9_MARKET_ACTIVITY_CAUSES_PRICE
B9_VOLUME_AS_FUEL
B9_VOLUME_AS_BRAKE
B9_EFFORT_RESULT_PROGRESS
B9_EFFORT_WITHOUT_RESULT
B9_PROGRESSIVE_WAVE
B9_CORRECTIVE_WAVE
B9_MOVEMENT_SKELETON
B9_SCENE_SPINE
B9_VOLUME_MEMORY_ZONE
B9_FRESH_VOLUME_LEVEL
B9_LOCAL_POC_PROXY
B9_VALUE_AREA_PROXY
B9_BREAKOUT_PENDING_RETEST
B9_TRUE_BREAK_AFTER_RETEST
B9_FALSE_BREAK_REINTEGRATION
B9_TRAPPED_PARTICIPANTS_RETEST
B9_LIMIT_BARRIER_INFERRED
B9_PUSH_AGAINST_WALL
B9_MARKET_BUY_ABSORBED_BY_LIMIT_SELL
B9_MARKET_SELL_ABSORBED_BY_LIMIT_BUY
B9_DELTA_WAVE_ALIGNMENT
B9_DELTA_WAVE_WEAKENING
B9_SIDEWAYS_RANGE_BY_TOUCHES
B9_NESTED_TIMEFRAME_MICROSCOPE
B9_CONTEXT_OVERRIDES_LOCAL_PATTERN
B9_CLUSTER_CONFIDENCE_BY_SOURCE
B9_LOCAL_NORMALIZATION_WINDOW
```

---

## 6. Nouveaux `T009_MOMENT_*` proposés

```text
T009_MOMENT_EFFORT_WITHOUT_RESULT
T009_MOMENT_VOLUME_WITH_MOVEMENT_NO_PROGRESS
T009_MOMENT_PROGRESSIVE_WAVE
T009_MOMENT_CORRECTIVE_WAVE
T009_MOMENT_VOLUME_TO_VOLUME_TRANSITION
T009_MOMENT_FRESH_VOLUME_REACTION
T009_MOMENT_BREAKOUT_PENDING_RETEST
T009_MOMENT_BREAK_RETEST
T009_MOMENT_BREAK_RETEST_FAILED
T009_MOMENT_RETEST_BY_TRAPPED_FLOW
T009_MOMENT_ABSORPTION_LEVEL_BORN
T009_MOMENT_FIRST_TEST_OF_ABSORPTION_LEVEL
T009_MOMENT_VOLUME_BACKED_STRUCTURE_BREAK
T009_MOMENT_RETRACE_DECISION_AREA
T009_MOMENT_DELTA_WAVE_WEAKENING
T009_MOMENT_PROJECTION_DECAY
T009_MOMENT_MOMENTUM_DECAY
T009_MOMENT_SHADOW_WEAKNESS
T009_MOMENT_WICK_OVER_50_REJECTION
T009_MOMENT_RANGE_ESTABLISHED
T009_MOMENT_RANGE_BOUNDARY_REACTION
T009_MOMENT_LOCAL_BRAKE_FAILED
T009_MOMENT_AVOIDED_CLUSTER_REACTION
T009_MOMENT_DOJI_VOLUME_STOP
T009_MOMENT_STOP_BEFORE_REVERSAL
T009_MOMENT_NEGATIVE_TAIL_BOUGHT_BACK
```

---

## 7. Raw tick vs M1 proxy

| Lecture | Raw tick | M1_BAR_PROXY |
|---|---:|---:|
| Cluster exact par prix | oui | non |
| Delta réel buy/sell | oui | non / très partiel |
| Delta dans les mèches | oui | non / proxy faible |
| POC / VAH / VAL exacts | oui | partiel par bucket |
| Squelette du mouvement | non | oui |
| Momentum / projection decay | non | oui |
| Wick ratio | non | oui |
| Break / retest | non obligatoire | oui |
| Failed displacement | non obligatoire | oui |
| Center migration | non obligatoire | oui |
| Effort/result/progress | idéalement oui | oui partiel |
| Retest causal | oui pour confiance forte | partiel |
| Imbalance efficace/absorbée | oui | partiel |
| Trap candidate | idéalement oui | oui partiel |

---

## 8. Recommandation de codage ultérieur

Ne pas coder un gros module.

Coder ensuite seulement :

```text
T009 Sequence Summarizer V0
```

But : transformer 100+ events bruts en 5 à 8 moments lisibles.

Entrées : events T009 existants + buckets + source_mode + quality.  
Sortie : `output/t009_sequence_summary.json` + surface cockpit ultérieure.

Ordre recommandé :

```text
1. taxonomy T009_MOMENT_*
2. event → moment gate
3. moment aggregation by zone/time
4. reading phrase courte
5. limitations/source quality visible
```

Pas de B8 dans cette phase. B9 apprend d'abord à raconter la scène locale.

---

## 9. Phrase de verrouillage

```text
B8 dit qui pousse contre qui.
B9 dit comment le flux laisse des traces dans le prix.
DeltaRiver donne l'angle : ne pas lire le signal, lire la situation.
PowerFlow doit transformer cette situation en moment lisible, sans jamais décider.
```
