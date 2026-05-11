# VALIDATION CHECKLIST - Session Overlay + Dashboard Dual

- [ ] pf_session_overlay.py py_compile PASS
- [ ] run_session_overlay_once.py py_compile PASS
- [ ] patch_behavioral_alert_mapper.py py_compile PASS
- [ ] test_session_overlay.py py_compile PASS
- [ ] Tests 4 cas UTC passent
- [ ] 22:15 UTC = ASIAN IGNITION
- [ ] 07:05 UTC = LONDON IGNITION
- [ ] 13:30 UTC = OVERLAP MAX_VELOCITY
- [ ] 20:30 UTC = DEAD_ZONE
- [ ] Behavioral mapper injection fonctionne
- [ ] Dashboard affiche STALE en rouge
- [ ] B1 Legacy et B1+ HMM cote a cote
- [ ] B4 Rolling et B4+ Wavelet cote a cote
- [ ] Session card visible
- [ ] data-brick + data-method + timestamp visibles
- [ ] MISSING data affiche clairement
- [ ] Aucun BUY/SELL
- [ ] DB read-only respectee
- [ ] Pas d'import cockpit_* depuis pf_*
- [ ] LEXIQUE_PATCH_SESSION.md complet
- [ ] REGISTRE_PATCH_SESSION.md complet
- [ ] RAPPORT_SESSION_20260511.md complet

