"""
PowerFlow Multidevise Context Module
=====================================

Brique unifiee pour contexte relationnel multi-devises.

RESPONSABILITE:
  - Lire force_snapshots_v2 (13 symboles FX cohort)
  - Calculer baskets GBP/USD (scores bruts, pas interpretation)
  - Detecter patterns coalition/opposition
  - Evaluer coverage/alignment/freshness
  - Exposer contexte qualifie avec limits explicites

HORS SCOPE (interdits):
  - Decider GBP fort vs USD faible (interpretatif)
  - Valider/invalider scene B9
  - Emettre signal trade (BUY/SELL)
  - Ecriture DB (powerflow.db / tick_archive.db)
  - Auto-update dashboard
  - Auto-send Telegram

Version: V1.0
Schema: MULTIDEVISE_CONTEXT_V1
"""

import sqlite3
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================================
# CONSTANTS
# ============================================================================

ALL_SYMBOLS = [
    'GBPUSD', 'EURUSD', 'AUDUSD', 'NZDUSD',
    'USDJPY', 'USDCAD', 'USDCHF',
    'EURGBP', 'GBPJPY', 'GBPAUD', 'GBPCAD',
    'GBPCHF', 'GBPNZD'
]

GBP_BASKET_SYMBOLS = [
    'GBPUSD', 'GBPJPY', 'GBPCHF', 'GBPCAD',
    'GBPAUD', 'GBPNZD', 'EURGBP'
]

USD_BASKET_SYMBOLS = [
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF',
    'USDCAD', 'AUDUSD', 'NZDUSD'
]

COALITION_USD_QUOTE = ['GBPUSD', 'EURUSD', 'AUDUSD', 'NZDUSD']
OPPOSITION_USD_BASE = ['USDJPY', 'USDCAD', 'USDCHF']

DIRECTION_THRESHOLD_UP = 0.1
DIRECTION_THRESHOLD_DOWN = -0.1

ALIGNMENT_THRESHOLD_ALIGNED = 60
ALIGNMENT_THRESHOLD_PARTIAL = 120

FRESHNESS_THRESHOLD_LIVE = 2
FRESHNESS_THRESHOLD_STALE = 5

COVERAGE_THRESHOLD_FULL = 0.8
COVERAGE_THRESHOLD_PARTIAL = 0.5
COVERAGE_THRESHOLD_THIN = 0.3


# ============================================================================
# ENUMS
# ============================================================================

class CoverageState(Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    THIN = "THIN"
    BLIND = "BLIND"


class AlignmentState(Enum):
    ALIGNED = "ALIGNED"
    PARTIAL = "PARTIAL"
    DEGRADED = "DEGRADED"


class FreshnessState(Enum):
    LIVE = "LIVE"
    DELAYED = "DELAYED"
    STALE = "STALE"


class ConfidenceCap(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class BasketScore:
    currency: str
    required_symbols: List[str]
    available_symbols: List[str]
    missing_symbols: List[str]
    direction_up_count: int = 0
    direction_down_count: int = 0
    direction_neutral_count: int = 0


@dataclass
class CoalitionPattern:
    pattern_type: str = "USD_QUOTE_COALITION"
    symbols_in_pattern: List[str] = field(default_factory=list)
    aligned_count: int = 0
    opposed_count: int = 0
    all_aligned_up: bool = False
    all_aligned_down: bool = False
    mixed: bool = False


@dataclass
class OppositionPattern:
    pattern_type: str = "USD_BASE_OPPOSITION"
    symbols_in_pattern: List[str] = field(default_factory=list)
    aligned_count: int = 0
    opposed_count: int = 0
    all_aligned_up: bool = False
    all_aligned_down: bool = False
    mixed: bool = False


@dataclass
class MultideviseContext:
    symbol_local: str
    timestamp_utc: str
    computed_at_utc: str
    schema_version: str = "MULTIDEVISE_CONTEXT_V1"

    coverage: CoverageState = CoverageState.BLIND
    coverage_ratio: float = 0.0
    symbols_available: List[str] = field(default_factory=list)
    symbols_missing: List[str] = field(default_factory=list)
    symbols_stale: List[str] = field(default_factory=list)

    alignment: AlignmentState = AlignmentState.DEGRADED
    aligned_symbols: List[str] = field(default_factory=list)
    max_skew_seconds: Optional[int] = None

    gbp_basket: Optional[BasketScore] = None
    usd_basket: Optional[BasketScore] = None

    coalition_usd_quote: Optional[CoalitionPattern] = None
    opposition_usd_base: Optional[OppositionPattern] = None

    freshness: FreshnessState = FreshnessState.STALE
    confidence_cap: ConfidenceCap = ConfidenceCap.NONE

    explicit_limits: List[str] = field(default_factory=list)
    technical_risks: List[str] = field(default_factory=list)

    b9_annotation_allowed: bool = True
    b9_reclassification_allowed: bool = False
    db_write_allowed: bool = False
    dashboard_auto_update_allowed: bool = False
    telegram_auto_send_allowed: bool = False


# ============================================================================
# LAYER 1: DATA ACCESS
# ============================================================================

class MultideviseDataAccess:
    """Layer 1: Acces read-only force_snapshots_v2."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    def __enter__(self):
        uri = f"file:{self.db_path}?mode=ro"
        self._conn = sqlite3.connect(uri, uri=True)
        return self

    def __exit__(self, *args):
        if self._conn:
            self._conn.close()

    @staticmethod
    def _normalize_timestamp(ts: str) -> str:
        """Normaliser timestamp pour SQLite datetime() function."""
        normalized = ts.replace('T', ' ')
        if '.' in normalized:
            normalized = normalized.split('.')[0]
        if '+' in normalized:
            normalized = normalized.split('+')[0]
        if 'Z' in normalized:
            normalized = normalized.replace('Z', '')
        return normalized.strip()

    def read_symbols_window(
        self,
        symbols: List[str],
        target_time_utc: str,
        window_seconds: int = 60
    ) -> List[Dict[str, Any]]:
        """Lire symboles dans fenetre temporelle."""

        if not symbols:
            return []

        target_normalized = self._normalize_timestamp(target_time_utc)
        placeholders = ','.join('?' * len(symbols))

        query = f"""
            SELECT
                symbol,
                COALESCE(force_pair_normalized, 0.0) as force_value,
                created_at,
                timeframe
            FROM force_snapshots_v2
            WHERE symbol IN ({placeholders})
              AND timeframe = 1
              AND created_at BETWEEN
                  datetime(?, '-{window_seconds} seconds')
                  AND datetime(?, '+{window_seconds} seconds')
            ORDER BY created_at DESC
        """

        try:
            cursor = self._conn.execute(
                query,
                (*symbols, target_normalized, target_normalized)
            )
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            return []

        # Dedoublonner par symbol
        seen = set()
        result = []
        for row in rows:
            symbol = row[0]
            if symbol not in seen:
                seen.add(symbol)
                result.append({
                    'symbol': symbol,
                    'force_value': float(row[1]) if row[1] is not None else 0.0,
                    'created_at': row[2],
                    'timeframe': row[3]
                })

        return result

    def detect_stale_symbols(
        self,
        symbols: List[str],
        threshold_minutes: int = 5
    ) -> List[str]:
        """Detecter symboles stale."""

        if not symbols:
            return []

        placeholders = ','.join('?' * len(symbols))

        query = f"""
            WITH latest AS (
                SELECT MAX(created_at) AS max_ts
                FROM force_snapshots_v2
                WHERE timeframe = 1
            )
            SELECT
                symbol,
                CAST(
                    (julianday((SELECT max_ts FROM latest)) -
                     julianday(MAX(created_at))) * 24 * 60
                    AS INTEGER
                ) AS minutes_stale
            FROM force_snapshots_v2
            WHERE symbol IN ({placeholders})
              AND timeframe = 1
            GROUP BY symbol
            HAVING minutes_stale > ?
        """

        try:
            cursor = self._conn.execute(query, (*symbols, threshold_minutes))
            return [r[0] for r in cursor.fetchall()]
        except sqlite3.OperationalError:
            return []


# ============================================================================
# LAYER 2: BASKET COMPUTATION
# ============================================================================

class BasketComputation:
    """Layer 2: Calcul baskets GBP/USD."""

    @staticmethod
    def compute_gbp_basket(symbols_data: List[Dict]) -> BasketScore:
        available = [d for d in symbols_data if d['symbol'] in GBP_BASKET_SYMBOLS]
        available_symbols = [d['symbol'] for d in available]
        missing = [s for s in GBP_BASKET_SYMBOLS if s not in available_symbols]

        up_count = 0
        down_count = 0
        neutral_count = 0

        for d in available:
            force = d['force_value']
            if d['symbol'] == 'EURGBP':
                force = -force

            if force > DIRECTION_THRESHOLD_UP:
                up_count += 1
            elif force < DIRECTION_THRESHOLD_DOWN:
                down_count += 1
            else:
                neutral_count += 1

        return BasketScore(
            currency="GBP",
            required_symbols=GBP_BASKET_SYMBOLS,
            available_symbols=available_symbols,
            missing_symbols=missing,
            direction_up_count=up_count,
            direction_down_count=down_count,
            direction_neutral_count=neutral_count
        )

    @staticmethod
    def compute_usd_basket(symbols_data: List[Dict]) -> BasketScore:
        available = [d for d in symbols_data if d['symbol'] in USD_BASKET_SYMBOLS]
        available_symbols = [d['symbol'] for d in available]
        missing = [s for s in USD_BASKET_SYMBOLS if s not in available_symbols]

        usd_quote = {'EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD'}

        stronger_count = 0
        weaker_count = 0
        neutral_count = 0

        for d in available:
            force = d['force_value']
            symbol = d['symbol']

            if symbol in usd_quote:
                normalized = -force
            else:
                normalized = force

            if normalized > DIRECTION_THRESHOLD_UP:
                stronger_count += 1
            elif normalized < DIRECTION_THRESHOLD_DOWN:
                weaker_count += 1
            else:
                neutral_count += 1

        return BasketScore(
            currency="USD",
            required_symbols=USD_BASKET_SYMBOLS,
            available_symbols=available_symbols,
            missing_symbols=missing,
            direction_up_count=stronger_count,
            direction_down_count=weaker_count,
            direction_neutral_count=neutral_count
        )


# ============================================================================
# LAYER 3: PATTERN DETECTION
# ============================================================================

class PatternDetection:
    """Layer 3: Detection patterns coalition/opposition."""

    @staticmethod
    def detect_coalition_usd_quote(symbols_data: List[Dict]) -> CoalitionPattern:
        available = [d for d in symbols_data if d['symbol'] in COALITION_USD_QUOTE]

        up_count = sum(1 for d in available if d['force_value'] > DIRECTION_THRESHOLD_UP)
        down_count = sum(1 for d in available if d['force_value'] < DIRECTION_THRESHOLD_DOWN)

        all_up = (up_count == len(available)) and len(available) >= 3
        all_down = (down_count == len(available)) and len(available) >= 3
        mixed = not all_up and not all_down

        return CoalitionPattern(
            pattern_type="USD_QUOTE_COALITION",
            symbols_in_pattern=[d['symbol'] for d in available],
            aligned_count=max(up_count, down_count),
            opposed_count=min(up_count, down_count),
            all_aligned_up=all_up,
            all_aligned_down=all_down,
            mixed=mixed
        )

    @staticmethod
    def detect_opposition_usd_base(symbols_data: List[Dict]) -> OppositionPattern:
        available = [d for d in symbols_data if d['symbol'] in OPPOSITION_USD_BASE]

        up_count = sum(1 for d in available if d['force_value'] > DIRECTION_THRESHOLD_UP)
        down_count = sum(1 for d in available if d['force_value'] < DIRECTION_THRESHOLD_DOWN)

        all_up = (up_count == len(available)) and len(available) >= 2
        all_down = (down_count == len(available)) and len(available) >= 2
        mixed = not all_up and not all_down

        return OppositionPattern(
            pattern_type="USD_BASE_OPPOSITION",
            symbols_in_pattern=[d['symbol'] for d in available],
            aligned_count=max(up_count, down_count),
            opposed_count=min(up_count, down_count),
            all_aligned_up=all_up,
            all_aligned_down=all_down,
            mixed=mixed
        )


# ============================================================================
# LAYER 4: QUALITY ASSESSMENT
# ============================================================================

class QualityAssessment:
    """Layer 4: Evaluation quality."""

    @staticmethod
    def assess_coverage(available_count: int, required_count: int) -> CoverageState:
        if required_count == 0:
            return CoverageState.BLIND

        ratio = available_count / required_count

        if ratio >= COVERAGE_THRESHOLD_FULL:
            return CoverageState.FULL
        elif ratio >= COVERAGE_THRESHOLD_PARTIAL:
            return CoverageState.PARTIAL
        elif ratio >= COVERAGE_THRESHOLD_THIN:
            return CoverageState.THIN
        else:
            return CoverageState.BLIND

    @staticmethod
    def assess_alignment(timestamps: List[str]) -> tuple:
        if not timestamps or len(timestamps) < 2:
            return AlignmentState.DEGRADED, None

        try:
            dt_list = []
            for ts in timestamps:
                clean = ts.replace('T', ' ')
                if '.' in clean:
                    clean = clean.split('.')[0]
                if 'Z' in clean:
                    clean = clean.replace('Z', '')
                dt_list.append(datetime.fromisoformat(clean.strip()))
        except (ValueError, AttributeError):
            return AlignmentState.DEGRADED, None

        min_dt = min(dt_list)
        max_dt = max(dt_list)
        skew_seconds = int((max_dt - min_dt).total_seconds())

        if skew_seconds <= ALIGNMENT_THRESHOLD_ALIGNED:
            return AlignmentState.ALIGNED, skew_seconds
        elif skew_seconds <= ALIGNMENT_THRESHOLD_PARTIAL:
            return AlignmentState.PARTIAL, skew_seconds
        else:
            return AlignmentState.DEGRADED, skew_seconds

    @staticmethod
    def assess_freshness(latest_timestamp: Optional[str]) -> FreshnessState:
        if not latest_timestamp:
            return FreshnessState.STALE

        try:
            clean = latest_timestamp.replace('T', ' ')
            if '.' in clean:
                clean = clean.split('.')[0]
            if 'Z' in clean:
                clean = clean.replace('Z', '')
            latest_dt = datetime.fromisoformat(clean.strip())
        except (ValueError, AttributeError):
            return FreshnessState.STALE

        now = datetime.utcnow()
        delta_minutes = (now - latest_dt).total_seconds() / 60

        if delta_minutes <= FRESHNESS_THRESHOLD_LIVE:
            return FreshnessState.LIVE
        elif delta_minutes <= FRESHNESS_THRESHOLD_STALE:
            return FreshnessState.DELAYED
        else:
            return FreshnessState.STALE

    @staticmethod
    def compute_confidence_cap(
        coverage: CoverageState,
        alignment: AlignmentState,
        freshness: FreshnessState
    ) -> ConfidenceCap:
        if coverage == CoverageState.BLIND or freshness == FreshnessState.STALE:
            return ConfidenceCap.NONE

        if (coverage == CoverageState.FULL and
            alignment == AlignmentState.ALIGNED and
            freshness == FreshnessState.LIVE):
            return ConfidenceCap.HIGH

        if (coverage in [CoverageState.FULL, CoverageState.PARTIAL] and
            alignment in [AlignmentState.ALIGNED, AlignmentState.PARTIAL] and
            freshness == FreshnessState.LIVE):
            return ConfidenceCap.MEDIUM

        return ConfidenceCap.LOW


# ============================================================================
# LAYER 5: CONTEXT ASSEMBLY (API PRINCIPALE)
# ============================================================================

class MultideviseContextBuilder:
    """API principale brique multidevise."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.data_access = None

    def __enter__(self):
        self.data_access = MultideviseDataAccess(self.db_path).__enter__()
        return self

    def __exit__(self, *args):
        if self.data_access:
            self.data_access.__exit__(*args)

    def build_context(
        self,
        symbol_local: str,
        timestamp_utc: str,
        window_seconds: int = 60
    ) -> MultideviseContext:
        """Construire contexte multidevise complet."""

        symbols_data = self.data_access.read_symbols_window(
            ALL_SYMBOLS, timestamp_utc, window_seconds
        )

        stale_symbols = self.data_access.detect_stale_symbols(
            ALL_SYMBOLS, threshold_minutes=FRESHNESS_THRESHOLD_STALE
        )

        available_symbols = list({d['symbol'] for d in symbols_data})
        missing_symbols = [s for s in ALL_SYMBOLS if s not in available_symbols]

        gbp_basket = BasketComputation.compute_gbp_basket(symbols_data)
        usd_basket = BasketComputation.compute_usd_basket(symbols_data)

        coalition = PatternDetection.detect_coalition_usd_quote(symbols_data)
        opposition = PatternDetection.detect_opposition_usd_base(symbols_data)

        coverage = QualityAssessment.assess_coverage(
            len(available_symbols), len(ALL_SYMBOLS)
        )

        timestamps = [d['created_at'] for d in symbols_data]
        alignment, skew = QualityAssessment.assess_alignment(timestamps)

        latest_ts = max(timestamps) if timestamps else None
        freshness = QualityAssessment.assess_freshness(latest_ts)

        confidence_cap = QualityAssessment.compute_confidence_cap(
            coverage, alignment, freshness
        )

        explicit_limits = []
        if missing_symbols:
            explicit_limits.append(
                f"Missing symbols: {', '.join(missing_symbols[:5])}"
                + (f" (+{len(missing_symbols)-5} more)" if len(missing_symbols) > 5 else "")
            )
        if stale_symbols:
            explicit_limits.append(f"Stale symbols: {', '.join(stale_symbols[:5])}")
        if alignment != AlignmentState.ALIGNED:
            explicit_limits.append(f"Alignment: {alignment.value} (skew {skew}s)")
        if gbp_basket.missing_symbols:
            explicit_limits.append(
                f"GBP basket incomplete: missing {len(gbp_basket.missing_symbols)}/7"
            )
        if usd_basket.missing_symbols:
            explicit_limits.append(
                f"USD basket incomplete: missing {len(usd_basket.missing_symbols)}/7"
            )

        technical_risks = []
        if coverage == CoverageState.BLIND:
            technical_risks.append("BLIND_COVERAGE")
        elif coverage == CoverageState.THIN:
            technical_risks.append("THIN_COVERAGE")
        if freshness == FreshnessState.STALE:
            technical_risks.append("STALE_DATA")
        if len(stale_symbols) >= 3:
            technical_risks.append("MULTIPLE_STALE_SYMBOLS")
        if alignment == AlignmentState.DEGRADED:
            technical_risks.append("ALIGNMENT_DEGRADED")
        if not symbols_data:
            technical_risks.append("NO_DATA_AVAILABLE")

        return MultideviseContext(
            symbol_local=symbol_local,
            timestamp_utc=timestamp_utc,
            computed_at_utc=datetime.utcnow().isoformat(),

            coverage=coverage,
            coverage_ratio=round(len(available_symbols) / len(ALL_SYMBOLS), 3),
            symbols_available=sorted(available_symbols),
            symbols_missing=sorted(missing_symbols),
            symbols_stale=sorted(stale_symbols),

            alignment=alignment,
            aligned_symbols=sorted(available_symbols),
            max_skew_seconds=skew,

            gbp_basket=gbp_basket,
            usd_basket=usd_basket,

            coalition_usd_quote=coalition,
            opposition_usd_base=opposition,

            freshness=freshness,
            confidence_cap=confidence_cap,

            explicit_limits=explicit_limits,
            technical_risks=technical_risks,

            b9_annotation_allowed=True,
            b9_reclassification_allowed=False,
            db_write_allowed=False,
            dashboard_auto_update_allowed=False,
            telegram_auto_send_allowed=False
        )


# ============================================================================
# SERIALIZATION
# ============================================================================

def context_to_dict(context: MultideviseContext) -> Dict[str, Any]:
    """Convertir MultideviseContext en dict JSON-serializable."""

    def basket_to_dict(b):
        if b is None:
            return None
        return {
            'currency': b.currency,
            'required_symbols': b.required_symbols,
            'available_symbols': b.available_symbols,
            'missing_symbols': b.missing_symbols,
            'direction_up_count': b.direction_up_count,
            'direction_down_count': b.direction_down_count,
            'direction_neutral_count': b.direction_neutral_count
        }

    def pattern_to_dict(p):
        if p is None:
            return None
        return {
            'pattern_type': p.pattern_type,
            'symbols_in_pattern': p.symbols_in_pattern,
            'aligned_count': p.aligned_count,
            'opposed_count': p.opposed_count,
            'all_aligned_up': p.all_aligned_up,
            'all_aligned_down': p.all_aligned_down,
            'mixed': p.mixed
        }

    return {
        'schema_version': context.schema_version,
        'symbol_local': context.symbol_local,
        'timestamp_utc': context.timestamp_utc,
        'computed_at_utc': context.computed_at_utc,

        'coverage': context.coverage.value,
        'coverage_ratio': context.coverage_ratio,
        'symbols_available': context.symbols_available,
        'symbols_missing': context.symbols_missing,
        'symbols_stale': context.symbols_stale,

        'alignment': context.alignment.value,
        'aligned_symbols': context.aligned_symbols,
        'max_skew_seconds': context.max_skew_seconds,

        'gbp_basket': basket_to_dict(context.gbp_basket),
        'usd_basket': basket_to_dict(context.usd_basket),

        'coalition_usd_quote': pattern_to_dict(context.coalition_usd_quote),
        'opposition_usd_base': pattern_to_dict(context.opposition_usd_base),

        'freshness': context.freshness.value,
        'confidence_cap': context.confidence_cap.value,

        'explicit_limits': context.explicit_limits,
        'technical_risks': context.technical_risks,

        'policy': {
            'b9_annotation_allowed': context.b9_annotation_allowed,
            'b9_reclassification_allowed': context.b9_reclassification_allowed,
            'db_write_allowed': context.db_write_allowed,
            'dashboard_auto_update_allowed': context.dashboard_auto_update_allowed,
            'telegram_auto_send_allowed': context.telegram_auto_send_allowed
        }
    }


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    import sys
    from argparse import ArgumentParser

    parser = ArgumentParser(description="PowerFlow Multidevise Context Builder")
    parser.add_argument("--db", default="Core/powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--time", default=None)
    parser.add_argument("--window", type=int, default=60)
    parser.add_argument("--output", default=None)

    args = parser.parse_args()

    target_time = args.time or datetime.utcnow().isoformat()

    try:
        with MultideviseContextBuilder(args.db) as builder:
            context = builder.build_context(
                symbol_local=args.symbol,
                timestamp_utc=target_time,
                window_seconds=args.window
            )
    except sqlite3.OperationalError as e:
        print(f"ERROR: Cannot access database: {e}", file=sys.stderr)
        sys.exit(1)

    output_dict = context_to_dict(context)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output_dict, f, indent=2)
        print(f"Context written to {args.output}")
    else:
        print(json.dumps(output_dict, indent=2))


if __name__ == "__main__":
    main()
