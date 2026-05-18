# T0124 — B9 V4 Regression Guard + Golden Replay Cases V2

## Résumé exécutif

T0124 fige les cas replay critiques de B9 V4 pour empêcher les régressions sur :

```text
Effort sans résultat
Vague progressive
Centre de gravité qui descend
Retest échoué
Respiration corrective
Source quality + timestamp policy
```

Phrase de cap :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Ne lis pas l'absorption comme une direction.
Lis où elle déplace la mémoire.
```

## Résultat sample

```text
regression_guard_state = PASS
golden_case_count = 6
golden_cases_passed = 6
golden_cases_failed = 0
total_missing_required_fields = 0
forbidden_language_hit_count = 0
```

## Rôle

T0124 n'est pas un moteur live. C'est un garde anti-régression.
Il vérifie qu'un summary B9 V4 conserve les lectures structurantes : effort/résultat/progrès, chemin interne du centre, retest, source quality, limites et timestamp policy.

## Limites

- Read-only.
- Aucune écriture `powerflow.db`.
- Aucune écriture `tick_archive.db`.
- Aucun dashboard.
- Aucun Telegram.
- Aucun BUY/SELL.
- Aucune probabilité de succès.

## Prochain geste

T0125 — B9 V4 Golden Replay Batch Runner : appliquer T0124 sur plusieurs summaries replay réels.


## Correctif V2

V2 aligne pytest et CLI sur le fallback local déterministe afin d’éviter le drift observé quand pytest importe un contrat natif disponible dans le repo alors que la CLI exécutée depuis tools/ utilise le fallback. T0122/T0123 restent les validations natives du hook/summarizer.
