"""Band recalibration (Amendment 3, "Descriptive, no bar").

The 80 % band of the reveal is widened or narrowed about the estimate by one factor, or by one factor per day
since the sensor. The factor and the choice between the two designs come from CGMacros development patients;
test patients only report: mean coverage, and how many patients fall within 70 to 90 %. The estimator and the
Gate 2 results are not touched: the factor is applied to cached traces, and later by the dashboard.

Usage: python -m chhaya.eval.calibrate             (development patients: choose, write band.json)
       python -m chhaya.eval.calibrate --confirm   (test patients, once, with the committed band.json)
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import REPO_ROOT, RESULTS_DIR
from chhaya.eval.descriptive import (
    MIN_DAY_READINGS,
    check_committed,
    day_index,
    provenance,
    table,
    write_outputs,
)
from chhaya.eval.gate2 import COVERAGE_BAND, _clean, _git
from chhaya.eval.gate3 import refuse_second_run
from chhaya.eval.metrics import coverage
from chhaya.eval.traces import load_traces, require_gate2, trace_provenance

TARGET = 0.80
GRID = np.round(np.arange(0.50, 2.0001, 0.01), 2)  # the factors tried
MIN_FACTOR_PATIENTS = 10  # a day needs this many development patients to get its own factor ...
MIN_DAY_SHARE = 0.8  # ... and this share of them: later days hold whoever is left, at the end of their wear
MIN_GAIN = (
    0.02  # a factor per day must bring each day's coverage this much closer to target, or it is not used
)
PRIMARY_K = 5.0  # the Gate 2 setting; the factor is chosen there
ALSO_K = 3.0  # reported with the same factor
FOLDER = RESULTS_DIR / "calibrate"
BAND = FOLDER / "cgmacros-dev" / "band.json"
UNCHANGED = {"design": "single", "factor": 1.0, "by_day": {}}


def rescale(tr: dict, factor) -> tuple[np.ndarray, np.ndarray]:
    """The band with both half-widths about the estimate multiplied by `factor` (a number, or one per reading).

    A half-width is signed: where the estimate lies outside its own band one of them is negative. That keeps a
    factor of 1 the band exactly as Gate 2 scored it, whatever the estimate does.
    """
    return tr["twin"] - factor * (tr["twin"] - tr["lo"]), tr["twin"] + factor * (tr["hi"] - tr["twin"])


def prepare(tr: dict) -> dict:
    """What the factor fit needs of a trace: per hidden reading its distance from the estimate, the band's two
    half-widths and the day since the sensor; and the coverage of the band as it is, the way Gate 2 counts it."""
    return {
        "patient_id": str(tr["patient_id"]),
        "off": tr["truth"] - tr["twin"],
        "down": tr["twin"] - tr["lo"],
        "up": tr["hi"] - tr["twin"],
        "day": day_index(tr["t"], float(tr["k_days"]) * 1440.0),
        "gate2_cov": coverage(tr["truth"], tr["lo"], tr["hi"]),
    }


def inside(item: dict, factor) -> np.ndarray:
    """Which hidden readings the band holds once both half-widths are multiplied by `factor`."""
    return (item["off"] >= -factor * item["down"]) & (item["off"] <= factor * item["up"])


def factors(item: dict, design: dict):
    """The factor each reading of `item` gets under `design`; days past the last fitted day use the last one."""
    if design["design"] == "single":
        return design["factor"]
    by_day = {int(d): f for d, f in design["by_day"].items()}
    last = max(by_day)
    return np.array([by_day[min(int(d), last)] for d in item["day"]])


def patient_coverage(items: list[dict], design: dict = UNCHANGED) -> pd.Series:
    """Share of hidden readings inside the band, per patient (recordings of one patient are averaged)."""
    rows = [
        {"patient_id": i["patient_id"], "cov": float(np.mean(inside(i, factors(i, design))))} for i in items
    ]
    return pd.DataFrame(rows).groupby("patient_id")["cov"].mean()


def fit_factor(items: list[dict]) -> float:
    """The factor whose mean coverage over patients is closest to 80 %; of two equally close, the one nearer 1."""
    if not items:
        raise ValueError("no trace to fit a band factor on")
    # coverage of every recording at every factor of the grid, then patients, then the cohort
    grid = GRID[None, :]
    curves = pd.DataFrame(
        [
            np.mean(
                (i["off"][:, None] >= -grid * i["down"][:, None])
                & (i["off"][:, None] <= grid * i["up"][:, None]),
                axis=0,
            )
            for i in items
        ],
        index=[i["patient_id"] for i in items],
    )
    miss = np.abs(curves.groupby(level=0).mean().mean(axis=0).to_numpy() - TARGET)
    best = min(range(GRID.size), key=lambda j: (round(float(miss[j]), 9), abs(float(GRID[j]) - 1.0)))
    return float(GRID[best])


def on_day(item: dict, d: int) -> dict | None:
    """The readings of one day since the sensor, or None when that day holds too few."""
    m = item["day"] == d
    if m.sum() < MIN_DAY_READINGS:
        return None
    return {"patient_id": item["patient_id"], **{key: item[key][m] for key in ("off", "down", "up", "day")}}


def fit_by_day(items: list[dict]) -> dict[str, float]:
    """One factor per day since the sensor, for the consecutive days that most of the cohort reaches.

    Recordings end at different lengths. A late day holds the few patients still recording, on the last days
    of their sensor, so a factor fitted there would describe who is left, not how the band ages.
    """
    n_patients = len({i["patient_id"] for i in items})
    enough = max(MIN_FACTOR_PATIENTS, int(np.ceil(MIN_DAY_SHARE * n_patients)))
    out: dict[str, float] = {}
    d = 1
    while True:
        sub = [s for s in (on_day(i, d) for i in items) if s is not None]
        if len({s["patient_id"] for s in sub}) < enough:
            return out
        out[str(d)] = fit_factor(sub)
        d += 1


def within(cov: pd.Series) -> int:
    return int(((cov >= COVERAGE_BAND[0]) & (cov <= COVERAGE_BAND[1])).sum())


def day_gap(by_day: pd.DataFrame) -> float:
    """How far the coverage of each day lies from 80 %, averaged over days (0.05 is five points)."""
    return float((by_day.groupby("day")["cov"].mean() - TARGET).abs().mean())


def prefer_by_day(gaps: dict, inside: dict, fitted: bool) -> bool:
    """Whether the factor per day replaces the single factor, from what both did on patients left out.

    It has more freedom, so it must earn its place twice: each day's coverage at least MIN_GAIN closer to
    target, and no fewer patients within 70 to 90 %, which is the number the registration reports.
    """
    closer = fitted and gaps["single"] - gaps["by_day"] >= MIN_GAIN
    return bool(closer and inside["by_day"] >= inside["single"])


def choose(items: list[dict]) -> dict:
    """Fit both designs on development patients and pick one, leaving each patient out in turn.

    One factor already brings a patient's coverage over the whole hidden window to target; what a factor per
    day can add is a band that is right on day 1 and still right on day 5. So for patients left out of the
    fit both are measured: how far each day's coverage lies from 80 %, and how many patients fall within
    70 to 90 %. `prefer_by_day` decides. The factors written are then fitted on all development patients.
    """
    patients = sorted({i["patient_id"] for i in items})
    by_day = fit_by_day(items)
    inside = {"single": 0, "by_day": 0}
    cells: dict[str, list[dict]] = {"single": [], "by_day": []}
    for p in patients:
        rest = [i for i in items if i["patient_id"] != p]
        held = [i for i in items if i["patient_id"] == p]
        designs = {
            "single": {"design": "single", "factor": fit_factor(rest)},
            "by_day": {"design": "by_day", "by_day": fit_by_day(rest)},
        }
        for name, design in designs.items():
            if name == "by_day" and not design["by_day"]:
                continue
            inside[name] += within(patient_coverage(held, design))
            for d in by_day:  # the same days for both designs
                sub = [s for s in (on_day(i, int(d)) for i in held) if s is not None]
                if sub:
                    cells[name].append({"day": int(d), "cov": float(patient_coverage(sub, design).iloc[0])})
    gaps = {name: day_gap(pd.DataFrame(rows)) if rows else float("nan") for name, rows in cells.items()}
    return {
        "design": "by_day" if prefer_by_day(gaps, inside, bool(by_day)) else "single",
        "factor": fit_factor(items),
        "by_day": by_day,
        "left_out_day_gap": gaps,
        "left_out_patients_within": inside,
        "n_patients": len(patients),
        "target": TARGET,
    }


def evaluate(items: list[dict], design: dict) -> dict:
    """Coverage before and after the recalibration: mean over patients, range, patients within 70 to 90 %.

    "Before" has to be the coverage Gate 2 counted, recording by recording, or the comparison is with some
    other band. That is checked here and the run stops if it is not so.
    """
    apart = max(abs(float(np.mean(inside(i, 1.0))) - i["gate2_cov"]) for i in items)
    if apart > 1e-6:
        raise SystemExit(
            f"the unchanged band is not the band Gate 2 scored: coverage differs by {apart:.4f} in a recording"
        )
    out: dict = {"n_patients": len({i["patient_id"] for i in items}), "before_differs_from_gate2_by": apart}
    for name, d in (("before", UNCHANGED), ("after", design)):
        cov = patient_coverage(items, d)
        out[name] = {
            "mean_coverage": float(cov.mean()),
            "min": float(cov.min()),
            "max": float(cov.max()),
            "patients_within": within(cov),
        }
    by_day = []
    for d in sorted({int(x) for i in items for x in np.unique(i["day"])}):
        sub = [s for s in (on_day(i, d) for i in items) if s is not None]
        if sub:
            by_day.append(
                {
                    "day": d,
                    "n_patients": len({s["patient_id"] for s in sub}),
                    "before": float(patient_coverage(sub).mean()),
                    "after": float(patient_coverage(sub, design).mean()),
                }
            )
    out["by_day"] = by_day
    return out


def _report(result: dict) -> str:
    design = result["design"]
    lines = ["# Band recalibration", ""]
    lines.append(
        "Test patients; the factor was fixed on development patients. Descriptive: no bar."
        if result["confirmatory"]
        else "Development patients: the factor is chosen here, so its coverage below is in-sample."
    )
    chosen = (
        f"one factor, {design['factor']:.2f}"
        if design["design"] == "single"
        else f"per day, {design['by_day']}"
    )
    lines += [
        "",
        f"Design: {chosen}. On development patients left out of the fit, distance of each day's coverage from "
        f"80 %: {design['left_out_day_gap']}; patients within 70 to 90 %: {design['left_out_patients_within']}.",
    ]
    if result["confirmatory"]:
        verdict = "is used" if result["use_recalibrated_band"] else "is not used: it did not transfer"
        lines += ["", f"On these patients, at k = {PRIMARY_K:g}: the recalibrated band {verdict}."]
    for block in result["by_k"]:
        lines += ["", f"## k = {block['k_days']:g} days ({block['n_patients']} patients)", ""]
        rows = [{"band": name, **block[name]} for name in ("before", "after")]
        lines += [table(rows, digits=3), "", table(block["by_day"], digits=3)]
    return "\n".join(lines) + "\n"


def transfers(block: dict) -> bool:
    """Whether the recalibrated band is the one to show, judged on the patients it was not fitted on.

    Yes only if its mean coverage is no further from 80 % than the band as Gate 2 scored it and no fewer
    patients fall within 70 to 90 %. Otherwise the band stays as it was and the result says so.
    """
    before, after = block["before"], block["after"]
    no_further = abs(after["mean_coverage"] - TARGET) <= abs(before["mean_coverage"] - TARGET)
    return bool(no_further and after["patients_within"] >= before["patients_within"])


def run(items_by_k: dict[float, list[dict]], confirmatory: bool, design: dict | None = None) -> dict:
    """Report every k under one design. Without a design (development) it is chosen here, on the primary k."""
    if design is None:
        design = choose(items_by_k[PRIMARY_K])
    by_k = [{"k_days": k, **evaluate(items, design)} for k, items in items_by_k.items()]
    primary = next(b for b in by_k if b["k_days"] == PRIMARY_K)
    # only held-out patients can say whether the factor transfers; on development patients it is in-sample
    use = transfers(primary) if confirmatory else None
    return {"confirmatory": confirmatory, "design": design, "use_recalibrated_band": use, "by_k": by_k}


def _digest(design: dict) -> str:
    """A hash of the design's content, the same whatever the file's line endings or key order."""
    return hashlib.sha256(json.dumps(design, sort_keys=True).encode("utf-8")).hexdigest()


def write_band(design: dict, path: Path = BAND) -> str:
    """Write the chosen design as strict JSON and return the hash that identifies it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_clean(design), indent=2, allow_nan=False), encoding="utf-8")
    return read_band(path)[1]


def read_band(path: Path = BAND) -> tuple[dict, str]:
    design = json.loads(path.read_text(encoding="utf-8"))
    return design, _digest(design)


def check_band_committed(tracked: str | None, status: str | None) -> None:
    """The band a test pass reads was fixed beforehand: the file is in git and has not been touched since."""
    if not tracked or status is None:
        raise SystemExit(
            f"{BAND} is not committed: choose the band on development patients and commit it before the test pass"
        )
    if status:
        raise SystemExit(
            f"{BAND} has changed since it was committed: commit it, or restore it, before the test pass"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="report on the test patients; this is done once")
    args = ap.parse_args()
    out_dir = FOLDER / ("cgmacros" if args.confirm else "cgmacros-dev")
    split = "test" if args.confirm else "dev"
    design = digest = None
    if args.confirm:
        check_committed(_git("status", "--porcelain", "--", "src"))
        refuse_second_run(out_dir)
        rel = BAND.relative_to(REPO_ROOT).as_posix()
        check_band_committed(
            _git("ls-files", "--error-unmatch", "--", rel), _git("status", "--porcelain", "--", rel)
        )
        design, digest = read_band()
    items_by_k = {}
    for k in (PRIMARY_K, ALSO_K):
        traces = load_traces("cgmacros", split, k)
        if args.confirm:
            require_gate2(traces, k)
        elif not traces:
            raise SystemExit(
                f"no {split} traces at k = {k:g}: run python -m chhaya.eval.traces --split {split}"
            )
        items_by_k[k] = [prepare(tr) for tr in traces]
    result = run(items_by_k, args.confirm, design)
    report = _report(result)  # everything is computed before the first file is written
    if not args.confirm:
        digest = write_band(result["design"])
    prov = provenance(
        args.confirm, k=[PRIMARY_K, ALSO_K], band_sha256=digest, traces=trace_provenance("cgmacros", split)
    )
    write_outputs(out_dir, result, report, prov)
    print(report)


if __name__ == "__main__":
    main()
