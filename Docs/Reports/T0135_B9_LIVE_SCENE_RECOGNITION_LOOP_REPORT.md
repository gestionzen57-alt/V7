# T0135 — B9 Live Scene Recognition Loop V0

## Résumé exécutif

T0135 assemble les briques B9/B6 déjà livrées dans une boucle CLI read-only : scène live B9, films B6 proches, contexte de faux positif, synthèse terrain et rapport français trader.

La boucle ne déclenche rien. Elle produit un paquet de reconnaissance exploitable par le trader et par les futures surfaces PowerFlow.

```text
B9 scène actuelle
→ B6 films proches
→ pièges techniques
→ synthèse terrain
→ brief de reconnaissance
```

## Doctrine

```text
B9 lit la scène.
B6 compare les films.
T0135 reconnaît une famille de scène.
Le trader décide.
```

Interdits : DB write, dashboard, Telegram, ordre d'exécution, taux de réussite.

## Entrées

- `--live-scene-json` : payload live compatible T0116 ou scène B9 enrichie.
- `--similarity-query-json` : résultat T0115.
- `--false-positive-json` : contexte T0117.
- `--terrain-synthesis-json` : synthèse T0118.
- `--french-report-json` : rapport T0134 optionnel.

## Sorties

```text
B9_LIVE_SCENE_RECOGNITION_LOOP_V0.json
B9_LIVE_SCENE_RECOGNITION_LOOP_V0.md
B9_LIVE_SCENE_RECOGNITION_MATCHES_V0.csv
B9_LIVE_SCENE_RECOGNITION_FLAGS_V0.csv
B9_LIVE_SCENE_RECOGNITION_LOOP_MANIFEST.json
B9_LIVE_SCENE_RECOGNITION_LOOP_V0.zip
```

## Validation sample

```text
recognition_state = B9_LIVE_SCENE_RECOGNITION_READY
match_count = 3
top_match_film_id = B6FC_20260514_1903_E8F0918A
cross_family_match_count = 0
low_trust_in_results = false
raw_unavailable_in_results = false
false_positive_context_available = true
terrain_synthesis_available = true
forbidden_language_hit_count = 0
```

## Limites techniques

- La boucle assemble des sorties existantes ; elle ne recalcule pas l'index B6.
- La similarité reste une proximité de lecture, pas une répétition certaine.
- Une scène proxy reste proxy même si elle ressemble à un film historique.
- Le retest non visible reste non visible.

## Prochaine brique

T0136 — Live Loop Runtime Wiring Guard V0 : vérifier comment brancher T0135 au runtime sans casser scheduler, cockpit ou Telegram.
