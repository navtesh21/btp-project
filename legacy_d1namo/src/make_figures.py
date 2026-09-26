"""
src/make_figures.py
===================
Draw the result charts from the predictions saved by src/generate_results.py.

This reproduces, on our real D1NAMO data, the figures the paper reports:

  fig09_timeseries_<patient>.png  -- paper Fig. 9: predicted vs reference blood glucose
                                     over time, with day separators.
  fig10_parkes_<protocol>.png     -- paper Fig. 10: Parkes (consensus) error grid.
  rmse_by_method.png              -- does the Choquet fusion actually beat the simpler
                                     ways of combining the three models?
  zone_distribution.png           -- how the predictions spread across the clinical
                                     safety zones A-E, per method.
  densities_by_fold.png           -- the fuzzy densities the Choquet integral assigned
                                     to each base model, fold by fold.

Because this reads the saved CSVs instead of retraining, it runs in seconds, so a figure
can be re-tuned without repeating the (slow) cross-validation.

DESIGN NOTES
------------
Colour is only ever used where it carries information that the text does not. In the
bar charts the method name is already on the axis, so the bars use ONE colour, with the
paper's own method (Choquet) picked out in a second colour -- that is a highlight, not a
category code. The two-series time plot uses the same blue/red the paper's Fig. 9 uses;
both palettes were checked for colour-vision-deficiency separation. The error-grid zones
are ordered by severity (A best to E worst), so they get a green-to-red severity ramp
rather than arbitrary hues, and every zone is labelled with its letter as well.

Run (after src/generate_results.py):   python -m src.make_figures
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")            # render to files; no interactive window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.error_grid import draw_grid, parkes_zones, zone_percentages
from src.metrics import mard, rmse

RESULTS_DIR = "results"
FIG_DIR = os.path.join("figures", "results")

# --- the two validated palettes (see the design note above) ------------------------
BLUE, RED = "#1f6feb", "#cf222e"          # prediction vs reference (paper Fig. 9)
BAR, ACCENT = "#1f6feb", "#bc4c00"        # ordinary bar vs the highlighted Choquet bar
INK, MUTED = "#24292f", "#57606a"         # text colours; never a series colour
# Severity ramp for zones A(safe) -> E(dangerous). Ordinal data gets an ordered ramp.
ZONE_COLOURS = {"A": "#1a7f37", "B": "#8ab000", "C": "#d4a72c",
                "D": "#e16f24", "E": "#cf222e"}

METHODS = ["RandomForest", "GradientBoosting", "Bagging",
           "PlainAverage", "WeightedAverage", "Choquet"]


def _style(ax) -> None:
    """Recessive grid and axes, so the data is the loudest thing on the chart."""
    ax.grid(True, color="#d0d7de", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#d0d7de")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)


def _save(fig, name: str) -> None:
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"   wrote {path}")


# ----------------------------------------------------------------------------------
# Paper Fig. 10 -- Parkes error grid
# ----------------------------------------------------------------------------------
def figure_parkes(preds: pd.DataFrame, protocol: str, label: str,
                  method: str = "Choquet") -> None:
    y_true = preds["glucose"].to_numpy()
    y_pred = preds[method].to_numpy()
    pct = zone_percentages(y_true, y_pred)

    # Clip the axes to just past the data so the points are not a tiny blob in the
    # corner of the full 30.56 mmol/L grid (the paper's own Fig. 10 does the same).
    top = float(max(y_true.max(), y_pred.max())) * 1.15

    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    draw_grid(ax, max_mmol=min(30.56, max(top, 16.0)))

    # 2px surface ring on the markers keeps overlapping points readable where the
    # scatter is dense.
    ax.scatter(y_true, y_pred, s=14, color=INK, alpha=0.35,
               edgecolors="white", linewidths=0.4, zorder=3)

    ax.set_title(f"Parkes error grid - {method} fusion\n{label}",
                 fontsize=11, color=INK, pad=10)
    # Direct annotation of the two numbers the paper reports, so the reader never has
    # to count dots. It sits bottom-right: that corner is the deep zone C/D region,
    # which is empty of points for any model that is not catastrophically broken, and
    # it keeps clear of the zone letters along the top-left edge.
    ax.text(0.975, 0.025,
            f"Zone A      {pct['A']:.2f}%\nZone A + B  {pct['A+B']:.2f}%\n"
            f"RMSE        {rmse(y_true, y_pred):.2f} mmol/L\nMARD        {mard(y_true, y_pred):.2f}%",
            transform=ax.transAxes, va="bottom", ha="right", fontsize=9, color=INK,
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor="#d0d7de"))
    _save(fig, f"fig10_parkes_{protocol}.png")


# ----------------------------------------------------------------------------------
# Paper Fig. 9 -- prediction vs reference over time
# ----------------------------------------------------------------------------------
def figure_timeseries(preds: pd.DataFrame, protocol: str, label: str,
                      method: str = "Choquet", n_patients: int = 3) -> None:
    """Plot the patients with the most readings, one figure each."""
    counts = preds["subject"].value_counts()
    for subject in counts.index[:n_patients]:
        block = preds[preds["subject"] == subject].sort_values("timestamp")
        t = pd.to_datetime(block["timestamp"])

        fig, ax = plt.subplots(figsize=(9.5, 4.2))
        # Plot against reading index, not wall-clock: D1NAMO recordings have long gaps
        # between sessions, and plotting real time would squeeze every day into a
        # sliver separated by empty space. Day separators keep the time meaning.
        x = np.arange(len(block))
        ax.plot(x, block[method], color=BLUE, lw=0, marker=".", ms=3.5,
                label="Prediction value")
        ax.plot(x, block["glucose"], color=RED, lw=0, marker=".", ms=3.5,
                label="Reference value (CGM)")

        # Vertical rules where the calendar day changes, labelled day 1, day 2, ...
        days = t.dt.date.to_numpy()
        change = np.flatnonzero(days[1:] != days[:-1]) + 1
        for c in change:
            ax.axvline(c, color=MUTED, lw=0.8, ls="--", alpha=0.6)
        starts = np.concatenate([[0], change, [len(block)]])
        for i in range(len(starts) - 1):
            mid = (starts[i] + starts[i + 1]) / 2
            ax.text(mid, ax.get_ylim()[0], f"day {i + 1}", fontsize=8,
                    color=MUTED, ha="center", va="bottom")

        _style(ax)
        ax.set_xlabel("Reading (ordered in time, day boundaries marked)")
        ax.set_ylabel("Blood glucose (mmol/L)")
        ax.set_title(f"Patient {subject} - predicted vs reference blood glucose\n{label}",
                     fontsize=11, color=INK)
        ax.legend(frameon=False, fontsize=9, loc="upper right", markerscale=3)
        _save(fig, f"fig09_timeseries_{protocol}_patient{subject}.png")


# ----------------------------------------------------------------------------------
# Method comparison
# ----------------------------------------------------------------------------------
def figure_rmse_by_method(tables: dict[str, pd.DataFrame], baseline: float) -> None:
    """One panel per protocol: RMSE of every method, against the no-skill baseline."""
    fig, axes = plt.subplots(1, len(tables), figsize=(11.5, 4.6), sharey=True)
    for ax, (label, table) in zip(np.atleast_1d(axes), tables.items()):
        table = table.set_index("Method").reindex(METHODS)
        values = table["RMSE (mmol/L)"].to_numpy()
        colours = [ACCENT if m == "Choquet" else BAR for m in table.index]

        bars = ax.barh(np.arange(len(table)), values, color=colours, height=0.62)
        # 4px rounded ends would need a custom patch; instead we keep the bars thin and
        # let a small gap between them do the separating work.
        ax.set_yticks(np.arange(len(table)))
        ax.set_yticklabels(table.index, fontsize=9)
        ax.invert_yaxis()

        # The reference line every reader needs: "always guess the average glucose".
        ax.axvline(baseline, color=INK, ls="--", lw=1.2)
        ax.text(baseline, -0.9, f" no-skill baseline {baseline:.2f}",
                fontsize=8, color=INK, va="bottom", ha="left")

        # Direct value labels: the number belongs on the bar, not in a lookup.
        for bar, v in zip(bars, values):
            ax.text(v + 0.04, bar.get_y() + bar.get_height() / 2, f"{v:.2f}",
                    va="center", fontsize=8.5, color=INK)

        _style(ax)
        ax.set_xlabel("RMSE (mmol/L) - lower is better")
        ax.set_title(label, fontsize=10, color=INK)
        ax.set_xlim(0, max(values.max(), baseline) * 1.18)

    fig.suptitle("Does the Choquet fusion beat the simpler combinations?",
                 fontsize=12, color=INK, y=1.02)
    _save(fig, "rmse_by_method.png")


def figure_zone_distribution(preds_by_protocol: dict[str, pd.DataFrame]) -> None:
    """Stacked bars: what fraction of predictions land in each clinical safety zone."""
    fig, axes = plt.subplots(1, len(preds_by_protocol), figsize=(11.5, 4.6), sharey=True)
    for ax, (label, preds) in zip(np.atleast_1d(axes), preds_by_protocol.items()):
        y = np.arange(len(METHODS))
        left = np.zeros(len(METHODS))
        for zone in "ABCDE":
            widths = np.array([
                float(np.mean(parkes_zones(preds["glucose"], preds[m]) == zone) * 100)
                for m in METHODS])
            ax.barh(y, widths, left=left, height=0.62, color=ZONE_COLOURS[zone],
                    label=f"Zone {zone}" if ax is np.atleast_1d(axes)[0] else None,
                    edgecolor="white", linewidth=1.0)      # 2px surface gap between segments
            # Label a segment directly when it is wide enough to hold the text.
            for yi, (w, l) in enumerate(zip(widths, left)):
                if w >= 7:
                    ax.text(l + w / 2, yi, f"{w:.0f}", ha="center", va="center",
                            fontsize=8, color="white", weight="bold")
            left += widths

        ax.set_yticks(y)
        ax.set_yticklabels(METHODS, fontsize=9)
        ax.invert_yaxis()
        _style(ax)
        ax.set_xlim(0, 100)
        ax.set_xlabel("Percentage of predictions (%)")
        ax.set_title(label, fontsize=10, color=INK)

    handles, labels = np.atleast_1d(axes)[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=9, ncol=5,
               loc="lower center", bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("Clinical safety zones (Parkes error grid): A is harmless, E is dangerous",
                 fontsize=12, color=INK, y=1.02)
    _save(fig, "zone_distribution.png")


def figure_densities(protocol: str, label: str) -> None:
    """The fuzzy density the Choquet integral gave each base model, per fold."""
    path = os.path.join(RESULTS_DIR, f"densities_{protocol}.csv")
    if not os.path.exists(path):
        return
    dens = pd.read_csv(path).set_index("fold")

    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    x = np.arange(len(dens))
    width = 0.26
    # Three series here genuinely need three colours, and each is direct-labelled in
    # the legend; the shades are one hue family ordered by model, not arbitrary hues.
    shades = ["#1f6feb", "#bc4c00", "#1a7f37"]
    for i, (col, shade) in enumerate(zip(dens.columns, shades)):
        ax.bar(x + (i - 1) * width, dens[col], width=width * 0.92, color=shade, label=col)

    _style(ax)
    ax.set_xticks(x)
    ax.set_xticklabels(dens.index, fontsize=9)
    ax.set_xlabel("Cross-validation fold")
    ax.set_ylabel("Fuzzy density (out-of-fold R2)")
    ax.set_title(f"How much the Choquet integral trusted each base model\n{label}",
                 fontsize=11, color=INK, pad=26)
    # Legend above the plot: with three bars per fold there is no reliable
    # empty corner inside the axes for it to sit in.
    ax.legend(frameon=False, fontsize=9, ncol=3, loc="lower center",
              bbox_to_anchor=(0.5, 1.0))
    ax.set_ylim(top=ax.get_ylim()[1] * 1.05)
    _save(fig, f"densities_{protocol}.png")


def main() -> None:
    os.makedirs(FIG_DIR, exist_ok=True)

    # Protocol A's fold count is a command-line option of generate_results.py, so read
    # it back from the saved predictions rather than hardcoding it into the caption.
    protocols = {
        "protocolA": "Protocol A: pooled {k}-fold (paper-style; patient seen in training)",
        "protocolB": "Protocol B: leave-one-subject-out (patient never seen)",
    }

    preds_by_protocol, tables = {}, {}
    for protocol, label in protocols.items():
        pred_path = os.path.join(RESULTS_DIR, f"predictions_{protocol}.csv")
        if not os.path.exists(pred_path):
            print(f"   skipping {protocol}: {pred_path} not found "
                  f"(run python -m src.generate_results first)")
            continue
        preds = pd.read_csv(pred_path, dtype={"subject": str})
        preds["subject"] = preds["subject"].str.zfill(3)
        label = label.format(k=preds["fold"].nunique())
        preds_by_protocol[label] = preds

        figure_parkes(preds, protocol, label)
        figure_timeseries(preds, protocol, label)
        figure_densities(protocol, label)

        table_path = os.path.join(RESULTS_DIR, f"methods_{protocol}.csv")
        if os.path.exists(table_path):
            tables[label] = pd.read_csv(table_path)

    if preds_by_protocol:
        baseline = float(next(iter(preds_by_protocol.values()))["glucose"].std())
        if tables:
            figure_rmse_by_method(tables, baseline)
        figure_zone_distribution(preds_by_protocol)

    print(f"\nAll figures written to {FIG_DIR}/")


if __name__ == "__main__":
    main()
