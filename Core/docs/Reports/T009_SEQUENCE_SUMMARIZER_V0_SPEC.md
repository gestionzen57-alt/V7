# T009_SEQUENCE_SUMMARIZER_V0_1_V1_V2_V3_SPEC

## Objectif

Etendre `T009 Sequence Summarizer V0` vers une lecture B9 complete en quatre paliers propres :

1. **V0.1 DB / replay validation** : verifier que la sortie automatique reste lisible sur des packs reels ou rejoues.
2. **V1 Why/How** : expliquer ce qui se passe, pourquoi cela compte et comment B9 le detecte.
3. **V2 Scene Causality** : relier les moments en cause, reaction, consequence et deplacement memoire.
4. **V3 Fractal Scene** : relier microfilm, moment, scene et chapitre de session.

Phrase de cap :

```text
B9 ne cherche pas le signal. B9 cherche la trace laissee par l'effort.
```

Phrase de controle :

```text
Ne lis pas l'absorption comme une direction. Lis ou elle deplace la memoire.
```

## Contraintes

- Read-only.
- Aucune ecriture `powerflow.db`.
- Aucune ecriture `tick_archive.db`.
- Aucun moteur modifie.
- Aucun Telegram.
- Aucun dashboard.
- Aucun croisement B8 premature.
- Aucun ordre automatique.
- Rendu humain en francais.
- Source quality visible : `source_mode`, `data_visibility`, `confidence_cap`.
- Limites visibles : `M1_BAR_PROXY`, `RECONSTRUCTED`, `delta proxy`.

## Entrees / sorties

Entrees :

```text
battlefield_flux_state.json
battlefield_flux_events.json
```

Sorties :

```text
t009_sequence_summary.json
t009_sequence_summary.md
```

CLI :

```powershell
python Core/run_t009_sequence_summarizer_once.py `
  --state output_t009_sequence_replay\battlefield_flux_state.json `
  --events output_t009_sequence_replay\battlefield_flux_events.json `
  --output output_t009_sequence_summary
```

## Moments detectes

- `T009_MOMENT_EFFORT_WITHOUT_RESULT`
- `T009_MOMENT_ABSORPTION_SHELF`
- `T009_MOMENT_CENTER_MIGRATION_UP`
- `T009_MOMENT_CENTER_MIGRATION_DOWN`
- `T009_MOMENT_PROGRESSIVE_WAVE`
- `T009_MOMENT_CORRECTIVE_WAVE`
- `T009_MOMENT_BREAKOUT_PENDING_RETEST`
- `T009_MOMENT_BREAK_RETEST_FAILED`
- `T009_MOMENT_RETRACE_DECISION_AREA`
- `T009_MOMENT_FLOW_BREATHING`
- `T009_MOMENT_GENERIC_BATTLEFIELD`

## V1 — Why / How

Chaque moment contient maintenant :

```text
what_happens_fr
why_it_matters_fr
how_it_happened_fr
mechanism_fr
proof_summary_fr
```

Objectif : ne pas seulement nommer le moment, mais expliquer la situation.

## V2 — Scene Causality

Chaque moment contient maintenant :

```text
previous_context_fr
cause_fr
reaction_fr
consequence_fr
memory_shift_fr
retest_role_fr
```

Objectif : commencer a relier les moments entre eux.

Lecture cible :

```text
cause -> reaction -> consequence -> nouvelle memoire
```

## V3 — Fractal Scene

Chaque moment contient maintenant :

```text
scene_id
scene_role
parent_scene
child_moments
session_chapter
fractal_reading_fr
```

Chapitres de session :

- Ouverture / transition
- Construction de shelf
- Test / retest
- Migration de centre
- Respiration
- Essoufflement
- Decision de zone
- Memoire deplacee

## Algorithme de regroupement

V0/V3 conserve un regroupement simple et robuste :

```text
nouveau groupe si :
- gap temps > max_gap_sec
- ou distance centre > price_merge_pips
```

Valeurs par defaut :

```text
max_gap_sec = 300
price_merge_pips = 5.0
pip_size = 0.0001
```

## Classification V0/V3

Regles principales :

```text
absorption forte + failed displacement fort + centre peu mobile
-> Effort sans resultat

events nombreux + dwell/compression eleves + centre stable
-> Palier d'absorption

centre qui migre franchement
-> Vague progressive ou migration de centre

retour oppose apres extension
-> Vague corrective / zone de decision / retest echoue

groupe leger apres sequence dense, retour en zone
-> Respiration du flux
```

## Rendu Markdown

Le Markdown rend chaque moment avec :

- titre francais ;
- type interne ;
- scene et chapitre ;
- zone ;
- ce qui se passe ;
- pourquoi c'est important ;
- comment cela se produit ;
- mecanisme ;
- cause / reaction / consequence ;
- lecture fractale ;
- preuves ;
- limites.

## Limites

V3 reste heuristique.

Il ne pretend pas :

- lire le footprint raw tick complet si la source est `M1_BAR_PROXY` ;
- deduire un delta agressif reel si la source est reconstruite ;
- produire un ordre automatique ;
- croiser B9 avec B8 ;
- remplacer le trader.

## Tests

Commande :

```powershell
python -m py_compile Core/pf_t009_sequence_summarizer.py Core/run_t009_sequence_summarizer_once.py
python -m pytest Core/tests/test_t009_sequence_summarizer_v0.py -v
```

Couverture :

- chargement JSON vide ;
- JSON UTF-8 BOM ;
- normalisation event ;
- grouping temps/prix ;
- detection shelf ;
- migration UP/DOWN ;
- effort sans resultat ;
- validation London fixture ;
- rendu francais ;
- limites preservees ;
- champs V1 ;
- champs V2 ;
- champs V3 ;
- contrat summary ;
- export JSON / MD ;
- absence de termes d'ordre dans le rendu.

## Prochaines etapes

- Branch V0.1 : validation sur vrais replay packs London / Asia / Asia-London.
- V1+ : enrichir les phrases par type de scene avec exemples terrain.
- V2+ : durcir causalite de retest et deplacement memoire.
- V3+ : chaptering multi-timeframe quand B9 sera pret a dialoguer avec une couche superieure, sans croisement B8 premature.

## Addendum V0.1 — London validation hotfix

La V0.1 corrige une limite de la V0/V3 : la classification ne doit pas seulement comparer le premier et le dernier centre du groupe. Elle doit lire le chemin interne.

Nouveaux champs :

```text
center_min
center_max
center_range_pips
max_favorable_excursion_pips
max_adverse_excursion_pips
```

Temps historique :

```text
1. evidence.L1_raw.first_ts_utc
2. timestamp / ts_utc fallback
3. --replay-report pour shifted_start_utc -> original_start_utc
```

Règle de cap :

```text
Ne juge pas seulement le début et la fin. Lis le chemin du centre dans le groupe.
```
