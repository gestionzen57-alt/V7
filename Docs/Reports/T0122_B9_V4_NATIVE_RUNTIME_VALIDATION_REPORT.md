# T0122 — B9 V4 Native Runtime Validation

## Résumé

T0122 vérifie que l’intégration T0121 produit réellement les champs B9 V4 dans les summaries T009/B9.

Doctrine :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Ne lis pas l’absorption comme une direction.
Lis où elle déplace la mémoire.
```

## Rôle

T0122 ne modifie pas le moteur. Il valide :

- présence du hook T0121 dans `pf_t009_sequence_summarizer.py` ;
- couverture des champs V1/V2/V3/V4 ;
- absence de langage BUY/SELL/probabilité ;
- état read-only ;
- rapport Markdown/JSON/CSV exploitable.

## Sorties

```text
B9_V4_NATIVE_RUNTIME_VALIDATION_V0.md
B9_V4_NATIVE_RUNTIME_VALIDATION_V0.json
B9_V4_NATIVE_RUNTIME_FIELD_COVERAGE_V0.csv
B9_V4_NATIVE_RUNTIME_CHECKS_V0.csv
B9_V4_NATIVE_RUNTIME_ENRICHED_SUMMARY_SAMPLE_V0.json
B9_V4_NATIVE_RUNTIME_VALIDATION_MANIFEST.json
B9_V4_NATIVE_RUNTIME_VALIDATION_V0.zip
```

## Limites

- Aucun accès DB.
- Aucun dashboard.
- Aucun Telegram.
- Aucun BUY/SELL.
- Aucune probabilité de succès.
- Si le hook T0121 n’est pas visible, T0122 le signale sans modifier le summarizer.

## Prochain geste

Si T0122 passe : T0123 — B9 V4 Replay Runtime Comparison.
