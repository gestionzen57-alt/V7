# T0139 — B9 London / NY / Asian Replay Scorecard V0

## Objectif

Comparer la qualité des replays B9 par session : Asian, London, Overlap, NY, Dead Zone.

T0139 ne prédit rien. Il qualifie la couverture des summaries replay et expose les trous techniques.

## Contrat

- Read-only.
- Aucune écriture `powerflow.db`.
- Aucune écriture `tick_archive.db`.
- Aucun dashboard.
- Aucun Telegram.
- Aucun BUY/SELL.
- Aucun taux de réussite.

## Ce que T0139 mesure

- nombre de fichiers par session ;
- nombre de moments ;
- couverture V4 ;
- retest fields ;
- effort/résultat/progrès ;
- center path ;
- source quality ;
- timestamp policy ;
- session overlay ;
- failure patterns.

## Doctrine

B9 ne cherche pas le signal. B9 cherche la trace laissée par l’effort.

Une scène London open ne porte pas la même texture qu’une scène Asian ou Dead Zone.
