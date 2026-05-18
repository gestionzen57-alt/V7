# T0128 — B9 Native Retest Source Fields / T0111B

## Résumé exécutif

B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Le retest juge une scène, il ne produit pas un ordre.

T0128 enrichit chaque moment B9 avec des champs retest natifs explicites : visible, source, zone, fenêtre, résultat, jugement FR et limites.

## Counts

- moments: 5
- retest_visible: 4
- retest_not_visible: 1
- missing_required_field_counts: {}
- forbidden_language_hits: []

## Retest result counts

- FAILED_REINTEGRATION: 1
- RETEST_ACCEPTED: 1
- RETEST_FAILED: 1
- RETEST_NOT_VISIBLE: 1
- RETEST_PENDING: 1

## Champs natifs

- `retest_source_fields_version`
- `retest_visible`
- `retest_source`
- `retest_zone`
- `retest_start`
- `retest_end`
- `retest_result`
- `retest_judgment_fr`
- `retest_limits`

## Scènes retest visibles

- 2026-05-15T09:10:00Z → 2026-05-15T09:31:00Z | Retest échoué / reprise refusée | RETEST_FAILED | Le retest ne confirme pas la reprise : le prix juge la zone défavorablement.
- 2026-05-15T10:35:00Z → 2026-05-15T10:55:00Z | Pullback absorbé / zone défendue | RETEST_ACCEPTED | Le retour teste la zone sans casser la provenance : le retest est accepté ou défendu.
- 2026-05-15T13:53:00Z → 2026-05-15T13:57:00Z | Réintégration échouée sous le haut | FAILED_REINTEGRATION | Le retour dans la zone échoue : la scène reste jugée par un retest défavorable.
- 2026-05-15T14:25:00Z → 2026-05-15T14:41:00Z | Zone de décision au retest | RETEST_PENDING | La scène montre un retour de jugement, mais le verdict du retest reste en attente.

## Limites techniques

- Un retest non visible reste `RETEST_NOT_VISIBLE`.
- Une scène proxy ne devient pas une vérité raw.
- Le jugement retest est un contexte de scène, pas une décision de trading.
- Aucune écriture `powerflow.db` ou `tick_archive.db`.
- Aucun dashboard, aucun Telegram, aucun BUY/SELL, aucune probabilité de succès.
