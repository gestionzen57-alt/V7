# CHECKPOINT V7.3.6b - Trader Journal J1 schema-flex

Etat attendu apres installation :

- `pf_trader_journal_j1.py` compile.
- `trader_journal_j1.json` est produit.
- `trader_journal_j1.md` est produit.
- Les champs daily ne doivent plus etre UNKNOWN/null si `daily_flow_packet.json` est present.

Champs attendus :

- high_of_day
- low_of_day
- close_position
- tested_levels
- rejected_levels
- sweeps
- intent
- prediction_next_session

Statut normal :

`J1_REVIEW_PENDING`

Ce statut est normal car le trader doit remplir le resultat J+1 et les lecons.
