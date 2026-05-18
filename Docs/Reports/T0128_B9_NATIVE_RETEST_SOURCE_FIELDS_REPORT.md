# T0128 — B9 Native Retest Source Fields / T0111B

## Résumé exécutif

T0128 ajoute une couche native et read-only pour porter les champs retest directement dans les moments B9/T009.

Phrase de cap :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Le retest juge une scène, il ne produit pas un ordre.
```

## Objectif

Transformer les retests reconstruits ou implicites en champs explicites portés par chaque moment :

```text
retest_visible
retest_source
retest_zone
retest_start
retest_end
retest_result
retest_judgment_fr
retest_limits
```

## États produits

```text
RETEST_NOT_VISIBLE
RETEST_PENDING
RETEST_ACCEPTED
RETEST_FAILED
FAILED_REINTEGRATION
```

## Garanties

```text
read-only
no powerflow.db write
no tick_archive.db write
no dashboard
no Telegram
no BUY/SELL
no probability of success
```

## Usage CLI

```powershell
python tools\build_t0128_b9_native_retest_source_fields.py `
  --sequence-summary-json samples\b9_native_retest_source_fields_v0\sample_t009_sequence_summary_retest_candidate.json `
  --output-dir outputs\b9_native_retest_source_fields_v0
```

## Limites techniques

- Si le retest n’est pas visible, il reste `RETEST_NOT_VISIBLE`.
- Les scènes proxy ne deviennent pas des vérités raw.
- Le jugement retest est une lecture de scène, pas une décision.
- Le module peut être intégré plus tard dans le summarizer natif, mais il est déjà testable isolément.

## Prochain geste

T0129 — B9 Effort / Résultat / Progrès Scorer V0.
