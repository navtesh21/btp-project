"""
bgfusion/figures_results.py
===========================
The paper's own figures, reproduced on our data.

    fig10_parkes_<protocol>.png    Paper Fig. 10 - Parkes error grid scatter, with the
                                   zone percentages annotated on the plot.
    fig09_timeseries_<subject>.png Paper Fig. 9 - predicted vs reference glucose over
                                   time for one patient, with day separators.
    fig_protocol_collapse.png      Our headline: R2 by method under each split protocol,
                                   with the no-skill baseline drawn as the line to beat.
    fig_zone_vs_r2.png             Why clinical zone metrics mask failure: Zone A+B and
                                   R2 plotted for the same models side by side.

DESIGN
------
Colour carries information only where the text does not already. Method names sit on the
axis of every bar chart, so bars use one colour with the fusion picked out in a second;
that is a highlight, not a category code. The blue/red pair in the time plot matches the
paper's own Fig. 9. Both palettes were checked for colour-vision-deficiency separation.

Run:  python -m bgfusion.figures_results
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bgfusion.error_grid import draw_grid, zone_percentages
from bgfusion.metrics import mard, rmse

RESULTS = "results"
FIG_DIR = os.path.join("figures", "results")

BLUE, RED = "#1f6feb", "#cf222e"
INK, MUTED, MINT = "#0B2F3A", "#5A6B72", "#00C2A8"
TEAL, ACCENT = "#1C7293", "#BC4C00"
GREY = "#8C9196"

PROTO_LABEL = {
    "random_window": "Random window split",
    "subject_aware": "Subject-aware split",
    "loso": "Leave-one-subject-out",
}
METHODS = ["RandomForest", "GradientBoosting", "Bagging",
           "PlainAverage", "WeightedAverage", "Choquet"]


def _style(ax):
    ax.grid(True, color="#D0D7DE", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#D0D7DE")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)


def _save(fig, name):
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"   wrote {path}")


def _preds(tag):
    p = os.path.join(RESULTS, f"preds_fused_{tag}.csv")
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p, dtype={"subject": str})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


# ----------------------------------------------------------------------------------
# Paper Fig. 10 - Parkes error grid
# ----------------------------------------------------------------------------------
def figure_parkes(tag, method="Choquet"):
    df = _preds(tag)
    if df is None:
        return
    y, p = df["glucose"].to_numpy(), df[method].to_numpy()
    pct = zone_percentages(y, p)
    top = min(30.56, max(float(max(y.max(), p.max())) * 1.12, 16.0))

    fig, ax = plt.subplots(figsize=(6.2, 6.0))
    draw_grid(ax, max_mmol=top)
    # Dense scatter: small, translucent, with a thin light edge so overlapping points
    # stay individually visible rather than merging into a solid blob.
    ax.scatter(y, p, s=7, color=INK, alpha=0.22, edgecolors="white", linewidths=0.25,
               zorder=3)
    ax.set_title(f"Parkes error grid - {method}\n{PROTO_LABEL.get(tag, tag)}",
                 fontsize=11.5, color=INK, pad=10)
    ax.text(0.975, 0.025,
            f"Zone A      {pct['A']:.2f}%\nZone A + B  {pct['A+B']:.2f}%\n"
            f"RMSE        {rmse(y, p):.2f} mmol/L\nMARD        {mard(y, p):.2f}%\n"
            f"n           {len(y):,}",
            transform=ax.transAxes, va="bottom", ha="right", fontsize=9, color=INK,
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="#D0D7DE"))
    _save(fig, f"fig10_parkes_{tag}.png")


# ----------------------------------------------------------------------------------
# Paper Fig. 9 - prediction vs reference over time
# ----------------------------------------------------------------------------------
def figure_timeseries(tag, method="Choquet", n_subjects=2):
    df = _preds(tag)
    if df is None:
        return
    for subject in df["subject"].value_counts().index[:n_subjects]:
        blk = df[df["subject"] == subject].sort_values("timestamp")
        t = pd.to_datetime(blk["timestamp"])
        x = np.arange(len(blk))

        fig, ax = plt.subplots(figsize=(9.6, 4.0))
        ax.plot(x, blk["glucose"], color=RED, lw=0, marker=".", ms=3,
                label="Reference value (CGM)")
        ax.plot(x, blk[method], color=BLUE, lw=0, marker=".", ms=3,
                label="Prediction value")

        # Day separators: the recordings have long gaps between sessions, so plotting
        # against wall-clock would squeeze each day into a sliver. Index keeps the
        # readings evenly spaced and the rules preserve the time meaning.
        days = t.dt.date.to_numpy()
        change = np.flatnonzero(days[1:] != days[:-1]) + 1
        for c in change:
            ax.axvline(c, color=MUTED, lw=0.7, ls="--", alpha=0.55)
        starts = np.concatenate([[0], change, [len(blk)]])
        lo = ax.get_ylim()[0]
        for i in range(len(starts) - 1):
            ax.text((starts[i] + starts[i + 1]) / 2, lo, f"day {i + 1}",
                    fontsize=7.5, color=MUTED, ha="center", va="bottom")

        _style(ax)
        ax.set_xlabel("Reading (time-ordered; dashed rules mark day boundaries)")
        ax.set_ylabel("Blood glucose (mmol/L)")
        ax.set_title(f"Patient {subject}: predicted vs reference glucose\n"
                     f"{PROTO_LABEL.get(tag, tag)}", fontsize=11.5, color=INK)
        ax.legend(frameon=False, fontsize=9, loc="upper right", markerscale=4)
        _save(fig, f"fig09_timeseries_{tag}_{subject}.png")


# ----------------------------------------------------------------------------------
# Our headline figure: the collapse across protocols
# ----------------------------------------------------------------------------------
def figure_protocol_collapse():
    tags = [t for t in ("random_window", "subject_aware", "loso")
            if os.path.exists(os.path.join(RESULTS, f"summary_fused_{t}.csv"))]
    if not tags:
        return
    # sharex matters as much as sharey here: with independent x-scales each panel
    # autoscales to its own range, so bars of very different magnitude render at the
    # same length and the panels cannot be compared by eye - which is the entire point
    # of putting them side by side.
    fig, axes = plt.subplots(1, len(tags), figsize=(4.4 * len(tags), 4.6),
                             sharey=True, sharex=True)
    axes = np.atleast_1d(axes)

    for ax, tag in zip(axes, tags):
        s = pd.read_csv(os.path.join(RESULTS, f"summary_fused_{tag}.csv")).set_index("Method")
        vals = [s.loc[m, "R2"] for m in METHODS]
        base = s.loc["NoSkillBaseline", "R2"]
        colours = [ACCENT if m == "Choquet" else BLUE for m in METHODS]
        ypos = np.arange(len(METHODS))
        ax.barh(ypos, vals, height=0.62, color=colours)
        ax.axvline(base, color=INK, ls="--", lw=1.4)
        ax.axvline(0, color=MUTED, lw=0.8)
        ax.annotate(f"no-skill baseline {base:+.3f}",
                    xy=(base, 1.0), xycoords=("data", "axes fraction"),
                    xytext=(0, 5), textcoords="offset points",
                    fontsize=8.5, color=INK, ha="center", va="bottom")
        for yi, v in zip(ypos, vals):
            ax.text(v + (0.012 if v >= 0 else -0.012), yi, f"{v:+.3f}",
                    va="center", ha="left" if v >= 0 else "right",
                    fontsize=8.5, color=INK)
        ax.set_yticks(ypos)
        ax.set_yticklabels(METHODS, fontsize=9.5)
        ax.invert_yaxis()
        _style(ax)
        ax.set_title(PROTO_LABEL[tag], fontsize=10.5, color=INK, pad=20)

    lo = min(min(pd.read_csv(os.path.join(RESULTS, f"summary_fused_{t}.csv"))["R2"])
             for t in tags)
    hi = max(max(pd.read_csv(os.path.join(RESULTS, f"summary_fused_{t}.csv"))["R2"])
             for t in tags)
    axes[0].set_xlim(lo - 0.08, hi + 0.08)
    # NOT "progressively worse": leave-one-subject-out scores better than the
    # subject-aware split because it trains on 9 of 10 patients rather than 4 of 5.
    # The invariant worth claiming is that both honest splits put every method behind
    # the baseline, so the title says that instead.
    # One shared axis label rather than three: repeating it wastes space and the
    # rightmost copy was being clipped by the figure edge.
    fig.supxlabel("R$^2$   (higher is better; 0 = no better than predicting the mean)",
                  fontsize=11, color=INK, y=-0.02)
    fig.suptitle("Under both honest splits, every method falls behind the no-skill baseline",
                 fontsize=13, color=INK, y=1.04)
    _save(fig, "fig_protocol_collapse.png")


# ----------------------------------------------------------------------------------
# Why the clinical metric masks the failure
# ----------------------------------------------------------------------------------
def figure_zone_vs_r2(tag="subject_aware"):
    path = os.path.join(RESULTS, f"summary_fused_{tag}.csv")
    if not os.path.exists(path):
        return
    s = pd.read_csv(path).set_index("Method")
    rows = METHODS + ["NoSkillBaseline"]
    labels = [m if m != "NoSkillBaseline" else "No-skill baseline" for m in rows]

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.6), sharey=True)
    y = np.arange(len(rows))
    # The baseline is the comparison the reader must make, so it alone is coloured.
    colours = [RED if m == "NoSkillBaseline" else GREY for m in rows]

    for ax, col, xlabel, fmt in (
        (axes[0], "ZoneA+B", "Parkes Zone A+B (%)  -  the usual clinical headline", "{:.1f}%"),
        (axes[1], "R2", "R$^2$  -  did it beat predicting the mean?", "{:+.3f}"),
    ):
        key = col if col in s.columns else col.replace("+", " + ")
        vals = [s.loc[m, key] for m in rows]
        ax.barh(y, vals, height=0.62, color=colours)
        for yi, v in zip(y, vals):
            ax.text(v + (abs(max(vals)) * 0.012 if v >= 0 else -abs(min(vals)) * 0.05),
                    yi, fmt.format(v), va="center",
                    ha="left" if v >= 0 else "right", fontsize=8.5, color=INK)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=9.5)
        ax.invert_yaxis()
        _style(ax)
        ax.set_xlabel(xlabel)
        if col == "R2":
            ax.axvline(0, color=MUTED, lw=0.9)

    axes[0].set_xlim(80, 95)
    fig.suptitle("The same models, two metrics: the clinical score cannot tell them apart\n"
                 f"({PROTO_LABEL.get(tag, tag)})", fontsize=12.5, color=INK, y=1.07)
    fig.text(0.5, -0.04,
             "The baseline predicts a constant and explains zero variance, yet scores the "
             "highest Zone A+B of any method.",
             ha="center", fontsize=9.5, color=MUTED, style="italic")
    _save(fig, "fig_zone_vs_r2.png")



# ----------------------------------------------------------------------------------
# The feature-set ablation
# ----------------------------------------------------------------------------------
def figure_ablation():
    """Every feature set under leave-one-subject-out, against the baseline.

    Two things this figure has to make visible: that all five land in a narrow band
    behind the baseline, and that the ordering runs OPPOSITE to feature count - which
    is the signature of fitting noise rather than signal.
    """
    sets = [
        ("morphological_loso", "Morphological (shape)", 33),
        ("ppg_only_loso", "PPG only", 94),
        ("ecg_only_loso", "ECG only", 99),
        ("temporal_loso", "Temporal (wavelet)", 160),
        ("fused_loso", "Fused (ECG + PPG)", 193),
    ]
    rows = []
    for tag, label, n in sets:
        p = os.path.join(RESULTS, f"summary_{tag}.csv")
        if not os.path.exists(p):
            continue
        s = pd.read_csv(p).set_index("Method")
        rows.append((label, n, float(s.loc["Choquet", "R2"]),
                     float(s.loc["Choquet", "ZoneA+B"])))
    if not rows:
        return
    base = pd.read_csv(os.path.join(RESULTS, "summary_fused_loso.csv")).set_index("Method")
    base_r2 = float(base.loc["NoSkillBaseline", "R2"])
    base_zab = float(base.loc["NoSkillBaseline", "ZoneA+B"])

    rows.sort(key=lambda r: r[2])                      # worst R2 first
    labels = [f"{l}  ({n})" for l, n, _, _ in rows] + ["NO-SKILL BASELINE  (0)"]
    r2s = [r[2] for r in rows] + [base_r2]
    zabs = [r[3] for r in rows] + [base_zab]
    colours = [GREY] * len(rows) + [RED]

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.4), sharey=True)
    y = np.arange(len(labels))

    axes[0].barh(y, r2s, height=0.6, color=colours)
    axes[0].axvline(base_r2, color=INK, ls="--", lw=1.3)
    for yi, v in zip(y, r2s):
        axes[0].text(v - 0.004, yi, f"{v:+.3f}", va="center", ha="right",
                     fontsize=9, color=INK)
    axes[0].set_xlabel("R$^2$   (0 = no better than the mean; negative = worse)")
    axes[0].set_xlim(min(r2s) - 0.035, 0.005)

    axes[1].barh(y, zabs, height=0.6, color=colours)
    axes[1].axvline(base_zab, color=INK, ls="--", lw=1.3)
    for yi, v in zip(y, zabs):
        axes[1].text(v + 0.06, yi, f"{v:.1f}%", va="center", fontsize=9, color=INK)
    axes[1].set_xlabel("Parkes Zone A+B (%)   -  the usual clinical headline")
    axes[1].set_xlim(89.5, 92.4)

    for ax in axes:
        _style(ax)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=9.5)
        ax.invert_yaxis()

    fig.suptitle("Every feature set falls behind the baseline - and the clinical score "
                 "runs the wrong way", fontsize=12.5, color=INK, y=1.05)
    fig.text(0.5, -0.06,
             "Feature counts in brackets. Fewer features score BETTER on R-squared, which "
             "is what fitting noise looks like. Meanwhile the worst models by R-squared "
             "carry the highest Zone A+B.",
             ha="center", fontsize=9.5, color=MUTED, style="italic")
    _save(fig, "fig_ablation.png")


def main():
    print("Drawing result figures:")
    for tag in ("random_window", "subject_aware", "loso"):
        figure_parkes(tag)
        figure_timeseries(tag, n_subjects=1)
    figure_protocol_collapse()
    figure_zone_vs_r2()
    figure_ablation()
    print(f"\nDone. Figures in {FIG_DIR}/")


if __name__ == "__main__":
    main()
