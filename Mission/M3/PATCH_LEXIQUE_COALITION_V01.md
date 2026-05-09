# PATCH LEXIQUE COALITION — AJOUT CLAUDE.md V6

**Mission** : termes coalition + battlefield + tension signature pour intégration lab  
**Version** : V0.1 — 7 mai 2026  
**Cible** : CLAUDE.md section LEXIQUE POWERFLOW V6  

---

## SECTION 1 — COALITIONS (pf_coalitions.py)

### Structures de base

**CurrencyVector** — vecteur mathématique représentant une devise dans l'espace tension-timing.
- Composantes : `z_basket` (position actuelle), `slope` (vitesse), `curvature` (accélération)
- Métadonnées : `phase`, `quality`, `zone_state`, `zone_level`, `context_tags`
- Propriétés dérivées : `polarity` (HIGH/LOW/CENTER), `direction` (RISING/FALLING/FLAT), `is_tense` (abs(z) ≥ 1.20)

**CurrencyCoalition** — groupe de devises qui respirent ensemble (z_basket proche + slope alignée + curvature proche).
- Membres : liste devises (ex: ["USD", "CAD", "CHF"])
- Caractéristiques : `polarity` (HIGH/LOW), `direction` (RISING/FALLING), `state` (voir états ci-dessous)
- Scores : `cohesion` [0..1], `z_mean`, `slope_mean`, `curvature_mean`
- Acteurs : `leader` (devise slope max), `follower` (devise slope min), `antagonist_candidates`
- Phase : synchronisation temporelle (`MICROFILM`, `INTERMEDIATE`, `SCENARIO`)

### Seuils critiques

```
DEFAULT_MAX_Z_GAP = 0.55         # écart z_basket max entre 2 membres coalition
DEFAULT_MAX_SLOPE_GAP = 0.18     # écart slope max entre 2 membres
DEFAULT_MAX_CURVATURE_GAP = 0.14 # écart curvature max entre 2 membres
DEFAULT_MIN_ABS_Z = 1.20         # tension minimale pour entrer coalition (abs)
DEFAULT_MIN_COHESION = 0.62      # cohésion minimale pour coalition valide
EXTREME_Z = 2.0                  # seuil extrême (états spéciaux)
CENTER_Z = 0.50                  # seuil centre neutre
```

### États coalition

**LOW_ELASTIC_COALITION_RESPRING** — coalition basse en respring.
- Condition : `polarity=LOW` + `direction=RISING` + `abs(z_mean) ≥ 2.0`
- Lecture : groupe de devises comprimées bas qui rebondissent vers haut avec force extrême
- Exemple : GBP+JPY+AUD z_mean=-2.3, slope +0.15 → respring élastique actif

**LOW_COALITION_RISING** — coalition basse montante standard.
- Condition : `polarity=LOW` + `direction=RISING` + `abs(z_mean) < 2.0`
- Lecture : groupe bas qui monte sans compression extrême
- Exemple : EUR+CHF z_mean=-1.5, slope +0.08 → montée progressive

**LOW_PRESSURE_COALITION_EXPANDING** — coalition basse en expansion descendante.
- Condition : `polarity=LOW` + `direction=FALLING`
- Lecture : groupe bas qui s'enfonce davantage, pression augmente
- Exemple : AUD+NZD z_mean=-1.8, slope -0.12 → compression bas s'intensifie

**HIGH_PRESSURE_COALITION_FOLDING** — coalition haute qui plie avec force extrême.
- Condition : `polarity=HIGH` + `direction=FALLING` + `abs(z_mean) ≥ 2.0`
- Lecture : groupe très haut qui craque et descend rapidement (release haute)
- Exemple : USD+CAD z_mean=+2.4, slope -0.18 → folding haute pression

**HIGH_COALITION_FALLING** — coalition haute descendante standard.
- Condition : `polarity=HIGH` + `direction=FALLING` + `abs(z_mean) < 2.0`
- Lecture : groupe haut qui descend sans extrême
- Exemple : GBP+EUR z_mean=+1.6, slope -0.07 → descente modérée

**HIGH_PRESSURE_COALITION_EXPANDING** — coalition haute en expansion montante.
- Condition : `polarity=HIGH` + `direction=RISING`
- Lecture : groupe haut qui monte encore, pression haute augmente
- Exemple : USD+CHF z_mean=+1.9, slope +0.11 → expansion haute continue

### Phases synchronisation

**MICROFILM_SYNCHRONIZED_FIELD** — synchronisation M1 microfilm.
- Tag : `M1_SPECIAL_MICROFILM` présent dans context_tags
- Lecture : coalition formée sur micro-agitation M1, durée vie courte, réaction rapide

**INTERMEDIATE_SYNCHRONIZED_FIELD** — synchronisation M5/M15 intermédiaire.
- Tag : `M5_M15_INTERMEDIATE_FIELD` présent
- Lecture : coalition formée sur TFs intermédiaires, durée vie moyenne

**SCENARIO_SYNCHRONIZED_FIELD** — synchronisation H1+ scenario.
- Tag : `SCENARIO_ZONE_WORK` ou `H1_SCENARIO_CURVE` présent
- Lecture : coalition formée sur TFs scenario, durée vie longue, structure stable

**SYNCHRONIZED_RESPRING** — respring synchronisé.
- Condition : état coalition contient `RESPRING`
- Lecture : plusieurs devises rebondissent ensemble depuis zone basse

**SYNCHRONIZED_FOLDING** — folding synchronisé.
- Condition : état coalition contient `FOLDING`
- Lecture : plusieurs devises plient ensemble depuis zone haute

### Compatibilité personality

**personality_compatibility_score** — score compatibilité [0..1] entre 2 devises basé sur profils.
- Composantes : `volatility_compatibility` (35%), `role_compatibility` (35%), `tempo_compatibility` (30%)
- Exemple : GBP (RISK, HIGH volatility, tempo=5) + AUD (RISK, HIGH volatility, tempo=15) → score 0.82 (compatible)
- Exemple : JPY (REFUGE, LOW volatility, tempo=60) + AUD (RISK, HIGH volatility, tempo=15) → score 0.53 (incompatible)

**cohesion** — score cohésion coalition [0..1].
- Calcul : `0.45*z_part + 0.35*slope_part + 0.20*curv_part + tag_bonus + personality_calibration`
- Seuil minimal : 0.62
- Lecture : cohésion 0.78 = coalition très soudée, cohésion 0.64 = coalition faible

---

## SECTION 2 — BATTLEFIELD RELATIONS (pf_coalition_relations.py)

### Structure de base

**CoalitionBattlefieldRelation** — relation opposition structurelle entre coalition et antagoniste.
- Acteurs : `coalition_members` (liste), `antagonist` (devise unique)
- Classification : `relation_type`, `field_state`, `phase`
- Polarités : `coalition_polarity` (HIGH/LOW), `antagonist_polarity` (HIGH/LOW)
- Directions : `coalition_direction` (RISING/FALLING), `antagonist_direction` (RISING/FALLING)
- Tensions : `coalition_z`, `antagonist_z`, `coalition_slope`, `antagonist_slope`
- Scores : `opposition_score`, `timing_score`, `field_score`

### Relation types — classification opposition

**LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING** — bloc bas respring vs haut folding.
- Condition : coalition LOW+RISING vs antagoniste HIGH+FALLING
- Lecture : groupe bas rebondit pendant que devise haute plie → potentiel rotation complète
- Exemple : EUR+GBP+CHF z=-1.8 slope=+0.12 vs USD z=+2.1 slope=-0.15
- Criticité : **HAUTE** — setup rotation classique, fenêtre tactique probable

**HIGH_BLOCK_FOLDING_AGAINST_LOW_RESPRING** — bloc haut folding vs bas respring.
- Condition : coalition HIGH+FALLING vs antagoniste LOW+RISING
- Lecture : groupe haut plie pendant que devise basse rebondit → rotation inverse
- Exemple : USD+CAD z=+2.3 slope=-0.14 vs JPY z=-1.9 slope=+0.10
- Criticité : **HAUTE** — rotation inverse, USD/JPY setup classique

**COALITION_VS_ANTAGONIST_OPPOSITION** — opposition générique.
- Condition : polarité inverse + direction inverse, pas de pattern extrême
- Lecture : groupe et antagoniste se déplacent en sens opposé sans extrêmes marqués
- Exemple : GBP+AUD z=-1.2 slope=+0.08 vs CHF z=+1.4 slope=-0.06
- Criticité : MOYENNE — opposition présente mais pas critique

**POLARIZED_FIELD_WITH_WEAK_TIMING** — polarité présente, timing faible.
- Condition : polarité inverse MAIS direction=FLAT pour l'un ou l'autre
- Lecture : opposition polarité existe mais timing non aligné (pas de mouvement clair)
- Exemple : EUR+GBP z=-1.5 vs USD z=+1.8 slope=-0.02 (USD quasi-flat)
- Criticité : FAIBLE — attente mouvement timing clair

### Field states — qualification champ de bataille

**FIELD_SIDE_SHIFT_ACTIVE** — rotation coalition active.
- Condition : `field_score ≥ 0.72` + relation_type = RESPRING vs FOLDING
- Lecture : rotation complète en cours, les deux côtés bougent fort en sens opposé
- Criticité : **CRITIQUE** — fenêtre tactique large ouverte, high probability move
- Exemple : field_score=0.78, opposition=0.82, timing=0.73

**BATTLEFIELD_WINDOW_OPENING** — fenêtre tactique s'ouvre.
- Condition : `field_score ≥ 0.58`
- Lecture : opposition + timing suffisants pour qualifier fenêtre ouverte
- Criticité : HAUTE — setup valide, surveiller confirmation
- Exemple : field_score=0.64, opposition=0.68, timing=0.59

**POLARITY_PRESENT_TIMING_WEAK** — polarité forte, timing faible.
- Condition : `opposition_score ≥ 0.55` ET `timing_score < 0.35`
- Lecture : devises sur côtés opposés mais mouvement timing pas encore synchronisé
- Criticité : MOYENNE — attente timing pickup
- Exemple : opposition=0.71, timing=0.28 → polarité OK, attente slope opposée

**STRUCTURE_BUILDING** — construction structure.
- Condition : tout le reste (field_score < 0.58)
- Lecture : relation détectée mais pas encore battlefield window
- Criticité : FAIBLE — observation, pas encore setup

**WEAK_FIELD_OPPOSITION** — opposition faible.
- Condition : `opposition_score < 0.40`
- Lecture : polarité inverse mais écart faible, pas de tension réelle
- Criticité : TRÈS FAIBLE — bruit, pas d'intérêt tactique

### Phases battlefield

**ACTIVE_COALITION_ROTATION** — rotation coalition active.
- Condition : field_state = FIELD_SIDE_SHIFT_ACTIVE
- Lecture : rotation en cours confirmée, phase tactique active
- Action : surveiller confirmation nodes, fractal coherence

**TEMPORAL_WINDOW_PREPARING** — préparation fenêtre temporelle.
- Condition : field_state = BATTLEFIELD_WINDOW_OPENING
- Lecture : fenêtre s'ouvre, attente confirmation complète
- Action : surveiller turning_points, kinematics detachment

**LOW_COALITION_RELEASE_BIRTH** — naissance release coalition basse.
- Condition : relation_type = LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
- Lecture : coalition basse prête à release UP
- Action : chercher first_detachment UP sur membre leader coalition

**HIGH_COALITION_RELEASE_BIRTH** — naissance release coalition haute.
- Condition : relation_type = HIGH_BLOCK_FOLDING_AGAINST_LOW_RESPRING
- Lecture : coalition haute prête à release DOWN
- Action : chercher first_detachment DOWN sur membre leader coalition

**FIELD_RELATION_OBSERVATION** — observation relation champ.
- Condition : défaut
- Lecture : relation détectée sans phase tactique
- Action : monitoring passif

### Scores battlefield

**opposition_score** — score opposition polarité [0..1].
- Calcul : `(min(abs(coalition_z), 3.0)/3.0 + min(abs(antagonist_z), 3.0)/3.0) / 2.0`
- Lecture : mesure écart polarité normalisé (cap à 3.0 pour éviter outliers)
- Exemple : coalition z=-2.1, antagonist z=+1.8 → opposition=0.65

**timing_score** — score opposition timing slope [0..1].
- Calcul : `(min(abs(coalition_slope), 0.35)/0.35 + min(abs(antagonist_slope), 0.35)/0.35) / 2.0`
- Lecture : mesure écart slope normalisé (cap à 0.35)
- Exemple : coalition slope=+0.12, antagonist slope=-0.14 → timing=0.59

**field_score** — score global champ de bataille.
- Calcul : `0.55*opposition_score + 0.45*timing_score`
- Seuil battlefield_window : 0.58
- Seuil field_side_shift : 0.72
- Lecture : score composite polarité + timing, détermine field_state

---

## SECTION 3 — TENSION SIGNATURE (pf_tension_signature.py)

### Structure de base

**TensionSignature** — signature micro/macro variance d'une devise.
- Composantes : `micro_var` (variance bar-to-bar), `macro_var` (variance sub-means fenêtre)
- Score : `micro_var / (macro_var + EPSILON)` cap à MAX_SCORE=50.0
- Label : `ELASTIC_LOADED` / `DIRECTIONAL_MOVE` / `DEAD_CURRENCY`
- Note : description textuelle état

### États tension

**ELASTIC_LOADED** — devise comprimée, élastique en charge.
- Condition : `score > 2.5`
- Lecture : micro-agitation haute (bar-to-bar volatile) sur fond macro plat → devise comprimée prête à release
- Exemple : USD score=4.2, micro_var=3.8, macro_var=0.9 → forte compression, attente release
- Action : chercher first_detachment imminent, surveiller kinematics angle soudain

**DIRECTIONAL_MOVE** — mouvement directionnel lent.
- Condition : `score < 0.35`
- Lecture : macro-variance dominante (trend smooth) sur micro faible → devise en mouvement trend
- Exemple : JPY score=0.22, micro_var=0.8, macro_var=3.6 → trend DOWN lent et régulier
- Action : surveiller zone_state progression (PRE_EXTREME → EARLY_EXTREME → ACCUMULATING)

**DEAD_CURRENCY** — devise inactive ou pause.
- Condition : `0.35 ≤ score ≤ 2.5` OU `micro < 1.0 ET macro < 1.0`
- Lecture : micro/macro équilibrés OU amplitude absolue négligeable → devise en pause ou bruit blanc
- Exemple : CHF score=1.1, micro_var=1.2, macro_var=1.1 → équilibre, pas de mouvement clair
- Action : ignorer jusqu'à pickup variance

### Seuils critiques

```
ELASTIC_THRESHOLD = 2.5      # seuil score ELASTIC_LOADED
DIRECTIONAL_THRESHOLD = 0.35 # seuil score DIRECTIONAL_MOVE
DEAD_ABS_THRESHOLD = 1.00    # variance absolue min (micro ET macro)
MIN_BARS = 6                 # minimum barres valides
MAX_SCORE = 50.0             # cap score pour éviter division par zéro outliers
```

### Calculs variance

**micro_variance** — variance bar-to-bar deltas.
```python
deltas = [force[i] - force[i-1] for i in range(1, len(force))]
micro_var = variance(deltas)
```
- Lecture : mesure volatilité court terme (bar suivante vs bar précédente)
- High micro_var → agitation haute, barres erratiques
- Low micro_var → mouvement smooth, barres régulières

**macro_variance** — variance sub-means fenêtre glissante.
```python
sub_means = [mean(force[i:i+window]) for i in steps]
macro_var = variance(sub_means)
```
- Lecture : mesure volatilité trend moyen terme (moyennes chunks vs moyennes chunks)
- High macro_var → trend volatile, direction change
- Low macro_var → trend plat, direction stable

---

## SECTION 4 — INTÉGRATION LAB

### Cas d'usage coalition lab

**Scénario 1 : USD H1 6 mai détection**
```
Kinematics détecte : USD first_detachment +22.5° UP
Zones détecte : USD EARLY_EXTREME UP
Nodes détecte : PRE_CROSS_COMPRESSION_NODE H1 16:00
Fractal coherence : M1 PHASE_OPPOSITION, M30 PARTIAL_SYNC

AVEC coalitions :
- Coalition détectée : USD+CAD+CHF
  - Polarity=HIGH, direction=RISING
  - State=HIGH_PRESSURE_COALITION_EXPANDING
  - Cohesion=0.78 (forte)
  - Leader=USD, followers=[CAD, CHF]
  - Antagonists=[AUD, JPY]
- Relation USD+CAD+CHF vs AUD :
  - Type=HIGH_BLOCK vs LOW_RESPRING (rotation probable)
  - Field_state=BATTLEFIELD_WINDOW_OPENING (score 0.64)
  - Phase=TEMPORAL_WINDOW_PREPARING
  - Opposition=0.68, timing=0.59
- Tension USD :
  - Score=3.8 ELASTIC_LOADED
  - micro_var=4.2, macro_var=1.1
  - Note : compression avant detachment
```

**Gain** : passage de "USD monte +22°" à "coalition USD+CAD+CHF haute vs AUD basse, battlefield window ouverte, USD comprimé avant detachment".

**Scénario 2 : Battlefield window sans coalition**
```
Kinematics : pas de detachment
Zones : plusieurs PRE_EXTREME mais pas cascade
Fractal coherence : FRACTAL_PARTIAL

AVEC coalitions :
- Aucune coalition cohesion > 0.62 détectée
- Plusieurs paires opposées mais pas de bloc structurel
- Battlefield relations : WEAK_FIELD_OPPOSITION
- Tension signatures : mix DEAD_CURRENCY + 1 DIRECTIONAL_MOVE
```

**Gain** : confirmation absence setup → pas de fenêtre tactique, market en pause structure.

### Query lab proposée

```python
def query_coalitions(db_path, symbol, tfs, start, end, min_cohesion=0.62):
    """
    Retourne :
    - active_relations : list[CoalitionBattlefieldRelation] avec field_score ≥ 0.45
    - strong_coalitions : list[Coalition] cohesion ≥ 0.75 sans antagoniste actif
    - weak_field : list[Coalition] cohesion < 0.75 ou field_score < 0.45
    """

def query_tension_signature(db_path, symbol, tfs, window=5, bars=30):
    """
    Retourne per devise per TF :
    - score, label (ELASTIC/DIRECTIONAL/DEAD)
    - micro_var, macro_var
    - note
    """
```

---

## SECTION 5 — RÉFÉRENCES CROISÉES

### Coalitions ↔ Nodes
- Coalition HIGH_PRESSURE_FOLDING + Node TRIPLE_CROSS_CLUSTER → confirmation release probable
- Coalition LOW_ELASTIC_RESPRING + Node PRE_CROSS_COMPRESSION_NODE → respring coalition validé
- Pas de coalition détectée + Node TRIPLE_NODE_PREPARATION → attente confirmation structure

### Coalitions ↔ Kinematics
- Coalition leader=USD + Kinematics USD first_detachment → confirmation leader détaché
- Coalition cohesion=0.78 + Kinematics same_angle_cluster → validation cluster tight
- Coalition state=EXPANDING + Kinematics speed=FAST → mouvement rapide confirmé

### Coalitions ↔ Zones
- Coalition members zone_state=ACCUMULATING → coalition en phase accumulation extrême
- Coalition field_state=BATTLEFIELD_WINDOW + Zone cascade divergence → transition régime
- Antagonist zone_state=RUPTURE + Coalition RESPRING → rotation complète probable

### Coalitions ↔ Fractal Coherence
- Coalition MICROFILM_SYNCHRONIZED + Fractal M1 PHASE_OPPOSITION → divergence LTF/HTF
- Coalition SCENARIO_SYNCHRONIZED + Fractal H1 PARTIAL_SYNC → structure HTF stable
- Field_state=ACTIVE_ROTATION + Fractal global=FRACTAL_PARTIAL → rotation partielle TFs

### Tension ↔ Kinematics
- Tension ELASTIC_LOADED + Kinematics speed=SLOW → compression sans mouvement (attente release)
- Tension DIRECTIONAL_MOVE + Kinematics angle stable → trend directionnel confirmé
- Tension DEAD_CURRENCY + Kinematics speed=SLOW → devise inactive, ignorer

### Tension ↔ Zones
- Tension ELASTIC_LOADED + Zone PRE_EXTREME → compression extrême imminente
- Tension DIRECTIONAL_MOVE + Zone ACCUMULATING → accumulation trend lent
- Tension DEAD_CURRENCY + Zone NEUTRAL → pause confirmée

---

**Fin patch lexique coalition V0.1**  
**Date** : 7 mai 2026  
**Intégration** : CLAUDE.md V6 section LEXIQUE  
**Prochaine étape** : validation seuils sur données 6-7 mai + test battlefield window
