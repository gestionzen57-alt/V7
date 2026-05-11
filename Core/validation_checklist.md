# Validation Checklist — Session Overlay + Dashboard Dual

## Python

- [ ] `python -m py_compile pf_session_overlay.py` PASS
- [ ] `python -m py_compile patch_behavioral_alert_mapper.py` PASS
- [ ] `python test_session_overlay.py` PASS
- [ ] `python run_session_overlay_once.py --pretty` PASS

## Session overlay cases

- [ ] 22:15 UTC -> ASIAN / IGNITION
- [ ] 07:05 UTC -> LONDON / IGNITION
- [ ] 13:30 UTC -> OVERLAP / MAX_VELOCITY_BATTLEFIELD
- [ ] 20:30 UTC -> DEAD_ZONE / DEAD_ZONE
- [ ] `minutes_since_open >= 0`
- [ ] `session_bias` dans enum valide

## Mapper

- [ ] `pf_behavioral_alert_mapper.py` importe `get_session_context`
- [ ] Chaque alerte porte `session_context`
- [ ] Aucun filtre session ajouté
- [ ] Aucun BUY/SELL ajouté

## Dashboard

- [ ] Chaque bloc porte `data-brick`
- [ ] Chaque bloc porte `data-method`
- [ ] Chaque bloc porte `data-symbol`
- [ ] B1 Legacy et B1+ HMM côte à côte
- [ ] B4 Rolling et B4+ Wavelet côte à côte
- [ ] `FRESH / AGING / STALE / MISSING` visibles
- [ ] STALE rouge/grisé
- [ ] MISSING avec message clair
- [ ] INSUFFICIENT_DATA visible avec raison/progression

## Git

- [ ] `git status` inspecté avant commit
- [ ] `git add` limité aux fichiers du patch
- [ ] Commit message exact : `SessionOverlay: V2 complete injection + Dashboard dual display hardening`
- [ ] `git push` PASS
