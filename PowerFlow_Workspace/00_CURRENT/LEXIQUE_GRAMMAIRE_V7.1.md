# LEXIQUE GRAMMAIRE — PowerFlow V7
**Version : V0.9.0 | Date : 2026-05-09 | Statut : RÉFÉRENCE ACTIVE**

---

## PRINCIPE

Ce lexique est la langue de PowerFlow.
Pas un glossaire académique. Un langage de perception.

Chaque terme nomme un comportement de flux, pas une figure technique classique.
Si un terme classique apparaît ici, il a été redéfini dans la logique PowerFlow.

Ordre : domaine → terme → définition comportementale → usage.

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
Angle filtré par Kalman adaptatif. Plus propre que la fenêtre fixe.
Paramètres : Q=0.01 (bruit processus) R=0.10 (bruit mesure).

### VITESSE (speed_state)
Taux de variation de l'angle dans le temps.
États : ACCELERATING / STEADY / DECELERATING / STALLING / REVERSING.

### ACCÉLÉRATION
Variation de la vitesse. Signe de momentum ou d'épuisement.

### NOISE_RATIO
Ratio bruit/signal issu du filtre Kalman. 0 = propre. >0.3 = beaucoup de bruit.
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
Synthèse de l'état cinématique d'une devise :
angle + vitesse + accélération + first_detachment + clusters.
Produit par `pf_force_kinematics.py`.

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

## 4. CYCLES ET DENSITÉ TEMPORELLE

### TEMPORAL_DENSITY
Comportement des oscillations de force dans le temps.
Mesurée par autocorrélation rolling.
Permet de voir si une devise "respire" ou se comprime.

### CYCLE_COMPRESSING
Les oscillations se compriment dans le temps.
La fréquence augmente. La période raccourcit.
Pré-signal de rupture avant que M1 le montre.
`compression_ratio` proche de 1.0.

### CYCLE_EXPANDING
Les oscillations s'allongent. Pullback ou respiration.

### CYCLE_STABLE
Fréquence stable. Range / consolidation.

### CYCLE_NOISY
Pas de cycle dominant. Transition ou chaos.

### COMPRESSION_RATIO
Score 0.0–1.0 de compression des cycles. 1.0 = compression maximale.

### DOMINANT_PERIOD_BARS
Période dominante du cycle en nombre de barres.
Si = 1 (weekend) → séries statiques, normal.

### COMPRESSION_ALERT
True si 3+ devises simultanément en CYCLE_COMPRESSING.
Signal systémique — pas juste une devise isolée.

### FRACTAL_ALIGN_WINDOW
TF60 > TF30 > TF15 tous en CYCLE_COMPRESSING simultanément.
Compression fractale multi-TF. Signal fort de rupture imminente.

---

## 5. RÉGIME HTF

### REGIME
Contexte directionnel global du marché sur les TF hauts.
Qualifie chaque alerte LTF — deux détachements identiques peuvent avoir
des significations opposées selon le régime.

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

### HTF_CONTEXT_STACK
Stack JSON W/D/H4/H1 du contexte complet.
Produit par `pf_regime_engine.py`.
Injecté dans chaque alerte behavioral V7.

### REGIME_CONFIDENCE
Probabilité du régime détecté. 0.0–1.0.
< 0.5 → REGIME_TRANSITION probable.

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

### CASCADE_ENGINE
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

---

## 9. ÉNERGIE ET TENSION ÉLASTIQUE

### CURRENCY_ENERGY
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

## 10. ORCHESTRAL GRAVITY

### ORCHESTRAL_GRAVITY
Vision multi-devise multi-TF simultanée.
Qui mène, qui suit, qui résiste, qui comprime.
Vue "orchestre" des devises.

### ORCHESTRAL_COMPRESSION
Compression collective de plusieurs devises simultanément.
Pré-signal d'explosion directionnelle.
Voir `pf_orchestral_gravity_v02.py`.

---

## 11. NODES ET EVENTS

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
File JSON des alertes produites par le mapper.
Lue par le cockpit et le daemon Telegram.
Append only. Ne pas supprimer d'entrées manuellement.

---

## 12. QUALIFICATEURS D'ALERTE

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

## 13. TIMEFRAMES — RÔLES POWERFLOW

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

## 14. TERMES INTERDITS (BIAIS GPT)

Ces termes n'existent pas dans PowerFlow :
```
"trop risqué"           → risque technique spécifique seulement
"attends la confirmation" → qualifier, pas retenir
"sois prudent"          → pas de nanny
"signal dangereux"      → qualifier techniquement
"RSI suracheté"         → indicateur retardé non PowerFlow
"rejet de résistance"   → chartisme classique non PowerFlow
"figure en tête-épaules" → pattern chartiste hors domaine
```

---

## 15. NOMENCLATURE FICHIERS

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

*Lexique vivant — mise à jour après chaque nouveau terme validé en session*
*Version 0.9.0 — PowerFlow V7 — 2026-05-09*
---

## 16. QUALITÉ DONNÉES ET VALIDATION MARCHÉ OUVERT (V7.1)

### DATA_QUALITY_GUARD
Module (`pf_data_quality_guard.py`) de contrôle qualité de la mémoire SQLite. Vérifie la densité, la continuité temporelle, et détecte les données figées sans jamais filtrer les alertes. Produit le `QUALITY_REPORT`.

### STALE_DATA
Donnée trop ancienne par rapport au temps courant (capture arrêtée, fermée ou en retard). Risque technique de perception, pas un risque marché.

### TEMPORAL_GAP
Trou temporel entre deux snapshots supérieur à l'intervalle attendu (ex: gap de 5 min sur le M1). Indique un microfilm interrompu. Évalué via le `GAP_MULTIPLE`.

### NO_ROWS / TF1440_NO_ROWS
Absence totale de lignes sur un timeframe. `TF1440_NO_ROWS` indique l'absence de bougies daily dans la fenêtre scannée (HTF incomplet).

### MARKET_OPEN_VALIDATOR
Module (`pf_market_open_validator.py`) vérifiant que B4, B5 et EIE ne sont pas figés en condition live. Refuse une validation si la DB n'a pas de données fraîches.

### SIGNATURES STATIQUES (B4, B5, EIE)
- **B4_STATIC_DOMINANT_PERIOD / B4_WEEKEND_STATIC_SIGNATURE** : Les cycles ne respirent pas (souvent `dominant_period_bars = 1` en week-end).
- **B5_RHO_STATIC_OR_INSUFFICIENT_FLUCTUATION** : Corrélations Spearman figées.
- **EIE_STATIC_OUTPUT / EIE_ALL_NEUTRAL_STATIC** : Confluence élastique inerte (ou inexistence de capture).

### DB_PROXY & JSON_OUTPUT_MODE
Modes de validation : `DB_PROXY` recalcule une approximation depuis la DB brute. `JSON_OUTPUT_MODE` lit directement les fichiers JSON produits par les briques.

---

## 17. CONTEXTE SESSIONNEL ET ENTROPIE D'ALERTES (V7.1)

### SESSION_OVERLAY
Couche temporelle (`pf_session_overlay.py`) injectant le contexte de marché (Asian, London, NY) dans l'alerte via le `SESSION_CONTEXT`. Ne modifie pas la décision de trade.

### SESSION & OVERLAP
Nom de la session principale active (ex: London) et session secondaire en cas de chevauchement (ex: NY). `ASIAN_TO_LONDON_HANDOVER` (07h-08h UTC) et `MAX_VELOCITY_BATTLEFIELD` (London/NY, 12h-16h UTC) qualifient l'environnement naturel du flux.

### SESSION_PHASE & SESSION_BIAS
Phases internes (`IGNITION`, `MID_SESSION`, `DEAD_ZONE`) et biais comportementaux (`MAX_VELOCITY_BATTLEFIELD`). Ils qualifient l'environnement dans lequel l'alerte apparaît. Mesuré via `MINUTES_SINCE_OPEN`.

### ALERT_ENTROPY
Mesure (`pf_alert_entropy.py`) de la saturation du champ d'alertes sur fenêtre glissante. Quantifie la "Alert Fatigue" sans jamais censurer.

### DUPLICATION_RATIO & ALERT_KEY
Ratio d'alertes répétées. L'`ALERT_KEY` (ex: `FIRST_DETACHMENT_MICRO|GBP|HOT|EARLY`) permet de détecter si le moteur répète la même observation.

### BURST_DETECTION & BURST_SCORE
Détection d'une concentration rapide d'alertes (ex: 3 alertes en 5 min). Un burst indique une accélération, il ne censure rien.

### SHANNON_ENTROPY & NORMALIZED_ENTROPY
Mesure statistique de la dispersion des alertes. Entropie basse = champ répétitif. Entropie haute = champ diversifié. 

### ALERT_ENTROPY_STATE
Étiquette synthétique (`NORMAL_ALERT_FLOW`, `BURST_ACTIVE`, `SATURATED_DUPLICATE_BURST`). Qualifie la lisibilité technique, ne filtre pas les trades.

---

## 18. REPLAY ENGINE ET FILM HISTORIQUE (V7.1)

### REPLAY_ENGINE
Moteur read-only (`pf_replay_engine.py`) extrayant la mémoire brute (snapshots historiques) pour construire une timeline `REPLAY_FRAME` minute par minute. Ne recalcule aucun indicateur.

### RAW_MEMORY_REPLAY & DETERMINISTIC_REPLAY
Replay factuel de ce qui a été enregistré. Produit le même JSON si les arguments (symbole, date, start, end) sont identiques. Préserve les `FRAME_EMPTY` (trous de perception).

### FILM_ENGINE
Moteur de traduction comportementale (`pf_film_engine.py`). Transforme le Replay JSON en une frise chronologique Markdown (`FILM`). Raconte ce que la machine a perçu, sans conseiller de trades.

### TIMELINE & SCENE
La `TIMELINE` est l'ordonnancement chronologique. La `SCENE` est un événement narratif détecté (ex: `INFLEXION`, `COMPRESSION`, `ELASTIC_TENSION`, `RELEASE`, `CASCADE`).

### SCÈNES CINÉMATIQUES CLÉS
- **INFLEXION** : Premier décrochage (M1 exposé immédiatement).
- **KINEMATIC_SHIFT** : Changement d'angle brutal (accélération/décélération).
- **M1_M5_DESYNC** : M1 devance ou s'écarte de M5 (info de timing, pas un défaut).
- **CASCADE_SCENE** : Accélération d'une séquence d'événements.

### EVIDENCE & BEHAVIORAL_TRANSLATION
`EVIDENCE` attache les données brutes à la scène pour traçabilité. `BEHAVIORAL_TRANSLATION` transforme la data (ex: `first_detachment=true`) en récit humain ("Naissance d'une inflexion cinématique").