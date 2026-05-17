# T009_SEQUENCE_SUMMARIZER_V0_SPEC

## Objectif

Créer une couche read-only PowerFlow T009/B9 qui transforme les events bruts du champ de bataille local en 5 à 8 moments lisibles.

Le Summarizer ne décide rien. Il ne produit pas d'ordre. Il ne parle pas au dashboard ni a Telegram. Il lit seulement les traces locales laissees par l'effort.

## Philosophie B9

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissee par l'effort.
```

Formule de lecture :

```text
event brut -> moment -> scene -> memoire de zone
```

La sortie doit rester en francais humain : ce qui se passe, pourquoi c'est important, comment B9 le voit, preuves, limites.

## Entrees / sorties

### Entrees

```text
battlefield_flux_state.json
battlefield_flux_events.json
```

Le code accepte aussi plusieurs variantes de structure JSON : liste directe d'events, dictionnaire avec `events`, `battlefield_events`, `t009_events`, `items` ou `data`.

### Sorties

```text
t009_sequence_summary.json
t009_sequence_summary.md
```

## Moments detectes

V0 sait classifier :

```text
T009_MOMENT_EFFORT_WITHOUT_RESULT
T009_MOMENT_ABSORPTION_SHELF
T009_MOMENT_CENTER_MIGRATION_UP
T009_MOMENT_CENTER_MIGRATION_DOWN
T009_MOMENT_PROGRESSIVE_WAVE
T009_MOMENT_CORRECTIVE_WAVE
T009_MOMENT_BREAKOUT_PENDING_RETEST
T009_MOMENT_BREAK_RETEST_FAILED
T009_MOMENT_RETRACE_DECISION_AREA
T009_MOMENT_FLOW_BREATHING
T009_MOMENT_GENERIC_BATTLEFIELD
```

## Rendu francais

Chaque moment contient :

```text
label_fr
reading_fr
why_it_matters_fr
how_detected_fr
evidence_fr
limits_fr
```

Exemple :

```text
Effort sans resultat
Le flux depense de l'energie, mais le centre de zone gagne peu de terrain.
```

## Algorithme de regroupement

1. Charger state/events.
2. Normaliser chaque event en `NormalizedEvent`.
3. Trier par timestamp UTC.
4. Regrouper selon :
   - `max_gap_sec`, defaut 300 secondes ;
   - `price_merge_pips`, defaut 5 pips.
5. Calculer les metriques par groupe.
6. Classifier chaque groupe en moment B9.
7. Exporter JSON + Markdown.

## Regles de classification V0

Regles simples, lisibles, volontairement imparfaites :

```text
absorption >= 0.70
+ failed_displacement >= 0.65
+ abs(center_delta_pips) < 3
=> T009_MOMENT_EFFORT_WITHOUT_RESULT

abs(center_delta_pips) < 2
+ event_count >= 4
+ dwell >= 0.75
+ compression >= 0.75
=> T009_MOMENT_ABSORPTION_SHELF

center_delta_pips >= +4
+ event_count >= 4
=> T009_MOMENT_PROGRESSIVE_WAVE ou CENTER_MIGRATION_UP

center_delta_pips <= -4
+ event_count >= 4
=> T009_MOMENT_CENTER_MIGRATION_DOWN

retour oppose apres extension
=> T009_MOMENT_CORRECTIVE_WAVE ou T009_MOMENT_BREAK_RETEST_FAILED

petit groupe apres groupe dense
+ retour dans zone precedente
=> T009_MOMENT_FLOW_BREATHING
```

## Limites

Le module expose toujours :

```text
source_mode
data_visibility
confidence_cap
```

Si la source est `M1_BAR_PROXY`, la sortie indique que la lecture est reconstruite et ne correspond pas a un footprint raw tick complet.

Si la visibilite est `RECONSTRUCTED`, la sortie indique que le microfilm est approxime.

La mention `delta proxy` est ajoutee pour eviter de confondre pression deduite et delta achat/vente reel.

## Tests

Fichier :

```text
Core/tests/test_t009_sequence_summarizer_v0.py
```

Commande :

```powershell
python -m pytest Core/tests/test_t009_sequence_summarizer_v0.py -v
```

Tests couverts :

```text
load empty events
normalisation robuste
regroupement temps/prix
absorption shelf
center migration up/down
effort without result
export JSON
export Markdown
source quality preserved
rendu francais
no BUY/SELL words
```

## CLI

Commande :

```powershell
python Core/run_t009_sequence_summarizer_once.py `
  --state output_t009_sequence_replay\battlefield_flux_state.json `
  --events output_t009_sequence_replay\battlefield_flux_events.json `
  --output output_t009_sequence_summary
```

Sorties :

```text
output_t009_sequence_summary\t009_sequence_summary.json
output_t009_sequence_summary\t009_sequence_summary.md
```

## Prochaines etapes V1 / V2 / V3

```text
V0 = lecture lisible et stable.
V1 = enrichir les explications why/how par role de zone.
V2 = causalite de scene : effort, resultat, retest, reaction.
V3 = fractalite microfilm -> moment -> scene -> session.
```

## Interdits respectes

```text
read-only
aucune ecriture DB
aucun moteur
aucun Telegram
aucun dashboard
aucun croisement B8
aucun ordre
```

