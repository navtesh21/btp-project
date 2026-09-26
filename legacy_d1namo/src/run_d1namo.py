"""
src/run_d1namo.py
=================
Evaluate the Image #1 fusion on the REAL D1NAMO features (the cached output of
src/d1namo.py). This is the real-data counterpart of src/main.py.

We report results under TWO evaluation protocols, because how you split the data changes
what the score *means*:

  PROTOCOL A -- "paper-style" k-fold (pooled).
     Mix everyone's windows together and do standard k-fold cross-validation. The SAME
     patient can appear in both train and test (on different readings). This mirrors the
     paper, which pooled all participants and split by DAYS, aiming for a "universal" model
     that has seen each person before. Scores are optimistic for brand-new patients.

  PROTOCOL B -- leave-one-subject-out (GroupKFold by patient).
     Train on 8 patients, test on the 9th; rotate. The test patient is a COMPLETE STRANGER
     to the model. This is the honest test of "will it work on someone new?" and is usually
     harder (individual physiology differs a lot -- a point the paper itself makes).

For each protocol we collect predictions across all folds and grade every method
(each base model, plain average, weighted average, Choquet) with RMSE and MARD.

Run it (after the feature cache exists):   python -m src.run_d1namo
"""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import GroupKFold, KFold

from src.d1namo import build_dataset
from src.fusion import ChoquetMultiModelFusion
from src.metrics import mard, rmse


def _evaluate(splits, X, y, groups, seed=42) -> dict[str, np.ndarray]:
    """Run the given train/test splits and return {method: predictions over all test rows}.

    We also return the matching true values under key '_truth' (in the same order).
    """
    methods = None
    collected: dict[str, list[np.ndarray]] = {}
    truth: list[np.ndarray] = []

    for fold, (tr, te) in enumerate(splits, 1):
        Xtr, Xte = X.iloc[tr], X.iloc[te]
        ytr, yte = y.iloc[tr], y.iloc[te]

        # cv_folds=3 (not 5) for the density estimate: ~40% less compute, negligible
        # effect on the densities. Keeps the full evaluation fast.
        fusion = ChoquetMultiModelFusion(seed=seed, cv_folds=3).fit(Xtr, ytr)
        preds = fusion.predict_all(Xte)

        if methods is None:
            methods = list(preds.keys())
            collected = {m: [] for m in methods}
        for m in methods:
            collected[m].append(preds[m])
        truth.append(yte.to_numpy())
        print(f"   fold {fold}: trained on {len(tr)} rows, tested on {len(te)} rows")

    out = {m: np.concatenate(v) for m, v in collected.items()}
    out["_truth"] = np.concatenate(truth)
    return out


def _report(title: str, results: dict[str, np.ndarray], model_names: list[str]) -> None:
    y_true = results["_truth"]
    print(f"\n=== {title} ===")
    print(f"{'METHOD':>16s} | {'RMSE (mmol/L)':>13s} | {'MARD (%)':>9s}")
    print("-" * 46)
    order = model_names + ["PlainAverage", "WeightedAverage", "Choquet"]
    for name in order:
        if name not in results:
            continue
        r = rmse(y_true, results[name])
        m = mard(y_true, results[name])
        star = "  <-- fusion" if name == "Choquet" else ""
        print(f"{name:>16s} | {r:13.3f} | {m:9.2f}{star}")


def main() -> None:
    # Load the cached real features (built by src/d1namo.py).
    X, y, groups = build_dataset(use_cache=True)
    print(f"Loaded REAL D1NAMO features: {X.shape[0]} windows x {X.shape[1]} features "
          f"from {groups.nunique()} patients.")
    print(f"Glucose range: {y.min():.1f} - {y.max():.1f} mmol/L\n")

    model_names = list(ChoquetMultiModelFusion().model_names_)

    # PROTOCOL A: paper-style pooled k-fold.
    print("PROTOCOL A: paper-style 5-fold (same patient may appear in train & test)")
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    res_a = _evaluate(list(kf.split(X)), X, y, groups)
    _report("PROTOCOL A — pooled 5-fold", res_a, model_names)

    # PROTOCOL B: leave-one-subject-out.
    n_subjects = groups.nunique()
    print(f"\nPROTOCOL B: leave-one-subject-out ({n_subjects} folds, test patient unseen)")
    gkf = GroupKFold(n_splits=n_subjects)
    res_b = _evaluate(list(gkf.split(X, y, groups)), X, y, groups)
    _report("PROTOCOL B — leave-one-subject-out", res_b, model_names)

    print("\nReminder: this is an ECG-temporal-only reproduction (no PPG, no ResNet "
          "morphological branch), so expect higher RMSE than the paper's 1.49 mmol/L, "
          "which used ECG+PPG + morphological features + the full 9-model fusion.")


if __name__ == "__main__":
    main()
