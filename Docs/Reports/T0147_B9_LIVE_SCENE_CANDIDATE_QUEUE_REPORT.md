# T0147 — B9 Live Scene Candidate Queue V0

## Objectif

Créer une file read-only de scènes candidates B9 live à partir des moments enrichis par T0128→T0146.

T0147 ne déclenche rien. Il prépare :

- `B9_LATEST_SCENE_CANDIDATE_V0.json`
- `B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.json`
- `B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.md`
- `B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.csv`
- `B9_LIVE_SCENE_CANDIDATE_REJECTED_V0.csv`
- `B9_LIVE_SCENE_CANDIDATE_LOW_SIGNAL_V0.csv`

## Doctrine

B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.

La queue transmet une scène candidate, une raison technique et des limites. Elle ne produit aucun ordre.

## Contrat

- read-only ;
- aucune écriture `powerflow.db` ;
- aucune écriture `tick_archive.db` ;
- aucun dashboard ;
- aucun Telegram ;
- aucun ordre directionnel ;
- aucun taux de réussite ;
- RAW_UNAVAILABLE rejeté de la queue active.

## Entrée

Un `t009_sequence_summary*.json` enrichi avec les champs B9 récents :

- scene role ;
- price verdict ;
- terrain node ;
- B6 scene family ;
- source quality gate ;
- memory confidence ladder ;
- false positive memory state ;
- session overlay ;
- retest ;
- center path.

## États de sortie

```text
B9_LIVE_SCENE_CANDIDATE_READY
B9_LIVE_SCENE_CANDIDATE_REVIEW
B9_LIVE_SCENE_CANDIDATE_LOW_SIGNAL
B9_LIVE_SCENE_CANDIDATE_REJECT_RAW_UNAVAILABLE
B9_LIVE_SCENE_CANDIDATE_REJECT_FORBIDDEN_LANGUAGE
B9_LIVE_SCENE_CANDIDATE_REJECT_MEMORY
B9_LIVE_SCENE_CANDIDATE_REJECT_SOURCE
```

## Prochain geste

T0148 — B9 Live Brief Once Runner V0.
