"""
bgfusion/figures_theory.py
==========================
Figures for the degeneracy result -- the paper's theoretical contribution.

These are generated from the closed form and from the fuser itself, so they need no
dataset and can be regenerated in a second.

    fig_degeneracy_weights.png   How the Choquet integral's effective weights move as
                                 the (equal) fuzzy density g changes: from an
                                 arithmetic mean at sum(g)=1 to a minimum operator as
                                 g -> 0.
    fig_degeneracy_regimes.png   The same story as a single readable curve: the share
                                 of weight landing on the smallest prediction, with
                                 the observed floored-density case marked.

THE RESULT BEING DRAWN
----------------------
For a Sugeno lambda-measure over n sources whose densities are all equal to g, the
measure is symmetric, so the Choquet integral is an OWA operator with weights

    w_j = g * beta^(j-1),    beta = 1 + lambda*g,    j = 1..n sorted LARGEST first

Because sum(g_i) < 1 forces lambda > 0 and hence beta > 1, the weights increase towards
the smallest prediction. As g -> 0 the mass concentrates entirely on the minimum, and
the "fusion" stops depending on which model was more competent.

Colours: a validated colour-vision-safe pair (blue / orange) plus a green accent; every
series is also direct-labelled, so identity never rests on colour alone.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from bgfusion.stage3_fusion import degeneracy_report

FIG_DIR = os.path.join("figures", "theory")

BLUE, ORANGE, GREEN = "#1f6feb", "#bc4c00", "#1a7f37"
INK, MUTED = "#24292f", "#57606a"


def _style(ax) -> None:
    ax.grid(True, color="#d0d7de", lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#d0d7de")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)


def _save(fig, name: str) -> None:
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"   wrote {path}")


def figure_weights(n: int = 3) -> None:
    """Effective OWA weight on each rank, as the equal density g varies."""
    gs = np.linspace(0.005, 1.0 / n, 240)
    W = np.array([degeneracy_report(np.full(n, g))["weights_largest_to_smallest"]
                  for g in gs])

    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    labels = ["largest prediction", "middle prediction", "smallest prediction"]
    colours = [BLUE, GREEN, ORANGE]
    for j in range(n):
        ax.plot(gs, W[:, j], color=colours[j], lw=2.2, label=labels[j])
        # Direct labels at the left edge, so the lines are identified without the legend.
        ax.annotate(labels[j], xy=(gs[0], W[0, j]), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=8.5,
                    color=colours[j], weight="bold")

    # Mark the case we actually observed: every density clipped to the 0.01 floor.
    # The callout sits well clear of the left-edge direct labels.
    obs = degeneracy_report(np.full(n, 0.01))
    ax.axvline(0.01, color=INK, ls="--", lw=1.2)
    ax.annotate(f"observed: densities floored at g = 0.01,\n"
                f"{obs['weight_on_min'] * 100:.1f}% of weight on the minimum",
                xy=(0.011, obs["weight_on_min"]), xytext=(0.085, 0.74),
                fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.1,
                                connectionstyle="arc3,rad=-0.2"))

    ax.axvline(1.0 / n, color=MUTED, ls=":", lw=1.2)
    ax.annotate("sum(g) = 1: lambda = 0,\nweights equal -> arithmetic mean",
                xy=(1.0 / n, 1.0 / n), xytext=(-12, 34), textcoords="offset points",
                fontsize=8.5, color=MUTED, ha="right")

    _style(ax)
    ax.set_xlabel("fuzzy density g assigned to every model (equal densities)")
    ax.set_ylabel("effective weight on that rank")
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, 1.0 / n * 1.06)
    # No legend: each line is already direct-labelled at its left end, so a legend box
    # would repeat that information and collide with the annotations.
    ax.set_title("When every model looks equally competent, the Choquet integral\n"
                 "stops fusing and becomes a fixed order statistic",
                 fontsize=12, color=INK)
    fig.text(0.5, -0.03,
             "Closed form: w_j = g * beta^(j-1), beta = 1 + lambda*g, for n = 3 models.",
             ha="center", fontsize=8, color=MUTED, style="italic")
    _save(fig, "fig_degeneracy_weights.png")


def figure_regimes(n: int = 3) -> None:
    """A single curve: how much weight lands on the minimum, and what that means."""
    gs = np.linspace(0.005, 1.0 / n, 240)
    wmin = np.array([degeneracy_report(np.full(n, g))["weight_on_min"] for g in gs])

    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    ax.plot(gs, wmin * 100, color=BLUE, lw=2.4)
    ax.axhline(100.0 / n, color=MUTED, ls=":", lw=1.2)
    ax.annotate(f"{100.0/n:.1f}% = a fair share\n(no rank preference)",
                xy=(0.24, 100.0 / n), xytext=(0, 8), textcoords="offset points",
                fontsize=8.5, color=MUTED)

    obs = degeneracy_report(np.full(n, 0.01))
    ax.scatter([0.01], [obs["weight_on_min"] * 100], s=90, color=ORANGE, zorder=4,
               edgecolors="white", linewidths=1.5)
    ax.annotate(f"the run we observed\ng = 0.01  ->  {obs['weight_on_min']*100:.1f}%",
                xy=(0.01, obs["weight_on_min"] * 100), xytext=(0.06, 78),
                fontsize=9, color=ORANGE, weight="bold",
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.2))

    _style(ax)
    ax.set_xlabel("fuzzy density g assigned to every model")
    ax.set_ylabel("share of weight on the SMALLEST prediction (%)")
    ax.set_ylim(0, 100)
    ax.set_xlim(0, 1.0 / n * 1.05)
    ax.set_title("The weaker the base models look, the closer the fusion gets to min()",
                 fontsize=12, color=INK)
    _save(fig, "fig_degeneracy_regimes.png")


def main() -> None:
    print("Drawing the degeneracy figures (no dataset required):")
    figure_weights()
    figure_regimes()
    print(f"\nDone. Figures in {FIG_DIR}/")


if __name__ == "__main__":
    main()
