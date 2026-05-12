# VALIDATION CHECKLIST — COMMANDO P2

- [ ] `python -m py_compile pf_m1_noise_ratio_probe.py` PASS
- [ ] `python run_m1_noise_ratio_once.py --pretty` produit `output/force_kinematics_state.json`
- [ ] `output/force_kinematics_state.json` contient `noise_ratio`
- [ ] `python run_m1_context_score_once.py --pretty` relit le noise_ratio
- [ ] `dashboard_normalize_m1_context.py` produit `output/dashboard_surface/m1_context_score.json`
- [ ] `run_usdjpy_capture_diagnostic_once.py --pretty` produit un diagnostic USDJPY
- [ ] DB read-only
- [ ] Aucun BUY/SELL
- [ ] Dashboard card injectée seulement si `-InjectDashboard`
- [ ] LEXIQUE patch commité
- [ ] REGISTRE patch commité
