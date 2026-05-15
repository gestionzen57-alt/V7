# T008/T009 Scheduler Telegram Safety Audit

Date: 2026-05-15 19:28:25 +02:00

## Scope

Role: GPT-3 Scheduler  
Mission: orchestration, Telegram dry-run safety, dashboard_surface routing map.

Allowed:
- Scheduler wrappers
- Telegram wrappers
- Dry-run orchestration
- Read-only static audit
- Checkpoint report

Forbidden:
- DB modification
- Dashboard V7.4 / FR Trader V5 modification
- T004 USDJPY diagnostic
- Core Engine T002/T003
- BUY/SELL trading semantics

## Verdict

Failures: 1  
Warnings: 1  
Passes: 25

## Passes

- PASS: V7.6 wrapper default TelegramMode is dry-run
- PASS: V7.6 wrapper no longer defaults to send
- PASS: V7.6.6 short-live wrapper defaults to dry-run
- PASS: V7.6.6 calls legacy V7.6 in dry-run
- PASS: V7.6.7 reality wrapper defaults to dry-run
- PASS: V7.6.7 forces legacy V7.6 cycle to dry-run
- PASS: V7.6 Python tail defaults to dry-run
- PASS: V7.6 Python tail maps dry-run to --dry-run
- PASS: V7.6 Python tail requires explicit send mode
- PASS: Qualified Telegram supports explicit --dry-run
- PASS: Qualified Telegram requires explicit --send
- PASS: Qualified Telegram has dry-run guard
- PASS: Qualified Telegram does not send unless --send
- PASS: Qualified Telegram dry-run guard occurs before credential lookup/send
- PASS: Short-live Telegram defaults to dry-run
- PASS: Short-live Telegram sends only in explicit send mode
- PASS: Reality Board Telegram default mode is dry-run
- PASS: Reality Board modes are explicit
- PASS: Reality Board has dry-run branch
- PASS: Reality Board sends only from live branch
- PASS: Telegram network calls inventoried; static guards checked above
- PASS: No BUY/SELL trading instruction tokens found in Scheduler/Telegram target files
- PASS: No Dashboard V7.4 mutation/reference pattern found in Scheduler/Telegram target files
- PASS: Core scheduler surface references collected
- PASS: Root Telegram surface references collected

## Warnings

- WARN: pytest not found in PATH; skipped targeted tests

## Failures

- FAIL: Potential DB write pattern found in Scheduler/Telegram target files

## Telegram network call inventory

- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_telegram_qualified_alert_once.py:159: url = f"https://api.telegram.org/bot{token}/sendMessage"
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_telegram_qualified_alert_once.py:168: with urllib.request.urlopen(request, timeout=20) as response:
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_telegram_short_live_v766.py:144: url = f"https://api.telegram.org/bot{token}/sendMessage"
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_telegram_short_live_v766.py:147: with urllib.request.urlopen(url, data=payload, timeout=20) as resp:
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_telegram_reality_board_v767.py:314: url = f"https://api.telegram.org/bot{token}/sendMessage"
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_telegram_reality_board_v767.py:322: with urllib.request.urlopen(req, timeout=20) as response:

## BUY/SELL doctrine scan

- No BUY/SELL tokens found.

## dashboard_surface routing map

### Core scheduler surface

Expected runtime family:
- Core/output/dashboard_surface/...

Collected refs:

- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:132: "output/dashboard_surface/data_health.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:156: "output/dashboard_surface/signal_adaptive_profiles.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:158: "output/dashboard_surface/signal_adaptive.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:175: "output/dashboard_surface/topdown_market_reader.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:177: "output/dashboard_surface/topdown_reader.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:239: "--output", "output/dashboard_surface/live_brief_dashboard.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:248: "--output", "output/dashboard_surface/b6_live_fusion_dashboard.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:253: "--output", "output/dashboard_surface/powerflow_multiread_synthesis.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:257: "--input", "output/dashboard_surface/powerflow_multiread_synthesis.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:258: "--output", "output/dashboard_surface/multiread_synthesis_dashboard.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:276: "--output", "output/dashboard_surface/time_profiles_dashboard.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:283: "--output", "output/dashboard_surface/trader_cockpit.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:284: "--txt", "output/dashboard_surface/trader_cockpit.txt",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:288: "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:289: "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:290: "--time-profiles", "output/dashboard_surface/time_profiles_dashboard.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:296: "--output", "output/dashboard_surface/b8_cross_surface.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:297: "--txt", "output/dashboard_surface/b8_cross_surface.txt",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:302: "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:303: "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:304: "--b8", "output/dashboard_surface/b8_cross_surface.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:310: "--time-profiles", "output/dashboard_surface/time_profiles_dashboard.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:311: "--cockpit", "output/dashboard_surface/trader_cockpit.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:312: "--b8", "output/dashboard_surface/b8_cross_surface.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:313: "--output", "output/dashboard_surface/phase_synthesis.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:314: "--txt", "output/dashboard_surface/phase_synthesis.txt",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:319: "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:320: "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:321: "--phase", "output/dashboard_surface/phase_synthesis.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:327: "--output", "output/dashboard_surface/evidence_bus.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:328: "--txt", "output/dashboard_surface/evidence_bus.txt",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:333: "--evidence-bus", "output/dashboard_surface/evidence_bus.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:334: "--output", "output/dashboard_surface/evidence_reading.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:335: "--txt", "output/dashboard_surface/evidence_reading.txt",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:340: "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:341: "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:342: "--evidence-reading", "output/dashboard_surface/evidence_reading.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:343: "--evidence-bus", "output/dashboard_surface/evidence_bus.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:354: "--output", "output/dashboard_surface/trader_journal_j1.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:355: "--md", "output/dashboard_surface/trader_journal_j1.md",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:375: "--output", "output/dashboard_surface/daily_journal.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:379: "--input", "output/dashboard_surface/daily_journal.json",
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\scheduler_powerflow_turbo_wrapper.py:380: "--output", "output/dashboard_surface/daily_journal_dashboard.json",

### Root Telegram surface

Expected runtime family:
- output/dashboard_surface/GBPUSD/...

Collected refs:

- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_v76_telegram_cycle_once.py:67: def write_dashboard_surface(symbol: str, context: Dict[str, Any], packet: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, str]:
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_v76_telegram_cycle_once.py:68: out_dir = ROOT / "output" / "dashboard_surface" / symbol
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_v76_telegram_cycle_once.py:163: paths = write_dashboard_surface(symbol, context, packet, memory)
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_v76_telegram_cycle_once.py:182: result_path = ROOT / "output" / "dashboard_surface" / symbol / "v76_telegram_cycle_result.json"
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_v76_telegram_cycle_once.py:196: legacy_source = Path(args.legacy_source) if args.legacy_source else ROOT / "Core" / "output" / "dashboard_surface" / symbol / "legacy_behavioral_state.json"
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_telegram_short_live_v766.py:161: ap.add_argument("--output", default="output/dashboard_surface/GBPUSD/v766_telegram_short_live_result.json")
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_telegram_short_live_v766.py:164: surface = ROOT / "output" / "dashboard_surface" / args.symbol
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_telegram_reality_board_v767.py:352: rb_path = Path(args.input) if args.input else ROOT / "output" / "dashboard_surface" / symbol / "reality_board_state.json"
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_telegram_reality_board_v767.py:353: out_path = Path(args.out) if args.out else ROOT / "output" / "dashboard_surface" / symbol / "v767_reality_telegram_result.json"
- C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\patch\pf_telegram_reality_board_v767.py:354: memory_path = ROOT / "output" / "dashboard_surface" / symbol / "v767_reality_telegram_sent_memory.json"

## Operational conclusion

- Telegram default safety is expected to be dry-run across wrappers.
- Real Telegram transmission must require explicit send/live mode.
- V7.6 legacy wrapper default was previously hardened by commit c0d3aee.
- Scheduler orchestrates; it does not decide.
- Telegram transmits; it is not source of truth.
- No BUY/SELL instruction should be emitted.
- dashboard_surface has two families and should not be merged without architecture decision:
  - Core/output/dashboard_surface for Dashboard live surfaces.
  - output/dashboard_surface/GBPUSD for Telegram/cycle-tail artifacts.

