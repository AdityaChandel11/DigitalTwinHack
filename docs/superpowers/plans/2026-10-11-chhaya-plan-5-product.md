# Chhaya Plan 5: the product (Milestone 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan
> task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The team lead chose native execution on
> 8 Oct ("go on, keep building", Opus 5.5 at xhigh for every task), in the session that wrote the plan, so
> each task gives files, interfaces and the tests that define done, not a second copy of the code.

**Goal:** A three-screen, offline dashboard served by one command from a pre-built bundle, plus the one
science pass the product needs (a band for the fingerstick estimate), finished by the freeze on 15 Oct.

**Architecture:** `chhaya.build` turns `results/`, the decision records' wording and recordings into a JSON
bundle; `chhaya.dashboard` serves that bundle and a static page of plain ES modules with hand-built SVG charts.
The browser never touches the model and nothing is fitted while the page runs.

**Tech Stack:** Python 3.13 (stdlib `http.server`, numpy, pandas, the existing `chhaya` modules), plain
HTML, CSS and ES modules, no runtime dependencies, vendored OFL fonts, pytest and ruff.

**Spec:** `docs/superpowers/specs/2026-10-08-chhaya-m4-product-design.md` (read with the mocks in
`docs/superpowers/specs/m4-mocks/` and `docs/decisions/2026-10-08-m4-kickoff.md`).

## Status

| Task | State |
|---|---|
| A1 register the pass | Done 8 Oct (`5943bbc`) |
| A2 the spread of the filter | Done 8 Oct; checked against the exact posterior |
| A3 the experiment module | Done 8 Oct |
| A4 reviews, development run, freeze | Done 8 Oct: no leakage path; `patient` frozen (addendum to the note) |
| A5 the one held-out pass | **Waiting for the team lead's go.** Must run by 10 Oct, 16:00 |
| B1 claims, B2 wording, B3 names, record, treatment, B4 the synthetic patient | Done 8 Oct. `copy.py` was named `wording.py`; `pseudonym` became `pseudonyms` (one call names a whole cohort, so no two patients share a name) |
| B5 to B8, C1 to C7, D1, D2 | Not started |

## Global Constraints

- Rules 1 to 8 of CLAUDE.md. In particular: nothing under `results/` is written by the build; per-reading
  arrays of real patients never enter git; held-out patients are read only with `--confirm` on committed code.
- No existing module under `src/chhaya/` is changed. New code only.
- On screen, never: a dose recommendation; a low-glucose estimate; time in range or time below range from an
  estimate; GMI or estimated HbA1c from fingersticks; the word "alarm"; a ranking by risk; an estimate
  without its band and the word "estimated"; fusion described as a gain.
- Safety wording is verbatim from the records' "Consequences for the product"; results are each record's
  "claim to quote", whole. Tests compare both with the records.
- Limits line, always visible: "Research prototype; evaluated on a Chinese cohort in supervised care and a
  US free-living cohort; estimates, not measurements; not for dosing."
- Storage and screen in mg/dL; `encoding="utf-8"` on every read and write; `ruff format` (110) and
  `ruff check` clean; tests first.
- No network request at run time; no Node, no Docker on a clean clone.
- Light theme by default for everyone; dark behind the toggle. Tokens from `m4-mocks/mock.css`.

## Review Focus

1. **The bundle is missing, half-built or from an older build.** The page says which command builds it and
   which version it expected; it never shows a blank screen or `undefined`. (Tasks C1, C6)
2. **A patient lacks something**: no fingersticks, no hidden sensor, no estimated trace, no dose table, a
   missing age or HbA1c. Each panel shows its worded state ("not computed", "not recorded", "withheld") at the
   same weight as its filled state. (Tasks B7, C3, C6)
3. **The sensor has gaps.** A missing stretch is a break in the line, never a straight bridge, in the bundle
   and on the chart. (Tasks B7, C2)
4. **Long text on a narrow screen**: a long reason, a long pseudonym, a long command. It wraps or scrolls in
   its own box; the page never scrolls sideways at 375 px. (Tasks C4, C5, C7)
5. **A reader without a mouse or with reduced motion.** Every control and the chart are reachable by keyboard
   with a visible focus ring; the reveal is instant under reduced motion; values exist as a table. (Tasks C2, C6)

## Calendar and models

| Day | Tasks | Recommended model (the team lead runs all of it on Opus 5.5, xhigh) |
|---|---|---|
| Fri 9 Oct | A1 to A4; B1 to B5 | A: Opus 5.5, max for the note, high for code and review. B1 to B5: Sonnet 5.5, medium |
| Sat 10 Oct | A5 by 16:00 (needs the team lead's go); B6 to B9 | A5: Opus 5.5, max. B6, B7: Opus 5.5, high. B8, B9: Sonnet 5.5, medium |
| Sun 11 Oct | B10; C1, C2 | B10: Opus 5.5, high (touches held-out patients). C1: Sonnet 5.5, medium. C2: Opus 5.5, high |
| Mon 12 Oct | C3, C4, C5 | Sonnet 5.5, high; Opus 5.5, high for C3 |
| Tue 13 Oct | C6, C7; D1. **18:00: Streamlit decision** | C6, C7: Sonnet 5.5, high. D1 reviews: Opus 5.5, high |
| Wed 14 Oct | Clinician looks at it; fixes from D1 and from the clinician | Sonnet 5.5, high |
| Thu 15 Oct | D2; clean-clone test; **freeze** | Sonnet 5.5, medium |

**Cut order.** First the meal what-if (B7's `whatif`, C3's panel), then patient search (C6), then polish of
the dark theme (C7). Then what-if for real patients and the table view of the small charts. If A5 has not run
by 10 Oct, 16:00, Part A is dropped whole and B7 writes no estimated trace for Shanghai patients. Never cut:
the reveal, the band, the limits line, the Evidence screen, the three states of the prompt.

---

## Part A: a band for the fingerstick estimate (science; stops 10 Oct)

### Task A1: Register the pass

**Files:** Modify `docs/PREREGISTRATION.md` (a fourth dated note to Amendment 3, appended).

- [ ] Read Amendment 3's sections F and "Band", and its three notes of 8 Oct, so the new note contradicts
  none of them.
- [ ] Write the note, before any code: what is estimated (the live and the in-hindsight estimates of
  section F, frozen); the two band constructions compared on development patients (both use only
  calibration-window quantities and fingerstick times, never a hidden reading):
  (1) the filter's own spread: half-widths `1.2816 x sd(t)`, `sd(t)` the filter's state spread at `t`;
  (2) the same, rescaled per patient by `profile_sigma / fast_sd`;
  the choice rule (mean coverage on development patients nearest 80 %; ties to the one with more patients
  within 70 to 90 %); what the one held-out pass reports (mean coverage, per-patient range, patients within 70
  to 90 %, coverage by day since the sensor, at k = 3 primary and k = 5 reported); that it is descriptive with
  no bar; the cohort (section F's, `why_not`); the cut rule of the kickoff record.
- [ ] Commit: `docs: register the band of the fingerstick estimate (note to Amendment 3)`.

### Task A2: The spread of the filter

**Files:** Create `src/chhaya/twin/stickband.py`; Test `tests/test_stickband.py`.

**Interfaces.** Produces:
`deviation_sd(t_obs, t_eval, cfg: FilterConfig = FilterConfig(), smooth: bool = False, strictly_before: bool = False) -> np.ndarray`
(the spread, in mg/dL, of the fading deviation at each `t_eval` given fingersticks at `t_obs`; it does not
take the readings, because a Kalman variance does not depend on them) and
`band(est, sd, scale: float = 1.0, z: float = 1.2816) -> tuple[np.ndarray, np.ndarray]`.

- [ ] Tests first, each asserting a number: with no fingerstick the spread is `cfg.fast_sd` everywhere; at a
  fingerstick it is `sqrt(fast_sd^2 * obs_sd^2 / (fast_sd^2 + obs_sd^2))` (12.86 for the registered filter);
  long after one it returns to within 1 % of `fast_sd` after `5 * tau_min`; `strictly_before=True` leaves a
  reading stamped at a fingerstick's own minute at the prior spread; the smoothed spread is never above the
  filtered one; fingersticks in any order give the same answer; `band` is symmetric and `scale=1` leaves it
  unchanged.
- [ ] Run them, see them fail, implement by mirroring the recursion of `chhaya.twin.assimilate.deviation`
  (same `a = exp(-dt / tau)`, same gain) without touching that module. One more test: `deviation` still
  returns what it returned (import it, compare with a stored vector from the current commit).
- [ ] `ruff`, commit.

### Task A3: The experiment module

**Files:** Create `src/chhaya/eval/stickband.py`; Test `tests/test_eval_stickband.py`.

**Interfaces.** Consumes `chhaya.eval.fingersticks.estimates`, `why_not`, `REGISTERED_FILTER`, `REGISTERED_K`;
`chhaya.eval.descriptive.profile_sigma`, `pooled_line`, `check_committed`, `refuse_second_pass`, `provenance`,
`write_outputs`, `day_index`; `chhaya.eval.metrics.coverage`. Produces
`band_of(rec, k_days, pooled, construction: str, which: str = "live") -> dict` with keys `t`, `est`, `lo`,
`hi` (this is what Task B7 calls), `score_recording(...) -> dict | None`, `run(recs, confirm) -> dict`, and
the command `python -m chhaya.eval.stickband [--confirm]` writing `results/stickband/shanghai[-dev]/`.

- [ ] Tests first: **leakage**: replace every hidden sensor reading of a synthetic recording with a
  different number and assert `est`, `lo`, `hi` are identical (rule 1); a recording outside section F's cohort
  returns `None`; a development run never loads a test patient into a score (monkeypatch `is_dev_patient`);
  `--confirm` refuses on uncommitted `src/` and refuses a second pass; coverage of a band that contains every
  reading is 1.0 and of one that contains none is 0.0; patients, not recordings, are the unit of the summary.
- [ ] Implement; `ruff`; commit.

### Task A4: Reviews, development run, freeze

- [ ] `mle-reviewer` and `python-reviewer` on A2 and A3; fix findings test-first; record them in an addendum
  to the note.
- [ ] `python -m chhaya.eval.stickband` (development patients). Read the report; apply the choice rule; write
  the frozen construction into the addendum. Commit results and the addendum together.

### Task A5: The one held-out pass (stop for the team lead's go)

- [ ] **Stop and ask.** It scores held-out patients once and cannot be repeated.
- [ ] `python -m chhaya.eval.stickband --confirm`; write `docs/decisions/2026-10-10-stickband.md` (what it is,
  the numbers, what a reader should weigh, consequences for the product with the exact sentence for the
  screen, the claim to quote); `healthcare-reviewer` on that wording; update PROGRESS, roadmap, CLAUDE.md and
  `claims.py` (a tenth result) in the same commit.

---

## Part B: the bundle

### Task B1: `claims.py`, the nine results

**Files:** Create `src/chhaya/product/__init__.py`, `src/chhaya/product/claims.py`; Test `tests/test_product_claims.py`.

**Interfaces.** Produces `CLAIMS: tuple[Claim, ...]` with
`Claim(id, grade, bars, title, sub, claim, bar_text: tuple[str, ...], cohort, command, record, figure: dict)`,
`grade` in `{"pass", "miss", "descriptive"}`, in the order of the mock's Evidence screen.

- [ ] Tests: each claim's text equals the "claim to quote" section of its record after whitespace is
  collapsed (Gate 2 is the documented exception: its record's claim minus the clause "lasts about five days",
  plus the correction in the expiry record; the test checks the two halves against the two records); no claim
  contains "alarm"; every `record` path exists; every `command` names a module that imports; the tally is 5
  bars passed, 4 missed, 5 descriptive.
- [ ] Implement from the mock's `EV` array; commit.

### Task B2: `wording.py`, the reviewed wording

**Files:** Create `src/chhaya/product/wording.py`; Test `tests/test_product_wording.py`.

**Interfaces.** Produces module constants (`LIMITS`, `BAND`, `DAYS_NOTE`, `TREATMENT_CHANGED`,
`SINCE_SENSOR`, `NOT_ESTIMATED`, `PROMPT`, `PROMPT_ABOUT`, `PROMPT_NONE`, `PROMPT_NOT_COMPUTED`,
`NOT_COMPUTED_REASONS`, `KEEP_FINGERSTICKS`, `LIST_NOTE`, `LIST_NOTE_PROMPT`, `PSEUDONYMS`, `FUSION`) and
`fill(template: str, **gaps) -> str`, which raises on a gap left unfilled.

- [ ] Tests: each constant, with its gaps turned into the record's own bracketed words, is found in the named
  record's "Consequences for the product" (or, for `LIMITS`, in the kickoff prompt and the expiry record);
  `fill` raises `KeyError` on a missing gap; none contains "alarm".
- [ ] Implement; commit.

### Task B3: `names.py`, `record.py`, `treatment.py`

**Files:** Create the three modules; Test `tests/test_product_small.py`.

**Interfaces.**
`pseudonym(patient_id: str, dataset: str, sex: str | None) -> str`;
`fhir_record(rec: Recording, synthetic: bool = False) -> dict` (a `Bundle` of `Patient`, `Condition`,
`Observation`s for HbA1c, fasting glucose and BMI where recorded, `MedicationStatement`s from the agents
list; `meta.tag` says synthetic when it is);
`treatment_since(rec: Recording, k_days: float) -> dict` with `state` in `{"changed", "none",
"not_recorded"}` and `day` when changed, by the three comparisons of the case series (agents listed, insulin
given, pump used) between the dose table before and after the split; dose amounts are not compared.

- [ ] Tests: the same id always gives the same name and two cohorts draw from different lists; a missing sex
  gives no honorific; `"Mrs. R."` is never produced for a real id; a NaN age or HbA1c is left out of the
  record, never written as `NaN`; a recording with an empty dose table is `not_recorded`, never `none`; adding
  a pump dose after the split turns `none` into `changed` with the right day; a dose of the same agent at a
  different amount stays `none`.
- [ ] Implement; commit.

### Task B4: `synthetic.py`, Mrs. R.

**Files:** Create `src/chhaya/product/synthetic.py`; Test `tests/test_product_synthetic.py` (marked `slow`).

**Interfaces.** Produces `mrs_r(seed: int = SEED) -> Recording` (`dataset="synthetic"`,
`patient_id="mrs-r"`, 11 days, 15-minute sensor, logged meals, six fingersticks a day on the meter's scale,
a dose table with a change on day 2 after the split, `static["synthetic"] = True`,
`static["genetic_marker"] = "synthetic field"`) and `WEAR_DAYS = 5.0`.

- [ ] Tests: `validate()` passes; the same seed gives the same recording; fingersticks read above the sensor
  on average (the sensor reads lower, as in Shanghai); the hidden-window mean lies 15 to 30 mg/dL below the
  wear's mean (the built-in drift); every fingerstick lies inside the recording; the recording is inside
  section F's cohort at k = 5 (`why_not` is `None`) and `run_reveal(rec, 5.0)` returns a reveal.
- [ ] Implement with the twin's own simulator, as `tests/conftest.py::make_recording` does; commit.

### Task B5: `patient.py`, one patient's bundle

**Files:** Create `src/chhaya/product/patient.py`; Test `tests/test_product_patient.py`.

**Interfaces.** Consumes B3, B4, `chhaya.eval.reveal.run_reveal` or a cached trace dict (`chhaya.eval.traces`),
`chhaya.eval.fingersticks.estimates`, `chhaya.twin.staleness`, `chhaya.eval.descriptive.profile_sigma`,
and (if Part A ran) `chhaya.eval.stickband.band_of`. Produces
`wear_report(rec, k_days) -> dict`, `shadow_days(trace: dict, rec, k_days) -> list[dict]`,
`since_sensor(rec, k_days, pooled) -> dict`, `prompt_state(rec, k_days, pooled, thresholds: dict[float, float]) -> dict`,
`patient_bundle(rec, k_days, trace: dict | None, pooled, thresholds, name: str) -> dict` and
`SCHEMA = 1`. `MIN_STICKS_PER_DAY = 4.6`, `LAST_TESTED_DAY = 11`.

- [ ] Tests: **leakage**: change the hidden sensor readings and assert that only `days[].sensor` and
  `days[].inside_band` differ in the bundle; a gap of more than 30 minutes in the sensor becomes a `null` in
  the arrays, not an interpolated value; `since` is `withheld` below 4.6 fingersticks a day and `outside`
  after day 11, each with its reason from `wording.NOT_COMPUTED_REASONS`; `prompt` is `not_computed` for a wear
  that is neither 3 nor 5 days, for fewer than 4.6 a day, and when first raised after day 11, and a prompt
  raised by day 11 stays raised with its day; no key of the bundle is named or valued with `tir`, `tbr`,
  `gmi` or `hba1c_est`; every number is finite or `null` (`json.dumps(..., allow_nan=False)` succeeds);
  a patient with no fingersticks gets `since.state == "withheld"` and `prompt.state == "not_computed"`.
- [ ] Implement; commit.

### Task B6: `evidence.py`

**Files:** Create `src/chhaya/product/evidence.py`; Test `tests/test_product_evidence.py`.

**Interfaces.** Produces `evidence(results_dir: Path = RESULTS_DIR) -> dict` (`results`, `tally`,
`limits`, `data`), each figure value read from a `summary.json` by a path named in `claims.py`.

- [ ] Tests: every figure value, rounded as shown, appears in its claim's text; a missing results file raises
  with the path and the command that regenerates it; the label check gives 8 of 64 and 732 of 809; both AUROCs
  of the prompt are present with their intervals; the output passes `json.dumps(..., allow_nan=False)`.
- [ ] Implement; commit.

### Task B7: `build.py` and the committed demo bundle

**Files:** Create `src/chhaya/build.py`, `src/chhaya/dashboard/demo/` (written by the command);
Test `tests/test_build.py` (the rebuild test is `slow`).

**Interfaces.** `build_demo(out: Path) -> None`; `python -m chhaya.build [--out DIR]`. `index.json` holds
`schema`, `built` (commit, date, `bundle: "demo" | "local"`), `today`, and `patients[]` (id, name, cohort,
wear days, days since, treatment, prompt, fingersticks a day).

- [ ] Tests: a rebuild into a temporary folder equals the committed demo bundle file for file; `index.json`
  lists exactly Mrs. R.; the what-if arrays for the largest logged meal of the last day exist at 20 to 100 g
  in steps of 10 and each has a band.
- [ ] Implement; run `python -m chhaya.build`; commit code and bundle together.

### Task B8: real patients (`--real --confirm`)

**Files:** Modify `src/chhaya/build.py`; Test `tests/test_build_real.py` (unit tests on synthetic recordings;
the real run is marked `data`).

- [ ] Tests: `--real` without `--confirm` exits with the reason; uncommitted `src/` exits; a development
  patient passed in is refused; the Shanghai prompt counts that differ from `results/staleness/shanghai/`
  stop the build with both numbers in the message; nothing is written under `results/`.
- [ ] Implement; run it from a checkout with the data and the trace cache; read three bundles by eye against
  the Gate 2 `metrics.csv` (RMSE, coverage). Nothing from `artifacts/` is committed.

---

## Part C: the page

### Task C1: server, skeleton, tokens, fonts

**Files:** Create `src/chhaya/dashboard/__init__.py`, `__main__.py`, `static/index.html`,
`static/css/{tokens,base,components,views}.css`, `static/js/{app,data,ui}.js`, `static/fonts/` with
`OFL.txt`; Test `tests/test_dashboard_server.py`.

**Interfaces.** `make_server(bundle: Path, port: int = 0) -> ThreadingHTTPServer` bound to `127.0.0.1`;
`/` serves the page, `/data/...` the bundle, anything else under `static/`. `python -m chhaya.dashboard
[--bundle DIR] [--port N] [--no-open]` prints the address and which bundle it serves.

- [ ] Tests: `/`, `/data/index.json` and a font return 200 with the right content type; `/data/../build.py`
  and an encoded traversal return 404; a missing bundle folder exits with the command that builds it; the
  server binds to loopback only.
- [ ] Implement; the header, the limits line, the three routes, the theme toggle (remembered in
  `localStorage`, inside try/catch), the "bundle missing" and "schema mismatch" screens (Review Focus 1).
- [ ] **Fonts need one small download** (the licence text) or a copy from the environment: ask the team lead
  before fetching anything. Commit.

### Task C2: `chart.js`

**Files:** Create `static/js/chart.js`.

**Interfaces.** `frame(box, opts)`, `zones(svg, id, f)`, `linePath(ts, vs, X, Y)` (breaks at `null`),
`bandPath(...)`, `heroChart(box, day, {onRead})` returning `{setReveal(p), setCross(t), destroy()}`,
`profileChart(box, wear)`, `whatIfChart(box, logged, simulated)`.

- [ ] Port from `m4-mocks/mock.js`; add gap handling (Review Focus 3); keyboard reading with arrow keys,
  Home, End and Escape; reduced motion; the table twin. Check in the browser against the demo bundle.

### Task C3: patient screen

- [ ] `static/js/views/patient.js`: every panel of the spec from `patients/<id>.json`, each with its absent
  state (Review Focus 2); the hero's inline note when the prompt is raised; wording only from the bundle's
  `wording` block. Verify at 1440, 820 and 375 px in both themes; console clean.

### Task C4: clinic list. Task C5: Evidence

- [ ] `views/clinic.js`: columns, sorting with `aria-sort`, cohort filter, cards under 860 px, the three
  sentences under the list, rows open the patient.
- [ ] `views/evidence.js`: tally, the fusion sentence, nine (or ten) results with the dot-and-interval
  figures, the label-check pictogram, limits, data and licences, the side list on wide screens.
- [ ] Compare every number on the Evidence screen with `results/` by reading `evidence.json` next to the
  summaries. Verify at the three widths.

### Task C6: search, states, access

- [ ] Patient search (Ctrl K, arrows, Enter, Escape); skeletons; focus order and visible rings; `aria-live`
  on the readout; the "no hidden sensor" and "no estimated trace" states of the hero.

### Task C7: verification pass

- [ ] Run `python -m chhaya.dashboard`; drive all three screens at desktop, tablet and phone width in light
  and dark; screenshot each; fix what looks off; confirm no request leaves `127.0.0.1` (network panel) and the
  console is clean. No "done" from code alone.

---

## Part D: close

### Task D1: reviews

- [ ] `healthcare-reviewer` on every screen's wording and states; `python-reviewer` on `product/`,
  `build.py`, `dashboard/`; `mle-reviewer` on the bundle's leakage test and the `--real` guards. Fix
  test-first; list what was found and fixed in the commit message.

### Task D2: docs and the clean run

- [ ] README: how to run the dashboard, a screenshot of the synthetic patient (labelled synthetic), the
  Evidence tally. CLAUDE.md: architecture and commands. PROGRESS and the roadmap Status table. Remove
  `m4-mocks/` once the page replaces it.
- [ ] From a fresh clone in a second folder: `uv sync`, `uv run pytest -q`, `uv run python -m chhaya.build`,
  `uv run python -m chhaya.dashboard --no-open`; the page loads with the network unplugged.
