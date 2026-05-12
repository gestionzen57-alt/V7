# LEXIQUE PATCH V7.3.5 — TRADER COCKPIT

## TRADER_COCKPIT

Surface frontale lisible par le trader.

Elle transforme plusieurs lectures PowerFlow en une seule perception courte :

- HTF / Topdown ;
- Daily / Journal ;
- Live Brief ;
- B6 ;
- Multiread ;
- risques techniques utiles.

Elle ne décide pas.

## SALLE_MACHINE

Nom donné au dashboard technique dense.

Contient :

- runtime source audit ;
- dual regime ;
- dual density ;
- kinematics ;
- fractal ;
- cascade ;
- session ;
- memory ;
- contract audit.

Utile pour Claude, debug et maintenance. Non prioritaire pour le trader pendant le marché.

## TRADER_LINE

Phrase courte qui dit ce que PowerFlow perçoit.

Exemple :

```text
Conflit actif : daily/topdown piège-rejet, live pousse en sens opposé. Surveiller réintégration, piège inverse ou second test.
```

## FEUX

Résumé compact des quatre lectures principales :

- HTF ;
- DAILY ;
- LIVE ;
- B6.

Objectif : savoir vite si le flux est aligné, mixte ou en conflit.

## SCENARIOS_DE_SURVEILLANCE

Hypothèses de lecture à observer, pas des ordres.

Exemples :

- réintégration ;
- piège inverse ;
- second test ;
- acceptation baissière ;
- acceptation haussière ;
- absorption / friction.

## WAKE_TRADER

Niveau d'attention fort.

Signifie : le flux mérite d'être regardé maintenant.

Ne signifie pas : entrer en position.

## WATCH_ATTENTION

Niveau intermédiaire.

Le contexte est actif mais pas encore assez tranché pour une alerte forte.

## WATCH

Lecture présente, mais pas de réveil trader fort.

## MULTIREAD

Synthèse parallèle Daily + Topdown + Live + B6.

Le multiread ne fusionne pas silencieusement les lectures. Il expose :

- alignement ;
- conflit ;
- divergence ;
- absence de B6 sur paire contexte ;
- risques techniques.

## CONFLICT_OR_REINTEGRATION_TEST

Cas où une lecture supérieure ou daily pointe un piège/rejet, tandis que le live pousse en sens opposé.

À surveiller :

- réintégration ;
- piège inverse ;
- second test ;
- acceptation ou échec.

## PARTIAL_BEARISH_CONTEXT_WITH_B6

Daily et/ou B6 donnent une pression PAIR_DOWN, mais le reste n'est pas totalement aligné.

C'est un contexte partiel, pas une décision.

## PARTIAL_BULLISH_CONTEXT_WITH_B6

Daily et/ou B6 donnent une pression PAIR_UP, mais le reste n'est pas totalement aligné.

C'est un contexte partiel, pas une décision.

## TECHNICAL_RISKS_UTILES

Risques affichés seulement s'ils qualifient la lecture.

Exemples :

- `HTF_INCOMPLETE`
- `TEMPORAL_GAPS_PRESENT`
- `LOW_SAMPLE_FOR_ROTATION`

Le cockpit trader ne doit pas afficher toute la télémétrie brute.
