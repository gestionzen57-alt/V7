from pf_symbol_mapper import (
    SymbolMappingError,
    get_force_columns,
    normalize_symbol,
    parse_symbols,
    resolve_symbol_mapping,
)


def test_normalize_symbol():
    assert normalize_symbol(" gbp/usd ") == "GBPUSD"
    assert normalize_symbol("XAUUSD.") == "XAUUSD"


def test_known_symbols():
    assert get_force_columns("GBPUSD") == ("force_gbp", "force_usd")
    assert get_force_columns("EURUSD") == ("force_eur", "force_usd")
    assert get_force_columns("USDJPY") == ("force_usd", "force_jpy")
    assert get_force_columns("XAUUSD") == ("force_xau", "force_usd")


def test_db_columns_validation_ok():
    cols = ["symbol", "timeframe", "timestamp", "force_gbp", "force_usd"]
    assert get_force_columns("GBPUSD", cols) == ("force_gbp", "force_usd")


def test_db_columns_validation_missing():
    cols = ["symbol", "timeframe", "timestamp", "force_gbp"]
    try:
        get_force_columns("GBPUSD", cols)
    except SymbolMappingError as exc:
        assert "missing" in str(exc).lower()
    else:
        raise AssertionError("Expected SymbolMappingError")


def test_parse_symbols_unique():
    assert parse_symbols("GBPUSD, eurusd, GBPUSD") == ["GBPUSD", "EURUSD"]


def test_resolve_mapping_dict():
    mapping = resolve_symbol_mapping("USDJPY")
    assert mapping.symbol == "USDJPY"
    assert mapping.as_dict()["force_columns"] == ["force_usd", "force_jpy"]
