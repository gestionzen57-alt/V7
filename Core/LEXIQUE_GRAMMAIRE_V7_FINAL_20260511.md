# LEXIQUE GRAMMAIRE — PowerFlow V7.2 FINAL OFFICIAL
**Version : V7.2 | Date : 2026-05-11 | Validity : PRODUCTION post-P0 live**  
**Generated UTC : 2026-05-11T10:30:45Z**  
**Status : CANONICAL — sections 1-18 conservées + patch post-P0 intégré**  
**Attestation : tous les termes post-P0 sont attestés par rapports P0 live / Dashboard hydration**

---

## NOTE D’INTÉGRATION OFFICIELLE

Ce fichier produit la version canonique `LEXIQUE_GRAMMAIRE_V7_FINAL_20260511.md`.

Règle appliquée :

```text
Sections 1-18 : conservées depuis LEXIQUE_GRAMMAIRE_V72.md
Sections 19-23 : ajoutées depuis LEXIQUE_GRAMMAIRE_V72_PATCH_POST_P0_20260511.md
```

Les termes historiques restent valides.  
Le patch post-P0 ajoute les termes de production live sans effacer la grammaire existante.

---

## TABLE RÉCAPITULATIVE — AJOUTS POST-P0

| Terme | Domaine | Type | Statut |
|---|---|---|---|
| LAG1_COMPRESSION | B4 Temporal Density | État | PROD |
| PENDING_DATA_WINDOW | P0 Validation | Verdict | PROD |
| PASS_CORE_PARTIAL_STRICT | P0 Validation | Verdict | PROD |
| PASS_ALIVE | Moteur | Verdict | PROD |
| PASS_ENGINE / SILENT_STATE | Moteur | Verdict / état | PROD |
| PASS_DRY_RUN | Runner | Verdict | PROD |
| ACTIVE_COMPRESSION | B4 / marché | État | PROD |
| SPEARMAN_GRAVITY_ACTIVE | B5 | État | PROD |
| TAIL_EXTREME | B5 | État corrélation | PROD |
| HOT_NODE | Temporal Node | Priorité | PROD |
| M1_MICRO_NODE_BIRTH | Temporal Node | Événement | PROD |
| DATA_QUALITY_LTF_PASS | Guard DQ | Verdict | PROD |
| INSUFFICIENT_DATA → PENDING_DATA_WINDOW | Validateurs | Redéfinition | PROD |
| dominant_period_bars=1 → LAG1_COMPRESSION | B4 | Redéfinition | PROD |

---

# LEXIQUE GRAMMAIRE — PowerFlow V7.2
**Version : V7.2 | Date : 2026-05-10 | Statut : RÉFÉRENCE ACTIVE**

---

## PRINCIPE

Ce lexique est la langue de PowerFlow V7.2.
Pas un glossaire académique. Un langage de perception multi-dimensionnelle.

Chaque terme nomme un comportement de flux, pas une figure technique classique.
Si un terme classique apparaît ici, il a été redéfini dans la logique PowerFlow.

Ordre : domaine → terme → définition comportementale → usage V7.2.

---

## 1. FLUX ET FORCE

### FORCE
La pression directionnelle brute d'une devise sur une fenêtre temporelle donnée.
Mesurée comme z-score vs panier USD ou vs déviation propre.
Ne signifie pas "direction du trade". Signifie intensité mesurable.

### FORCE RELATIVE
Rapport de force entre deux devises ou entre une devise et son panier.
Base de toute comparaison PowerFlow. Rien n'est absolu — tout est relatif.

### FLUX
Le mouvement continu et évolutif de la force dans le temps.
Flux ≠ tendance. Un flux peut être directionnel, comprimé, en rotation, en absorption.
PowerFlow perçoit le flux, pas la direction.

### ANGLE
Pente de la force sur N barres. Exprime la directionnalité du flux.
Seuils first_detachment : M1=55° M5=45° M15=35° M30=28° H1=22°.

### ANGLE_KALMAN
Angle filtré par Kalman adaptatif (B3). Plus propre que la fenêtre fixe.
Paramètres : Q=0.01 (bruit processus) R=0.10 (bruit mesure).

### VITESSE (speed_state)
Taux de variation de l'angle dans le temps.
États : ACCELERATING / STEADY / DECELERATING / STALLING / REVERSING.

### ACCÉLÉRATION
Variation de la vitesse. Signe de momentum ou d'épuisement.

### NOISE_RATIO
Ratio bruit/signal issu du filtre Kalman (B3). 0 = propre. >0.3 = beaucoup de bruit.
Qualifie la fiabilité du signal avant d'alerter.

---

## 2. CINÉMATIQUE ET COMPORTEMENT

### FIRST_DETACHMENT
Premier décrochage angulaire significatif d'une devise par rapport au groupe.
Signe de début de mouvement ou d'inflexion naissante.
C'est une naissance, pas une confirmation. L'alerter tôt.

### SAME_ANGLE_CLUSTER
Groupe de devises alignées sur le même angle directeur.
Signal de coalition en formation ou de compression collective.

### TIGHT_GRAVITY_CLUSTER
Groupe serré en termes de distance z-score.
Pré-signal de compression avant explosion ou d'absorption collective.

### KINEMATICS_STATE
Synthèse de l'état cinématique d'une devise (B3) :
angle + vitesse + accélération + first_detachment + clusters.

---

## 3. ZONES ET ÉTATS DE TENSION

### ZONE_STATE
État de tension accumulée d'une devise sur un TF donné.
Séquence naturelle :
NEUTRAL → PRE_EXTREME → EARLY_EXTREME → ACCUMULATING → LEAKING → RUPTURE

### RUPTURE
La zone a cédé. Force libérée. Signal post-compression.

### LEAKING
La zone commence à fuir. La tension ne tient plus.
Précède souvent une RUPTURE ou un REJECTION.

### ACCUMULATING
La force s'accumule dans la zone. Pression croissante.
Signal d'attention — quelque chose se prépare.

### PRE_EXTREME
Approche des extrêmes de la zone. Tension préliminaire.

### ELASTIC_LOADED (ELASTIC_IN_EXTREME — EIE)
Zone active + élastique chargé sur TF1 + TF5 simultanément.
L'élastique se tend. Relâchement possible imminent.
Alerte la plus précoce du système avant une libération de flux.

### EIE_PERSISTANT
EIE maintenu sur 2+ snapshots consécutifs (≥ 10 min).
Confirmation de la tension. Pas de faux positif flash.

### FRACTALITÉ (0-3)
Nombre de TF simultanément en zone active parmi TF15/30/60.
3 = confluence fractale maximum — signal fort.
0 = LTF isolé — signal faible.

### EIE_LEADER_CONFIRMED
Devise en EIE + identifiée comme leader RG sur TF fiables.
Alerte prioritaire HOT. Confluence maximale.

---

## 4. CYCLES ET DENSITÉ TEMPORELLE (DUAL V7.2)

### TEMPORAL_DENSITY
Comportement des oscillations de force dans le temps.
**V7.2 : Dual perception Rolling (B4) + Wavelet (B4+).**

### CYCLE_COMPRESSING (B4 Rolling)
Les oscillations se compriment dans le temps via autocorrélation rolling.
La fréquence augmente. La période raccourcit.
Pré-signal de rupture avant que M1 le montre.
`compression_ratio` proche de 1.0.

### CYCLE_EXPANDING
Les oscillations s'allongent. Pullback ou respiration.

### CYCLE_STABLE
Fréquence stable. Range / consolidation.

### CYCLE_NOISY
Pas de cycle dominant. Transition ou chaos.

### COMPRESSION_RATIO (B4 Rolling)
Score 0.0–1.0 de compression des cycles via autocorrélation rolling.
1.0 = compression maximale.

### DOMINANT_PERIOD_BARS (B4 Rolling)
Période dominante du cycle en nombre de barres.
Si = 1 (weekend) → séries statiques, normal.

### WAVELET_POWER (B4+ Wavelet)
Puissance du signal dans la décomposition Morlet CWT.
Plus élevé = cycle non-stationnaire plus fort.

### DOMINANT_SCALE (B4+ Wavelet)
Échelle dominante en barres détectée par CWT.
Équivalent wavelet de `dominant_period_bars`.

### CYCLE_DETECTED (B4+ Wavelet)
Bool. True = cycle non-stationnaire détecté par CWT.

### COMPRESSION_ALERT
True si 3+ devises simultanément en CYCLE_COMPRESSING (B4).
Signal systémique — pas juste une devise isolée.

### FRACTAL_ALIGN_WINDOW
TF60 > TF30 > TF15 tous en CYCLE_COMPRESSING simultanément.
Compression fractale multi-TF. Signal fort de rupture imminente.

### DUAL_DENSITY_DIVERGENCE (V7.2)
Divergence entre B4 Rolling et B4+ Wavelet.
Ex: Rolling dit COMPRESSING (0.76), Wavelet dit EXPANDING (0.48).
Information critique — trader arbitre.

---

## 5. RÉGIME HTF (DUAL V7.2)

### REGIME
Contexte directionnel global du marché sur les TF hauts.
Qualifie chaque alerte LTF — deux détachements identiques peuvent avoir
des significations opposées selon le régime.
**V7.2 : Dual perception Legacy (B1) + HMM (B1+).**

### REGIME_COMPRESSION
Marché serré. Pas de flux clair. Explosion possible imminente.
FIRST_DETACHMENT + COMPRESSION → HOT.

### REGIME_TENDANCE
Flux directionnel établi. Le marché a choisi.
FIRST_DETACHMENT + TENDANCE → INFO (déjà en cours).

### REGIME_RANGE
Pas de flux. Consolidation / oscillation.
FIRST_DETACHMENT + RANGE → WATCH.

### REGIME_TRANSITION
Changement de régime en cours. Données mixtes.

### HTF_CONTEXT_STACK (B1 Legacy)
Stack JSON W/D/H4/H1 du contexte complet.
Méthode heuristique classique — rapide, robuste.

### HMM_TRANSITION_MATRIX (B1+ HMM)
Matrice de transition Hidden Markov Model.
Probabilités de passage entre régimes.

### HMM_EMISSION_PROBS (B1+ HMM)
Probabilités d'émission par état de régime.
Capture nuances transitions mieux que heuristique.

### REGIME_CONFIDENCE
Probabilité du régime détecté. 0.0–1.0.
< 0.5 → REGIME_TRANSITION probable.

### DUAL_REGIME_DIVERGENCE (V7.2)
Divergence entre B1 Legacy et B1+ HMM.
Ex: Legacy dit COMPRESSION (0.82), HMM dit TENDANCE (0.51).
Information critique — trader arbitre.

---

## 6. GRAVITÉ RELATIONNELLE

### RELATIONAL_GRAVITY (RG)
Comment les devises se tiennent et s'organisent entre elles.
Leader, followers, antagonistes, coalitions, cohérence multi-TF.
Pas une heuristique fixe — une mesure comportementale.

### LEADER
Devise qui tire le groupe. Angle le plus divergent.
Change selon le contexte. Pas toujours USD.

### FOLLOWER
Devise qui suit le leader avec cohérence.

### ANTAGONISTE
Devise qui va à l'opposé du leader.

### COALITION
Bloc de devises qui respirent ensemble.
Même angle, même zone, même pente.
Signal d'énergie groupée.

### MIXED (problème P1.2 résolu par B5)
Ancienne étiquette vague de RG V6 — devise simultanément leader ET antagoniste.
Résolu par avg_rho Spearman : relation faible mais mesurée, pas heuristique.

### BRIDGE_VERSION
Version du bridge RG validé. Actuellement 0.1.4.
Ne pas modifier sans tests.

---

## 7. GRAVITÉ DE SPEARMAN (B5)

### SPEARMAN_RHO
Corrélation de rang entre deux devises sur une fenêtre rolling.
-1.0 à +1.0. Statistique — pas une heuristique.

### AVG_RHO
Moyenne Spearman sur plusieurs TF. Résout l'ambiguïté MIXED.

### SYNCHRO
rho > 0.70 — devises bougent ensemble. Coalition probable.

### DIVERGENT
rho < -0.50 — devises bougent en sens opposé.

### CODEPENDANT_EXTREME
rho > 0.85 — co-dépendance aux extrema. Signal structurel fort.

### DIVERGENT_EXTREME
rho < -0.85 — opposition structurelle forte. Pair fracturé.

### MIXED_PROBABILISTE
avg_rho faible mais mesurable. Relation réelle, ambiguë.
Mieux que le label MIXED heuristique.

---

## 8. CASCADES ET VÉLOCITÉ

### CASCADE_ENGINE (B2)
Moteur de détection d'amplification d'événements.
Compte les HOT dans une fenêtre glissante de 5 min.
FIRST_DETACHMENT → M5_RELAY → RELEASE_ATTEMPT en 5 min = cascade.

### SEQUENCE_VELOCITY_HIGH
3+ HOT dans la fenêtre 5min. Cascade en formation. Alerte HOT.

### SEQUENCE_VELOCITY_MEDIUM
2 HOT dans la fenêtre. Signal d'attention.

### SEQUENCE_VELOCITY_LOW
0–1 HOT. Normal.

### CASCADE_BUILDING
Bool. True = cascade en formation.

### EVENTS_COUNT
Nombre d'événements HOT dans la fenêtre active.

### EVENT_RATE (V7.2)
Événements par minute dans la fenêtre.
Mesure la densité temporelle d'alertes.

---

## 9. ÉNERGIE ET TENSION ÉLASTIQUE

### CURRENCY_ENERGY (P1)
Vitalité d'une devise sur un TF donné.
Combinaison : zones, kinematics, tension élastique.
≠ direction. ≠ Node Heat. Contexte d'énergie.

### ELASTIC_TENSION_SCORE
Score de tension élastique dans l'energy probe.
Issu de pf_tension_signature.py.
Donne une mesure quantitative de l'élastique chargé.

### TENSION_SIGNATURE
Micro-variance vs macro-variance d'une devise.
Labels :
- ELASTIC_LOADED : micro agitation haute + macro plat = compression avant release
- DIRECTIONAL_MOVE : macro dominante = trend lent
- DEAD_CURRENCY : équilibré ou amplitude négligeable

---

## 10. MÉMOIRE COMPORTEMENTALE (B6 — V7.2)

### MEMORY_ENGINE
Mémoire de pattern comportemental.
"La dernière fois que [pattern 6D], que s'est-il passé ?"

### PATTERN_6D
Indexing 6 dimensions :
1. alert_type (ex: FIRST_DETACHMENT_MICRO)
2. regime (ex: COMPRESSION)
3. session (ex: LONDON_OPEN)
4. EIE_state (ex: ELASTIC_LOADED)
5. spearman (ex: SYNCHRO)
6. cascade (ex: VELOCITY_HIGH)

### PATTERN_HASH
Hash unique du pattern 6D.
Permet recherche rapide dans historique.

### OCCURRENCE_COUNT
Nombre de fois que ce pattern est apparu historiquement.

### MEDIAN_DURATION_BEFORE_MOVE_BARS
Médiane du nombre de barres avant mouvement significatif.
Pas une prédiction — une fréquence historique.

### OUTCOME_DISTRIBUTION
Distribution des outcomes historiques :
- EXPANSION : nombre de fois où mouvement directionnel a suivi
- REJECTION : nombre de fois où pattern a été rejeté/inversé

### MEMORY_CONTEXT (V7.2)
Contexte mémoire injecté dans alerte.
Pas de prédiction. Fréquence historique. Trader interprète.

---

## 11. SYNCHRONISATION FRACTALE (B7/B7+ — V7.2)

### FRACTAL_RESONANCE (B7)
Cross-correlation entre TF adjacents.
Détecte si LTF/MTF/HTF vibrent ensemble ou lag.

### RESONANCE_STATE
État de synchronisation fractale :
- **RESONANT** : TF en phase, amplification attendue
- **LAGGED** : TF décalés, LTF a bougé, MTF pas encore — fenêtre encore ouverte
- **DISSONANT** : TF incohérents
- **SILENT** : aucune cross-correlation significative

### RESONANT_TFS
Liste des TF en phase (ex: [1, 5, 15]).

### LAG_TFS
Liste des TF décalés (ex: [30, 60]).

### RESONANCE_SCORE
Score 0.0–1.0 de force de résonance.
Plus élevé = harmonie fractale plus forte.

### EXPECTED_AMPLIFICATION
Bool. True = amplification multi-TF attendue (si RESONANT).

### VOLATILITY_TEXTURE (B7+)
Nature de la volatilité — distingue pourquoi elle existe.

### VARIANCE_NATURE
Type de variance détecté :
- **STRUCTURAL** : mouvement directionnel structurel
- **NEWS_SPIKE** : spike ponctuel (news/event)
- **SESSION_FRICTION** : friction transition de session
- **MM_NOISE** : micro-agitation market maker

### MICRO_MACRO_RATIO
Ratio variance micro / variance macro.
Élevé = micro agitation dominante (compression élastique).
Bas = macro dominante (mouvement directionnel).

### SPREAD_BEHAVIOR
Comportement du spread (si disponible) :
- WIDENING : élargissement (risque technique)
- STABLE : stable
- TIGHTENING : resserrement (signal propre)

### PATTERN_CONSISTENCY
Consistance du pattern de variance sur fenêtre rolling.
0.0–1.0. Plus élevé = pattern répétitif (structurel).

---

## 12. ORCHESTRAL GRAVITY

### ORCHESTRAL_GRAVITY
Vision multi-devise multi-TF simultanée.
Qui mène, qui suit, qui résiste, qui comprime.
Vue "orchestre" des devises.

### ORCHESTRAL_COMPRESSION
Compression collective de plusieurs devises simultanément.
Pré-signal d'explosion directionnelle.

---

## 13. NODES ET EVENTS

### TEMPORAL_NODE
Convergence de signaux sur un TF donné formant un point d'inflexion.
Nommé, qualifié, horodaté.

### NODE_HEAT
Intensité de l'activité sur un node actif.
≠ Currency Energy.

### FIRST_DETACHMENT_MICRO (M1)
Premier décrochage visible sur M1. Naissance du mouvement.
Alerte la plus précoce. Ne pas censurer.

### COUNTER_RELEASE
Libération de flux en direction opposée à la pression dominante.
Peut être partielle, tentative, ou confirmée.
Alerter même non confirmée avec maturité exposée.

### COUNTER_RELEASE_ATTEMPT
Début d'un counter-release. Non confirmé. Exposer la maturation.

### RELEASE_STATE
État de libération du flux : BUILDING / ATTEMPT / CANDIDATE / CONFIRMED.

### BEHAVIORAL_ALERT_QUEUE
File JSON des alertes produites par le mapper (P2).
Lue par le cockpit et le daemon Telegram.
Append only. Ne pas supprimer d'entrées manuellement.

---

## 14. QUALIFICATEURS D'ALERTE

### HOT
Alerte prioritaire. Signal fort, contexte confirmé. Attention immédiate.

### WATCH
Alerte secondaire. Signal présent, contexte partiel. Surveiller l'évolution.

### INFO
Information contextuelle. Pas d'action requise. Enrichit la perception.

### MATURITY
Maturité d'un signal : BIRTH / EARLY / CANDIDATE / CONFIRMED.
Toujours exposée dans l'alerte. Jamais masquée.

### CAPTURE_QUALITY
Qualité de la capture MT4 → DB :
FULL_STACK_VISIBLE / TACTICAL_OK / DEGRADED / MINIMAL / BLIND.

### RELAY_QUALITY
Qualité du relais M5 pour une alerte M1 :
M5_RELAY_CLEAN / M5_THIN / M5_MISSING.

### TECHNICAL_RISKS
Liste des risques techniques identifiés pour une alerte.
Exemples : M1_NOISE_POSSIBLE / EARLY_MATURITY / RELAY_ABSENT / SQL_LATENCY.
Jamais des risques financiers. Jamais de morale.

---

## 15. TIMEFRAMES — RÔLES POWERFLOW

```
W       Mémoire profonde / régime lent / biais fond
D       Cycle mère / respiration supérieure
H4      Gravité structurelle / zone de bataille
H1      Traducteur intraday H4→M15
M30     Fenêtre énergétique / scénario court
M15     Battle window / transition MTF-LTF
M5      Relais tactique / confirmation
M1      Microfilm / ignition / first detachment
```

### LTF (Low TimeFrame)
M1, M5, M15. Intervention chirurgicale. Ignition. Exécution.

### MTF (Mid TimeFrame)
M15, M30, H1. Plan. Scénario. Fenêtre temporelle.

### HTF (High TimeFrame)
H4, D, W. Stratégie. Régime. Contexte primaire.

---

## 16. TERMES INTERDITS (BIAIS GPT)

Ces termes n'existent pas dans PowerFlow :
```
"trop risqué"           → risque technique spécifique seulement
"attends la confirmation" → qualifier, pas retenir
"sois prudent"          → pas de nanny
"signal dangereux"      → qualifier techniquement
"RSI suracheté"         → indicateur retardé non PowerFlow
"rejet de résistance"   → chartisme classique non PowerFlow
"figure en tête-épaules" → pattern chartiste hors domaine
"choisir entre Legacy et HMM" → exposer les deux, trader arbitre
"fusionner Rolling et Wavelet" → dual séparé, trader arbitre
```

---

## 17. NOMENCLATURE FICHIERS

```
capture_*   = acquisition / pont MT4 / insertion DB
pf_*        = moteur PowerFlow / calcul / analyse
run_*       = runner / daemon / CLI
lab_*       = outil d'exploration / analyse historique
cockpit_*   = affichage / lecture / synthèse
dashboard_* = serveur web / HTML live
telegram_*  = transmission d'alertes
```

---

## 18. GUARDS & INFRASTRUCTURE (V7.2)

### DATA_QUALITY_GUARD
Module (`pf_data_quality_guard.py`) de contrôle qualité de la mémoire SQLite.
Vérifie la densité, la continuité temporelle, et détecte les données figées.
Produit le `QUALITY_REPORT`.

### STALE_DATA
Donnée trop ancienne par rapport au temps courant (capture arrêtée).
Risque technique de perception, pas un risque marché.

### TEMPORAL_GAP
Trou temporel entre deux snapshots supérieur à l'intervalle attendu.
Indique un microfilm interrompu. Évalué via le `GAP_MULTIPLE`.

### NO_ROWS / TF1440_NO_ROWS
Absence totale de lignes sur un timeframe.

### MARKET_OPEN_VALIDATOR
Module (`pf_market_open_validator.py`) vérifiant que B4, B5 et EIE ne sont pas figés.
Refuse une validation si la DB n'a pas de données fraîches.

### SIGNATURES_STATIQUES (B4, B5, EIE)
- **B4_STATIC_DOMINANT_PERIOD** : cycles ne respirent pas (souvent `dominant_period_bars = 1` en week-end)
- **B5_RHO_STATIC** : corrélations Spearman figées
- **EIE_STATIC_OUTPUT** : confluence élastique inerte

### SESSION_OVERLAY
Couche temporelle (`pf_session_overlay.py`) injectant le contexte de marché.

### SESSION & OVERLAP
Nom de la session principale active (ASIAN, LONDON, NY) et session secondaire en chevauchement.

### SESSION_PHASE & SESSION_BIAS
Phases internes (`IGNITION`, `MID_SESSION`, `DEAD_ZONE`) et biais comportementaux.

### MINUTES_SINCE_OPEN
Minutes écoulées depuis ouverture de session.

### ALERT_ENTROPY
Mesure (`pf_alert_entropy.py`) de la saturation du champ d'alertes.
Quantifie la "Alert Fatigue" sans jamais censurer.

### DUPLICATION_RATIO & ALERT_KEY
Ratio d'alertes répétées. L'`ALERT_KEY` permet de détecter répétitions.

### BURST_DETECTION & BURST_SCORE
Détection d'une concentration rapide d'alertes (ex: 3 alertes en 5 min).

### SHANNON_ENTROPY & NORMALIZED_ENTROPY
Mesure statistique de la dispersion des alertes.
Entropie basse = champ répétitif. Entropie haute = champ diversifié.

### ALERT_ENTROPY_STATE
Étiquette synthétique :
- NORMAL_ALERT_FLOW
- BURST_ACTIVE
- SATURATED_DUPLICATE_BURST

Qualifie la lisibilité technique, ne filtre pas les trades.

---

---

## SECTION 19 — NOUVEAUX TERMES POST-P0

### LAG1_COMPRESSION

```
Domaine : B4 Temporal Density
Définition :
  dominant_period_bars = 1
  + unique_count élevé (20+)
  + écart-type non nul
  + Data Quality LTF PASS
  = État de compression avec période dominante ultra-courte

Distingue :
  LAG1_COMPRESSION   (lag1 mais flux réel)
  STATIC_SIGNATURE   (lag1 + variance = 0)

Contexte :
  Observé en P0 : GBP_TF1/TF5/TF15 compression_ratio=0.933
  + 30 rows uniques par TF
  + std = 18.1 (TF1), 11.6 (TF5), 13.4 (TF15)

Sémantique :
  Période cicle très courte mais signal réel.
  Pas du bruit. Pas du figé.
  Compression agressive en phase naissante.

Usage :
  B4_STATUS = PASS_ALIVE / LAG1_COMPRESSION
```

### PENDING_DATA_WINDOW

```
Domaine : P0 Validation, market_open_validator
Définition :
  Briques vivantes et respirant
  + fenêtre statistique insuffisante pour PASS strict
  ≠ FAIL moteur
  ≠ STATIC_SIGNATURE
  = Attente d'accumulation de données fraîches

Distinction critique :
  PENDING_DATA_WINDOW    (briques ALIVE, fenêtre trop courte)
  FAIL_STATIC_SIGNATURE  (briques DEAD, variance=0)
  FAIL_STALE_DATA        (dernière donnée > 1h)

Contexte :
  market_open_validator retourne : B4_INSUFFICIENT_DATA, B5_INSUFFICIENT_DATA
  Diagnostic vérifiait : B4 variance=18.1, B5 rho=-0.37, données < 10 min old
  Verdict : PENDING, pas FAIL

Progression :
  TF1  : 25 → 50 → 100+ rows fraîches
  TF5  : 6  → 20  → 50+ rows fraîches
  TF15 : 2  → 10  → 30+ rows fraîches
  Tout naturel, sans action requise

Timeline :
  Quelques heures de market normal = fenêtre complète
  Relancer validation toutes les heures

Sémantique :
  Pas d'urgence. Pas de panne. Juste accumulation.
```

### PASS_CORE_PARTIAL_STRICT

```
Domaine : P0 Validation, verdict multi-axes
Définition :
  Verdict tridimensionnel :
    1. Core Perception = PASS
    2. Dashboard Flow = PASS
    3. Strict Full = PENDING_DATA_WINDOW

Usage :
  "P0 PASS_CORE_PARTIAL_STRICT"
  = Perception validée, infrastructure OK, attente fenêtre

Opposé :
  FAIL_MOTEUR (briques crashées)
  FAIL_INFRASTRUCTURE (runners cassés)
  FAIL_STATIC (données figées)

Contexte P0 :
  ✅ Core perception  : B4/B5/Node produisent des observations vivantes
  ✅ Dashboard       : cockpit_agentic_state_v01.py produit JSON, interface affiche
  ✅ Automation     : run_p0_final_auto.ps1 tourne, verdict auto
  ⚠️ Strict full    : market_open_validator demande plus de rows/variance
```

### PASS_ALIVE

```
Domaine : Validateurs B4, B5, généralement
Définition :
  Brique moteur opérationnelle
  + produisant états non-figés
  + variance réelle mesurable
  + labels/rho changeant selon contexte

Critères PASS_ALIVE :
  B4 :
    - compression_ratio change (0.93, 0.91, etc.)
    - dominant_period varie
    - autocorr_peak non constant
    - Data Quality PASS sur TF

  B5 :
    - rho non-figés (-0.37, -0.50, 0.57, etc.)
    - labels divergent/synchro/neutral alternatifs
    - tail_extreme présents
    - bad_static = false

Opposés :
  STATIC_OUTPUT  (même valeur répétée)
  FAIL_MOTEUR    (crash, erreur)
  PASSIVE_WATCH  (non-vivant)

Contexte P0 :
  B4 PASS_ALIVE : "TEMPORAL_DENSITY_ACTIVE, COMPRESSION ALERT 17-19 devises/TF"
  B5 PASS_ALIVE : "SPEARMAN_GRAVITY_ACTIVE, rho vivants, mixed résolus"

Sémantique :
  La brique respire. Elle n'est pas morte.
```

### PASS_ENGINE / SILENT_STATE

```
Domaine : B7 Fractal Resonance, moteurs d'état
Définition :
  Moteur fonctionne et produit un état
  État observé = SILENT / RESONANT / DISSONANT / LAGGED
  ≠ moteur cassé

Exemples :
  B7_FRACTAL_RESONANCE = PASS_ENGINE / SILENT_STATE
    = Moteur calcule bien, état = pas de résonance en ce moment
    ≠ Moteur cassé

Lecture correcte :
  SILENT n'est pas mauvais. C'est un état de flux.
  Quelques TF résonnent, d'autres sont en lag ou dissonants.
  Normal. À surveiller pour quand ça s'aligne.

Contexte P0 :
  B7 : resonance_state=SILENT | dissonant_tfs=[1,5,15,30,60] | PASS_ENGINE
```

### PASS_DRY_RUN

```
Domaine : Runners, daemons
Définition :
  Runner testé en --dry-run
  Contrat CLI validé
  Pas d'alerte écrite en persistant
  Prêt pour activation réelle

Usage :
  Valider un daemon avant de le déployer en production
  Vérifier que le format output est bon sans modifier la file

Contexte P0 :
  run_confluence_alert.py --dry-run = PASS_DRY_RUN
  = Daemon prêt, pas d'alerte EIE écrite au fichier
```

### ACTIVE_COMPRESSION

```
Domaine : Dynamique marché, B4 Temporal Density
Définition :
  Compression réelle en cours de flux
  Mesurée par B4 sur 17-19 devises/TF simultanément
  compression_ratio = 0.93+
  Multiple TF (TF1, TF5, TF15) en phase CYCLE_COMPRESSING

Sémantique :
  Signal d'attention marché.
  Pré-signal de rupture.
  Accumulation d'énergie.
  Pas une panne, une situation marché.

Contexte P0 :
  "COMPRESSION ALERT : 17 à 19 devises / TF comprimés"
  "GBP_TF1 : CYCLE_COMPRESSING | compression_ratio=0.933"
```

### SPEARMAN_GRAVITY_ACTIVE

```
Domaine : B5 Spearman Gravity
Définition :
  B5 produit des corrélations vivantes
  rho non-figés (changent entre runs)
  États : SYNCHRO / DIVERGENT / NEUTRAL / CODEPENDANT_EXTREME / DIVERGENT_EXTREME
  mixed_resolved = true (P1.2 résolu)

Caractéristiques :
  - avg_rho change selon fenêtre
  - paires exhibent tail_extremes
  - divergences réelles (GBP_CAD, CAD_AUD observés)
  - relation probabiliste vraie

Contexte P0 :
  "SPEARMAN_GRAVITY_ACTIVE"
  "DIVERGENT : CAD_AUD, GBP_CAD / CAD_AUD selon run"
  "MIXED RÉSOLU : 14 à 17 paires"

Opposé :
  SPEARMAN_STATIC (rho=constant, aucun changement)
```

### TAIL_EXTREME

```
Domaine : B5 Spearman Gravity, états corrélation
Définition :
  Paire de devises en dépendance structurelle extrême
  rho > 0.85 (CODEPENDANT_EXTREME)
  ou rho < -0.85 (DIVERGENT_EXTREME)
  
Sémantique :
  Relation structurelle. Pas aléatoire.
  Forte liaison ou forte opposition.
  À surveiller pour changements de phase.

Contexte P0 :
  "TAIL EXTREME : GBP_AUD_TF15, USD_CAD_TF1, CAD_CHF_TF5"
```

### HOT_NODE

```
Domaine : Temporal Node State, priorité
Définition :
  Nœud temporel au niveau prioritaire HOT
  Caractéristiques :
    db_status = TACTICAL_PARTIAL_NO_M1 (ou mieux)
    highest_level = HOT_NODE
    level = HOT (vs WATCH / INFO)
    fractal_state = LTF_NODE_INSIDE_HTF_BATTLE_FIELD

Sémantique :
  Nœud actif d'importance maximale.
  Confluence M1/M5/M15.
  Pression évidente mesurable.
  À monitorer immédiatement.

Contexte P0 :
  "highest_level=HOT_NODE"
  "dominant_direction=GBP pressure down / USD pressure up"
  "structure_label=M5_NODE_WITH_M15_ENERGY_RELAY"
```

### M1_MICRO_NODE_BIRTH

```
Domaine : Temporal Node State, chronologie événement
Définition :
  Première détection de nœud sur M1 microfilm
  Signal de naissance d'une inflexion
  État = BIRTH (vs EARLY / CANDIDATE / CONFIRMED)
  Relais M5 attendu dans les 1-5 minutes

Sémantique :
  Événement le plus précoce du système de perception.
  Ignition de mouvement.
  Observation immédiate, confirmation attendue.
  À ne jamais censurer "trop tôt".

Contexte P0 :
  Observé dans Temporal Node outputs
  Indication : "M1_MICRO_NODE_BIRTH visible"
```

### DATA_QUALITY_LTF_PASS

```
Domaine : Data Quality Guard, validation
Définition :
  Validation d'une fenêtre de données LTF propre
  Critères :
    TF1  >= 25 rows
    TF5  >= 6 rows
    TF15 >= 2 rows
    stale = false (donnée < 10 min)
    gaps = 0 (fenêtre contigue)

Verdict :
  overall_status = PASS
  technical_risks = [] (aucun)

Sémantique :
  Capture LTF fiable pour B4 / B5 / Node.
  Pas d'ambiguïté données.
  Briques peuvent respirer normalement.

Contexte P0 :
  Validé depuis fenêtre 2026-05-11T01:15:00
  → M5/M15 revenus après rechargement EA
```

---

## SECTION 20 — REDÉFINITIONS CRITIQUES POST-P0

### INSUFFICIENT_DATA → PENDING_DATA_WINDOW

```
Domaine : Tous validateurs
Ancien terme : INSUFFICIENT_DATA (ambigu)
Nouveau terme : PENDING_DATA_WINDOW (précis)

Ancien problème :
  market_open_validator retourne "INSUFFICIENT_DATA"
  Interprétation floue : FAIL? ATTENDRE? MOTEUR CASSÉ?

Nouvelle clarification :
  PENDING_DATA_WINDOW
  = briques ALIVE + fenêtre trop courte
  ≠ FAIL_STATIC_SIGNATURE
  ≠ FAIL_STALE_DATA

Impact :
  Requalifie le validateur comme outil de mesure de fenêtre
  Pas comme jugement de santé moteur
  Progression naturelle : % fenêtre → statut changera

Exemple conversion :
  Ancien : "B4_INSUFFICIENT_DATA → FAIL"
  Nouveau : "B4_INSUFFICIENT_DATA → PENDING_DATA_WINDOW (88% fenêtre)"
```

### dominant_period_bars = 1 → LAG1_COMPRESSION

```
Domaine : B4 Temporal Density
Ancien problème :
  Règle simple : "dominant_period_bars = 1 → FAIL"
  Trop brutale. Faux négatifs.

Nouvelle règle :
  Cas 1 :
    dominant_period_bars = 1
    + unique_count élevé (20+)
    + std > 10
    + Data Quality PASS
    → LAG1_COMPRESSION (PASS_ALIVE)

  Cas 2 :
    dominant_period_bars = 1
    + unique_count faible
    + std ≈ 0
    + variance stagnante
    → STATIC_SIGNATURE (FAIL)

Impact :
  B4 correctement qualifié.
  Moins de faux FAIL.
  Distinction lag1 vivant vs figé.

Exemple P0 :
  Ancien : dominant_period=1 → FAIL
  Nouveau : dominant_period=1 + unique=30 + std=18 → LAG1_COMPRESSION PASS
```

---

## SECTION 21 — CLARIFICATIONS D'ÉTATS OBSERVÉS

### EIE_NEUTRAL ≠ EIE_STATIC_OUTPUT

```
Domaine : Confluence Élastique
Distinction : Deux états différents, même apparence
  EIE_NEUTRAL
    = zone NEUTRAL, aucune tension élastique active
    = État normal hors accumulation
    = Pas une panne

  EIE_STATIC_OUTPUT
    = EIE produit toujours NEUTRAL, aucun changement possible
    = Output figé
    = Panne moteur

Contexte P0 :
  EIE observé = NEUTRAL
  Raison : pas d'accumulation en ce moment
  Statut : Normal. À surveiller.
  ≠ Panne.
```

### COMPRESSION_ALERT vs. CYCLE_COMPRESSING

```
Domaine : B4 Temporal Density
Distinction :
  CYCLE_COMPRESSING
    = État d'UNE devise sur UN TF
    = Oscillation comprimée en période

  COMPRESSION_ALERT
    = État SYSTÉMIQUE
    = 3+ devises simultanément en CYCLE_COMPRESSING
    = Signal marché collectif

Contexte P0 :
  GBP_TF1 = CYCLE_COMPRESSING (état devise)
  COMPRESSION_ALERT = TRUE (système comprime)
  Lecture : 17-19 devises comprimées simultanément
```

### PASS vs PASS_ALIVE vs PASS_DRY_RUN

```
Domaine : Validateurs, nuance de verdict
PASS
  = État nominal, pas d'alerte particulière
  Exemple : Regime Engine PASS, Cascade Engine PASS

PASS_ALIVE
  = État nominal + preuve de vie / variance réelle
  Exemple : B4 PASS_ALIVE, B5 PASS_ALIVE
  Usage : Briques critiques où "vivant" doit être attesté

PASS_DRY_RUN
  = Contrat validé sans effet persistant
  Exemple : run_confluence_alert --dry-run = PASS_DRY_RUN
  Usage : Daemons prêts pour activation
```

---

## SECTION 22 — TABLEAU RÉCAPITULATIF TERMES POST-P0

| Terme | Domaine | Type | Contexte | Statut |
|-------|---------|------|---------|--------|
| LAG1_COMPRESSION | B4 | État | Période=1 + vivant | ✅ PROD |
| PENDING_DATA_WINDOW | P0 Valid. | Verdict | Attente fenêtre | ✅ PROD |
| PASS_CORE_PARTIAL_STRICT | P0 Valid. | Verdict | P0 final | ✅ PROD |
| PASS_ALIVE | Moteur | Verdict | Brique vivante | ✅ PROD |
| PASS_ENGINE | Moteur | Verdict | Moteur + état | ✅ PROD |
| PASS_DRY_RUN | Runner | Verdict | Contrat OK | ✅ PROD |
| ACTIVE_COMPRESSION | Marché | État | 17-19 devises | ✅ PROD |
| SPEARMAN_GRAVITY_ACTIVE | B5 | État | rho vivants | ✅ PROD |
| TAIL_EXTREME | B5 | État | rho extrema | ✅ PROD |
| HOT_NODE | Node | Priorité | Node prioritaire | ✅ PROD |
| M1_MICRO_NODE_BIRTH | Node | Événement | Naissance M1 | ✅ PROD |
| DATA_QUALITY_LTF_PASS | Guard | Verdict | Fenêtre clean | ✅ PROD |

---

## SECTION 23 — USAGE DANS RAPPORTS P0

Ces termes apparaissent dans :

```
RAPPORT_ARCHITECTE_MISSION_P0_POWERFLOW_V72.md
  - LAG1_COMPRESSION (section B4)
  - PASS_ALIVE (sections B4, B5)
  - HOT_NODE (section Temporal Node)
  - PASS_CORE_PARTIAL_STRICT (verdict final)

P0_VALIDATION_MARKET_OPEN_POWERFLOW_V72.md
  - PENDING_DATA_WINDOW (tout le document)
  - LAG1_COMPRESSION (diagnostic B4)
  - SPEARMAN_GRAVITY_ACTIVE (diagnostic B5)
  - DATA_QUALITY_LTF_PASS (validation LTF)
  - PASS_ALIVE (B4, B5, Node verdicts)
  - TAIL_EXTREME (B5 examples)
```

---

## CONSERVATION ORIGINALE

Tous les termes LEXIQUE_GRAMMAIRE_V7.md originaux restent valides.

Ce patch AJOUTE les nouveaux termes sans modifier les existants.

Intégration recommandée :
```
LEXIQUE_GRAMMAIRE_V7.md
  + SECTION 19 (nouveaux termes post-P0)
  + SECTION 20 (redéfinitions)
  + SECTION 21 (clarifications)
  = LEXIQUE_GRAMMAIRE_V7.2.md
```

---

*Patch lexique PowerFlow V7.2 — Validé en production P0 live — 2026-05-11*
*Tous les termes attestés par rapports architecte et validation marché ouvert.*

---

*LEXIQUE_GRAMMAIRE_V7_FINAL_20260511 — PowerFlow V7.2 — production post-P0 live.*
