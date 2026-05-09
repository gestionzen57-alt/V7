"""
PowerFlow V4.1 — detect_nodes_v6.py
Ajout V6 : CROISEMENT (double et triple)

CROISEMENT_DOUBLE : 2 devises échangent leur position en 1-2 bougies
CROISEMENT_TRIPLE : 3 devises se croisent au même point (signal fort)

Règle de détection :
- Bougie N   : dev_A > dev_B
- Bougie N+1 : dev_A < dev_B
→ CROISEMENT entre A et B

Triple : A croise B ET A croise C (ou B croise C) dans la même bougie
"""
import sqlite3

DB_PATH = "powerflow.db"

COMPRESSION_THRESHOLD = 13.0
COMPRESSION_MIN_BARS  = 3
LIBERATION_THRESHOLD  = 15.0
LIBERATION_MAX_BARS   = 40
PENTE_THRESHOLD       = 3.0
LOCK_DOMINANT_MIN     = 75.0
LOCK_OTHERS_MAX       = 60.0
LOCK_MIN_BARS         = 3
CROSS_MIN_DELTA       = 3.0   # écart minimum pour qualifier un vrai croisement (éviter le bruit)

SYMBOLS    = ["GBPUSD", "EURUSD", "GBPJPY", "USDJPY", "EURGBP"]
TIMEFRAMES = [5, 15, 30, 60, 240]
TF_NAMES   = {5:"M5", 15:"M15", 30:"M30", 60:"H1", 240:"H4"}


def init_table(conn):
    conn.execute("DROP TABLE IF EXISTS nodes_v6")
    conn.execute("""
        CREATE TABLE nodes_v6 (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            detected_at    TEXT NOT NULL,
            symbol         TEXT NOT NULL,
            timeframe      INTEGER NOT NULL,
            node_type      TEXT NOT NULL,
            dev_a          TEXT,
            dev_b          TEXT,
            dev_c          TEXT,
            ecart_max      REAL,
            delta          REAL,
            direction      TEXT,
            pente          TEXT,
            bars_count     INTEGER,
            bars_after     INTEGER,
            linked_node_id INTEGER,
            note           TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nv6_sym_tf ON nodes_v6(symbol, timeframe)")
    conn.commit()


def get_bars(conn, symbol, timeframe):
    cur = conn.execute("""
        SELECT
            strftime('%Y-%m-%dT%H:', created_at) ||
            printf('%02d', (CAST(strftime('%M', created_at) AS INTEGER) / ?) * ?) || ':00' AS bar_time,
            AVG(force_gbp) AS gbp,
            AVG(force_usd) AS usd,
            AVG(force_eur) AS eur,
            AVG(force_jpy) AS jpy
        FROM force_snapshots
        WHERE symbol=? AND timeframe=?
          AND force_gbp IS NOT NULL
          AND force_usd IS NOT NULL
          AND force_eur IS NOT NULL
        GROUP BY bar_time
        ORDER BY bar_time
    """, (timeframe, timeframe, symbol, timeframe))
    return cur.fetchall()


def calc_pente(comp_bars):
    if len(comp_bars) < 2:
        return "PLATE"
    f, l = comp_bars[0], comp_bars[-1]
    avg = ((l[1]-f[1]) + (l[2]-f[2]) + (l[3]-f[3])) / 3
    if avg < -PENTE_THRESHOLD: return "DESCENDANTE"
    if avg >  PENTE_THRESHOLD: return "MONTANTE"
    return "PLATE"


def detect_crossings(bars):
    """
    Détecte les croisements entre GBP, USD, EUR bougie par bougie.
    Retourne liste de (bar_time, type, dev_a, dev_b, dev_c, note)
    """
    crossings = []
    cross_done = set()  # éviter doublons sur même timestamp

    pairs = [("gbp", "usd"), ("gbp", "eur"), ("usd", "eur")]
    idx   = {"gbp": 1, "usd": 2, "eur": 3}

    for i in range(1, len(bars)):
        prev = bars[i-1]
        curr = bars[i]
        bar_time = curr[0]

        if bar_time in cross_done:
            continue

        crossed_pairs = []

        for dev_a, dev_b in pairs:
            va_prev = prev[idx[dev_a]]
            vb_prev = prev[idx[dev_b]]
            va_curr = curr[idx[dev_a]]
            vb_curr = curr[idx[dev_b]]

            if None in (va_prev, vb_prev, va_curr, vb_curr):
                continue

            # Vérifier inversion de position
            was_above = va_prev > vb_prev
            is_above  = va_curr > vb_curr

            if was_above != is_above:
                # Delta minimum pour filtrer le bruit
                delta = abs(va_curr - vb_curr)
                if delta >= CROSS_MIN_DELTA:
                    crossed_pairs.append((dev_a, dev_b, delta))

        if len(crossed_pairs) == 0:
            continue

        if len(crossed_pairs) >= 2:
            # TRIPLE CROISEMENT — plusieurs paires se croisent en même temps
            devs = set()
            for dp in crossed_pairs:
                devs.add(dp[0]); devs.add(dp[1])

            devs = list(devs)
            vals_curr = {d: curr[idx[d]] for d in devs}
            note = (f"TRIPLE CROSS : "
                    f"{' + '.join(f'{a.upper()}/{b.upper()}' for a,b,_ in crossed_pairs)} | "
                    f"valeurs: {' '.join(f'{d.upper()}={vals_curr[d]:.1f}' for d in sorted(devs))}")

            crossings.append((
                bar_time, "CROISEMENT_TRIPLE",
                devs[0] if len(devs) > 0 else None,
                devs[1] if len(devs) > 1 else None,
                devs[2] if len(devs) > 2 else None,
                note
            ))
            cross_done.add(bar_time)

        elif len(crossed_pairs) == 1:
            dev_a, dev_b, delta = crossed_pairs[0]
            va = curr[idx[dev_a]]
            vb = curr[idx[dev_b]]
            # Qui est au-dessus maintenant ?
            leader = dev_a if va > vb else dev_b
            follower = dev_b if va > vb else dev_a
            note = (f"CROSS {dev_a.upper()}/{dev_b.upper()} | "
                    f"{leader.upper()} prend le dessus | "
                    f"Δ={delta:.1f}pts | "
                    f"{dev_a.upper()}={va:.1f} {dev_b.upper()}={vb:.1f}")

            crossings.append((
                bar_time, "CROISEMENT_DOUBLE",
                dev_a, dev_b, None, note
            ))
            cross_done.add(bar_time)

    return crossings


def detect(conn, symbol, timeframe):
    bars = get_bars(conn, symbol, timeframe)
    if len(bars) < COMPRESSION_MIN_BARS:
        return 0

    nodes = 0
    liberation_done = set()
    cross_done_global = set()

    # === CROISEMENTS ===
    crossings = detect_crossings(bars)
    for cross in crossings:
        bar_time, ctype, da, db, dc, note = cross
        conn.execute("""
            INSERT INTO nodes_v6
            (detected_at, symbol, timeframe, node_type,
             dev_a, dev_b, dev_c, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (bar_time, symbol, timeframe, ctype, da, db, dc, note))
        nodes += 1
    conn.commit()

    # === LOCK ===
    lock_streak = 0
    lock_dev    = None
    lock_start  = None
    lock_note   = ""

    for i, bar in enumerate(bars):
        bar_time, gbp, usd, eur, jpy = bar
        gbp = gbp or 0; usd = usd or 0
        eur = eur or 0; jpy = jpy or 0
        vals = {"gbp": gbp, "usd": usd, "eur": eur, "jpy": jpy}

        dominant = None
        dominant_val = 0
        for dev, val in vals.items():
            if val >= LOCK_DOMINANT_MIN and val > dominant_val:
                others_max = max(v for k, v in vals.items() if k != dev)
                if others_max <= LOCK_OTHERS_MAX:
                    dominant = dev
                    dominant_val = val

        if dominant:
            if lock_dev == dominant:
                lock_streak += 1
            else:
                if lock_streak >= LOCK_MIN_BARS and lock_dev:
                    conn.execute("""
                        INSERT INTO nodes_v6
                        (detected_at, symbol, timeframe, node_type,
                         dev_a, bars_count, note)
                        VALUES (?, ?, ?, 'LOCK', ?, ?, ?)
                    """, (lock_start, symbol, timeframe,
                          lock_dev, lock_streak, lock_note))
                    conn.commit()
                    nodes += 1
                lock_streak = 1
                lock_dev    = dominant
                lock_start  = bar_time
                others_str  = " ".join(
                    f"{k.upper()}={v:.0f}"
                    for k, v in vals.items() if k != dominant
                )
                lock_note = (f"LOCK {dominant.upper()}={dominant_val:.0f} "
                             f"autres:[{others_str}]")
        else:
            if lock_streak >= LOCK_MIN_BARS and lock_dev:
                conn.execute("""
                    INSERT INTO nodes_v6
                    (detected_at, symbol, timeframe, node_type,
                     dev_a, bars_count, note)
                    VALUES (?, ?, ?, 'LOCK', ?, ?, ?)
                """, (lock_start, symbol, timeframe,
                      lock_dev, lock_streak, lock_note))
                conn.commit()
                nodes += 1
            lock_streak = 0; lock_dev = None

    if lock_streak >= LOCK_MIN_BARS and lock_dev:
        conn.execute("""
            INSERT INTO nodes_v6
            (detected_at, symbol, timeframe, node_type,
             dev_a, bars_count, note)
            VALUES (?, ?, ?, 'LOCK', ?, ?, ?)
        """, (lock_start, symbol, timeframe,
              lock_dev, lock_streak, lock_note + " [fin période]"))
        conn.commit()
        nodes += 1

    # === COMPRESSION + LIBERATION ===
    streak = 0; in_comp = False
    comp_id = None; comp_streak = 0; comp_bars = []

    for i, bar in enumerate(bars):
        bar_time, gbp, usd, eur, jpy = bar
        if None in (gbp, usd, eur):
            streak = 0; in_comp = False; comp_bars = []; continue

        ecart = max(gbp, usd, eur) - min(gbp, usd, eur)

        if ecart < COMPRESSION_THRESHOLD:
            streak += 1
            comp_bars.append(bar)

            if streak == COMPRESSION_MIN_BARS and not in_comp:
                in_comp = True; comp_streak = streak
                pente = calc_pente(comp_bars)
                cur2 = conn.execute("""
                    INSERT INTO nodes_v6
                    (detected_at, symbol, timeframe, node_type,
                     dev_a, ecart_max, pente, bars_count, note)
                    VALUES (?, ?, ?, 'COMPRESSION', 'gbp/usd/eur', ?, ?, ?, ?)
                """, (bar_time, symbol, timeframe,
                      round(ecart, 2), pente, streak,
                      f"GBP={gbp:.1f} USD={usd:.1f} EUR={eur:.1f} "
                      f"écart={ecart:.1f}pts pente={pente}"))
                comp_id = cur2.lastrowid
                conn.commit(); nodes += 1
            elif in_comp:
                comp_streak = streak

        else:
            if in_comp:
                pente_finale = calc_pente(comp_bars)
                for j in range(i, min(i + LIBERATION_MAX_BARS, len(bars))):
                    if j == 0: continue
                    t2, g2, u2, e2, _ = bars[j]
                    t1, g1, u1, e1, _ = bars[j-1]
                    if None in (g2, u2, e2, g1, u1, e1): continue
                    if t2 in liberation_done: continue

                    d = {"gbp": abs(g2-g1), "usd": abs(u2-u1), "eur": abs(e2-e1)}
                    dev = max(d, key=d.get); delta = d[dev]

                    if delta >= LIBERATION_THRESHOLD:
                        bars_after = j - i + 1
                        pv = {"gbp": g1, "usd": u1, "eur": e1}
                        cv = {"gbp": g2, "usd": u2, "eur": e2}
                        direction = "HAUSSE" if cv[dev] > pv[dev] else "BAISSE"
                        conn.execute("""
                            INSERT INTO nodes_v6
                            (detected_at, symbol, timeframe, node_type,
                             dev_a, delta, direction, pente,
                             bars_count, bars_after, linked_node_id, note)
                            VALUES (?, ?, ?, 'LIBERATION', ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (t2, symbol, timeframe,
                              dev, round(delta, 2), direction, pente_finale,
                              comp_streak, bars_after, comp_id,
                              f"{dev.upper()} Δ{delta:.1f}pts {direction} | "
                              f"{bars_after}b après compression {pente_finale} ({comp_streak}b)"))
                        conn.commit()
                        liberation_done.add(t2); nodes += 1
                        break

            streak = 0; in_comp = False; comp_id = None; comp_bars = []

    return nodes


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_table(conn)

    total = 0
    for sym in SYMBOLS:
        for tf in TIMEFRAMES:
            n = detect(conn, sym, tf)
            if n:
                print(f"  {sym} {TF_NAMES.get(tf,str(tf))} → {n} nœuds")
                total += n
    print(f"\n✅ Total : {total} nœuds\n")

    print("=== GBPUSD M15 — film complet ===")
    cur = conn.execute("""
        SELECT detected_at, node_type, dev_a, dev_b, dev_c,
               ecart_max, delta, direction, pente,
               bars_count, bars_after, linked_node_id, note
        FROM nodes_v6
        WHERE symbol='GBPUSD' AND timeframe=15
        ORDER BY detected_at
    """)
    for r in cur.fetchall():
        h = r[0][11:16]
        if r[1] == 'LOCK':
            print(f"  {h} | 🔒 LOCK              | {r[2].upper()} dominant | {r[9]}b")
        elif r[1] == 'COMPRESSION':
            print(f"  {h} | 🗜  COMPRESSION       | pente={r[8]:12} | écart={r[5]}pts | {r[9]}b")
        elif r[1] == 'LIBERATION':
            print(f"  {h} | ⚡ LIBERATION        | {r[2].upper()} Δ{r[6]}pts {r[7]:6} | {r[10]}b après [#{r[11]}]")
        elif r[1] == 'CROISEMENT_TRIPLE':
            print(f"  {h} | 🔥 CROSS TRIPLE      | {r[2].upper()}/{r[3].upper()}/{(r[4] or '?').upper()} | {r[12][:60]}")
        elif r[1] == 'CROISEMENT_DOUBLE':
            print(f"  {h} | ✂️  CROSS DOUBLE      | {r[2].upper()}/{r[3].upper()} | {r[12][:60]}")

    print()
    print("=== CROISEMENTS TRIPLES — tous symboles M15 ===")
    cur = conn.execute("""
        SELECT detected_at, symbol, node_type, dev_a, dev_b, dev_c, note
        FROM nodes_v6
        WHERE timeframe=15 AND node_type='CROISEMENT_TRIPLE'
        ORDER BY detected_at
    """)
    for r in cur.fetchall():
        print(f"  {r[0][11:16]} | {r[1]:8} | 🔥 {r[3].upper()}/{r[4].upper()}/{(r[5] or '?').upper()} | {r[6][:70]}")

    conn.close()


if __name__ == "__main__":
    run()
