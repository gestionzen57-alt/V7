from __future__ import annotations

import json
from pathlib import Path

from pf_currency_energy_probe import build_currency_energy_state


def main() -> int:
    state = build_currency_energy_state(
        db_path=Path("powerflow.db"),
        symbol="GBPUSD",
        timeframe=1,
        bars=50,
        htf_tfs=(5, 15, 30),
    )

    assert isinstance(state, dict), "state must be dict"

    # JSON-safe
    json.dumps(state, ensure_ascii=False)

    print("CURRENCY_ENERGY_API_REUSE_OK")
    print(f"keys={sorted(state.keys())}")

    currencies = state.get("currencies", {})
    print(f"currencies={list(currencies.keys())}")

    for ccy, data in currencies.items():
        print(
            f"{ccy}: "
            f"label={data.get('energy_label')} "
            f"score={data.get('energy_score')} "
            f"confidence={data.get('energy_confidence')}"
        )

    out = Path("output") / "currency_energy_state_api_reuse_test.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"out={out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())