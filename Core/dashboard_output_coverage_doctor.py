#!/usr/bin/env python3
"""
PowerFlow V7.2 Dashboard Output Coverage Doctor

Reads output/dashboard_surface/*.json and output/*.json, then explains why the
cockpit displays LIVE / STALE / DEGRADED / MISSING cards. It does not import
pf_* and does not write to powerflow.db.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

SURFACE_KEYS = [
    'regime_legacy','regime_hmm','kinematics','force_kinematics','energy','density','wavelet',
    'spearman','fractal','texture','cascade','entropy','session','dq','memory','alerts','node'
]
RUNNER_HINTS = {
    'regime_legacy': 'python run_regime_engine_once.py --db powerflow.db --pretty',
    'regime_hmm': 'python run_hmm_regime_engine_once.py --db powerflow.db --pretty',
    'kinematics': 'python run_force_kinematics_once.py --db powerflow.db --symbol GBPUSD --pretty',
    'force_kinematics': 'python run_force_kinematics_once.py --db powerflow.db --symbol GBPUSD --pretty',
    'energy': 'python run_currency_energy_probe_once.py --db powerflow.db --symbol GBPUSD --pretty',
    'density': 'python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty',
    'wavelet': 'python run_wavelet_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty',
    'spearman': 'python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty',
    'fractal': 'python run_fractal_resonance_once.py --db powerflow.db --summary --pretty',
    'texture': 'python run_volatility_texture_once.py --db powerflow.db --summary --pretty',
    'cascade': 'python run_cascade_engine_once.py --pretty',
    'entropy': 'python run_alert_entropy_once.py --pretty',
    'session': 'python run_session_overlay_once.py --pretty',
    'dq': 'python run_data_quality_guard_once.py --db powerflow.db --since 2026-05-11T01:15:00 --tfs 1,5,15 --pretty --output output/data_quality_report.json',
    'memory': 'python run_memory_engine_once.py --db powerflow.db --summary --pretty',
    'alerts': 'python run_behavioral_alert_mapper_once.py --symbol GBPUSD --pretty',
    'node': 'python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 60 --timeframes 1,5,15,30,60 --pretty',
}

def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None

def is_missing_payload(x: Any) -> bool:
    if x is None: return True
    if isinstance(x, dict):
        payload=x.get('payload', x)
        status=str(x.get('freshness') or x.get('status') or '').upper()
        if x.get('_placeholder') is True or status=='MISSING': return True
        if isinstance(payload, dict):
            meaningful=[k for k,v in payload.items() if k not in {'timestamp_utc','freshness','data_age_seconds','timestamp_provenance','_dashboard_surface_meta'} and v not in (None,'',{},[],'MISSING')]
            return len(meaningful)==0
    if isinstance(x, list): return len(x)==0
    return False

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='output/DASHBOARD_OUTPUT_COVERAGE_DOCTOR.md')
    args=ap.parse_args()
    root=Path(args.root)
    rows=[]
    for key in SURFACE_KEYS:
        path=root/'output/dashboard_surface'/f'{key}.json'
        obj=load(path)
        exists=path.exists()
        fresh=str((obj or {}).get('freshness','MISSING')).upper() if isinstance(obj,dict) else 'MISSING'
        prov=str((obj or {}).get('timestamp_provenance','-')) if isinstance(obj,dict) else '-'
        source=str((obj or {}).get('_raw_source','-')) if isinstance(obj,dict) else '-'
        reason='OK'
        if not exists:
            reason='surface file absent'
        elif is_missing_payload(obj):
            reason='no payload available; this is an honest MISSING state'
        elif fresh=='DEGRADED':
            reason='payload exists but source timestamp is absent; surface timestamp protects UI freshness'
        elif fresh=='STALE':
            reason='payload timestamp exists but is older than stale threshold'
        rows.append((key,exists,fresh,prov,source,reason,RUNNER_HINTS.get(key,'')))
    counts={s:sum(1 for r in rows if r[2]==s) for s in ['LIVE','STALE','DEGRADED','MISSING','ERROR']}
    lines=['# DASHBOARD OUTPUT COVERAGE DOCTOR — PowerFlow V7.2','',f'Generated UTC : {datetime.now(timezone.utc).isoformat().replace("+00:00","Z")}', '', '## Summary', '']
    for k,v in counts.items(): lines.append(f'- {k}: {v}')
    lines += ['', '## Interpretation', '', '- MISSING is acceptable when the runtime did not produce that brick output yet.', '- DEGRADED means payload exists but no source UTC timestamp was found.', '- This doctor does not modify the engine and does not write to powerflow.db.', '', '## Surface Coverage', '', '| Brick | Exists | Freshness | Timestamp provenance | Source | Reason | Suggested refresh |', '|---|---:|---|---|---|---|---|']
    for r in rows:
        lines.append('| ' + ' | '.join(str(x).replace('|','/') for x in r) + ' |')
    out=root/args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(f'Dashboard coverage doctor wrote: {out}')
    return 0
if __name__=='__main__': raise SystemExit(main())
