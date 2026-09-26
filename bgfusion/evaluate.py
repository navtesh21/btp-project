"""
bgfusion/evaluate.py
====================
Leakage-controlled evaluation of the full pipeline.

THE POINT OF THIS FILE
----------------------
Blood-glucose estimation from physiological signals is a field where reported accuracy
depends enormously on HOW the data was split, because consecutive windows from one
person are highly correlated. Split them at random and the model can recognise the
person rather than the glucose level, which inflates every metric. So we never report a
single number: every configuration is evaluated under three progressively stricter
protocols.

    random_window   Shuffle all windows and k-fold them. The same subject appears in
                    train and test. This is what most published work reports, and it
                    is the optimistic case.
    subject_aware   k-fold by SUBJECT: no subject appears in both train and test.
    loso            Leave-one-subject-out: train on n-1 subjects, test on the held-out
                    one, rotate. The deployment case -- a brand-new patient.

Two controls are reported alongside every model, because without them the numbers are
uninterpretable:

    NoSkillBaseline  Always predict the TRAINING fold's mean glucose. Any model that
                     cannot beat this has learned nothing. It is computed per fold, so
                     it never sees the test labels.
    MinOfModels      The order statistic that a degenerate Choquet integral collapses
                     into (see stage3_fusion.degeneracy_report). Reporting it makes it
                     immediately visible when the "fusion" has stopped fusing.

WHY THE CLINICAL METRICS NEED THE BASELINE
------------------------------------------
Parkes/Clarke error-grid zone percentages are the headline clinical numbers in this
field, but they are extremely forgiving: because most glucose readings sit in a narrow
band, even predicting a constant lands the large majority of points in zones A+B. We
therefore always print the baseline's zone percentages next to the model's. A model
that beats the baseline on Zone A+B while LOSING to it on R-squared has not learned
anything useful, and only showing both makes that visible.

FEATURE SELECTION HAPPENS INSIDE THE FOLD
-----------------------------------------
stage2_fusion.select_features is fitted on the training split only, once per fold.
Selecting on the full dataset first would leak test labels into the feature choice.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold, KFold

from bgfusion.error_grid import zone_percentages
from bgfusion.metrics import mard, rmse
from bgfusion.stage2_fusion import feature_sets, select_features
from bgfusion.stage3_fusion import ChoquetMultiModelFusion

PROTOCOLS = ("random_window", "subject_aware", "loso")


def make_splits(df: pd.DataFrame, protocol: str, n_splits: int = 5, seed: int = 42):
    """Train/test index pairs for one protocol."""
    groups = df["subject"]
    if protocol == "random_window":
        return list(KFold(n_splits=n_splits, shuffle=True, random_state=seed).split(df))
    if protocol == "subject_aware":
        k = min(n_splits, groups.nunique())
        return list(GroupKFold(n_splits=k).split(df, df["glucose"], groups))
    if protocol == "loso":
        return list(GroupKFold(n_splits=groups.nunique()).split(df, df["glucose"], groups))
    raise ValueError(f"unknown protocol {protocol!r}")


def grade(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """The four numbers the paper reports, plus R-squared.

    R-squared is included because it is the one metric that exposes a model performing
    no better than the mean: it goes to zero (or negative), while RMSE, MARD and the
    error-grid zones all stay superficially respectable.
    """
    z = zone_percentages(y_true, y_pred)
    return {
        "R2": r2_score(y_true, y_pred),
        "RMSE": rmse(y_true, y_pred),
        "MARD": mard(y_true, y_pred),
        "ZoneA": z["A"],
        "ZoneA+B": z["A+B"],
    }


def run_protocol(df: pd.DataFrame, protocol: str, feature_cols: list[str],
                 do_selection: bool = True, n_splits: int = 5, seed: int = 42,
                 verbose: bool = True) -> tuple[pd.DataFrame, list[dict]]:
    """Evaluate every method under one protocol.

    Returns (predictions, diagnostics) where `predictions` is one row per test window
    with a column per method, and `diagnostics` records the per-fold degeneracy report
    and feature-selection summary.
    """
    X_all, y_all = df[feature_cols], df["glucose"]
    splits = make_splits(df, protocol, n_splits, seed)
    frames, diags = [], []

    for fold, (tr, te) in enumerate(splits, 1):
        X_tr, y_tr = X_all.iloc[tr], y_all.iloc[tr]
        X_te, y_te = X_all.iloc[te], y_all.iloc[te]
        g_tr = df["subject"].iloc[tr]

        # ---- Level 2c: selection, fitted on the TRAINING split only ---------------
        if do_selection:
            report = select_features(X_tr, y_tr, seed=seed)
            cols = report.selected
            sel_summary = report.summary()
        else:
            cols = feature_cols
            sel_summary = f"no selection ({len(cols)} features)"

        # ---- Level 3: fusion -------------------------------------------------------
        fusion = ChoquetMultiModelFusion(seed=seed, cv_folds=3).fit(
            X_tr[cols], y_tr, groups=g_tr)
        preds = fusion.predict_all(X_te[cols])

        # ---- controls ---------------------------------------------------------------
        # The baseline uses the TRAINING mean, so it never peeks at test labels.
        preds["NoSkillBaseline"] = np.full(len(te), float(y_tr.mean()))

        block = df.iloc[te][["subject", "timestamp", "glucose"]].copy()
        block["fold"] = fold
        for name, values in preds.items():
            block[name] = values
        frames.append(block)

        diags.append({"protocol": protocol, "fold": fold,
                      "n_train": len(tr), "n_test": len(te),
                      "n_features": len(cols), "selection": sel_summary,
                      **{f"r2_{k}": v for k, v in fusion.raw_r2_.items()},
                      **{k: v for k, v in fusion.degeneracy_.items()
                         if k in ("lambda", "weight_on_min", "density_spread",
                                  "equivalent_operator", "degenerate")}})
        if verbose:
            d = diags[-1]
            print(f"   [{protocol}] fold {fold}/{len(splits)}: "
                  f"train {len(tr)} test {len(te)} | {sel_summary} | "
                  f"fusion={d['equivalent_operator']}", flush=True)

    return pd.concat(frames, ignore_index=True), diags


def summarise(preds: pd.DataFrame, methods: list[str] | None = None) -> pd.DataFrame:
    """Grade every method on the pooled out-of-fold predictions."""
    methods = methods or [c for c in preds.columns
                          if c not in ("subject", "timestamp", "glucose", "fold")]
    # Put the controls last so the table reads model-first, control-last.
    controls = ["MinOfModels", "NoSkillBaseline"]
    ordered = [m for m in methods if m not in controls] + \
              [m for m in controls if m in methods]
    y = preds["glucose"].to_numpy()
    return pd.DataFrame([{"Method": m, **grade(y, preds[m].to_numpy())} for m in ordered])


def choquet_vs_min(preds: pd.DataFrame) -> dict[str, float]:
    """How close did the 'fusion' come to simply taking the minimum prediction?

    This is the empirical counterpart of the degeneracy theorem: a correlation near 1
    and a mean absolute difference near 0 mean the Choquet integral was computing an
    order statistic rather than fusing.
    """
    if "MinOfModels" not in preds or "Choquet" not in preds:
        return {}
    c, m = preds["Choquet"].to_numpy(), preds["MinOfModels"].to_numpy()
    mean_pred = preds[["RandomForest", "GradientBoosting", "Bagging"]].mean(axis=1).to_numpy()
    return {
        "corr_choquet_min": float(np.corrcoef(c, m)[0, 1]),
        "mad_choquet_min": float(np.abs(c - m).mean()),
        "mad_choquet_mean": float(np.abs(c - mean_pred).mean()),
    }
