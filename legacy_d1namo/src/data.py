"""
src/data.py
===========
A *stand-in* dataset so we can build and test the Choquet fusion (Image #1) TODAY,
before the real ECG/PPG signal processing exists.

WHAT THIS PRODUCES
------------------
- X : a table of "features" (numbers describing a moment of ECG/PPG).
- y : the blood-glucose (BG) value we want to predict, in mmol/L.

We deliberately mirror the paper's structure: the paper extracts TWO kinds of features
-- "temporal" (time statistics) and "morphological" (waveform shape). So we generate two
blocks of columns with those names. Later, when real feature extraction is built, we will
replace this file's output with the real features and NOTHING ELSE has to change.

IMPORTANT: this is synthetic (made-up) data. It is NOT medical data and predicts nothing
real. Its only job is to give the fusion code realistic-looking numbers to chew on so we
can verify the machinery works.
"""

from __future__ import annotations  # lets us write modern type hints on older Pythons

import numpy as np
import pandas as pd


def make_bg_dataset(
    n_samples: int = 2000,
    n_temporal: int = 12,
    n_morphological: int = 8,
    noise: float = 0.8,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """Create a synthetic blood-glucose dataset.

    Parameters
    ----------
    n_samples : int
        How many rows (each row = one "measurement moment").
    n_temporal : int
        How many "temporal" (time-statistic) feature columns to create.
    n_morphological : int
        How many "morphological" (waveform-shape) feature columns to create.
    noise : float
        How much random wobble to add to the blood-glucose value. Bigger = harder
        to predict (more realistic, since real biology is noisy).
    seed : int
        A fixed number so the "random" data is the SAME every run. This is called
        making the experiment *reproducible* -- crucial in science.

    Returns
    -------
    X : pandas.DataFrame   shape (n_samples, n_temporal + n_morphological)
    y : pandas.Series      shape (n_samples,)   the blood-glucose targets in mmol/L
    """
    # `default_rng(seed)` builds a random-number generator seeded with `seed`.
    # Same seed -> same numbers -> reproducible results.
    rng = np.random.default_rng(seed)

    # --- 1. Create the raw feature columns -------------------------------------------
    # `standard_normal` draws numbers from a bell curve centred at 0 with spread 1.
    # Shape (n_samples, n_temporal) means "n_samples rows, n_temporal columns".
    temporal = rng.standard_normal((n_samples, n_temporal))
    morphological = rng.standard_normal((n_samples, n_morphological))

    # --- 2. Decide HOW blood glucose depends on the features -------------------------
    # In reality the relationship is unknown and complex. We invent a relationship that
    # is non-linear (curvy) so simple models can't trivially solve it -- this is what
    # makes Random Forest / Gradient Boosting / Bagging actually useful to compare.
    #
    # We say: only the FIRST few columns of each block truly influence BG. The rest are
    # "distractor" / noise features -- exactly like real data, where many measured
    # numbers turn out to be useless. (Later, "feature selection" removes those.)

    # Blood glucose driven by temporal features (a curvy mix):
    bg_from_temporal = (
        1.5 * temporal[:, 0]                 # a straight-line effect from column 0
        + 0.8 * temporal[:, 1] ** 2          # a U-shaped (quadratic) effect from column 1
        + 0.6 * np.sin(temporal[:, 2] * 2.0) # a wavy effect from column 2
    )

    # Blood glucose driven by morphological features (another curvy mix):
    bg_from_morph = (
        1.2 * morphological[:, 0]                              # straight-line
        + 0.9 * morphological[:, 1] * morphological[:, 2]      # an INTERACTION (two
        #                                                        features multiplied --
        #                                                        only matters when BOTH
        #                                                        are large)
    )

    # --- 3. Combine into a realistic blood-glucose value -----------------------------
    # Start from a baseline of 7 mmol/L (a typical human value) and add the effects.
    raw = 7.0 + bg_from_temporal + bg_from_morph

    # Add random noise so it isn't perfectly predictable (real measurements are noisy).
    raw = raw + noise * rng.standard_normal(n_samples)

    # Real CGM devices in the paper read between 2.2 and 21.8 mmol/L. `np.clip` forces
    # every value to stay inside that range (anything below 2.2 becomes 2.2, etc.).
    y_values = np.clip(raw, 2.2, 21.8)

    # --- 4. Package as nicely-labelled tables ----------------------------------------
    # Build human-readable column names like "temporal_00", "morph_03", ...
    temporal_names = [f"temporal_{i:02d}" for i in range(n_temporal)]
    morph_names = [f"morph_{i:02d}" for i in range(n_morphological)]

    # Glue the two blocks side by side into one wide array, then wrap in a DataFrame
    # (a DataFrame is just a spreadsheet-like table with named columns).
    features = np.hstack([temporal, morphological])
    X = pd.DataFrame(features, columns=temporal_names + morph_names)
    y = pd.Series(y_values, name="blood_glucose_mmol_L")

    return X, y


# Convenience lists so other files can ask "which columns are temporal vs morphological".
# We rebuild a tiny dataset once to read the names back out (cheap, runs only on import
# if someone explicitly calls this helper).
def feature_groups(X: pd.DataFrame) -> dict[str, list[str]]:
    """Split the columns of X into the paper's two feature families.

    Returns a dict like {"temporal": [...], "morphological": [...]}.
    This becomes useful later when we build the paper's 3 feature SETS
    (temporal-only, morphological-only, and the fusion of both).
    """
    temporal = [c for c in X.columns if c.startswith("temporal_")]
    morph = [c for c in X.columns if c.startswith("morph_")]
    return {"temporal": temporal, "morphological": morph}


# Running `python -m src.data` directly will print a small preview, so you can SEE the
# data with your own eyes. `__name__ == "__main__"` is True only when this file is run
# directly (not when imported by another file).
if __name__ == "__main__":
    X, y = make_bg_dataset()
    print("Feature table X — shape (rows, columns):", X.shape)
    print(X.head(), "\n")  # .head() shows the first 5 rows
    print("Target y — first 5 blood-glucose values (mmol/L):")
    print(y.head().to_string(), "\n")
    print("Blood glucose ranges from", round(y.min(), 2), "to", round(y.max(), 2), "mmol/L")
    print("Feature groups:", feature_groups(X))
