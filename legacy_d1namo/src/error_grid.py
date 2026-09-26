"""
src/error_grid.py
=================
The PARKES ERROR GRID (also called the CONSENSUS error grid) -- the third assessment
metric in the paper's Section II-E, alongside RMSE and MARD. This is what produces the
paper's Fig. 10 and the "Zone A (%)" / "Zone A + B (%)" columns of its Table II.

WHY A GRID AND NOT JUST RMSE?
-----------------------------
RMSE and MARD say how *numerically* wrong we are. A doctor cares about something else:
would acting on this prediction HURT the patient? Being wrong by 2 mmol/L when the true
value is 12 (high but safe) is harmless. Being wrong by 2 mmol/L when the true value is
3.5 (dangerously low) could mean the patient eats nothing instead of treating a hypo.
Same numeric error, completely different clinical consequence.

So the Parkes grid plots every prediction as a point:
      x = REFERENCE glucose  (what the CGM actually measured -- the truth)
      y = PREDICTED glucose  (what our model said)
and carves the plane into five zones by how dangerous that particular mistake would be:

  Zone A -- no effect on clinical action.            (perfect / harmless)
  Zone B -- altered clinical action, little or no effect on outcome.  (acceptable)
  Zone C -- altered clinical action, likely to affect the outcome.    (bad)
  Zone D -- altered clinical action, could have significant medical risk.  (dangerous)
  Zone E -- altered clinical action, could have dangerous consequences.    (worst)

A perfect model puts 100% of points in A. The accepted clinical bar is that essentially
everything lands in A + B. The paper reports Zone A = 80.09% and Zone A + B = 99.49%.

WHERE THE BOUNDARY NUMBERS COME FROM
------------------------------------
The zone boundaries are NOT something we invent -- they were set by a panel of 100
diabetes clinicians and published as a fixed table of coordinates. We use the TYPE 1
diabetes grid (D1NAMO's patients are all Type 1), with the coordinates from:

    Pfutzner, Klonoff, Pardo, Parkes, "Technical Aspects of the Parkes Error Grid",
    J. Diabetes Sci. Technol. 2013;7(5):1275-1281.

Those coordinates are published in mg/dL, which is the unit American papers use. Our
data (D1NAMO, and the paper) is in mmol/L. The conversion is a fixed constant:

    1 mmol/L = 18.018 mg/dL

So we keep the official boundary table in mg/dL exactly as published (no transcription
risk), convert our mmol/L values to mg/dL for the zone test, and convert the boundaries
to mmol/L only when we DRAW them. See MATH.md section 8 for the full explanation.

HOW A POINT IS ASSIGNED TO A ZONE
---------------------------------
The grid is split by the diagonal y = x (a perfect prediction).

  * ABOVE the diagonal (we predicted HIGHER than the truth -- over-estimation) the
    boundaries are curves of the form  y = f(x): for a given reference x, each boundary
    tells you the predicted value at which you cross into the next-worse zone. So we
    look up f(x) for each boundary and see how many the point sits above.

  * BELOW the diagonal (we predicted LOWER than the truth -- under-estimation) the
    boundaries are more naturally curves of the form  x = g(y): for a given prediction y,
    each boundary tells you the reference value at which you cross into the next-worse
    zone. So we look up g(y) and see how many the point sits to the right of.

Each boundary is a POLYLINE -- a few corner points joined by straight segments -- so
"look up f(x)" is just linear interpolation between the two corners that bracket x.
np.interp does exactly that. Note that np.interp CLAMPS outside the listed range (it
returns the first/last y), and here that is exactly the behaviour we want: every boundary
polyline is listed until it exits the top of the 550 mg/dL grid, so clamping to that last
value correctly says "you cannot reach this zone out here".

Note there is no lower E zone in the Type 1 grid: massively under-estimating a high
reading is capped at zone D by the consensus panel.
"""

from __future__ import annotations

import numpy as np

# The one fixed unit conversion. Blood glucose in mg/dL = mmol/L * 18.018.
MGDL_PER_MMOL = 18.018

# ----------------------------------------------------------------------------------
# The official Type 1 Parkes boundary coordinates, in mg/dL, exactly as published.
# Each list is a polyline: consecutive (x, y) corners joined by straight lines.
# ----------------------------------------------------------------------------------

# UPPER boundaries (over-estimation, above the y = x diagonal). Written as y = f(x),
# so x is strictly increasing down each list.
_UPPER = {
    # crossing this line takes you from zone A into zone B
    "AB": [(0, 50), (30, 50), (140, 170), (280, 380), (430, 550)],
    "BC": [(0, 60), (30, 60), (50, 80), (70, 110), (260, 550)],
    "CD": [(0, 100), (25, 100), (50, 125), (80, 215), (125, 550)],
    "DE": [(0, 150), (35, 155), (50, 550)],
}

# LOWER boundaries (under-estimation, below the diagonal). Written as x = g(y),
# so y is strictly increasing down each list. (Type 1 has no lower E zone.)
_LOWER = {
    "AB": [(50, 0), (50, 30), (170, 145), (385, 300), (550, 450)],
    "BC": [(120, 0), (120, 30), (260, 130), (550, 250)],
    "CD": [(250, 0), (250, 40), (550, 150)],
}


def _upper_at(name: str, ref_mgdl: np.ndarray) -> np.ndarray:
    """Height y of the named UPPER boundary at reference value x (all mg/dL)."""
    xs, ys = zip(*_UPPER[name])
    return np.interp(ref_mgdl, xs, ys)


def _lower_at(name: str, pred_mgdl: np.ndarray) -> np.ndarray:
    """Reference x of the named LOWER boundary at prediction value y (all mg/dL)."""
    xs, ys = zip(*_LOWER[name])
    # This polyline is a function of y, so y is the "known x" argument to np.interp.
    return np.interp(pred_mgdl, ys, xs)


def parkes_zones(y_true_mmol: np.ndarray, y_pred_mmol: np.ndarray) -> np.ndarray:
    """Assign every (reference, prediction) pair to a Parkes zone letter.

    Inputs are in mmol/L (the units of D1NAMO and of the paper). Returns an array of
    single-character strings: 'A', 'B', 'C', 'D' or 'E', one per sample.
    """
    ref = np.asarray(y_true_mmol, dtype=float) * MGDL_PER_MMOL
    pred = np.asarray(y_pred_mmol, dtype=float) * MGDL_PER_MMOL

    # Start everyone in zone A, then promote to worse zones where the tests fire.
    zones = np.full(ref.shape, "A", dtype="<U1")

    over = pred > ref          # over-estimation -> use the upper boundaries
    under = ~over              # under-estimation (and exact hits) -> lower boundaries

    # --- over-estimation half. Test from the mildest boundary to the worst, so that a
    # point failing several tests ends up labelled with the WORST zone it reaches.
    for name, letter in (("AB", "B"), ("BC", "C"), ("CD", "D"), ("DE", "E")):
        crossed = over & (pred > _upper_at(name, ref))
        zones[crossed] = letter

    # --- under-estimation half (no E zone here in the Type 1 grid).
    for name, letter in (("AB", "B"), ("BC", "C"), ("CD", "D")):
        crossed = under & (ref > _lower_at(name, pred))
        zones[crossed] = letter

    return zones


def zone_percentages(y_true_mmol: np.ndarray, y_pred_mmol: np.ndarray) -> dict[str, float]:
    """Percentage of predictions falling in each zone, plus the combined 'A+B'.

    'A' and 'A+B' are the two columns the paper reports in its Table II.
    """
    zones = parkes_zones(y_true_mmol, y_pred_mmol)
    n = len(zones)
    out = {letter: float(np.sum(zones == letter) / n * 100.0) for letter in "ABCDE"}
    out["A+B"] = out["A"] + out["B"]
    return out


def draw_grid(ax, max_mmol: float = 30.56) -> None:
    """Draw the Parkes zone boundaries and zone letters onto a matplotlib axis.

    Everything is drawn in mmol/L so it matches the paper's Fig. 10 axes. `max_mmol`
    defaults to 30.56 mmol/L (= 550 mg/dL), the full extent of the published grid.
    """
    lim = max_mmol

    def to_mmol(seq):
        return [v / MGDL_PER_MMOL for v in seq]

    # Colours follow the paper's Fig. 10: the A/B border green, the B/C border blue,
    # the deeper borders black. Identity is carried by the zone LETTER labels too, so
    # the figure still reads correctly in greyscale or with colour-vision deficiency.
    styles = {"AB": "#1a7f37", "BC": "#1f6feb", "CD": "#24292f", "DE": "#24292f"}

    for name, colour in styles.items():
        xs, ys = zip(*_UPPER[name])
        ax.plot(to_mmol(xs), to_mmol(ys), color=colour, lw=1.2, zorder=2)
    for name, colour in (("AB", styles["AB"]), ("BC", styles["BC"]), ("CD", styles["CD"])):
        xs, ys = zip(*_LOWER[name])
        ax.plot(to_mmol(xs), to_mmol(ys), color=colour, lw=1.2, zorder=2)

    # The y = x diagonal: a perfect prediction.
    ax.plot([0, lim], [0, lim], color="#57606a", ls=":", lw=1.0, zorder=2)

    # Zone letters, positioned inside each region (mmol/L), as in the paper's figure.
    labels = [
        (1.1, 25.0, "E"), (3.3, 25.0, "D"), (6.1, 25.0, "C"), (11.1, 23.0, "B"),
        (14.4, 17.8, "A"), (18.9, 15.0, "A"), (21.1, 10.6, "B"), (24.4, 6.7, "C"),
        (26.7, 2.2, "D"),
    ]
    # The label coordinates above are chosen for the full 550 mg/dL grid. When we zoom
    # in to fit the data (which real datasets always need -- nobody has 30 mmol/L
    # readings) a label can land outside or right on the frame edge, so nudge any that
    # would collide with the border back inside.
    for x, y, text in labels:
        if x <= lim and y <= lim:
            ax.text(min(x, 0.96 * lim), min(y, 0.94 * lim), text,
                    fontsize=10, color="#24292f", ha="center", va="center")

    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Reference glucose concentration (mmol/L)")
    ax.set_ylabel("Prediction glucose concentration (mmol/L)")


if __name__ == "__main__":
    # Sanity checks we can verify by hand -- see MATH.md section 8 for the reasoning.
    # 1. A perfect prediction must be zone A.
    assert parkes_zones([5.0], [5.0])[0] == "A"
    # 2. A prediction identical to the reference at any level stays in A.
    assert all(parkes_zones([3.0, 8.0, 15.0], [3.0, 8.0, 15.0]) == "A")
    # 3. True 2.2 mmol/L (=39.6 mg/dL, a severe hypo) predicted as 16.7 mmol/L
    #    (=300 mg/dL) is the textbook worst case: "treat a severe low as a high" -> E.
    #    Note zone E only exists below ~50 mg/dL (2.78 mmol/L) reference: above that the
    #    DE boundary has already left the top of the grid, so D is the worst reachable.
    assert parkes_zones([2.2], [16.7])[0] == "E"
    assert parkes_zones([2.8], [16.7])[0] == "D"
    # 4. True 22.2 mmol/L (=400 mg/dL) predicted as 2.8 (=50 mg/dL) -- massive
    #    under-estimation of a high reading. Type 1 grid caps this at D.
    assert parkes_zones([22.2], [2.8])[0] == "D"
    # 5. A small error near a normal reading stays harmless.
    assert parkes_zones([6.0], [6.5])[0] == "A"

    pct = zone_percentages([5.0, 5.0, 2.8, 6.0], [5.0, 5.2, 16.7, 6.5])
    print("self-test passed. example zone percentages:", pct)
