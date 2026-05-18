# T0133 — B9 Source Quality Hard Gate V0

## Phrase de cap

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l'effort.  
Une scène proxy ne devient jamais une vérité raw.

## Résumé exécutif

- Moments analysés : 5
- Raw claim allowed : 1
- Confirmation claim allowed : 2
- NUANCED promus à confirmed : 0
- RAW_UNAVAILABLE autorisés : 0

## Counts par état

- SOURCE_RAW_CONFIRMED: 2
- SOURCE_RAW_NUANCED: 2
- SOURCE_RAW_UNAVAILABLE_REJECTED: 1

## Counts par famille source

- FORCE_SNAPSHOT_DERIVED: 3
- ORIGINAL_AVAILABLE_SUMMARY: 1
- RECOVERED_EXISTING_B9_SUMMARY: 1

## Règles hard gate

- FORCE_SNAPSHOT_DERIVED reste séparé de RECOVERED_EXISTING_B9_SUMMARY.
- NUANCED_BY_RAW ne doit jamais être présenté comme CONFIRMED_BY_RAW.
- RAW_UNAVAILABLE sort de la mémoire active.
- Une source proxy ou reconstruite garde sa provenance visible.
- Un claim raw n’est permis que si la visibilité raw complète est explicite.

## Échantillon de scènes

### M1_FORCE_CONFIRMED_PROXY
- Famille : FORCE_SNAPSHOT_DERIVED
- Gate : SOURCE_RAW_CONFIRMED
- Lecture : La lecture est appuyée par le raw, avec conservation de la provenance et des limites de source.

### M2_NUANCED_PROXY
- Famille : FORCE_SNAPSHOT_DERIVED
- Gate : SOURCE_RAW_NUANCED
- Lecture : Le raw nuance la lecture : la scène peut être exploitée comme contexte, jamais comme confirmation dure.

### M3_RAW_UNAVAILABLE
- Famille : FORCE_SNAPSHOT_DERIVED
- Gate : SOURCE_RAW_UNAVAILABLE_REJECTED
- Lecture : Raw indisponible : la scène doit rester hors mémoire active et ne peut pas être durcie.

### M4_RECOVERED_NUANCED
- Famille : RECOVERED_EXISTING_B9_SUMMARY
- Gate : SOURCE_RAW_NUANCED
- Lecture : Le raw nuance la lecture : la scène peut être exploitée comme contexte, jamais comme confirmation dure.

### M5_ORIGINAL_FULL_RAW
- Famille : ORIGINAL_AVAILABLE_SUMMARY
- Gate : SOURCE_RAW_CONFIRMED
- Lecture : La lecture est appuyée par le raw, avec conservation de la provenance et des limites de source.

## Ce que B9 ne doit pas conclure

- Pas de BUY/SELL.
- Pas de probabilité de succès.
- Pas de durcissement proxy vers raw.
- Pas de confusion entre nuanced et confirmed.

## Prochaine brique

T0134 — B9 French Trader Scene Report V0.
