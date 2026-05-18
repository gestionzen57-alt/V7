Claude,

T0133 — B9 Source Quality Hard Gate V0 est prêt.

Branche :
feat/t0133-b9-source-quality-hard-gate

Commit proposé :
feat(t0133): add B9 source quality hard gate v0

Objectif :
Empêcher toute confusion entre proxy, raw, reconstructed, recovered, CONFIRMED_BY_RAW, NUANCED_BY_RAW et RAW_UNAVAILABLE.

Fichiers livrés :

pf_t009_source_quality_hard_gate.py
tools/build_t0133_b9_source_quality_hard_gate.py
scripts/RUN_T0133_B9_SOURCE_QUALITY_HARD_GATE_FROM_DOWNLOADS.ps1
tests/test_t0133_b9_source_quality_hard_gate.py
samples/b9_source_quality_hard_gate_v0/sample_t009_sequence_summary_source_quality.json
Docs/Reports/T0133_B9_SOURCE_QUALITY_HARD_GATE_REPORT.md
Docs/Reports/T0133_B9_SOURCE_QUALITY_HARD_GATE_MANIFEST.json
Docs/Reports/COMMANDES_T0133_B9_SOURCE_QUALITY_HARD_GATE.md
Docs/Reports/MESSAGE_CLAUDE_T0133_B9_SOURCE_QUALITY_HARD_GATE.md
outputs/b9_source_quality_hard_gate_v0/*

Champs ajoutés :

b9_source_quality_gate_version
b9_source_truth_family
b9_source_quality_gate_state
b9_source_quality_gate_severity
b9_source_quality_flags
b9_source_confidence_cap_effective
b9_raw_claim_allowed
b9_confirmation_claim_allowed
b9_source_quality_reading_fr
b9_source_quality_limits

États :

SOURCE_RAW_CONFIRMED
SOURCE_RAW_NUANCED
SOURCE_PROXY_ONLY
SOURCE_RECONSTRUCTED_LIMITED
SOURCE_RAW_UNAVAILABLE_REJECTED
SOURCE_QUALITY_WEAK_LIMITED
SOURCE_UNKNOWN_LIMITED

Tests :
python -m py_compile pf_t009_source_quality_hard_gate.py toolsuild_t0133_b9_source_quality_hard_gate.py
python -m pytest tests	est_t0133_b9_source_quality_hard_gate.py

Résultat attendu :
2 passed

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Une scène proxy ne devient jamais une vérité raw.

Limites :
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun ordre d’exécution.
Aucune probabilité de succès.
NUANCED_BY_RAW ne devient jamais CONFIRMED_BY_RAW.
RAW_UNAVAILABLE est rejeté de la mémoire active.

Prochain geste :
T0134 — B9 French Trader Scene Report V0.
Mode recommandé : GPT Thinking étendue.
