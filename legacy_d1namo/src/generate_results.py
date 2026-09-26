"""
src/generate_results.py
=======================
Produce the RESULTS of this project, in the exact shape the paper reports them.

The paper grades its method three ways (Section II-E): RMSE, MARD, and the Parkes
error grid (Zone A %, Zone A + B %). Its Table II lists all four numbers PER FOLD of a
tenfold cross-validation, plus an average row. Its Fig. 9 plots predicted vs reference
glucose over time, and its Fig. 10 is the Parkes scatter. This script generates the
data behind all of that on our real D1NAMO features; src/make_figures.py then draws it.

WHY THIS SCRIPT EXISTS SEPARATELY FROM run_d1namo.py
----------------------------------------------------
run_d1namo.py PRINTS a summary and throws the predictions away. To draw Fig. 9 and
Fig. 10 we need to keep every individual prediction, paired with its true value, its
patient, and its timestamp. So this script saves them to CSV, and the plotting script
reads those CSVs. That split means we can re-tune a figure in seconds without re-running
the (slow) cross-validation.

THE TWO PROTOCOLS -- and why we report both
-------------------------------------------
  PROTOCOL A -- pooled tenfold cross-validation. This is what the paper does: pool all
     participants' windows and split into ten folds, so the same patient can appear in
     both training and test (on different readings). It measures "how well does this
     work for a patient the model has already been calibrated on?"

  PROTOCOL B -- leave-one-subject-out. Train on 8 patients, test on the 9th, rotate.
     The test patient is a complete stranger. This measures "will it work on someone
     new, with no calibration?" It is the harder and more honest question, and it is
     NOT what the paper's headline number answers.

Reporting both is the honest thing to do: Protocol A is the like-for-like comparison
with the paper's Table II, and Protocol B says what the method is actually worth on a
new person.

COST
----
Every fold trains the three base models twice over: once via cross-validation to
estimate the Choquet densities, and once on the full training split. On a CPU that is
roughly two minutes per fold, so the fold counts are adjustable from the command line:

    python -m src.generate_results                     # paper-faithful: 10-fold + LOSO
    python -m src.generate_results --folds-a 5 --cv-folds 2   # quicker, same pipeline
    python -m src.generate_results --protocols A       # Protocol A only

Protocol A's predictions are written to disk as soon as Protocol A finishes, so the
figures for it can be drawn while Protocol B is still running.

Outputs land in  results/.
"""

from __future__ import annotations

import argparse
import os
import time

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold

from src.d1namo import DATA_ROOT
from src.error_grid import zone_percentages
from src.fusion import ChoquetMultiModelFusion
from src.metrics import mard, rmse

CACHE = os.path.join(DATA_ROOT, "features_temporal.csv")
RESULTS_DIR = "results"

# The paper uses tenfold cross-validation for its Table II, so Protocol A does too.
N_FOLDS_A = 10


def load_features() -> pd.DataFrame:
    """Load the cached real D1NAMO features, keeping subject + timestamp columns.

    The dtype/zfill dance is deliberate: patient ids are '001'..'009', and pandas will
    happily read '001' as the integer 1, which silently breaks every per-patient
    grouping downstream. Reading as str and re-padding keeps them intact.
    """
    df = pd.read_csv(CACHE, dtype={"subject": str})
    df["subject"] = df["subject"].str.zfill(3)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def run_protocol(df: pd.DataFrame, splits, protocol: str, cv_folds: int = 3) -> pd.DataFrame:
    """Run one cross-validation protocol and return every prediction as a tidy frame.

    One row per test window, with columns: subject, timestamp, fold, glucose (the true
    reference value), and one column per method (the 3 base models plus PlainAverage,
    WeightedAverage and Choquet).
    """
    feat_cols = [c for c in df.columns if c.startswith("FE")]
    X, y = df[feat_cols], df["glucose"]

    frames = []
    densities = []
    for fold, (tr, te) in enumerate(splits, 1):
        t0 = time.time()
        # cv_folds controls only the density estimate (not the final models), so
        # lowering it trades a slightly noisier density for a lot less compute.
        fusion = ChoquetMultiModelFusion(seed=42, cv_folds=cv_folds).fit(
            X.iloc[tr], y.iloc[tr])
        preds = fusion.predict_all(X.iloc[te])

        block = df.iloc[te][["subject", "timestamp", "glucose"]].copy()
        block["fold"] = fold
        for name, values in preds.items():
            block[name] = values
        frames.append(block)

        # Keep the fuzzy densities too -- they show WHICH model the Choquet integral
        # trusted in each fold, which is worth a figure of its own.
        densities.append(
            {"fold": fold, **dict(zip(fusion.model_names_, fusion.densities_))}
        )

        print(f"   [{protocol}] fold {fold}/{len(splits)}: "
              f"train {len(tr)}, test {len(te)}  ({time.time() - t0:.0f}s)", flush=True)

    out = pd.concat(frames, ignore_index=True)
    pd.DataFrame(densities).to_csv(
        os.path.join(RESULTS_DIR, f"densities_{protocol}.csv"), index=False)
    return out


def grade(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """All four of the paper's numbers for one set of predictions."""
    z = zone_percentages(y_true, y_pred)
    return {
        "RMSE (mmol/L)": rmse(y_true, y_pred),
        "MARD (%)": mard(y_true, y_pred),
        "Zone A (%)": z["A"],
        "Zone A+B (%)": z["A+B"],
    }


def per_fold_table(preds: pd.DataFrame, method: str = "Choquet") -> pd.DataFrame:
    """The paper's Table II layout: one row per fold for a single method, plus Average.

    The 'Average' row is the average OF THE FOLD SCORES (that is what the paper's
    Average row is), not the score computed over all the pooled predictions at once.
    Those two differ slightly whenever the folds have different sizes.
    """
    rows = []
    for fold, block in preds.groupby("fold"):
        rows.append({"Fold": str(fold), **grade(block["glucose"], block[method])})
    table = pd.DataFrame(rows)
    avg = table.drop(columns="Fold").mean().to_dict()
    return pd.concat([table, pd.DataFrame([{"Fold": "Average", **avg}])], ignore_index=True)


def method_table(preds: pd.DataFrame, methods: list[str]) -> pd.DataFrame:
    """Every method graded on the pooled predictions across all folds."""
    return pd.DataFrame([{"Method": m, **grade(preds["glucose"], preds[m])} for m in methods])


def _show(title: str, table: pd.DataFrame) -> None:
    print(f"\n=== {title} ===")
    print(table.to_string(index=False, float_format=lambda v: f"{v:.2f}"))


def _write_tables(preds: pd.DataFrame, protocol: str, label: str,
                  methods: list[str]) -> None:
    """Save (and print) both tables for one protocol, as soon as it finishes."""
    t2 = per_fold_table(preds)
    mt = method_table(preds, methods)
    t2.to_csv(os.path.join(RESULTS_DIR, f"tableII_{protocol}.csv"), index=False)
    mt.to_csv(os.path.join(RESULTS_DIR, f"methods_{protocol}.csv"), index=False)
    _show(f"TABLE II equivalent - Choquet fusion, {label}", t2)
    _show(f"All methods - {label}", mt)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folds-a", type=int, default=N_FOLDS_A,
                        help="folds for Protocol A (paper uses 10)")
    parser.add_argument("--cv-folds", type=int, default=3,
                        help="inner folds used to estimate the Choquet densities")
    parser.add_argument("--protocols", default="AB",
                        help="which protocols to run: 'A', 'B' or 'AB'")
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    df = load_features()
    groups = df["subject"]

    baseline = float(df["glucose"].std())
    print(f"Loaded REAL D1NAMO features: {len(df)} windows x "
          f"{sum(c.startswith('FE') for c in df.columns)} features "
          f"from {groups.nunique()} patients.")
    print(f"Glucose range: {df['glucose'].min():.1f} - {df['glucose'].max():.1f} mmol/L")
    print(f"No-skill baseline (always predict the mean) RMSE = {baseline:.3f} mmol/L\n")

    methods = list(ChoquetMultiModelFusion().model_names_) + [
        "PlainAverage", "WeightedAverage", "Choquet"]

    # ---- PROTOCOL A: pooled k-fold, the paper's own setup -------------------------
    # Written to disk immediately so the figures can be drawn while B still runs.
    if "A" in args.protocols:
        print(f"PROTOCOL A: pooled {args.folds_a}-fold (paper-style; a patient may "
              f"appear in both train and test)")
        kf = KFold(n_splits=args.folds_a, shuffle=True, random_state=42)
        preds_a = run_protocol(df, list(kf.split(df)), "protocolA", args.cv_folds)
        preds_a.to_csv(os.path.join(RESULTS_DIR, "predictions_protocolA.csv"), index=False)
        _write_tables(preds_a, "protocolA",
                      f"pooled {args.folds_a}-fold (Protocol A)", methods)

    # ---- PROTOCOL B: leave-one-subject-out, the honest generalisation test --------
    if "B" in args.protocols:
        print(f"\nPROTOCOL B: leave-one-subject-out ({groups.nunique()} folds, test "
              f"patient never seen in training)")
        gkf = GroupKFold(n_splits=groups.nunique())
        preds_b = run_protocol(df, list(gkf.split(df, df["glucose"], groups)),
                               "protocolB", args.cv_folds)
        preds_b.to_csv(os.path.join(RESULTS_DIR, "predictions_protocolB.csv"), index=False)
        _write_tables(preds_b, "protocolB",
                      "leave-one-subject-out (Protocol B)", methods)

    print(f"\nSaved predictions and tables to {RESULTS_DIR}/")
    print("Reminder: this is an ECG-temporal-only reproduction. D1NAMO has no PPG, so "
          "the paper's PPG features and its ResNet morphological branch are absent, and "
          "the RMSE is correspondingly higher than the paper's 1.49 mmol/L.")


if __name__ == "__main__":
    main()
