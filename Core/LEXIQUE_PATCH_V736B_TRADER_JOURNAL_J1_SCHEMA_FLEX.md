# LEXIQUE PATCH V7.3.6b - Trader Journal J1 schema-flex

## TRADER_JOURNAL_J1

Objet quotidien de revue. Il fige la perception machine et laisse des champs au trader.

## J1_REVIEW_PENDING

Le journal est pret mais le resultat reel J+1 n'est pas encore renseigne.

## machine_snapshot

Bloc qui contient la lecture machine figee :

- niveaux daily
- sweeps
- intention
- prediction
- synthese multiread
- direction machine

## trader_fields

Champs manuels :

- lecture HTF
- zones vues
- prediction trader
- resultat reel
- ecart machine vs reel
- apprentissage

## schema-flex

Lecture defensive de plusieurs schemas JSON.  
Evite de casser si `symbols` est une liste de strings ou si les objets sont dans `journals`, `packets`, ou `symbols`.

## role

La brique journalise.  
Elle ne decide pas.
