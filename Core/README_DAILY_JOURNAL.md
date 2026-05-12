# PowerFlow V7.3.2 — DAILY_PACKET_REFINEMENT

Mission: transformer le Daily Flow Packet en journal opérationnel.

Sorties:
- `output/dashboard_surface/daily_journal.json`
- `output/dashboard_surface/daily_journal_dashboard.json`
- `output/dashboard_surface/<SYMBOL>/daily_journal.json`

Commandes:

```powershell
python run_daily_journal_all_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --output output/dashboard_surface/daily_journal.json --pretty
python dashboard_normalize_daily_journal.py --input output/dashboard_surface/daily_journal.json --output output/dashboard_surface/daily_journal_dashboard.json --pretty
```
