#!/usr/bin/env python3
import argparse, json
from audit_usdjpy_capture import audit_usdjpy_capture, write_report

def main():
    ap=argparse.ArgumentParser(description='Run USDJPY capture audit once')
    ap.add_argument('--db', default='powerflow.db'); ap.add_argument('--symbol', default='USDJPY'); ap.add_argument('--out', default='output/audit_usdjpy_report.json'); ap.add_argument('--pretty', action='store_true')
    a=ap.parse_args(); rep=audit_usdjpy_capture(a.db, a.symbol); write_report(rep,a.out)
    if a.pretty: print(json.dumps(rep, indent=2, ensure_ascii=False))
    else: print(f"USDJPY_AUDIT_OK | symbol={rep.get('symbol')} | rows_total={rep.get('rows_total')} | diagnosis={rep.get('diagnosis')} | out={a.out}")
    return 0 if rep.get('status') in {'PASS','DEGRADED'} else 2
if __name__=='__main__': raise SystemExit(main())
