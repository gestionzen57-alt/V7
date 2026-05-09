"""
PowerFlow V6 - run_temporal_patterns_smoke.py

Smoke test synthetique pour pf_temporal_patterns.py.
Aucune lecture DB. Aucune ecriture DB.
"""

from __future__ import annotations

from pf_temporal_patterns import (
    temporal_density,
    detect_angular_alignment,
    extreme_zone_breathing,
)


def main() -> int:
    # rows = (time, GBP, USD, EUR, JPY, CAD)
    # Serie synthetique en zscore-like.
    rows = [
        ("2026-05-02 10:00", -2.60,  2.40, -1.80,  1.20,  0.20),
        ("2026-05-02 10:05", -2.35,  2.10, -1.40,  1.10,  0.50),
        ("2026-05-02 10:10", -2.70,  1.80, -1.90,  1.40,  0.90),
        ("2026-05-02 10:15", -2.45,  1.30, -1.50,  1.70,  1.40),
        ("2026-05-02 10:20", -2.85,  0.70, -2.05,  2.10,  1.90),
        ("2026-05-02 10:25", -2.65,  0.20, -1.80,  2.40,  2.30),
        ("2026-05-02 10:30", -3.00, -0.40, -2.25,  2.70,  2.70),
    ]

    devise_cols = [
        ("TIME", "0"),
        ("GBP", "1"),
        ("USD", "2"),
        ("EUR", "3"),
        ("JPY", "4"),
        ("CAD", "5"),
    ]

    bar_index = len(rows) - 1

    print("PowerFlow Temporal Patterns Smoke")
    print("=" * 72)

    print("\n1) temporal_density")
    for devise in ["GBP", "EUR", "CAD"]:
        value = temporal_density(devise, rows, bar_index, window=5, devise_cols=devise_cols)
        print(f"{devise}: density={value:.3f}")

    print("\n2) extreme_zone_breathing")
    for devise in ["GBP", "EUR", "CAD"]:
        result = extreme_zone_breathing(devise, rows, bar_index, window=6, devise_cols=devise_cols)
        print(f"{devise}: {result}")

    print("\n3) detect_angular_alignment")
    # Serie separee: GBP/USD/EUR changent simultanement de pente
    # avec un angle proche. JPY/CAD servent de bruit.
    angle_rows = [
        ("2026-05-02 11:00", 0.0, 0.1, -0.1, 1.0, -1.0),
        ("2026-05-02 11:05", 0.8, 0.9, 0.7, 1.2, -0.8),
        ("2026-05-02 11:10", 1.6, 1.7, 1.5, 1.4, -0.6),
        ("2026-05-02 11:15", 1.2, 1.3, 1.1, 1.5, -0.5),
        ("2026-05-02 11:20", 0.8, 0.9, 0.7, 1.6, -0.4),
    ]
    result = detect_angular_alignment(
        devises=["GBP", "USD", "EUR", "JPY", "CAD"],
        rows=angle_rows,
        bar_index=len(angle_rows) - 1,
        tf=5,
        devise_cols=devise_cols,
        angle_tolerance=3.0,
    )
    print(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
