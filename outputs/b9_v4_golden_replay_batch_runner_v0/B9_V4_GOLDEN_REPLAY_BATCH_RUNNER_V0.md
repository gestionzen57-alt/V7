# B9 V4 Golden Replay Batch Runner V0

## Résumé exécutif

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l'effort.  
Ne lis pas l'absorption comme une direction.  
Lis où elle déplace la mémoire.

## Résultat batch

- État : `PASS`
- Fichiers traités : 3
- Fichiers passés : 3
- Fichiers échoués : 0
- Moments avant : 18
- Moments après : 18
- Champs requis manquants : 0
- Langage interdit : 0
- Changements de champs préservés : 0

## Ce que T0125 protège

- effort sans résultat ;
- vague progressive ;
- centre de gravité qui descend ;
- retest échoué ;
- respiration corrective ;
- source quality et timestamp policy.

## Limites techniques

T0125 est un runner de batch read-only. Il ne remplace pas T0122/T0123 pour la validation native du hook local. Il sert à vérifier que des lots de summaries conservent le contrat V4 et les cas golden.

## Interdits respectés

Aucune écriture powerflow.db.  
Aucune écriture tick_archive.db.  
Aucun dashboard.  
Aucun Telegram.  
Aucun BUY/SELL.  
Aucune probabilité de succès.
