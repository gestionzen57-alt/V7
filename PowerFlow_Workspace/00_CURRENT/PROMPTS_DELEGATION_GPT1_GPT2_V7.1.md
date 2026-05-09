# PROMPTS DÉLÉGATION — PowerFlow V7.1
**Chef d'orchestre : Claude Projects | Date : 2026-05-09**
**Mode : War mode — zéro administration — action directe**

---

## CONTEXTE COMMUN À COLLER EN DÉBUT DE CHAQUE PROMPT GPT

```
Tu travailles sur PowerFlow V7.1 — moteur de perception du flux Forex.
Architecture : pf_* (moteur, read-only DB) → run_* (runners CLI) → cockpit_* (affichage)
Règles absolues :
  - pf_* n'importe JAMAIS cockpit_*, dashboard_*, telegram_*
  - DB read-only : sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
  - Pas de BUY/SELL dans les alertes
  - py_compile avant tout commit
  - 1 feature = 1 commit
  - Pas de conseil financier, pas de nanny, risques techniques uniquement
  - Ne pas toucher : capture_bridge.py, pf_temporal_node_state.py, pf_relational_gravity_bridge.py
Doctrine : la machine perçoit, nomme, alerte. Le trader décide.
```

---

## PROMPT GPT1 — MISSION : TASK SCHEDULER V7.1

### Coller ce prompt dans GPT Pro 1 (Infrastructure / Algo)

```
[CONTEXTE POWERFLOW — voir section ci-dessus]

MISSION : créer run_powerflow_cycle_once.py — orchestrateur du cycle complet V7.1

OBJECTIF :
  Exécuter la séquence complète dans l'ordre exact, avec logs, 
  gestion d'erreur non-bloquante, et rapport JSON final.

SÉQUENCE EXACTE (ordre non négociable) :
  1. run_data_quality_guard_once.py      → output/data_quality_guard.json
  2. run_market_open_validator_once.py   → output/market_open_validator.json
  3. run_entropy_engine_once.py          → output/entropy_engine.json
  4. run_session_overlay_once.py         → output/session_overlay.json
  5. run_temporal_node_state_once.py     → output/temporal_node_state.json
  6. run_currency_energy_probe_once.py   → output/currency_energy.json
  7. run_confluence_alert.py --once      → output/behavioral_alert_queue.json (append)
  8. run_cascade_engine_once.py          → output/cascade_state.json
  9. run_powerflow_dashboard_refresh_once.py → output/dashboard_data.json

SPÉCIFICATIONS :
  - Chaque step = subprocess.run() avec timeout=30s
  - Si un step fail : log erreur + continuer (non-bloquant)
  - Mesurer durée chaque step (time.perf_counter)
  - Produire output/cycle_report.json à la fin :
    {
      "cycle_id": "uuid4",
      "started_at_utc": "...",
      "total_duration_ms": int,
      "steps": [
        {"step": 1, "module": "run_data_quality_guard_once", "status": "OK|FAIL", "duration_ms": int, "error": null|"..."}
      ],
      "cycle_status": "COMPLETE|PARTIAL|FAILED"
    }
  - CLI args : --db (default: powerflow.db) --symbol (default: GBPUSD) --dry-run (flag)
  - Logs console avec timestamp UTC + step number
  - py_compile ce fichier avant livraison

CONTRAINTES :
  - Python pur, pas de dépendances externes
  - Aucun import pf_* direct — subprocess seulement
  - Compatible cmd.exe Windows (pas PowerShell-only)
  - Fichier unique < 150 lignes
  - Constantes nommées pour timeouts et paths

LIVRAISON :
  - run_powerflow_cycle_once.py complet
  - py_compile validé
  - 3 lignes de test de lancement : python run_powerflow_cycle_once.py --db powerflow.db --symbol GBPUSD
```

---

## PROMPT GPT2 — MISSION : DASHBOARD CARDS V7.1

### Coller ce prompt dans GPT Pro 2 (ML / Automation / Docs)

```
[CONTEXTE POWERFLOW — voir section ci-dessus]

MISSION : ajouter 4 nouvelles cards au dashboard_live.html de PowerFlow V7.1

CONTEXTE FICHIERS :
  dashboard_live.html = interface cockpit existante avec cards Bootstrap/CSS
  Les nouvelles cards lisent des JSON depuis /output/ via fetch() polling

CARDS À CRÉER (1 section HTML + JS par card) :

CARD 1 — DATA QUALITY
  Source JSON : output/data_quality_guard.json
  Affiche :
    - Statut global : OK / DEGRADED / CRITICAL (badge couleur)
    - Par TF : rows count + last_timestamp + is_stale (bool) + gap_count
    - Alerte visuelle si stale=true ou gap_count > 0
  Couleurs : vert=OK, orange=DEGRADED, rouge=CRITICAL

CARD 2 — MARKET VALIDATOR
  Source JSON : output/market_open_validator.json
  Affiche :
    - B4 : PASS / PARTIAL / FAIL (dominant_period_bars ≠ 1 ?)
    - B5 : PASS / PARTIAL / FAIL (rho fluctuant ?)
    - EIE : PASS / PARTIAL / FAIL (non statique ?)
    - Verdict global : MARKET_OPEN_VALIDATED / PENDING / STATIC_WARNING
  Couleurs : vert=PASS, orange=PARTIAL, rouge=FAIL

CARD 3 — ENTROPY
  Source JSON : output/entropy_engine.json
  Affiche :
    - alert_entropy_state : NORMAL_ALERT_FLOW / BURST_ACTIVE / SATURATED
    - normalized_entropy : valeur 0.0-1.0 (barre de progression)
    - duplication_ratio : valeur 0.0-1.0
    - burst_score si burst actif
  Couleurs : vert=NORMAL, orange=BURST, rouge=SATURATED

CARD 4 — SESSION OVERLAY
  Source JSON : output/session_overlay.json
  Affiche :
    - session : ASIAN / LONDON / NY / OVERLAP / DEAD
    - session_phase : IGNITION / MID_SESSION / DEAD_ZONE / PRE_OPEN
    - minutes_since_open : valeur entière
    - session_bias : EXPANSION_EXPECTED / COMPRESSION / ROTATION
    - overlap si présent
  Couleurs : bleu=ASIAN, orange=LONDON, vert=NY, rouge=OVERLAP, gris=DEAD

SPÉCIFICATIONS TECHNIQUES :
  - JS vanilla (pas de React/Vue) — fetch() polling toutes les 30s
  - Gestion erreur fetch : afficher "No data" si JSON absent
  - Responsive — même style que les cards existantes
  - Commentaires HTML clairs par card
  - Intégration directe dans dashboard_live.html (section dédiée)

LIVRAISON :
  - Bloc HTML complet des 4 cards
  - Bloc JS complet (fetch + render functions)
  - Prêt à copier-coller dans dashboard_live.html
  - Indiquer où exactement insérer dans le fichier existant
```

---

## PROMPT BONUS — MISSION P0 VALIDATION TEMPLATE

### Pour GPT1 ou GPT2 : créer le template de rapport P0

```
[CONTEXTE POWERFLOW — voir section ci-dessus]

MISSION : créer P0_MARKET_OPEN_VALIDATION_TEMPLATE.md

Objectif : template de rapport que je remplis manuellement lundi 12 mai
           pendant et après l'Asian open (23h CEST)

STRUCTURE DU TEMPLATE :

# P0 — VALIDATION MARCHÉ OUVERT
Date : 2026-05-12 | Session : ASIAN | Heure début : 23h CEST

## CHECKLIST DB HEALTH
[ ] Data Quality Guard lancé : résultat = ___
[ ] TF1 rows fresh : ___  | last_ts : ___
[ ] TF5 rows fresh : ___  | last_ts : ___
[ ] Stale flags : ___
[ ] Gaps détectés : ___

## B4 TEMPORAL DENSITY — VERDICT
[ ] dominant_period_bars TF1 : ___ (PASS si ≠ 1)
[ ] dominant_period_bars TF5 : ___ (PASS si ≠ 1)
[ ] cycle_state TF1 : ___
[ ] cycle_state TF5 : ___
[ ] COMPRESSION_ALERT : ___
Verdict B4 : PASS / PARTIAL / FAIL

## B5 SPEARMAN GRAVITY — VERDICT
[ ] rho GBP_USD TF1 : ___
[ ] rho GBP_USD TF5 : ___
[ ] Labels non figés : OUI / NON
[ ] avg_rho fluctuant : OUI / NON
Verdict B5 : PASS / PARTIAL / FAIL

## EIE CONFLUENCE — VERDICT
[ ] EIE snapshot : ___
[ ] fractalite : ___
[ ] elastic_score : ___
[ ] EIE ≠ NEUTRAL : OUI / NON
Verdict EIE : PASS / PARTIAL / FAIL

## DAEMON CONFLUENCE
[ ] run_confluence_alert.py --once : OK / FAIL
[ ] behavioral_alert_queue.json mis à jour : OUI / NON
[ ] Entries sans doublons : OUI / NON

## SESSION OVERLAY
[ ] session : ___
[ ] session_phase : ___
[ ] minutes_since_open : ___
Verdict Session : CORRECT / WRONG

## ENTROPY
[ ] alert_entropy_state : ___
[ ] normalized_entropy : ___
Verdict : NORMAL / BURST / SATURATED

## VERDICT GLOBAL P0
[ ] PASS complet → lancer Task Scheduler P1
[ ] PARTIAL → lister items en échec → corriger avant P1
[ ] FAIL → stopper expansion, diagnostiquer

## NOTES LIBRES
[espace libre pour observations terrain]

---

LIVRAISON : template Markdown propre, prêt à imprimer/remplir
```

---

*Prompts délégation PowerFlow V7.1 — Chef d'orchestre Claude Projects — 2026-05-09*
