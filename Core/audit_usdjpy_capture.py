#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

def connect_ro(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)

def table_exists(conn, table):
    return conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None

def columns(conn, table):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]

def ts_col(cols):
    for c in ["timestamp","timestamp_utc","time","datetime","created_at","ts"]:
        for x in cols:
            if x.lower()==c: return x
    return None

def parse_dt(v):
    if v is None: return None
    try:
        s=str(v).replace('Z','+00:00')
        d=datetime.fromisoformat(s)
        if d.tzinfo is None: d=d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None

def age_seconds(v):
    d=parse_dt(v)
    return None if not d else max(0, int((datetime.now(timezone.utc)-d).total_seconds()))

def dict_rows(conn, sql, params=()):
    old=conn.row_factory; conn.row_factory=sqlite3.Row
    try: return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally: conn.row_factory=old

def audit_usdjpy_capture(db_path='powerflow.db', symbol='USDJPY', max_rows_preview=500) -> Dict[str,Any]:
    symbol=symbol.upper()
    rep={"symbol":symbol,"audit_type":"AUDIT_USDJPY_CAPTURE","timestamp_utc":datetime.now(timezone.utc).isoformat(),"db_path":db_path,"db_mode":"READ_ONLY","table":"force_snapshots","technical_risks":[]}
    try: conn=connect_ro(db_path)
    except Exception as e:
        rep.update(status='FAIL', diagnosis='DB_OPEN_FAILED', recommendation='Check db path and file permissions', error=str(e), action_required='URGENT'); return rep
    try:
        if not table_exists(conn,'force_snapshots'):
            rep.update(status='FAIL', diagnosis='FORCE_SNAPSHOTS_TABLE_MISSING', recommendation='Check DB schema or active DB path', action_required='URGENT'); return rep
        cols=columns(conn,'force_snapshots'); rep['columns']=cols
        sym_col=next((c for c in cols if c.lower()=='symbol'), None)
        if not sym_col:
            rep.update(status='FAIL', diagnosis='SYMBOL_COLUMN_MISSING', recommendation='MultiSymbol requires force_snapshots.symbol', action_required='URGENT'); return rep
        tcol=ts_col(cols); fcol=next((c for c in cols if c.lower()=='timeframe'), None)
        rep['timestamp_column']=tcol; rep['timeframe_column']=fcol
        rows=int(conn.execute(f"SELECT COUNT(*) FROM force_snapshots WHERE UPPER({sym_col})=?",(symbol,)).fetchone()[0])
        rep['rows_total']=rows
        if tcol:
            earliest=conn.execute(f"SELECT {tcol} FROM force_snapshots WHERE UPPER({sym_col})=? ORDER BY {tcol} ASC LIMIT 1",(symbol,)).fetchone()
            latest=conn.execute(f"SELECT {tcol} FROM force_snapshots WHERE UPPER({sym_col})=? ORDER BY {tcol} DESC LIMIT 1",(symbol,)).fetchone()
            rep['earliest_timestamp']=str(earliest[0]) if earliest else None; rep['latest_timestamp']=str(latest[0]) if latest else None
        else:
            rep['earliest_timestamp']=rep['latest_timestamp']=None; rep['technical_risks'].append('TIMESTAMP_COLUMN_NOT_DETECTED')
        rep['latest_age_seconds']=age_seconds(rep.get('latest_timestamp'))
        rep['timeframes']=[r[0] for r in conn.execute(f"SELECT DISTINCT {fcol} FROM force_snapshots WHERE UPPER({sym_col})=? ORDER BY {fcol}",(symbol,)).fetchall()] if fcol else []
        rep['other_symbols']=[r[0] for r in conn.execute(f"SELECT DISTINCT {sym_col} FROM force_snapshots ORDER BY {sym_col}").fetchall()]
        rep['symbol_counts']=[{'symbol':r[0], 'rows':int(r[1])} for r in conn.execute(f"SELECT {sym_col}, COUNT(*) FROM force_snapshots GROUP BY {sym_col} ORDER BY COUNT(*) DESC").fetchall()]
        if tcol:
            rep['symbol_latest']=[{'symbol':r[0], 'rows':int(r[1]), 'latest_timestamp':r[2]} for r in conn.execute(f"SELECT {sym_col}, COUNT(*), MAX({tcol}) FROM force_snapshots GROUP BY {sym_col} ORDER BY {sym_col}").fetchall()]
        rep['usdjpy_rows_preview_limit']=max_rows_preview
        rep['usdjpy_rows']=dict_rows(conn, f"SELECT * FROM force_snapshots WHERE UPPER({sym_col})=? LIMIT ?", (symbol, max_rows_preview))
        age=rep.get('latest_age_seconds')
        if rows==0:
            diag='NO_USDJPY_ROWS - CAPTURE INACTIVE OR SYMBOL NOT INSERTED'; rec='Check MT4 EA symbols list, bridge symbol routing, and force_snapshots insertion path'; action='URGENT'; rep['technical_risks']+=['USDJPY_NO_ROWS','CAPTURE_INACTIVE']
        elif rows<100:
            diag='STALE DATA - CAPTURE INACTIVE OR INCOMPLETE'; rec='Check MT4 EA symbols list / Check bridge insertion logic / Verify USDJPY enabled in capture'; action='URGENT'; rep['technical_risks']+=['USDJPY_INSUFFICIENT_ROWS','CAPTURE_INCOMPLETE']
        elif age is not None and age>86400:
            diag='STALE TIMESTAMP - USDJPY NOT LIVE'; rec='Check MT4 EA live feed and bridge insertion for USDJPY'; action='URGENT'; rep['technical_risks']+=['USDJPY_STALE_TIMESTAMP','CAPTURE_NOT_LIVE']
        else:
            diag='USDJPY CAPTURE APPEARS ACTIVE'; rec='Continue monitoring row growth and timeframe completeness'; action='MONITOR'
        rep.update(status='PASS' if action=='MONITOR' else 'DEGRADED', diagnosis=diag, recommendation=rec, action_required=action, expected={'rows_total':'> 100 if capture OK','latest_timestamp':'today/recent if capture OK','timeframes':'multiple active TFs if full capture OK'})
        return rep
    finally:
        conn.close()

def write_report(rep, out):
    p=Path(out); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(description='Audit USDJPY capture in PowerFlow DB')
    ap.add_argument('--db', default='powerflow.db'); ap.add_argument('--symbol', default='USDJPY'); ap.add_argument('--out', default='output/audit_usdjpy_report.json'); ap.add_argument('--pretty', action='store_true'); ap.add_argument('--max-rows-preview', type=int, default=500)
    a=ap.parse_args(); rep=audit_usdjpy_capture(a.db, a.symbol, a.max_rows_preview); write_report(rep,a.out)
    if a.pretty: print(json.dumps(rep, indent=2, ensure_ascii=False))
    else: print(f"AUDIT_USDJPY_CAPTURE_OK | symbol={rep.get('symbol')} | rows={rep.get('rows_total')} | diagnosis={rep.get('diagnosis')} | out={a.out}")
    return 0 if rep.get('status') in {'PASS','DEGRADED'} else 2
if __name__=='__main__': raise SystemExit(main())
