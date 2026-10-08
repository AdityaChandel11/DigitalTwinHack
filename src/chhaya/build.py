"""Build the bundle the dashboard reads. Nothing is fitted while the dashboard runs; it is all done here.

    python -m chhaya.build                    the demo bundle: the synthetic patient and the Evidence data
    python -m chhaya.build --real --confirm   the local bundle: the demo plus every held-out patient

The demo bundle (`src/chhaya/dashboard/demo/`) is committed and needs no dataset. The local bundle goes to
`artifacts/`, which git ignores: per-reading arrays of real patients are patient data (rule 6). `--real` reads
held-out patients, so it needs `--confirm` and committed code, scores nothing, writes nothing under `results/`,
and stops unless it reproduces the committed prompt counts of the staleness pass.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from chhaya.config import REPO_ROOT, RESULTS_DIR, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.descriptive import check_committed, pooled_line
from chhaya.eval.fingersticks import why_not
from chhaya.eval.gate2 import _git
from chhaya.eval.reveal import run_reveal
from chhaya.product import wording
from chhaya.product.evidence import evidence
from chhaya.product.names import pseudonyms
from chhaya.product.patient import SCHEMA, patient_bundle, stick_estimate, twin_estimate
from chhaya.product.synthetic import START, WEAR_DAYS, mrs_r
from chhaya.product.whatif import meal_whatif

DEMO_DIR = Path(__file__).parent / "dashboard" / "demo"
LOCAL_DIR = REPO_ROOT / "artifacts"
K_SHANGHAI, K_CGMACROS = 3.0, 5.0  # the primary calibration lengths of section F and of Gate 2
# written for the product on 9 Oct from the stickband record; not yet read by healthcare-reviewer (Task D1)
STICK_BAND = (
    "80 % band; on held-out patients tested about six times a day it held 86 % of sensor readings on average "
    "and between 57 % and 100 % for an individual. About 45 mg/dL each side: a rough estimate, on the sensor's "
    "scale, not a measurement."
)


def thresholds(results_dir: Path = RESULTS_DIR) -> dict[float, float]:
    """The prompt's threshold at each tested wear length, as the staleness pass set them on development recordings."""
    path = results_dir / "staleness" / "shanghai" / "summary.json"
    blocks = json.loads(path.read_text(encoding="utf-8"))["by_k"]
    return {float(b["k_days"]): float(b["score"]["threshold"]) for b in blocks if "score" in b}


def words() -> dict:
    """Every sentence the page shows that is not a number: the page holds no wording of its own."""
    out = {k.lower(): v for k, v in vars(wording).items() if k.isupper() and isinstance(v, str | dict)}
    out["band_twin"] = out.pop("band")
    out["band_fingersticks"] = STICK_BAND
    return out


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, allow_nan=False, ensure_ascii=False) + "\n", encoding="utf-8")


def _row(b: dict) -> dict:
    """A patient's line in the clinic list."""
    return {
        "id": b["id"], "name": b["name"], "cohort": b["cohort"], "synthetic": b["synthetic"],
        "wear_days": b["wear"]["days"], "days_since": b["days_since"], "treatment": b["treatment"],
        "prompt": {k: b["prompt"][k] for k in ("state", "day", "reason") if k in b["prompt"]},
        "sticks_per_day": b["since"]["per_day"], "dates": b.get("dates"),
    }  # fmt: skip


def demo_patient(th: dict[float, float]) -> dict:
    """Mrs. R., run through the real pipeline: the twin's reveal, the fingerstick code, the prompt."""
    rec = mrs_r()
    out = run_reveal(rec, WEAR_DAYS)
    estimate = twin_estimate({"t": out.t_test, "twin": out.twin, "lo": out.lo, "hi": out.hi, "day": out.day})
    b = patient_bundle(
        rec, WEAR_DAYS, name="Mrs. R.", cohort="synthetic", estimate=estimate, pooled=(0.0, 1.0), thresholds=th,
        synthetic=True,
    )  # fmt: skip
    b["dates"] = {"start": START.strftime("%Y-%m-%d"), "wear_days": int(WEAR_DAYS)}
    b["whatif"] = meal_whatif(rec, out, WEAR_DAYS)
    return b


def write_bundle(out: Path, patients: list[dict], kind: str) -> None:
    for b in patients:
        _write(out / "patients" / f"{b['id']}.json", b)
    _write(out / "evidence.json", evidence())
    index = {
        "schema": SCHEMA,
        "bundle": kind,
        "commit": _git("rev-parse", "--short", "HEAD"),
        "wording": words(),
        "patients": [_row(b) for b in patients],
    }
    _write(out / "index.json", index)


def check_prompt_counts(
    recs: list[Recording], pooled: tuple[float, float], results_dir: Path = RESULTS_DIR
) -> None:
    """Stop unless these recordings give back the counts the staleness pass committed: same data, same estimator."""
    from chhaya.eval.staleness import score_recording

    block = json.loads((results_dir / "staleness" / "shanghai" / "summary.json").read_text(encoding="utf-8"))[
        "by_k"
    ][0]
    h = block["score"]["threshold"]
    rows = [r for r in (score_recording(rec, K_SHANGHAI, pooled) for rec in recs) if r]
    found = (
        sum(r["drifted"] and r["score"] > h for r in rows),
        sum((not r["drifted"]) and r["score"] > h for r in rows),
    )
    want = (block["score"]["drifted_alarmed"], block["score"]["quiet_alarmed"])
    if found != want:
        raise SystemExit(
            f"prompt counts {found} do not reproduce the committed {want}: not the scored cohort"
        )


def real_patients(th: dict[float, float]) -> list[dict]:
    """Every held-out patient the committed runs scored: Shanghai (section F, k = 3) and CGMacros (Gate 2, k = 5)."""
    from chhaya.eval.gate2 import load
    from chhaya.eval.traces import load_traces, require_gate2

    out = []
    shanghai = load("shanghai")
    dev = [r for r in shanghai if is_dev_patient(r.patient_id)]
    held = [r for r in shanghai if not is_dev_patient(r.patient_id) and why_not(r, K_SHANGHAI) is None]
    pooled = pooled_line(dev, K_SHANGHAI)
    check_prompt_counts(held, pooled)
    names = pseudonyms(
        {r.patient_id for r in shanghai}, "shanghai", {r.patient_id: r.static.get("sex") for r in shanghai}
    )
    seen: set[str] = set()
    for rec in held:
        if rec.patient_id in seen:  # one recording a patient: the first
            continue
        seen.add(rec.patient_id)
        out.append(
            patient_bundle(
                rec,
                K_SHANGHAI,
                name=names[rec.patient_id],
                cohort="supervised",
                estimate=stick_estimate(rec, K_SHANGHAI, pooled),
                pooled=pooled,
                thresholds=th,
            )  # fmt: skip
        )

    cgmacros = {r.rec_id: r for r in load("cgmacros")}
    traces = load_traces("cgmacros", "test", K_CGMACROS)
    require_gate2(traces, K_CGMACROS)
    people = list(cgmacros.values())
    names = pseudonyms(
        {r.patient_id for r in people}, "cgmacros", {r.patient_id: r.static.get("sex") for r in people}
    )
    for tr in traces:
        rec = cgmacros[str(tr["rec_id"])]
        assert not is_dev_patient(rec.patient_id)
        out.append(
            patient_bundle(
                rec,
                K_CGMACROS,
                name=names[rec.patient_id],
                cohort="free-living",
                estimate=twin_estimate(tr),
                pooled=(0.0, 1.0),
                thresholds=th,
            )  # fmt: skip
        )
    return out


def check_real(confirm: bool, src_status: str | None) -> None:
    if not confirm:
        raise SystemExit("--real reads held-out patients: pass --confirm")
    check_committed(src_status)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--real",
        action="store_true",
        help="add every held-out patient (needs the datasets and the trace cache)",
    )
    ap.add_argument("--confirm", action="store_true", help="needed with --real")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    th = thresholds()
    patients = [demo_patient(th)]
    if args.real:
        check_real(args.confirm, _git("status", "--porcelain", "--", "src"))
        patients += sorted(real_patients(th), key=lambda b: b["name"].split()[-1])
    out = args.out or (LOCAL_DIR if args.real else DEMO_DIR)
    write_bundle(out, patients, "local" if args.real else "demo")
    n = np.sum([len(d["t"]) for b in patients for d in b["days"]])
    print(f"{len(patients)} patients, {int(n)} readings, written to {out}")


if __name__ == "__main__":
    main()
