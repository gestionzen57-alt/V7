# CHECKPOINT V7.5 FINAL DASHBOARD

Date: 2026-05-12
Branch: main

PowerFlow V7.5 status:
- Dashboard final exploitable en live.
- Auto-refresh actif.
- Contract dashboard OK.
- Visual leak contract actif.
- Evidence reading présent.
- Evidence bus présent.
- Session memory affichée, compacte, pleine largeur.
- Quick navigation active: TOP / PROFILES / EVIDENCE / MEMORY / COCKPIT / BOTTOM.
- Cockpit source lisible.
- Risques cockpit humanisés.
- B8 dégradé correctement affiché comme risque analytique, pas comme blocage.
- Telegram gate revenu à état propre avant expérimentation dedup V7.4h.

Architecture validée:
- capture_* = acquisition
- pf_* = moteur / synthèse / evidence / cockpit enrich
- dashboard_* = normalisation / contrat / rendu
- telegram_* = transmission séparée
- scheduler_powerflow_turbo_wrapper.py = orchestration
- dashboard_powerflow_v74.html = cockpit final live

État visuel:
- Bandeau décisionnel
- Lecture trader
- Profils temps
- Evidence bus / risques
- Session memory
- Cockpit source
- Footer

Risques techniques restants:
- B8 coverage insuffisant sur cross pairs.
- Data health partiellement stale selon fenêtres.
- Telegram alert discipline à reprendre séparément, hors dashboard.
- Possibilité future de scinder dashboard HTML en composants JS/CSS si taille trop élevée.

Prochaine phase proposée:
V7.6 = Telegram discipline séparée:
- dry-run clair
- live-send clair
- dedup mémoire propre
- packet_id stable
- mark_sent_reason explicite
- no duplicate wake-trader
- aucun impact sur dashboard
