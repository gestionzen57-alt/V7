
```markdown id="claude_md_v7_1_patch"
# PATCH CLAUDE.md — Passage V7 → V7.1  
**Date : 2026-05-09**  
**Objet : Sections 1, 7, 10, 14**

---

## SECTION 1 — Ajouter cette sous-section dans “BRIQUES V7 VALIDÉES”

### V7.1 Validation & Traceability

```text
V7.1 ajoute une couche de validation, traçabilité, replay et contexte sessionnel.

Objectif :
  Vérifier la qualité de la mémoire DB
  Valider que les briques critiques ne sont pas figées
  Rejouer le passé de manière déterministe
  Construire un film comportemental exploitable
  Qualifier le contexte sessionnel
  Mesurer la texture d'entropie du flux

Modules V7.1 créés / intégrés :

  Phase 1 — Infra & Qualité
    pf_data_quality_guard.py
    run_data_quality_guard_once.py
    pf_market_open_validator.py
    run_market_open_validator_once.py

  Phase 2 — Entropy & Session Overlay
    pf_entropy_engine.py
    run_entropy_engine_once.py
    pf_session_overlay.py
    run_session_overlay_once.py

  Phase 3 — Replay & Film
    pf_replay_engine.py
    lab_replay.py
    pf_film_engine.py
    lab_film.py

Garanties :
  DB read-only stricte via ?mode=ro
  Aucun import cockpit_* dans pf_*
  Aucun import dashboard_* dans pf_*
  Aucun import telegram_* dans pf_*
  Aucun BUY/SELL
  Aucun conseil financier
  Risques techniques uniquement
  Sorties JSON exploitables