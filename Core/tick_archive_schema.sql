PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=250;

CREATE TABLE IF NOT EXISTS tick_stream (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    symbol TEXT NOT NULL,

    -- UTC timestamps
    ts_utc TEXT NOT NULL,
    ts_epoch_ms INTEGER NOT NULL,

    bid REAL NOT NULL,
    ask REAL NOT NULL,
    mid REAL NOT NULL,
    spread REAL NOT NULL,

    tick_volume INTEGER,

    -- CRITICAL: distinguish source
    source TEXT NOT NULL DEFAULT 'mt4',
    source_mode TEXT NOT NULL DEFAULT 'TIMER_1S_SAMPLE',

    -- Allow several ticks in the same millisecond
    capture_seq INTEGER NOT NULL DEFAULT 0,

    -- Data visibility
    gap_ms INTEGER,
    quality_flags TEXT NOT NULL DEFAULT '[]',

    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (bid > 0),
    CHECK (ask > 0),
    CHECK (ask >= bid),
    CHECK (mid > 0),
    CHECK (spread >= 0),
    CHECK (source_mode IN ('ONTICK_RAW', 'TIMER_1S_SAMPLE', 'M1_BAR_PROXY'))
);

CREATE INDEX IF NOT EXISTS idx_tick_stream_symbol_epoch
ON tick_stream(symbol, ts_epoch_ms);

CREATE INDEX IF NOT EXISTS idx_tick_stream_created
ON tick_stream(created_at_utc);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tick_unique
ON tick_stream(symbol, ts_epoch_ms, capture_seq, source);

CREATE TABLE IF NOT EXISTS tick_archive_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    source_mode TEXT NOT NULL,
    data_start_utc TEXT,
    data_end_utc TEXT,
    tick_count INTEGER,
    file_size_mb REAL,
    last_rotation_utc TEXT,
    last_purge_utc TEXT,
    status TEXT DEFAULT 'ACTIVE',
    created_at_utc TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tick_rotation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    rotation_time_utc TEXT,
    old_file TEXT,
    new_file TEXT,
    tick_count_archived INTEGER,
    size_mb REAL,
    created_at_utc TEXT DEFAULT CURRENT_TIMESTAMP
);
