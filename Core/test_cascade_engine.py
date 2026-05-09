import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pf_cascade_engine import evaluate_cascade


def write_queue(path: Path, events):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(events), encoding='utf-8')


def test_high_counts_hot_events_in_last_five_minutes(tmp_path):
    base = datetime(2026, 5, 9, 9, 0, tzinfo=timezone.utc)
    q = tmp_path / 'output' / 'behavioral_alert_queue.json'
    write_queue(q, [
        {'severity': 'HOT', 'timestamp': (base - timedelta(minutes=1)).isoformat()},
        {'alert_level': 'HOT', 'created_at': (base - timedelta(minutes=2)).isoformat()},
        {'level': 'HOT', 'ts': base.isoformat()},
        {'severity': 'WATCH', 'timestamp': base.isoformat()},
        {'severity': 'HOT', 'timestamp': (base - timedelta(minutes=6)).isoformat()},
    ])
    assert evaluate_cascade(q) == {
        'cascade_state': 'SEQUENCE_VELOCITY_HIGH',
        'events_count': 3,
        'window_minutes': 5,
        'cascade_building': True,
    }


def test_medium_two_hot_events_dict_alerts(tmp_path):
    base = datetime(2026, 5, 9, 9, 0, tzinfo=timezone.utc)
    q = tmp_path / 'output' / 'behavioral_alert_queue.json'
    write_queue(q, {'alerts': [
        {'state': 'HOT', 'time': (base - timedelta(minutes=5)).isoformat()},
        {'state': 'HOT', 'time': base.isoformat()},
    ]})
    assert evaluate_cascade(q)['cascade_state'] == 'SEQUENCE_VELOCITY_MEDIUM'
    assert evaluate_cascade(q)['events_count'] == 2
    assert evaluate_cascade(q)['cascade_building'] is True


def test_low_one_or_missing_queue(tmp_path):
    q = tmp_path / 'output' / 'behavioral_alert_queue.json'
    write_queue(q, [{'severity': 'HOT', 'timestamp': '2026-05-09T09:00:00Z'}])
    assert evaluate_cascade(q)['cascade_state'] == 'SEQUENCE_VELOCITY_LOW'
    assert evaluate_cascade(tmp_path / 'missing.json')['events_count'] == 0
