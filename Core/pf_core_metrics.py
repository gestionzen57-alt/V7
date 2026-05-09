import sqlite3
import numpy as np
from typing import Optional, Dict, List, Tuple

DB_PATH = 'powerflow.db'
ALL_DEVISES = ['gbp', 'usd', 'eur', 'jpy', 'cad', 'chf', 'aud', 'nzd']
TF_WINDOWS = {1: 10, 5: 15, 15: 20, 30: 25, 60: 30, 240: 50}
FATIGUE_WINDOWS = {1: 5, 5: 6, 15: 6, 30: 8, 60: 8, 240: 10}
PIC_WINDOW = 10
PIC_SLOPE_THRESHOLD = 2.0
PIC_MIN_AMPLITUDE = 8.0


def get_available_columns(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(force_snapshots)")
    return [r[1] for r in cur.fetchall()]


def get_devise_forces(conn, symbol, tf, bar_time_str, window=20):
    available = get_available_columns(conn)
    devise_cols = []
    for d in ALL_DEVISES:
        col = f'force_{d}'
        if col in available:
            devise_cols.append((d, col))

    if not devise_cols:
        fallback = ['gbp', 'usd', 'eur', 'jpy', 'cad', 'chf', 'aud']
        devise_cols = [(d, f'force_{d}') for d in fallback]

    cols_sql = ', '.join([f'{c} as f_{d}' for d, c in devise_cols])
    sql = f"""
        SELECT strftime('%Y-%m-%d %H:%M', datetime(created_at)) as bt,
               {cols_sql}
        FROM force_snapshots
        WHERE symbol = ? AND timeframe = ?
          AND strftime('%Y-%m-%d %H:%M', datetime(created_at)) <= ?
          AND force_gbp IS NOT NULL
        GROUP BY bt
        ORDER BY bt DESC
        LIMIT ?
    """
    cur = conn.cursor()
    cur.execute(sql, (symbol, tf, bar_time_str, window))
    rows = cur.fetchall()
    rows.reverse()
    return rows, devise_cols


def _get_devise_col_idx(devise, devise_cols):
    devise = devise.lower()
    for idx, (d, _c) in enumerate(devise_cols):
        if d == devise:
            return idx + 1
    return None


def _valid_series(rows, start_idx, end_idx, col_idx):
    start_idx = max(0, start_idx)
    end_idx = min(len(rows) - 1, end_idx)
    if start_idx > end_idx:
        return []
    return [rows[i][col_idx] for i in range(start_idx, end_idx + 1) if rows[i][col_idx] is not None]


def _linear_slope(values):
    if len(values) < 3:
        return None
    x = np.arange(len(values))
    y = np.array(values, dtype=float)
    coeffs = np.polyfit(x, y, 1)
    return float(coeffs[0])


def _angle_from_slope(slope):
    return float(np.degrees(np.arctan(slope / 10.0)))


def calc_provenance(devise, rows, bar_index, devise_cols):
    if len(rows) < 2 or bar_index >= len(rows):
        return {'status': 'N/A', 'note': ''}

    col_idx = _get_devise_col_idx(devise, devise_cols)
    if col_idx is None:
        return {'status': 'N/A', 'note': ''}

    current_val = rows[bar_index][col_idx] if rows[bar_index][col_idx] is not None else 50.0
    first_val = rows[0][col_idx] if rows[0][col_idx] is not None else 50.0
    delta = current_val - first_val

    if first_val < 40:
        zone_origine = 'BAS'
    elif first_val > 70:
        zone_origine = 'HAUT'
    else:
        zone_origine = 'MEDIANE'

    direction = 'MONTANTE' if delta > 0 else 'DESCENDANTE' if delta < 0 else 'PLATE'
    if abs(delta) < 3:
        direction = 'PLATE'

    note = (
        f"{devise.upper()} arrive de {first_val:.1f}"
        f"{' (' + zone_origine + ')' if zone_origine != 'MEDIANE' else ''} "
        f"et {'monte' if delta > 0 else 'descend' if delta < 0 else 'stagne'} "
        f"-> {zone_origine}-{direction}"
    )
    return {
        'devise': devise.upper(),
        'force_debut': round(first_val, 1),
        'force_actuelle': round(current_val, 1),
        'delta_total': round(delta, 1),
        'zone_origine': zone_origine,
        'direction': direction,
        'note': note,
    }


def calc_pente(devise, rows, bar_index, tf, devise_cols):
    if len(rows) < 3 or bar_index >= len(rows):
        return {'status': 'N/A', 'note': 'Pas assez de données'}

    col_idx = _get_devise_col_idx(devise, devise_cols)
    if col_idx is None:
        return {'status': 'N/A', 'note': f'Devise {devise} non disponible'}

    window = TF_WINDOWS.get(tf, 20)
    start_idx = max(0, bar_index - window + 1)
    subset = [r[col_idx] for r in rows[start_idx:bar_index + 1] if r[col_idx] is not None]
    if len(subset) < 3:
        return {'status': 'N/A', 'note': f'Pas assez de valeurs valides (seulement {len(subset)})'}

    try:
        slope = _linear_slope(subset)
        if slope is None:
            return {'status': 'N/A', 'note': 'Pas assez de valeurs valides'}
        delta_total = subset[-1] - subset[0]
        angle = _angle_from_slope(slope)

        if abs(angle) < 0.5:
            direction = 'PLATE'
        elif angle > 0:
            direction = 'HAUT'
        else:
            direction = 'BAS'

        force_pct = min(100, abs(slope) * 5)
        note = f"{devise.upper()}: angle {angle:+.1f}° ({delta_total:+.1f} pts sur {len(subset)}b)"
        return {
            'devise': devise.upper(),
            'angle': round(angle, 1),
            'slope': round(slope, 4),
            'delta_total': round(delta_total, 1),
            'direction': direction,
            'force_pct': round(force_pct, 1),
            'note': note,
        }
    except Exception as e:
        return {'status': 'ERROR', 'note': str(e)}


def detect_fatigue(devise, rows, bar_index, tf, devise_cols):
    """
    Fatigue = chute de puissance entre deux fenetres consecutives.
    Compare [bar-2N : bar-N] vs [bar-N : bar].
    Mesure sur les angles absolus pour capter une perte d'energie,
    quelle que soit la direction de la devise.
    """
    if len(rows) < 6 or bar_index >= len(rows):
        return {'statut': 'N/A', 'angle_ancien': None, 'angle_recent': None, 'chute_pct': None, 'note': ''}

    col_idx = _get_devise_col_idx(devise, devise_cols)
    if col_idx is None:
        return {
            'statut': 'N/A',
            'angle_ancien': None,
            'angle_recent': None,
            'chute_pct': None,
            'note': f'Devise {devise.upper()} non disponible',
        }

    n = FATIGUE_WINDOWS.get(tf, max(5, min(10, TF_WINDOWS.get(tf, 20) // 2)))
    old_start = bar_index - (2 * n) + 1
    old_end = bar_index - n
    recent_start = bar_index - n + 1
    recent_end = bar_index

    old_values = _valid_series(rows, old_start, old_end, col_idx)
    recent_values = _valid_series(rows, recent_start, recent_end, col_idx)

    if len(old_values) < 3 or len(recent_values) < 3:
        return {
            'statut': 'N/A',
            'angle_ancien': None,
            'angle_recent': None,
            'chute_pct': None,
            'note': f'Pas assez de donnees fatigue ({len(old_values)} anciennes / {len(recent_values)} recentes, besoin >=3/3)',
        }

    try:
        old_slope = _linear_slope(old_values)
        recent_slope = _linear_slope(recent_values)
        if old_slope is None or recent_slope is None:
            return {'statut': 'N/A', 'angle_ancien': None, 'angle_recent': None, 'chute_pct': None, 'note': ''}

        old_angle = _angle_from_slope(old_slope)
        recent_angle = _angle_from_slope(recent_slope)
        old_power = abs(old_angle)
        recent_power = abs(recent_angle)

        if old_power < 0.5:
            chute_pct = 0.0 if recent_power >= old_power else 100.0
        else:
            chute_pct = max(0.0, ((old_power - recent_power) / old_power) * 100.0)

        if chute_pct > 50.0:
            statut = 'FATIGUE_FORTE'
        elif chute_pct >= 25.0:
            statut = 'FATIGUE_NAISSANTE'
        else:
            statut = 'ENERGIE_STABLE'

        note = (
            f"{devise.upper()} fatigue: ancien {old_angle:+.1f}° -> recent {recent_angle:+.1f}° "
            f"| chute {chute_pct:.0f}% | {statut}"
        )
        return {
            'statut': statut,
            'angle_ancien': round(old_angle, 1),
            'angle_recent': round(recent_angle, 1),
            'chute_pct': round(chute_pct, 1),
            'note': note,
        }
    except Exception as e:
        return {'statut': 'ERROR', 'angle_ancien': None, 'angle_recent': None, 'chute_pct': None, 'note': str(e)}


def detect_pic(devise, rows, bar_index, devise_cols):
    """
    PIC_HAUSSIER = montee brutale puis rechute.
    PIC_BAISSIER = chute brutale puis reprise.
    Critere: slopes opposees et fortes + amplitude totale > 8 pts.
    """
    if len(rows) < 5 or bar_index >= len(rows):
        return {'detecte': False, 'type': '', 'amplitude': 0.0, 'note': ''}

    col_idx = _get_devise_col_idx(devise, devise_cols)
    if col_idx is None:
        return {'detecte': False, 'type': '', 'amplitude': 0.0, 'note': f'Devise {devise.upper()} non disponible'}

    start_idx = max(0, bar_index - PIC_WINDOW + 1)
    subset = [r[col_idx] for r in rows[start_idx:bar_index + 1] if r[col_idx] is not None]
    if len(subset) < 5:
        return {'detecte': False, 'type': '', 'amplitude': 0.0, 'note': ''}

    mid = len(subset) // 2
    first_half = subset[:mid]
    second_half = subset[mid:]
    if len(first_half) < 2 or len(second_half) < 2:
        return {'detecte': False, 'type': '', 'amplitude': 0.0, 'note': ''}

    try:
        slope1 = (first_half[-1] - first_half[0]) / max(1, len(first_half) - 1)
        slope2 = (second_half[-1] - second_half[0]) / max(1, len(second_half) - 1)
        amplitude = max(subset) - min(subset)

        if slope1 > PIC_SLOPE_THRESHOLD and slope2 < -PIC_SLOPE_THRESHOLD and amplitude > PIC_MIN_AMPLITUDE:
            note = (
                f"PIC_HAUSSIER {devise.upper()}: montee brutale puis rechute | "
                f"slope {slope1:+.2f}->{slope2:+.2f} pts/b | amplitude {amplitude:.1f}pts"
            )
            return {
                'detecte': True,
                'type': 'PIC_HAUSSIER',
                'amplitude': round(amplitude, 1),
                'slope1': round(slope1, 2),
                'slope2': round(slope2, 2),
                'note': note,
            }

        if slope1 < -PIC_SLOPE_THRESHOLD and slope2 > PIC_SLOPE_THRESHOLD and amplitude > PIC_MIN_AMPLITUDE:
            note = (
                f"PIC_BAISSIER {devise.upper()}: chute brutale puis reprise | "
                f"slope {slope1:+.2f}->{slope2:+.2f} pts/b | amplitude {amplitude:.1f}pts"
            )
            return {
                'detecte': True,
                'type': 'PIC_BAISSIER',
                'amplitude': round(amplitude, 1),
                'slope1': round(slope1, 2),
                'slope2': round(slope2, 2),
                'note': note,
            }

        return {
            'detecte': False,
            'type': '',
            'amplitude': round(amplitude, 1),
            'slope1': round(slope1, 2),
            'slope2': round(slope2, 2),
            'note': '',
        }
    except Exception as e:
        return {'detecte': False, 'type': 'ERROR', 'amplitude': 0.0, 'note': str(e)}


def detect_courbure(devise, rows, bar_index, devise_cols):
    if len(rows) < 5 or bar_index >= len(rows):
        return {'status': 'N/A', 'note': '', 'confirm': ''}

    col_idx = _get_devise_col_idx(devise, devise_cols)
    if col_idx is None:
        return {'status': 'N/A', 'note': '', 'confirm': ''}

    pic = detect_pic(devise, rows, bar_index, devise_cols)
    if pic.get('detecte'):
        return {
            'devise': devise.upper(),
            'courbure': 'DELEGUEE_A_DETECT_PIC',
            'slope1': pic.get('slope1'),
            'slope2': pic.get('slope2'),
            'confirm': '',
            'note': 'Rupture brutale exclue de detect_courbure()',
        }

    window = 10
    start_idx = max(0, bar_index - window + 1)
    subset = [r[col_idx] for r in rows[start_idx:bar_index + 1] if r[col_idx] is not None]
    if len(subset) < 5:
        return {'status': 'N/A', 'note': '', 'confirm': ''}

    mid = len(subset) // 2
    first_half = subset[:mid]
    second_half = subset[mid:]

    try:
        slope1 = (first_half[-1] - first_half[0]) / max(1, len(first_half) - 1)
        slope2 = (second_half[-1] - second_half[0]) / max(1, len(second_half) - 1)
    except Exception:
        return {'status': 'ERROR', 'note': '', 'confirm': ''}

    if slope1 > 0 and slope2 < 0:
        courbure = 'BOSSE'
        confirm = f"Monte puis descend : {first_half[0]:.1f}->{first_half[-1]:.1f}->{second_half[-1]:.1f}"
    elif slope1 < 0 and slope2 > 0:
        courbure = 'CREUX'
        confirm = f"Descend puis remonte : {first_half[0]:.1f}->{first_half[-1]:.1f}->{second_half[-1]:.1f}"
    else:
        courbure = 'PLATE'
        confirm = f"Pente reguliere : {slope1:+.2f} -> {slope2:+.2f} pts/b"

    return {
        'devise': devise.upper(),
        'courbure': courbure,
        'slope1': round(slope1, 2),
        'slope2': round(slope2, 2),
        'confirm': confirm,
    }


def detect_coalition(devise_a, devise_b, contre, rows, bar_index, tf, devise_cols):
    if len(rows) < 3 or bar_index >= len(rows):
        return {'status': 'N/A', 'note': '', 'score': 'N/A'}

    pente_a = calc_pente(devise_a, rows, bar_index, tf, devise_cols)
    pente_b = calc_pente(devise_b, rows, bar_index, tf, devise_cols)
    pente_c = calc_pente(contre, rows, bar_index, tf, devise_cols)
    if pente_a.get('status') == 'N/A' or pente_b.get('status') == 'N/A' or pente_c.get('status') == 'N/A':
        return {'status': 'N/A', 'note': 'Donnees insuffisantes pour la coalition', 'score': 'N/A'}

    angle_a = pente_a.get('angle', 0)
    angle_b = pente_b.get('angle', 0)
    angle_c = pente_c.get('angle', 0)
    same_sign = (angle_a > 0 and angle_b > 0) or (angle_a < 0 and angle_b < 0)
    opposite = (angle_c < 0 and same_sign and angle_a > 0) or (angle_c > 0 and same_sign and angle_a < 0)

    if same_sign and opposite:
        angle_diff = abs(angle_a - angle_b)
        if angle_diff < 3:
            score = 'FORTE'
            note = f"{devise_a.upper()}+{devise_b.upper()} synchro (angles {angle_a:+.1f}°/{angle_b:+.1f}°) vs {contre.upper()} ({angle_c:+.1f}°) - coalition PARFAITE"
        else:
            score = 'MOYENNE'
            note = f"{devise_a.upper()}+{devise_b.upper()} alignees mais ecart {angle_diff:.1f}° - coalition PARTIELLE"
    elif same_sign:
        score = 'FAIBLE'
        note = f"{devise_a.upper()}+{devise_b.upper()} meme direction mais {contre.upper()} aussi - pas de coalition claire"
    else:
        score = 'AUCUNE'
        note = f"{devise_a.upper()} et {devise_b.upper()} divergent - pas de coalition"

    return {
        'devise_a': devise_a.upper(),
        'devise_b': devise_b.upper(),
        'contre': contre.upper(),
        'angle_a': round(angle_a, 1),
        'angle_b': round(angle_b, 1),
        'angle_contre': round(angle_c, 1),
        'score': score,
        'note': note,
    }


def detect_cross_triple(devise_a, devise_b, devise_c, rows, bar_index, devise_cols):
    if len(rows) < 2 or bar_index >= len(rows):
        return {'status': 'N/A', 'note': '', 'detecte': False}

    col_a = _get_devise_col_idx(devise_a, devise_cols)
    col_b = _get_devise_col_idx(devise_b, devise_cols)
    col_c = _get_devise_col_idx(devise_c, devise_cols)
    if None in (col_a, col_b, col_c):
        return {'status': 'N/A', 'note': 'Une devise non disponible', 'detecte': False}

    val_a = rows[bar_index][col_a]
    val_b = rows[bar_index][col_b]
    val_c = rows[bar_index][col_c]
    if None in (val_a, val_b, val_c):
        return {'status': 'N/A', 'note': 'Valeurs manquantes', 'detecte': False}

    marge = 3.0
    if abs(val_a - val_b) <= marge and abs(val_b - val_c) <= marge:
        ecart_max = max(abs(val_a - val_b), abs(val_b - val_c), abs(val_a - val_c))
        avg_val = (val_a + val_b + val_c) / 3
        note = (
            f"TRIPLE NODE {devise_a.upper()}/{devise_b.upper()}/{devise_c.upper()} : "
            f"toutes a ~{avg_val:.1f} (+/-{ecart_max:.1f}pts) - alignement de flux"
        )
        return {
            'detecte': True,
            'type': 'CROSS_TRIPLE',
            'valeurs': {
                devise_a.upper(): round(val_a, 1),
                devise_b.upper(): round(val_b, 1),
                devise_c.upper(): round(val_c, 1),
            },
            'ecart_max': round(ecart_max, 1),
            'note': note,
        }
    return {'detecte': False, 'note': '', 'type': ''}


def produce_report(symbol, tf, h_start, h_end, date='2026-04-29', core_devise='eur', coalition_a='eur', coalition_b='gbp', contre='usd'):
    conn = sqlite3.connect(DB_PATH)
    rows, devise_cols = get_devise_forces(conn, symbol, tf, f"{date} {h_end - 1:02d}:59:59", window=120)
    print(f"Colonnes DB detectees: {[d for d, _c in devise_cols]} | Total bougies: {len(rows)}")
    if not rows:
        print("Aucune donnee trouvee en DB pour cette periode.")
        conn.close()
        return

    print("=" * 70)
    print("  PowerFlow V5 Core - Rapport de lecture structurelle")
    print(f"  {symbol} | M{tf} | {date} | {h_start:02d}:00->{h_end:02d}:00 broker")
    print("=" * 70)
    print()

    for i, row in enumerate(rows):
        bar_time = row[0]
        provenance = calc_provenance(core_devise, rows, i, devise_cols)
        pente = calc_pente(core_devise, rows, i, tf, devise_cols)
        fatigue = detect_fatigue(core_devise, rows, i, tf, devise_cols)
        pic = detect_pic(core_devise, rows, i, devise_cols)
        courbure = detect_courbure(core_devise, rows, i, devise_cols)
        coalition = detect_coalition(coalition_a, coalition_b, contre, rows, i, tf, devise_cols)
        cross = detect_cross_triple(coalition_a, contre, coalition_b, rows, i, devise_cols)

        print(f"[{bar_time}] {core_devise.upper()}: {pente.get('note', 'N/A')}")
        if provenance.get('note'):
            print(f"  Provenance: {provenance['note']}")
        if fatigue.get('statut') not in ('N/A', None):
            print(f"  Fatigue: {fatigue['note']}")
        if pic.get('detecte'):
            print(f"  PIC: {pic['note']}")
        if courbure.get('confirm'):
            print(f"  Courbure: {courbure['courbure']} - {courbure['confirm']}")
        if coalition.get('score') and coalition['score'] not in ('AUCUNE', 'N/A'):
            print(f"  Coalition: {coalition['note']}")
        if cross.get('detecte'):
            print(f"  >>> {cross['note']} <<<")
        print()

    print("=" * 70)
    print("FIN DU RAPPORT")
    print("=" * 70)
    conn.close()


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 6:
        print("Usage: python detect_v5_core.py GBPUSD 15 2026-04-29 09 13")
        sys.exit(1)

    sym = sys.argv[1].upper()
    tf = int(sys.argv[2])
    run_date = sys.argv[3]
    h_start = int(sys.argv[4])
    h_end = int(sys.argv[5])
    produce_report(sym, tf, h_start, h_end, date=run_date)
