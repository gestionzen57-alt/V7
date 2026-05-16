"""T009 Battlefield Flux feature flags.

Phase 0 contract:
- all live side effects are OFF by default;
- dry-run is ON by default;
- source mode is explicit and validated;
- engine integration is not silently enabled during Phase 1A.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass


@dataclass(frozen=True)
class T009Flags:
    """T009 Battlefield Flux feature flags."""

    # Archive tick writer
    TICK_ARCHIVE_WRITE: bool = bool(int(os.getenv("POWERFLOW_T009_TICK_ARCHIVE_WRITE", "0")))

    # Battlefield flux compute
    USE_BATTLEFIELD_FLUX: bool = bool(int(os.getenv("POWERFLOW_T009_USE_BATTLEFIELD_FLUX", "0")))

    # Source mode: auto detects, or forces a path.
    SOURCE_MODE: str = os.getenv("POWERFLOW_T009_SOURCE_MODE", "auto")

    # Allow fallback from M1 bars.
    ALLOW_M1_FALLBACK: bool = bool(int(os.getenv("POWERFLOW_T009_ALLOW_M1_FALLBACK", "1")))

    # Telegram live: OFF during Phase 1A.
    ENABLE_TELEGRAM: bool = bool(int(os.getenv("POWERFLOW_T009_ENABLE_TELEGRAM", "0")))

    # Engine integration: OFF during Phase 1A.
    ENABLE_ENGINE_INTEGRATION: bool = bool(int(os.getenv("POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION", "0")))

    # Max lookback minutes.
    MAX_LOOKBACK_MIN: int = int(os.getenv("POWERFLOW_T009_MAX_LOOKBACK_MIN", "120"))

    # Dry-run mode.
    DRY_RUN: bool = bool(int(os.getenv("POWERFLOW_T009_DRY_RUN", "1")))

    def __post_init__(self) -> None:
        """Validate Phase 0 / Phase 1A feature-flag safety."""
        if self.SOURCE_MODE not in ["auto", "ontick", "timer", "fallback"]:
            raise ValueError(f"Invalid SOURCE_MODE: {self.SOURCE_MODE}")

        if self.MAX_LOOKBACK_MIN > 240:
            raise ValueError(f"MAX_LOOKBACK_MIN too large: {self.MAX_LOOKBACK_MIN}")

        if self.ENABLE_TELEGRAM and self.DRY_RUN:
            raise ValueError("ENABLE_TELEGRAM=1 impossible with DRY_RUN=1")

        if self.ENABLE_ENGINE_INTEGRATION:
            warnings.warn("T009 engine integration is Phase 2 only", UserWarning, stacklevel=2)


FLAGS = T009Flags()
