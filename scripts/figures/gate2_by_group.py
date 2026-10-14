"""Display-only figure: Gate 2 per-participant results broken down by diagnosis group.

Reads the registered primary-analysis inclusion rule from results/gate2/cgmacros-test/metrics.csv.
No new statistics, no p-values, no subgroup intervals or medians.
Deterministic output: no random jitter.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from chhaya.config import REPO_ROOT, RESULTS_DIR
from chhaya.eval.gate2 import PRIMARY_K

METRICS_PATH = RESULTS_DIR / "gate2" / "cgmacros-test" / "metrics.csv"
OUTPUT_IMAGE = REPO_ROOT / "docs" / "images" / "gate2-by-group.png"


def load_gate2_participants() -> pd.DataFrame:
    """Apply the registered primary-analysis inclusion rule to Gate 2 test metrics."""
    if not METRICS_PATH.exists():
        raise FileNotFoundError(f"Missing metrics file: {METRICS_PATH}")

    df = pd.read_csv(METRICS_PATH)
    at_k = df[df["k_days"] == PRIMARY_K]
    valid = at_k[at_k["twin_rmse"].notna()]

    per = valid.groupby("patient_id").mean(numeric_only=True)
    diff = per["twin_rmse"] - per["day_rmse"]
    groups = valid.groupby("patient_id")["group"].first()

    result = pd.DataFrame({
        "patient_id": per.index,
        "diff": diff.values,
        "group": groups.values,
    })

    if len(result) != 19:
        raise ValueError(f"Expected exactly 19 participants, found {len(result)}")

    counts = result["group"].value_counts().to_dict()
    expected = {"t2d": 7, "prediabetes": 7, "healthy": 5}
    if counts != expected:
        raise ValueError(f"Expected counts {expected}, got {counts}")

    return result


def plot_gate2_by_group(df: pd.DataFrame, out_path: Path) -> None:
    # Groups configuration: order, label with n, color, y position
    group_specs = [
        {"key": "t2d", "label": "Type 2 diabetes\n(n = 7)", "color": "#dc2626", "y": 2},
        {"key": "prediabetes", "label": "Prediabetes\n(n = 7)", "color": "#4a3aa7", "y": 1},
        {"key": "healthy", "label": "Healthy\n(n = 5)", "color": "#0d9488", "y": 0},
    ]

    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=200)

    # Reference zero line
    ax.axvline(0, color="#6b7280", linestyle="--", linewidth=1.2, zorder=1)

    # Direction annotations
    ax.text(-0.2, 2.55, "← Twin closer (lower RMSE)", ha="right", va="bottom",
            fontsize=9.5, fontweight="600", color="#374151")
    ax.text(0.2, 2.55, "Average day closer →", ha="left", va="bottom",
            fontsize=9.5, fontweight="600", color="#374151")

    # Plot dots with deterministic spreading for overlapping points
    for spec in group_specs:
        sub = df[df["group"] == spec["key"]].sort_values("diff").reset_index(drop=True)
        y_base = spec["y"]

        # Deterministic y-offset to avoid exact overlaps
        diffs = sub["diff"].values
        y_offsets = [0.0] * len(diffs)
        for i in range(1, len(diffs)):
            if abs(diffs[i] - diffs[i - 1]) < 0.15:
                # Alternate offset deterministically
                y_offsets[i] = 0.08 if y_offsets[i - 1] <= 0 else -0.08

        for i, row in sub.iterrows():
            ax.scatter(
                row["diff"],
                y_base + y_offsets[i],
                color=spec["color"],
                s=90,
                alpha=0.9,
                edgecolors="#ffffff",
                linewidths=1.2,
                zorder=3,
            )

    ax.set_yticks([s["y"] for s in group_specs])
    ax.set_yticklabels([s["label"] for s in group_specs], fontsize=10, fontweight="500")
    ax.set_ylim(-0.6, 2.85)

    ax.set_xlabel("Twin RMSE minus average-day RMSE (mg/dL)", fontsize=10, fontweight="500", labelpad=8)
    ax.set_xlim(-7.5, 2.0)

    # Styling
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#d1d5db")
    ax.spines["bottom"].set_color("#d1d5db")
    ax.tick_params(colors="#374151", labelsize=9.5)
    ax.grid(axis="x", color="#f3f4f6", linestyle=":", linewidth=1, zorder=0)

    # Title and descriptive footnote
    fig.suptitle(
        "Gate 2 per-participant results by diagnosis group (CGMacros test split, k = 5 days)",
        fontsize=11,
        fontweight="bold",
        color="#111827",
        y=0.98,
    )
    plt.figtext(
        0.5,
        0.01,
        "Descriptive display of the registered per-participant results. Not a test. Seven type 2 participants: too few for their own test.",
        ha="center",
        fontsize=8.5,
        fontstyle="italic",
        color="#4b5563",
    )

    plt.tight_layout(rect=[0, 0.05, 1, 0.94])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, metadata={"Date": None})
    plt.close(fig)


def main() -> None:
    df = load_gate2_participants()
    counts = df["group"].value_counts()
    print("Gate 2 test participants count = 19:")
    for group, n in counts.items():
        print(f"  {group}: {n}")

    plot_gate2_by_group(df, OUTPUT_IMAGE)
    print(f"Saved figure to: {OUTPUT_IMAGE}")


if __name__ == "__main__":
    main()
