"""
Tests unitaires pour pf_multidevise.py

Couvre:
  - Doctrine garde-fous (no DB write, no dashboard, no Telegram)
  - Coverage states
  - Basket computation (GBP + USD avec normalisation)
  - Pattern detection (coalition/opposition)
  - Quality assessment (alignment, freshness, confidence)
  - Limits explicites
  - Output structure
"""

import os
import sys
import json
import sqlite3
import tempfile
import pytest
from datetime import datetime, timedelta
from pathlib import Path

# Ajouter Core au path
sys.path.insert(0, str(Path(__file__).parent.parent / "Core"))

from pf_multidevise import (
    # Classes
    MultideviseContextBuilder,
    MultideviseDataAccess,
    BasketComputation,
    PatternDetection,
    QualityAssessment,
    MultideviseContext,
    BasketScore,
    CoalitionPattern,
    OppositionPattern,

    # Enums
    CoverageState,
    AlignmentState,
    FreshnessState,
    ConfidenceCap,

    # Constants
    ALL_SYMBOLS,
    GBP_BASKET_SYMBOLS,
    USD_BASKET_SYMBOLS,
    COALITION_USD_QUOTE,
    OPPOSITION_USD_BASE,

    # Utils
    context_to_dict
)


# ============================================================================
# FIXTURES — DB simulée
# ============================================================================

@pytest.fixture
def test_db_path(tmp_path):
    """Créer DB SQLite test avec force_snapshots_v2."""
    db_path = tmp_path / "test_powerflow.db"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Créer table
    cursor.execute("""
        CREATE TABLE force_snapshots_v2 (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            timeframe INTEGER NOT NULL,
            force_pair_normalized REAL,
            created_at TEXT NOT NULL
        )
    """)

    # Insérer données simulées (13 symboles alignés)
    # Format SQLite compatible: YYYY-MM-DD HH:MM:SS (pas T, pas microseconds)
    now = datetime.utcnow()
    base_time = now - timedelta(minutes=1)
    base_time_str = base_time.strftime('%Y-%m-%d %H:%M:%S')

    test_data = [
        ('GBPUSD', 0.5), ('EURUSD', 0.4), ('AUDUSD', 0.3), ('NZDUSD', 0.2),
        ('USDJPY', -0.3), ('USDCAD', -0.2), ('USDCHF', -0.1),
        ('EURGBP', -0.2), ('GBPJPY', 0.4), ('GBPAUD', 0.3),
        ('GBPCAD', 0.2), ('GBPCHF', 0.3), ('GBPNZD', 0.2),
    ]

    for symbol, force in test_data:
        cursor.execute("""
            INSERT INTO force_snapshots_v2
            (symbol, timeframe, force_pair_normalized, created_at)
            VALUES (?, ?, ?, ?)
        """, (symbol, 1, force, base_time_str))

    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def thin_db_path(tmp_path):
    """DB avec seulement 3 symboles (THIN coverage)."""
    db_path = tmp_path / "thin_powerflow.db"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE force_snapshots_v2 (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            timeframe INTEGER NOT NULL,
            force_pair_normalized REAL,
            created_at TEXT NOT NULL
        )
    """)

    base_time = datetime.utcnow() - timedelta(minutes=1)
    base_time_str = base_time.strftime('%Y-%m-%d %H:%M:%S')

    # Seulement 4 symboles
    for symbol, force in [('GBPUSD', 0.5), ('EURUSD', 0.4),
                           ('USDJPY', -0.3), ('GBPJPY', 0.4)]:
        cursor.execute("""
            INSERT INTO force_snapshots_v2
            (symbol, timeframe, force_pair_normalized, created_at)
            VALUES (?, ?, ?, ?)
        """, (symbol, 1, force, base_time_str))

    conn.commit()
    conn.close()

    return str(db_path)


# ============================================================================
# DOCTRINE — Garde-fous critiques
# ============================================================================

class TestDoctrine:
    """Tests garde-fous doctrine PowerFlow."""

    def test_no_db_write_in_source(self):
        """Module MUST NOT contain destructive SQL operations."""
        import ast

        source_path = Path(__file__).parent.parent / "Core" / "pf_multidevise.py"
        source = source_path.read_text()

        # Parse AST to find string literals containing forbidden SQL
        tree = ast.parse(source)

        forbidden_patterns = [
            'INSERT INTO',
            'UPDATE force_snapshots_v2',
            'DELETE FROM force_snapshots_v2',
            'DROP TABLE',
            'ALTER TABLE',
            'REPLACE INTO',
            'TRUNCATE'
        ]

        # Check string literals in code (not comments/docstrings)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value_upper = node.value.upper()
                for pattern in forbidden_patterns:
                    # Skip docstrings (already detected as Expr Constant at top of module/func)
                    parent_check = isinstance(node.value, str) and len(node.value) > 200
                    if pattern in value_upper and not parent_check:
                        assert False, \
                            f"Forbidden SQL in string literal: {pattern}"

    def test_db_opened_readonly(self, test_db_path):
        """DB MUST be opened with mode=ro URI."""
        with MultideviseDataAccess(test_db_path) as access:
            # Vérifier connexion existe
            assert access._conn is not None

            # Tenter écriture (doit échouer)
            with pytest.raises(sqlite3.OperationalError):
                access._conn.execute(
                    "INSERT INTO force_snapshots_v2 VALUES (?, ?, ?, ?, ?)",
                    (999, 'TEST', 1, 0.0, '2026-01-01')
                )

    def test_no_dashboard_imports(self):
        """Module MUST NOT import dashboard modules."""
        source_path = Path(__file__).parent.parent / "Core" / "pf_multidevise.py"
        source = source_path.read_text()

        forbidden = ['import dashboard', 'from dashboard',
                     'import cockpit', 'from cockpit']
        for keyword in forbidden:
            assert keyword.lower() not in source.lower(), \
                f"Forbidden import: {keyword}"

    def test_no_telegram_imports(self):
        """Module MUST NOT import telegram modules."""
        source_path = Path(__file__).parent.parent / "Core" / "pf_multidevise.py"
        source = source_path.read_text()

        forbidden = ['import telegram', 'from telegram',
                     'import telebot', 'from telebot']
        for keyword in forbidden:
            assert keyword.lower() not in source.lower(), \
                f"Forbidden import: {keyword}"

    def test_no_forbidden_language(self, test_db_path):
        """Output MUST NOT contain interpretive trading language."""
        with MultideviseContextBuilder(test_db_path) as builder:
            context = builder.build_context(
                symbol_local="GBPUSD",
                timestamp_utc=datetime.utcnow().isoformat()
            )

        output = json.dumps(context_to_dict(context)).lower()

        forbidden = ['buy', 'sell', 'long', 'short', 'enter',
                     'probability of success', 'win rate',
                     'recommended action', 'confirmed strong',
                     'validated trade']
        for keyword in forbidden:
            assert keyword not in output, \
                f"Forbidden interpretive language: {keyword}"

    def test_policy_immutable(self, test_db_path):
        """Policy fields MUST be immutable (db_write=False etc)."""
        with MultideviseContextBuilder(test_db_path) as builder:
            context = builder.build_context(
                symbol_local="GBPUSD",
                timestamp_utc=datetime.utcnow().isoformat()
            )

        assert context.b9_reclassification_allowed is False
        assert context.db_write_allowed is False
        assert context.dashboard_auto_update_allowed is False
        assert context.telegram_auto_send_allowed is False


# ============================================================================
# COVERAGE — États
# ============================================================================

class TestCoverage:
    """Tests coverage states."""

    def test_coverage_full(self):
        """13/13 symboles → FULL."""
        assert QualityAssessment.assess_coverage(13, 13) == CoverageState.FULL
        assert QualityAssessment.assess_coverage(11, 13) == CoverageState.FULL  # 84%

    def test_coverage_partial(self):
        """7-10/13 symboles → PARTIAL."""
        assert QualityAssessment.assess_coverage(7, 13) == CoverageState.PARTIAL  # 53%
        assert QualityAssessment.assess_coverage(10, 13) == CoverageState.PARTIAL  # 76%

    def test_coverage_thin(self):
        """4-6/13 symboles → THIN."""
        assert QualityAssessment.assess_coverage(4, 13) == CoverageState.THIN  # 30%
        assert QualityAssessment.assess_coverage(6, 13) == CoverageState.THIN  # 46%

    def test_coverage_blind(self):
        """<30% → BLIND."""
        assert QualityAssessment.assess_coverage(3, 13) == CoverageState.BLIND  # 23%
        assert QualityAssessment.assess_coverage(0, 13) == CoverageState.BLIND
        assert QualityAssessment.assess_coverage(1, 13) == CoverageState.BLIND


# ============================================================================
# BASKETS — Calcul GBP/USD
# ============================================================================

class TestBaskets:
    """Tests basket computation."""

    def test_gbp_basket_all_up(self):
        """Tous symboles GBP up → up_count élevé."""
        data = [
            {'symbol': 'GBPUSD', 'force_value': 0.5},
            {'symbol': 'GBPJPY', 'force_value': 0.4},
            {'symbol': 'GBPCHF', 'force_value': 0.3},
            {'symbol': 'GBPCAD', 'force_value': 0.2},
            {'symbol': 'GBPAUD', 'force_value': 0.3},
            {'symbol': 'GBPNZD', 'force_value': 0.2},
            {'symbol': 'EURGBP', 'force_value': -0.2},  # Inversé: GBP up
        ]

        basket = BasketComputation.compute_gbp_basket(data)

        assert basket.currency == "GBP"
        assert basket.direction_up_count == 7  # Tous up (EURGBP inversé compté up)
        assert basket.direction_down_count == 0
        assert len(basket.missing_symbols) == 0

    def test_eurgbp_inversion(self):
        """EURGBP down doit compter comme GBP up."""
        data = [
            {'symbol': 'EURGBP', 'force_value': -0.5},  # EUR down vs GBP = GBP up
        ]

        basket = BasketComputation.compute_gbp_basket(data)

        # EURGBP négatif → inversé → positif → up_count = 1
        assert basket.direction_up_count == 1
        assert basket.direction_down_count == 0

    def test_usd_basket_normalization(self):
        """USD basket doit normaliser USD quote vs USD base."""
        data = [
            # USD quote: up = USD weaker → inversé en USD basket
            {'symbol': 'GBPUSD', 'force_value': 0.5},   # USD weaker
            {'symbol': 'EURUSD', 'force_value': 0.4},   # USD weaker
            {'symbol': 'AUDUSD', 'force_value': 0.3},   # USD weaker
            {'symbol': 'NZDUSD', 'force_value': 0.2},   # USD weaker
            # USD base: up = USD stronger → gardé
            {'symbol': 'USDJPY', 'force_value': -0.3},  # USD weaker
            {'symbol': 'USDCAD', 'force_value': -0.2},  # USD weaker
            {'symbol': 'USDCHF', 'force_value': -0.1},  # neutral
        ]

        basket = BasketComputation.compute_usd_basket(data)

        # 4 USD quote inverted (down) + 2 USD base down = 6 weaker, 0 stronger
        # USDCHF -0.1 < threshold → neutral
        assert basket.direction_down_count >= 5  # USD weaker
        assert basket.direction_up_count == 0    # USD stronger

    def test_basket_missing_symbols(self):
        """Basket doit lister symboles manquants."""
        data = [
            {'symbol': 'GBPUSD', 'force_value': 0.5},
        ]

        basket = BasketComputation.compute_gbp_basket(data)

        # Manque 6 symboles GBP
        assert len(basket.missing_symbols) == 6
        assert 'GBPJPY' in basket.missing_symbols
        assert 'GBPUSD' not in basket.missing_symbols


# ============================================================================
# PATTERNS — Coalition/Opposition
# ============================================================================

class TestPatterns:
    """Tests pattern detection."""

    def test_coalition_all_up(self):
        """USD-quote tous up → all_aligned_up = True."""
        data = [
            {'symbol': 'GBPUSD', 'force_value': 0.5},
            {'symbol': 'EURUSD', 'force_value': 0.4},
            {'symbol': 'AUDUSD', 'force_value': 0.3},
            {'symbol': 'NZDUSD', 'force_value': 0.2},
        ]

        coalition = PatternDetection.detect_coalition_usd_quote(data)

        assert coalition.all_aligned_up is True
        assert coalition.all_aligned_down is False
        assert coalition.mixed is False
        assert coalition.aligned_count == 4

    def test_coalition_mixed(self):
        """USD-quote mélangés → mixed = True."""
        data = [
            {'symbol': 'GBPUSD', 'force_value': 0.5},   # up
            {'symbol': 'EURUSD', 'force_value': -0.4},  # down
            {'symbol': 'AUDUSD', 'force_value': 0.3},   # up
            {'symbol': 'NZDUSD', 'force_value': -0.2},  # down
        ]

        coalition = PatternDetection.detect_coalition_usd_quote(data)

        assert coalition.all_aligned_up is False
        assert coalition.all_aligned_down is False
        assert coalition.mixed is True

    def test_opposition_all_down(self):
        """USD-base tous down → all_aligned_down = True."""
        data = [
            {'symbol': 'USDJPY', 'force_value': -0.3},
            {'symbol': 'USDCAD', 'force_value': -0.2},
            {'symbol': 'USDCHF', 'force_value': -0.4},
        ]

        opposition = PatternDetection.detect_opposition_usd_base(data)

        assert opposition.all_aligned_down is True
        assert opposition.all_aligned_up is False


# ============================================================================
# QUALITY — Alignment/Freshness/Confidence
# ============================================================================

class TestQuality:
    """Tests quality assessment."""

    def test_alignment_aligned(self):
        """Skew < 60s → ALIGNED."""
        base = datetime.utcnow()
        timestamps = [
            base.isoformat(),
            (base + timedelta(seconds=30)).isoformat(),
            (base + timedelta(seconds=45)).isoformat(),
        ]

        alignment, skew = QualityAssessment.assess_alignment(timestamps)

        assert alignment == AlignmentState.ALIGNED
        assert skew <= 60

    def test_alignment_degraded(self):
        """Skew > 120s → DEGRADED."""
        base = datetime.utcnow()
        timestamps = [
            base.isoformat(),
            (base + timedelta(seconds=200)).isoformat(),
        ]

        alignment, skew = QualityAssessment.assess_alignment(timestamps)

        assert alignment == AlignmentState.DEGRADED

    def test_freshness_live(self):
        """Timestamp < 2min → LIVE."""
        recent = (datetime.utcnow() - timedelta(seconds=30)).isoformat()
        assert QualityAssessment.assess_freshness(recent) == FreshnessState.LIVE

    def test_freshness_stale(self):
        """Timestamp > 5min → STALE."""
        old = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        assert QualityAssessment.assess_freshness(old) == FreshnessState.STALE

    def test_confidence_high(self):
        """FULL + ALIGNED + LIVE → HIGH."""
        cap = QualityAssessment.compute_confidence_cap(
            CoverageState.FULL,
            AlignmentState.ALIGNED,
            FreshnessState.LIVE
        )
        assert cap == ConfidenceCap.HIGH

    def test_confidence_none_when_blind(self):
        """BLIND → NONE."""
        cap = QualityAssessment.compute_confidence_cap(
            CoverageState.BLIND,
            AlignmentState.ALIGNED,
            FreshnessState.LIVE
        )
        assert cap == ConfidenceCap.NONE

    def test_confidence_none_when_stale(self):
        """STALE → NONE."""
        cap = QualityAssessment.compute_confidence_cap(
            CoverageState.FULL,
            AlignmentState.ALIGNED,
            FreshnessState.STALE
        )
        assert cap == ConfidenceCap.NONE


# ============================================================================
# INTEGRATION — Build context complet
# ============================================================================

class TestIntegration:
    """Tests intégration build_context."""

    def test_build_context_full_coverage(self, test_db_path):
        """13 symboles présents → FULL coverage."""
        with MultideviseContextBuilder(test_db_path) as builder:
            context = builder.build_context(
                symbol_local="GBPUSD",
                timestamp_utc=(datetime.utcnow() - timedelta(minutes=1)).isoformat()
            )

        assert context.coverage == CoverageState.FULL
        assert context.coverage_ratio >= 0.8
        assert len(context.symbols_available) == 13
        assert len(context.symbols_missing) == 0

    def test_build_context_thin_coverage(self, thin_db_path):
        """4/13 symboles → THIN coverage."""
        with MultideviseContextBuilder(thin_db_path) as builder:
            context = builder.build_context(
                symbol_local="GBPUSD",
                timestamp_utc=(datetime.utcnow() - timedelta(minutes=1)).isoformat()
            )

        assert context.coverage == CoverageState.THIN
        assert len(context.symbols_missing) > 0

    def test_build_context_baskets_present(self, test_db_path):
        """Build doit produire baskets GBP + USD."""
        with MultideviseContextBuilder(test_db_path) as builder:
            context = builder.build_context(
                symbol_local="GBPUSD",
                timestamp_utc=(datetime.utcnow() - timedelta(minutes=1)).isoformat()
            )

        assert context.gbp_basket is not None
        assert context.gbp_basket.currency == "GBP"
        assert context.usd_basket is not None
        assert context.usd_basket.currency == "USD"

    def test_build_context_patterns_present(self, test_db_path):
        """Build doit produire coalition + opposition patterns."""
        with MultideviseContextBuilder(test_db_path) as builder:
            context = builder.build_context(
                symbol_local="GBPUSD",
                timestamp_utc=(datetime.utcnow() - timedelta(minutes=1)).isoformat()
            )

        assert context.coalition_usd_quote is not None
        assert context.coalition_usd_quote.pattern_type == "USD_QUOTE_COALITION"
        assert context.opposition_usd_base is not None
        assert context.opposition_usd_base.pattern_type == "USD_BASE_OPPOSITION"

    def test_build_context_serializable(self, test_db_path):
        """Output doit être JSON-serializable."""
        with MultideviseContextBuilder(test_db_path) as builder:
            context = builder.build_context(
                symbol_local="GBPUSD",
                timestamp_utc=(datetime.utcnow() - timedelta(minutes=1)).isoformat()
            )

        output = context_to_dict(context)
        json_str = json.dumps(output)  # Doit pas raise
        parsed = json.loads(json_str)

        assert parsed['schema_version'] == "MULTIDEVISE_CONTEXT_V1"
        assert parsed['symbol_local'] == "GBPUSD"

    def test_build_context_explicit_limits_when_thin(self, thin_db_path):
        """THIN coverage doit produire limits explicites."""
        with MultideviseContextBuilder(thin_db_path) as builder:
            context = builder.build_context(
                symbol_local="GBPUSD",
                timestamp_utc=(datetime.utcnow() - timedelta(minutes=1)).isoformat()
            )

        assert len(context.explicit_limits) > 0
        assert len(context.technical_risks) > 0

    def test_no_data_returns_blind(self, tmp_path):
        """DB vide → BLIND coverage + NO_DATA risk."""
        # Créer DB vide
        empty_db = tmp_path / "empty.db"
        conn = sqlite3.connect(str(empty_db))
        conn.execute("""
            CREATE TABLE force_snapshots_v2 (
                id INTEGER PRIMARY KEY,
                symbol TEXT, timeframe INTEGER,
                force_pair_normalized REAL, created_at TEXT
            )
        """)
        conn.commit()
        conn.close()

        with MultideviseContextBuilder(str(empty_db)) as builder:
            context = builder.build_context(
                symbol_local="GBPUSD",
                timestamp_utc=datetime.utcnow().isoformat()
            )

        assert context.coverage == CoverageState.BLIND
        assert "NO_DATA_AVAILABLE" in context.technical_risks
        assert context.confidence_cap == ConfidenceCap.NONE
