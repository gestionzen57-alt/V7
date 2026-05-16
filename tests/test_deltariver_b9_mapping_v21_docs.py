from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "Docs" / "Reports" / "DELTARIVER_TO_POWERFLOW_B9_MAPPING.md"
COMPARISON = ROOT / "Docs" / "Reports" / "DELTARIVER_TO_POWERFLOW_B9_V2_V21_COMPARISON.md"
PHILO = ROOT / "Docs" / "Reports" / "DELTARIVER_TO_POWERFLOW_B9_PHILOSOPHY.md"


def read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_v21_reports_exist_and_are_not_empty():
    for path in (REPORT, COMPARISON, PHILO):
        text = read(path)
        assert len(text) > 1000


def test_mapping_contains_core_b9_doctrine():
    text = read(REPORT)
    required = [
        "tick → bucket → event → moment → zone mémoire → scène",
        "B9_EFFORT_RESULT_PROGRESS",
        "B9_VOLUME_AS_FUEL",
        "B9_VOLUME_AS_BRAKE",
        "B9_PUSH_AGAINST_WALL",
        "T009_MOMENT_EFFORT_WITHOUT_RESULT",
        "T009 Sequence Summarizer V0",
    ]
    for token in required:
        assert token in text


def test_philosophy_contains_powerflow_reading_key():
    text = read(PHILO)
    required = [
        "Ne lis pas un signal.",
        "Lis une situation.",
        "Le retest est le juge.",
        "B8 dit qui pousse contre qui.",
        "B9 dit comment le flux imprime ses traces dans le prix.",
    ]
    for token in required:
        assert token in text
