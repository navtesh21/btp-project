"""
src/temporal_choquet.py
=======================
The paper's STAGE 2: the "temporal Choquet" (paper Section II-D, eq. 13, with N = 7).

THE IDEA (why this exists)
--------------------------
Blood glucose changes SLOWLY and smoothly -- it does not jump around minute to minute. So a
model's prediction for "now" should be consistent with its recent predictions. The paper
exploits this by fusing, FOR EACH MODEL, its recent prediction history with a Choquet
integral:

    paper: "the BG value of each model was fused ... based on the BG historical prediction
            values and BG current prediction value by using Choquet integral. ... N was set
            as 7, indicating that six closest BG historical values and the current value
            were used for analysis in each model."

So the "sources" of the Choquet integral here are NOT the 3 models -- they are the 7
TIME-POINTS of one model's own prediction stream:  [t-6, t-5, ..., t-1, t].

It is the SAME math as src/choquet.py (a Sugeno-lambda fuzzy measure + the Choquet
integral, eq. 13) -- only the "sources" change from models to time-lags. We reuse
ChoquetFuser directly.

EFFECT: this is a smart, robust SMOOTHING of each model's prediction stream. It damps noisy
one-off predictions using the recent context, because a proper fuzzy measure makes the
Choquet integral idempotent (a constant stream passes through unchanged) while pulling
outliers toward the recent consensus.

DENSITIES: the paper does not pin down the per-lag densities, so we use EQUAL densities for
the N time-lags (a symmetric measure -- every recent reading equally trusted). The density
value is a tunable knob; src/run_temporal.py sweeps a few values to see what helps.

NOTE ON DATA: glucose readings are ~5 min apart but there are gaps (between sessions/days).
A "history" is only valid across CONSECUTIVE-in-time readings, so we never let a window
cross a gap larger than `max_gap_min` minutes -- the window simply uses the contiguous run
available (and shrinks near the start of a run).
"""

from __future__ import annotations

import numpy as np

from src.choquet import ChoquetFuser

DEFAULT_N = 7              # paper: 6 historical + 1 current
# Equal density per time-lag. The VALUE controls the operator's character:
#   density = 1/N  -> the N sources' densities sum to 1 -> lambda = 0 -> a plain AVERAGE
#                     (a moving average: damps spikes, tracks the slow drift). Good default.
#   density > 1/N  -> lambda < 0 -> the integral leans toward the MAX (a spike contaminates
#                     the whole window) -- usually bad for smoothing.
#   density < 1/N  -> lambda > 0 -> leans toward the MIN.
# We default to the average-like setting and let run_temporal.py sweep others empirically.
DEFAULT_DENSITY = 1.0 / DEFAULT_N
DEFAULT_MAX_GAP_MIN = 15.0 # readings more than this far apart are NOT one contiguous run


def build_fusers(n: int, density: float) -> dict[int, ChoquetFuser]:
    """Pre-build one ChoquetFuser per possible window length k = 2..n.

    Densities are equal (`density` for every source), so the fuzzy measure depends only on
    the window length -- we can build each once and reuse it for every window of that size.
    (k = 1 needs no fuser: a single value smooths to itself.)
    """
    return {k: ChoquetFuser(np.full(k, density)) for k in range(2, n + 1)}


def temporal_choquet_smooth(
    preds: np.ndarray,
    timestamps: np.ndarray,
    n: int = DEFAULT_N,
    density: float = DEFAULT_DENSITY,
    max_gap_min: float = DEFAULT_MAX_GAP_MIN,
    fusers: dict[int, ChoquetFuser] | None = None,
) -> np.ndarray:
    """Smooth ONE model's prediction stream with the temporal Choquet integral.

    Parameters
    ----------
    preds : 1-D array of one model's predictions, **sorted by time ascending**.
    timestamps : matching 1-D array of datetimes (same order as preds).
    n : window size (paper uses 7 = current + 6 history).
    density : equal Sugeno density per time-lag.
    max_gap_min : a reading is only added to the history if it is within this many minutes
                  of the next one (keeps windows inside one contiguous recording run).

    Returns
    -------
    smoothed : 1-D array, same length as preds.
    """
    preds = np.asarray(preds, dtype=float)
    ts = np.asarray(timestamps, dtype="datetime64[s]")
    if fusers is None:
        fusers = build_fusers(n, density)

    out = np.empty_like(preds)
    for i in range(len(preds)):
        # Walk backwards from i collecting up to n consecutive-in-time predictions.
        window = [preds[i]]            # current prediction (newest)
        j = i - 1
        while j >= 0 and len(window) < n:
            gap_min = (ts[j + 1] - ts[j]) / np.timedelta64(1, "m")
            if gap_min > max_gap_min:  # a time gap -> stop; history ends here
                break
            window.append(preds[j])
            j -= 1
        window = window[::-1]          # oldest -> newest
        k = len(window)

        if k == 1:
            out[i] = window[0]         # nothing to fuse yet
        else:
            out[i] = fusers[k]._choquet_one(np.asarray(window))
    return out


if __name__ == "__main__":
    # Demo: a noisy-but-slowly-drifting glucose stream, 5 min apart. The temporal Choquet
    # should track the drift while damping the spikes.
    import numpy as np

    n_pts = 12
    t0 = np.datetime64("2024-10-01T09:00:00")
    ts = np.array([t0 + np.timedelta64(5 * i, "m") for i in range(n_pts)])
    true = np.linspace(7.0, 9.0, n_pts)                 # slow drift up
    rng = np.random.default_rng(0)
    noisy = true + rng.normal(0, 0.8, n_pts)
    noisy[5] += 4.0                                     # one big spike (a bad prediction)

    smoothed = temporal_choquet_smooth(noisy, ts)
    print("idx | noisy  -> smoothed (true)")
    for i in range(n_pts):
        mark = "  <-- spike damped" if i == 5 else ""
        print(f"{i:3d} | {noisy[i]:5.2f}  -> {smoothed[i]:5.2f}  ({true[i]:.2f}){mark}")
