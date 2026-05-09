# LAB_004 — TEMPORAL WINDOW FRACTAL IMBRICATION

**Date :** 2026-05-04  
**Symbole :** GBPUSD  
**Fenêtre principale DB :** 09:00 → 10:15  
**Statut :** VALIDÉ TRADER  
**Type :** Lab de fenêtre temporelle fractale  
**Sous-pattern interne :** Gravity Respring / Multi-currency layer  
**Mode DB :** legacy force-only pour la fenêtre historique du matin  
**Screens fournis :** Weekly, Daily, H4, H1, M30, M15, M5  
**M1 visuel :** indisponible au-delà de 4h, mais DB M1 exploitable

---

## 1. Phrase noyau

```text
Un node n’est pas seulement un croisement.
C’est un ancrage énergétique qui permet à plusieurs timeframes de s’imbriquer dans une histoire supérieure.
```

Ce Lab valide une couche plus haute que le simple pattern `GRAVITY_RESPRING_NODE`.

Le vrai objet du Lab est :

```text
une fenêtre temporelle fractale
où HTF / M15 / M5 / DB M1 s’imbriquent
avec compression et étirement du temps
couche multidevise
tempo propre par devise
et confirmation tardive H4 possible
```

---

## 2. Hypothèse centrale

```text
Une fenêtre temporelle fractale apparaît quand un node énergétique local s’insère dans une structure HTF déjà chargée,
avec compression / étirement du temps, corrélation multidevise, tempo propre par devise et confirmation tardive sur timeframe supérieur.
```

Le marché ne déroule pas une scène à vitesse constante.

Il peut :

```text
compresser une phase
étirer une respiration
retarder une confirmation
faire naître une scène en LTF
la confirmer plus tard en HTF
absorber un contre-mouvement
préparer une deuxième jambe
```

---

## 3. Lecture DB validée

Commande validée :

```powershell
python run_scene_report_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --timeframes 1,5,15 --out scene_report_lab004.txt
```

Film extrait automatiquement :

```text
09:00→09:20 PRE_FIELD
09:21→09:28 NODE_BIRTH
09:30→09:48 CONFIRMATION
09:48→10:01 COUNTER_BREATH
10:02→10:08 ABSORPTION
```

Scène nommée :

```text
GRAVITY_RESPRING_NODE
```

État :

```text
WINDOW_ACTIVE_AFTER_BREATH
dominant_phase = ABSORPTION
next_watch = WATCH_SECOND_LEG
```

Bloc dominant DB :

```text
JPY + CAD + USD respring
contre
EUR + GBP + AUD + CHF fold
```

---

## 4. Lecture visuelle HTF

Les screens Weekly / Daily / H4 / H1 montrent que la fenêtre n’apparaît pas dans le vide.

Le contexte HTF contient déjà :

```text
une gravité de fond
une compression ou pré-organisation
des courbes qui convergent
des acteurs qui préparent une zone de croisement
un H4 qui confirme tardivement une structure déjà travaillée en dessous
```

Concept validé :

```text
HTF_PRE_NODE_FIELD
```

Définition :

```text
Champ HTF où les devises convergent ou se rapprochent avant que le vrai node tactique ne soit visible en M15/M5.
```

---

## 5. H4 : confirmation tardive ou relais

Observation trader :

```text
Le croisement / node H4 arrive alors que les mouvements forts ont déjà commencé sur les timeframes inférieurs.
```

Concept validé :

```text
H4_CROSS_CONFIRMATION_LATE
```

Définition :

```text
Le H4 ne donne pas la naissance.
Il confirme ou relaie une structure déjà préparée en LTF.
```

Nuance importante :

```text
H4 peut être à la fois confirmation tardive du chapitre précédent
et relais vers le chapitre suivant.
```

Donc PowerFlow ne doit pas attendre le H4 pour voir le départ.

Lecture correcte :

```text
M5/M15 = naissance / activation tactique
H4 = confirmation / relais / histoire supérieure
```

---

## 6. M30 / M15 : scène de bataille

Sur M30 / M15, la fenêtre du Lab devient lisible comme scène.

Lecture :

```text
compression / recentrage
bascule de forces
séparation de blocs
respiration contraire
absorption
```

La DB confirme cette structure :

```text
PRE_FIELD
→ NODE_BIRTH
→ CONFIRMATION
→ COUNTER_BREATH
→ ABSORPTION
```

Concept validé :

```text
M15_SCENE_BUILDING
```

Définition :

```text
Le M15 ne donne pas toujours le point de naissance.
Il raconte la scène tactique en construction.
```

---

## 7. M5 : timing tactique

Sur M5, la fenêtre montre la naissance plus clairement.

Concept validé :

```text
M5_TACTICAL_NODE_BIRTH
```

Définition :

```text
Moment où le timing tactique révèle la naissance du node dans une fenêtre déjà portée par une scène supérieure.
```

La DB confirme :

```text
NODE_BIRTH = PRICE_LAG
CONFIRMATION = PRICE_PAYING
```

Concept validé :

```text
PRICE_LAG_THEN_CATCHUP
```

Définition :

```text
Les forces bougent avant le prix.
Le prix reste retenu puis rattrape.
```

---

## 8. M1

Le M1 visuel n’est pas disponible au-delà de 4h.

Mais la DB M1 a permis la lecture microfilm du matin.

Conclusion :

```text
Pour ce Lab, M1 visuel est bonus.
M5 + DB M1 suffisent à documenter la naissance tactique.
```

Règle retenue :

```text
M1 bavarde hors fenêtre.
M1 révèle la naissance dans la bonne fenêtre.
```

---

## 9. Couche multidevise

Légende fournie :

```text
GBP = orange
USD = cyan
EUR = vert
AUD = rouge
JPY = magenta
CHF = blanc
CAD = jaune
```

Lecture du Lab :

```text
La Gravity Family n’est pas le Lab entier.
Elle est une couche de corrélation multidevise à l’intérieur de la fenêtre temporelle.
```

Bloc principal DB :

```text
JPY + CAD + USD
contre
EUR + GBP + AUD + CHF
```

Mais la lecture correcte n’est pas un bloc rigide.

Il faut lire :

```text
qui impulse
qui suit
qui lag
qui absorbe
qui confirme
qui relaie
```

---

## 10. Tempo par devise

### USD

```text
Pivot gravitaire / colonne structurante.
Peut confirmer ou porter l’inertie du champ.
```

### CAD

```text
Renfort / accompagnement de structure.
Peut devancer ou confirmer USD selon le contexte.
```

### JPY

```text
Acteur rapide / nerveux / accélérant.
Peut déclencher ou rendre visible la rotation tactique.
```

### GBP

```text
Acteur central du cross GBPUSD.
Fragilité ou tension lisible dans la fenêtre.
```

### EUR

```text
Relais / couche intermédiaire.
Peut confirmer, retarder ou créer une contradiction de champ.
```

### AUD

```text
Composante risk / volatile.
Peut plier ou participer à une rotation variante.
```

### CHF

```text
Refuge lent / acteur de retenue ou de confirmation.
Son tempo peut être décalé.
```

### NZD

```text
Absent du legacy morning force-only.
À intégrer dans V2 extended.
```

---

## 11. Temporalité : compression et étirement

Concept validé :

```text
TEMPORAL_ELASTICITY_FIELD
```

Définition :

```text
Champ où le temps du marché se comprime ou s’étire pour orchestrer plusieurs comportements stratégiques dans une même fenêtre.
```

Deux modes :

```text
TIME_COMPRESSION_PHASE
→ beaucoup d’information / force / bascule sur peu de bougies

TIME_STRETCHING_PHASE
→ respiration plus longue permettant aux scènes de s’imbriquer
```

Dans LAB_004 :

```text
NODE_BIRTH = phase compressée
COUNTER_BREATH / ABSORPTION = phase étirée / rééquilibrage
H4 = confirmation ou relais tardif
```

---

## 12. Node énergétique

Concept validé :

```text
ENERGETIC_NODE_ANCHOR
```

Définition :

```text
Un node est un point d’énergie où plusieurs forces se croisent, se disjoignent ou se redistribuent.
Il peut naître en LTF, être confirmé tardivement en HTF, puis s’affirmer en amplitude sur Daily / Weekly.
```

Ce n’est pas un simple cross géométrique.

Rappel doctrine :

```text
Cross sans tension préalable = bruit.
Node avec tension + ordre des acteurs + densité + imbrication = scène d’intérêt stratégique.
```

---

## 13. Fabrication du temps

Concept validé :

```text
TIME_FABRICATION_FIELD
```

Définition :

```text
Organisation progressive du temps par le marché pour permettre à plusieurs scènes locales de s’insérer dans une histoire supérieure.
```

Phrase trader filtrée :

```text
Les mouvements ne se font pas à n’importe quel moment.
Il y a une orchestration.
```

Lecture PowerFlow :

```text
Le marché fabrique le timing de ses chapitres.
```

---

## 14. Contradictions fractales

Concept validé :

```text
FRACTAL_CONTRADICTION_FIELD
```

Définition :

```text
État où plusieurs timeframes racontent des phases différentes de la même histoire.
Le LTF peut montrer la naissance.
Le M15 peut sembler plat.
Le H4 peut confirmer tardivement.
Le Daily peut porter l’amplitude longue.
```

Conclusion :

```text
Contradiction timeframe ≠ invalidation.
Elle peut être un emboîtement de chapitres.
```

---

## 15. M15 plat / microstructure cachée

Concept validé :

```text
FLAT_SCENE_HIDDEN_MICROSTRUCTURE
```

Définition :

```text
Une scène plate en M15 peut contenir une microstructure vivante en M5/M1.
Le plat n’est pas forcément mort.
Il peut être une fabrication lente de direction.
```

Rappel :

```text
plat + micro-mouvements vivants = élastique chargé possible
```

---

## 16. Amplitude temporelle

Concept validé :

```text
TIME_AMPLITUDE_COLLAPSE
```

Définition :

```text
Phase où une fenêtre courte concentre une amplitude normalement répartie sur une période beaucoup plus longue.
```

Exemples conceptuels :

```text
une journée contient l’énergie d’une semaine
une session contient une amplitude mensuelle
une bougie HTF confirme après coup une fabrication LTF
```

---

## 17. Mur haut / mur bas

Concept validé :

```text
TEMPORAL_WALL_FIELD
```

Définition :

```text
Borne de force/prix où le marché retient la libération et force une respiration ou un rééquilibrage.
```

Ce n’est pas un range classique.

C’est plutôt :

```text
mur de forces
bassin temporel
champ de retenue
```

---

## 18. Histoire supérieure

Concept validé :

```text
HIGHER_STORY_FIELD
```

Définition :

```text
Histoire portée par les timeframes supérieurs dans laquelle les scènes M15/M5/M1 viennent s’insérer.
```

LAB_004 est une scène locale dans une histoire supérieure.

---

## 19. Orchestration stratégique

Concept validé :

```text
STRATEGIC_TEMPORAL_ORCHESTRATION
```

Définition :

```text
Organisation de comportements d’intérêt stratégique dans le temps :
compression, attente, node, respiration, confirmation, absorption, relais HTF.
```

Ce n’est pas un signal.

C’est une mise en scène du flux.

---

## 20. Comparaison avec fenêtres historiques

Deux fenêtres historiques ont été validées par scan DB.

### MATCH FORT — 2026-05-01 08:00 → 09:30

```text
GRAVITY_RESPRING_NODE
JPY+CAD+USD vs EUR+GBP+CHF+AUD
WINDOW_ACTIVE_AFTER_BREATH
WATCH_SECOND_LEG
```

Film :

```text
08:00→08:03 NODE_BIRTH
08:24→08:44 CONFIRMATION
09:09→09:25 COUNTER_BREATH
09:25→09:30 ABSORPTION
```

Classement :

```text
LAB_MATCH_FORT
```

### VARIANTE — 2026-04-30 17:30 → 19:00

```text
GRAVITY_RESPRING_NODE
AUD+CAD+CHF+JPY vs EUR+USD+GBP
WINDOW_ACTIVE_AFTER_BREATH
WATCH_SECOND_LEG
```

Film :

```text
17:30→17:38 PRE_FIELD
17:39→17:46 NODE_BIRTH
17:48→18:01 CONFIRMATION
18:02→18:21 COUNTER_BREATH
18:21→18:36 ABSORPTION
```

Classement :

```text
LAB_MATCH_PARTIEL / RAW_VARIANT_ROTATION
```

---

## 21. Ce que les agents doivent apprendre

### Agent 1 — DBVisionGuard

```text
la DB voit vraiment
les gaps sont connus
legacy vs v2 est distingué
```

### Agent 2 — FlowEventExtractor

```text
PRE_FIELD
NODE_BIRTH
CONFIRMATION
COUNTER_BREATH
ABSORPTION
SECOND_LEG
```

Règle critique :

```text
Une respiration contraire ne doit pas voler le node principal.
```

### Agent 3 — SceneNamer

```text
GRAVITY_RESPRING_NODE
RAW_NODE_BIRTH
WINDOW_ACTIVE_AFTER_BREATH
WATCH_SECOND_LEG
```

### Agent 4 — WeeklyAgentScan / LabCandidateScanner

```text
fenêtres répétables
clusters propres
candidats Lab
variantes
```

---

## 22. Prochain agent à coder

Nom :

```text
FractalWindowEngine V0.1
```

Mission :

```text
relier événements LTF et contexte HTF
qualifier compression / étirement du temps
détecter confirmation H4 tardive
classer les contradictions fractales
```

Sorties futures :

```text
HTF_PRE_NODE_FIELD
LTF_BIRTH_ACTIVE
H4_CROSS_CONFIRMATION_LATE
FRACTAL_CONTRADICTION_FIELD
TIME_COMPRESSION_PHASE
TIME_STRETCHING_PHASE
HIGHER_STORY_FIELD
```

---

## 23. Métriques DB futures

```text
event_density_per_window
force_energy_per_minute
multi_currency_sync_count
tf_lag_minutes
leader_follower_delay
price_lag_minutes
breath_duration
absorption_strength
htf_confirmation_delay
amplitude_vs_baseline
zone_disjunction_score
htf_relay_score
```

---

## 24. Conclusion

LAB_004 est validé comme :

```text
LAB_004_TEMPORAL_WINDOW_FRACTAL_IMBRICATION
```

Nature :

```text
fenêtre temporelle fractale
node énergétique
imbrication HTF/LTF
couche multidevise
tempo par devise
sous-pattern Gravity Respring
fabrication du temps
```

Verdict :

```text
Ce Lab donne de la matière aux agents.
Il transforme une intuition visuelle en structure testable :
DB → film → scène → fractalité → histoire supérieure.
```

Fin du Lab.
