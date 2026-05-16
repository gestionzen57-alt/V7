# DELTARIVER → POWERFLOW B9 MAPPING — V2

**Projet :** PowerFlow V7.6.7 / T009 Battlefield Flux  
**Brique cible :** B9 — Microfilm Battlefield Memory  
**Livrable repo :** `Docs/Reports/DELTARIVER_TO_POWERFLOW_B9_MAPPING.md`  
**Version :** V2 — enrichie par 6 transcriptions DeltaRiver fournies par l'utilisateur  
**Date :** 2026-05-16  
**Statut :** Rapport de transposition conceptuelle. Aucune copie de logique propriétaire. Aucun signal BUY/SELL.  

---

## 0. Résumé exécutif

La V1 posait un premier mapping à partir des sources publiques DeltaRiver et du handoff T009/B9. La V2 intègre maintenant les **six vidéos / webinaires DeltaRiver transmis sous forme de transcriptions** :

1. Webinar 1 — Patterns of price movement in the DeltaRiver terminal.
2. Webinar 2 — Cluster analysis in the DeltaRiver terminal.
3. Webinar 3 — Price Action in DeltaRiver.
4. Webinar 5 — Analysis logic in the DeltaRiver terminal.
5. Webinar 6 — Surfing the waves of price movement and indicators.
6. Webinar medium-term/template — tick history, visible-range normalization, movement skeleton, correction zones.

La conclusion V2 est plus forte que la V1 :

```text
DeltaRiver ne doit pas être copié.
DeltaRiver sert ici de matière d'observation microstructure.
PowerFlow B9 doit extraire une grammaire propre :
preuve locale → moment → scène → mémoire de zone.
```

V2 confirme que B9 doit rester indépendant de B8 au départ :

```text
B8 = qui pousse contre qui dans le champ multi-devises.
B9 = comment le flux laisse des traces locales dans le prix.
```

La transposition centrale :

```text
tick / pseudo-tick
→ bucket temporel / bucket prix
→ event brut
→ moment contextualisé
→ zone mémoire
→ scène lisible
```

V2 ajoute une doctrine clé :

```text
Un cluster isolé n'est pas un signal.
Un delta isolé n'est pas un signal.
Un volume isolé n'est pas un signal.

Ils deviennent utiles seulement lorsqu'ils racontent une scène :
niveau + effort + résultat + déplacement + mèche + clôture + retest + contexte.
```

---

## 1. Sources et statut de preuve

### 1.1 Sources PowerFlow

- `T009_B9_HANDOFF_WORKSPACES_20260516.md`
- Vérité PowerFlow actuelle :

```text
B9 — Microfilm Battlefield Memory
B9 lit le micro-film tick/pseudo-tick pour détecter :
zones mémoire, absorption, dwell, failed displacement, compression,
expansion, respiration, essoufflement, traps, imbalance efficace ou absorbée,
migration du centre de gravité.
```

T009 sait déjà produire :

```text
T009_ABSORPTION_CLUSTER
T009_BATTLE_LEVEL_BORN
T009_CLUSTER_DELTA_FLIP
T009_BATTLE_ZONE_BROKEN
dwell_score
failed_displacement_score
compression_score
pressure_score
center migration
```

### 1.2 Sources DeltaRiver publiques utilisées en V1

La V1 utilisait les éléments publics :

```text
https://deltariver.pro/eng
https://deltariver.pro/video_en/
Documentation officielle DeltaRiver quand accessible
```

Ces sources confirmaient surtout :

```text
cluster analysis
volume par prix / temps
delta achats / ventes
profil local
cumulative delta
historique tick MT5
```

### 1.3 Sources V2 : transcriptions utilisateur

La V2 utilise les transcriptions fournies par l'utilisateur dans ce fil. Elles sont traitées comme matière qualitative. Les passages sont parfois traduits automatiquement ou nettoyés ; donc le rapport sépare :

```text
FAIT TRANSCRIPT = ce qui est explicitement dit dans la transcription.
TRANSPOSITION B9 = traduction dans la grammaire PowerFlow.
HYPOTHÈSE TECHNIQUE = proposition à tester, pas vérité moteur.
```

---

## 2. Doctrine B9 issue de la V2

### 2.1 Ne pas copier DeltaRiver

PowerFlow ne doit pas reconstruire DeltaRiver. B9 doit convertir les concepts en signatures PowerFlow.

```text
DeltaRiver concept
→ preuve observable
→ équivalent PowerFlow
→ marker T009/B9
→ besoin raw tick ?
→ possible M1 proxy ?
→ risque technique
```

### 2.2 Le rôle de B9

B9 doit répondre :

```text
où le flux pousse ?
où il est absorbé ?
où il respire ?
où il s'essouffle ?
où il piège ?
où il accepte ?
où il refuse ?
où le centre de gravité migre ?
```

### 2.3 Event, moment, scène, mémoire

```text
event brut = preuve locale non contextualisée
moment = event + contexte zone + résultat prix + qualité source
scène = suite cohérente de moments
zone mémoire = zone ayant produit une conséquence structurelle
```

### 2.4 Règle effort / résultat

La V2 confirme que l'axe le plus exploitable est :

```text
effort = volume / delta / pression / densité
résultat = déplacement prix / clôture / migration du centre / renouvellement d'extrême
```

Donc :

```text
effort élevé + déplacement élevé = imbalance push / fuel
effort élevé + déplacement faible = absorption / brake / failed displacement
effort élevé + mèche + retour = rejection / trap candidate
effort décroissant + projection décroissante = exhaustion
```

---

## 3. Comparaison V1 → V2

| Zone | V1 | V2 |
|---|---|---|
| Sources | Public web + handoff T009 | Public + 6 transcriptions utilisateur |
| Niveau | Conceptuel | Conceptuel + grammaire opérationnelle |
| Delta | Delta = imbalance | Delta = imbalance, zero-cross, divergence, shadow distortion, limite absorbante |
| Volume | Cluster / profil local | Fuel vs brake, distribution, queue, POC, VAH/VAL, gros volumes derrière les turns |
| Price action | Peu développé | Force/faiblesse, momentum, projection decay, wick ratio, structure break |
| B9 moments | Liste initiale | Catalogue enrichi + event→moment gate |
| M1 proxy | Mentionné | Classé concept par concept : oui / partiel / non |
| Raw tick | Recommandé | Recommandé + justifié par MT5 history et delta/shadow/cluster exact |
| Risques | Génériques | Normalization drift, broker-relative delta, overfitting, single-bar false positive |

Verdict :

```text
V1 = bonne cartographie initiale.
V2 = base de spécification pour un Sequence Summarizer B9.
```

---

## 4. Concepts DeltaRiver → PowerFlow B9

### 4.1 Clusters

**Nom DeltaRiver :** Clusters  
**Description :** activité regroupée par niveau de prix et fenêtre temporelle.  
**Ce que cela mesure :** concentration locale d'activité.  
**Preuve observable :** volume / tick density sur une zone prix-temps.  
**Équivalent PowerFlow :** `price_bucket`, `battle_bucket`, `zone_memory_cell`.  
**Possible T009/B9 marker :**

```text
T009_CLUSTER_DWELL_ZONE
T009_BATTLE_LEVEL_BORN
T009_MOMENT_ABSORPTION_SHELF
```

**Besoin raw tick ?** Oui pour vrai cluster.  
**Possible avec M1 proxy ?** Partiel.  
**Risque d'erreur :** bucket artificiel, tick quality broker, M1 qui invente une présence intra-bar.

---

### 4.2 Delta

**Nom DeltaRiver :** Delta  
**Description :** différence achats / ventes dans le cluster ou la zone.  
**Ce que cela mesure :** déséquilibre apparent d'activité agressive.  
**Preuve observable :** delta positif / négatif, delta cumulé, delta qui traverse zéro.  
**Équivalent PowerFlow :** `signed_pressure`, `delta_imbalance`, `aggressive_flow_proxy`.  
**Possible T009/B9 marker :**

```text
T009_CLUSTER_DELTA_FLIP
T009_DELTA_PRESSURE_BURST
T009_MOMENT_IMBALANCE_PUSH
T009_MOMENT_IMBALANCE_ABSORBED
```

**Besoin raw tick ?** Oui pour robuste.  
**Possible avec M1 proxy ?** Non ou proxy très faible.  
**Risque d'erreur :** delta broker-relative, feed bias, vrai marché global non observé.

---

### 4.3 Delta sans progression prix

**Nom DeltaRiver :** delta positive / négative sans mouvement.  
**Description :** achats ou ventes agressives visibles mais sans déplacement attendu.  
**Ce que cela mesure :** absorption ou contention.  
**Preuve observable :** delta haut + déplacement faible + clôture qui ne valide pas le sens attendu.  
**Équivalent PowerFlow :** `effort_without_result`, `failed_displacement`.  
**Possible T009/B9 marker :**

```text
T009_MOMENT_IMBALANCE_ABSORBED
T009_MOMENT_ABSORPTION_SHELF
T009_MOMENT_REJECTION
```

**Besoin raw tick ?** Oui pour delta réel.  
**Possible avec M1 proxy ?** Partiel via `failed_displacement_score`, `dwell_score`, `compression_score`.  
**Risque d'erreur :** confondre manque de données et absorption.

---

### 4.4 Effort / résultat

**Nom DeltaRiver :** volume = fuel, le résultat du volume doit être mouvement.  
**Description :** l'activité doit produire une conséquence.  
**Ce que cela mesure :** efficacité ou échec de l'effort.  
**Preuve observable :** rapport effort / déplacement / clôture / extrême.  
**Équivalent PowerFlow :** `effort_result_alignment`.  
**Possible T009/B9 marker :**

```text
B9_EFFORT_RESULT_ALIGNMENT
B9_EFFORT_WITHOUT_PROGRESS
B9_FAILED_DISPLACEMENT
B9_VOLUME_AS_FUEL
B9_VOLUME_AS_BRAKE
```

**Besoin raw tick ?** Non pour une version proxy.  
**Possible avec M1 proxy ?** Oui.  
**Risque d'erreur :** seuils universels, volatilité variable, mauvaise normalisation.

---

### 4.5 Volume as fuel vs brake

**Nom DeltaRiver :** volume comme carburant ou frein.  
**Description :** le même volume peut propulser ou arrêter selon le résultat prix.  
**Ce que cela mesure :** rôle de l'effort.  
**Preuve observable :** volume élevé + déplacement élevé ou volume élevé + déplacement faible.  
**Équivalent PowerFlow :** `effort_role_classifier`.  
**Possible T009/B9 marker :**

```text
T009_MOMENT_IMBALANCE_PUSH
T009_MOMENT_FLOW_BRAKE
T009_MOMENT_IMBALANCE_ABSORBED
```

**Besoin raw tick ?** Idéalement oui.  
**Possible avec M1 proxy ?** Oui partiel.  
**Risque d'erreur :** volume apparent ≠ volume centralisé réel sur Forex.

---

### 4.6 Local Profile / POC / VAH / VAL

**Nom DeltaRiver :** profil local, Point of Control, VAH, VAL.  
**Description :** distribution locale des volumes sur zone sélectionnée.  
**Ce que cela mesure :** centre et bornes de valeur / bataille.  
**Preuve observable :** niveau de volume maximal, bornes de zone de valeur.  
**Équivalent PowerFlow :**

```text
zone_center = POC proxy
zone_high = VAH proxy
zone_low = VAL proxy
```

**Possible T009/B9 marker :**

```text
T009_BATTLE_LEVEL_BORN
T009_BATTLE_ZONE_MEMORY
T009_LOCAL_POC_PROXY
T009_VALUE_AREA_PROXY
```

**Besoin raw tick ?** Oui pour profil réel.  
**Possible avec M1 proxy ?** Partiel via densité de mid / bucket.  
**Risque d'erreur :** POC proxy trop grossier, range M1 trop large.

---

### 4.7 Braking bar / bar d'arrêt

**Nom DeltaRiver :** braking bullish / bearish bar.  
**Description :** volume maximal placé vers la clôture ou dans la mèche, sans continuation nette.  
**Ce que cela mesure :** freinage / absorption locale.  
**Preuve observable :** volume dans mèche + déplacement limité + clôture qui ne poursuit pas.  
**Équivalent PowerFlow :** `flow_brake`, `wick_absorption`.  
**Possible T009/B9 marker :**

```text
B9_BRAKING_BAR
B9_TAIL_CLUSTER_BRAKE
T009_MOMENT_FLOW_BRAKE
T009_MOMENT_ABSORPTION_SHELF
```

**Besoin raw tick ?** Oui pour confirmer cluster dans mèche.  
**Possible avec M1 proxy ?** Partiel via OHLC, wick ratio, failed displacement.  
**Risque d'erreur :** single-bar false positive.

---

### 4.8 Impulse bar

**Nom DeltaRiver :** bullish / bearish impulse bar.  
**Description :** volume placé au départ du mouvement et résultat clair dans le sens du déplacement.  
**Ce que cela mesure :** effort propulsif.  
**Preuve observable :** volume + clôture directionnelle + renouvellement d'extrême.  
**Équivalent PowerFlow :** `imbalance_push`.  
**Possible T009/B9 marker :**

```text
T009_MOMENT_IMBALANCE_PUSH
B9_BULLISH_IMPULSE_BAR
B9_BEARISH_IMPULSE_BAR
```

**Besoin raw tick ?** Idéalement oui.  
**Possible avec M1 proxy ?** Partiel.  
**Risque d'erreur :** confondre impulsion et extension tardive.

---

### 4.9 Wick / shadow volume rejection

**Nom DeltaRiver :** gros volume / delta dans ombre ou queue.  
**Description :** activité importante dans une extension rejetée.  
**Ce que cela mesure :** rejet, absorption, piège possible.  
**Preuve observable :** wick ratio élevé + volume/delta dans la mèche + retour.  
**Équivalent PowerFlow :** `wick_rejection`, `failed_extreme_probe`.  
**Possible T009/B9 marker :**

```text
B9_WICK_CLUSTER_REJECTION
B9_WICK_ABSORPTION
T009_MOMENT_REJECTION
T009_MOMENT_TRAP_CANDIDATE
```

**Besoin raw tick ?** Oui pour volume réel dans mèche.  
**Possible avec M1 proxy ?** Partiel via wick ratio et close position.  
**Risque d'erreur :** mèche news / spread spike confondue avec absorption.

---

### 4.10 Delta zero-cross

**Nom DeltaRiver :** delta traverse zéro.  
**Description :** changement de signe de l'activité dominante.  
**Ce que cela mesure :** transfert local d'initiative.  
**Preuve observable :** delta négatif → positif, ou inversement, sur niveau / zone.  
**Équivalent PowerFlow :** `initiative_shift`, `delta_flip`.  
**Possible T009/B9 marker :**

```text
T009_CLUSTER_DELTA_FLIP
B9_DELTA_ZERO_CROSS_IN_ZONE
B9_MICRO_INITIATIVE_SHIFT
```

**Besoin raw tick ?** Oui.  
**Possible avec M1 proxy ?** Non ou très faible.  
**Risque d'erreur :** broker feed, noise, zéro-cross isolé sans niveau.

---

### 4.11 Squeeze → breakout → retest → escape

**Nom DeltaRiver :** поджатие / squeeze vers niveau, breakout, retest, fuite du prix.  
**Description :** le prix se presse contre une borne, casse, teste, puis accepte ou fuit.  
**Ce que cela mesure :** compression locale puis acceptation / rejet.  
**Preuve observable :** compression + center migration vers borne + break + retest.  
**Équivalent PowerFlow :** `compression_to_level`, `acceptance_after_break`.  
**Possible T009/B9 marker :**

```text
B9_SQUEEZE_TO_LEVEL
B9_BREAK_RETEST_ESCAPE
T009_BATTLE_ZONE_BROKEN
T009_MOMENT_ACCEPTANCE
```

**Besoin raw tick ?** Non obligatoire.  
**Possible avec M1 proxy ?** Oui partiel.  
**Risque d'erreur :** break sans acceptation, retest trop rapide pour M1.

---

### 4.12 Trap / false breakout

**Nom DeltaRiver :** false breakout / shake-out / retour dans zone.  
**Description :** sortie apparente puis absence d'acceptation et réintégration.  
**Ce que cela mesure :** piège / rejet de la sortie.  
**Preuve observable :** break + imbalance apparent + retour rapide + absorption opposée.  
**Équivalent PowerFlow :** `trap_candidate`.  
**Possible T009/B9 marker :**

```text
T009_MOMENT_TRAP_CANDIDATE
B9_FALSE_BREAKOUT
B9_FAILED_ACCEPTANCE
```

**Besoin raw tick ?** Idéalement oui.  
**Possible avec M1 proxy ?** Oui partiel.  
**Risque d'erreur :** retest normal confondu avec trap.

---

### 4.13 Momentum / wave steepness / projection decay

**Nom DeltaRiver :** momentum, pente, projection, raideur de vague.  
**Description :** la force du mouvement se lit par l'angle, la projection et le renouvellement d'extrême.  
**Ce que cela mesure :** énergie cinématique.  
**Preuve observable :** vague moins raide, projection qui diminue, extrême à peine renouvelé.  
**Équivalent PowerFlow :** `projection_decay`, `wave_steepness_decay`.  
**Possible T009/B9 marker :**

```text
B9_MOMENTUM_SLOPE
B9_PROJECTION_DECAY
T009_MOMENT_FLOW_EXHAUSTION
```

**Besoin raw tick ?** Non.  
**Possible avec M1 proxy ?** Oui.  
**Risque d'erreur :** mauvais découpage des vagues.

---

### 4.14 Upper wick weakness / lower wick support

**Nom DeltaRiver :** ombres supérieures / inférieures comme force-faiblesse.  
**Description :** dans un mouvement up, ombres supérieures = vendeur local ; dans un mouvement down, ombres inférieures = acheteur local.  
**Ce que cela mesure :** présence opposée / rejet local.  
**Preuve observable :** wick ratio élevé + absence de continuation.  
**Équivalent PowerFlow :** `local_opposition_presence`.  
**Possible T009/B9 marker :**

```text
B9_UPPER_WICK_WEAKNESS
B9_LOWER_WICK_SUPPORT
T009_MOMENT_REJECTION
```

**Besoin raw tick ?** Non pour mèche ; oui pour delta dans mèche.  
**Possible avec M1 proxy ?** Oui.  
**Risque d'erreur :** spread widening / news wick.

---

### 4.15 Pushing / supportive-pushing structures

**Nom DeltaRiver :** толкающие / подталкивающие конструкции.  
**Description :** structures qui poussent directement ou soutiennent une poussée.  
**Ce que cela mesure :** initiative active ou relais de pression.  
**Preuve observable :** déplacement + delta/volume cohérent, puis micro-poussées de maintien.  
**Équivalent PowerFlow :** `pressure_relay`, `initiative_transfer`.  
**Possible T009/B9 marker :**

```text
B9_PUSHING_STRUCTURE
B9_SUPPORTIVE_PUSH_STRUCTURE
B9_PRESSURE_RELAY
T009_MOMENT_IMBALANCE_PUSH
```

**Besoin raw tick ?** Idéalement oui.  
**Possible avec M1 proxy ?** Partiel.  
**Risque d'erreur :** relais confondu avec simple respiration.

---

### 4.16 Movement skeleton

**Nom DeltaRiver :** squelette du mouvement sans bruit.  
**Description :** afficher la structure linéaire du mouvement pour voir direction, bornes, moment.  
**Ce que cela mesure :** trajectoire et charpente de scène.  
**Équivalent PowerFlow :** `scene_spine`, `movement_skeleton`.  
**Possible T009/B9 marker :**

```text
B9_MOVEMENT_SKELETON
B9_SCENE_SPINE
B9_NOISE_REDUCED_PRICE_PATH
```

**Besoin raw tick ?** Non.  
**Possible avec M1 proxy ?** Oui.  
**Risque d'erreur :** utiliser une moyenne comme vérité retardée. PowerFlow doit extraire la cinématique, pas copier l'indicateur.

---

### 4.17 Visible-window normalization

**Nom DeltaRiver :** recalcul des dominances selon zone visible.  
**Description :** les couleurs / dominances changent quand la fenêtre visible change.  
**Ce que cela mesure :** relativité locale du score.  
**Équivalent PowerFlow :** `normalization_window`.  
**Possible T009/B9 marker :**

```text
B9_VISIBLE_WINDOW_RELATIVITY
B9_LOCAL_NORMALIZATION_WINDOW
```

**Besoin raw tick ?** Non.  
**Possible avec M1 proxy ?** Oui.  
**Risque d'erreur :** comparer des scores calculés sur fenêtres différentes.

---

### 4.18 Correction depth / retrace depth

**Nom DeltaRiver :** niveaux 30 / 50 / 70, zones de correction.  
**Description :** profondeur du retracement comme stress ou invalidation de structure.  
**Ce que cela mesure :** respiration, neutralisation, réintégration.  
**Équivalent PowerFlow :** `breath_depth`, `structure_stress_level`.  
**Possible T009/B9 marker :**

```text
B9_RETRACE_DEPTH
B9_BREATH_DEPTH
B9_DIRECTION_STRESS_LEVEL
```

**Besoin raw tick ?** Non.  
**Possible avec M1 proxy ?** Oui.  
**Risque d'erreur :** ne pas copier Fibonacci/Trinity ; calibrer par comportement réel.

---

### 4.19 Symbol-specific calibration

**Nom DeltaRiver :** chaque instrument doit être observé / calibré.  
**Description :** les deltas et réactions diffèrent par paire.  
**Ce que cela mesure :** profil comportemental propre au symbole.  
**Équivalent PowerFlow :** `pair_behavior_profile`.  
**Possible T009/B9 marker :**

```text
B9_SYMBOL_SPECIFIC_CALIBRATION
B9_PAIR_BEHAVIOR_PROFILE
```

**Besoin raw tick ?** Idéalement oui.  
**Possible avec M1 proxy ?** Oui pour seuils proxy.  
**Risque d'erreur :** seuils universels, hardcoding.

---

## 5. Ce que T009 couvre déjà

T009 couvre déjà correctement la couche “résultat prix” :

```text
dwell_score
failed_displacement_score
compression_score
pressure_score
center migration
```

Correspondances :

| Brique T009 actuelle | Couverture DeltaRiver transposée | Statut |
|---|---|---|
| `T009_ABSORPTION_CLUSTER` | effort sans progrès, absorption, bar d'arrêt | déjà bon, à contextualiser |
| `T009_BATTLE_LEVEL_BORN` | cluster level, POC proxy, zone mémoire | déjà bon, manque confirmation structurelle |
| `T009_CLUSTER_DELTA_FLIP` | delta zero-cross / initiative shift | besoin raw tick pour robuste |
| `T009_BATTLE_ZONE_BROKEN` | breakout zone | déjà bon, manque retest/acceptation |
| `dwell_score` | prix qui habite une zone | déjà bon |
| `failed_displacement_score` | volume/delta sans résultat | cœur B9 |
| `compression_score` | squeeze / podjatie | déjà bon |
| `pressure_score` | effort / pression | bon proxy |
| `center migration` | déplacement du centre de gravité | central pour scènes |

---

## 6. Ce que T009 couvre partiellement

```text
Braking bar
Wick rejection
Impulse vs braking
Trap candidate
Breakout + retest
Acceptance / rejection
Flow exhaustion
Movement skeleton
Retrace depth
Symbol-specific thresholds
```

Ces concepts peuvent être approchés avec `M1_BAR_PROXY`, mais doivent être plafonnés en confiance :

```text
source_mode = M1_BAR_PROXY
data_visibility = RECONSTRUCTED
confidence_cap = 0.35
```

---

## 7. Ce qui manque et exige raw tick

Priorité raw tick :

```text
vrai delta buy/sell
cumulative delta robuste
delta zero-cross fiable
cluster maximal exact par prix
volume/delta dans mèche
shadow delta distortion
micro-flips
aggressive vs passive inference
unfinished / finished auction si validé plus tard
```

Architecture recommandée :

```text
MT5 raw tick recorder
→ tick_archive.db
→ tick_stream
→ B9 raw microfilm
```

Ne pas remplacer :

```text
MT4 indicateur → powerflow.db → force_snapshots_v2 → contexte PowerFlow
```

---

## 8. Ce qui peut fonctionner en M1_BAR_PROXY

```text
failed displacement
compression
center migration
movement skeleton
projection decay
wave steepness
wick ratio
break / retest grossier
acceptance / rejection grossier
retrace depth
dwell approximatif
scene segmentation lente
```

Règle :

```text
M1 proxy ne doit pas prétendre lire le footprint.
M1 proxy lit la scène, pas le carnet microstructure.
```

---

## 9. Nouveaux T009_MOMENT_* proposés V2

### 9.1 Moments prioritaires

```text
T009_MOMENT_ABSORPTION_SHELF
T009_MOMENT_CENTER_MIGRATION_UP
T009_MOMENT_CENTER_MIGRATION_DOWN
T009_MOMENT_IMBALANCE_PUSH
T009_MOMENT_IMBALANCE_ABSORBED
T009_MOMENT_FLOW_BRAKE
T009_MOMENT_FLOW_EXHAUSTION
T009_MOMENT_FLOW_BREATHING
T009_MOMENT_TRAP_CANDIDATE
T009_MOMENT_ACCEPTANCE
T009_MOMENT_REJECTION
```

### 9.2 Moments V2 ajoutés

```text
T009_MOMENT_BREAK_RETEST
T009_MOMENT_BREAK_RETEST_FAILED
T009_MOMENT_RETURN_TO_POC
T009_MOMENT_VALUE_AREA_BREAK
T009_MOMENT_VALUE_AREA_REINTEGRATION
T009_MOMENT_LEVEL_INTERACTION
T009_MOMENT_RETEST_HOLDS_STRUCTURE
T009_MOMENT_STRUCTURE_PRESERVED
T009_MOMENT_BATTLE_LEVEL_CONFIRMED
T009_MOMENT_WICK_VOLUME_REJECTION
T009_MOMENT_PROJECTION_DECAY
T009_MOMENT_RETRACE_STRESS
T009_MOMENT_EFFORT_WITHOUT_RESULT
```

---

## 10. Event → Moment Gate proposé

### 10.1 Pourquoi

V1 listait des markers. V2 ajoute la règle : ne pas transformer un event brut en moment sans contexte.

```text
T009 event brut
+ zone mémoire
+ effort/result
+ structure
+ retest/acceptance
+ data visibility
= moment B9
```

### 10.2 Champs minimum d'un moment

```json
{
  "moment_type": "T009_MOMENT_IMBALANCE_ABSORBED",
  "time_start": "...",
  "time_end": "...",
  "zone_low": 0.0,
  "zone_high": 0.0,
  "zone_center": 0.0,
  "event_count": 0,
  "dominant_event_type": "T009_ABSORPTION_CLUSTER",
  "avg_dwell_score": 0.0,
  "avg_failed_displacement_score": 0.0,
  "avg_compression_score": 0.0,
  "avg_pressure_score": 0.0,
  "migration_direction": "UP | DOWN | STABLE | MIXED",
  "effort_role": "FUEL | BRAKE | ABSORBED | UNKNOWN",
  "acceptance_state": "ACCEPTED | REJECTED | PENDING | FAILED",
  "source_mode": "RAW_TICK | TIMER_1S_SAMPLE | M1_BAR_PROXY",
  "data_visibility": "FULL | PARTIAL | RECONSTRUCTED",
  "confidence_cap": 0.35,
  "reading": "...",
  "limitations": []
}
```

---

## 11. Metrics proposées pour futur Sequence Summarizer

### 11.1 Effort-result

```python
effort = pressure_score + tick_density_score + delta_proxy_score
result = displacement_efficiency + center_migration_score + close_acceptance_score
failed_effort = effort * (1.0 - result)
```

### 11.2 Wick rejection proxy

```python
upper_wick_ratio = (high - max(open, close)) / max(high - low, pip_size)
lower_wick_ratio = (min(open, close) - low) / max(high - low, pip_size)
```

### 11.3 Projection decay

```python
projection_decay = current_wave_projection / max(previous_wave_projection, pip_size)
```

### 11.4 Center migration

```python
center_migration = current_zone_center - previous_zone_center
```

### 11.5 Acceptance / rejection grossier

```python
accepted_above = close > zone_high and next_close >= zone_high
rejected_above = high > zone_high and close < zone_high
accepted_below = close < zone_low and next_close <= zone_low
rejected_below = low < zone_low and close > zone_low
```

---

## 12. Risques techniques V2

```text
SINGLE_BAR_FALSE_POSITIVE
CLUSTER_OVERINTERPRETATION
BROKER_FEED_BIAS
SYNTHETIC_VOLUME_BIAS
NORMALIZATION_WINDOW_DRIFT
M1_PROXY_OVERCLAIM
RAW_TICK_REQUIRED_FOR_DELTA
SPREAD_WICK_CONFUSION
NEWS_WICK_CONFUSION
UNIVERSAL_THRESHOLD_FALSE_POSITIVE
HARD_CODED_DELTA_FILTER
EVENT_WITHOUT_CONTEXT
RETEST_TOO_FAST_FOR_M1_PROXY
```

---

## 13. Recommandation finale

### 13.1 Ne pas coder un gros module maintenant

La prochaine étape ne doit pas être un nouveau monstre. Elle doit être un petit gate :

```text
T009 Sequence Summarizer V0
```

But :

```text
100+ events bruts
→ 5 à 8 moments lisibles
```

### 13.2 Priorité d'implémentation

```text
P0 — Ajouter le vocabulaire moment V2 dans docs/lexique.
P1 — Créer un classifier event→moment minimal, read-only.
P2 — Produire un JSON moments, sans dashboard lourd.
P3 — Comparer RAW_TICK vs M1_BAR_PROXY quand tick_archive.db existe.
P4 — Seulement ensuite croiser avec B8.
```

### 13.3 Phrase de cap V2

```text
B9 ne doit pas prédire.
B9 doit raconter la scène locale.

Le cluster est une preuve.
Le delta est une pression.
Le prix donne le résultat.
La zone garde la mémoire.
Le moment relie cause et conséquence.
```

---

## 14. Message court pour architecte

```text
V2 DeltaRiver→B9 transforme le rapport V1 en base de spécification.
Les 6 transcriptions confirment : il ne faut pas copier DeltaRiver.
Il faut extraire une grammaire B9 : effort/résultat, fuel/brake,
absorption, delta sans progression, wick rejection, POC/zone mémoire,
projection decay, squeeze→break→retest, event→moment gate.

T009 couvre déjà dwell/failed displacement/compression/pressure/center migration.
Il manque surtout : retest status, wick/projection/retrace, acceptance/rejection,
normalization window, et raw tick pour delta/cluster exact.

Prochain geste recommandé : Sequence Summarizer V0, pas gros module.
```
