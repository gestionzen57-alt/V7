# T0133 — B9 Source Quality Hard Gate V0

## Objectif

Empêcher toute confusion de provenance dans B9 : proxy, reconstructed, recovered, raw confirmed et raw nuanced restent distincts.

## Doctrine

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l'effort.  
Une scène proxy ne devient jamais une vérité raw.

## Règles verrouillées

- FORCE_SNAPSHOT_DERIVED ne devient jamais RECOVERED_EXISTING_B9_SUMMARY.
- RECOVERED_EXISTING_B9_SUMMARY ne devient jamais FORCE_SNAPSHOT_DERIVED.
- NUANCED_BY_RAW ne devient jamais CONFIRMED_BY_RAW.
- RAW_UNAVAILABLE exclut la mémoire active.
- FULL_RAW explicite est requis pour autoriser un claim raw.

## Tests

```powershell
python -m py_compile pf_t009_source_quality_hard_gate.py toolsuild_t0133_b9_source_quality_hard_gate.py
python -m pytest tests	est_t0133_b9_source_quality_hard_gate.py
```

## Commande CLI

```powershell
python toolsuild_t0133_b9_source_quality_hard_gate.py --sequence-summary-json samples9_source_quality_hard_gate_v0\sample_t009_sequence_summary_source_quality.json --output-dir outputs9_source_quality_hard_gate_v0
```

## Limites

Read-only. Aucun DB write. Aucun dashboard. Aucun Telegram. Aucun BUY/SELL. Aucune probabilité de succès.
