"""
src/plot_reported.py
====================
Charts of results that ALREADY EXIST -- nothing here is estimated, predicted or
invented. There are exactly two sources, and every chart is labelled with which one it
came from:

  SOURCE 1 -- THE PAPER'S OWN PUBLISHED NUMBERS.
     Transcribed from Table II of Li et al., "Noninvasive Blood Glucose Monitoring Using
     Spatiotemporal ECG and PPG Feature Fusion and Weight-Based Choquet Integral
     Multimodel Approach", IEEE TNNLS 2024. These are the AUTHORS' results on THEIR
     private dataset, not ours. They are plotted so the target is visible.

  SOURCE 2 -- OUR OWN MEASURED RESULTS on the real D1NAMO data.
     Taken from the verified evaluation runs logged in eval_progress.log and
     temporal_progress.log (4054 real ECG windows, 9 Type-1 patients). These are real
     measurements from our pipeline.

The distinction matters: the paper had ECG + PPG signals and a ResNet morphological
branch. D1NAMO is ECG-only, so our reproduction implements the 80 ECG temporal features
and the Choquet fusion, and cannot implement the PPG half. Charts that put the two side
by side say so explicitly, because comparing them without that caveat would be
misleading.

Run:  python -m src.plot_reported
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIG_DIR = os.path.join("figures", "results")

BLUE, ORANGE, GREEN = "#1f6feb", "#bc4c00", "#1a7f37"
INK, MUTED = "#24292f", "#57606a"
ACCENT = "#bc4c00"

# ----------------------------------------------------------------------------------
# SOURCE 1: the paper's Table II, transcribed exactly as printed.
# Tenfold cross-validation, three signal configurations.
# ----------------------------------------------------------------------------------
PAPER_TABLE_II = pd.DataFrame({
    "Fold": list(range(1, 11)),
    "ECG_RMSE":  [2.04, 1.16, 1.49, 1.85, 1.42, 1.50, 1.67, 1.17, 1.98, 1.31],
    "ECG_MARD":  [11.54, 12.70, 17.72, 13.39, 14.47, 13.35, 14.35, 12.43, 13.74, 15.14],
    "ECG_ZA":    [79.61, 80.52, 77.38, 76.46, 72.30, 77.83, 77.19, 77.89, 84.03, 75.79],
    "ECG_ZAB":   [99.93, 100.0, 95.85, 99.82, 100.0, 99.91, 99.95, 99.37, 99.27, 99.70],
    "PPG_RMSE":  [2.81, 1.20, 1.58, 2.40, 1.49, 1.85, 1.74, 1.38, 2.13, 1.59],
    "PPG_MARD":  [17.26, 13.58, 19.95, 16.90, 13.05, 17.29, 17.91, 15.01, 18.59, 21.10],
    "PPG_ZA":    [69.75, 76.11, 73.14, 70.47, 73.69, 66.78, 69.13, 71.28, 67.61, 64.64],
    "PPG_ZAB":   [96.65, 99.93, 95.85, 97.93, 100.0, 98.34, 99.89, 98.97, 99.20, 98.54],
    "BOTH_RMSE": [1.93, 1.10, 1.45, 1.83, 1.22, 1.48, 1.68, 1.13, 1.79, 1.28],
    "BOTH_MARD": [10.85, 12.62, 17.68, 12.64, 11.62, 13.56, 13.72, 12.24, 13.74, 15.58],
    "BOTH_ZA":   [81.65, 81.69, 78.10, 77.84, 83.44, 77.85, 80.48, 80.40, 83.25, 76.27],
    "BOTH_ZAB":  [100.0, 100.0, 96.07, 100.0, 100.0, 99.88, 100.0, 99.37, 100.0, 99.63],
})
# The paper's own Average row, as printed (not recomputed).
PAPER_AVERAGE = {
    "ECG":  {"RMSE": 1.56, "MARD": 13.88, "ZA": 77.90, "ZAB": 99.38},
    "PPG":  {"RMSE": 1.82, "MARD": 17.06, "ZA": 70.26, "ZAB": 98.53},
    "BOTH": {"RMSE": 1.49, "MARD": 13.42, "ZA": 80.09, "ZAB": 99.49},
}
SIGNAL_LABEL = {"ECG": "ECG only", "PPG": "PPG only", "BOTH": "ECG + PPG (proposed)"}
SIGNAL_COLOUR = {"ECG": BLUE, "PPG": ORANGE, "BOTH": GREEN}

# ----------------------------------------------------------------------------------
# SOURCE 2: our measured results on real D1NAMO, from the logged evaluation runs.
# ----------------------------------------------------------------------------------
OUR_METHODS = ["RandomForest", "GradientBoosting", "Bagging",
               "PlainAverage", "WeightedAverage", "Choquet"]
# These are the CORRECTED runs (after the inner-CV shuffling fix in src/fusion.py; see
# RESULTS.md section 6.2). The pre-fix numbers are kept in results/uncorrected/.
OUR_RESULTS = pd.DataFrame({
    "Method": OUR_METHODS,
    # Protocol A: pooled 5-fold (a patient may appear in train and test)
    "A_RMSE": [3.90, 4.03, 3.90, 3.93, 3.91, 3.92],
    "A_MARD": [45.79, 47.36, 45.80, 46.16, 45.99, 44.84],
    # Protocol B: leave-one-subject-out (test patient never seen)
    "B_RMSE": [4.41, 4.43, 4.41, 4.40, 4.40, 4.40],
    "B_MARD": [53.92, 52.58, 53.90, 53.27, 53.50, 52.18],
})
OUR_BASELINE_RMSE = 4.192      # "always predict the mean glucose"

# Temporal Choquet sweep (paper stage 2), leave-one-subject-out.
TEMPORAL = pd.DataFrame({
    "Setting": ["RAW\n(no temporal)", "temporal\nd=1/7", "temporal\nd=0.20",
                "temporal\nd=0.35"],
    "RMSE": [4.409, 4.318, 4.320, 4.352],
    "MARD": [51.13, 51.15, 52.43, 55.16],
})


def _style(ax) -> None:
    ax.grid(True, color="#d0d7de", lw=0.6, alpha=0.7, axis="both")
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#d0d7de")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)


def _save(fig, name: str) -> None:
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"   wrote {path}")


def _source_note(fig, text: str, y: float = -0.04) -> None:
    """Stamp every figure with where its numbers came from."""
    fig.text(0.5, y, text, ha="center", fontsize=8, color=MUTED, style="italic")


# ----------------------------------------------------------------------------------
# Paper Table II, per fold
# ----------------------------------------------------------------------------------
def figure_paper_tableII() -> None:
    """The paper's tenfold RMSE and MARD, by signal configuration."""
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6))
    x = np.arange(11)          # 10 folds plus the Average slot
    width = 0.26
    labels = [str(i) for i in range(1, 11)] + ["Avg"]

    for ax, metric, unit in ((axes[0], "RMSE", "RMSE (mmol/L)"),
                             (axes[1], "MARD", "MARD (%)")):
        for i, signal in enumerate(("ECG", "PPG", "BOTH")):
            vals = list(PAPER_TABLE_II[f"{signal}_{metric}"]) + \
                [PAPER_AVERAGE[signal][metric]]
            ax.bar(x + (i - 1) * width, vals, width=width * 0.9,
                   color=SIGNAL_COLOUR[signal], label=SIGNAL_LABEL[signal])
        # Direct-label the Average bars: they are the numbers people quote, and they
        # also supply the secondary encoding the colour check asks for. Set vertically,
        # because the three averages are close in value and horizontal labels on
        # adjacent bars overlap.
        for i, signal in enumerate(("ECG", "PPG", "BOTH")):
            v = PAPER_AVERAGE[signal][metric]
            ax.text(10 + (i - 1) * width, v * 1.02, f"{v:.2f}", ha="center",
                    va="bottom", fontsize=8, color=INK, weight="bold", rotation=90)
        _style(ax)
        # Headroom so the rotated labels are not clipped by the top of the axes.
        ax.set_ylim(top=ax.get_ylim()[1] * 1.18)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=8.5)
        ax.set_xlabel("Cross-validation fold")
        ax.set_ylabel(unit + "  -  lower is better")
        ax.axvline(9.5, color=MUTED, lw=0.8, ls="--", alpha=0.7)

    axes[0].legend(frameon=False, fontsize=9, loc="upper right")
    fig.suptitle("Paper's reported tenfold performance by signal type (Table II)",
                 fontsize=12.5, color=INK, y=1.0)
    _source_note(fig, "Source: Li et al., IEEE TNNLS 2024, Table II - the authors' "
                      "results on their own private dataset, not ours.")
    _save(fig, "paper_tableII_rmse_mard.png")


def figure_paper_zones() -> None:
    """The paper's clinical-safety result: Zone A and Zone A+B by signal type."""
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    signals = ["ECG", "PPG", "BOTH"]
    x = np.arange(len(signals))
    width = 0.34

    za = [PAPER_AVERAGE[s]["ZA"] for s in signals]
    zab = [PAPER_AVERAGE[s]["ZAB"] for s in signals]

    b1 = ax.bar(x - width / 2, za, width * 0.92, color=BLUE, label="Zone A")
    b2 = ax.bar(x + width / 2, zab, width * 0.92, color=GREEN, label="Zone A + B")
    for bars in (b1, b2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                    f"{bar.get_height():.2f}", ha="center", va="bottom",
                    fontsize=9, color=INK)

    _style(ax)
    ax.set_xticks(x)
    ax.set_xticklabels([SIGNAL_LABEL[s] for s in signals], fontsize=9.5)
    ax.set_ylabel("Percentage of predictions (%)  -  higher is better")
    ax.set_ylim(0, 112)
    # Below the axis: the bars are full-height, so any in-plot legend would cover data.
    ax.legend(frameon=False, fontsize=9, ncol=2, loc="upper center",
              bbox_to_anchor=(0.5, -0.11))
    ax.set_title("Paper's Parkes error grid result: clinically acceptable predictions",
                 fontsize=12, color=INK)
    _source_note(fig, "Source: Li et al., IEEE TNNLS 2024, Table II (Average row).",
                 y=-0.13)
    _save(fig, "paper_zones.png")


# ----------------------------------------------------------------------------------
# Our measured D1NAMO results
# ----------------------------------------------------------------------------------
def figure_our_methods() -> None:
    """Our measured RMSE and MARD for every fusion method, under both protocols."""
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), sharey=True)
    y = np.arange(len(OUR_METHODS))

    panels = [
        (axes[0], "A", "Protocol A: pooled 5-fold\n(patient seen in training)"),
        (axes[1], "B", "Protocol B: leave-one-subject-out\n(patient never seen)"),
    ]
    for ax, key, title in panels:
        vals = OUR_RESULTS[f"{key}_RMSE"].to_numpy()
        # Colour is a highlight, not a category code: the method names are already on
        # the axis. Only the paper's own method is picked out.
        colours = [ACCENT if m == "Choquet" else BLUE for m in OUR_METHODS]
        bars = ax.barh(y, vals, height=0.62, color=colours)

        ax.axvline(OUR_BASELINE_RMSE, color=INK, ls="--", lw=1.3)
        # The baseline caption sits just above the axes: inside the plot it collided
        # with the bar value labels, since every RMSE here is close to the baseline.
        ax.annotate(f"no-skill baseline {OUR_BASELINE_RMSE:.2f}",
                    xy=(OUR_BASELINE_RMSE, 1.0), xycoords=("data", "axes fraction"),
                    xytext=(0, 4), textcoords="offset points",
                    fontsize=8, color=INK, ha="center", va="bottom")

        # Values go INSIDE the bars. Every bar is long enough to hold the text, and it
        # keeps the numbers clear of the baseline rule just past each bar's end.
        for bar, v, m in zip(bars, vals, OUR_RESULTS[f"{key}_MARD"]):
            ax.text(v - 0.08, bar.get_y() + bar.get_height() / 2,
                    f"{v:.3f}   MARD {m:.1f}%", va="center", ha="right",
                    fontsize=8.5, color="white", weight="bold")

        _style(ax)
        ax.set_yticks(y)
        ax.set_yticklabels(OUR_METHODS, fontsize=9.5)
        ax.invert_yaxis()
        ax.set_xlabel("RMSE (mmol/L)  -  lower is better")
        ax.set_title(title, fontsize=10.5, color=INK, pad=18)
        ax.set_xlim(0, 4.9)

    fig.suptitle("Our measured results on real D1NAMO ECG data (4054 windows, 9 patients)",
                 fontsize=12.5, color=INK, y=1.10)
    _source_note(fig, "Source: our own evaluation runs (eval_progress.log). ECG-only "
                      "reproduction: D1NAMO has no PPG signal.")
    _save(fig, "our_methods_rmse.png")


def figure_temporal() -> None:
    """Did the paper's stage-2 temporal Choquet smoothing help our predictions?

    Drawn as a DOT plot, not bars. The whole story here is a ~2% difference, so the
    axis has to be zoomed in to show it -- and a bar chart on a zoomed axis lies,
    because a bar's length is what encodes its value. A dot encodes position instead,
    so a non-zero axis is honest. The gain is real but small, and the chart should say
    exactly that rather than dramatise it.
    """
    fig, ax = plt.subplots(figsize=(8.2, 3.8))
    raw = TEMPORAL["RMSE"][0]
    y = np.arange(len(TEMPORAL))

    ax.axvline(raw, color=MUTED, ls="--", lw=1.1, zorder=1)
    ax.annotate("raw fusion, no temporal smoothing",
                xy=(raw, 1.0), xycoords=("data", "axes fraction"),
                xytext=(6, 4), textcoords="offset points",
                fontsize=8, color=MUTED, ha="left", va="bottom")

    for yi, v in zip(y, TEMPORAL["RMSE"]):
        better = v < raw
        colour = ACCENT if better else "#8c9196"
        # A thin leader from the reference line to the dot shows size AND direction
        # of the change without pretending to be a magnitude bar.
        ax.plot([raw, v], [yi, yi], color=colour, lw=2, alpha=0.5, zorder=2,
                solid_capstyle="round")
        ax.scatter([v], [yi], s=110, color=colour, zorder=3,
                   edgecolors="white", linewidths=1.5)
        delta = v - raw
        ax.text(v - 0.004 if better else v + 0.004, yi,
                f"{v:.3f}" + (f"  ({delta:+.3f})" if delta else ""),
                va="center", ha="right" if better else "left",
                fontsize=9, color=INK)

    _style(ax)
    ax.set_yticks(y)
    ax.set_yticklabels(TEMPORAL["Setting"].str.replace("\n", " "), fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("RMSE (mmol/L)  -  lower is better")
    ax.set_xlim(4.28, 4.45)
    ax.set_title("Stage-2 temporal Choquet: smoothing each model's predictions over time",
                 fontsize=11.5, color=INK, pad=18)
    _source_note(fig,
                 "Source: our own evaluation run (temporal_progress.log), "
                 "leave-one-subject-out. Note the zoomed axis: the best gain is 0.09 "
                 "mmol/L (~2%), which is real but small.", y=-0.12)
    _save(fig, "our_temporal_choquet.png")


def figure_paper_vs_ours() -> None:
    """The honest side-by-side, with the reason for the gap stated on the chart."""
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    entries = [
        ("Paper\nECG + PPG", PAPER_AVERAGE["BOTH"]["RMSE"], GREEN),
        ("Paper\nECG only", PAPER_AVERAGE["ECG"]["RMSE"], BLUE),
        ("Ours\nProtocol A", float(OUR_RESULTS.loc[
            OUR_RESULTS.Method == "Choquet", "A_RMSE"].iloc[0]), ACCENT),
        ("Ours\nProtocol B", float(OUR_RESULTS.loc[
            OUR_RESULTS.Method == "Choquet", "B_RMSE"].iloc[0]), ACCENT),
        ("No-skill\nbaseline", OUR_BASELINE_RMSE, "#8c9196"),
    ]
    x = np.arange(len(entries))
    bars = ax.bar(x, [e[1] for e in entries], width=0.58, color=[e[2] for e in entries])
    for bar, e in zip(bars, entries):
        ax.text(bar.get_x() + bar.get_width() / 2, e[1] + 0.06, f"{e[1]:.2f}",
                ha="center", va="bottom", fontsize=9.5, color=INK, weight="bold")

    _style(ax)
    ax.set_xticks(x)
    ax.set_xticklabels([e[0] for e in entries], fontsize=9.5)
    ax.set_ylabel("RMSE (mmol/L)  -  lower is better")
    ax.set_ylim(0, 5.3)
    ax.set_title("Paper's results vs ours, Choquet fusion", fontsize=12, color=INK)
    ax.text(0.5, -0.22,
            "Not a like-for-like comparison. The paper used a private ECG + PPG dataset "
            "with a ResNet\nmorphological branch and feature selection. D1NAMO is "
            "ECG-only, so our reproduction has the\n80 ECG temporal features and the "
            "Choquet fusion, but no PPG half and no morphological branch.",
            transform=ax.transAxes, ha="center", va="top", fontsize=8.5, color=MUTED)
    _save(fig, "paper_vs_ours.png")


def main() -> None:
    os.makedirs(FIG_DIR, exist_ok=True)
    print("Charting results that already exist (paper's published table + our logged runs):")
    figure_paper_tableII()
    figure_paper_zones()
    figure_our_methods()
    figure_temporal()
    figure_paper_vs_ours()

    # Also save the paper's table as a CSV so it can be quoted in the report.
    os.makedirs("results", exist_ok=True)
    PAPER_TABLE_II.to_csv(os.path.join("results", "paper_tableII.csv"), index=False)
    print(f"\nDone. Figures in {FIG_DIR}/")


if __name__ == "__main__":
    main()
