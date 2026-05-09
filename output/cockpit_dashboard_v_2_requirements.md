# COCKPIT DASHBOARD V2 REQUIREMENTS — PowerFlow V6

Date : 2026-05-02  
Statut : CAHIER DES CHARGES D’AFFICHAGE — PAS DE CODAGE INTERFACE IMMÉDIAT

---

## 1. Décision centrale

Le Dashboard V2 ne doit pas être une simple refonte visuelle.

Il doit devenir une lecture cockpit cohérente du champ PowerFlow.

Phrase noyau :

```text
L’ancien dashboard affichait les signaux.
Le nouveau dashboard doit afficher les fenêtres potentielles en préparation.
```

Le but n’est pas encore de déclarer une fenêtre active.

Le but est de montrer :

```text
ce qui se prépare
où la tension se concentre
qui mène
qui répond
qui reste en retard
sur quel profil temps la scène respire
```

---

## 2. Position actuelle

Déjà validé :

```text
core cleanup
cockpit field
battlefield radar
personality → zone bridge
lexique master
```

Fondation active :

```text
pf_personalities.py
→ pf_zone_dynamics.py
```

Chaîne cockpit validée :

```text
pf_zone_dynamics.py
→ pf_zone_context_logger.py
→ pf_zone_evolution_reader.py
→ pf_fractal_zone_stack.py
→ pf_session_zone_reader.py
→ pf_powerflow_zone_brief.py
→ pf_battlefield_map.py
→ pf_cockpit_field.py
```

Chaîne radar validée :

```text
pf_coalitions.py
→ pf_coalition_relations.py
→ pf_battlefield_radar.py
```

Stand-by :

```text
pf_temporal_density.py
TemporalWindowActive
Temporal Nodes Telegram
```

---

## 3. Rôle du Dashboard V2

Le Dashboard V2 doit afficher une vue globale de lecture.

Il doit répondre vite à ces questions :

```text
1. Quel est le champ dominant actuel ?
2. Quelle bataille se prépare ?
3. Quelles devises mènent ?
4. Quelles devises répondent en dernier ?
5. Où sont les zones chargées ?
6. Où sont les champs bipolaires ?
7. Quel profil temps porte la scène ?
8. Est-ce une scène courte, moyenne ou HTF ?
9. Est-ce un champ en préparation ou une release déjà visible ?
10. Qu’est-ce qui doit être regardé maintenant ?
```

---

## 4. Ce que le Dashboard V2 ne doit pas faire maintenant

Interdits temporaires :

```text
déclarer TemporalWindowActive
envoyer Telegram
brancher NODE_COMPLET_FULL
brancher NODE_REPULSION
forcer une direction trade
remplacer le Lab
remplacer le cahier des charges TemporalDensity
```

Le Dashboard V2 montre le champ.

Il ne doit pas encore :

```text
ouvrir officiellement la fenêtre
```

---

## 5. Sources d’information à afficher

### Source A — Cockpit Field

Fichier / module :

```text
pf_cockpit_field.py
run_cockpit_field.py
cockpit_field.txt
```

Affiche :

```text
FIELD
DOMINANT
OPPOSITE / CONTEXT
CONTESTED_WINDOW
BIPOLAR_FOCUS
BIPOLAR_LIST
```

Rôle :

```text
vue courte du champ utile
```

---

### Source B — Battlefield Radar

Fichier / module :

```text
pf_battlefield_radar.py
run_battlefield_radar_once.py
```

Affiche :

```text
bataille relationnelle prioritaire
batailles secondaires
coalitions fortes à surveiller
strategic_score
```

Rôle :

```text
hiérarchiser les scènes d’intérêt
```

Phrase :

```text
BattlefieldRadar ne dit pas “la fenêtre est ouverte”.
Il dit “ici, une bataille se prépare”.
```

---

### Source C — Zone Brief / Battlefield Map

Fichiers / modules :

```text
pf_powerflow_zone_brief.py
pf_battlefield_map.py
```

Affiche :

```text
zones en release
zones en préparation
coalitions HIGH
coalitions LOW
fenêtre contestée
champs bipolaires
```

Rôle :

```text
cartographier les camps et la dynamique de zone
```

---

### Source D — Personality / Zone Bridge

Fichiers :

```text
pf_personalities.py
pf_zone_dynamics.py
test_pf_personality_zone_bridge.py
```

Affiche plus tard :

```text
Z-score actuel par devise
state de zone par devise
tension_score
pullbacks absorbés
```

Rôle :

```text
fondation organique interne
```

À ne pas surcharger visuellement.

Cette source doit nourrir des résumés, pas devenir un tableau illisible.

---

## 6. Structure visuelle recommandée

Dashboard V2 doit avoir 5 blocs principaux.

```text
A. FIELD GLOBAL
B. RADAR DES BATAILLES
C. PROFILS TEMPS
D. DEVISES LEADER / LAST ACTOR / BIPOLAIRES
E. WATCHLIST COCKPIT
```

---

## 7. Bloc A — FIELD GLOBAL

Objectif :

```text
voir immédiatement le champ dominant
```

Contenu :

```text
FIELD
session
score
DOMINANT
OPPOSITE / CONTEXT
CONTESTED_WINDOW
BIPOLAR_FOCUS
```

Exemple :

```text
FIELD: TACTICAL_RELEASE_BATTLEFIELD | session=LATE_US
DOMINANT: CAD/GBP release HIGH M1/M5
CONTEXT: EUR/GBP/CHF/CAD/JPY LOW prep
CONTESTED: HIGH coalition vs LOW prep
BIPOLAR: EUR micro HIGH vs scenario LOW
```

Lecture :

```text
le cockpit montre l’état du champ en une respiration
```

---

## 8. Bloc B — RADAR DES BATAILLES

Objectif :

```text
voir les scènes d’intérêt en préparation
```

Contenu :

```text
bataille prioritaire
batailles secondaires
coalitions fortes
antagoniste répété
strategic_score
```

Exemple :

```text
PRIORITY: TF30 AUD+GBP vs EUR — BATTLE_FORMING — field=0.60
SECONDARY: TF15 AUD+CAD vs JPY — BATTLE_FORMING — field=0.57
SECONDARY: TF15 CAD+GBP vs JPY — BATTLE_PREPARING — field=0.54
WATCH: TF1 CHF+EUR — COALITION_FIELD_STRONG — cohesion=0.94
```

Lecture :

```text
le radar dit où regarder
pas encore quoi déclencher
```

---

## 9. Bloc C — PROFILS TEMPS

Objectif :

```text
voir sur quel horizon la scène existe
```

Profils :

```text
MICRO  : M1
SHORT  : M1/M5/M15
MEDIUM : M15/M30/H1
LONG   : H4/D1/W1 futur
```

Affichage recommandé :

```text
MICRO  : naissance / release locale / bruit utile
SHORT  : timing tactique / deuxième jambe
MEDIUM : scénario / bataille / champ porteur
LONG   : gravité future, pas encore mûre
```

Règle :

```text
M1 ne commande jamais seul.
M1 révèle la naissance.
M5 donne timing tactique.
M15/M30/H1 portent le scénario.
```

---

## 10. Bloc D — LEADERS / LAST ACTORS / BIPOLAIRES

Objectif :

```text
voir les acteurs du champ
```

Contenu :

```text
leader devise
leader coalition
antagoniste principal
last actor / dernier acteur
bipolar focus
bipolar list
```

Lectures utiles :

```text
qui impose le mouvement ?
qui répond en dernier ?
qui reste tiraillé entre micro et HTF ?
qui est en release courte contre préparation HTF ?
```

Codes bipolaires :

```text
PREPH = préparation HIGH
PREPL = préparation LOW
RELH  = release HIGH
RELL  = release LOW
```

---

## 11. Bloc E — WATCHLIST COCKPIT

Objectif :

```text
afficher seulement ce qui mérite attention
```

La watchlist doit contenir :

```text
1 à 3 batailles prioritaires
1 à 3 devises bipolaires
1 champ dominant
1 contexte opposé
1 note de vigilance temporelle
```

Elle ne doit pas contenir :

```text
20 lignes de détails
chaque devise brute
chaque micro-signal
chaque node non validé
```

Phrase :

```text
Le cockpit réduit la charge mentale.
Il ne recrée pas la DB à l’écran.
```

---

## 12. États d’affichage proposés

### FIELD_CLEAR

Champ lisible.

```text
une structure dominante apparaît
```

### FIELD_CONTESTED

Champ contesté.

```text
HIGH et LOW coexistent
```

### BATTLE_PREPARING

Bataille en préparation.

```text
relation active visible
```

### BATTLE_FORMING

Bataille qui devient lisible.

```text
relation prioritaire plus propre
```

### BIPOLAR_ROTATION_WATCH

Devise bipolaire à surveiller.

```text
micro vs HTF
release vs preparation
```

### DATA_STALE

DB trop vieille.

```text
ne pas interpréter le champ
```

### LAB_STANDBY

Brique visible mais non activée.

```text
Temporal Nodes / TemporalDensity / TemporalWindowActive non branchés
```

---

## 13. Couleurs / intensités conceptuelles

Pas de design imposé maintenant.

Mais l’intensité devrait suivre :

```text
gris    → neutre / absent
bleu    → watch / préparation
orange  → formation / tension lisible
rouge   → pression forte / rupture / release
violet  → bipolarité / rotation interne
```

À garder simple.

But :

```text
comprendre en 3 secondes
```

---

## 14. Données minimales à produire pour l’interface

Le Dashboard V2 aura besoin d’un JSON stable.

Nom futur possible :

```text
output/cockpit_dashboard_v2_state.json
```

Structure cible :

```json
{
  "version": "COCKPIT_DASHBOARD_V2",
  "generated_at": "...",
  "symbol": "GBPUSD",
  "freshness": "FRESH",
  "field": {
    "type": "TACTICAL_RELEASE_BATTLEFIELD",
    "session": "LATE_US",
    "score": 257.063,
    "dominant": "CAD/GBP release HIGH M1/M5",
    "context": "EUR/GBP/CHF/CAD/JPY LOW prep",
    "contested_window": "HIGH vs LOW",
    "bipolar_focus": "EUR"
  },
  "radar": {
    "priority_battle": "TF30 AUD+GBP vs EUR",
    "secondary_battles": [],
    "coalitions_watch": []
  },
  "time_profiles": {
    "micro": [],
    "short": [],
    "medium": [],
    "long": []
  },
  "actors": {
    "leaders": [],
    "last_actors": [],
    "antagonists": [],
    "bipolars": []
  },
  "watchlist": []
}
```

---

## 15. Interface legacy actuelle

Fichiers existants :

```text
dashboard_server.py
dashboard_live.html
cockpit_reader.py
cockpit_terminal.py
START.py
```

Statut :

```text
COCKPIT_PROTOTYPE_LEGACY
```

Ne pas supprimer.

Mais ne pas refondre brutalement.

Approche future :

```text
1. créer un JSON V2 stable
2. lire ce JSON dans dashboard_live.html ou nouvelle page
3. seulement après modifier l’interface
```

---

## 16. Ordre de développement futur recommandé

### Étape 1 — State Builder V2

Créer plus tard :

```text
pf_cockpit_dashboard_state.py
```

Mission :

```text
agréger cockpit_field + battlefield_radar + zone brief + freshness
produire output/cockpit_dashboard_v2_state.json
```

### Étape 2 — Runner

Créer plus tard :

```text
run_cockpit_dashboard_state.py
```

Mission :

```text
générer le JSON dashboard V2
```

### Étape 3 — Watch mode

Ajouter :

```text
--watch
--interval-seconds
```

### Étape 4 — Interface

Modifier ou remplacer :

```text
dashboard_live.html
```

seulement quand le JSON est stable.

---

## 17. Ce qui doit rester hors dashboard pour l’instant

```text
TemporalWindowActive
TemporalDensity score final
Temporal Nodes Telegram
NODE_COMPLET_FULL
NODE_REPULSION
signaux non validés Lab
```

Le Dashboard peut afficher :

```text
LAB_STANDBY
```

mais ne doit pas les utiliser comme moteur de décision.

---

## 18. Critères de réussite Dashboard V2

Le Dashboard V2 est réussi si en quelques secondes on voit :

```text
le champ dominant
la bataille prioritaire
le contexte opposé
la devise bipolaire principale
le profil temps porteur
la watchlist utile
```

Il échoue si :

```text
il affiche trop de lignes
il mélange signal et scène
il confond radar et fenêtre active
il enterre les leaders dans du bruit
il force une décision au lieu de montrer le champ
```

---

## 19. Phrase cockpit finale

Le Dashboard V2 doit pouvoir résumer une scène comme :

```text
Late US : champ tactique haut actif.
CAD/GBP libèrent haut en M1/M5.
EUR est bipolaire : micro haut contre scénario bas M15/M30.
JPY est contesté plusieurs fois par blocs bas M15.
Fenêtre potentielle en préparation, pas encore TemporalWindowActive.
```

---

## 20. Prochaine action après ce document

Créer :

```text
CHECKPOINT_MISSION_FOUNDATION_OK.md
```

Puis seulement après :

```text
optionnel : pf_cockpit_dashboard_state.py SPEC
```

Pas de code interface encore.

---

## 30. Verdict PowerFlow

```text
Le Dashboard V2 doit devenir un radar de champ.
Pas une usine à signaux.
Pas encore une fenêtre active.
```

Priorité :

```text
voir clair
réduire la charge mentale
préparer TemporalDensity sans la précipiter
```

Fin du cahier des charges Dashboard V2.

