# LEXIQUE_MASTER.md

Status: T006_B_FUSED_FROM_STAGED_CANDIDATES
Date: 2026-05-15 22:29:08 +02:00
Mission: consolidate PowerFlow trader language, lexique, grammar, film library, packet requirements, and requalification rules.

## Source mode

SOURCE_MODE: STAGED_V76_V6_WITH_RECREATED_AVENANT
AVENANT_STATUS: RECREATED_CANDIDATE_NOT_ORIGINAL

Important:

- This master lexique is not an exact V767-source fusion.
- Exact V767 source files were missing during T006-A2.
- T006-A3 staged available V76/V6 source candidates.
- T006-A4 recreated the missing AVENANT language candidate.
- This file is a deterministic fusion from the staged corpus, with provenance preserved.

## Non-negotiable doctrine

- PowerFlow reads market structure; it does not issue guaranteed trading signals.
- PowerFlow qualifies perception; the trader decides.
- PowerFlow must separate observation, qualification, hypothesis, confirmation, invalidation, data limits, and trader decision.
- GBPUSD remains the primary trading surface.
- Multidevise context is used for coalitions, antagonists, gravity, and tempo; it is not a direct trade trigger.
- M1 tickvolume/sec remains GBPUSD-only unless explicitly expanded later.
- B8 remains incomplete as a full multicurrency brick until currency-specific tempo is modeled.

## Required trader-facing output contract

- Film
- Dernier evenement structurel
- Zone active
- Role du mouvement
- Coalitions / antagonistes
- Gravite
- Qualite packet
- Confirmation prix
- Invalidation
- Limites donnees

## Provenance

- Docs\T006_Source_Staging\AVENANT_LANGAGE_FR_TRADER_POWERFLOW_V767_RECREATED_CANDIDATE.md | SHA256=F68543F5E6F0EF4168337CFC6C47A0793983245DAE5DC3251812537AFF58BC42 | bytes=4888
- Docs\T006_Source_Staging\CLAUDE__CLAUDE.md | SHA256=9A93745AA1BC3EB8A1416E457A926B0EF5A6B247DBF9CCDCFAF21E7E91654583 | bytes=11434
- Docs\T006_Source_Staging\FILM_LIBRARY__POWERFLOW_FILM_LIBRARY_GBPUSD_V76_FINAL.md | SHA256=A5F3386CC8825ED5C5C908B18F235E4EA01CEC791B9279B932CA2582D882332C | bytes=17330
- Docs\T006_Source_Staging\FILM_LIBRARY__POWERFLOW_FILM_MEMORY_CARDS_GBPUSD_V76.md | SHA256=14B5879E3DB204CFF15853905B0961F5D590FB6F1A7E14DBA99E0E64EE0975BC | bytes=10071
- Docs\T006_Source_Staging\FILM_LIBRARY__POWERFLOW_FILM_PATTERN_INDEX_V76.md | SHA256=B0698821AB0C378980305283527924EDDC03B8FBD3FE11E546781FD5E577265E | bytes=2560
- Docs\T006_Source_Staging\GRAMMAIRE__GRAMMAIRE_LEXIQUE_POWERFLOW_V6_UPDATE_2026-05-04.md | SHA256=D69483538FB9F3DAA1FC5A7CBB2B9A8295A3B5C92F0F3EFC748333945EF9B935 | bytes=8974
- Docs\T006_Source_Staging\GRAMMAIRE__GRAMMAIRE_LEXIQUE_SEQUENCE_NODES_V01.md | SHA256=564FE99648D70DEB3E1C0C07001CA292E0EAE46E3E50D81F93A8B66D33972FC5 | bytes=10875
- Docs\T006_Source_Staging\LEXIQUE__02_LEXIQUE_GRAMMAIRE_POWERFLOW_V6_ACTIVE_20260505.md | SHA256=A7BA1CE8522CDDFCE0C3964E96E05C27AA5B546596A6F4F49F0767D3250ED50F | bytes=2888
- Docs\T006_Source_Staging\LEXIQUE__LEXIQUE_GRAMMAIRE_COMPORTEMENTS_POWERFLOW.md | SHA256=3C152CCB816A34645A25A91AD30F90771732E8161C1570D5F3DEAFE303C03193 | bytes=7418
- Docs\T006_Source_Staging\LEXIQUE__LEXIQUE_GRAMMAIRE_COMPORTEMENTS_POWERFLOW.txt | SHA256=FD389FB437A9E99EBA6C7DDDB0406A858AA8FD18869F506C228C9C05E610C53F | bytes=42748
- Docs\T006_Source_Staging\LEXIQUE__LEXIQUE_GRAMMAIRE_POWERFLOW_V6_CONSOLIDE_2026-05-04.md | SHA256=8035BCECF2B3DECE27B6EBB5A6B6ECB217A22D696F814E0095C6BD29DA75F9BA | bytes=33107
- Docs\T006_Source_Staging\PACKET_REQUALIFICATION__POWERFLOW_BRICK_TO_PACKET_FIELD_MAPPING_V76.md | SHA256=9788FC333A4584D17F3FAE4454A6A877676B4685947DB740B029DD270FA4F131 | bytes=6349
- Docs\T006_Source_Staging\PACKET_REQUALIFICATION__POWERFLOW_PACKET_REQUALIFICATION_RULES_V76_FINAL.md | SHA256=23D419A222F49BDAD12A66892C68479C091F8B883DB69DC0E17648ADE11C4776 | bytes=15776
- Docs\T006_Source_Staging\PACKET_REQUALIFICATION__POWERFLOW_TRADER_PACKET_REQUIREMENTS_V76.md | SHA256=1B63AEAC33E3032DDC0C49CA809E37822E04464CB036059BA93415FCEF7BC304 | bytes=7537

---

# Fused staged source corpus


---

# SOURCE: Docs\T006_Source_Staging\AVENANT_LANGAGE_FR_TRADER_POWERFLOW_V767_RECREATED_CANDIDATE.md

SHA256: F68543F5E6F0EF4168337CFC6C47A0793983245DAE5DC3251812537AFF58BC42
BYTES: 4888

```text
# AVENANT_LANGAGE_FR_TRADER_POWERFLOW_V767 - RECREATED CANDIDATE

Status: RECREATED_CANDIDATE
Original exact source: MISSING
Mission: restore trader-facing French language doctrine for T006 LEXIQUE_MASTER.md fusion.

IMPORTANT

- This is not the original V767 file.
- This is a recreated candidate from staged V76/V6 sources and current PowerFlow doctrine.
- T006-B may use it only if explicitly accepted as replacement for the missing AVENANT source.

## 1. Non-negotiable language rules

PowerFlow must speak as a market-reading engine, not as a trading signal machine.

PowerFlow must always separate:
- observation
- qualification
- hypothesis
- confirmation
- invalidation
- data limits
- trader decision

Allowed phrasing:
- le film actuel montre...
- la machine lit...
- le terrain suggere...
- la zone active est...
- le prix confirme partiellement...
- la lecture reste fragile car...

Forbidden phrasing:
- achete
- vends
- signal certain
- trade garanti
- setup valide sans condition
- le marche va forcement...

## 2. PowerFlow role

PowerFlow qualifies market perception. PowerFlow does not replace the trader. Final decision remains manual.

PowerFlow must report:
- film
- last structural event
- active zone
- role of current movement
- packet quality
- price confirmation or rejection
- coalition and antagonist context
- gravity / compression / release state
- data limits

## 3. GBPUSD priority and multidevise context

Primary trading surface: GBPUSD.

Reason: M1 tickvolume/sec remains GBPUSD-only to avoid uncontrolled DB growth on other pairs.

The 13-symbol cohort is contextual. It reads USD/GBP behavior, coalitions, antagonists, gravity, and asynchronous tempo.

B8 is useful as cross-surface / multiread component, but remains incomplete as a true multicurrency brick until currency-specific tempo is modeled.

## 4. Core trader vocabulary

- Film: readable market sequence; what happened, what happens now, what confirms or invalidates.
- Terrain: structural context; active zone, range position, compression, expansion, compatibility, fragility.
- Packet: compressed trader-facing summary of machine perception.
- Compression: energy stored, movement constrained, release not clean yet.
- Release: stored pressure starts to escape; needs detachment, relay, or price acceptance.
- Detachment: one side separates clearly from previous cluster or equilibrium.
- Relay: continuation support after detachment.
- Rejection: price probes a zone and fails to accept beyond it.
- Acceptance: price holds beyond a level or zone.
- Gravity: attraction / compression field among currencies or symbols.
- Coalition: multiple actors push in compatible pressure.
- Antagonist: actor working against dominant coalition.
- Overlap skip: analytical continuation, not turbo failure.
- Data not ready: not enough depth, freshness, or coverage.

## 5. Required trader-facing summary format

- Film
- Dernier evenement structurel
- Zone active
- Role du mouvement
- Coalitions / antagonistes
- Gravite
- Qualite packet
- Confirmation prix
- Invalidation
- Limites donnees

## 6. Confidence language

Allowed: faible, partielle, correcte, propre, forte mais conditionnelle.
Forbidden: certain, garanti, 100%, entree automatique, signal infaillible.

## 7. Data limits language

PowerFlow must explicitly say when M1 exists only on GBPUSD, when non-GBPUSD symbols have thinner LTF coverage, when HTF sample is low, when OHLC is missing, or when multiread is contextual rather than a trade instruction.

## 8. T006 fusion instruction

If accepted for T006-B, LEXIQUE_MASTER.md must mark this source as RECREATED_CANDIDATE_NOT_ORIGINAL.

## 9. Provenance

- $rel | SHA256=9A93745AA1BC3EB8A1416E457A926B0EF5A6B247DBF9CCDCFAF21E7E91654583 | bytes=11434
- $rel | SHA256=A5F3386CC8825ED5C5C908B18F235E4EA01CEC791B9279B932CA2582D882332C | bytes=17330
- $rel | SHA256=14B5879E3DB204CFF15853905B0961F5D590FB6F1A7E14DBA99E0E64EE0975BC | bytes=10071
- $rel | SHA256=B0698821AB0C378980305283527924EDDC03B8FBD3FE11E546781FD5E577265E | bytes=2560
- $rel | SHA256=D69483538FB9F3DAA1FC5A7CBB2B9A8295A3B5C92F0F3EFC748333945EF9B935 | bytes=8974
- $rel | SHA256=564FE99648D70DEB3E1C0C07001CA292E0EAE46E3E50D81F93A8B66D33972FC5 | bytes=10875
- $rel | SHA256=A7BA1CE8522CDDFCE0C3964E96E05C27AA5B546596A6F4F49F0767D3250ED50F | bytes=2888
- $rel | SHA256=3C152CCB816A34645A25A91AD30F90771732E8161C1570D5F3DEAFE303C03193 | bytes=7418
- $rel | SHA256=FD389FB437A9E99EBA6C7DDDB0406A858AA8FD18869F506C228C9C05E610C53F | bytes=42748
- $rel | SHA256=8035BCECF2B3DECE27B6EBB5A6B6ECB217A22D696F814E0095C6BD29DA75F9BA | bytes=33107
- $rel | SHA256=9788FC333A4584D17F3FAE4454A6A877676B4685947DB740B029DD270FA4F131 | bytes=6349
- $rel | SHA256=23D419A222F49BDAD12A66892C68479C091F8B883DB69DC0E17648ADE11C4776 | bytes=15776
- $rel | SHA256=1B63AEAC33E3032DDC0C49CA809E37822E04464CB036059BA93415FCEF7BC304 | bytes=7537
```

---

# SOURCE: Docs\T006_Source_Staging\CLAUDE__CLAUDE.md

SHA256: 9A93745AA1BC3EB8A1416E457A926B0EF5A6B247DBF9CCDCFAF21E7E91654583
BYTES: 11434

```text
<!-- POWERFLOW_CURRENT_STATE_START -->
## Current State - updated 2026-05-15T21:01:26.5402470+02:00

- Workspace current-state update for Claude.
- T004 is requalified after expanded USD cohort.
- Global USD-base blockage is invalidated.
- Probable cause for initial USDJPY thin data: feed / EA / capture intermittent or initial setup incomplete.
- Current T004 dispatch status: DIAGNOSED_REQUALIFIED_FEED_CAPTURE_INTERMITTENT.
- No engine/scoring/dashboard/DB patch is justified for T004.
- Canonical current state file: Docs/CURRENT_STATE.md.
- Latest snapshot: Docs/CurrentState/CURRENT_STATE_20260515_210126_T004_REQUALIFIED.md.

<!-- POWERFLOW_CURRENT_STATE_END -->

# PowerFlow V7.6.7 ??? ??tat Central

## Last Session

- Date: 2026-05-15 21:00
- AI: Claude Sonnet 4.5
- Focus: fin
- Checkpoint: Checkpoints\CHECKPOINT_20260515_210015.md

## Derni??re session

- **Date:** 2026-05-15 10:30
- **IA:** Claude Sonnet 4.5
- **Focus:** Infrastructure Admin & Consolidation
- **Checkpoint:** `Checkpoints/CHECKPOINT_20260515_103000.md`
- **Commit:** `???? Infrastructure automation scripts + Docs/ structure`

---

## ??tat op??rationnel PowerFlow

### ??? Syst??mes LIVE

| Composant | Statut | Version | Notes |
|-----------|--------|---------|-------|
| **Core Engine** | ???? LIVE | V7.6.7 | Scheduler turbo wrapper actif |
| **Dashboard** | ???? LIVE | V7.4 | Terrain panel + time profiles |
| **Capture Bridge** | ???? LIVE | ??? | MT4 ??? SQLite op??rationnel |
| **PowerFlow.db** | ???? OK | 15.6 MB | GBPUSD dense, EURUSD HTF incomplet, USDJPY THIN |
| **P0 Validation** | ???? PASS_STRICT | ??? | 16/16 tests Dashboard OK |
| **Git Sync** | ???? AUTO | ??? | `auto_git_sync.ps1` actif |

### ?????? Points d'attention

- **USDJPY THIN** ??? Data stale/sparse, n??cessite diagnostic (T004)
- **EURUSD HTF** ??? Incomplet mais utilisable
- **pf_normalizer.py** ??? Signature mismatch API /cockpit-state (T003)
- **engine.py legacy** ??? Refonte V6 n??cessaire (T002)

---

## Architecture active

### Modules core PowerFlow

```
pf_*.py                      # Moteur perception flux
????????? pf_engine.py             # [LEGACY V5 - Refonte V6 en attente T002]
????????? pf_normalizer.py         # Normalisation devises vs USD [HOTFIX needed T003]
????????? pf_temporal_nodes.py     # D??tection nodes temporels
????????? pf_zones.py              # Identification zones cl??s
????????? pf_coalitions.py         # Analyse coalitions devises
????????? pf_memory.py             # Syst??me m??moire ??v??nements
????????? pf_battlefield_map.py    # Cartographie terrain
????????? pf_perception_spine_once.py  # Perception spine LIVE
????????? pf_trader_attention_packet_once.py  # Attention trader

dashboard_*.html/.py         # Interface trader
????????? dashboard_live.html      # [LEGACY - utilis?? V7.2.1]
????????? dashboard_v74.html       # CURRENT LIVE (terrain panel)
????????? dashboard_data_normalizer.py
????????? dashboard_v74_contract_check.py

scheduler_*.py               # Orchestration temps r??el
????????? scheduler_powerflow.py   # Orchestrateur principal
????????? scheduler_powerflow_turbo_wrapper.py  # Wrapper turbo LIVE

patch_*.py                   # Patches runtime V7.6+
telegram_*.py                # Alertes Telegram
```

### Base de donn??es

```sql
-- Tables principales
powerflow.db (15.6 MB)
????????? bars_m1, bars_m5, bars_m15, bars_m30, bars_h1, bars_h4  # Historique OHLC
????????? temporal_nodes           # Nodes d??tect??s
????????? scenes                   # Sc??nes H1 (COALITION_PUSH, TREND_CONTINUATION, etc.)
????????? memory_events            # ??v??nements m??moris??s
????????? dashboard_data           # ??tat dashboard JSON
```

---

## Workflow collaboratif 6 IA

### Dispatch par r??le

| IA | R??le | Status | Derni??re activit?? |
|---|---|---|---|
| **Claude Sonnet 4.5** | Chef orchestre, architecture, strat??gie | ???? ACTIVE | T001 Infrastructure automation |
| **GPT-1 Core Engine** | Modules Python `pf_*`, requ??tes SQL | ??? IDLE | pf_perception_spine patched |
| **GPT-2 Dashboard** | Interface HTML/JS, normalizers | ??? IDLE | Dashboard FR Trader V5 stable |
| **GPT-3 Scheduler** | Orchestration temps r??el, Telegram | ??? IDLE | scheduler_powerflow_turbo_wrapper.py |
| **GPT-4 Field Memory** | Analyses GBPUSD, film library | ??? IDLE | ANALYSE_GBPUSD_20260514 |
| **GPT Pro** | Refactoring majeur, probl??mes complexes | ??? IDLE | RAPPORT_V76 |

### Coordination

**Fichier central:** `DISPATCH_STATUS.json`  
**Checkpoints:** `Docs/Checkpoints/`  
**Lexique:** `Docs/LEXIQUE_MASTER.md`

**Workflow:**
1. Claude cr??e t??che ??? JSON mis ?? jour
2. GPT prend t??che ??? statut "in_progress"
3. GPT commit code ??? statut "completed"
4. Claude valide ??? archive

---

## Priorit??s actives

### P0 ??? CRITICAL
- ??? **T001** Infrastructure automation (Claude) ??? 80% complete

### P1 ??? HIGH
- ???? **T002** Refactor `pf_engine.py` V5 ??? V6 (GPT-1) ??? Pending
- ???? **T006** Consolidation `LEXIQUE_MASTER.md` (Claude) ??? In progress

### P2 ??? MEDIUM
- ???? **T003** Fix signature `pf_normalizer.py` (GPT-1) ??? Pending
- ???? **T004** Diagnostic USDJPY thin data (GPT Pro) ??? Pending

### P3 ??? LOW
- ??? **T005** Dashboard FR Trader V5 harmonisation (GPT-2) ??? Completed

**Voir `DISPATCH_STATUS.json` pour d??tails complets.**

---

## Scripts automatisation

### ???? Infrastructure (nouveaux)

| Script | Fonction | Fr??quence |
|--------|----------|-----------|
| `auto_git_sync.ps1` | Commit + push Git intelligent | Apr??s chaque session |
| `auto_checkpoint_claude.ps1` | Checkpoint fin session Claude | Fin session Claude |
| `sync_lexique.ps1` | Consolidation LEXIQUE_MASTER.md | Hebdomadaire |
| `cleanup_backups.ps1` | Nettoyage backups anarchiques | Mensuel |

### ?????? Runtime (existants)

| Script | Fonction |
|--------|----------|
| `run_powerflow_v767_reality_telegram_cycle.ps1` | Cycle complet perception + Telegram |
| `run_trader_perception_stack_once.py` | Stack perception trader |
| `run_powerflow_live_stack_once.py` | Stack live PowerFlow |

---

## Ressources cl??s

### Documentation

- **Lexique unifi??:** `Docs/LEXIQUE_MASTER.md`
- **Grammaire terrain:** `/mnt/project/07_GRAMMAIRE_NODE_ZONE_DRIVER_V767.md`
- **Film library GBPUSD:** `/mnt/project/09_FILM_LIBRARY_GBPUSD_V767_ENRICHED.md`
- **R??gles requalification:** `/mnt/project/10_PACKET_REQUALIFICATION_RULES_V767_ENRICHED.md`
- **Checkpoints:** `Docs/Checkpoints/`

### Liens externes

- **Git:** https://github.com/gestionzen57-alt/V7.git
- **Google Drive:** https://drive.google.com/drive/folders/13n3N2JDUcwf9AXwj7iV9VZkiH9e6bihw
- **Dashboard live:** `http://localhost:8880`

---

## Philosophy PowerFlow

### Concepts centraux

**PowerFlow n'est pas un syst??me d'analyse technique classique.**

PowerFlow est un **moteur de perception du flux** Forex.

**Mission:**
- Voir le flux
- D??tecter l'??v??nement
- Alerter vite
- Laisser le trader filtrer
- Laisser le trader d??cider

**R??les:**
- La machine ??? per??oit, mesure, nomme, alerte
- Le trader ??? filtre, arbitre, agit

### Doctrine centrale

**M1 est central** ??? Microfilm, naissance ??v??nements, inflexion pr??coce  
**Alerter vite** ??? Alerte ??? ordre, c'est une perception transmise  
**Pas de nounou** ??? Pas de rappels g??n??riques risque financier  
**Flux vivant** ??? March?? = organisme en mouvement, pas chandeliers isol??s  
**Comportemental** ??? Force relative, asym??tries, leader/follower  

---

## Lexique rapide

| Terme FR | Traduction | D??finition |
|----------|------------|------------|
| **Tension accumul??e** | Accumulated tension | Force potentielle comprim??e, pr??te ?? rel??cher |
| **??lastique charg??** | Overloaded elastic | Zone ayant accumul?? trop de pression d'un c??t?? |
| **Pullback absorb??** | Absorbed pullback | Repli rencontrant demande/offre imm??diate |
| **Node temporel** | Temporal node | Point pivot o?? plusieurs forces convergent |
| **Force relative** | Relative strength | Comportement devise vs panier USD |
| **Coalition** | Coalition | Devises majeures align??es poussant USD m??me sens |
| **Second leg** | Second leg | 2??me vague apr??s consolidation, souvent plus puissante |

**Lexique complet:** `Docs/LEXIQUE_MASTER.md`

---

## Garde-fous V7.6.7

### ??? INTERDIT

- Modifier `powerflow.db` manuellement
- Casser P0 PASS_STRICT
- Violer Dashboard contract V7.4
- Passer en V7.7 avant stabilit?? confirm??e
- ??diter `CLAUDE.md` manuellement (auto-g??n??r??)

### ??? AUTORIS??

- Extension/consolidation V7.6.7
- Patches runtime dans `patch/`
- Nouveaux modules `pf_*.py` si tests OK
- Documentation `Docs/`
- Scripts automation `scripts/`

---

## Reprise de session Claude

### Prompt minimal

```
PowerFlow V7.6.7 ??? Reprise session

Consulte CLAUDE.md pour contexte complet.
Consulte DISPATCH_STATUS.json pour t??ches actives.

Prochaine priorit??: [indiquer]
```

### Fichiers ?? charger projet Claude

- `00_README_PACK_POWERFLOW_V767_COLLAB.md`
- `01_RAPPORT_COMPLET_POWERFLOW_V767_FIELD_MEMORY.md`
- `03_CURRENT_STATE_POWERFLOW_V767.md`
- `04_DOCTRINE_MANIFESTE_POWERFLOW_V767.md`
- `06_NOMENCLATURE_BRIQUES_CORE_POWERFLOW_V767.md`
- `07_GRAMMAIRE_NODE_ZONE_DRIVER_V767.md`
- `09_FILM_LIBRARY_GBPUSD_V767_ENRICHED.md`
- `10_PACKET_REQUALIFICATION_RULES_V767_ENRICHED.md`
- `12_LEXIQUE_FR_TRADER_POWERFLOW_V767.md`

---

*Document vivant auto-g??n??r?? ??? Ne pas ??diter manuellement*  
*Mis ?? jour automatiquement par `auto_checkpoint_claude.ps1`*  
*Derni??re modification: 2026-05-15 10:30*













### ??? Termin??
- **T005** Dashboard FR Trader V5 harmonisation ??? Completed by GPT-2 Dashboard

<!-- GPT3_SCHEDULER_CURRENT_STATE_BEGIN -->
## GPT-3 Scheduler ??? Current State

Updated: 2026-05-15 20:58:14 +02:00

### Scheduler / Telegram status

- T007 completed: V7.6 Telegram cycle defaults to dry-run.
- T010 completed: Telegram dry-run stdout is UTF-8 safe.
- T011/T012 completed: Core/B8 scheduler scope can be multi-symbol while trader/Telegram tail remains GBPUSD.
- T013B/T013C completed: OVERLAP_SKIP no longer blocks analytical continuation under --continue-on-error.
- T015 completed: B8 FX cohort scope extended and verified on 13 symbols.

### Active B8 / multidevise scope

$coreSymbols

### Architecture note

GBPUSD remains the primary traded/execution symbol.

Do not require dense M1 / tickvolume-per-second data on all cohort pairs. M1/tickvolume-sec is intentionally reserved for GBPUSD to avoid DB growth.

Context symbols are used for coalition, antagonists, gravity, polarity and tempo.

### Recommended next task

T017 ??? make B8 role-aware:

- execution_symbol = GBPUSD
- context_symbols = USD cohort + GBP cohort
- Do not mark B8 degraded only because context symbols lack M1/tickvolume-sec density.
- Add statuses such as:
  - GBPUSD_FULL_STACK_READY
  - USD_INDEX_CONTEXT_READY
  - GBP_INDEX_CONTEXT_READY
  - B8_CONTEXT_READY
  - B8_CONTEXT_DEGRADED

### Guardrails

- No DB modification.
- No Dashboard V7.4 / FR Trader V5 modification.
- No BUY/SELL.
- Telegram stays context transmission only.
- Scheduler orchestrates only.
<!-- GPT3_SCHEDULER_CURRENT_STATE_END -->



```

---

# SOURCE: Docs\T006_Source_Staging\FILM_LIBRARY__POWERFLOW_FILM_LIBRARY_GBPUSD_V76_FINAL.md

SHA256: A5F3386CC8825ED5C5C908B18F235E4EA01CEC791B9279B932CA2582D882332C
BYTES: 17330

```text
# POWERFLOW FILM LIBRARY GBPUSD V7.6 FINAL

## 0. Doctrine

La film library sert Ã  reconnaÃ®tre des sÃ©quences et outcomes.
Elle ne dÃ©cide pas le trade.
Elle aide B6 Ã  comparer le film courant aux films dÃ©jÃ  vus.

PowerFlow V7.6 doit mÃ©moriser des films, pas seulement des Ã©vÃ©nements isolÃ©s. Un packet brut n'est utile que s'il est requalifiÃ© par le film courant, la zone active, le prix, la propagation et la visibilitÃ© data.

## 1. Tableau global des journÃ©es

| DATE | FILM_NAME | DOMINANT_STRUCTURE | KEY_EVENT | PRICE_ARBITER | EXPECTED_REQUALIFICATION | DATA_LIMITS | QA_TARGET |
|---|---|---|---|---|---|---|---|
| 2026-05-06 | `RELEASE_UP_FROM_LOW_THEN_HIGH_ZONE_EXHAUSTION` | Low-zone build puis high-zone consumed | Release UP validÃ©e puis exhaustion | Acceptation UP initiale, puis rejet/consommation high-zone | `PAIR_UP` tardif -> `CONSUMED` / `EXHAUSTION_RISK`; `PAIR_DOWN` -> `POST_RELEASE_UNWIND` | Prix + zone + propagation requis | `QA-FILM-20260506` |
| 2026-05-07 | `LATE_HIGH_REJECTION_WITH_DEEP_UNWIND` | High tardif rejetÃ© | `HIGH_ZONE_REJECTION` | Rejet du high puis acceptation plus basse | `PAIR_DOWN` -> `POST_HIGH_UNWIND` / `DEEP_POST_HIGH_UNWIND` | Distinguer pullback normal vs rejet de zone haute | `QA-FILM-20260507` |
| 2026-05-08 | `RELEASE_UP_VALIDATED_CLOSE_NEAR_HIGH` | Release UP acceptÃ©e jusqu'Ã  close | Pullback absorbÃ© | Prix accepte plus haut et clÃ´ture proche high | `PAIR_UP` -> `RELEASE_UP_VALIDATED` / `UP_CONTINUATION_ACCEPTED` | Ne pas valider sans prix + propagation | `QA-FILM-20260508` |
| 2026-05-11 | `RELEASE_UP_FROM_COMPRESSION_THEN_SECOND_LEG_UP_AND_EXHAUSTION` | Compression, false births, release, second leg, exhaustion | `B3+B2` false births puis release UP | False births invalidÃ©s, release validÃ©e par acceptation | `B3+B2` -> `EVENT_STACK`; second leg -> `SECOND_LEG_UP`; late UP -> `EXHAUSTION` | Session / timing obligatoires | `QA-FILM-20260511` |
| 2026-05-12 | `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK_AND_LATE_COUNTER_BREATH` | Release down + lower lock | `LOWER_LOCK` | Prix accepte lower zone; UP inverse reste rÃ©action | `PAIR_UP` -> `COUNTER_BREATH_UP` par dÃ©faut aprÃ¨s release down | last_structural_event indispensable | `QA-FILM-20260512` |
| 2026-05-13 | `POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN` | Counter-breath rejetÃ© puis second leg down | `COUNTER_BREATH_REJECTED` | Rejet UP puis lower low | `PAIR_DOWN` -> `SECOND_LEG_DOWN`; `PAIR_UP` tardif -> `POST_LOW_COUNTER_BREATH` / `LATE_THIN_BOUNCE` | Prix doit trancher rejet vs rÃ©intÃ©gration | `QA-FILM-20260513` |
| 2026-05-14 | `LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL` | Lower-zone range + lecture partielle | `READING_PARTIAL` | Confirmation pending si M1 absent / packets stale | `PAIR_UP` -> `POST_LOW_REACTION` ou `COUNTER_BREATH`; packet -> `DEGRADED` | `M1_MISSING`, `PACKETS_STALE`, `MICROFILM_MISSING` visibles | `QA-FILM-20260514` |

## 2. Film card â€” 2026-05-06

Date : 2026-05-06
Film name : `RELEASE_UP_FROM_LOW_THEN_HIGH_ZONE_EXHAUSTION`
Contexte : Low-zone building, release UP validÃ©e, puis high-zone exhaustion.
Dernier Ã©vÃ©nement structurel : `RELEASE_UP_VALIDATED_THEN_HIGH_ZONE_EXHAUSTION`
Zone active : Low zone au dÃ©part, high zone consommÃ©e ensuite.
Mouvement dominant : UP initial validÃ©, puis unwind post-extension.
RÃ´le du mouvement : Release fraÃ®che puis signal UP tardif consommÃ©.
Packets dÃ©tectÃ©s : `PAIR_UP`, `HOT`, puis `PAIR_DOWN` / unwind.
Confirmation prix : acceptation plus haute au moment de la release; aprÃ¨s high-zone, absence d'acceptation supplÃ©mentaire ou rejet = consommation.
Invalidation prix : `PAIR_UP` tardif invalidÃ© si lower close / rejet high-zone / perte acceptation.
Ce que PowerFlow doit comprendre : UP validÃ© puis signaux UP tardifs reclassÃ©s `CONSUMED` / `EXHAUSTION_RISK`.
Ce que PowerFlow doit Ã©viter : appeler un nouveau `PAIR_UP` frais aprÃ¨s high dÃ©jÃ  fait.
RÃ¨gle candidate : aprÃ¨s `RELEASE_UP_VALIDATED`, si high-zone active puis extension consommÃ©e, `PAIR_UP` devient `UP_CONSUMED` ou `HIGH_ZONE_EXHAUSTION`.
QA attendue : `QA-FILM-20260506`.
Memory signature : `LOW_ZONE_BUILDING -> RELEASE_UP_VALIDATED -> HIGH_ZONE_EXHAUSTION -> POST_RELEASE_UNWIND`.
Next expected behavior : surveiller rejet high-zone ou unwind post-release, pas fresh release automatique.
False positive risk : late `PAIR_UP`, HOT aprÃ¨s extension, B3/B2 tardif surinterprÃ©tÃ©.

## 3. Film card â€” 2026-05-07

Date : 2026-05-07
Film name : `LATE_HIGH_REJECTION_WITH_DEEP_UNWIND`
Contexte : Rebuild post-release, extension UP tardive, high-zone rejection, unwind profond.
Dernier Ã©vÃ©nement structurel : `HIGH_ZONE_REJECTION`.
Zone active : High zone rejetÃ©e.
Mouvement dominant : Deep unwind aprÃ¨s rejet.
RÃ´le du mouvement : `POST_HIGH_UNWIND`, pas `PAIR_DOWN` gÃ©nÃ©rique.
Packets dÃ©tectÃ©s : late `PAIR_UP`, `HOT`, `PAIR_DOWN`.
Confirmation prix : rejet du high, acceptation progressive plus basse.
Invalidation prix : `POST_HIGH_UNWIND` invalidÃ© seulement si rÃ©intÃ©gration high-zone acceptÃ©e.
Ce que PowerFlow doit comprendre : aprÃ¨s high tardif rejetÃ©, DOWN = unwind structurel.
Ce que PowerFlow doit Ã©viter : traiter `PAIR_DOWN` comme une naissance indÃ©pendante du contexte.
RÃ¨gle candidate : `HIGH_ZONE_REJECTION + PAIR_DOWN + lower acceptance -> POST_HIGH_UNWIND`.
QA attendue : `QA-FILM-20260507`.
Memory signature : `POST_RELEASE_REBUILD -> LATE_UP_EXTENSION -> HIGH_ZONE_REJECTION -> DEEP_POST_HIGH_UNWIND`.
Next expected behavior : continuation unwind tant que le prix ne rÃ©intÃ¨gre pas la high zone.
False positive risk : `HOT` sans dÃ©placement prix, late UP pris pour continuation.

## 4. Film card â€” 2026-05-08

Date : 2026-05-08
Film name : `RELEASE_UP_VALIDATED_CLOSE_NEAR_HIGH`
Contexte : Low-zone rebuild, release UP validÃ©e, pullback absorbÃ©, continuation acceptÃ©e.
Dernier Ã©vÃ©nement structurel : `RELEASE_UP_VALIDATED`.
Zone active : Low-zone rebuild vers acceptation supÃ©rieure.
Mouvement dominant : Continuation UP acceptÃ©e.
RÃ´le du mouvement : release validÃ©e puis pullback absorbÃ©.
Packets dÃ©tectÃ©s : `PAIR_UP`, pullback `PAIR_DOWN`, continuation `PAIR_UP`.
Confirmation prix : prix accepte plus haut, pullback ne casse pas la structure, close near high.
Invalidation prix : pullback devient invalidant si close basse et perte d'acceptation.
Ce que PowerFlow doit comprendre : release validÃ©e = prix + zone + propagation + pullback absorbÃ©.
Ce que PowerFlow doit Ã©viter : considÃ©rer tout `PAIR_DOWN` post-release comme reversal.
RÃ¨gle candidate : `RELEASE_UP_VALIDATED + pullback held + close near high -> UP_CONTINUATION_ACCEPTED`.
QA attendue : `QA-FILM-20260508`.
Memory signature : `LOW_ZONE_REBUILD -> RELEASE_UP_VALIDATED -> PULLBACK_ABSORBED -> CONTINUATION_UP -> CLOSE_NEAR_HIGH`.
Next expected behavior : continuation acceptÃ©e tant que le prix confirme au-dessus de la zone de pullback.
False positive risk : release validÃ©e sans prix, pullback absorbÃ© non reconnu.

## 5. Film card â€” 2026-05-11

Date : 2026-05-11
Film name : `RELEASE_UP_FROM_COMPRESSION_THEN_SECOND_LEG_UP_AND_EXHAUSTION`
Contexte : PrÃ©-London false births, compression, release UP, pullback, second leg, exhaustion.
Dernier Ã©vÃ©nement structurel : `SECOND_LEG_UP_THEN_HIGH_ZONE_EXHAUSTION`.
Zone active : compression puis high-zone consommÃ©e.
Mouvement dominant : UP en deux jambes puis exhaustion.
RÃ´le du mouvement : false births avant validation, release, second leg, exhaustion.
Packets dÃ©tectÃ©s : `B3+B2`, `B4`, `P1`, `PAIR_UP`, `PAIR_DOWN`, `HOT`.
Confirmation prix : false births non confirmÃ©s; release validÃ©e uniquement si prix accepte + propagation.
Invalidation prix : `B3+B2` sans prix = `EVENT_STACK`; late UP aprÃ¨s second leg = consumed.
Ce que PowerFlow doit comprendre : `B3+B2` seul = `EVENT_STACK`, pas naissance validÃ©e.
Ce que PowerFlow doit Ã©viter : valider une birth prÃ©-London sans prix + B7.
RÃ¨gle candidate : `B3+B2 -> EVENT_STACK`; `B3+B4+P1+price+B7 -> RELEASE_CANDIDATE/VALIDATED`.
QA attendue : `QA-FILM-20260511`.
Memory signature : `PRE_LONDON_FALSE_BIRTHS -> MIDDAY_RELEASE_UP -> POST_RELEASE_PULLBACK -> SECOND_LEG_UP -> HIGH_ZONE_EXHAUSTION -> LATE_UNWIND`.
Next expected behavior : second leg possible aprÃ¨s pullback absorbÃ©, puis exhaustion si high-zone consommÃ©e.
False positive risk : false birth, LTF_ONLY surinterprÃ©tÃ©, late second-leg UP survalidÃ©.

## 6. Film card â€” 2026-05-12

Date : 2026-05-12
Film name : `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK_AND_LATE_COUNTER_BREATH`
Contexte : Asia high failure, London release down, lower price acceptance, counter-breath tardif.
Dernier Ã©vÃ©nement structurel : `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK`.
Zone active : lower zone acceptÃ©e / locked.
Mouvement dominant : DOWN release puis counter-breath UP.
RÃ´le du mouvement : `PAIR_UP` aprÃ¨s release down = counter-breath par dÃ©faut.
Packets dÃ©tectÃ©s : `PAIR_DOWN`, `LOWER_LOCK`, `PAIR_UP`, `HOT` Ã©ventuel.
Confirmation prix : lower acceptance confirme release down; UP inverse doit rÃ©intÃ©grer pour changer de rÃ´le.
Invalidation prix : `COUNTER_BREATH_UP` invalidÃ© si rejet et second low test.
Ce que PowerFlow doit comprendre : last structural event domine la lecture suivante.
Ce que PowerFlow doit Ã©viter : transformer une rÃ©action UP en fresh release UP.
RÃ¨gle candidate : aprÃ¨s `RELEASE_DOWN_VALIDATED`, tout `PAIR_UP` devient `COUNTER_BREATH_UP` tant que le prix ne rÃ©intÃ¨gre pas.
QA attendue : `QA-FILM-20260512`.
Memory signature : `ASIA_HIGH_FAILURE -> LONDON_RELEASE_DOWN -> LOWER_PRICE_ACCEPTANCE -> POST_RELEASE_COUNTER_BREATH -> SECOND_LOW_TEST -> LATE_COUNTER_BOUNCE`.
Next expected behavior : second low test ou counter-breath tardif selon acceptation prix.
False positive risk : PAIR_UP brut, post-low reaction confondue avec nouvelle phase.

## 7. Film card â€” 2026-05-13

Date : 2026-05-13
Film name : `POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN`
Contexte : lower acceptance, counter-breath UP, rejet, second leg down, lower low.
Dernier Ã©vÃ©nement structurel : `COUNTER_BREATH_REJECTED`.
Zone active : lower acceptance puis lower low.
Mouvement dominant : second leg down aprÃ¨s rejet.
RÃ´le du mouvement : rejet du counter-breath devient carburant du second leg.
Packets dÃ©tectÃ©s : `PAIR_UP`, `PAIR_DOWN`, `HOT`, low retest.
Confirmation prix : UP rejetÃ©, lower low confirme second leg.
Invalidation prix : second leg invalidÃ© si rÃ©intÃ©gration supÃ©rieure acceptÃ©e.
Ce que PowerFlow doit comprendre : `PAIR_DOWN` aprÃ¨s counter-breath rejetÃ© = `SECOND_LEG_DOWN`.
Ce que PowerFlow doit Ã©viter : lire le second leg comme simple PAIR_DOWN gÃ©nÃ©rique.
RÃ¨gle candidate : `COUNTER_BREATH_REJECTED + lower acceptance/lower low -> SECOND_LEG_DOWN`.
QA attendue : `QA-FILM-20260513`.
Memory signature : `POST_RELEASE_LOWER_ACCEPTANCE -> LONDON_COUNTER_BREATH_UP -> COUNTER_BREATH_REJECTED -> SECOND_LEG_DOWN -> LOWER_LOW -> POST_LOW_COUNTER_BREATH -> LATE_THIN_BOUNCE`.
Next expected behavior : lower low puis post-low reaction / late thin bounce possible.
False positive risk : late bounce surinterprÃ©tÃ©, rejection non reconnue.

## 8. Film card â€” 2026-05-14

Date : 2026-05-14
Film name : `LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL`
Contexte : lower-zone range, counter-breath UP, rejet, low retest, post-low reaction avec visibilitÃ© partielle.
Dernier Ã©vÃ©nement structurel : `COUNTER_BREATH_REJECTED_IN_LOWER_ZONE_RANGE`.
Zone active : `LOWER_ZONE_RANGE_ACTIVE`.
Mouvement dominant : range lower-zone + rÃ©actions.
RÃ´le du mouvement : `POST_LOW_REACTION`, pas fresh release sans acceptation.
Packets dÃ©tectÃ©s : `PAIR_UP`, `PAIR_DOWN`, stale packets, M1 missing.
Confirmation prix : pending si donnÃ©es partielles; validation seulement par cassure/reintÃ©gration propre.
Invalidation prix : packet invalidÃ© si prix contredit la direction brute ou si stale trop Ã©levÃ©.
Ce que PowerFlow doit comprendre : `READING_PARTIAL` doit Ãªtre visible en haut si M1 manque / packets stale.
Ce que PowerFlow doit Ã©viter : masquer les limites data ou survalider une lecture aveugle.
RÃ¨gle candidate : `M1_MISSING OR PACKETS_STALE -> READING_PARTIAL + DEGRADED_PACKET`.
QA attendue : `QA-FILM-20260514`.
Memory signature : `LOWER_ZONE_RANGE_ACTIVE -> COUNTER_BREATH_UP -> COUNTER_BREATH_REJECTED -> LOW_RETEST -> POST_LOW_REACTION`.
Next expected behavior : attendre arbitrage prix entre rÃ©intÃ©gration et cassure basse; ne pas durcir sans data.
False positive risk : stale packet, B8 faible, LTF_ONLY surinterprÃ©tÃ©.

## 9. Patterns rÃ©currents

| Pattern | Signature | Conditions | PiÃ¨ge | Requalification attendue | Champs terrain_packet concernÃ©s |
|---|---|---|---|---|---|
| release candidate validÃ©e | `B3+B4+P1+price+B7` | zone active cohÃ©rente, prix accepte, propagation non dÃ©gradÃ©e | valider avec B3+B2 seul | `RELEASE_VALIDATED` | `film_state`, `price_confirmation`, `propagation_state`, `packet_quality` |
| false birth | `B3+B2` sans prix / sans propagation | souvent prÃ©-session ou compression instable | naissance fictive | `EVENT_STACK` / `FALSE_BIRTH` | `packet_quality`, `data_visibility`, `watch_condition` |
| high rejection | high-zone actif puis prix rejette | extension tardive ou high dÃ©jÃ  fait | lire DOWN comme signal neuf | `HIGH_ZONE_REJECTION` puis `POST_HIGH_UNWIND` | `current_zone`, `last_structural_event`, `qualified_bias` |
| lower lock | release down + lower acceptance | prix accepte lower zone | lire UP comme fresh release | `LOWER_LOCK` | `current_zone`, `price_confirmation`, `last_structural_event` |
| counter-breath | rÃ©action inverse aprÃ¨s release | direction inverse sans rÃ©intÃ©gration acceptÃ©e | confondre rÃ©action et nouvelle phase | `COUNTER_BREATH_UP/DOWN` | `current_move_role`, `qualified_bias`, `invalidation_condition` |
| counter-breath rejected | counter-breath Ã©choue | rejet prix + retour dans structure dominante | ne pas dÃ©tecter carburant second leg | `COUNTER_BREATH_REJECTED` | `last_structural_event`, `price_confirmation` |
| second leg | reprise aprÃ¨s pullback/counter-breath rejetÃ© | prix confirme continuation / lower low / higher continuation | `PAIR_DOWN/UP` brut | `SECOND_LEG_UP/DOWN` | `current_move_role`, `qualified_bias`, `watch_condition` |
| pullback absorbed | pullback post-release qui ne casse pas | prix tient zone et reprend | lire comme reversal | `PULLBACK_ABSORBED` | `price_confirmation`, `packet_quality`, `current_zone` |
| late thin bounce | rÃ©action tardive faible | session tardive, data faible, zone dÃ©jÃ  travaillÃ©e | survalider en release | `LATE_THIN_BOUNCE` | `session_context`, `data_visibility`, `packet_quality` |
| exhaustion / consumed | signal aprÃ¨s extension/high done | high-zone active, absence d'acceptation nouvelle | fresh release tardive | `EXHAUSTION` / `CONSUMED` | `is_event_consumed`, `current_zone`, `qualified_bias` |
| reading partial | M1 absent / packets stale / coverage faible | visibilitÃ© data dÃ©gradÃ©e | cacher l'aveuglement | `READING_PARTIAL` | `data_visibility`, `packet_quality`, `watch_condition` |

## 10. PiÃ¨ges rÃ©currents

- `B3+B2` trop nerveux : doit produire `EVENT_STACK`, pas naissance validÃ©e.
- `PAIR_UP` aprÃ¨s release down : counter-breath par dÃ©faut tant que le prix ne rÃ©intÃ¨gre pas.
- `HOT` sans dÃ©placement prix : `PRESSURE_PENDING`, pas Ã©vÃ©nement confirmÃ©.
- `LTF_ONLY` surinterprÃ©tÃ© : propagation absente = packet local / watch.
- Stale packet : reclasser `READING_PARTIAL` ou `DEGRADED`.
- B8 faible : `HONEST_UNKNOWN`, pas confirmation dure.
- High zone dÃ©jÃ  consommÃ©e : `PAIR_UP` tardif = `CONSUMED` / `EXHAUSTION_RISK`.
- Late bounce : informer, ne pas transformer en release sans prix + propagation.

## 11. Usage par B6

B6 doit mÃ©moriser les films sous forme comparable :

| Champ B6 | Usage |
|---|---|
| `FILM_PATTERN` | Nom stable du film ou pattern dominant. |
| `SEQUENCE` | ChaÃ®ne ordonnÃ©e des Ã©tats terrain. |
| `TRIGGER` | Ã‰vÃ©nement ou combinaison initiale qui dÃ©clenche l'attention. |
| `CONTEXT` | Session, zone, dernier Ã©vÃ©nement structurel, phase du film. |
| `PRICE_ARBITER` | Ce que le prix doit confirmer, invalider ou laisser pending. |
| `OUTCOME` | Outcome observÃ© du film calibrÃ©. |
| `INVALIDATION` | Condition qui aurait cassÃ© la lecture. |
| `NEXT_EXPECTED_BEHAVIOR` | Comportement suivant attendu comme hypothÃ¨se de film, pas ordre. |
| `FALSE_POSITIVE` | PiÃ¨ge rÃ©current observÃ©. |

B6 ne doit jamais produire de recommandation de trading. Il doit seulement comparer : film courant vs films calibrÃ©s.

## 12. Acceptance Criteria

- Chaque journÃ©e a une memory card complÃ¨te.
- Chaque journÃ©e mappe vers au moins une rÃ¨gle QA.
- Aucune journÃ©e ne produit une recommandation de trade.
- `data_visibility` est prÃ©sente.
- `price_confirmation` est prÃ©sente.
- Les films sont compatibles `terrain_packet_v76_0`.
- `PAIR_UP`, `PAIR_DOWN`, `HOT`, `B3+B2`, `B3+B4+P1` sont toujours requalifiÃ©s par film + zone + prix + propagation + data.
- Les cas `READING_PARTIAL`, `MICROFILM_MISSING`, `PACKETS_STALE`, `HONEST_UNKNOWN` sont visibles quand requis.

```

---

# SOURCE: Docs\T006_Source_Staging\FILM_LIBRARY__POWERFLOW_FILM_MEMORY_CARDS_GBPUSD_V76.md

SHA256: 14B5879E3DB204CFF15853905B0961F5D590FB6F1A7E14DBA99E0E64EE0975BC
BYTES: 10071

```text
# POWERFLOW FILM MEMORY CARDS GBPUSD V7.6

Ces cartes sont destinÃ©es Ã  B6 Memory et Ã  la QA V7.6. Elles ne dÃ©crivent pas des ordres. Elles dÃ©crivent des films calibrÃ©s.

## Film memory card â€” 2026-05-06

| Field | Value |
|---|---|
| Date | 2026-05-06 |
| Symbol | GBPUSD |
| Film name | `RELEASE_UP_FROM_LOW_THEN_HIGH_ZONE_EXHAUSTION` |
| Film state | `HIGH_ZONE_EXHAUSTION_AFTER_RELEASE_UP` |
| Last structural event | `RELEASE_UP_VALIDATED_THEN_HIGH_ZONE_EXHAUSTION` |
| Dominant zone status | `LOW_ZONE_BUILDING_TO_HIGH_ZONE_CONSUMED` |
| Dominant move role | `UP_RELEASE_THEN_LATE_UP_CONSUMED` |
| Raw bias risks | `PAIR_UP_AFTER_HIGH_ALREADY_DONE`, `HOT_AFTER_EXTENSION`, `UP_SIGNAL_CONSUMED` |
| Expected qualified bias | `RELEASE_UP_VALIDATED`, `HIGH_ZONE_EXHAUSTION`, `UP_CONSUMED`, `POST_RELEASE_UNWIND` |
| Packet quality expected | `FRESH_WHEN_PRICE_ACCEPTS_UP_THEN_CONSUMED_AFTER_HIGH_ZONE` |
| Price confirmation expected | UP accepted while price holds/extends; late UP invalidated if high zone rejects or no further acceptance |
| Data visibility notes | Data must expose price acceptance, zone transition and propagation before release validation. |
| Memory signature | `LOW_ZONE_BUILDING -> RELEASE_UP_VALIDATED -> HIGH_ZONE_EXHAUSTION -> POST_RELEASE_UNWIND` |
| False positive risks | `Treating late PAIR_UP as fresh release`, `Ignoring consumed high zone`, `HOT after extension misread as new birth` |
| QA targets | `QA-FILM-20260506`, `QA-PATTERN-EXHAUSTION-CONSUMED`, `QA-PATTERN-RELEASE-VALIDATED` |

## Film memory card â€” 2026-05-07

| Field | Value |
|---|---|
| Date | 2026-05-07 |
| Symbol | GBPUSD |
| Film name | `LATE_HIGH_REJECTION_WITH_DEEP_UNWIND` |
| Film state | `POST_HIGH_UNWIND_AFTER_LATE_HIGH_REJECTION` |
| Last structural event | `HIGH_ZONE_REJECTION` |
| Dominant zone status | `HIGH_ZONE_REJECTED_LATE_SESSION` |
| Dominant move role | `DEEP_POST_HIGH_UNWIND` |
| Raw bias risks | `PAIR_DOWN_GENERIC`, `LATE_UP_EXTENSION_MISREAD`, `HOT_WITHOUT_ACCEPTANCE` |
| Expected qualified bias | `HIGH_ZONE_REJECTION`, `POST_HIGH_UNWIND`, `DEEP_POST_HIGH_UNWIND` |
| Packet quality expected | `DOWN_PACKET_VALID_AS_UNWIND_ONLY_AFTER_HIGH_REJECTION_AND_PRICE_CONFIRMATION` |
| Price confirmation expected | High rejected; downside accepted by lower closes / unwind continuation. |
| Data visibility notes | Need enough price and zone visibility to distinguish rejection from normal pullback. |
| Memory signature | `POST_RELEASE_REBUILD -> LATE_UP_EXTENSION -> HIGH_ZONE_REJECTION -> DEEP_POST_HIGH_UNWIND` |
| False positive risks | `Calling every PAIR_DOWN fresh release`, `Missing late high rejection`, `Overweighting B3/B2 without price` |
| QA targets | `QA-FILM-20260507`, `QA-PATTERN-HIGH-REJECTION`, `QA-PATTERN-POST-HIGH-UNWIND` |

## Film memory card â€” 2026-05-08

| Field | Value |
|---|---|
| Date | 2026-05-08 |
| Symbol | GBPUSD |
| Film name | `RELEASE_UP_VALIDATED_CLOSE_NEAR_HIGH` |
| Film state | `RELEASE_UP_ACCEPTED_CONTINUATION` |
| Last structural event | `RELEASE_UP_VALIDATED` |
| Dominant zone status | `LOW_ZONE_REBUILD_TO_HIGH_ACCEPTANCE` |
| Dominant move role | `UP_CONTINUATION_AFTER_PULLBACK_ABSORBED` |
| Raw bias risks | `PAIR_UP_GENERIC`, `PAIR_DOWN_PULLBACK_MISREAD_AS_REVERSAL`, `HOT_NEEDS_PRICE_ACCEPTANCE` |
| Expected qualified bias | `RELEASE_UP_VALIDATED`, `PULLBACK_ABSORBED`, `UP_CONTINUATION_ACCEPTED`, `CLOSE_NEAR_HIGH` |
| Packet quality expected | `HIGH_QUALITY_WHEN_PULLBACK_ABSORBED_AND_CLOSE_REMAINS_NEAR_HIGH` |
| Price confirmation expected | Higher acceptance; pullback fails to invalidate; close near high validates continuation. |
| Data visibility notes | Requires price acceptance plus propagation; no release validation from B3+B4+P1 alone. |
| Memory signature | `LOW_ZONE_REBUILD -> RELEASE_UP_VALIDATED -> PULLBACK_ABSORBED -> CONTINUATION_UP -> CLOSE_NEAR_HIGH` |
| False positive risks | `Treating pullback as structural reversal`, `Validating release without close/acceptance`, `Ignoring propagation state` |
| QA targets | `QA-FILM-20260508`, `QA-PATTERN-PULLBACK-ABSORBED`, `QA-PATTERN-UP-CONTINUATION-ACCEPTED` |

## Film memory card â€” 2026-05-11

| Field | Value |
|---|---|
| Date | 2026-05-11 |
| Symbol | GBPUSD |
| Film name | `RELEASE_UP_FROM_COMPRESSION_THEN_SECOND_LEG_UP_AND_EXHAUSTION` |
| Film state | `COMPRESSION_RELEASE_SECOND_LEG_EXHAUSTION` |
| Last structural event | `SECOND_LEG_UP_THEN_HIGH_ZONE_EXHAUSTION` |
| Dominant zone status | `COMPRESSION_TO_HIGH_ZONE_CONSUMED` |
| Dominant move role | `RELEASE_UP_THEN_SECOND_LEG_UP_THEN_EXHAUSTION` |
| Raw bias risks | `B3_B2_FALSE_BIRTH`, `EVENT_STACK_MISREAD_AS_BIRTH`, `LATE_UP_AFTER_SECOND_LEG` |
| Expected qualified bias | `EVENT_STACK`, `FALSE_BIRTH`, `RELEASE_UP_VALIDATED`, `POST_RELEASE_PULLBACK`, `SECOND_LEG_UP`, `HIGH_ZONE_EXHAUSTION` |
| Packet quality expected | `B3+B2_ONLY_EVENT_STACK; RELEASE_ONLY_AFTER_B4_P1_PRICE_B7; LATE_SECOND_LEG_CONSUMED` |
| Price confirmation expected | False births invalidated before London; later release requires acceptance; exhaustion after high zone consumes UP. |
| Data visibility notes | Need pre-London segmentation; session context matters; false births must stay labelled. |
| Memory signature | `PRE_LONDON_FALSE_BIRTHS -> MIDDAY_RELEASE_UP -> POST_RELEASE_PULLBACK -> SECOND_LEG_UP -> HIGH_ZONE_EXHAUSTION -> LATE_UNWIND` |
| False positive risks | `B3+B2 over-validation`, `Second leg mistaken for new fresh release`, `Late unwind ignored` |
| QA targets | `QA-FILM-20260511`, `QA-PATTERN-FALSE-BIRTH`, `QA-PATTERN-SECOND-LEG`, `QA-PATTERN-EXHAUSTION-CONSUMED` |

## Film memory card â€” 2026-05-12

| Field | Value |
|---|---|
| Date | 2026-05-12 |
| Symbol | GBPUSD |
| Film name | `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK_AND_LATE_COUNTER_BREATH` |
| Film state | `RELEASE_DOWN_LOWER_LOCK_COUNTER_BREATH` |
| Last structural event | `LONDON_RELEASE_DOWN_WITH_LOWER_LOCK` |
| Dominant zone status | `LOWER_ZONE_ACCEPTED_LOCKED` |
| Dominant move role | `DOWN_RELEASE_THEN_COUNTER_BREATH_UP` |
| Raw bias risks | `PAIR_UP_AFTER_RELEASE_DOWN`, `POST_LOW_REACTION_MISREAD_AS_FRESH_UP`, `LATE_COUNTER_BOUNCE` |
| Expected qualified bias | `RELEASE_DOWN_VALIDATED`, `LOWER_LOCK`, `COUNTER_BREATH_UP`, `SECOND_LOW_TEST`, `LATE_COUNTER_BOUNCE` |
| Packet quality expected | `PAIR_UP_AFTER_RELEASE_DOWN_REACTION_NOT_NEW_RELEASE_UNLESS_PRICE_REINTEGRATES` |
| Price confirmation expected | Lower acceptance confirms down; PAIR_UP remains counter-breath until reintegration is accepted. |
| Data visibility notes | Must preserve last_structural_event; without it PAIR_UP becomes misleading. |
| Memory signature | `ASIA_HIGH_FAILURE -> LONDON_RELEASE_DOWN -> LOWER_PRICE_ACCEPTANCE -> POST_RELEASE_COUNTER_BREATH -> SECOND_LOW_TEST -> LATE_COUNTER_BOUNCE` |
| False positive risks | `Calling counter-breath a fresh UP release`, `Forgetting lower lock`, `Missing second low test` |
| QA targets | `QA-FILM-20260512`, `QA-PATTERN-LOWER-LOCK`, `QA-PATTERN-COUNTER-BREATH` |

## Film memory card â€” 2026-05-13

| Field | Value |
|---|---|
| Date | 2026-05-13 |
| Symbol | GBPUSD |
| Film name | `POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN` |
| Film state | `COUNTER_BREATH_REJECTED_SECOND_LEG_DOWN` |
| Last structural event | `COUNTER_BREATH_REJECTED` |
| Dominant zone status | `LOWER_ACCEPTANCE_THEN_LOWER_LOW` |
| Dominant move role | `SECOND_LEG_DOWN_AFTER_REJECTED_COUNTER_BREATH` |
| Raw bias risks | `PAIR_UP_COUNTER_BREATH_MISREAD`, `PAIR_DOWN_GENERIC`, `LOWER_LOW_AFTER_REJECTION_UNQUALIFIED` |
| Expected qualified bias | `COUNTER_BREATH_UP`, `COUNTER_BREATH_REJECTED`, `SECOND_LEG_DOWN`, `LOWER_LOW`, `POST_LOW_COUNTER_BREATH`, `LATE_THIN_BOUNCE` |
| Packet quality expected | `DOWN_AFTER_COUNTER_BREATH_REJECTED_QUALIFIES_AS_SECOND_LEG_DOWN_IF_PRICE_BREAKS_LOWER` |
| Price confirmation expected | Counter-breath fails; lower acceptance / lower low confirms second leg down. |
| Data visibility notes | Need price arbitration and last structural state; data weakness should degrade confidence. |
| Memory signature | `POST_RELEASE_LOWER_ACCEPTANCE -> LONDON_COUNTER_BREATH_UP -> COUNTER_BREATH_REJECTED -> SECOND_LEG_DOWN -> LOWER_LOW -> POST_LOW_COUNTER_BREATH -> LATE_THIN_BOUNCE` |
| False positive risks | `Treating rejected counter-breath as neutral noise`, `Not upgrading to second leg after lower low`, `Late thin bounce overread` |
| QA targets | `QA-FILM-20260513`, `QA-PATTERN-COUNTER-BREATH-REJECTED`, `QA-PATTERN-SECOND-LEG-DOWN` |

## Film memory card â€” 2026-05-14

| Field | Value |
|---|---|
| Date | 2026-05-14 |
| Symbol | GBPUSD |
| Film name | `LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL` |
| Film state | `LOWER_ZONE_RANGE_READING_PARTIAL` |
| Last structural event | `COUNTER_BREATH_REJECTED_IN_LOWER_ZONE_RANGE` |
| Dominant zone status | `LOWER_ZONE_RANGE_ACTIVE` |
| Dominant move role | `POST_LOW_REACTION_AFTER_REJECTED_COUNTER_BREATH` |
| Raw bias risks | `PAIR_UP_IN_LOWER_RANGE`, `STALE_PACKET`, `M1_MISSING`, `HOT_WITH_WEAK_VISIBILITY` |
| Expected qualified bias | `LOWER_ZONE_RANGE_ACTIVE`, `COUNTER_BREATH_UP`, `COUNTER_BREATH_REJECTED`, `LOW_RETEST`, `POST_LOW_REACTION`, `READING_PARTIAL` |
| Packet quality expected | `DEGRADED_WHEN_M1_MISSING_OR_PACKETS_STALE; OUTPUT_READING_PARTIAL_VISIBLE` |
| Price confirmation expected | Pending unless lower-zone break or reintegration acceptance; stale data prevents hard validation. |
| Data visibility notes | READING_PARTIAL / MICROFILM_MISSING / PACKETS_STALE must be visible at top of packet. |
| Memory signature | `LOWER_ZONE_RANGE_ACTIVE -> COUNTER_BREATH_UP -> COUNTER_BREATH_REJECTED -> LOW_RETEST -> POST_LOW_REACTION` |
| False positive risks | `Suppressing data warning`, `Reading PAIR_UP as fresh release despite lower range`, `Over-confirming with stale packet` |
| QA targets | `QA-FILM-20260514`, `QA-PATTERN-READING-PARTIAL`, `QA-PATTERN-LOWER-ZONE-RANGE` |

```

---

# SOURCE: Docs\T006_Source_Staging\FILM_LIBRARY__POWERFLOW_FILM_PATTERN_INDEX_V76.md

SHA256: B0698821AB0C378980305283527924EDDC03B8FBD3FE11E546781FD5E577265E
BYTES: 2560

```text
# POWERFLOW FILM PATTERN INDEX V7.6

Cet index relie les films calibrÃ©s GBPUSD aux patterns rÃ©currents que B6 et la QA doivent reconnaÃ®tre.

| PATTERN_ID | FILM_PATTERN | SEEN_ON_DATES | RAW_SIGNAL_RISK | EXPECTED_REQUALIFICATION | QA_CASES |
|---|---|---|---|---|---|
| `FP-001` | `RELEASE_CANDIDATE_VALIDATED` | 2026-05-06, 2026-05-08, 2026-05-11 | B3+B4+P1 without price | `RELEASE_VALIDATED only if price + zone + B7 confirm` | QA-FILM-20260506, QA-FILM-20260508, QA-FILM-20260511 |
| `FP-002` | `FALSE_BIRTH_EVENT_STACK` | 2026-05-11 | B3+B2 over-nervous | `EVENT_STACK / FALSE_BIRTH` | QA-FILM-20260511 |
| `FP-003` | `HIGH_ZONE_REJECTION` | 2026-05-06, 2026-05-07, 2026-05-11 | PAIR_UP late after high | `HIGH_ZONE_REJECTION / EXHAUSTION / CONSUMED` | QA-FILM-20260506, QA-FILM-20260507, QA-FILM-20260511 |
| `FP-004` | `LOWER_LOCK` | 2026-05-12, 2026-05-13 | PAIR_UP after release down | `LOWER_LOCK then COUNTER_BREATH_UP unless reintegration accepted` | QA-FILM-20260512, QA-FILM-20260513 |
| `FP-005` | `COUNTER_BREATH` | 2026-05-12, 2026-05-13, 2026-05-14 | Reverse raw bias treated as new phase | `COUNTER_BREATH / POST_LOW_REACTION` | QA-FILM-20260512, QA-FILM-20260513, QA-FILM-20260514 |
| `FP-006` | `COUNTER_BREATH_REJECTED` | 2026-05-13, 2026-05-14 | Failed reaction ignored | `COUNTER_BREATH_REJECTED` | QA-FILM-20260513, QA-FILM-20260514 |
| `FP-007` | `SECOND_LEG` | 2026-05-11, 2026-05-13 | PAIR_UP/PAIR_DOWN generic after pullback/rejection | `SECOND_LEG_UP / SECOND_LEG_DOWN` | QA-FILM-20260511, QA-FILM-20260513 |
| `FP-008` | `PULLBACK_ABSORBED` | 2026-05-08, 2026-05-11 | Post-release pullback misread as reversal | `PULLBACK_ABSORBED` | QA-FILM-20260508, QA-FILM-20260511 |
| `FP-009` | `LATE_THIN_BOUNCE` | 2026-05-12, 2026-05-13 | Late bounce overvalidated | `LATE_THIN_BOUNCE` | QA-FILM-20260512, QA-FILM-20260513 |
| `FP-010` | `EXHAUSTION_CONSUMED` | 2026-05-06, 2026-05-11 | HOT/PAIR_UP after extension | `EXHAUSTION / CONSUMED / EXHAUSTION_RISK` | QA-FILM-20260506, QA-FILM-20260511 |
| `FP-011` | `READING_PARTIAL` | 2026-05-14 | Stale packet or M1 missing treated as normal | `READING_PARTIAL / DEGRADED` | QA-FILM-20260514 |

## Notes d'indexation

- Un pattern peut apparaÃ®tre dans plusieurs films avec un rÃ´le diffÃ©rent.
- L'index ne remplace pas la film card : il accÃ©lÃ¨re le matching B6.
- `RAW_SIGNAL_RISK` dÃ©crit le piÃ¨ge du signal brut.
- `EXPECTED_REQUALIFICATION` dÃ©crit le nom terrain attendu dans `terrain_packet_v76_0`.
- `QA_CASES` indique les cas de validation minimaux.

```

---

# SOURCE: Docs\T006_Source_Staging\GRAMMAIRE__GRAMMAIRE_LEXIQUE_POWERFLOW_V6_UPDATE_2026-05-04.md

SHA256: D69483538FB9F3DAA1FC5A7CBB2B9A8295A3B5C92F0F3EFC748333945EF9B935
BYTES: 8974

```text
# GRAMMAIRE & LEXIQUE â€” Mise Ã  jour PowerFlow V6

**Date :** 2026-05-04  
**Objet :** nouveaux concepts issus de la session nodes / sÃ©quences / orchestration fractale / agents  
**Statut :** lexique Lab, non figÃ© dÃ©finitivement

---

## 1. Doctrine centrale

```text
Les forces prÃ©viennent.
Le prix confirme.
Le HTF donne la gravitÃ©.
Le LTF donne la naissance.
```

```text
Quand le HTF devient Ã©vident, la fenÃªtre tactique LTF peut dÃ©jÃ  Ãªtre fermÃ©e.
```

```text
PowerFlow doit voir le node quand les forces basculent,
pas attendre que le prix ait dÃ©jÃ  racontÃ© lâ€™histoire.
```

---

# 2. TemporalitÃ© fractale

## FRACTAL_TIME_IMBRICATION

**DÃ©finition :**  
Imbrication des timeframes oÃ¹ chaque Ã©tage temporel a un rÃ´le spÃ©cifique.

```text
H4/H1 = gravitÃ© / scÃ¨ne large
M30   = champ de bataille / scÃ¨ne active
M15   = relais / confirmation tactique
M5    = timing tactique
M1    = naissance / microfilm / prÃ©-signal
```

**Phrase :**

```text
Le HTF donne la scÃ¨ne, le LTF donne la fenÃªtre.
```

---

## HTF_GRAVITY_NODE

**DÃ©finition :**  
Node visible sur H4/H1/M30 qui porte la gravitÃ© de fond.

**RÃ´le :**

```text
Qualifier le contexte.
Ne pas forcÃ©ment donner un timing dâ€™entrÃ©e.
```

---

## LTF_PRESIGNAL_BIRTH

**DÃ©finition :**  
PrÃ©-signal ou naissance observable sur M1/M5/M15 avant que le HTF ne devienne Ã©vident.

**RÃ´le :**

```text
DÃ©tecter la fenÃªtre jeune.
```

---

## MTF_CONFIRMATION_LATE

**DÃ©finition :**  
Confirmation sur timeframe moyen alors que la naissance LTF a dÃ©jÃ  eu lieu.

**Exemple :**

```text
M30/H1 confirme une scÃ¨ne,
mais M1/M5 ont dÃ©jÃ  donnÃ© le dÃ©part.
```

---

## WINDOW_ALREADY_CLOSING

**DÃ©finition :**  
Ã‰tat oÃ¹ la scÃ¨ne HTF reste valide mais oÃ¹ la fenÃªtre tactique LTF est dÃ©jÃ  avancÃ©e ou consommÃ©e.

**Phrase cockpit future :**

```text
ScÃ¨ne HTF active, mais fenÃªtre LTF probablement tardive.
```

---

## HTF_NODE_LTF_WINDOW_CLOSED

**DÃ©finition :**  
Cas oÃ¹ le node large est visible sur H4/H1 mais les prÃ©-signaux M1/M5/M15 sont dÃ©jÃ  passÃ©s.

**Lecture :**

```text
Ne pas chercher le dÃ©part.
Chercher respiration, second leg ou absorption.
```

---

# 3. Phases de sÃ©quence

## PRE_FIELD

Champ prÃ©paratoire avant le node.

Signatures :

```text
compression
extension dâ€™un bloc
dÃ©sÃ©quilibre haut/bas
prix encore suspendu
```

---

## NODE_BIRTH

Naissance du node.

Signatures :

```text
basculement collectif des forces
bloc montant
bloc descendant
prix encore retenu ou pas encore Ã©vident
```

---

## CONFIRMATION_PENDING

Phase entre naissance LTF et validation M5/M15.

---

## CONFIRMED

La structure commence Ã  payer.

Signatures :

```text
M5/M15 suit le node
bid commence Ã  payer
bloc dominant persiste
```

---

## COUNTER_BREATH

Respiration contraire.

Signatures :

```text
bloc opposÃ© rebondit
camp dominant relÃ¢che
prix rÃ©pond peu ou temporairement
```

---

## ABSORPTION

La respiration contraire est absorbÃ©e.

Signatures :

```text
camp dominant reprend
prix revient dans le sens de la structure
contre-mouvement Ã©choue
```

---

## SECOND_LEG

DeuxiÃ¨me jambe aprÃ¨s respiration ou recharge.

---

## WINDOW_CLOSING

FenÃªtre de temps tactique qui se ferme.

Signatures :

```text
HTF toujours visible
LTF dÃ©jÃ  avancÃ©
prix a dÃ©jÃ  payÃ© une partie importante
```

---

# 4. Nodes et patterns

## RAW_NODE_BIRTH

DÃ©tection brute depuis la DB sans interprÃ©tation complÃ¨te.

---

## GRAVITY_RESPRING_NODE

Node oÃ¹ USD/CAD ou bloc pivot/gravity reprend depuis une position basse/comprimÃ©e.

---

## CAD_JPY_USD_RESPRING_NODE_AGAINST_RISK_BLOCK_FOLD

Pattern observÃ© sur GBPUSD 2026-05-04, 09:23â†’09:27.

Structure :

```text
CAD+JPY+USD respring
EUR+GBP+CHF/AUD fold
prix encore retenu
confirmation M5 ensuite
```

---

## POWER_ANGLE_ALERT

Alerte dâ€™angle fort avant ou pendant la cassure prix.

Signatures :

```text
devise dominante accÃ©lÃ¨re
angle de force augmente brutalement
bloc opposÃ© se vide
prix proche dâ€™une cassure ou commence Ã  payer
```

---

## FORCE_ANGLE_BREAK

Cassure dâ€™angle dans les forces.

DiffÃ©rence avec node :

```text
NODE_BIRTH = basculement de rÃ©gime
FORCE_ANGLE_BREAK = accÃ©lÃ©ration directionnelle lisible
```

---

## PRICE_IMPACT_LEG

Jambe oÃ¹ le prix paie brutalement la structure.

---

## POWER_ANGLE_BREAK_TO_PRICE_IMPACT

Pattern visuel observÃ© sur la sÃ©quence 12:45â†’13:45.

Structure :

```text
angle USD/CAD fort
GBP/EUR/AUD drainent
prix casse
respiration ensuite
```

---

## POST_IMPACT_BREATH

Respiration aprÃ¨s une jambe dâ€™impact.

---

## POST_IMPACT_FORCE_PERSISTENCE

Les forces dominantes restent orientÃ©es aprÃ¨s lâ€™impact, mÃªme si le prix respire.

Exemple :

```text
CAD/USD restent porteurs
prix stabilise ou rebondit lÃ©gÃ¨rement
```

---

## PRICE_BREATH_AGAINST_FORCE

Le prix respire contre une structure de force encore active.

---

# 5. Mesures cinÃ©matiques

## FORCE_VELOCITY

Variation de force par minute.

```text
force_velocity_per_min = force_delta / minutes
```

---

## FORCE_ANGLE_DEG

Angle gÃ©omÃ©trique approximatif de la force.

```text
angle = atan(force_velocity_per_min)
```

Ce nâ€™est pas un angle pixel du graphique.  
Câ€™est un proxy mathÃ©matique.

---

## FORCE_ACCELERATION

Variation de vitesse entre deux segments.

```text
acceleration = velocity_current - velocity_previous
```

---

## FORCE_ENERGY

Somme des variations absolues des devises.

```text
energy = Î£ abs(force_delta)
```

---

## PRICE_LAG

Les forces bougent fortement mais le prix rÃ©pond peu.

---

## PRICE_PAYING

Le prix commence Ã  suivre la structure.

---

## PIP_VELOCITY

Vitesse du prix en pips par minute.

---

# 6. Agents PowerFlow

## DB_FRESHNESS_AGENT

Mission :

```text
vÃ©rifier que la DB voit vraiment
contrÃ´ler lignes rÃ©centes par timeframe
vÃ©rifier colonnes EA
dÃ©tecter trous temporels
```

---

## SEQUENCE_READER

Mission :

```text
lire le film brut
extraire blocs, deltas, energy, nodes, breaths
```

Ne doit pas surinterprÃ©ter.

---

## FORCE_KINEMATICS_AGENT

Mission :

```text
mesurer vitesse, angle, accÃ©lÃ©ration, pips/min
```

---

## FRACTAL_ORCHESTRATOR

Mission :

```text
relier HTF et LTF
dire si la fenÃªtre est jeune, active, tardive ou fermÃ©e
```

Questions clÃ©s :

```text
Le prÃ©-signal LTF est-il portÃ© par une gravitÃ© HTF ?
Le HTF est-il dÃ©jÃ  Ã©vident mais LTF tardif ?
Chercher dÃ©part, respiration, second leg ou absorption ?
```

---

## NODE_INTERPRETER

Mission :

```text
nommer la scÃ¨ne
classer le comportement
transformer les events en langage Flow
```

---

## LAB_MEMORY_AGENT

Mission :

```text
sauver observation trader
crÃ©er fiche Lab
capturer vocabulaire nouveau
prÃ©parer hypothÃ¨se testable
```

---

## MISSION_BUILDER_AGENT

Mission :

```text
transformer un Lab en mission codable
dÃ©finir fichier cible, objectif, contraintes, tests
rÃ©duire les patchs confus
```

---

## COCKPIT_TRANSLATOR

Mission future :

```text
condense les sorties agents en 3 lignes utiles
ne calcule pas
ne dÃ©cide pas
```

---

# 7. Ã‰tats de fenÃªtre

## WINDOW_YOUNG

PrÃ©-signal jeune, opportun pour surveillance tactique.

---

## WINDOW_ACTIVE

ScÃ¨ne en cours, confirmation ou impact en dÃ©veloppement.

---

## WINDOW_LATE

Signal dÃ©jÃ  avancÃ©. Le HTF confirme mais le timing LTF est moins propre.

---

## WINDOW_CLOSED

La fenÃªtre de dÃ©part est consommÃ©e.

---

## WATCH_SECOND_LEG

Ne pas chercher la premiÃ¨re cassure.  
Surveiller respiration puis deuxiÃ¨me jambe.

---

## WATCH_ABSORPTION

Surveiller si la respiration est absorbÃ©e.

---

# 8. Patterns Lab enregistrÃ©s

## LAB_004_USD_CAD_JPY_RESPRING_AGAINST_RISK_BLOCK_FOLD

SÃ©quence :

```text
09:00 â†’ 10:15
Node birth 09:23 â†’ 09:27
Confirmation M5 09:35 â†’ 09:45
Counter breath 09:49 â†’ 09:54
Absorption 10:00 â†’ 10:15
```

---

## LAB_005_USD_CAD_ANGLE_BREAK_WITH_GBP_EUR_DRAIN

SÃ©quence :

```text
12:45 â†’ 13:45 visuel
DB fine absente
M30 confirme seulement lâ€™impact large
```

Pattern :

```text
POWER_ANGLE_BREAK_TO_PRICE_IMPACT
```

---

# 9. RÃ¨gles Ã  retenir

```text
Ne pas confondre respiration contraire et nouveau node principal.
```

```text
Un node principal doit Ãªtre lu dans son ordre temporel.
```

```text
M1/M5/M15 donnent les prÃ©-signaux.
M30/H1/H4 donnent la scÃ¨ne.
```

```text
Si HTF confirme mais LTF est dÃ©jÃ  passÃ© :
chercher second leg / absorption, pas naissance.
```

```text
La DB Freshness est une condition avant toute analyse automatique.
```

---

# 10. Formules cockpit futures

```text
LTF PRE-SIGNAL â€” microfilm M1/M5 sâ€™aligne sous gravitÃ© HTF.
```

```text
HTF NODE DETECTED â€” fenÃªtre LTF probablement avancÃ©e.
```

```text
POWER ANGLE ALERT â€” USD/CAD accÃ©lÃ¨rent, GBP/EUR/AUD drainent.
```

```text
PRICE IMPACT CONFIRMED â€” M5 paie la cassure.
```

```text
POST IMPACT BREATH â€” prix respire, forces dominantes encore actives.
```

```text
WINDOW CLOSING â€” ne pas chercher dÃ©part, surveiller absorption/second leg.
```

```

---

# SOURCE: Docs\T006_Source_Staging\GRAMMAIRE__GRAMMAIRE_LEXIQUE_SEQUENCE_NODES_V01.md

SHA256: 564FE99648D70DEB3E1C0C07001CA292E0EAE46E3E50D81F93A8B66D33972FC5
BYTES: 10875

```text
# GRAMMAIRE & LEXIQUE â€” PowerFlow V6 â€” Nodes, SÃ©quences, Agents

**Date :** 2026-05-04  
**Objet :** Formaliser le vocabulaire issu de lâ€™analyse sÃ©quence GBPUSD 2026-05-04  
**But :** PrÃ©parer lâ€™automatisation de la lecture de sÃ©quences sans coder trop tÃ´t  
**Doctrine :**

```text
PowerFlow doit voir le node quand les forces basculent,
pas attendre que le prix ait dÃ©jÃ  racontÃ© lâ€™histoire.
```

---

# 1. Grammaire gÃ©nÃ©rale dâ€™une sÃ©quence

## PRE_FIELD

**DÃ©finition :**  
Champ prÃ©paratoire avant la naissance visible dâ€™un node.

**Signatures possibles :**

```text
bloc haut en extension
bloc bas comprimÃ©
devises pivot/refuge en position anormale
prix encore calme ou suspendu
```

**RÃ´le :**

```text
PrÃ©parer le contexte.
Ce nâ€™est pas encore lâ€™alerte principale.
```

**Exemple :**

```text
AUD haut + JPY haut
USD/CAD bas
prix encore Ã©levÃ©
```

---

## NODE_BIRTH

**DÃ©finition :**  
Naissance du node. Moment oÃ¹ les forces basculent brutalement de faÃ§on collective.

**RÃ¨gle clÃ© :**

```text
Le node peut naÃ®tre avant que le prix bouge fortement.
```

**Signatures :**

```text
un bloc monte ensemble
un bloc opposÃ© tombe ensemble
Ã©nergie forte
synchronisation courte
prix encore retenu
```

**Exemple :**

```text
CAD+JPY+USD respring
EUR+GBP+CHF fold
bid presque stable
```

---

## CONFIRMATION_LEG

**DÃ©finition :**  
Jambe de confirmation aprÃ¨s la naissance du node.

**Signatures :**

```text
le mÃªme camp continue sur TF supÃ©rieur
le prix commence Ã  payer
la synchronisation sâ€™Ã©tend de M1 vers M5/M15
```

**RÃ´le :**

```text
Valider que le node nâ€™Ã©tait pas seulement un choc microfilm.
```

---

## COUNTER_BREATH

**DÃ©finition :**  
Respiration contraire aprÃ¨s confirmation.

**Signatures :**

```text
le camp opposÃ© rebondit
le camp dominant relÃ¢che
prix rend peu ou temporairement
```

**RÃ¨gle :**

```text
Une respiration contraire nâ€™invalide pas la structure.
Il faut voir si elle paie en prix.
```

---

## ABSORPTION

**DÃ©finition :**  
Moment oÃ¹ une respiration contraire est absorbÃ©e.

**Signatures :**

```text
le camp dominant reprend
le prix reprend la direction de la structure
la respiration prÃ©cÃ©dente perd son effet
```

**RÃ´le :**

```text
Confirmer que la structure principale reste active.
```

---

## STRUCTURE_PAYING

**DÃ©finition :**  
Moment oÃ¹ le prix commence Ã  raconter ce que les forces ont dÃ©jÃ  montrÃ©.

**Phrase Flow :**

```text
Le prix paie la structure.
```

**Important :**

```text
PowerFlow ne doit pas attendre cette phase pour voir la naissance.
```

---

# 2. Lexique des nodes

## RAW_NODE_BIRTH

**DÃ©finition :**  
DÃ©tection brute dâ€™une naissance de node depuis les donnÃ©es force_snapshots.

**Sans interprÃ©tation complÃ¨te.**

**Exemple :**

```text
UP_BLOCK = CAD+JPY+USD
DOWN_BLOCK = EUR+GBP+CHF
force_energy Ã©levÃ©e
bid_delta faible
```

---

## GRAVITY_RESPRING_NODE

**DÃ©finition :**  
Node oÃ¹ les devises de gravitÃ©/pivot ou assimilÃ©es reprennent fortement depuis une position basse ou comprimÃ©e.

**Exemple :**

```text
USD+CAD respring
```

**Extension possible :**

```text
JPY rejoint le mouvement comme refuge response.
```

---

## CAD_JPY_USD_RESPRING_NODE_AGAINST_RISK_BLOCK_FOLD

**DÃ©finition :**  
Pattern observÃ© sur GBPUSD le 2026-05-04.

**Structure :**

```text
CAD + JPY + USD montent brutalement
EUR + GBP + AUD/CHF se replient
prix encore retenu Ã  la naissance
confirmation M5 ensuite
```

**Famille :**

```text
GRAVITY_RESPRING_NODE
RISK_BLOCK_FOLD
```

---

## PRICE_LAG_AT_NODE_BIRTH

**DÃ©finition :**  
DÃ©calage entre lâ€™inversion des forces et le mouvement prix.

**RÃ¨gle :**

```text
Quand les forces basculent mais que le prix ne bouge pas encore,
PowerFlow doit suspecter une naissance de node.
```

**UtilitÃ© :**

```text
Alerter plus tÃ´t.
```

---

## M5_CONFIRMATION_LEG

**DÃ©finition :**  
Confirmation dâ€™un node M1 par une poursuite cohÃ©rente sur M5.

**Signatures :**

```text
mÃªme camp dominant
prix commence Ã  payer
bloc opposÃ© continue de se vider
```

---

## BREATH_ABSORBED

**DÃ©finition :**  
Respiration opposÃ©e qui ne casse pas la structure.

**Signatures :**

```text
rebond des forces opposÃ©es
rÃ©ponse prix faible
reprise du camp dominant ensuite
```

---

# 3. Lexique des blocs

## UP_BLOCK

**DÃ©finition :**  
Groupe de devises qui montent ensemble sur une fenÃªtre courte.

**Exemple :**

```text
CAD+JPY+USD
```

---

## DOWN_BLOCK

**DÃ©finition :**  
Groupe de devises qui tombent ensemble sur une fenÃªtre courte.

**Exemple :**

```text
EUR+GBP+CHF
```

---

## RISK_BLOCK

**DÃ©finition :**  
Bloc composÃ© majoritairement de devises de rÃ´le RISK.

**Exemples :**

```text
EUR+GBP+AUD
EUR+GBP
AUD+GBP
```

---

## REFUGE_BLOCK

**DÃ©finition :**  
Bloc composÃ© majoritairement de devises REFUGE.

**Exemples :**

```text
JPY+CHF
```

---

## PIVOT_BLOCK

**DÃ©finition :**  
Bloc dominÃ© par des devises pivot ou gravitationnelles.

**Exemples :**

```text
USD+CAD
```

---

## MIXED_GRAVITY_BLOCK

**DÃ©finition :**  
Bloc composÃ© de pivot + refuge.

**Exemple :**

```text
USD+CAD+JPY
```

**Lecture :**

```text
Ce bloc peut reprendre le champ contre un bloc risk.
```

---

# 4. Lexique des mouvements

## RESPRING

**DÃ©finition :**  
RemontÃ©e brusque dâ€™une devise ou dâ€™un bloc depuis une zone basse/comprimÃ©e.

**Exemple :**

```text
CAD +18.5 depuis bas
```

---

## FOLD

**DÃ©finition :**  
Pliage / vidange dâ€™une devise ou dâ€™un bloc depuis une zone haute ou intermÃ©diaire.

**Exemple :**

```text
EUR -23.2
GBP -20.1
CHF -17.1
```

---

## FORCE_ENERGY

**DÃ©finition :**  
Ã‰nergie brute dâ€™une fenÃªtre, souvent approximÃ©e par la somme des variations absolues des devises.

**UtilitÃ© :**

```text
RepÃ©rer les fenÃªtres oÃ¹ quelque chose se passe vraiment.
```

---

## SYNC_RESPRING

**DÃ©finition :**  
Plusieurs devises remontent ensemble sur une fenÃªtre courte.

**Exemple :**

```text
CAD+JPY+USD montent ensemble.
```

---

## SYNC_FOLD

**DÃ©finition :**  
Plusieurs devises tombent ensemble sur une fenÃªtre courte.

**Exemple :**

```text
EUR+GBP+CHF tombent ensemble.
```

---

## OPPOSITE_BLOCK_ROTATION

**DÃ©finition :**  
Rotation simultanÃ©e entre un bloc montant et un bloc descendant.

**Phrase :**

```text
Un camp reprend le champ pendant que lâ€™autre se vide.
```

---

# 5. Lexique prix / force

## PRICE_LAG

**DÃ©finition :**  
Le prix ne suit pas immÃ©diatement le basculement des forces.

**Lecture :**

```text
Le champ se prÃ©pare.
Le prix nâ€™a pas encore racontÃ© lâ€™histoire.
```

---

## WEAK_PRICE_RESPONSE

**DÃ©finition :**  
Les forces bougent fortement, mais le prix rÃ©pond peu.

**InterprÃ©tation possible :**

```text
absorption
contre-force
liquiditÃ©
structure plus large qui retient
```

---

## PRICE_PAYS_STRUCTURE

**DÃ©finition :**  
Le prix finit par suivre le node dÃ©tectÃ© dans les forces.

**Exemple :**

```text
Node M1 09:23â€“09:27
prix paie sur M5 09:35â€“09:45
```

---

# 6. Lexique agentique

## SEQUENCE_READER

**DÃ©finition :**  
Agent qui lit la DB et extrait les Ã©vÃ©nements bruts.

**Mission :**

```text
mesurer
extraire
classer froidement
ne pas interprÃ©ter trop loin
```

**EntrÃ©es :**

```text
force_snapshots
symbol
timeframes
start/end
```

**Sorties :**

```text
windows
up_block
down_block
energy
bid_delta
raw_event
```

---

## NODE_INTERPRETER

**DÃ©finition :**  
Agent qui transforme les Ã©vÃ©nements bruts en langage Flow.

**Mission :**

```text
nommer le node
identifier phase
identifier acteurs
connecter prÃ©-field / confirmation / breath / absorption
```

---

## COCKPIT_TRANSLATOR

**DÃ©finition :**  
Agent qui traduit lâ€™interprÃ©tation en phrase courte cockpit.

**Mission :**

```text
rÃ©duire la charge mentale
ne pas tout afficher
ne pas noyer le trader
```

**Exemple :**

```text
NODE NAISSANT â€” CAD+JPY+USD reprennent contre EUR+GBP+CHF. Prix encore retenu.
```

---

## LAB_TRANSLATOR

**DÃ©finition :**  
Agent qui transforme une observation trader ou sÃ©quence DB en fiche Lab.

**Mission :**

```text
sauver la mÃ©moire
nommer les comportements
prÃ©parer validation future
```

---

# 7. RÃ¨gles dâ€™alerte proposÃ©es

## NODE_BIRTH_FAST

**DÃ©finition :**  
Alerte rapide quand les forces basculent collectivement.

**PrÃ©conditions :**

```text
bloc haut / bloc bas
compression ou extension prÃ©alable
Ã©nergie forte
rotation opposÃ©e
```

**Trigger :**

```text
UP_BLOCK fort
DOWN_BLOCK fort
price_lag prÃ©sent
```

**Phrase cockpit :**

```text
NODE NAISSANT â€” forces basculent, prix encore retenu.
```

---

## NODE_CONFIRMATION_M5

**DÃ©finition :**  
Alerte quand le node M1 est confirmÃ© par M5.

**PrÃ©conditions :**

```text
node birth M1 dÃ©tectÃ©
mÃªme camp dominant sur M5
bid commence Ã  payer
```

**Phrase cockpit :**

```text
NODE CONFIRMÃ‰ M5 â€” structure commence Ã  payer.
```

---

## COUNTER_BREATH_ALERT

**DÃ©finition :**  
Alerte respiration contraire.

**PrÃ©conditions :**

```text
aprÃ¨s confirmation
bloc opposÃ© rebondit
camp dominant relÃ¢che
```

**Phrase cockpit :**

```text
RESPIRATION CONTRAIRE â€” surveiller absorption ou invalidation.
```

---

## BREATH_ABSORBED_ALERT

**DÃ©finition :**  
Alerte quand la respiration contraire est absorbÃ©e.

**PrÃ©conditions :**

```text
counter breath dÃ©tectÃ©
prix ne paie pas beaucoup contre la structure
camp dominant reprend
```

**Phrase cockpit :**

```text
RESPIRATION ABSORBÃ‰E â€” structure reprend.
```

---

# 8. SÃ©quence type apprise

## Pattern

```text
USD_CAD_JPY_RESPRING_AGAINST_RISK_BLOCK_FOLD
```

## Phases

```text
PRE_FIELD:
AUD_HIGH_EXTENSION_WITH_USD_CAD_LOW_COMPRESSION

NODE_BIRTH:
CAD_JPY_USD_RESPRING_NODE_AGAINST_RISK_BLOCK_FOLD

CONFIRMATION:
POST_NODE_GRAVITY_CONFIRMATION_LEG

BREATH:
COUNTER_FORCE_BREATH_WITH_WEAK_PRICE_RESPONSE

ABSORPTION:
BREATH_ABSORBED_BY_USD_CAD_GRAVITY
```

## RÃ¨gle stratÃ©gique

```text
Le node est visible dans les forces avant dâ€™Ãªtre Ã©vident sur le prix.
```

---

# 9. Ce que la DB doit apprendre ensuite

Quand le nouveau schÃ©ma EA sera persistÃ©, enrichir les nodes avec :

```text
OHLC
tick_volume
pip_range
pip_body
pip_change
spread_points
spread_price
spread_pips
ask
mid
bar_time
bar_close_time
server_time
capture_time
is_closed_bar
NZD
```

Nouvelles classes futures :

```text
NODE_BIRTH_FORCE_ONLY
NODE_BIRTH_WITH_PRICE_LAG
NODE_BIRTH_WITH_CANDLE_BODY
NODE_BIRTH_WITH_VOLUME
NODE_BIRTH_WITH_SPREAD_FRICTION
NODE_CONFIRMED_BY_CLOSED_BAR
```

---

# 10. Doctrine finale

```text
Un node nâ€™est pas un signal isolÃ©.
Câ€™est une fenÃªtre oÃ¹ les forces changent de rÃ©gime.
```

```text
Le prix confirme.
Les forces prÃ©viennent.
```

```text
PowerFlow doit lire le basculement du champ,
puis seulement ensuite vÃ©rifier si le prix paie.
```

```text
Le trader ne doit pas lire sept devises.
PowerFlow doit compresser le champ en une phrase utile.
```

```

---

# SOURCE: Docs\T006_Source_Staging\LEXIQUE__02_LEXIQUE_GRAMMAIRE_POWERFLOW_V6_ACTIVE_20260505.md

SHA256: A7BA1CE8522CDDFCE0C3964E96E05C27AA5B546596A6F4F49F0767D3250ED50F
BYTES: 2888

```text
# 02 â€” LEXIQUE / GRAMMAIRE ACTIVE POWERFLOW V6

Date : 2026-05-05  
Statut : GRAMMAIRE ACTIVE â€” version nettoyÃ©e

## Principe

```text
Nommer pour voir.
Pas nommer pour classer inutilement.
```

Une nomenclature doit rÃ©duire la charge mentale.

## Cycle de travail

```text
VISION NOTE
â†’ FLOW BEHAVIOR
â†’ FLOW EVENT
â†’ FLOW WINDOW
â†’ SYSTEM ACTION
```

## Familles

```text
VISION
FORCE
ZONE
NODE
TEMPORAL
FRACTAL
COALITION
BATTLEFIELD
COCKPIT
TELEGRAM
LAB
SYSTEM
```

## Force / tension

### FORCE_SHIFT
Changement dâ€™angle ou de rÃ©gime dâ€™une devise.

### TENSION_FIELD
Champ de tension actif.

### ELASTIC_LOADED
Ã‰lastique chargÃ©.

```text
tension maintenue
pullbacks absorbÃ©s
champ prÃªt Ã  libÃ©rer ou casser
```

### PRICE_LAG_THEN_CATCHUP
Le prix est en retard sur la force puis rattrape.

### SPREAD_FRICTION_FIELD
Le spread crÃ©e une friction ou une rugositÃ© de lecture.

## Zone

```text
NEUTRAL
PRE_EXTREME
EARLY_EXTREME
ACCUMULATING
LEAKING
RUPTURE
PULLBACK
ABSORBED_PULLBACK
```

## Nodes

Un node nâ€™est pas seulement un croisement.

Il peut Ãªtre contact, non-contact, Ã©tirement, opposition, pli, compression, rÃ©pulsion, synchronisation, bascule de leadership.

```text
NODE
NODE_BIRTH
FAST_NODE_BIRTH
NODE_WATCH
NODE_CONFIRMED
NODE_REPULSION
NODE_ABSORPTION
SECOND_LEG_NODE
LATE_NODE
```

## Temporal

```text
TEMPORAL_NODE_ALERT
TEMPORAL_WINDOW_CANDIDATE
TEMPORAL_WINDOW_ACTIVE
TEMPORAL_DENSITY
```

RÃ¨gle :

```text
Temporal Node Alert â‰  TemporalWindowActive.
```

## Fractal

```text
LTF = M1 / M5 / M15
HTF = M30 / H1 / H4
LTF_BIRTH_ACTIVE
HTF_GRAVITY_SUPPORTIVE
HTF_GRAVITY_OPPOSED
HTF_CONFIRMED_BUT_LTF_LATE
```

RÃ¨gle :

```text
HTF confirmÃ© + LTF tardif = pas NODE_BIRTH.
Chercher absorption, second leg ou clÃ´ture.
```

## Flow Events

```text
FAST_BIRTH_ALERT
NODE_BIRTH
COUNTER_BREATH
ABSORPTION
WATCH_SECOND_LEG
VOLUME_PRESSURE_SPIKE
PRICE_LAG_THEN_CATCHUP
SPREAD_FRICTION_FIELD
```

Signature minimale FAST_BIRTH_ALERT :

```text
M1 force shift
angle change
price lag
devise antagoniste active
spread non destructeur
pip_range ou volume en expansion si disponible
```

## Coalitions / Battlefield

```text
COALITION_FIELD
ANTAGONIST_FIELD
BATTLEFIELD_RADAR
BIPOLAR_FIELD
```

RÃ¨gle :

```text
Coalition forte seule â‰  bataille complÃ¨te.
Relation active moyenne > coalition isolÃ©e forte.
```

## Cockpit / Telegram

```text
COCKPIT_STATE
NODE_STATE
ALERT_LEVELS
TELEGRAM_NODE_MODE
```

Alert levels :

```text
BIRTH
WATCH
HOT
CONFIRMING
ABSORBING
SECOND_LEG
LATE
CHAOTIC
```

Telegram modes :

```text
OFF
WATCH
SCALPING
HOT_ONLY
```

RÃ¨gle :

```text
Le filtre Telegram appartient au trader.
```

## Labs

Ã‰tats :

```text
VISION NOTE
Ã€ TESTER
Ã€ PATCHER
Ã€ CONSOLIDER
LEGACY
```

Format fiche :

```text
ID :
VISION NOTE :
FLOW BEHAVIOR :
FLOW EVENT :
FLOW WINDOW :
SYSTEM ACTION :
DB TESTABLE :
ALERTE UTILE :
STATUT :
```

```

---

# SOURCE: Docs\T006_Source_Staging\LEXIQUE__LEXIQUE_GRAMMAIRE_COMPORTEMENTS_POWERFLOW.md

SHA256: 3C152CCB816A34645A25A91AD30F90771732E8161C1570D5F3DEAFE303C03193
BYTES: 7418

```text
# LEXIQUE_GRAMMAIRE_COMPORTEMENTS_POWERFLOW

**Version :** Mise Ã  jour 03/05/2026  
**Projet :** PowerFlow V6  
**Objet :** Grammaire vivante du langage PowerFlow : comportements, fenÃªtres, gates, compressions, releases et lecture fractale du marchÃ©.

---

## 1. Principe du lexique vivant

Le lexique PowerFlow nâ€™est pas une procÃ©dure bloquante.  
Il sert Ã  stabiliser le langage aprÃ¨s observation.

RÃ¨gle :

```text
Observation libre pendant la session.
Structuration lÃ©gÃ¨re en fin de session.
Stabilisation progressive du langage.
```

---

## 2. Doctrine gÃ©nÃ©rale

PowerFlow lit le marchÃ© comme un organisme de flux.

```text
Le marchÃ© respire.
Le marchÃ© compresse.
Le marchÃ© accumule.
Le marchÃ© libÃ¨re.
Le marchÃ© se replie.
Le marchÃ© redistribue la gravitÃ© entre devises.
```

PowerFlow ne donne pas de BUY/SELL.  
PowerFlow lit des Ã©tats, des fenÃªtres, des champs et des scÃ¨nes.

---

## 3. Familles du langage

```text
Force
Amplitude
Compression
Gate temporelle
Expansion
Release
Rebalancement
Coalition
Antagoniste
Personality
TemporalitÃ©
Zone
Cockpit
```

---

## 4. Grammaire fractale des timeframes

### WEEKLY_PROFILE

DÃ©cor trÃ¨s large, mÃ©moire des zones et champ de rotation supÃ©rieur.

### DAILY_REBALANCE_PREPARATION

Champ daily oÃ¹ les forces prÃ©parent une redistribution.

### H4_STRUCTURAL_RECOMPOSITION_FIELD

Champ H4 oÃ¹ les grandes forces se recomposent sans forcÃ©ment valider encore une direction exploitable.

### H1_TEMPORAL_EXPANSION_WINDOW

FenÃªtre H1 oÃ¹ le marchÃ© laisse assez dâ€™espace pour quâ€™un scÃ©nario infÃ©rieur puisse se dÃ©velopper.

### M30_TEMPORAL_EXPANSION_GATE

Porte temporelle. Moment oÃ¹ une compression supÃ©rieure peut devenir expansion sur M15/M5.

### M15_BATTLE_SCENE

ScÃ¨ne de bataille. Le M15 montre la construction du scÃ©nario.

### M5_TACTICAL_RELEASE

Le M5 montre la libÃ©ration tactique et la fabrication de la jambe.

### M1_MICRO_RECHARGE

Le M1 montre la naissance, la couture micro, les petites recharges et les rÃ©ponses rapides.

---

## 5. Termes CORE

### POWERFLOW_V6

Scanner de Confluence Temporelle.  
Il lit les forces, tensions, amplitudes, coalitions, compressions, gates, releases et rebalancements.

### COCKPIT

Dashboard lecture seule.  
Il affiche ce que PowerFlow comprend, sans dÃ©cider Ã  la place du trader.

### DEVISE_PERSONALITY

Profil comportemental dâ€™une devise : rÃ´le, tempo, amplitude normale, volatilitÃ© et Ã©ventuel lag.

### PERSONALITY_BRIDGE

Pont entre les mesures mathÃ©matiques et le comportement naturel des devises.

### COALITION

Groupe de devises avanÃ§ant avec cohÃ©rence commune.

### RELATION_ACTIVE

ScÃ¨ne oÃ¹ une coalition rencontre un antagoniste clair.

### BATTLEFIELD_RADAR

Bloc qui classe les scÃ¨nes stratÃ©giques du marchÃ©.

### PREPARATION_FIELD

Champ oÃ¹ le marchÃ© organise ses forces avant le mouvement visible.

---

## 6. Termes thermodynamiques

### COMPRESSED

Tension maximale, Ã©nergie concentrÃ©e.  
Attention : lâ€™Ã©tat COMPRESSED peut avoir existÃ© avant que le dashboard observe la release.

### ACTIVE

Devise ou champ vivant, mouvement prÃ©sent.

### NEUTRAL

ActivitÃ© moyenne, ni compression forte ni vide.

### HOLLOW

MarchÃ© creux, peu de matiÃ¨re, tendance vide.

### DEAD

Aucune activitÃ© mesurable utile.

---

## 7. Termes de fenÃªtre temporelle

### TEMPORAL_EXPANSION_WINDOW

FenÃªtre oÃ¹ les timeframes supÃ©rieurs donnent assez dâ€™espace, de respiration ou de conflit non rÃ©solu pour permettre une expansion sur les timeframes infÃ©rieurs.

### HTF_EXPANSION_PERMISSION

Ã‰tat oÃ¹ H1/H4/Daily ne valident pas forcÃ©ment une direction, mais laissent une permission de scÃ©nario aux timeframes infÃ©rieurs.

### TEMPORAL_EXPANSION_GATE

Moment ou zone oÃ¹ un timeframe supÃ©rieur valide quâ€™une compression peut devenir expansion sur les timeframes infÃ©rieurs.

### WINDOW_PREPARING

FenÃªtre en prÃ©paration. Les forces se regroupent, mais la release nâ€™est pas encore claire.

### WINDOW_GATE_OPEN

La porte temporelle est ouverte. La compression peut payer.

### WINDOW_EXPANDING

La fenÃªtre est en expansion active.

### WINDOW_PAID

La fenÃªtre a dÃ©jÃ  payÃ© une grande partie de son Ã©nergie.

### WINDOW_REBALANCING

Phase de rebalancement aprÃ¨s release.

---

## 8. Termes de compression / release

### LOW_COALITION_COMPRESSION

Plusieurs devises compressÃ©es ensemble en zone basse.

Exemple :

```text
GBP / USD / EUR / CAD compressÃ©s bas.
JPY haut extrÃªme.
```

### HIGH_PRESSURE_OPPOSITION

Devise ou famille haute qui exerce une pression sur une famille basse.

### M30_LOW_COALITION_COMPRESSION_GATE

Porte temporelle M30 crÃ©Ã©e par une compression basse multi-devise.

### ANGULAR_FIELD_OPENING

Ouverture du champ quand plusieurs devises prennent un angle fort dans un sens pendant quâ€™une devise opposÃ©e plie fortement.

### POST_COMPRESSION_EXPANSION_FIELD

Ã‰tat oÃ¹ la compression a dÃ©jÃ  libÃ©rÃ© et oÃ¹ le marchÃ© est en phase dâ€™expansion.

### M5_RELEASE_CONFIRMATION_AFTER_M30_GATE

Le M5 confirme tactiquement que la porte M30 commence Ã  payer.

### CAUSE_TO_EFFECT_EXPANSION_LEG

Une cause de force mesurable produit une jambe prix cohÃ©rente.

### RELEASE_POWER

Puissance de libÃ©ration issue dâ€™une compression passÃ©e.  
Ã€ ne pas confondre avec la densitÃ© instantanÃ©e.

### PRE_COMPRESSION_MEMORY

MÃ©moire dâ€™une compression prÃ©cÃ©dente utilisÃ©e pour comprendre une release prÃ©sente.

---

## 9. Termes de bataille / node

### CENTER_BATTLEFIELD_NODE

Node central oÃ¹ plusieurs forces se regroupent autour dâ€™une zone de dÃ©cision.

### EXTREME_RETURN_COMPRESSION_NODE

Node oÃ¹ une devise revient dâ€™un extrÃªme et rejoint une compression centrale.

### GBP_FROM_LOW_USD_REPULSED_NODE

Cas observÃ© : GBP revient dâ€™une zone basse pendant que USD est repoussÃ©.

### BIPOLAR_CONTESTED_RELEASE_WINDOW

FenÃªtre oÃ¹ les mÃªmes devises apparaissent dans des lectures opposÃ©es HIGH et LOW.

### MICRO_VS_HTF_ROTATION_CONTEST

Tension oÃ¹ les timeframes courts indiquent une direction opposÃ©e aux timeframes longs.

---

## 10. Termes de patterns temporels

### PULLURE_ABSORPTION_FIELD

Pattern oÃ¹ une devise encaisse plusieurs pullbacks successifs sans cÃ©der.

### EXTREME_BREATHING_FIELD

Respiration en zone extrÃªme, sans release immÃ©diate.

### ANGULAR_ALIGNMENT_NODE

Alignement angulaire simultanÃ© de plusieurs devises sur un mÃªme timeframe.

### ANGULAR_RELEASE_FIELD

Release lisible par lâ€™ouverture angulaire des devises.

---

## 11. RÃ¨gles de lecture

### RÃ¨gle 1

```text
Un timeframe supÃ©rieur ne donne pas toujours la direction.
Parfois il donne lâ€™espace.
```

### RÃ¨gle 2

```text
La compression nâ€™est pas toujours le moment visible.
La release peut Ãªtre visible aprÃ¨s coup.
```

### RÃ¨gle 3

```text
M30 ouvre la porte.
M15 porte la scÃ¨ne.
M5 montre la release.
M1 montre la recharge.
```

### RÃ¨gle 4

```text
Une devise peut ne pas Ãªtre dominante HTF,
mais avoir une permission dâ€™expansion.
```

### RÃ¨gle 5

```text
La densitÃ© locale ne suffit pas.
Il faut la mÃ©moire de compression.
```

---

## 12. Format conseillÃ© pour une phrase Cockpit

```text
HTF : champ ouvert mais contestÃ©.
M30 : compression basse validÃ©e.
M15 : scÃ¨ne en construction.
M5 : libÃ©ration angulaire active.
Lecture : fenÃªtre dâ€™expansion ouverte, dÃ©jÃ  en cours de paiement.
Attention : ne pas confondre compression et post-release.
```

```

---

# SOURCE: Docs\T006_Source_Staging\LEXIQUE__LEXIQUE_GRAMMAIRE_COMPORTEMENTS_POWERFLOW.txt

SHA256: FD389FB437A9E99EBA6C7DDDB0406A858AA8FD18869F506C228C9C05E610C53F
BYTES: 42748

```text
# Lexique, Grammaire et Comportements PowerFlow
## Le dictionnaire vivant du langage PowerFlow â€” V6

**Statut :** document de consolidation du corpus fourni  
**RÃ´le :** extraire le vocabulaire, les rÃ¨gles dâ€™addition et les scÃ¨nes comportementales propres Ã  PowerFlow.  
**RÃ¨gle suivie :** ne pas transformer PowerFlow en dictionnaire de trading classique. Les termes ci-dessous viennent du langage, des Labs, des rapports et des doctrines fournis.

---

# 0. Phrase noyau du langage PowerFlow

PowerFlow nâ€™est pas une usine Ã  signaux. Câ€™est un moteur de perception multi-devises et multi-timeframes.

La phrase complÃ¨te du langage PowerFlow peut se lire ainsi :

```text
acteur + comportement + contexte + timing + qualitÃ© + consÃ©quence
```

Exemple PowerFlow :

```text
GBP pousse proprement pendant que USD plie en extrÃªme H4, mais le cross M1 arrive tard.
```

Traduction opÃ©rationnelle :

```text
leader      = GBP
devise faible = USD
contexte    = pliure / extrÃªme H4
timing      = node tardif
qualitÃ©     = danger late
discipline  = ne pas courir aprÃ¨s le mouvement
```

ChaÃ®ne officielle :

```text
Flux
â†’ Ã‰vÃ©nements
â†’ Alertes / Signaux
â†’ MÃ©moire
â†’ Relations
â†’ Zones
â†’ ScÃ¨nes
â†’ Film
â†’ DÃ©cision trader
```

HiÃ©rarchie stricte :

```text
PowerFlow perÃ§oit, calcule, mesure, mÃ©morise.
ORION affiche, synthÃ©tise, protÃ¨ge la lecture.
Le trader dÃ©cide.
```

---

# 1. VOCABULAIRE ET LEXIQUE â€” Le dictionnaire PowerFlow

## 1.1 Acteurs fondamentaux

### Acteur
Une devise considÃ©rÃ©e comme un personnage du film. Les acteurs principaux du langage actuel sont :

```text
GBP, USD, EUR, JPY, CAD, CHF, AUD, NZD
```

Une devise nâ€™est pas seulement une valeur numÃ©rique. Elle a un comportement, un tempo, un rÃ´le, une signature et parfois un leadership.

Questions associÃ©es :

```text
Qui mÃ¨ne ?
Qui suit ?
Qui rÃ©siste ?
Qui abandonne ?
Qui confirme ?
Qui contredit ?
Qui absorbe ?
Qui se dÃ©synchronise ?
```

### Leader
Devise qui porte le mouvement principal ou qui impose la direction du champ. Un leader peut Ãªtre directionnel, pivot, refuge, ou leader de rotation.

### Follower
Devise qui suit un leader avec retard, souvent identifiable par corrÃ©lation dÃ©calÃ©e ou comportement de relais.

### Relay / Relais
Devise qui confirme sans forcÃ©ment mener. EUR est souvent dÃ©crit comme relais ou devise de synchronisation.

### Challenger
Devise qui approche ou conteste le leader. Elle nâ€™a pas encore pris la main, mais elle rÃ©duit lâ€™Ã©cart, change dâ€™angle ou prÃ©pare une rotation.

### Devise pivot
Devise qui pÃ¨se sur tout le champ sans forcÃ©ment Ãªtre un leader directionnel pur. USD est souvent pivot / gravitÃ© / contexte.

### Devise refuge
Devise qui rÃ©agit dans les phases risk-off ou de fuite. JPY et CHF sont les rÃ©fÃ©rences principales.

### Devise risque
Devise plus liÃ©e au flux directionnel et au risk-on/risk-off : GBP, EUR, AUD, NZD selon contexte.

---

## 1.2 Profils comportementaux des devises

### GBP â€” leader directionnel
GBP est dÃ©crit comme expressive, directionnelle, vive, parfois brutale. Quand GBP est propre, les paires GBP sâ€™alignent et le flux porte. GBPUSD devient alors paire prioritaire.

Signature :

```text
grandes phases
cassures nettes
coalition visible
mouvement rarement ambigu quand propre
```

PiÃ¨ge :

```text
GBP tardif aprÃ¨s un fort mouvement matinal peut devenir EXHAUST_NODE dÃ©guisÃ©.
```

### USD â€” pivot / gravitÃ©
USD exprime souvent une pression globale du marchÃ©. Il peut valider ou invalider les autres devises. Il nâ€™est pas toujours une cible directe ; parfois il est le poids de fond.

Signature :

```text
inertie
gravitÃ©
appel dâ€™air
pression globale
validation ou invalidation des autres devises
```

### JPY â€” oscillatoire / nerveux
JPY est trÃ¨s actif, rapide, violent, souvent lisible sur M1-M5. Sa prÃ©sence ne signifie pas toujours leadership propre : il peut produire beaucoup dâ€™activitÃ© avec faible cohÃ©rence.

Signature :

```text
verticalitÃ©
retournements rapides
clusters volatiles
signal fort sur M5, parfois dÃ©jÃ  vieux sur M15+
```

### EUR â€” relais / synchronisation
EUR valide ou invalide souvent ce que GBP ou USD initient. Il peut confirmer une lecture initiale par synchronisation.

Signature :

```text
oscillation rÃ©guliÃ¨re
cycles propres
rÃ©ponse avec dÃ©lai
synchronisation aprÃ¨s GBP ou USD
```

### CAD â€” leader diffÃ©rÃ© potentiel sur USD
CAD peut devancer USD dâ€™une Ã  deux barres dans certains contextes. Cette lecture devient une validation de lâ€™authenticitÃ© dâ€™un mouvement USD.

Signature :

```text
CAD tourne avant USD
CAD confirme ou invalide un dÃ©but de rebond USD
corrÃ©lation dÃ©calÃ©e Ã  surveiller
```

### AUD / NZD â€” challengers risk-on / rotation
AUD est plus rÃ©actif et volatil. NZD peut suivre AUD avec retard. Ils peuvent Ãªtre importants en rotation, mais doivent Ãªtre lus avec leur tempo et leur contexte.

### CHF â€” refuge lent / friction HTF
CHF est lent, structurel, souvent moins bruyant mais significatif lorsquâ€™il apparaÃ®t dans un contexte HTF tendu. Un signal CHF isolÃ© peut Ãªtre plus important quâ€™il ne semble.

---

## 1.3 Tempo natif

### Tempo natif
Timeframe oÃ¹ une devise parle le plus naturellement.

DÃ©finition :

```text
Le tempo natif est le timeframe oÃ¹ la devise donne son signal le plus frais, le plus lisible et le moins pÃ©rimÃ©.
```

Grille actuelle du corpus :

```text
JPY : M1-M5
CHF : M15-M30
EUR : M15-M30
GBP : M15-M30
USD : M15-M30, parfois M30 par inertie
AUD : M5-M15
NZD : M10-M20 / suit AUD avec retard
CAD : M10-M30 / peut devancer USD
```

Loi :

```text
Un signal nâ€™a pas la mÃªme fraÃ®cheur selon la devise.
Un croisement JPY vu sur M30 peut Ãªtre dÃ©jÃ  vieux.
Un croisement EUR vu sur M30 peut rester frais.
```

---

## 1.4 Comportements racines

### Push / Pousser
Une devise augmente sa pression. Elle avance, prend de lâ€™angle, rÃ©duit un gap ou force une autre devise Ã  rÃ©pondre.

### Fold / Plier
Une devise forte ou en extrÃªme perd son angle. Le pli peut Ãªtre le dÃ©but dâ€™un essoufflement, dâ€™une rotation ou dâ€™une absorption.

### Fake fold / Fausse pliure
Pli apparent qui ne confirme pas. Le marchÃ© semble cÃ©der, mais la rÃ©action suivante montre que ce nâ€™Ã©tait quâ€™une prÃ©paration, un piÃ¨ge ou une respiration.

### Charge / Charger
Ã‰nergie qui sâ€™accumule avant libÃ©ration possible.

Forme typique :

```text
zone extrÃªme
maintien
pullbacks refusÃ©s
micro-oscillations
compression
augmentation de densitÃ©
```

### Compress / Compresser
Deux forces restent proches, avec faible gap, ou une devise reste enfermÃ©e dans un couloir / palier. La compression peut Ãªtre spatiale, temporelle, ou comportementale.

### Release / LibÃ©rer
Ouverture claire dâ€™une compression ou dâ€™une tension. La libÃ©ration peut Ãªtre continuation, rotation ou rÃ©Ã©quilibrage.

### Lie / Mentir
Un signal apparent ne confirme pas. Exemple : cross sÃ©duisant sans suite, faux dÃ©part, fakeout, mouvement local qui ne tient pas dans le contexte.

### Clean / Nettoyer
Le marchÃ© piÃ¨ge, vide ou purge avant de rendre la structure plus lisible. Clean ne veut pas dire calme : cela veut dire que le film devient plus cohÃ©rent.

### Absorb / Absorber
La pression est reÃ§ue mais pas encore cassÃ©e. Lâ€™absorption retarde la libÃ©ration. Elle peut charger lâ€™Ã©lastique.

### Reject / Rejeter
Deux forces sâ€™approchent puis se repoussent franchement.

### Exhaust / Sâ€™Ã©puiser
Le mouvement existe encore mais son potentiel utile se dÃ©grade. Ce nâ€™est pas forcÃ©ment la fin immÃ©diate, mais le risque de poursuivre augmente.

### Pressure / Pression
Une devise pousse sans forcÃ©ment avoir encore switchÃ© complÃ¨tement. Une pression peut devenir approche, rÃ©duction de gap, accÃ©lÃ©ration de challenger.

### Delay / Retard
Signal rÃ©el mais opÃ©rationnellement tardif. Dans PowerFlow, un bon signal trop tard devient un mauvais signal.

### Sync / Synchronisation
Plusieurs paires, devises ou timeframes racontent le mÃªme film.

### Desync / DÃ©synchronisation
Une devise quitte le groupe, casse une harmonie, change dâ€™angle ou refuse la coalition. La premiÃ¨re devise qui se dÃ©synchronise aprÃ¨s une grappe de nodes peut donner le premier acteur de la phase.

### Relay / Relais
Devise confirmatrice qui ne mÃ¨ne pas forcÃ©ment mais valide le film.

### Gravity / GravitÃ©
Contexte HTF qui attire, limite ou pondÃ¨re la portÃ©e dâ€™un signal infÃ©rieur.

### Clean wave / Vague propre
Flux dense et structurÃ©.

### Dirty wave / Vague sale
Flux dense mais incohÃ©rent : beaucoup dâ€™activitÃ©, faible qualitÃ©, fakeouts possibles.

---

## 1.5 Pullure, pullback et respiration

### Pullure
Terme du trader pour les petits creux, micro-retours, micro-pullbacks ou petites oscillations internes dans une zone extrÃªme.

DÃ©finition PowerFlow :

```text
Une pullure est une micro-respiration visible dans une zone extrÃªme.
Elle nâ€™est pas forcÃ©ment du bruit.
Elle peut reprÃ©senter un mouvement impulsif miniature dans une construction plus large.
```

InterprÃ©tation :

```text
pullure refusÃ©e
â†’ absorption
â†’ tension qui monte
â†’ Ã©lastique qui se charge
```

Si les pullures deviennent de plus en plus profondes et durent plus longtemps, la zone peut Ãªtre en fuite ou en dÃ©synchronisation naissante.

### Pullback Ã©crasÃ©
Retour temporaire vers la neutralitÃ© qui est vite absorbÃ©. Plus les pullbacks sont Ã©crasÃ©s, plus la zone conserve son pouvoir dâ€™absorption.

### Respiration saine
Micro-oscillations qui restent dans le bassin de la zone. Les profondeurs diminuent ou restent stables, les retours sont rapides, la zone absorbe.

### DÃ©synchronisation naissante
Les pullbacks deviennent plus profonds, plus longs, moins bien rÃ©intÃ©grÃ©s. La zone perd son pouvoir dâ€™absorption avant mÃªme de casser visiblement.

---

## 1.6 Ã‰lastique

### Ã‰lastique chargÃ©
Devise Ã©crasÃ©e ou maintenue en extrÃªme, mais vivante en microstructure.

Signature :

```text
valeur moyenne plate ou extrÃªme
micro-oscillations prÃ©sentes
pullbacks avortÃ©s
asymÃ©trie des micro-mouvements
durÃ©e en zone
tension_signature Ã©levÃ©e
```

Formule conceptuelle :

```text
Ã‰LASTIQUE_CHARGÃ‰ =
extrÃªme relatif
+ durÃ©e
+ micro-variance
+ pullbacks refusÃ©s
+ absorption
```

### Ã‰lastique cassÃ©
La zone ne retient plus. Les pullbacks sâ€™approfondissent, lâ€™absorption ne fonctionne plus, la trajectoire sort du bassin ou la rupture sâ€™accÃ©lÃ¨re.

### Devise morte
Devise plate Ã  toutes les Ã©chelles : peu de micro-oscillation, faible entropie, faible mouvement. Ã€ distinguer dâ€™un Ã©lastique chargÃ©.

### Bruit blanc
ActivitÃ© sans structure ni asymÃ©trie exploitable. Ne pas confondre avec compression chargÃ©e.

---

## 1.7 Index comportemental bornÃ©

### Index comportemental bornÃ©
Mesure relative dâ€™une devise par rapport Ã  sa propre norme et Ã  lâ€™USD comme pivot.

Formule :

```text
spread(t) = force_devise(t) - force_usd(t)
Z(t)      = (spread(t) - moyenne(spread, lookback)) / Ã©cart_type(spread, lookback)
Index(t)  = clip(Z(t), -3, +3)
```

InterprÃ©tation :

```text
Index > +2  = comportement extrÃªme haut vs USD
Index â‰ˆ 0   = comportement normal
Index < -2  = comportement extrÃªme bas / Ã©lastique potentiellement chargÃ©
```

RÃ´le :

```text
ne plus lire une valeur brute 0-100,
mais lire un comportement relatif et anormal.
```

---

## 1.8 Tension accumulÃ©e

### Tension accumulÃ©e
Ã‰nergie potentielle construite par une devise dans une zone ou un Ã©tat extrÃªme.

Formule actuelle :

```text
tension_score = |Z_current| Ã— log(1 + bars_in_extreme) Ã— absorption_factor
```

Facteurs :

```text
ACCUMULATING â†’ 1.5
NEUTRAL      â†’ 1.0
LEAKING      â†’ 0.6
RUPTURE      â†’ 0.2
```

Formule complÃ¨te candidate :

```text
tension_score =
behavioral_index
Ã— log(1 + barres_en_extreme)
Ã— tension_signature
Ã— pullback_asymmetry
```

Lecture :

```text
plus la devise reste longtemps en zone extrÃªme
et plus les pullbacks sont absorbÃ©s,
plus la libÃ©ration potentielle devient violente.
```

---

## 1.9 Tension signature

### Tension signature
Rapport entre micro-variance et macro-variance.

```text
tension_signature = micro_variance / (macro_variance + Îµ)
```

InterprÃ©tation :

```text
tension_signature >> 1 â†’ devise plate en moyenne mais agitÃ©e en micro = Ã©lastique chargÃ©
tension_signature â‰ˆ 1  â†’ devise vraiment morte / bruit blanc
```

---

## 1.10 Compression du temps / extension du temps

### Compression de temps
Beaucoup dâ€™information ou de mouvement en peu de barres. Le marchÃ© accÃ©lÃ¨re son langage.

Exemple conceptuel :

```text
GBP passe de 12 Ã  52 en 3 barres.
```

### Extension de temps
Le marchÃ© flotte, les barres semblent vides, le temps sâ€™allonge.

Exemple conceptuel :

```text
USD reste Ã  9-10 pendant 15 barres.
```

### DensitÃ© temporelle
MÃ©trique proposÃ©e :

```text
densitÃ©_temporelle = abs(delta_force) / nombre_de_barres
```

InterprÃ©tation :

```text
mÃªme distance en 3 barres â‰  mÃªme distance en 30 barres.
Le temps devient lui-mÃªme une information.
```

### Temps informationnel
Temps mesurÃ© par la quantitÃ© de changement, de tension, de retournements et de densitÃ© â€” pas seulement par lâ€™horloge.

### Entropie locale
Outil candidat pour distinguer compression chargÃ©e et session creuse.

```text
E = entropie locale
V = volatilitÃ© rÃ©alisÃ©e
T = taux de retournement
```

Lecture :

```text
compression chargÃ©e = E Ã©levÃ©e, V modÃ©rÃ©e, T Ã©levÃ©
session creuse      = E faible, V faible, T faible
```

---

## 1.11 Vibration

### Vibration
Perception visuelle encore non totalement formalisÃ©e : rythme interne, rÃ©gularitÃ© dâ€™oscillation, frÃ©quence dominante, sensation que la sÃ©quence â€œsonne justeâ€.

Statut :

```text
Ã  observer avant de coder.
```

HypothÃ¨se :

```text
certaines sÃ©quences sont cohÃ©rentes parce que leur frÃ©quence dominante est stable ou signifiante.
```

---

## 1.12 Nodes et Ã©vÃ©nements

### Node
Point ou fenÃªtre oÃ¹ le film change dâ€™Ã©tat. Un node nâ€™est pas forcÃ©ment un croisement.

DÃ©finition Ã©largie :

```text
un node est une sÃ©quence comportementale construite par prix, force, temps et contexte.
```

Un cross peut Ãªtre :

```text
dÃ©part
confirmation
objectif de bataille atteint
retard
piÃ¨ge
fin de jambe
```

Question centrale :

```text
ce node ouvre-t-il le film ou le termine-t-il ?
```

### Node building sequence
SÃ©quence de construction dâ€™un node :

```text
cross initial
â†’ divergence prix / force
â†’ fake fold
â†’ mÃ¨che / mur / prise de liquiditÃ©
â†’ collage ou distance maintenue
â†’ absorption
â†’ dÃ©synchronisation
â†’ sÃ©paration significative
â†’ node actif
â†’ extrÃªme
â†’ re-cross / Ã©quilibre orchestrÃ©
```

### Active node
Moment oÃ¹ la synchronisation casse ou oÃ¹ lâ€™Ã©cartement devient significatif. Le contact nâ€™est pas forcÃ©ment le vrai node.

### Post-cross behavior
Comportement aprÃ¨s croisement. Loi :

```text
Le cross pose la question.
Le comportement post-cross donne la rÃ©ponse.
```

### GAP_BEHAVIOR
Comportement de lâ€™Ã©cart entre deux devises : maintien, fermeture, extension, plateau, tension, recollage.

### GAP_HOLD_TIME
DurÃ©e pendant laquelle un Ã©cart se maintient. Peut signaler une opposition structurÃ©e ou une compression.

### Recollage / Collage
Rapprochement ou maintien proche de deux forces. Peut Ãªtre prÃ©paration et non validation.

### SÃ©paration angle
Angle de sÃ©paration aprÃ¨s contact, recollage ou dÃ©synchronisation. Plus lâ€™angle est propre, plus le comportement devient lisible.

### Orchestrated equilibrium
Ã‰quilibre construit aprÃ¨s bataille : retour ou re-cross oÃ¹ plusieurs forces se rÃ©organisent.

---

## 1.13 Types de nodes

### CROSS_NODE
Croisement rÃ©el entre forces.

### NO_TOUCH_STRETCH_NODE
Les forces ne se touchent pas mais gardent distance, opposition ou Ã©tirement significatif.

### PINCH_FOLD_NODE
Les forces se croisent, se pincent puis se plient.

### PARALLEL_CANCEL_NODE
Forces parallÃ¨les Ã  distance qui sâ€™annulent ou temporisent.

### TEMPORAL_EVENT_NODE
FenÃªtre oÃ¹ quelque chose se passe dans les flux mÃªme sans contact exact.

### TRIPLE_NODE
Concentration / croisement de trois forces ou trois acteurs significatifs.

### TRIPLE_CROSS_CLUSTER
Deux ou plusieurs prÃ©parations de triple node dans une mÃªme fenÃªtre fractale. Le node devient une grappe temporelle chargÃ©e dâ€™Ã©nergie.

### NODE_ENERGY
Charge du node. Loi :

```text
Un node nâ€™a pas seulement une forme.
Il a une charge.
```

### EXTREME_BOUND_NODE
Node liÃ© Ã  une zone extrÃªme ou Ã  un retour dâ€™extrÃªme.

### MULTI_NODE_SEQUENCE
Suite de nodes proches qui indique rÃ©organisation forte de la structure.

---

## 1.14 Temporal Nodes

### TEMPORAL_NODE
Lecture Ã©vÃ©nementielle multi-timeframe. Il regroupe des signaux dans une fenÃªtre temporelle et les classe selon leur combinaison.

Types validÃ©s :

```text
NODE_COMPLET_FULL = CONVERGENCE + KISS_REJECT / combinaison rare
NODE_COMPLET      = CONVERGENCE active
NODE_REPULSION    = rÃ©pulsion forte, Ã  amÃ©liorer
NODE_CROSS        = croisement confirmÃ©
NODE_SIMPLE       = bruit filtrable
```

### Grammaire pondÃ©rÃ©e Module A

```text
COMPRESSION          = 1
COMPRESSION_BREAK    = 2
CONVERGENCE          = 5
CROSS                = 2
KISS_REJECT          = 3
COMPRESSION_SQUEEZE  = 3
SLINGSHOT            = 2
REPULSION            = 4
```

InterprÃ©tation :

```text
CONVERGENCE rare = trÃ¨s fort
NODE_CROSS frÃ©quent = bruit normal si isolÃ©
M1 peut prÃ©parer M15
FractalitÃ© confirmÃ©e si plusieurs TF sâ€™alignent
```

---

## 1.15 Signaux V6

### CROSS
Croisement. Ne vaut rien seul. Il pose une question.

### KISS_REJECT
Les forces sâ€™approchent, se frÃ´lent, puis rejet fort. Peut Ãªtre alignÃ© ou contre-tendance HTF.

### FAKEOUT
Signal sÃ©duisant qui piÃ¨ge. En V6, il dÃ©grade lâ€™intÃ©rÃªt dâ€™un cran.

### SUPER_SWITCH
Switch de domination plus fort quâ€™un cross simple.

### CONVERGENCE
Plusieurs Ã©lÃ©ments ou timeframes se rejoignent. Rare. Signal fort sâ€™il sâ€™inscrit dans une scÃ¨ne.

### COMPRESSION
Palier, couloir, zone dâ€™attente. Souvent utile pour DB / Lab plutÃ´t que Telegram direct.

### COMPRESSION_BREAK
Sortie de palier. Peut devenir dÃ©clencheur brut si filtrÃ© par scÃ¨ne, HTF et alignement.

### COMPRESSION_SQUEEZE
Une devise dÃ©jÃ  comprimÃ©e subit la poussÃ©e adverse dâ€™une autre devise ; le gap se resserre et lâ€™Ã©crase.

### COMPRESSION_SQUEEZE_CONTINUATION
Repli compressÃ© dans une zone extrÃªme de timeframe infÃ©rieur qui repart dans le sens du leader H1/H4/D1.

### COMPRESSION_SQUEEZE_REVERSAL
Compression en fin de cycle HTF oÃ¹ lâ€™ancienne victime reprend la main. Peut Ãªtre setup de rotation ou warning.

### SLINGSHOT
Ã‰nergie de fronde aprÃ¨s repli ; peut annoncer relance si contexte cohÃ©rent.

### APPROACH
Approche imminente, souvent avant contact ou seuil.

### ZONE_BATTLE
Bataille dans une zone dynamique.

### EXTREME_HIGH / EXTREME_LOW
ExtrÃªme relatif ou contextuel ; pas seulement seuil fixe.

### REPULSION
Deux forces se repoussent, divergent continuellement, sans inversion rapide. Inverse comportemental du cross.

---

## 1.16 Zones

### Zone dynamique
Une zone nâ€™est pas une ligne fixe. Elle est un comportement.

Dimensions dâ€™une zone :

```text
position actuelle
phase
temps passÃ©
durÃ©e rÃ©elle selon timeframe
sortie
cross / changement de rang
tension opposÃ©e
session
```

### Zone mÃ©moire
Zone oÃ¹ les acteurs ont dÃ©jÃ  combattu. Elle garde un vÃ©cu.

### Zone extrÃªme
Zone de tension, excÃ¨s, mÃ©moire ou prÃ©paration. Les zones 20/30/80/90 sont des zones de travail dynamiques, pas des lignes absolues.

### LOW_ZONE_WORK
Devise qui travaille la cave / zone basse.

### LOW_ZONE_RELEASE_TO_CENTER
Sortie de zone basse vers centre.

### HIGH_ZONE_HOLD
Maintien en zone haute.

### HIGH_ZONE_DECELERATION
DÃ©cÃ©lÃ©ration en zone haute, possible fatigue.

### HIGH_ZONE_DOMINANCE_LOSS
Perte de rang aprÃ¨s zone haute ; peut peser dans une scÃ¨ne de rotation.

### CENTER_BATTLE_ZONE
Bataille dans la zone centrale ; souvent zone de validation plutÃ´t que zone dâ€™entrÃ©e.

### ZONE_TIME_WEIGHT
Poids donnÃ© au temps vÃ©cu dans une zone.

Une zone prend du poids si :

```text
elle dure longtemps
elle sort ou rejette
elle confirme par cross
elle confirme par changement de rang
elle fait double top / double bottom
elle a une tension opposÃ©e
```

### SESSION_ZONE_MEMORY
MÃ©moire de zone liÃ©e Ã  la session.

---

## 1.17 ScÃ¨nes ORION / PowerFlow

### ScÃ¨ne
Contexte interprÃ©tÃ© Ã  partir des courbes, relations, zones, nodes et temps.

Formule :

```text
relation + node + zone vÃ©cue + temps de zone = scÃ¨ne PowerFlow
```

### COALITION_PUSH
Plusieurs devises ou paires poussent dans la mÃªme direction, souvent contre une cible commune.

### ROTATION_BUILDING
Construction dâ€™une rotation. Un ancien leader fatigue, un challenger rÃ©pond, le champ se rÃ©organise.

### OPPOSITION_REBALANCE
Opposition qui rÃ©Ã©quilibre le champ.

### TREND_CONTINUATION
Continuation propre aprÃ¨s respiration / zone / confirmation.

### COMPRESSION_BUILD
Ã‰nergie stockÃ©e dans compression.

### COMPRESSION_RELEASE
LibÃ©ration de compression.

### CENTER_BATTLE
Bataille centrale, zone de validation, hÃ©sitation ou transition.

### CHAOS_NO_TRADE
Trop de bruit, faible cohÃ©rence, pas de structure exploitable.

---

## 1.18 Niveaux dâ€™intÃ©rÃªt

### IGNORE
Bruit.

### WATCH_ZONE
Zone intÃ©ressante mais pas encore structure active.

### STRUCTURE_BUILDING
Le film raconte quelque chose ; la scÃ¨ne est en construction.

### TACTICAL_READY
Confirmation tactique possible ; chercher la jambe / validation.

### SIGNAL_VALIDATED
Confluence forte. Telegram possible seulement si les conditions V6 sont rÃ©unies.

---

## 1.19 Timing

### EARLY
Naissance possible. Ã€ observer ; pas une confirmation.

### ACTIVE
Film structurÃ© et actif.

### LATE
Signal rÃ©el mais tardif. Danger.

### EXHAUST
Risque de fin de mouvement.

Loi :

```text
Un bon signal trop tard devient un mauvais signal.
```

### Node timing Pattern 1

```text
EARLY_NODE
ACTIVE_NODE
LATE_NODE
EXHAUST_NODE
```

---

## 1.20 Timeframes

### M1
Capteur nerveux, naissance, microstructure, microfilm. M1 ne commande jamais seul.

### M5
Scout / timing / confirmation tactique.

### M15
Intention / scÃ©nario / structure tactique majeure.

### M30
Transition / structure intraday.

### H1
RÃ©gime / switch / Ã©tat de sÃ©ance.

### H4
GravitÃ©, respiration, zone majeure, structure lourde.

### Daily
Cycle, pente mÃ¨re, mÃ©moire structurelle, poids probabiliste.

### Weekly
Intention lente, gravitÃ© profonde, rÃ©gime long terme.

Loi synthÃ©tique :

```text
Daily pÃ¨se.
H4 autorise.
H1 raconte.
M15 structure.
M5 dÃ©clenche.
M1 affine.
```

---

## 1.21 RÃ©gimes et qualitÃ©s de flow

### Flow propre
Leader clair, cohÃ©rence multi-paires, propagation lower timeframe, peu de danger late.

### Flow structurel
Flux lisible, cadrÃ© par zone / HTF / scÃ¨ne.

### Flow fragile
Signal local sÃ©duisant mais contexte supÃ©rieur, rÃ©gime ou structure insuffisante.

### Flow sale
ActivitÃ© dense, faible cohÃ©rence, fakeouts possibles.

### FLOW_CONTINUATION_PROPRE
Continuation dans le sens dâ€™un leader stable et alignement suffisant.

### FLOW_PULLBACK_TENDANCE
Repli dans tendance, potentiellement exploitable si la recharge est propre.

### FLOW_RANGE_SALE
Croisements frÃ©quents, peu dâ€™extension, valeurs proches de 50, absence de leader net.

### FLOW_ROTATION
Ancienne domination qui se fatigue ; challenger ou ancienne victime reprend la main.

### FLOW_EXHAUSTION
Flux tardif ou en fin de phase.

### FLOW_INCONNU
Pas assez de matiÃ¨re ou incohÃ©rence.

---

## 1.22 Notions Lab / MÃ©moire

### Lab
Espace de traduction : vision humaine â†’ mot Flow â†’ hypothÃ¨se â†’ trace DB â†’ variable manquante â†’ future spec â†’ code.

### NOTE
Observation brute.

### VOCABULARY
Terme Ã  ajouter au langage.

### HYPOTHESIS
HypothÃ¨se comportementale.

### TEST_DB
HypothÃ¨se testable sur DB.

### SPEC_FUTURE
Ã€ transformer plus tard en spÃ©cification.

### PATTERN_CANDIDATE
Pattern candidat, pas encore loi.

### REJECTED
HypothÃ¨se rejetÃ©e.

---

# 2. LA GRAMMAIRE DES SIGNAUX â€” Comment les Ã©lÃ©ments sâ€™additionnent

## 2.1 Grammaire principale

```text
Acteur + Comportement + Contexte + Timing + QualitÃ© + ConsÃ©quence
```

Exemple :

```text
EUR relaie GBP contre USD, en M15 scÃ©nario, aprÃ¨s compression, mais le node est late.
```

Lecture :

```text
acteur      = EUR / GBP / USD
comportement= relais + coalition
contexte    = M15 scÃ©nario + compression
timing      = late
qualitÃ©     = danger
consÃ©quence = ne pas poursuivre
```

---

## 2.2 Grammaire du film

```text
Flux â†’ Ã‰vÃ©nement â†’ MÃ©moire â†’ Relation â†’ Zone â†’ ScÃ¨ne â†’ Film â†’ DÃ©cision
```

Explication :

```text
Flux       = forces vivantes
Ã‰vÃ©nement  = cross, compression, rupture, kiss, fakeout
MÃ©moire    = zone dÃ©jÃ  travaillÃ©e, durÃ©e, vÃ©cu
Relation   = coalition, opposition, leader/follower
Zone       = champ comportemental
ScÃ¨ne      = contexte lisible
Film       = rÃ©cit multi-TF
DÃ©cision   = acte humain
```

---

## 2.3 Grammaire V6 des signaux

```text
Le signal pose la question.
La scÃ¨ne donne le contexte.
Lâ€™alignement TF valide ou invalide.
ORION synthÃ©tise.
Le trader dÃ©cide.
```

En V6, les signaux se divisent en trois familles :

```text
DÃ©clencheurs :
CROSS, SUPER_SWITCH, KISS_REJECT, COMPRESSION_BREAK, COMPRESSION_SQUEEZE

Filtres nÃ©gatifs :
FAKEOUT

Microfilm interne / DB uniquement :
COMPRESSION, SLINGSHOT, APPROACH, ZONE_BATTLE, CONVERGENCE, EXTREME_HIGH/LOW
```

RÃ¨gle :

```text
Un dÃ©clencheur seul nâ€™est pas une dÃ©cision.
Un microfilm peut Ãªtre prÃ©cieux pour la DB mais inutile en Telegram.
Un filtre nÃ©gatif dÃ©grade la lecture.
```

---

## 2.4 Grammaire du cross

```text
CROSS = question
POST_CROSS_BEHAVIOR = rÃ©ponse
```

Formules :

```text
CROSS + absorption + sÃ©paration propre = node actif potentiel
CROSS + recollage sans sÃ©paration = prÃ©paration ou temporisation
CROSS + fake fold + wick/liquidity grab = piÃ¨ge possible
CROSS + zone vÃ©cue + confirmation rang = valeur renforcÃ©e
CROSS isolÃ© + aucune structure = bruit / signal pauvre
```

---

## 2.5 Grammaire de la compression

```text
COMPRESSION = Ã©nergie stockÃ©e
COMPRESSION_BREAK = libÃ©ration
COMPRESSION_SQUEEZE = pression adverse maximale
```

Formules :

```text
COMPRESSION + durÃ©e + gap faible = palier / attente
COMPRESSION + pullbacks refusÃ©s = absorption
COMPRESSION + squeeze + HTF leader = continuation possible
COMPRESSION + fin de cycle HTF + ancienne victime reprend = reversal warning
COMPRESSION seule en live = souvent DB / Lab, pas Telegram
```

---

## 2.6 Grammaire de lâ€™Ã©lastique

```text
ExtrÃªme relatif
+ durÃ©e en zone
+ micro-oscillations
+ pullbacks avortÃ©s
+ asymÃ©trie
= Ã‰LASTIQUE_CHARGÃ‰
```

Formule de tension complÃ¨te :

```text
behavioral_index
Ã— log(1 + barres_en_extreme)
Ã— tension_signature
Ã— pullback_asymmetry
= tension_score complet
```

InterprÃ©tation :

```text
Si tous les facteurs sâ€™alignent, PowerFlow lit une Ã©nergie potentielle.
Si un facteur manque, le signal est qualifiÃ© plus fragile.
```

---

## 2.7 Grammaire de la zone

```text
Zone = comportement + temps + mÃ©moire
```

Formules :

```text
Zone haute tenue + dÃ©cÃ©lÃ©ration = fatigue possible
Zone haute tenue + perte de rang = rotation possible
Zone basse travaillÃ©e + sortie vers centre = rebalance possible
Zone + cross de confirmation = poids renforcÃ©
Zone + durÃ©e longue = ZONE_TIME_WEIGHT
Zone centrale + triple/cross = validation ou bataille
```

Loi :

```text
Une zone nâ€™est pas un niveau.
Une zone est un comportement.
```

---

## 2.8 Grammaire multi-devise

```text
Une devise parle vraiment quand elle apparaÃ®t sur plusieurs paires.
```

Formules :

```text
GBP > USD + GBP > JPY + GBP > EUR = GBP leader probable
EUR aprÃ¨s GBP/USD = relais / synchronisation possible
JPY trÃ¨s actif + faible cohÃ©rence = flux nerveux, pas forcÃ©ment leader propre
CAD bouge avant USD = validation ou invalidation future du signal USD
```

---

## 2.9 Grammaire multi-timeframe

```text
M1 = naissance / microfilm
M5 = timing / jambe tactique
M15 = scÃ©nario
M30/H1 = structure intraday / transition
H4/D1/W1 = gravitÃ©
```

Formules :

```text
M1 fort seul = bruit ou prÃ©-signal
M1 + M5 + M15 alignÃ©s = fractalitÃ© utile
M5 dÃ©clenche mais M15 nâ€™a pas de scÃ©nario = fragile
M15 scÃ©nario + M5 jambe + M1 microstructure = setup lisible
Signal M30 contre H4 en accumulation = prÃ©maturÃ© / respiration intra-phase
```

---

## 2.10 Grammaire de lâ€™alignement TF

Verdicts V6 :

```text
ALIGNEMENT_COMPLET
ALIGNEMENT_PARTIEL
STRUCTURE_NAISSANTE
CONFLIT_STRUCTURE
CONFLIT_DIRECT
NEUTRE
```

RÃ¨gles :

```text
TF courts alignÃ©s + TF longs vides = STRUCTURE_NAISSANTE
TF courts contre TF longs = CONFLIT_STRUCTURE
Alignement complet fort = TACTICAL_READY minimum
Conflit TF = plafonne Ã  WATCH_ZONE
```

---

## 2.11 Grammaire des Temporal Nodes

```text
CONVERGENCE rare + KISS_REJECT = NODE_COMPLET_FULL
CONVERGENCE active = NODE_COMPLET
REPULSION + BREAK = NODE_REPULSION
CROSS + BREAK = NODE_CROSS
Faible combinaison = NODE_SIMPLE
```

PondÃ©ration :

```text
CONVERGENCE 5 > REPULSION 4 > KISS_REJECT / SQUEEZE 3 > BREAK / CROSS / SLINGSHOT 2 > COMPRESSION 1
```

Lecture :

```text
NODE_COMPLET_FULL = alerte critique
NODE_COMPLET = signal fort
NODE_CROSS = structure, frÃ©quent
NODE_SIMPLE = bruit Ã  filtrer
```

---

## 2.12 Grammaire des scÃ¨nes

```text
Relation + Node + Zone vÃ©cue + Temps de zone = ScÃ¨ne ORION
```

Exemples :

```text
COALITION_PUSH + zone confirmÃ©e + alignement M5/M15 = TACTICAL_READY
ROTATION_BUILDING + conflit H1 = STRUCTURE_NAISSANTE / WATCH
TREND_CONTINUATION + LOW_ZONE_EXIT + alignement = continuation aprÃ¨s respiration
CHAOS_NO_TRADE + fakeout + faible cohÃ©rence = ne pas agir
```

---

## 2.13 Grammaire des rÃ©gimes

```text
RÃ©gime prÃ©cÃ¨de pattern.
```

Formules :

```text
Trend propre + leader stable + alignement = revalorisation du signal
Range structurÃ© + signal local = surveiller, pas surcharger
Flow sale + cross frÃ©quent = danger fakeout
Rotation + ancienne victime qui reprend = changement possible
News/toxique + pattern standard = dÃ©gradation ou suspension
```

---

## 2.14 Grammaire de la dÃ©cision

```text
Voir le flux.
DÃ©tecter lâ€™Ã©vÃ©nement.
Alerter vite.
Filtrer humainement.
DÃ©cider clairement.
```

Le systÃ¨me peut afficher :

```text
WATCH
ARMED
CONFIRM
DANGER
```

Mais il ne doit pas produire BUY/SELL.

---

# 3. INTERPRÃ‰TATION DES COMPORTEMENTS â€” Les scÃ¨nes du marchÃ©

## 3.1 Devise plate en zone basse avec micro-sauts

Lecture PowerFlow :

```text
Ce nâ€™est pas automatiquement une devise morte.
Cela peut Ãªtre un Ã©lastique chargÃ©.
```

Conditions qui renforcent la lecture â€œÃ©lastique chargÃ©â€ :

```text
zone extrÃªme relative
durÃ©e en zone
micro-oscillations
pullures / pullbacks refusÃ©s
asymÃ©trie des micro-mouvements
entropie locale non nulle
tension_signature Ã©levÃ©e
```

Conditions qui affaiblissent :

```text
faible micro-variance
faible entropie
aucune tentative
aucune absorption visible
contexte de session creuse
```

InterprÃ©tation finale :

```text
plate + vivante = tension
plate + lisse = morte / bruit blanc
```

---

## 3.2 Pullures en zone extrÃªme

Les petits creux et micro-retours dans une zone extrÃªme sont des respirations. Ils peuvent Ãªtre reprÃ©sentatifs de mouvements impulsifs internes.

ScÃ¨ne :

```text
La devise est tenue en extrÃªme.
Elle tente de respirer.
Chaque pullure refusÃ©e confirme que la zone absorbe.
La tension sâ€™accumule.
```

Danger :

```text
si les pullures deviennent plus profondes et plus longues,
la respiration saine devient dÃ©synchronisation naissante.
```

---

## 3.3 CAD qui tourne avant USD

Lecture PowerFlow :

```text
CAD peut Ãªtre leader diffÃ©rÃ© de USD.
Si CAD a bougÃ© 1-2 barres avant USD, le rebond USD est plus authentique.
Si USD bouge sans confirmation CAD, il peut Ãªtre prÃ©maturÃ© ou faux dÃ©part.
```

Workflow :

```text
M5 USD montre un dÃ©but de rebond.
PowerFlow vÃ©rifie CAD sur les 1-2 barres prÃ©cÃ©dentes.
CAD confirme â†’ signal USD renforcÃ©.
CAD ne confirme pas â†’ signal USD reclassÃ© fragile / false start.
```

---

## 3.4 Alignement angulaire simultanÃ©

Lecture PowerFlow :

```text
Quand plusieurs devises changent de direction au mÃªme angle et au mÃªme moment,
ce nâ€™est pas une coÃ¯ncidence : câ€™est une convergence dâ€™intentions.
```

Signal rare :

```text
EUR + GBP + USD changent ensemble
angle commun
fenÃªtre 1-2 barres
pic de courbure ou convergence de phase
```

InterprÃ©tation :

```text
moment clÃ©
libÃ©ration possible
qualitÃ© maximale si le contexte confirme
```

Garde-fou :

```text
Ã  valider par scÃ¨ne, zone, HTF et fraÃ®cheur ; ne jamais transformer en BUY/SELL automatique.
```

---

## 3.5 JPY trÃ¨s actif mais peu cohÃ©rent

Lecture :

```text
JPY peut produire beaucoup dâ€™Ã©vÃ©nements sans Ãªtre un leader propre.
```

InterprÃ©tation :

```text
activitÃ© â‰  qualitÃ©
nervositÃ© â‰  leadership
volatile â‰  tradable sans contexte
```

Si JPY est actif sur plusieurs paires avec faible cohÃ©rence :

```text
flux nerveux
danger de surinterprÃ©tation
exÃ©cution difficile
```

---

## 3.6 GBP propre multi-paires

Lecture :

```text
Quand GBP se confirme sur plusieurs paires, il peut devenir leader directionnel prioritaire.
```

ScÃ¨ne :

```text
GBPUSD + GBPJPY + GBPEUR / autres paires alignÃ©es
â†’ coalition GBP
â†’ leader clair
â†’ paire GBPUSD prioritaire
```

Danger :

```text
si le cluster GBP arrive tard, il peut Ãªtre EXHAUST_NODE dÃ©guisÃ©.
```

---

## 3.7 EUR en relais

Lecture :

```text
EUR apparaÃ®t aprÃ¨s GBP ou USD pour confirmer ou invalider la lecture initiale.
```

ScÃ¨ne :

```text
GBP initie
USD pivote ou oppose
EUR rÃ©pond avec dÃ©lai
â†’ synchronisation ou contradiction
```

---

## 3.8 Triple node / triple cross cluster

Lecture :

```text
Deux ou plusieurs prÃ©parations de triple node dans une fenÃªtre courte signalent une grappe temporelle chargÃ©e dâ€™Ã©nergie.
```

InterprÃ©tation :

```text
les forces se regroupent
se rejettent
se recroisent
la structure se rÃ©organise
la premiÃ¨re dÃ©synchronisation donne souvent le premier acteur de la phase
```

Action ORION :

```text
M1 seul = STRUCTURE_BUILDING max
M5/M15 confirmÃ© = TACTICAL_READY possible
pas de Telegram automatique en V1.1
```

---

## 3.9 Refused cross / cross attendu qui ne vient pas

Lecture :

```text
Le marchÃ© prÃ©pare un croisement attendu, mais une force refuse de cÃ©der.
```

InterprÃ©tation :

```text
bataille
temporisation
distant parallel battle
fausse attente
prÃ©paration dâ€™un changement plus tardif
```

---

## 3.10 Center validation cross

Lecture :

```text
Les croisements importants peuvent apparaÃ®tre en zone centrale, pas seulement aux extrÃªmes.
```

InterprÃ©tation :

```text
la zone centrale valide que la structure a payÃ©
le marchÃ© revient Ã  lâ€™Ã©quilibre
la bataille se transforme en rÃ©cit final
```

---

## 3.11 Compression puis break

ScÃ¨ne :

```text
une devise reste en palier
lâ€™autre pousse ou le contexte se charge
la sortie de palier devient COMPRESSION_BREAK
```

Lecture :

```text
COMPRESSION = silence / attente / Ã©nergie stockÃ©e
BREAK = reprise de parole
```

Danger :

```text
compression simple peut spammer ; en live elle doit Ãªtre filtrÃ©e ou gardÃ©e en DB.
```

---

## 3.12 Compression squeeze continuation

ScÃ¨ne :

```text
une devise se replie en zone extrÃªme infÃ©rieure
reste compressÃ©e
puis repart dans le sens du leader H1/H4/D1
```

Lecture :

```text
recharge avant continuation
```

---

## 3.13 Compression squeeze reversal

ScÃ¨ne :

```text
fin de cycle HTF
ancienne victime comprimÃ©e commence Ã  reprendre la main
```

Lecture :

```text
warning de rotation
ne plus charger dans lâ€™ancien sens sans confirmation
```

---

## 3.14 Zone haute tenue puis dÃ©cÃ©lÃ©ration

Lecture :

```text
la devise domine mais fatigue.
```

Si elle perd son rang aprÃ¨s zone haute :

```text
rotation possible
HIGH_ZONE_DOMINANCE_LOSS
```

---

## 3.15 Zone basse travaillÃ©e puis sortie

Lecture :

```text
la devise a travaillÃ© la cave.
La sortie vers le centre peut signaler reconstruction ou rebalance.
```

Si sortie + cross/rang :

```text
LOW_ZONE_EXIT_RANK_CONFIRMATION
```

---

## 3.16 Opposition diffÃ©rÃ©e

Lecture :

```text
une devise rÃ©agit avec retard Ã  la poussÃ©e adverse.
```

ScÃ¨ne :

```text
USD dÃ©clenche
EUR rÃ©pond aprÃ¨s dÃ©lai
GBP se synchronise ou contredit
```

---

## 3.17 Coalition multiple

Lecture :

```text
la paire nâ€™est plus seule.
Le mouvement vient dâ€™un camp.
```

Exemple :

```text
GBP + EUR contre USD
```

InterprÃ©tation :

```text
la coalition donne le poids
le timeframe donne lâ€™Ã©chelle
la zone donne le vÃ©cu
la scÃ¨ne donne le film
```

---

## 3.18 Rotation depuis extrÃªmes

ScÃ¨ne :

```text
ancienne force Ã  lâ€™extrÃªme fatigue
challenger sort de sa zone
opposition se recompose
centre devient validation
```

Lecture :

```text
rotation active ou rotation building selon confirmation.
```

---

## 3.19 Flow propre vs flow sale

### Flow propre
```text
leader clair
multi-pair coherence
propagation lower TF
pas de danger late
zone/context alignÃ©s
```

### Flow sale
```text
beaucoup dâ€™Ã©vÃ©nements
faible cohÃ©rence
cross frÃ©quents
fakeouts
leaders contradictoires
```

InterprÃ©tation :

```text
un marchÃ© actif nâ€™est pas forcÃ©ment tradable.
```

---

## 3.20 Signal tardif

Lecture :

```text
le signal peut Ãªtre vrai mais trop tardif pour Ãªtre utile.
```

ScÃ¨ne :

```text
le mouvement a dÃ©jÃ  payÃ©
le cluster revient aprÃ¨s la fenÃªtre active
liquiditÃ© plus faible
risque fakeout / fin de jambe
```

---

## 3.21 Local contre global

Lecture :

```text
un signal local peut Ãªtre propre mais fragile si le HTF le contredit.
```

InterprÃ©tation :

```text
M1/M5 peuvent montrer une respiration dans une bougie H4,
pas nÃ©cessairement une nouvelle histoire.
```

---

## 3.22 News / toxique

Lecture :

```text
les news crÃ©ent un rÃ©gime spÃ©cial.
La lecture standard est dÃ©formÃ©e.
```

Phases :

```text
prÃ©-news = signaux sÃ©duisants mais fragiles
pendant news = lecture standard suspendue
post-news immÃ©diat = redistribution / faux retour au normal
reconstruction = patterns reprennent du poids progressivement
```

---

## 3.23 Vibration non formalisÃ©e

Lecture :

```text
si la sÃ©quence semble cohÃ©rente visuellement mais pas encore mesurable,
elle va en Lab, pas directement en code.
```

RÃ¨gle :

```text
observer
nommer
documenter
attendre rÃ©pÃ©tition
ensuite seulement formaliser
```

---

# 4. Ã‰QUATIONS CONCEPTUELLES POWERFLOW

## 4.1 Ã‰quations de base

```text
Signal isolÃ© â‰  vÃ©ritÃ©
```

```text
Cross + post-cross behavior = rÃ©ponse
```

```text
Zone + durÃ©e + mÃ©moire = poids
```

```text
Devise + tempo natif = fraÃ®cheur rÃ©elle
```

```text
M1 + sans contexte = bruit possible
```

```text
M1 + M5 + M15 = fractalitÃ© utile
```

```text
HTF + zone + scÃ¨ne = portÃ©e rÃ©elle
```

---

## 4.2 Ã‰quations dâ€™accumulation

```text
ExtrÃªme relatif + durÃ©e = tension de base
```

```text
Tension de base + pullbacks refusÃ©s = accumulation
```

```text
Accumulation + micro-variance = Ã©lastique chargÃ©
```

```text
Ã‰lastique chargÃ© + alignement + libÃ©ration = mouvement potentiel
```

---

## 4.3 Ã‰quations de scÃ¨ne

```text
Relation + Node + Zone vÃ©cue + Temps = ScÃ¨ne
```

```text
Coalition + leader clair + cohÃ©rence = flux propre
```

```text
Opposition + retard + zone = rebalance / rotation
```

```text
Compression + squeeze + HTF alignÃ© = continuation candidate
```

```text
Compression + fin cycle HTF + ancienne victime = reversal candidate
```

---

## 4.4 Ã‰quations de qualitÃ©

```text
Timing tardif + signal rÃ©el = danger
```

```text
Convergence rare + multi-TF + zone = signal renforcÃ©
```

```text
Fakeout + conflit TF = dÃ©gradation
```

```text
Signal + scÃ¨ne confirmÃ©e + zone confirmÃ©e + 2 TF alignÃ©s = SIGNAL_VALIDATED possible
```

---

## 4.5 Ã‰quations de dÃ©cision

```text
PowerFlow voit.
ORION synthÃ©tise.
Le trader filtre.
Le trader dÃ©cide.
```

```text
Alerte â‰  ordre.
Signal â‰  trade.
ScÃ¨ne â‰  certitude.
Film â‰  automatisme.
```

---

# 5. ANNEXE â€” Liste brute des termes PowerFlow

```text
ABSORPTION_BEFORE_RELEASE
ABSORPTION_REPULSION_NODE
ACTIVE_NODE
ACTIVE_ROTATION_RESPONSE
ALIGNEMENT_ANGULAIRE_MULTI_DEVISES
ALIGNEMENT_COMPLET
ALIGNEMENT_PARTIEL
APPROACH
ASYMETRIE_DES_MICRO_MOUVEMENTS
BEHAVIORAL_INDEX
BIRTH_OF_SITUATION
BRUIT_BLANC
CAD_LEADS_USD
CENTER_BATTLE
CENTER_BATTLE_ZONE
CENTER_VALIDATION_CROSS
CHAOS_NO_TRADE
CHARGE
CLEAN_WAVE
COALITION_PUSH
COMPRESSION
COMPRESSION_BREAK
COMPRESSION_BUILD
COMPRESSION_RELEASE
COMPRESSION_SQUEEZE
COMPRESSION_SQUEEZE_CONTINUATION
COMPRESSION_SQUEEZE_REVERSAL
COMPRESSION_DE_TEMPS
CONFLIT_DIRECT
CONFLIT_STRUCTURE
CONVERGENCE
CROSS
CROSS_NODE
CURRENCY_COALITION_NODE
CYCLE_POSITION_AMPLITUDE
DELAY
DENSITE_TEMPORELLE
DESYNC
DESYNCHRONISATION_NAISSANTE
DIRTY_WAVE
DOUBLE_BOTTOM_LOW_ZONE
DOUBLE_TOP_HIGH_ZONE
ELASTIQUE_CASSE
ELASTIQUE_CHARGE
ENTROPIE_LOCALE
EXHAUST_NODE
EXTENSION_DE_TEMPS
EXTREME_BOUND_NODE
EXTREME_BOUND_WINDOW
EXTREME_HIGH
EXTREME_LOW
EXTREME_ZONE_BREATHING
EXTREME_ZONE_MEMORY
FAKE_FOLD
FAKEOUT
FLOW_EXHAUSTION
FLOW_FRAGILE
FLOW_PROPRE
FLOW_ROTATION
FLOW_SALE
FLOW_STRUCTUREL
FOLD
FRACTAL_NODE_BEHAVIOR
GAP_BEHAVIOR
GAP_HOLD_TIME
GAP_SYNC_FAMILY
GRAVITY
HIGH_ZONE_DECELERATION
HIGH_ZONE_DOMINANCE_LOSS
HIGH_ZONE_HOLD
HTF_CANDLE_RESPIRATION
INDEX_COMPORTEMENTAL_BORNE
KISS_REJECT
LATE_NODE
LEADER_FOLLOWER
LOW_ZONE_RELEASE_TO_CENTER
LOW_ZONE_WORK
M1_MICROSTRUCTURE_SUPPORT
M5_TACTICAL_CONFIRMATION_LEG
M15_SCENARIO_NODE
MICRO_VARIANCE
MULTI_NODE_SEQUENCE
MULTI_TF_CURRENCY_COALITION
NODE
NODE_BUILDING_SEQUENCE
NODE_CROSS
NODE_ENERGY
NODE_REPULSION
NO_TOUCH_STRETCH_NODE
OPPOSITION_DIFFEREE
OPPOSITION_DIRECTE
OPPOSITION_REBALANCE
ORCHESTRATED_EQUILIBRIUM
PARALLEL_CANCEL_NODE
PINCH_FOLD_NODE
POSITIVE_DISTANCE_SYNC
POST_CROSS_BEHAVIOR
PRE_EXTREME
PRESSURE
PULLBACK_ECRASE
PULLURE
RECOLLAGE
REFUSED_CROSS
REJECT
RELEASE
REPULSION
RESPIRATION_SAINE
ROTATION_BUILDING
SESSION_ZONE_MEMORY
SEPARATION_ANGLE
SIGNAL_VALIDATED
SLINGSHOT
SUPER_SWITCH
SYNC
TEMPO_NATIF
TEMPORAL_DENSITY
TEMPORAL_EVENT_NODE
TEMPORAL_NODE
TENSION_ACCUMULEE
TENSION_SIGNATURE
THIRD_CURRENCY_ROTATION_CONTEXT
TIME_INFORMATIONNEL
TRIPLE_CROSS_CLUSTER
TRIPLE_NODE
VIBRATION
WATCH_ZONE
ZONE_BATTLE
ZONE_DYNAMIC
ZONE_MEMORY
ZONE_TIME_WEIGHT
```

---

# 6. RÃ¨gle finale du dictionnaire

Le langage PowerFlow doit rester vivant.

```text
Nommer avant de coder.
Observer avant de figer.
Mesurer avant de croire.
Afficher seulement ce qui aide.
DÃ©cider humainement.
```


```

---

# SOURCE: Docs\T006_Source_Staging\LEXIQUE__LEXIQUE_GRAMMAIRE_POWERFLOW_V6_CONSOLIDE_2026-05-04.md

SHA256: 8035BCECF2B3DECE27B6EBB5A6B6ECB217A22D696F814E0095C6BD29DA75F9BA
BYTES: 33107

```text
# LEXIQUE & GRAMMAIRE POWERFLOW V6 â€” CONSOLIDATION

**Date de consolidation :** 2026-05-04  
**Statut :** fichier de rÃ©fÃ©rence consolidÃ© â€” lexique vivant  
**Objet :** regrouper les derniers lexiques, patches de grammaire, ajouts Zone/Cockpit, Sequence Nodes, Battlefield Radar, Coalitions et Agents.

---

## 0. Sources consolidÃ©es

Ce fichier regroupe et dÃ©duplique les contenus issus des documents rÃ©cents suivants :

```text
LEXIQUE_GRAMMAIRE_COMPORTEMENTS_POWERFLOW.md
LEXIQUE_POWERFLOW_ZONE_COCKPIT_UPDATE.md
PATCH_LEXIQUE_DOCTRINE_POWERFLOW_V6_BATTLEFIELD_RADAR_V02.md
DOCTRINE_ADDENDUM_POWERFLOW_V6_COALITIONS_THERMO.md
GRAMMAIRE_LEXIQUE_SEQUENCE_NODES_V01.md
GRAMMAIRE_LEXIQUE_POWERFLOW_V6_UPDATE_2026-05-04.md
CHECKPOINT_SEQUENCE_NODE_READER_V01.md
RAPPORT_SESSION_POWERFLOW_V6_2026-05-04.md
CHECKPOINT_POWERFLOW_V6_2026-05-04.md
```

Ce document ne remplace pas lâ€™observation vivante. Il sert de socle propre pour Ã©viter que le vocabulaire PowerFlow se disperse entre plusieurs sessions.

---

# 1. Doctrine centrale PowerFlow V6

PowerFlow V6 nâ€™est pas une analyse technique classique.

PowerFlow lit :

```text
le flux
la tension
les comportements relatifs
les zones chargÃ©es
les pullbacks absorbÃ©s
les pullures
les coalitions
les antagonistes
les rotations
les nodes temporels
les fenÃªtres potentielles
les scÃ¨nes fractales
```

PowerFlow ne donne pas de BUY/SELL.

PowerFlow produit des Ã©tats :

```text
WATCH
WINDOW_OPENING
WINDOW_YOUNG
WINDOW_ACTIVE
WINDOW_LATE
WINDOW_CLOSED
ARMED
DANGER
DATA_BLIND
```

Phrase noyau :

```text
Les forces prÃ©viennent.
Le prix confirme.
Le HTF donne la gravitÃ©.
Le LTF donne la naissance.
```

Autre phrase centrale :

```text
PowerFlow doit voir le node quand les forces basculent,
pas attendre que le prix ait dÃ©jÃ  racontÃ© lâ€™histoire.
```

RÃ¨gle absolue :

```text
Un Ã©vÃ©nement gÃ©omÃ©trique sans tension prÃ©alable nâ€™est que du bruit.
```

---

# 2. Lexique vivant : principe

Le lexique PowerFlow est vivant.

Il sert Ã  stabiliser le langage aprÃ¨s observation.

RÃ¨gle de travail :

```text
Observer librement.
Nommer.
Documenter.
Comparer.
Attendre rÃ©pÃ©tition.
Formaliser.
Coder seulement ensuite.
```

Mais les briques de lecture brute peuvent Ãªtre codÃ©es avant les lois dÃ©finitives, si elles restent mesurantes et non prÃ©dictives.

---

# 3. Grammaire fractale des timeframes

## WEEKLY_PROFILE

DÃ©cor trÃ¨s large, mÃ©moire des zones et champ de rotation supÃ©rieur.

## DAILY_REBALANCE_PREPARATION

Champ daily oÃ¹ les forces prÃ©parent une redistribution.

## H4_STRUCTURAL_RECOMPOSITION_FIELD

Champ H4 oÃ¹ les grandes forces se recomposent sans forcÃ©ment valider encore une direction exploitable.

## H1_TEMPORAL_EXPANSION_WINDOW

FenÃªtre H1 oÃ¹ le marchÃ© laisse assez dâ€™espace pour quâ€™un scÃ©nario infÃ©rieur puisse se dÃ©velopper.

## M30_TEMPORAL_EXPANSION_GATE

Porte temporelle. Moment oÃ¹ une compression supÃ©rieure peut devenir expansion sur M15/M5.

## M15_BATTLE_SCENE

ScÃ¨ne de bataille. Le M15 montre la construction du scÃ©nario.

## M5_TACTICAL_RELEASE

Le M5 montre la libÃ©ration tactique, la confirmation ou la fabrication de la jambe.

## M1_MICRO_RECHARGE

Le M1 montre la naissance, le microfilm, la couture micro, les petites recharges et les rÃ©ponses rapides.

## FRACTAL_TIME_IMBRICATION

Imbrication des timeframes oÃ¹ chaque Ã©tage temporel porte une fonction.

```text
H4/H1 = gravitÃ© / scÃ¨ne large
M30   = champ de bataille / scÃ¨ne active
M15   = relais / confirmation tactique
M5    = timing tactique
M1    = naissance / microfilm / prÃ©-signal
```

Phrase :

```text
Le HTF donne la scÃ¨ne.
Le LTF donne la fenÃªtre.
```

## HTF_GRAVITY_NODE

Node visible sur H4/H1/M30 qui porte la gravitÃ© de fond.

RÃ´le :

```text
Qualifier le contexte.
Ne pas forcÃ©ment donner le timing dâ€™entrÃ©e.
```

## LTF_PRESIGNAL_BIRTH

PrÃ©-signal ou naissance observable sur M1/M5/M15 avant que le HTF ne devienne Ã©vident.

RÃ´le :

```text
DÃ©tecter la fenÃªtre jeune.
```

## MTF_CONFIRMATION_LATE

Confirmation sur timeframe moyen alors que la naissance LTF a dÃ©jÃ  eu lieu.

Exemple :

```text
M30/H1 confirme une scÃ¨ne,
mais M1/M5 ont dÃ©jÃ  donnÃ© le dÃ©part.
```

## WINDOW_ALREADY_CLOSING

Ã‰tat oÃ¹ la scÃ¨ne HTF reste valide mais oÃ¹ la fenÃªtre tactique LTF est dÃ©jÃ  avancÃ©e ou consommÃ©e.

Phrase cockpit future :

```text
ScÃ¨ne HTF active, mais fenÃªtre LTF probablement tardive.
```

## HTF_NODE_LTF_WINDOW_CLOSED

Cas oÃ¹ le node large est visible sur H4/H1 mais oÃ¹ les prÃ©-signaux M1/M5/M15 sont dÃ©jÃ  passÃ©s.

Lecture :

```text
Ne pas chercher le dÃ©part.
Chercher respiration, second leg ou absorption.
```

---

# 4. Ã‰tats de zone

## NEUTRAL

Ã‰tat neutre.

```text
Aucune tension suffisante.
Aucune zone active clairement nommable.
```

## PRE_EXTREME

Zone dâ€™approche dâ€™un extrÃªme.

```text
La devise approche une zone haute ou basse significative,
mais nâ€™est pas encore dans une charge mature.
```

UtilitÃ© :

```text
prÃ©-zone
prÃ©paration
surveillance
```

## EARLY_EXTREME

ExtrÃªme naissant.

```text
La devise est dÃ©jÃ  dans une zone extrÃªme ou quasi extrÃªme,
mais la zone nâ€™a pas encore assez de maturitÃ© pour Ãªtre ACCUMULATING.
```

Importance :

```text
PowerFlow ne noie plus les extrÃªmes jeunes dans NEUTRAL.
Il voit la naissance du champ.
```

## ACCUMULATING

Zone en accumulation.

```text
La devise reste dans une zone extrÃªme ou prÃ©-extrÃªme
avec une tension qui se construit dans le temps.
```

Lecture :

```text
Ã©nergie stockÃ©e
Ã©lastique chargÃ©
zone travaillÃ©e
```

## LEAKING

Fuite de zone.

```text
La zone commence Ã  perdre son absorption.
La tension nâ€™est pas forcÃ©ment cassÃ©e,
mais lâ€™Ã©nergie commence Ã  fuir.
```

Lecture :

```text
premiÃ¨re perte de contrÃ´le
prÃ©-rupture
dÃ©but de libÃ©ration
```

## RUPTURE

Rupture de zone.

```text
La zone a libÃ©rÃ© ou cassÃ© sa structure prÃ©cÃ©dente.
```

Lecture :

```text
release
cassure comportementale
changement de phase
```

## NORMAL

Zone non extrÃªme.

## EXTREME

Zone extrÃªme dynamique.

## POST_ZONE

AprÃ¨s-zone, souvent liÃ©e Ã  LEAKING ou RUPTURE.

---

# 5. Film de zone

## Zone Event

Diagnostic isolÃ© dans `zone_diagnostics`.

Exemple :

```text
JPY M1 ACCUMULATING EXTREME
```

## Zone Sequence

Suite dâ€™Ã©vÃ©nements sur une mÃªme devise, mÃªme timeframe, mÃªme direction.

Exemple :

```text
PRE_EXTREME â†’ ACCUMULATING â†’ PRE_EXTREME â†’ LEAKING â†’ RUPTURE
```

Lecture :

```text
La zone devient un film.
```

## Zone Evolution Score

Score dâ€™importance dâ€™une sÃ©quence de zone.

Il tient compte de :

```text
contexte
tension
durÃ©e
Ã©tats traversÃ©s
rupture
fuite
```

## FRACTAL_ZONE_STACK

DÃ©tection dâ€™une mÃªme devise travaillÃ©e sur plusieurs timeframes.

CritÃ¨res :

```text
mÃªme devise
mÃªme direction HIGH/LOW
proximitÃ© ou chevauchement temporel
timeframe supÃ©rieur porteur
timeframe infÃ©rieur relais
```

## HTF_ANCHORED_ZONE

Zone portÃ©e par un timeframe supÃ©rieur.

Exemple :

```text
H1 porte
M30 structure
M15 relaie
```

## HTF_ANCHORED_RELEASE_STACK

Stack fractal avec release.

Exemple :

```text
AUD LOW M15/M30/H1
H1 anchor
M30 scenario
M15 trigger
RUPTURE prÃ©sente
```

## SCENARIO_ANCHORED_ZONE

Zone portÃ©e par M30/M15.

Lecture :

```text
scÃ©nario intermÃ©diaire actif
```

## M15_SCENARIO_WITH_M5_RELAY

M15 porte le scÃ©nario, M5 relaie tactiquement.

## SHORT_FRACTAL_RELEASE

Release courte sur M1/M5.

Lecture :

```text
microfilm + release tactique
```

---

# 6. Sessions

## ASIA_SEED

Asia pose ou porte une tension initiale.

## LONDON_OPEN_FORGE

London Open concentre ou travaille la zone.

## LONDON_FORGE

London faÃ§onne le champ de bataille.

## US_RELEASE

US libÃ¨re ou commence Ã  libÃ©rer la tension.

## LATE_US_MICROFILM

Late US montre surtout du microfilm M1/M5.

## SESSION_CARRIED_TENSION

Tension portÃ©e entre plusieurs sessions.

Exemple :

```text
ASIA â†’ LONDON_OPEN
```

## FULL_DAY_CARRY

Champ portÃ© sur une grande partie de la journÃ©e.

## SESSION_RELEASE

Release dÃ©tectÃ©e dans une session.

---

# 7. Termes thermodynamiques

## COMPRESSED

Tension maximale, Ã©nergie concentrÃ©e.

Attention : lâ€™Ã©tat COMPRESSED peut avoir existÃ© avant que le dashboard observe la release.

## ACTIVE

Devise ou champ vivant, mouvement prÃ©sent.

## NEUTRAL

ActivitÃ© moyenne, ni compression forte ni vide.

## HOLLOW

MarchÃ© creux, peu de matiÃ¨re, tendance vide.

## DEAD

Aucune activitÃ© mesurable utile.

## Ã‰LASTIQUE CHARGÃ‰

Une devise reste tendue dans une zone extrÃªme, absorbe les respirations et garde une tension exploitable.

Lecture :

```text
la zone encaisse
la tension reste chargÃ©e
une libÃ©ration potentielle se prÃ©pare
```

## TENSION_SCORE

Score de charge comportementale dâ€™une zone.

Ne doit pas Ãªtre confondu avec une alerte.

## PULLURE

Micro-respiration dans une zone.

Exemples :

```text
Pullure absorbÃ©e   : -2.60 â†’ -2.35 â†’ -2.70
Pullure qui fuit   : -2.70 â†’ -2.40 â†’ -2.20
Pullure de rupture : -2.50 â†’ -2.10 â†’ -1.60
```

## PULLURE_ABSORPTION_FIELD

Pattern oÃ¹ une devise encaisse plusieurs pullures ou pullbacks successifs sans cÃ©der.

## EXTREME_BREATHING_FIELD

Respiration en zone extrÃªme, sans release immÃ©diate.

---

# 8. FenÃªtres temporelles

## TEMPORAL_EXPANSION_WINDOW

FenÃªtre oÃ¹ les timeframes supÃ©rieurs donnent assez dâ€™espace, de respiration ou de conflit non rÃ©solu pour permettre une expansion sur les timeframes infÃ©rieurs.

## HTF_EXPANSION_PERMISSION

Ã‰tat oÃ¹ H1/H4/Daily ne valident pas forcÃ©ment une direction, mais laissent une permission de scÃ©nario aux timeframes infÃ©rieurs.

## TEMPORAL_EXPANSION_GATE

Moment ou zone oÃ¹ un timeframe supÃ©rieur valide quâ€™une compression peut devenir expansion sur les timeframes infÃ©rieurs.

## WINDOW_PREPARING

FenÃªtre en prÃ©paration. Les forces se regroupent, mais la release nâ€™est pas encore claire.

## WINDOW_GATE_OPEN

La porte temporelle est ouverte. La compression peut payer.

## WINDOW_EXPANDING

La fenÃªtre est en expansion active.

## WINDOW_PAID

La fenÃªtre a dÃ©jÃ  payÃ© une grande partie de son Ã©nergie.

## WINDOW_REBALANCING

Phase de rebalancement aprÃ¨s release.

## WINDOW_YOUNG

PrÃ©-signal jeune, opportun pour surveillance tactique.

## WINDOW_ACTIVE

ScÃ¨ne en cours, confirmation ou impact en dÃ©veloppement.

## WINDOW_LATE

Signal dÃ©jÃ  avancÃ©. Le HTF confirme mais le timing LTF est moins propre.

## WINDOW_CLOSED

La fenÃªtre de dÃ©part est consommÃ©e.

## WINDOW_CLOSING

FenÃªtre de temps tactique qui se ferme.

Signatures :

```text
HTF toujours visible
LTF dÃ©jÃ  avancÃ©
prix a dÃ©jÃ  payÃ© une partie importante
```

## WATCH_SECOND_LEG

Ne pas chercher la premiÃ¨re cassure.

Surveiller respiration puis deuxiÃ¨me jambe.

## WATCH_ABSORPTION

Surveiller si la respiration est absorbÃ©e.

---

# 9. Phases de sÃ©quence

## PRE_FIELD

Champ prÃ©paratoire avant la naissance visible dâ€™un node.

Signatures possibles :

```text
bloc haut en extension
bloc bas comprimÃ©
devises pivot/refuge en position anormale
prix calme ou suspendu
```

## NODE_BIRTH

Naissance du node.

Moment oÃ¹ les forces basculent brutalement de faÃ§on collective.

RÃ¨gle clÃ© :

```text
Le node peut naÃ®tre avant que le prix bouge fortement.
```

Signatures :

```text
un bloc monte ensemble
un bloc opposÃ© tombe ensemble
Ã©nergie forte
synchronisation courte
prix encore retenu
```

## CONFIRMATION_PENDING

Phase entre naissance LTF et validation M5/M15.

## CONFIRMATION_LEG

Jambe de confirmation aprÃ¨s la naissance du node.

Signatures :

```text
le mÃªme camp continue sur TF supÃ©rieur
le prix commence Ã  payer
la synchronisation sâ€™Ã©tend de M1 vers M5/M15
```

## CONFIRMED

La structure commence Ã  payer.

Signatures :

```text
M5/M15 suit le node
bid commence Ã  payer
bloc dominant persiste
```

## COUNTER_BREATH

Respiration contraire aprÃ¨s confirmation.

Signatures :

```text
le camp opposÃ© rebondit
le camp dominant relÃ¢che
prix rend peu ou temporairement
```

RÃ¨gle :

```text
Une respiration contraire nâ€™invalide pas la structure.
Il faut voir si elle paie en prix.
```

## ABSORPTION

Moment oÃ¹ une respiration contraire est absorbÃ©e.

Signatures :

```text
le camp dominant reprend
le prix reprend la direction de la structure
la respiration prÃ©cÃ©dente perd son effet
```

## SECOND_LEG

DeuxiÃ¨me jambe aprÃ¨s respiration ou recharge.

## STRUCTURE_PAYING

Moment oÃ¹ le prix commence Ã  raconter ce que les forces ont dÃ©jÃ  montrÃ©.

Phrase Flow :

```text
Le prix paie la structure.
```

Important :

```text
PowerFlow ne doit pas attendre cette phase pour voir la naissance.
```

---

# 10. Nodes et patterns

## RAW_NODE_BIRTH

DÃ©tection brute dâ€™une naissance de node depuis les donnÃ©es `force_snapshots`.

Sans interprÃ©tation complÃ¨te.

## NODE_BIRTH_FAST

Alerte rapide quand les forces basculent collectivement.

PrÃ©conditions :

```text
bloc haut / bloc bas
compression ou extension prÃ©alable
Ã©nergie forte
rotation opposÃ©e
```

Trigger :

```text
UP_BLOCK fort
DOWN_BLOCK fort
PRICE_LAG prÃ©sent
```

Phrase cockpit :

```text
NODE NAISSANT â€” forces basculent, prix encore retenu.
```

## GRAVITY_RESPRING_NODE

Node oÃ¹ les devises de gravitÃ©/pivot ou assimilÃ©es reprennent fortement depuis une position basse ou comprimÃ©e.

Exemple :

```text
USD + CAD respring
```

Extension possible :

```text
JPY rejoint le mouvement comme refuge response.
```

## CAD_JPY_USD_RESPRING_NODE_AGAINST_RISK_BLOCK_FOLD

Pattern observÃ© sur GBPUSD le 2026-05-04.

Structure :

```text
CAD + JPY + USD montent brutalement
EUR + GBP + AUD/CHF se replient
prix encore retenu Ã  la naissance
confirmation M5 ensuite
```

Famille :

```text
GRAVITY_RESPRING_NODE
RISK_BLOCK_FOLD
```

## PRICE_LAG_AT_NODE_BIRTH

DÃ©calage entre lâ€™inversion des forces et le mouvement prix.

RÃ¨gle :

```text
Quand les forces basculent mais que le prix ne bouge pas encore,
PowerFlow doit suspecter une naissance de node.
```

## M5_CONFIRMATION_LEG

Confirmation dâ€™un node M1 par une poursuite cohÃ©rente sur M5.

Signatures :

```text
mÃªme camp dominant
prix commence Ã  payer
bloc opposÃ© continue de se vider
```

## BREATH_ABSORBED

Respiration opposÃ©e qui ne casse pas la structure.

Signatures :

```text
rebond des forces opposÃ©es
rÃ©ponse prix faible
reprise du camp dominant ensuite
```

## POWER_ANGLE_ALERT

Alerte dâ€™angle fort avant ou pendant la cassure prix.

Signatures :

```text
devise dominante accÃ©lÃ¨re
angle de force augmente brutalement
bloc opposÃ© se vide
prix proche dâ€™une cassure ou commence Ã  payer
```

## FORCE_ANGLE_BREAK

Cassure dâ€™angle dans les forces.

DiffÃ©rence avec node :

```text
NODE_BIRTH = basculement de rÃ©gime
FORCE_ANGLE_BREAK = accÃ©lÃ©ration directionnelle lisible
```

## PRICE_IMPACT_LEG

Jambe oÃ¹ le prix paie brutalement la structure.

## POWER_ANGLE_BREAK_TO_PRICE_IMPACT

Pattern visuel observÃ© sur la sÃ©quence 12:45 â†’ 13:45.

Structure :

```text
angle USD/CAD fort
GBP/EUR/AUD drainent
prix casse
respiration ensuite
```

## POST_IMPACT_BREATH

Respiration aprÃ¨s une jambe dâ€™impact.

## POST_IMPACT_FORCE_PERSISTENCE

Les forces dominantes restent orientÃ©es aprÃ¨s lâ€™impact, mÃªme si le prix respire.

Exemple :

```text
CAD/USD restent porteurs
prix stabilise ou rebondit lÃ©gÃ¨rement
```

## PRICE_BREATH_AGAINST_FORCE

Le prix respire contre une structure de force encore active.

---

# 11. Blocs, coalitions et mouvements

## UP_BLOCK

Groupe de devises qui montent ensemble sur une fenÃªtre courte.

Exemple :

```text
CAD + JPY + USD
```

## DOWN_BLOCK

Groupe de devises qui tombent ensemble sur une fenÃªtre courte.

Exemple :

```text
EUR + GBP + CHF
```

## RISK_BLOCK

Bloc composÃ© majoritairement de devises de rÃ´le RISK.

Exemples :

```text
EUR + GBP + AUD
EUR + GBP
AUD + GBP
```

## REFUGE_BLOCK

Bloc composÃ© majoritairement de devises REFUGE.

Exemple :

```text
JPY + CHF
```

## PIVOT_BLOCK

Bloc dominÃ© par des devises pivot ou gravitationnelles.

Exemple :

```text
USD + CAD
```

## MIXED_GRAVITY_BLOCK

Bloc composÃ© de pivot + refuge.

Exemple :

```text
USD + CAD + JPY
```

Lecture :

```text
Ce bloc peut reprendre le champ contre un bloc risk.
```

## RESPRING

RemontÃ©e brusque dâ€™une devise ou dâ€™un bloc depuis une zone basse ou comprimÃ©e.

## FOLD

Pliage / vidange dâ€™une devise ou dâ€™un bloc depuis une zone haute ou intermÃ©diaire.

## SYNC_RESPRING

Plusieurs devises remontent ensemble sur une fenÃªtre courte.

## SYNC_FOLD

Plusieurs devises tombent ensemble sur une fenÃªtre courte.

## OPPOSITE_BLOCK_ROTATION

Rotation simultanÃ©e entre un bloc montant et un bloc descendant.

Phrase :

```text
Un camp reprend le champ pendant que lâ€™autre se vide.
```

## COALITION

Famille temporaire de devises avanÃ§ant avec cohÃ©rence commune.

Une coalition apparaÃ®t quand plusieurs devises :

```text
ont une tension comparable
partagent une polaritÃ©
prennent une direction proche
respirent ensemble dans le temps
```

Phrase :

```text
Une coalition nâ€™est pas une prÃ©diction.
Câ€™est une famille de forces qui respire ensemble.
```

## RELATION_ACTIVE

ScÃ¨ne oÃ¹ une coalition rencontre un antagoniste clair.

Formule :

```text
devise isolÃ©e
â†’ anomalie relative
â†’ respiration de zone
â†’ coalition temporaire
â†’ antagoniste
â†’ relation active
â†’ future fenÃªtre temporelle
```

## ANTAGONISTE

Devise ou coalition qui travaille en face.

Lecture :

```text
opposition de champ
force contraire
camp adverse
```

## HIGH_COALITION

Ensemble de devises travaillant cÃ´tÃ© HIGH dans la mÃªme fenÃªtre.

## LOW_COALITION

Ensemble de devises travaillant cÃ´tÃ© LOW dans la mÃªme fenÃªtre.

---

# 12. Prix / force

## PRICE_LAG

Le prix ne suit pas immÃ©diatement le basculement des forces.

Lecture :

```text
Le champ se prÃ©pare.
Le prix nâ€™a pas encore racontÃ© lâ€™histoire.
```

## WEAK_PRICE_RESPONSE

Les forces bougent fortement, mais le prix rÃ©pond peu.

InterprÃ©tations possibles :

```text
absorption
contre-force
liquiditÃ©
structure plus large qui retient
```

## PRICE_PAYS_STRUCTURE

Le prix finit par suivre le node dÃ©tectÃ© dans les forces.

Exemple :

```text
Node M1 09:23â€“09:27
prix paie sur M5 09:35â€“09:45
```

## PRICE_PAYING

Le prix commence Ã  suivre la structure.

## PIP_VELOCITY

Vitesse du prix en pips par minute.

## PIP_RANGE

Amplitude en pips sur la fenÃªtre ou la bougie.

## PIP_BODY

Corps de bougie exprimÃ© en pips.

## PIP_CHANGE

Variation nette du prix sur une fenÃªtre.

---

# 13. Mesures cinÃ©matiques

## FORCE_VELOCITY

Variation de force par minute.

```text
force_velocity_per_min = force_delta / minutes
```

## FORCE_ANGLE_DEG

Angle gÃ©omÃ©trique approximatif de la force.

```text
angle = atan(force_velocity_per_min)
```

Ce nâ€™est pas un angle pixel du graphique. Câ€™est un proxy mathÃ©matique.

## FORCE_ACCELERATION

Variation de vitesse entre deux segments.

```text
acceleration = velocity_current - velocity_previous
```

## FORCE_ENERGY

Ã‰nergie brute dâ€™une fenÃªtre, souvent approximÃ©e par la somme des variations absolues des devises.

```text
energy = Î£ abs(force_delta)
```

UtilitÃ© :

```text
RepÃ©rer les fenÃªtres oÃ¹ quelque chose se passe vraiment.
```

## THERMAL_NET_ENERGY

Ã‰nergie nette.

Formule conceptuelle :

```text
thermal_net_energy = Ã©nergie brute - dissipation - friction
```

## DISSIPATION

Ã‰nergie qui se vide sans libÃ©ration exploitable.

## FRICTION

RÃ©sistance ou bloqueur de libÃ©ration.

## ENTROPY / DISORDER_FIELD

Champ actif mais dÃ©sordonnÃ©, non structurÃ©.

RÃ¨gle :

```text
Nommer, ne pas forcer en signal.
```

---

# 14. Battlefield Radar

## BATTLEFIELD_RADAR

Brique qui agrÃ¨ge coalitions et relations actives pour repÃ©rer les scÃ¨nes dâ€™intÃ©rÃªt stratÃ©gique.

Phrase noyau :

```text
BattlefieldRadar ne dit pas â€œla fenÃªtre est ouverteâ€.
Il dit â€œici, une bataille se prÃ©pareâ€.
```

Place dans la grammaire :

```text
acteur individuel
â†’ respiration de zone
â†’ coalition
â†’ relation coalition vs antagoniste
â†’ scÃ¨ne dâ€™intÃ©rÃªt radar
â†’ densitÃ© temporelle future
â†’ fenÃªtre active future
```

## SCÃˆNE Dâ€™INTÃ‰RÃŠT STRATÃ‰GIQUE

Zone temporelle oÃ¹ PowerFlow aperÃ§oit une structure collective utile pour le cockpit.

Elle peut Ãªtre :

```text
relation active
coalition forte
champ en prÃ©paration
```

Mais elle nâ€™est pas encore :

```text
TemporalWindowActive
```

## BATAILLE_EN_PRÃ‰PARATION

Une coalition rencontre ou commence Ã  rencontrer un antagoniste.

Exemple :

```text
AUD+CAD vs JPY
LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING
```

Lecture :

```text
un bloc bas rÃ©pond contre un antagoniste haut
```

## RELATION_ACTIVE_PRIORITAIRE

Doctrine V0.2 :

```text
Relation active moyenne > coalition isolÃ©e forte
```

Raison :

```text
relation active = coalition + antagoniste + opposition de champ
coalition forte = famille synchronisÃ©e mais bataille incomplÃ¨te
```

## COALITION_FORTE_Ã€_SURVEILLER

Famille synchronisÃ©e qui mÃ©rite attention cockpit, mais dont lâ€™antagoniste est absent ou pas assez propre.

## Ã‰tats BattlefieldRadar

```text
BATTLE_WATCH
BATTLE_PREPARING
BATTLE_FORMING
BATTLE_PRESSURIZED
COALITION_FIELD_WATCH
COALITION_FIELD_VISIBLE
COALITION_FIELD_STRONG
```

## Types de scÃ¨nes

```text
RELATION_ACTIVE
COALITION_STRONG
```

## STRATEGIC_SCORE

Score de tri cockpit propre au radar.

Il ne remplace pas :

```text
field_score
cohesion
context_score
```

Il sert Ã  classer les scÃ¨nes dans le cockpit.

RÃ¨gle :

```text
relations actives dâ€™abord
coalitions fortes ensuite
```

---

# 15. Battlefield Map et Cockpit Field

## BATTLEFIELD_MAP

Carte globale des zones Cockpit.

Elle rÃ©pond :

```text
qui pousse haut ?
qui travaille bas ?
qui libÃ¨re ?
qui prÃ©pare ?
qui est bipolaire ?
oÃ¹ est la fenÃªtre contestÃ©e ?
```

## TACTICAL_RELEASE_BATTLEFIELD

Champ de release tactique.

Exemple :

```text
CAD HIGH / GBP HIGH release M1/M5
```

## HTF_PREPARATION_FIELD

Champ de prÃ©paration portÃ© par des timeframes supÃ©rieurs.

Exemple :

```text
EUR LOW M15/M30
GBP LOW M15/M30/H1
CAD LOW M30/H1
```

## GLOBAL_RELEASE_BATTLEFIELD

Ancien comportement V0.1 qui mÃ©langeait trop HIGH et LOW.

Ã€ utiliser avec prudence.

PrÃ©fÃ©rer :

```text
cluster-mode side
```

## CONTESTED_WINDOW

FenÃªtre oÃ¹ une coalition HIGH et une coalition LOW coexistent.

## CONTESTED_RELEASE_WINDOW

FenÃªtre contestÃ©e avec release dâ€™un cÃ´tÃ©.

## BIPOLAR_CONTESTED_RELEASE_WINDOW

FenÃªtre contestÃ©e oÃ¹ au moins une devise existe en HIGH et LOW.

## BIPOLAR_CURRENCY_FIELD

Une mÃªme devise apparaÃ®t des deux cÃ´tÃ©s du champ.

DÃ©finition :

```text
la devise a une bataille HIGH
et une bataille LOW
dans la mÃªme fenÃªtre temporelle
```

Ce nâ€™est pas une erreur. Câ€™est une contestation interne.

## INTERNAL_ROTATION_CONTEST

Conflit interne pouvant prÃ©parer une rotation.

## MICRO_VS_HTF_ROTATION_CONTEST

Microfilm contre scÃ©nario/HTF.

Exemple :

```text
EUR HIGH prep M1/M5
vs
EUR LOW prep M15/M30
```

Lecture :

```text
micro haut contre scÃ¨ne basse
rotation interne potentielle
```

## HIGH_RELEASE_VS_LOW_HTF_PREP

Release haute court terme contre prÃ©paration basse HTF.

## LOW_RELEASE_VS_HIGH_HTF_PREP

Release basse court terme contre prÃ©paration haute HTF.

## DOUBLE_SIDE_RELEASE_CONTEST

La devise libÃ¨re des deux cÃ´tÃ©s.

Cas rare, probablement chaotique ou transitionnel.

## COCKPIT_FIELD

Vue finale ultra-courte.

Elle affiche :

```text
FIELD
DOMINANT
OPPOSITE / CONTEXT
CONTESTED_WINDOW
BIPOLAR_FOCUS
BIPOLAR_LIST
```

## FIELD

Champ dominant actuel.

Exemple :

```text
TACTICAL_RELEASE_BATTLEFIELD | session=LATE_US
```

## DOMINANT

Camp dominant ou actif.

## OPPOSITE / CONTEXT

Camp opposÃ© ou contexte supÃ©rieur.

## BIPOLAR_FOCUS

Devise bipolaire principale.

## BIPOLAR_LIST

RÃ©sumÃ© compact des devises bipolaires.

Exemple :

```text
EUR:PREPH/PREPL
GBP:RELH/PREPL
CAD:RELH/PREPL
CHF:PREPH/PREPL
```

Signification :

```text
PREPH = prÃ©paration HIGH
PREPL = prÃ©paration LOW
RELH  = release HIGH
RELL  = release LOW
```

---

# 16. Agents PowerFlow

## DB_FRESHNESS_AGENT / DBVisionGuard

Mission :

```text
vÃ©rifier que la DB voit vraiment
contrÃ´ler lignes rÃ©centes par timeframe
vÃ©rifier colonnes EA
dÃ©tecter trous temporels
dÃ©tecter DATA_BLIND
```

ContrÃ´les prioritaires :

```text
M1/M5/M15/M30/H1/H4 prÃ©sents
derniÃ¨re ligne par TF
trous temporels
colonnes EA Extended
NZD
OHLC
volume
pips
spread
is_closed_bar
```

## SEQUENCE_READER

Agent qui lit la DB et extrait les Ã©vÃ©nements bruts.

Mission :

```text
mesurer
extraire
classer froidement
ne pas interprÃ©ter trop loin
```

EntrÃ©es :

```text
force_snapshots
symbol
timeframes
start/end
```

Sorties :

```text
windows
up_block
down_block
energy
bid_delta
raw_event
phase
```

## FLOW_EVENT_EXTRACTOR

Nom recommandÃ© pour fusionner SequenceReader + features cinÃ©matiques.

Mission :

```text
lire les snapshots
calculer deltas + blocs + Ã©nergie + vitesse + angle
sortir des Ã©vÃ©nements bruts ordonnÃ©s
```

Sorties :

```text
PRE_FIELD
NODE_BIRTH
CONFIRMATION
COUNTER_BREATH
ABSORPTION
SECOND_LEG
WINDOW_CLOSING
```

## FORCE_KINEMATICS_AGENT

Mission :

```text
mesurer vitesse
angle
accÃ©lÃ©ration
pips/min
force energy
price lag
```

Statut recommandÃ© :

```text
module mathÃ©matique interne plutÃ´t quâ€™agent autonome au dÃ©but
```

## FRACTAL_ORCHESTRATOR / FractalWindowEngine

Mission :

```text
relier HTF et LTF
dire si la fenÃªtre est jeune, active, tardive ou fermÃ©e
```

Questions clÃ©s :

```text
Le prÃ©-signal LTF est-il portÃ© par une gravitÃ© HTF ?
Le HTF est-il dÃ©jÃ  Ã©vident mais LTF tardif ?
Chercher dÃ©part, respiration, second leg ou absorption ?
```

## NODE_INTERPRETER / SceneNamer

Mission :

```text
nommer la scÃ¨ne
classer le comportement
transformer les events en langage Flow
```

RÃ¨gle :

```text
Il nomme.
Il ne recalcule pas.
```

## COCKPIT_TRANSLATOR

Mission future :

```text
condense les sorties agents en 3 lignes utiles
ne calcule pas
ne dÃ©cide pas
```

## COCKPIT_STATE_EMITTER

Brique recommandÃ©e avant interface.

Mission :

```text
Ã©crire un cockpit_state_v2.json stable
```

## LAB_MEMORY_AGENT

Mission :

```text
sauver observation trader
crÃ©er fiche Lab
capturer vocabulaire nouveau
prÃ©parer hypothÃ¨se testable
```

## LAB_TRANSLATOR

Agent qui transforme une observation trader ou sÃ©quence DB en fiche Lab.

Mission :

```text
sauver la mÃ©moire
nommer les comportements
prÃ©parer validation future
```

## MISSION_BUILDER_AGENT

Mission :

```text
transformer un Lab en mission codable
dÃ©finir fichier cible, objectif, contraintes, tests
rÃ©duire les patchs confus
```

Format attendu :

```text
MISSION
FICHIER CIBLE
OBJECTIF
CONTRAINTES
INPUTS
OUTPUTS
TESTS
ROLLBACK
```

---

# 17. Alertes proposÃ©es

## NODE_BIRTH_FAST

Alerte rapide quand les forces basculent collectivement.

Phrase cockpit :

```text
NODE NAISSANT â€” forces basculent, prix encore retenu.
```

## NODE_CONFIRMATION_M5

Alerte quand le node M1 est confirmÃ© par M5.

PrÃ©conditions :

```text
node birth M1 dÃ©tectÃ©
mÃªme camp dominant sur M5
bid commence Ã  payer
```

Phrase cockpit :

```text
NODE CONFIRMÃ‰ M5 â€” structure commence Ã  payer.
```

## COUNTER_BREATH_ALERT

Alerte respiration contraire.

PrÃ©conditions :

```text
aprÃ¨s confirmation
bloc opposÃ© rebondit
camp dominant relÃ¢che
```

Phrase cockpit :

```text
RESPIRATION CONTRAIRE â€” surveiller absorption ou invalidation.
```

## BREATH_ABSORBED_ALERT

Alerte quand la respiration contraire est absorbÃ©e.

PrÃ©conditions :

```text
counter breath dÃ©tectÃ©
prix ne paie pas beaucoup contre la structure
camp dominant reprend
```

Phrase cockpit :

```text
RESPIRATION ABSORBÃ‰E â€” structure reprend.
```

---

# 18. Patterns Lab enregistrÃ©s

## LAB_004_USD_CAD_JPY_RESPRING_AGAINST_RISK_BLOCK_FOLD

SÃ©quence :

```text
GBPUSD
2026-05-04
09:00 â†’ 10:15
```

DÃ©coupage :

```text
PRE_FIELD        09:00 â†’ 09:20
NODE_BIRTH       09:23 â†’ 09:27
CONFIRMATION     09:30 â†’ 09:45
COUNTER_BREATH   09:49 â†’ 09:54
ABSORPTION       10:00 â†’ 10:15
```

Structure :

```text
CAD+JPY+USD respring
EUR+GBP+CHF/AUD fold
prix encore retenu
confirmation M5 ensuite
```

Pattern compact :

```text
GRAVITY_RESPRING_NODE
```

## LAB_005_USD_CAD_ANGLE_BREAK_WITH_GBP_EUR_DRAIN

SÃ©quence :

```text
GBPUSD
2026-05-04
12:45 â†’ 13:45 visuel
```

Ã‰tat :

```text
DB fine absente sur M1/M5/M15
M30 confirme seulement lâ€™impact large
```

Pattern :

```text
POWER_ANGLE_BREAK_TO_PRICE_IMPACT
```

Structure :

```text
angle USD/CAD fort
GBP/EUR/AUD drainent
prix casse
respiration ensuite
```

---

# 19. DB et donnÃ©es attendues

La DB actuelle sait exploiter :

```text
created_at
symbol
timeframe
bid
spread
force_gbp
force_usd
force_eur
force_jpy
force_cad
force_chf
force_aud
```

La DB Extended doit ajouter :

```text
force_nzd
open
high
low
close
tick_volume
pip_range
pip_body
pip_change
spread_points
spread_price
spread_pips
ask
mid
bar_time
bar_close_time
server_time
capture_time
is_closed_bar
```

Nouvelles classes futures possibles :

```text
NODE_BIRTH_FORCE_ONLY
NODE_BIRTH_WITH_PRICE_LAG
NODE_BIRTH_WITH_CANDLE_BODY
NODE_BIRTH_WITH_VOLUME
NODE_BIRTH_WITH_SPREAD_FRICTION
NODE_CONFIRMED_BY_CLOSED_BAR
```

RÃ¨gle :

```text
Si M1/M5/M15 manquent, PowerFlow est aveugle tactiquement.
Si H1/H4 manquent, PowerFlow manque la gravitÃ©.
```

---

# 20. RÃ¨gles de non-confusion

```text
Z-score â‰  signal
Zone state â‰  alerte
ScÃ¨ne dâ€™intÃ©rÃªt â‰  signal
Coalition forte â‰  bataille complÃ¨te
Relation active â‰  fenÃªtre ouverte
BattlefieldRadar â‰  TemporalDensity
BattlefieldRadar â‰  TemporalWindowActive
TemporalDensity â‰  TemporalWindowActive
Cockpit Field â‰  Telegram
M1 â‰  dÃ©cision seule
Node â‰  simple croisement
Cross gÃ©omÃ©trique sans tension â‰  signal
Respiration contraire â‰  nouveau node principal
HTF confirmation tardive â‰  naissance LTF
```

---

# 21. RÃ¨gles de lecture

## RÃ¨gle 1

```text
Un timeframe supÃ©rieur ne donne pas toujours la direction.
Parfois il donne lâ€™espace.
```

## RÃ¨gle 2

```text
La compression nâ€™est pas toujours le moment visible.
La release peut Ãªtre visible aprÃ¨s coup.
```

## RÃ¨gle 3

```text
M30 ouvre la porte.
M15 porte la scÃ¨ne.
M5 montre la release.
M1 montre la recharge.
```

## RÃ¨gle 4

```text
Une devise peut ne pas Ãªtre dominante HTF,
mais avoir une permission dâ€™expansion.
```

## RÃ¨gle 5

```text
La densitÃ© locale ne suffit pas.
Il faut la mÃ©moire de compression.
```

## RÃ¨gle 6

```text
Le node principal doit Ãªtre lu dans son ordre temporel.
```

## RÃ¨gle 7

```text
Si HTF confirme mais LTF est dÃ©jÃ  passÃ© :
chercher second leg / absorption, pas naissance.
```

## RÃ¨gle 8

```text
La DB Freshness est une condition avant toute analyse automatique.
```

---

# 22. Formules cockpit futures

```text
LTF PRE-SIGNAL â€” microfilm M1/M5 sâ€™aligne sous gravitÃ© HTF.
```

```text
HTF NODE DETECTED â€” fenÃªtre LTF probablement avancÃ©e.
```

```text
POWER ANGLE ALERT â€” USD/CAD accÃ©lÃ¨rent, GBP/EUR/AUD drainent.
```

```text
PRICE IMPACT CONFIRMED â€” M5 paie la cassure.
```

```text
POST IMPACT BREATH â€” prix respire, forces dominantes encore actives.
```

```text
WINDOW CLOSING â€” ne pas chercher dÃ©part, surveiller absorption/second leg.
```

```text
NODE NAISSANT â€” forces basculent, prix encore retenu.
```

```text
RESPIRATION ABSORBÃ‰E â€” structure reprend.
```

---

# 23. ChaÃ®ne agentique recommandÃ©e

Circuit chaud :

```text
capture_bridge.py / EA Extended
        â†“
powerflow.db
        â†“
DBVisionGuard
        â†“
FlowEventExtractor
        â†“
FractalWindowEngine
        â†“
SceneNamer
        â†“
cockpit_state_v2.json
        â†“
Cockpit / Telegram / Dashboard plus tard
```

Circuit froid :

```text
screens + ressenti trader
        â†“
LabMemory
        â†“
MissionBuilder
        â†“
TestRunner
        â†“
Checkpoint
```

PrioritÃ©s recommandÃ©es :

```text
P0 â€” DBVisionGuard
P1 â€” FlowEventExtractor
P2 â€” FractalWindowEngine
P3 â€” SceneNamer
P4 â€” cockpit_state_v2.json spec
P5 â€” LabMemory
P6 â€” MissionBuilder
P7 â€” Cockpit UI plus tard
```

---

# 24. Verdict doctrinal final

```text
Un node nâ€™est pas un signal isolÃ©.
Câ€™est une fenÃªtre oÃ¹ les forces changent de rÃ©gime.
```

```text
Le prix confirme.
Les forces prÃ©viennent.
```

```text
PowerFlow doit lire le basculement du champ,
puis seulement ensuite vÃ©rifier si le prix paie.
```

```text
Le trader ne doit pas lire sept devises.
PowerFlow doit compresser le champ en une phrase utile.
```

```text
La DB ouvre les yeux.
Lâ€™extracteur lit le choc.
Le fractal situe la fenÃªtre.
Le namer donne le mot juste.
Le cockpit affiche seulement lâ€™essentiel.
```

---

# 25. Ã€ faire aprÃ¨s intÃ©gration de ce lexique

```text
1. DÃ©poser ce fichier dans Docs.
2. Le dÃ©clarer comme lexique consolidÃ© officiel.
3. Archiver les anciens patches lexique comme sources historiques.
4. CrÃ©er la spec DBVisionGuard.
5. CrÃ©er la spec FlowEventExtractor V0.1.
6. Ne pas lancer le cockpit final avant cockpit_state_v2.json.
```

Fin du fichier consolidÃ©.

```

---

# SOURCE: Docs\T006_Source_Staging\PACKET_REQUALIFICATION__POWERFLOW_BRICK_TO_PACKET_FIELD_MAPPING_V76.md

SHA256: 9788FC333A4584D17F3FAE4454A6A877676B4685947DB740B029DD270FA4F131
BYTES: 6349

```text
# POWERFLOW BRICK TO PACKET FIELD MAPPING V7.6

## 0. Principe

Chaque brique supporte un ou plusieurs champs du `terrain_packet`. Aucune brique ne dÃ©cide seule du film complet. Les champs critiques doivent Ãªtre arbitrÃ©s par prix, zone, propagation, texture et data visibility.

```text
BRICK SUPPORTS FIELD.
BRICK DOES NOT DECIDE FINAL SEMANTICS ALONE.
```

## 1. Mapping global

| BRICK | SUPPORTS FIELD | DOES NOT DECIDE | REQUIRED CROSSCHECK | FAILURE MODE |
|---|---|---|---|---|
| B2 event stack | `event_stack_state`, `event_density`, `birth_attempt` | `release_validation`, `qualified_bias` | B3, price, zone, B7, data_visibility | `B3_B2_FALSE_BIRTH` |
| B3 detachment / birth attempt | `detachment_state`, `raw_bias`, support `current_move_role` | `RELEASE_VALIDATED`, structural direction | B7+, price confirmation, current_zone, last_structural_event | Directionnel sans prix |
| B4 compression | `compression_state`, `temporal_density`, `pressure_pending` | Release, outcome, trade direction | P1, B3, price, propagation | Compression prise pour cassure |
| P1 energy / elastic load | `energy_state`, `elastic_load`, `freshness_state` | Release validation | B4, B3, price, zone, freshness | Charge late/consumed prise pour fresh |
| B3+B4+P1 | `release_candidate_state`, `packet_quality` | `RELEASE_VALIDATED` | price accepted, zone coherent, B7 relay, data acceptable | Candidate rejetÃ© par prix |
| B5 relational gravity | `relational_context`, `leader_follower_state` | Driver final, outcome | B8, coverage, price, B7 | Fausse certitude relationnelle |
| B8 cross-symbol validation | `cross_validation_state`, `driver_context` | Vraie force GBP/USD si coverage faible | coverage map, symbol freshness, B5 | `B8_DEGRADED` |
| B6 film memory | `memory_match`, `known_false_positive`, `next_expected_behavior`, `invalidation_reference` | Prediction, outcome certain | current film, price arbiter, guards | Ã‰vÃ©nement isolÃ© confondu avec film |
| B7 propagation | `propagation_state`, `relay_quality` | Trade, release alone, qualified_bias alone | B3, price, zone, B7+, data | `LTF_ONLY` pris pour structure |
| B7+ detachment texture | `detachment_texture`, support `current_move_role` | Direction finale | price, last_structural_event, B7, B6 | Texture floue / UNKNOWN masquÃ© |
| Guards data/session/entropy | `data_visibility`, `session_context`, `entropy_state`, `packet_quality` | Market role unless degraded constraints | all fields, timestamps, source freshness | Stale packet pris pour live |
| Time Profiles LTF/MTF/HTF | `time_profile_state`, support `propagation_state` | Release validation | B7, B3, price | LTF fort sans MTF pris pour validÃ© |
| Evidence Bus | `evidence_refs` | Any semantic role | field_supported required | Evidence spam |
| Perception Spine actuelle | `spine_summary` | Override terrain_packet | terrain_packet | Spine contredit packet |
| Trader Packet | `terrain_packet` | Trade decision | all source fields | Packet trop brut |
| Alert Gate | `alert_gate_state`, `dedupe_state` | Semantic invention | terrain_packet | Gate renomme le signal |
| Dashboard | `dashboard_surface` | Business logic | terrain_packet readonly | Dashboard dÃ©cide |
| Telegram | `telegram_packet` if enabled later | Activation V7.6 | QA pass + feature flag | Transmission prÃ©maturÃ©e |

## 2. Champs terrain_packet et briques support

| FIELD | PRIMARY SUPPORT | SECONDARY SUPPORT | HARD BLOCKERS |
|---|---|---|---|
| `film_state` | B6, terrain grammar | price, zone | `READING_PARTIAL` must be shown |
| `last_structural_event` | B6, price history | B7, B7+ | missing history => `UNKNOWN` |
| `current_zone` | price/zone context | B4, P1 | stale price => `UNKNOWN` |
| `current_move_role` | B7+, B6, price | B3, B7 | B3 alone cannot decide |
| `raw_bias` | B3, packet raw | B2 | raw only, no final meaning |
| `qualified_bias` | packet requalification | B6, B7+, price, zone | no price arbiter => not validated |
| `packet_quality` | Guards, price, B7 | Evidence Bus | degraded data must downgrade |
| `price_confirmation` | price arbiter | zone, B6 | missing price => `PENDING` or `UNKNOWN` |
| `propagation_state` | B7 | Time Profiles | no MTF => `LTF_ONLY` or `UNKNOWN` |
| `detachment_texture` | B7+ | B3, B6 | texture unknown must be explicit |
| `data_visibility` | Guards | timestamps, source freshness | degraded must display first |
| `watch_condition` | terrain grammar | B6, price | cannot be empty if packet is WATCH |
| `invalidation_condition` | terrain grammar, B6 | price | cannot be vague for high-priority packet |
| `memory_match` | B6 | film library | no match => `NO_FILM_MATCH` |
| `evidence_refs` | Evidence Bus | all bricks | no orphan evidence |

## 3. Non-dÃ©cision par brique

### B3

B3 supports `current_move_role` but does not decide release validation.

### B7

B7 supports `propagation_state` but does not decide trade or outcome.

### B6

B6 supports `memory_match` but does not decide outcome.

### Guards

Guards support `data_visibility` and must be displayed first if degraded.

### Dashboard

Dashboard displays `terrain_packet`. It does not modify `qualified_bias`, `price_confirmation`, `packet_quality`, or `current_move_role`.

## 4. Required crosscheck rules

```text
RELEASE_VALIDATED requires:
- release_candidate_state = RELEASE_CANDIDATE
- price_confirmation = ACCEPTED
- current_zone coherent with direction
- propagation_state in [LTF_MTF_RELAY, MTF_HTF_RELAY]
- data_visibility not in [READING_PARTIAL, MICROFILM_MISSING, M1_MISSING, PACKETS_STALE]
```

```text
COUNTER_BREATH requires:
- last_structural_event opposite or lower/higher lock context
- B7+ texture = COUNTER_BREATH_DETACHMENT or POST_RELEASE_DETACHMENT
- price_confirmation pending or rejected until acceptance proves reintegration
```

```text
HONEST_UNKNOWN requires:
- B5/B8 coverage insufficient
- stale or missing cross-symbol data
- relational conflict unresolved
```

## 5. Failure mode vocabulary

```text
B3_B2_FALSE_BIRTH
DIRECTIONAL_WITHOUT_PRICE
HOT_WITHOUT_PRICE_MOVE
RELEASE_CANDIDATE_PRICE_REJECTED
B8_DEGRADED
B5_B8_HONEST_UNKNOWN
LTF_ONLY_MISREAD_AS_STRUCTURE
STALE_PACKET_MISREAD_AS_LIVE
EVENT_TIME_OFFSET
EVIDENCE_SPAM
DASHBOARD_LOGIC_LEAK
TELEGRAM_PREMATURE
```

```

---

# SOURCE: Docs\T006_Source_Staging\PACKET_REQUALIFICATION__POWERFLOW_PACKET_REQUALIFICATION_RULES_V76_FINAL.md

SHA256: 23D419A222F49BDAD12A66892C68479C091F8B883DB69DC0E17648ADE11C4776
BYTES: 15776

```text
# POWERFLOW PACKET REQUALIFICATION RULES V7.6 FINAL

## 0. Doctrine

`raw_bias` = ce que les briques ont vu.

`qualified_bias` = ce que cela signifie dans le film.

PowerFlow ne dÃ©cide pas le trade. PowerFlow ne produit pas d'ordre, ne crÃ©e pas de buy/sell, ne fabrique pas de stratÃ©gie et ne transforme pas une lecture terrain en instruction d'action.

Contrat V7.6 :

```text
La machine perÃ§oit, mesure, nomme et alerte.
Le trader filtre, arbitre et agit.
```

Le `raw_bias` doit Ãªtre conservÃ© dans chaque packet pour auditabilitÃ©, mais il ne doit jamais Ãªtre affichÃ© seul comme vÃ©ritÃ© principale. L'affichage principal doit exposer le film, la zone, le rÃ´le courant, la confirmation prix et la visibilitÃ© data.

---

## 1. Ordre strict des rÃ¨gles

La requalification V7.6 doit appliquer les rÃ¨gles dans cet ordre exact :

1. VÃ©rifier `data_visibility`.
2. VÃ©rifier prix / invalidation / stale.
3. Identifier `last_structural_event`.
4. Identifier `current_zone`.
5. Lire `raw_bias`.
6. Appliquer rÃ¨gles de contexte film.
7. Appliquer propagation B7.
8. Appliquer texture B7+.
9. Appliquer mÃ©moire B6.
10. Produire `qualified_bias` + `packet_quality` + `watch_condition` + `invalidation_condition`.

Raison : le packet brut ne suffit pas. Il doit Ãªtre requalifiÃ© par film + zone + prix + propagation + texture + mÃ©moire + guards.

---

## 2. RÃ¨gles data_visibility

### Ã‰tats officiels

| Ã‰tat | Sens | Effet V7.6 |
|---|---|---|
| `FULL_READING` | Microfilm, packets, prix, propagation, cross-validation disponibles | Lecture complÃ¨te autorisÃ©e. |
| `READING_PARTIAL` | Lecture utilisable mais incomplÃ¨te | Doit apparaÃ®tre en haut ; peut limiter `packet_quality`. |
| `MICROFILM_MISSING` | M1 / microfilm absent | EmpÃªche validation dure d'une release micro. |
| `M1_MISSING` | DonnÃ©es M1 absentes ou inutilisables | Force visibilitÃ© dÃ©gradÃ©e. |
| `PACKETS_STALE` | Packets trop vieux pour valider le live | Force visibilitÃ© dÃ©gradÃ©e ; empÃªche release validÃ©e seule. |
| `CROSS_VALIDATION_DEGRADED` | B5/B8 incomplet ou faible couverture | La confirmation relationnelle devient soft. |
| `B8_DEGRADED` | B8 faible, partiel ou non reprÃ©sentatif | Ne doit pas confirmer dur ; expose risque technique. |
| `B5_B8_HONEST_UNKNOWN` | B5/B8 ne sait pas honnÃªtement | Requalifier en `HONEST_UNKNOWN` si aucune preuve plus forte. |
| `TEMPORAL_GAPS` | Trous temporels dans la sÃ©quence | EmpÃªche lecture continue du film. |
| `EVENT_TIME_OFFSET` | DÃ©calage entre event_at et market_time | Exposer risque de lecture dÃ©calÃ©e. |
| `UNKNOWN` | VisibilitÃ© non fournie | Fallback prudent cÃ´tÃ© technique, jamais vÃ©ritÃ© complÃ¨te. |

### RÃ¨gle dure

Si la data est dÃ©gradÃ©e, elle doit apparaÃ®tre en haut du packet et peut limiter `packet_quality`.

RÃ¨gles d'application :

```text
M1 absent                -> data_visibility=M1_MISSING ou READING_PARTIAL
M1 absent + stale        -> data_visibility=M1_MISSING_PACKETS_STALE
packets stale            -> data_visibility=PACKETS_STALE ou READING_PARTIAL
B8 faible                -> technical_risks += B8_DEGRADED
B5/B8 faible sans prix   -> qualified_bias=HONEST_UNKNOWN possible
event_at offset          -> data_visibility=EVENT_TIME_OFFSET ou technical_risks += EVENT_TIME_OFFSET
```

La visibilitÃ© n'annule pas nÃ©cessairement le packet. Elle le qualifie. Une lecture partielle peut rester utile si elle dit clairement ce qu'elle ne voit pas.

---

## 3. RÃ¨gles prix

### Ã‰tats officiels

| Ã‰tat | Sens |
|---|---|
| `PRICE_CONFIRMED` | Prix confirme le rÃ´le du packet. |
| `PRICE_PENDING` | Le prix n'a pas encore tranchÃ©. |
| `PRICE_FAILED` | Le prix Ã©choue Ã  confirmer le packet. |
| `PRICE_INVALIDATED` | Le prix contredit explicitement la lecture. |
| `PRICE_ACCEPTED_ABOVE_ZONE` | Acceptation au-dessus de la zone active. |
| `PRICE_ACCEPTED_BELOW_ZONE` | Acceptation sous la zone active. |
| `PRICE_REJECTED_HIGH` | Rejet de zone haute / high rejetÃ©. |
| `PRICE_REJECTED_LOW` | Rejet de zone basse / low rejetÃ©. |
| `PRICE_ABSORBED_PULLBACK` | Pullback absorbÃ© par prix / clÃ´ture. |
| `UNKNOWN` | Aucun Ã©tat prix fiable. |

### RÃ¨gles obligatoires

```text
PAIR_UP + lower low ensuite = COUNTER_BREATH_FAILED ou PRICE_INVALIDATED
PAIR_DOWN + close high ensuite = PULLBACK_ABSORBED ou FAILED_PRESSURE
HOT sans dÃ©placement prix = PRESSURE_PENDING
HOT aprÃ¨s extension = EXHAUSTION_OR_CONSUMED
B3+B4+P1 + rejet prix immÃ©diat = FAILED_RELEASE ou PRESSURE_PENDING
```

Le prix tranche le packet. Une brique ne peut pas valider seule une release si le prix l'a rejetÃ©e, si le packet est stale, ou si la zone active contredit la lecture.

---

## 4. RÃ¨gles raw_bias -> qualified_bias

| RULE_ID | RAW_BIAS | CONTEXT | REQUIRED_CONFIRMATION | QUALIFIED_BIAS | PACKET_QUALITY | PRICE_CONFIRMATION | WATCH | INVALIDATION |
|---|---|---|---|---|---|---|---|---|
| `R_PAIR_UP_AFTER_RELEASE_DOWN_COUNTER_BREATH` | `PAIR_UP` | AprÃ¨s `RELEASE_DOWN_VALIDATED`, `LOWER_LOCK`, `LOWER_PRICE_ACCEPTANCE` | RÃ©intÃ©gration prix au-dessus zone ou relais MTF | `POST_RELEASE_COUNTER_BREATH` | `REACTION_NOT_RELEASE` | `PRICE_PENDING` | Acceptation au-dessus zone active | Lower low / rejet sous zone |
| `R_PAIR_UP_AFTER_LOWER_LOW_POST_LOW_REACTION` | `PAIR_UP` | AprÃ¨s lower low ou low retest | Rejet low + maintien au-dessus low | `POST_LOW_COUNTER_BREATH` | `REACTION_NOT_RELEASE` | `PRICE_PENDING` | Reprise au-dessus zone basse | Nouveau lower low |
| `R_PAIR_UP_LATE_SESSION_THIN_BOUNCE` | `PAIR_UP` | Session tardive, relay faible | Besoin acceptance + relay | `LATE_THIN_BOUNCE` | `LOW_QUALITY_REACTION` | `PRICE_PENDING` | Tenue zone + relais | Rejet rapide / stale |
| `R_PAIR_UP_ACCEPTED_ABOVE_ZONE_CONTINUATION` | `PAIR_UP` | Prix acceptÃ© au-dessus zone | Close/acceptance au-dessus zone + propagation non failed | `UP_CONTINUATION_ACCEPTED` | `CONTINUATION_ACCEPTED` | `PRICE_ACCEPTED_ABOVE_ZONE` | Maintien au-dessus zone | RÃ©intÃ©gration sous zone |
| `R_PAIR_UP_AFTER_HIGH_EXHAUSTION_RISK` | `PAIR_UP` | AprÃ¨s high zone, extension dÃ©jÃ  faite | Acceptation forte requise | `HIGH_ZONE_EXHAUSTION_RISK` | `EXHAUSTION_RISK` | `PRICE_PENDING` | Nouveau high acceptÃ© | Rejet high / unwind |
| `R_PAIR_DOWN_AFTER_RELEASE_UP_PULLBACK` | `PAIR_DOWN` | AprÃ¨s `RELEASE_UP_VALIDATED` | Rejet ou cassure structurelle pour plus que pullback | `POST_RELEASE_PULLBACK` | `PULLBACK_CONTEXT` | `PRICE_PENDING` | Absorption ou rejet du pullback | Close high / absorption |
| `R_PAIR_DOWN_AFTER_HIGH_REJECTION_UNWIND` | `PAIR_DOWN` | High rejetÃ© / `HIGH_ZONE_REJECTION` | Rejet prix confirmÃ© | `POST_HIGH_UNWIND` | `STRUCTURAL_REACTION` | `PRICE_REJECTED_HIGH` | Continuation unwind | Reprise au-dessus high rejetÃ© |
| `R_PAIR_DOWN_AFTER_COUNTER_BREATH_REJECTED_SECOND_LEG` | `PAIR_DOWN` | Counter-breath rejetÃ© | Lower acceptance / relay non failed | `SECOND_LEG_DOWN` | `STRUCTURAL_CONTINUATION` | `PRICE_CONFIRMED` | Lower acceptance | RÃ©intÃ©gration au-dessus zone |
| `R_HOT_WITHOUT_PRICE_PRESSURE_PENDING` | `HOT` | Pas de dÃ©placement prix | DÃ©placement rÃ©el ou acceptance | `PRESSURE_PENDING` | `PRESSURE_NOT_RELEASE` | `PRICE_PENDING` | DÃ©placement hors zone | Stale / rejet immÃ©diat |
| `R_HOT_AFTER_EXTENSION_CONSUMED` | `HOT` | AprÃ¨s extension / high fait / release consommÃ©e | Nouvelle acceptance indÃ©pendante | `EXHAUSTION_OR_CONSUMED` | `CONSUMED_OR_LATE` | `PRICE_PENDING` | Acceptance fraÃ®che | Rejet extension |
| `R_HOT_WITH_ACCEPTANCE_EVENT_CONFIRMED` | `HOT` | Prix acceptÃ© + zone cohÃ©rente | Acceptance + propagation non failed + data acceptable | `EVENT_CONFIRMED` | `CONFIRMED_EVENT` | `PRICE_CONFIRMED` | Surveiller rÃ©solution prix | Perte acceptance |
| `R_B5_B8_WEAK_HONEST_UNKNOWN` | `ANY` | B5/B8 faible | Prix ou autre preuve dure requise | `HONEST_UNKNOWN` | `CROSS_VALIDATION_DEGRADED` | `UNKNOWN` | Attendre preuve indÃ©pendante | Ne pas valider par B8 seul |
| `R_PACKETS_STALE_READING_PARTIAL` | `ANY` | Packets stale / M1 absent | Refresh data requis | `READING_PARTIAL` | `DATA_LIMITED` | `UNKNOWN` | RafraÃ®chissement packets / M1 | Packet ancien utilisÃ© comme live |
| `R_B3_B2_EVENT_STACK_NOT_RELEASE` | `B3+B2` | B3+B2 actif seul | B4+P1+prix+B7 requis | `EVENT_STACK` | `EVENT_STACK_NOT_RELEASE` | `PRICE_PENDING` | Confirmation B4/P1/prix | Rejet prix ou bruit M1 |
| `R_B3_B4_P1_RELEASE_CANDIDATE` | `B3+B4+P1` | DÃ©tachement + compression + Ã©nergie | Prix + zone + B7 requis | `RELEASE_CANDIDATE` | `CANDIDATE_NOT_VALIDATED` | `PRICE_PENDING` | Acceptance prix | Rejet prix immÃ©diat |
| `R_B3_B4_P1_WITH_PRICE_ACCEPTANCE_RELEASE_VALIDATED` | `B3+B4+P1` | Candidate + acceptance | Data acceptable + propagation pas failed | `RELEASE_VALIDATED` | `RELEASE_VALIDATED` | `PRICE_CONFIRMED` | RÃ©solution structurelle | Perte acceptance |
| `R_B3_B4_P1_WITH_PRICE_REJECTION_FAILED_RELEASE` | `B3+B4+P1` | Candidate + rejet immÃ©diat | Aucune validation sans prix | `FAILED_RELEASE` | `FAILED_RELEASE` | `PRICE_FAILED` | Rebuild / pression pending | Continuer Ã  lire comme release |

---

## 5. RÃ¨gles B3+B2

`B3+B2 = EVENT_STACK / BIRTH_ATTEMPT`.

Jamais `RELEASE_VALIDATED`.

RÃ¨gles :

```text
B3+B2 actif seul -> EVENT_STACK
B3+B2 + bruit M1 Ã©levÃ© -> EVENT_STACK_NOISY
B3+B2 + B4 absent -> EVENT_STACK_NOT_RELEASE
B3+B2 + prix absent -> EVENT_STACK_NOT_RELEASE
B3+B2 + B4 + P1 -> RELEASE_CANDIDATE seulement
```

B2 empile des Ã©vÃ©nements. B3 lit un dÃ©tachement. Ensemble, ils signalent une activitÃ©. Ils ne prouvent pas que le film a changÃ©.

---

## 6. RÃ¨gles B3+B4+P1

`B3+B4+P1 = RELEASE_CANDIDATE`.

Devient `RELEASE_VALIDATED` seulement si :

- `price_confirmation` acceptable ;
- `current_zone` cohÃ©rente ;
- `propagation_state` pas seulement failed ;
- `data_visibility` acceptable.

Matrice :

```text
B3+B4+P1 + PRICE_ACCEPTED_ABOVE_ZONE + LTF_MTF_RELAY -> RELEASE_VALIDATED
B3+B4+P1 + PRICE_ACCEPTED_BELOW_ZONE + LTF_MTF_RELAY -> RELEASE_VALIDATED
B3+B4+P1 + PRICE_PENDING -> RELEASE_CANDIDATE
B3+B4+P1 + PRICE_FAILED -> FAILED_RELEASE
B3+B4+P1 + FAILED_PROPAGATION -> RELEASE_CANDIDATE_LIMITED
B3+B4+P1 + READING_PARTIAL -> RELEASE_CANDIDATE_DATA_LIMITED
```

---

## 7. RÃ¨gles B7 propagation

| propagation_state | Effet |
|---|---|
| `LTF_ONLY` | Mouvement local. Peut qualifier une rÃ©action, pas valider seul une release structurelle. |
| `LTF_MTF_RELAY` | Relais M1/M5/M15 : renforce candidate, permet validation si prix et zone confirment. |
| `MTF_HTF_RELAY` | Relais profond : renforce `packet_quality`. |
| `FAILED_PROPAGATION` | Limite fortement : pression locale, false reaction ou failed release. |
| `RELAY_DEGRADING` | Conserve packet mais dÃ©grade qualitÃ©. |
| `COUNTERFLOW_AGAINST_STRUCTURE` | Information qualitative : mouvement contre structure, pas blocage automatique. |
| `UNKNOWN` | Ne valide rien seul. |

B7 ne dÃ©cide pas le film. B7 dit si le mouvement reste local, se propage, se dÃ©grade, ou se fait contre la structure.

---

## 8. RÃ¨gles B7+ texture

| detachment_texture | Effet |
|---|---|
| `STRUCTURAL_DETACHMENT` | Renforce release candidate si prix confirme. |
| `NOISY_DETACHMENT` | Ajoute risque technique `NOISY_DETACHMENT`; limite qualitÃ©. |
| `COUNTER_BREATH_DETACHMENT` | Requalifie direction brute en respiration inverse. |
| `POST_RELEASE_DETACHMENT` | Requalifie en pullback, continuation ou absorption selon prix. |
| `LATE_SESSION_DETACHMENT` | Suspect / thin bounce sauf prix trÃ¨s clair. |
| `EXHAUSTION_DETACHMENT` | Risque consumed/exhaustion. |
| `REJECTION_DETACHMENT` | Favorise unwind / failed release. |
| `FALSE_REACTION_DETACHMENT` | Limite Ã  watch ou reading partial. |
| `UNKNOWN` | Ne renforce rien seul. |

B7+ ne remplace pas le prix. Il donne la texture du dÃ©tachement.

---

## 9. RÃ¨gles B6 memory

B6 devient mÃ©moire de films, pas mÃ©moire d'Ã©vÃ©nements isolÃ©s.

B6 peut :

- renforcer si le film actuel ressemble Ã  un film calibrÃ© et que les preuves live sont cohÃ©rentes ;
- limiter si le film ressemble Ã  un faux positif connu ;
- signaler `false_positive_risk` ;
- indiquer `expected_next_behavior`.

B6 ne dÃ©cide jamais seul.

Sortie B6 attendue :

```json
{
  "memory_match": "LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL",
  "memory_confidence": 0.74,
  "expected_next_behavior": "LOW_RETEST_OR_POST_LOW_REACTION",
  "false_positive_risk": "READING_PARTIAL_CAN_OVERSTATE_COUNTER_BREATH"
}
```

Si B6 contredit prix ou zone, il reste informatif.

---

## 10. terrain_packet_v76_0

Champs obligatoires :

```text
schema_version
symbol
generated_at
market_time
film_state
last_structural_event
last_structural_direction
last_structural_time
current_zone
current_zone_low
current_zone_high
current_zone_status
current_move_role
raw_bias
qualified_bias
packet_quality
price_confirmation
propagation_state
detachment_texture
data_visibility
watch_condition
invalidation_condition
technical_risks
evidence_refs
```

RÃ¨gle d'affichage :

```text
DATA_VISIBILITY
FILM / LAST_EVENT / ZONE
RAW_BIAS conservÃ© mais secondaire
QUALIFIED_BIAS principal
PRICE_CONFIRMATION obligatoire
WATCH / INVALIDATION sans buy/sell/entry/target/stop
```

---

## 11. Audit log

Format `terrain_packet_audit.jsonl` : un JSON par ligne.

Champs recommandÃ©s :

```json
{
  "schema_version": "terrain_packet_audit_v76_0",
  "generated_at": "2026-05-14T12:00:00Z",
  "symbol": "GBPUSD",
  "raw_bias": "PAIR_UP",
  "qualified_bias": "POST_LOW_COUNTER_BREATH",
  "packet_quality": "REACTION_NOT_RELEASE",
  "price_confirmation": "PRICE_PENDING",
  "data_visibility": "M1_MISSING_PACKETS_STALE",
  "rules_fired": ["R_PAIR_UP_AFTER_LOWER_LOW_POST_LOW_REACTION", "R_PACKETS_STALE_READING_PARTIAL"],
  "technical_risks": ["M1_MISSING", "PACKETS_STALE"],
  "evidence_refs": ["film:2026-05-14", "packet:latest"]
}
```

Audit obligatoire pour comprendre pourquoi `qualified_bias` diffÃ¨re de `raw_bias`.

---

## 12. QA obligatoire

| QA_ID | ScÃ©nario | Attendu |
|---|---|---|
| `QA-01` | B3+B2 actif seul | `EVENT_STACK`, pas `RELEASE_VALIDATED`. |
| `QA-02` | B3+B4+P1 + prix acceptÃ© | `RELEASE_VALIDATED`. |
| `QA-03` | Release UP puis `PAIR_DOWN` | `POST_RELEASE_PULLBACK`. |
| `QA-04` | Pullback absorbÃ© | `PULLBACK_ABSORBED`. |
| `QA-05` | High rejetÃ© puis DOWN | `POST_HIGH_UNWIND`. |
| `QA-06` | Release DOWN puis `PAIR_UP` | `COUNTER_BREATH_UP` ou `POST_RELEASE_COUNTER_BREATH`. |
| `QA-07` | Counter-breath Ã©choue | `COUNTER_BREATH_REJECTED`. |
| `QA-08` | AprÃ¨s rejet counter-breath | `SECOND_LEG_DOWN`. |
| `QA-09` | HOT sans dÃ©placement | `PRESSURE_PENDING`. |
| `QA-10` | HOT aprÃ¨s extension | `EXHAUSTION_OR_CONSUMED`. |
| `QA-11` | B8 coverage faible | `HONEST_UNKNOWN` / `B8_DEGRADED`. |
| `QA-12` | M1 absent/stale | `READING_PARTIAL` en haut ou `M1_MISSING_PACKETS_STALE`. |
| `QA-13` | `event_at` offset | `EVENT_TIME_OFFSET`. |
| `QA-14` | LTF contre MTF | Information qualitative, pas blocage. |

---

## 13. Non-rÃ©gression V7.6

Interdits :

```text
Ne pas inventer une nouvelle spine.
Ne pas refaire le dashboard.
Ne pas activer Telegram.
Ne pas produire de stratÃ©gie de trading.
Ne pas crÃ©er buy/sell/entry/exit/target/stop.
Ne pas valider une release depuis un seul Ã©vÃ©nement.
Ne pas afficher PAIR_UP / PAIR_DOWN seul comme lecture principale.
Ne pas masquer data_visibility.
Ne pas ignorer price_confirmation.
Ne pas transformer Alert Gate en moteur sÃ©mantique.
```

Ce patch est minimal : il qualifie un packet. Il ne refond pas PowerFlow.

```

---

# SOURCE: Docs\T006_Source_Staging\PACKET_REQUALIFICATION__POWERFLOW_TRADER_PACKET_REQUIREMENTS_V76.md

SHA256: 1B63AEAC33E3032DDC0C49CA809E37822E04464CB036059BA93415FCEF7BC304
BYTES: 7537

```text
# POWERFLOW TRADER PACKET REQUIREMENTS V7.6

## 0. Objet

Ce document dÃ©finit le minimum qu'un packet PowerFlow V7.6 doit dire au trader pour Ãªtre utile. Il ne dÃ©finit pas une stratÃ©gie, ne crÃ©e pas de signal de trading et ne modifie pas le dashboard. Il impose une structure de perception exploitable.

## 1. Principe

Un packet utile ne dit pas seulement :

```text
PAIR_UP WATCH
```

Il doit dire :

```text
FILM=...
LAST_EVENT=...
ZONE=...
MOVE=...
RAW_BIAS=...
QUALIFIED_BIAS=...
PACKET_QUALITY=...
PRICE_CONFIRMATION=...
PROPAGATION=...
TEXTURE=...
DATA=...
WATCH=...
INVALIDATION=...
```

## 2. Champs obligatoires

### 2.1 Film

**Champ** : `film_state`

**But** : situer l'Ã©vÃ©nement dans le film courant.

**Exemples** :

- `LOWER_ZONE_ACTIVE`
- `POST_HIGH_UNWIND`
- `PRE_LONDON_FALSE_BIRTHS`
- `READING_PARTIAL`

**RÃ¨gle** : si le film n'est pas dÃ©terminable, utiliser `UNKNOWN`, pas une supposition.

### 2.2 Dernier Ã©vÃ©nement structurel

**Champs** : `last_structural_event`, `last_structural_direction`

**But** : empÃªcher PowerFlow de lire chaque packet comme un nouveau dÃ©part.

**Exemples** :

- `COUNTER_BREATH_REJECTED / DOWN`
- `RELEASE_UP_VALIDATED / UP`
- `HIGH_ZONE_REJECTION / DOWN`

**RÃ¨gle** : le dernier Ã©vÃ©nement structurel influence la requalification des packets suivants tant qu'il n'est pas invalidÃ© ou consommÃ©.

### 2.3 Zone active

**Champs** : `current_zone`, `current_zone_low`, `current_zone_high`, `current_zone_status`

**But** : dire oÃ¹ le prix travaille.

**Exemples** :

```text
current_zone=LOWER_ZONE_1.3504_1.3532
current_zone_status=LOWER_RANGE_ACTIVE
```

**RÃ¨gle** : une poussÃ©e dans une zone basse active n'a pas le mÃªme sens qu'une poussÃ©e hors zone acceptÃ©e.

### 2.4 RÃ´le du mouvement

**Champ** : `current_move_role`

**But** : remplacer la lecture directionnelle brute par un rÃ´le terrain.

**Exemples** :

- `COUNTER_BREATH`
- `POST_RELEASE_PULLBACK`
- `PULLBACK_ABSORBED`
- `SECOND_LEG`
- `LATE_THIN_BOUNCE`

**RÃ¨gle** : `current_move_role` est le champ central du packet.

### 2.5 QualitÃ© du packet

**Champ** : `packet_quality`

**But** : distinguer fresh, rÃ©action, late, degraded, unknown.

**Enums recommandÃ©s** :

- `FRESH_STRUCTURE`
- `RELEASE_CANDIDATE_ONLY`
- `REACTION_NOT_RELEASE`
- `LATE_OR_CONSUMED`
- `HONEST_UNKNOWN`
- `DEGRADED`

**RÃ¨gle** : la qualitÃ© qualifie le packet sans le censurer.

### 2.6 Confirmation prix

**Champ** : `price_confirmation`

**But** : dire si le prix confirme, attend, rejette ou invalide.

**Enums recommandÃ©s** :

- `PRICE_CONFIRMED`
- `PRICE_PENDING`
- `PRICE_REJECTED`
- `PRICE_INVALIDATED`
- `PRICE_CONSUMED`
- `PRICE_UNKNOWN`

**RÃ¨gle** : 100% des packets doivent avoir ce champ.

### 2.7 Propagation

**Champ** : `propagation_state`

**But** : dire si le mouvement reste local ou se propage.

**Enums recommandÃ©s** :

- `LTF_ONLY`
- `LTF_MTF_RELAY`
- `MTF_HTF_RELAY`
- `FAILED_PROPAGATION`
- `COUNTERFLOW_AGAINST_STRUCTURE`
- `RELAY_DEGRADING`
- `PROPAGATION_UNKNOWN`

**RÃ¨gle** : absence de relais = information, pas censure.

### 2.8 Texture

**Champ** : `detachment_texture`

**But** : qualifier le type de dÃ©tachement.

**Enums recommandÃ©s** :

- `STRUCTURAL_DETACHMENT`
- `NOISY_DETACHMENT`
- `COUNTER_BREATH_DETACHMENT`
- `POST_RELEASE_DETACHMENT`
- `LATE_SESSION_DETACHMENT`
- `EXHAUSTION_DETACHMENT`
- `REJECTION_DETACHMENT`
- `FALSE_REACTION_DETACHMENT`
- `TEXTURE_UNKNOWN`

**RÃ¨gle** : B7+ doit rester terrain et lisible, pas thÃ©orique.

### 2.9 Limites data

**Champ** : `data_visibility`

**But** : afficher les limites de lecture en haut, pas en note cachÃ©e.

**Enums recommandÃ©s** :

- `FULL_STACK_VISIBLE`
- `TACTICAL_OK`
- `DATA_PARTIAL`
- `MICROFILM_MISSING`
- `PACKETS_STALE`
- `CROSS_VALIDATION_DEGRADED`
- `DATA_BLIND`
- `DATA_UNKNOWN`

**RÃ¨gle** : si data dÃ©gradÃ©e, le cockpit doit le montrer immÃ©diatement.

### 2.10 Watch

**Champ** : `watch_condition`

**But** : dire ce qui mÃ©rite attention ensuite.

**Exemples** :

- `acceptance above 1.3532`
- `rejection back into lower zone`
- `M5 relay appears after M1 pressure`

**RÃ¨gle** : une watch condition n'est pas un ordre.

### 2.11 Invalidation

**Champ** : `invalidation_condition`

**But** : rendre la lecture falsifiable.

**Exemples** :

- `lower low below 1.3504`
- `close back inside rejected high zone`
- `counter-breath accepted above zone`

**RÃ¨gle** : ce n'est pas un stop. C'est une condition d'invalidation analytique.

## 3. Message cockpit minimal

### Ligne courte

```text
GBPUSD | LOWER_ZONE_ACTIVE | POST_LOW_REACTION | PAIR_UP->POST_LOW_COUNTER_BREATH | PRICE_PENDING | DATA_PARTIAL
```

### Packet humain

```text
GBPUSD: film=LOWER_ZONE_ACTIVE. Last=COUNTER_BREATH_REJECTED/DOWN. Zone=LOWER_RANGE_ACTIVE 1.3504-1.3532. Move=POST_LOW_REACTION. Bias=PAIR_UP->POST_LOW_COUNTER_BREATH. Price=PRICE_PENDING. Propagation=LTF_ONLY. Texture=COUNTER_BREATH_DETACHMENT. Data=DATA_PARTIAL. Watch=acceptance above 1.3532. Invalid=lower low below 1.3504. Risks=M1_MISSING,PACKETS_STALE.
```

### Packet JSON minimal

```json
{
  "schema": "terrain_packet_v76_0",
  "symbol": "GBPUSD",
  "film_state": "LOWER_ZONE_ACTIVE",
  "last_structural_event": "COUNTER_BREATH_REJECTED",
  "last_structural_direction": "DOWN",
  "current_zone": "LOWER_ZONE_1.3504_1.3532",
  "current_zone_low": 1.3504,
  "current_zone_high": 1.3532,
  "current_zone_status": "LOWER_RANGE_ACTIVE",
  "current_move_role": "POST_LOW_REACTION",
  "raw_bias": "PAIR_UP",
  "qualified_bias": "POST_LOW_COUNTER_BREATH",
  "packet_quality": "REACTION_NOT_RELEASE",
  "price_confirmation": "PRICE_PENDING",
  "propagation_state": "LTF_ONLY",
  "detachment_texture": "COUNTER_BREATH_DETACHMENT",
  "data_visibility": "DATA_PARTIAL",
  "watch_condition": "acceptance above 1.3532",
  "invalidation_condition": "lower low below 1.3504",
  "technical_risks": ["M1_MISSING", "PACKETS_STALE"]
}
```

## 4. Requirements d'affichage

1. `film_state`, `current_move_role`, `qualified_bias`, `price_confirmation` et `data_visibility` doivent Ãªtre visibles sans ouvrir de dÃ©tail.
2. Si `data_visibility` vaut `DATA_PARTIAL`, `MICROFILM_MISSING`, `PACKETS_STALE`, `CROSS_VALIDATION_DEGRADED` ou `DATA_BLIND`, l'information doit remonter en haut.
3. `raw_bias` doit Ãªtre visible mais toujours accompagnÃ© de `qualified_bias`.
4. `UNKNOWN` doit Ãªtre affichable sans Ãªtre considÃ©rÃ© comme erreur applicative.
5. `READING_PARTIAL` doit Ãªtre un Ã©tat noble de vÃ©ritÃ© data, pas un Ã©chec cosmÃ©tique.

## 5. Non-dÃ©clencheurs

Un packet trader V7.6 ne doit jamais dÃ©clencher directement :

- buy ;
- sell ;
- entry ;
- exit ;
- target ;
- stop ;
- taille de position ;
- exÃ©cution automatique.

Il doit seulement rÃ©veiller une perception qualifiÃ©e.

## 6. Acceptance Criteria

- Aucun packet ne sort avec `PAIR_UP` ou `PAIR_DOWN` seul comme message principal.
- Tous les packets contiennent `data_visibility`.
- Tous les packets contiennent `price_confirmation`.
- Tous les packets contiennent une forme de `watch_condition` ou `UNKNOWN`.
- Tous les packets contiennent une forme de `invalidation_condition` ou `UNKNOWN`.
- `READING_PARTIAL`, `HONEST_UNKNOWN` et `UNKNOWN` sont acceptÃ©s par le schÃ©ma.
- Le packet est compatible `terrain_packet_v76_0`.

```