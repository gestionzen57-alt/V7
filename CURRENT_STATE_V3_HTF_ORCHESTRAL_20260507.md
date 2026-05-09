# CURRENT_STATE — POWERFLOW V6 ORCHESTRATION

Date : 2026-05-07  
Statut : ÉTAT ACTIF SYNCHRONISÉ — HTF CORRIGÉ + ORCHESTRAL  
Destination recommandée : `PowerFlow_Workspace/00_CURRENT/CURRENT_STATE.md`

---

# 1. Nature active de PowerFlow — DOCTRINE CORRIGÉE

PowerFlow V6 est un moteur de perception du flux Forex.

Il n'est pas :
- un bot BUY/SELL ;
- une nounou ;
- une tour de contrôle ;
- un indicateur technique classique ;
- une usine de signaux retardés ;
- **un lecteur M1-only** (CORRECTION MAJEURE).

Règle centrale :

```text
La machine perçoit.
La machine mesure.
La machine nomme.
La machine alerte.
Le trader filtre.
Le trader décide.
```

## CORRECTION DOCTRINE HTF (07/05)

```text
ANCIEN (FAUX):  M1/M5/M15 = centre de gravité
CORRIGÉ (VRAI): W/D/H4/H1 = contexte primaire / gravité / fenêtre
                M15/M5/M1 = manifestation tactique / ignition / relais
```

Formule opérationnelle PowerFlow :

```text
HTF delayed gravity (W/D/H4/H1)
+ H1 transition (pont HTF-LTF)
+ M15 tactical window (scénario court)
+ M5 relay (confirmation tactique)
+ M1 ignition (first detachment / rattrapage)
= PowerFlow actionable perception
```

Hiérarchie W-D-HTF-LTF :

```text
W       régime lent / mémoire profonde / biais structurel de fond
D       cycle / respiration mère / fenêtre de retard supérieur
H4      gravité structurelle / zone de bataille / mémoire opérationnelle majeure
H1      traducteur intraday de la gravité HTF / pont H4-M15
M15     fenêtre énergétique / scénario court / battle window
M5      relais tactique / déclenchement mesuré
M1      microfilm / ignition / first detachment / rattrapage prix
```

Phrase clé :

```text
HTF donne la fenêtre temporelle et la gravité retardée.
LTF détecte l'ignition, le relais ou l'invalidation de cette fenêtre.
```

---

# 2. État officiel attendu

```text
Node V0.7.1 — VALIDÉ
capture_quality / relative freshness / telegram_gating

Node V0.7.2 — VALIDÉ
relay_quality / M5 missing-thin-clean

Node V0.7.3 — VALIDÉ
session_transition / DAILY_OPEN_TRANSITION

Node V0.8-B — VALIDÉ (HTF CORRECTION APPLIQUÉE)
kinematics_state / first_detachment / angle-speed-acceleration
Règle : Kinematics doit dire si ignition LTF cohérente avec fenêtre HTF

Node V0.8.1 — VALIDÉ
release_state typé

Node V0.8.2 — VALIDÉ (HTF CORRECTION À VENIR)
energy_release_alignment
Règle : V0.8.3 ou V0.9 devra exposer HTF_CONTEXT_STACK explicitement

Currency Energy V0.1 — VALIDÉE EN OBSERVATION (HTF CORRECTION APPLIQUÉE)
probe standalone, non signal
Règle : Doit intégrer contexte W/D/H4/H1 comme gravité lente

Behavioral Flow Dashboard Live — VALIDÉ
temporal_node_state → behavioral_queue → cockpit → dashboard

Relational Gravity V0.1 — VALIDÉ
probe standalone

Relational Gravity V0.1.1 — VALIDÉ
DIRECTION_MIN_DELTA filtre les devises plates

Relational Gravity P1.1 — VALIDÉ
bloc relational_gravity visible dans cockpit_agentic_state_v01.json

Relational Gravity P1.2 — BLOCKER 🔴
Bridge Guard pour éviter qu'un champ MIXED soit raconté comme un leader clair
INTERDIT TANT QUE P1.2 NON CORRIGÉ : P2 Behavioral Mapper relational

Orchestral Gravity V0.2 — VALIDÉ (07/05)
pf_force_inflection.py (pliures contresens)
pf_force_extrema.py (valleys/peaks asymétrie)
pf_orchestral_gravity.py (leader/follower/coalitions)
run_orchestral_analysis_once.py (runner complet)
```

---

# 3. État actuel bloquant — P1.2 BRIDGE GUARD

Le cockpit contient maintenant `relational_gravity`, mais le dernier runtime a montré :

```text
cross_tf_state = RELATIONAL_GRAVITY_MIXED
dominant_direction = DOWN
dominant_leader = USD
dominant_antagonist = AUD/GBP/USD/CAD
aligned_tfs = [1, 5]
counter_tf = 15
```

Détail :

```text
M1  DOWN | leader USD | score 0.787 | HIGH
M5  DOWN | leader CHF | score 0.556 | MEDIUM
M15 UP   | leader CHF | score 0.871 | HIGH
```

Problème :

```text
USD apparaît comme leader dominant ET dans les antagonistes.
Un champ MIXED ne doit pas produire un leader top-level fiable.
```

Donc :

```text
P1.2 Bridge Guard obligatoire avant P2.
```

---

# 4. Nouvelles briques orchestrales validées (07/05)

## pf_force_inflection.py V0.1

Rôle :

```text
Détecter les pliures contresens par devise par TF.
```

Concepts :

```text
PLIURE                     Changement brutal d'angle contresens (sign flip + delta)
CONTRESENS_PLIURE_UP       Devise descendante plie brutalement vers haut
CONTRESENS_PLIURE_DOWN     Devise montante plie brutalement vers bas
SAME_DIRECTION_INFLECTION  Changement angle fort même sens
Sévérité : MICRO / MODERATE / BRUTAL / EXTREME
```

Validation DB 06/05 :

```text
07:30  CAD  CONTRESENS_PLIURE_DOWN  Δ-74.7°  EXTREME  — crash Acte 1
08:00  GBP  CONTRESENS_PLIURE_UP    Δ+44.1°  BRUTAL   — rebond birth GBP
11:00  GBP  CONTRESENS_PLIURE_DOWN  Δ-32.3°  MODERATE — pivot Acte 1→2
```

---

## pf_force_extrema.py V0.1

Rôle :

```text
Détecter valleys/peaks avec asymétrie entrée/sortie.
```

Concepts :

```text
VALLEY                    Minimum local qualifié (amplitude >= seuil par TF)
PEAK                      Maximum local qualifié
AMPLITUDE                 Profondeur valley ou hauteur peak
SLOW_ENTRY_FAST_EXIT      Énergie accumulée, libération explosive
FAST_ENTRY_SLOW_EXIT      Impulsion puis absorption
BALANCED                  Entrée/sortie symétriques
FAST_ENTRY_FAST_EXIT      Passage rapide, peu d'intérêt
```

Validation DB 06/05 :

```text
07:15  CAD  PEAK    amplitude=23.2  SLOW_ENTRY_FAST_EXIT  — chute explosive après
10:45  JPY  VALLEY  amplitude=10.5  FAST_ENTRY_SLOW_EXIT  — absorption JPY
14:45  EUR  PEAK    amplitude=12.8  SLOW_ENTRY_FAST_EXIT  — rotation après
```

---

## pf_orchestral_gravity.py V0.2

Rôle :

```text
Lire les relations vivantes entre devises : qui mène, qui suit, qui résiste, qui croise.
```

Concepts :

```text
ORCHESTRAL_GRAVITY         Carte des rôles et relations multi-devise
LEADER (orchestral)        Devise angle le plus fort MAINTENANT
FOLLOWER (orchestral)      Devise même direction, retard ou force moindre
ANTAGONIST (orchestral)    Devise direction opposée au leader
LAGGING                    Attiré mais trop faible pour être FOLLOWER
COALITION_UP/DOWN          Groupe devises même direction
CROSSING_ZONE              Deux devises niveaux proches
ATTRACTION_STRENGTH        Force attraction follower → leader
```

Patterns nommés :

```text
JPY_GRAVITY_PULLING_{X}_{Y}
LEADER_{X}_ACCUMULATING_ZONE
LEADER_{X}_RUPTURE_BREAKOUT
ANTAGONIST_{X}_RUPTURE
USD_CAD_SYNCHRO_DOWN_COALITION
GBP_EUR_RECOVERY_WAVE
CROSSING_IMMINENT_{A}_{B}
BIPOLAR_FIELD_ACTIVE
ORCHESTRAL_COMPRESSION
```

Validation DB 06/05 fin de journée H1 :

```text
LEADER  : USD (+5.6° [EARLY_EXTREME z=+2.11 t=1.9])
NEUTRAL : GBP, EUR, JPY, CAD, CHF, AUD
CROSSING_IMMINENT : USD↔CHF, USD↔AUD, EUR↔JPY
PATTERN : ORCHESTRAL_COMPRESSION
```

---

## run_orchestral_analysis_once.py

Rôle :

```text
Combiner inflection + extrema + orchestral en un rapport complet.
```

Sorties :

```text
Markdown (.md) pour lecture humaine
JSON (.json) pour cockpit
```

Commande validée :

```powershell
python run_orchestral_analysis_once.py `
  --db powerflow.db `
  --start "2026-05-07T05:00:00+00:00" `
  --end "2026-05-07T21:00:00+00:00" `
  --tfs "15,60" --out output/orchestral_today.md
```

---

# 5. Priorité active — ORDONNÉE

```text
P0 — Synchroniser workspace IA avec ce CURRENT_STATE + CHECKPOINT
P1 — P1.2 Relational Gravity Bridge Guard (BLOCKER 🔴)
P2 — Relancer audit runtime Kinematics / Energy / Gravity
P3 — HTF_CONTEXT_STACK spec (W/D/H4/H1 explicit exposure)
P4 — Orchestral integration dans cockpit_agentic_state_v01.py
P5 — P2 Behavioral Mapper (INTERDIT avant P1.2)
P6 — Dashboard Sync relationnel + orchestral
P7 — Telegram (plus tard, après stabilisation)
```

---

# 6. Besoins primaires du trader — CLARIFIÉS

## Le trader ne veut pas :

```text
❌ Un dashboard M1-only
❌ Un lecteur de microfilm sans gravité HTF
❌ 40 panneaux sans hiérarchie
❌ Des alertes confuses sur champ MIXED
```

## Le trader veut :

```text
✅ Savoir où est la gravité HTF (W/D/H4/H1)
✅ Savoir si le marché est en retard sur cette gravité
✅ Voir quand le LTF commence à rattraper
✅ Savoir qui tire, qui suit, qui contredit
✅ Savoir si l'énergie supporte ou diverge
✅ Savoir si les relations sont cohérentes ou mixtes
✅ Savoir quoi surveiller ensuite (next watch)
```

## Alertes critiques attendues :

```text
HTF_WINDOW_ACTIVE
HTF_LAG_CATCHUP_START
M1_IGNITION_INSIDE_HTF_WINDOW
M5_RELAY_CONFIRMS_HTF_WINDOW
RELATIONAL_GRAVITY_MIXED_WARNING
FIRST_DETACHMENT_WITH_CLEAN_RELAY
ENERGY_DOES_NOT_SUPPORT_RELEASE
ORCHESTRAL_COMPRESSION_BEFORE_MOVE
LEADER_RUPTURE_BREAKOUT
SECOND_LEG_WATCH
```

---

# 7. Cockpit structure cible

```text
HTF Stack          W/D/H4/H1 contexte, gravité, retard
Tactical Stack     M15/M5/M1 fenêtre, relais, ignition
Node State         Temporal nodes + kinematics + release
Energy Alignment   Currency energy support/divergence
Relational Gravity Leaders/Followers/Mixed warnings
Orchestral Gravity Pliures/Valleys/Peaks/Coalitions
Behavioral Alerts  3-5 alertes max mode Trading
Next Watch         Quoi surveiller ensuite
```

Mode double recommandé :

```text
Trading Mode = simple / rapide / actionnable (3-5 alertes max)
Lab Mode     = profond / complet / exploration
```

---

# 8. Interdits critiques

```text
❌ Ne pas empiler les briques sans plan HTF
❌ Ne pas continuer P2 Behavioral Mapper avant P1.2
❌ Ne pas intégrer Telegram avant stabilisation
❌ Ne pas transformer dashboard en usine à gaz
❌ Ne pas ignorer le contexte HTF dans les nouvelles features
❌ Ne pas confondre ORCHESTRAL_GRAVITY avec signal
❌ Ne pas réduire PowerFlow à M1/M5/M15
```

---

# 9. Phrase de reprise

```text
PowerFlow ne doit pas regarder seulement le microfilm.
PowerFlow doit lire le film HTF en retard,
puis détecter quand le LTF commence à le rattraper.
```

```text
Kinematics dit comment ça bouge.
Energy dit si le champ est vivant.
Relational Gravity dit comment les acteurs se tiennent.
Orchestral Gravity dit qui mène, qui plie, qui croise.
Behavioral Flow doit alerter seulement quand ces lectures sont qualifiées.
```

---

# 10. Message workspace multi-IA

À transmettre à tous les workspaces (Claude / GPT / Perplexity / Gemini) :

```text
CORRECTION MAJEURE DOCTRINE :
Le trader scalpe / trade court terme,
mais son analyse primaire est HTF : W, D, H4, H1.

Le LTF n'est pas la doctrine complète.
Le LTF sert à détecter l'ignition, le rattrapage ou l'invalidation d'une fenêtre HTF retardée.

Ne pas réduire PowerFlow à M1/M5/M15.
Construire PowerFlow comme :

HTF Context Stack (W/D/H4/H1)
→ Tactical Window (M15)
→ Node / Kinematics (M5/M1)
→ Energy Alignment
→ Relational Gravity
→ Orchestral Gravity
→ Behavioral Alerts
→ Trader Decision.

BLOCKER ACTUEL :
P1.2 Relational Gravity Bridge Guard.
P2 interdit tant que le bridge mixed peut raconter un leader clair.

NOUVELLES BRIQUES VALIDÉES 07/05 :
Orchestral Gravity V0.2 (inflection + extrema + orchestral).

PRIORITÉ ACTIVE :
1. P1.2 fix
2. Audit runtime
3. HTF_CONTEXT_STACK spec
4. Orchestral integration cockpit
```

---

**FIN CURRENT_STATE V3 — 2026-05-07**
