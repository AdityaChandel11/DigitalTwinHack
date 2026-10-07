# Research scripts, 4 Oct 2026 (archived as run)

These five scripts produced the counts and exploratory numbers in
`docs/decisions/2026-10-04-plan-revision.md`. They are kept exactly as they were run so that record can be
checked. They are not part of the package, are excluded from lint, and nothing they print may be quoted as a
result: Milestone 3 re-implements each one as a tested repo command under Amendment 3.

| Script | What it counts | Patients it touches |
|---|---|---|
| `counts_nights_and_record.py` | Overnight-low nights per patient, fingerstick clock times, record completeness, drug vocabulary | All (labels and availability only) |
| `counts_label_validity.py` | Sensor against fingerstick agreement, fingersticks per day, repeat recordings, drift of the sensor mean | All (labels and availability only) |
| `probe1_level_filter.py` | Random-walk level fed by fingersticks against controls | Development patients only |
| `probe2_decaying_filter.py` | Headroom of a perfect daily level; decaying-deviation filter; accuracy against the fingerstick | Development patients only |
| `probe3_report_level.py` | Mean, time above 180 and time in range for the hidden window against the stale report | Development patients only |

Run from the repo root, for example:

```bash
uv run python scripts/research_2026-10-04/counts_label_validity.py
```

No estimator or predictor was scored on a Shanghai test-split patient by any of these scripts.
