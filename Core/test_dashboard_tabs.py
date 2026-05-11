#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
SYMBOLS=['GBPUSD','EURUSD','USDJPY','XAUUSD']
SNIPS=['CROSS_SYMBOL_VALIDATION_CARD','output/dashboard_surface/','cross_validation.json','regime_legacy.json','regime_hmm.json','energy.json','node.json','cascade.json','data-brick','data-symbol','FRESH','AGING','STALE']

def validate_html(path):
    rep={'file':str(path),'exists':path.exists(),'checks':[],'status':'PASS','technical_risks':[]}
    if not path.exists(): rep['status']='FAIL'; rep['technical_risks'].append('DASHBOARD_PATCH_MISSING'); return rep
    txt=path.read_text(encoding='utf-8', errors='replace')
    for s in SYMBOLS:
        ok=s in txt; rep['checks'].append({'check':'symbol_tab_'+s,'pass':ok})
        if not ok: rep['status']='FAIL'; rep['technical_risks'].append('TAB_'+s+'_MISSING')
    for sn in SNIPS:
        ok=sn in txt; rep['checks'].append({'check':'snippet_'+sn,'pass':ok})
        if not ok: rep['status']='FAIL'; rep['technical_risks'].append('SNIPPET_MISSING_'+sn)
    return rep

def validate_outputs(root):
    checks=[]; status='PASS'; risks=[]
    for sym in ['GBPUSD','EURUSD','USDJPY']:
        for fn in ['node.json','energy.json','regime_legacy.json']:
            p=root/'output'/'dashboard_surface'/sym/fn; ok=p.exists(); checks.append({'symbol':sym,'file':fn,'path':str(p),'exists':ok})
            if not ok: status='WARN'; risks.append(f'MISSING_OUTPUT_{sym}_{fn}')
    p=root/'output'/'dashboard_surface'/'cross_validation.json'; ok=p.exists(); checks.append({'symbol':'GLOBAL','file':'cross_validation.json','path':str(p),'exists':ok})
    if not ok: status='WARN'; risks.append('MISSING_CROSS_VALIDATION_OUTPUT')
    return {'status':status,'checks':checks,'technical_risks':risks}

def main():
    ap=argparse.ArgumentParser(description='Validate MultiSymbol dashboard tabs patch')
    ap.add_argument('--html', default='dashboard_multisymbol_ui_patch.html'); ap.add_argument('--core', default='.'); ap.add_argument('--check-runtime-outputs', action='store_true'); ap.add_argument('--out', default='output/test_dashboard_tabs_report.json'); ap.add_argument('--pretty', action='store_true')
    a=ap.parse_args(); html=validate_html(Path(a.html)); runtime=validate_outputs(Path(a.core)) if a.check_runtime_outputs else None
    status=html['status'] if not runtime else ('FAIL' if html['status']=='FAIL' else runtime['status'])
    rep={'test':'DASHBOARD_MULTISYMBOL_TABS','html':html,'runtime_outputs':runtime,'status':status}
    out=Path(a.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding='utf-8')
    if a.pretty: print(json.dumps(rep, indent=2, ensure_ascii=False))
    else: print(f'DASHBOARD_TABS_TEST_{status} | out={out}')
    return 0 if status in {'PASS','WARN'} else 2
if __name__=='__main__': raise SystemExit(main())
