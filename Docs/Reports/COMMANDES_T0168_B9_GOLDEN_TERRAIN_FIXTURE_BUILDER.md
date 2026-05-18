# Commandes T0168

```powershell
python -m py_compile pf_t009_golden_terrain_fixture_builder.py tools\build_t0168_b9_golden_terrain_fixture_builder.py
python -m pytest tests\test_t0168_b9_golden_terrain_fixture_builder.py
python tools\build_t0168_b9_golden_terrain_fixture_builder.py --golden-cases-csv Docs\Reports\T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv --output-dir outputs\b9_golden_terrain_fixture_builder_v0 --min-ready 1
```
