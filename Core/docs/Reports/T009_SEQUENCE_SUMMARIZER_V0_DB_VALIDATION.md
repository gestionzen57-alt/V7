# T009_SEQUENCE_SUMMARIZER_V0_DB_VALIDATION

## Objectif

Valider la sortie du Summarizer sur la logique attendue des packs replay T009, en preparation des sequences :

- London 08:00-12:00 ;
- Asia/London 07:00-08:00 ;
- Asia 05:00-07:00.

Cette validation reste read-only et ne modifie aucune base.

## Statut

Le pack fournit :

- une validation de contrat `validate_summary_contract()` ;
- une fixture London representative dans les tests ;
- un CLI compatible JSON UTF-8 BOM ;
- un rendu Markdown enrichi V1/V2/V3.

## Controle London attendu

Lecture cible :

- 08:00-08:14 : effort sans resultat ;
- 09:10-09:31 : retest echoue / reprise refusee ;
- 10:00-10:23 : vague progressive ;
- 11:00-11:31 : centre de gravite qui descend ;
- 11:37-12:00 : respiration basse / retour partiel sans progres durable.

Le test `test_london_pack_summary_generates_moments` verifie au minimum :

- effort sans resultat ;
- vague progressive ;
- centre de gravite descendant ;
- generation de plusieurs moments lisibles.

## Points verifies automatiquement

- nombre de moments genere ;
- presence des labels francais ;
- presence des champs Why/How ;
- presence des champs causalite ;
- presence des champs scene fractale ;
- source quality preservee ;
- limites visibles ;
- aucun terme d'ordre en sortie Markdown / JSON ;
- compatibilite fichiers JSON avec UTF-8 BOM.

## Limite de cette validation

Le pack ne contient pas les replay packs reels London / Asia / Asia-London. La validation finale doit etre executee localement sur les fichiers reels :

```powershell
python Core/run_t009_sequence_summarizer_once.py `
  --state output_t009_sequence_replay\battlefield_flux_state.json `
  --events output_t009_sequence_replay\battlefield_flux_events.json `
  --output output_t009_sequence_summary
```

## Verdict V0.1

Le Summarizer est pret pour validation replay reelle :

- il charge les events ;
- il regroupe en moments ;
- il conserve source quality / limites ;
- il produit JSON + Markdown ;
- il explique les scenes en francais ;
- il reste read-only.

Phrase de controle :

```text
Ne lis pas l'absorption comme une direction. Lis ou elle deplace la memoire.
```
