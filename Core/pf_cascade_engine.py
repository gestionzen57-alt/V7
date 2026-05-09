import json
from datetime import datetime, timedelta, timezone
WINDOW_MINUTES = 5
def _events(data):
    return (data.get('events') or data.get('alerts') or data.get('queue') or []) if isinstance(data, dict) else data

def _parse_ts(value):
    if not value: return None
    if isinstance(value, (int, float)): return datetime.fromtimestamp(value, timezone.utc)
    return datetime.fromisoformat(str(value).replace('Z', '+00:00'))

def evaluate_cascade(path='output/behavioral_alert_queue.json'):
    try: rows = _events(json.load(open(path, encoding='utf-8')))
    except Exception: rows = []
    hot = [e for e in rows if str((e or {}).get('severity') or (e or {}).get('alert_level') or (e or {}).get('level') or (e or {}).get('state')).upper() == 'HOT']
    stamps = [_parse_ts((e or {}).get('timestamp') or (e or {}).get('created_at') or (e or {}).get('ts') or (e or {}).get('time')) for e in hot]
    anchor = max([s for s in stamps if s], default=datetime.now(timezone.utc))
    count = sum(1 for s in stamps if s and anchor - s <= timedelta(minutes=WINDOW_MINUTES)) + sum(1 for s in stamps if not s)
    state = 'HIGH' if count >= 3 else 'MEDIUM' if count == 2 else 'LOW'
    return {'cascade_state': f'SEQUENCE_VELOCITY_{state}', 'events_count': count, 'window_minutes': WINDOW_MINUTES, 'cascade_building': count >= 2}
