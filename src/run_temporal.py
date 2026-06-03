"""
src/run_temporal.py
===================
Does the TEMPORAL Choquet (paper stage 2) actually improve blood-glucose prediction?

We use leave-one-subject-out (each held-out patient is a full time-ordered sequence, which
is exactly what temporal smoothing needs). For each fold we:
  1. train the 3 models + multi-model Choquet fusion on the other 8 patients,
  2. predict the held-out patient's readings (sorted by time),
  3. compare:
       RAW         = multi-model Choquet on the raw per-model predictions (Image #2 only)
       TEMPORAL    = first smooth EACH model's prediction stream with the temporal Choquet
                     (stage 2), THEN multi-model fuse (stage 2 + Image #2 together)
We sweep a few density settings for the temporal smoother (the paper leaves this open) and
report RMSE / MARD for each, plus the no-skill baseline for context.

Training happens once per fold; the smoothing variants are cheap, applied to the stored
predictions afterward.

Run:  python -m src.run_temporal
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

from src.d1namo import DATA_ROOT
from src.fusion import ChoquetMultiModelFusion
from src.metrics import mard, rmse
from src.temporal_choquet import build_fusers, temporal_choquet_smooth

CACHE = os.path.join(DATA_ROOT, "features_temporal.csv")


def main() -> None:
    # Load cached features WITH timestamps + subject (we need time order for smoothing).
    df = pd.read_csv(CACHE, dtype={"subject": str})
    df["subject"] = df["subject"].str.zfill(3)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    feat_cols = [c for c in df.columns if c.startswith("FE")]
    X, y, groups = df[feat_cols], df["glucose"], df["subject"]

    print(f"{len(df)} windows, {groups.nunique()} patients. "
          f"No-skill baseline (predict mean) RMSE = {y.std():.3f} mmol/L\n")

    # The smoothing variants to compare. N=7 (paper). density 1/7 ~ average; we also try a
    # couple of others to show the effect.
    N = 7
    variants = {
        "RAW (no temporal)": None,
        "temporal d=1/7 (mean-like)": 1.0 / 7,
        "temporal d=0.20": 0.20,
        "temporal d=0.35": 0.35,
    }
    # Pre-build the per-window fusers for each density (reused across folds).
    fusers = {name: (build_fusers(N, d) if d is not None else None)
              for name, d in variants.items()}

    collected = {name: [] for name in variants}
    truth = []

    gkf = GroupKFold(n_splits=groups.nunique())
    for fold, (tr, te) in enumerate(gkf.split(X, y, groups), 1):
        fusion = ChoquetMultiModelFusion(seed=42, cv_folds=3).fit(X.iloc[tr], y.iloc[tr])

        # Held-out patient, sorted in time.
        test = df.iloc[te].sort_values("timestamp")
        ts = test["timestamp"].values
        model_preds = fusion._stack_predictions(test[feat_cols])   # (n_readings, 3 models)

        for name, d in variants.items():
            if d is None:
                fused = fusion.fuser_.fuse(model_preds)            # Image #2 only
            else:
                # Smooth each model's stream over time, then multi-model fuse.
                smoothed = np.column_stack([
                    temporal_choquet_smooth(model_preds[:, m], ts, n=N, density=d,
                                            fusers=fusers[name])
                    for m in range(model_preds.shape[1])
                ])
                fused = fusion.fuser_.fuse(smoothed)
            collected[name].append(fused)

        truth.append(test["glucose"].to_numpy())
        print(f"   fold {fold}: patient sequence of {len(te)} readings done")

    y_true = np.concatenate(truth)
    print(f"\n{'METHOD':>30s} | {'RMSE (mmol/L)':>13s} | {'MARD (%)':>9s}")
    print("-" * 60)
    for name in variants:
        preds = np.concatenate(collected[name])
        print(f"{name:>30s} | {rmse(y_true, preds):13.3f} | {mard(y_true, preds):9.2f}")

    print("\nIf a 'temporal' row beats 'RAW', the stage-2 temporal Choquet helped. Because "
          "our errors are largely BETWEEN-patient bias (not noise), expect a modest gain at "
          "best -- temporal smoothing mainly removes variance, not bias.")


if __name__ == "__main__":
    main()
