"""
bgfusion/stage3_fusion.py
=========================
LEVEL 3 of the paper: three models, fused by a weight-based Choquet integral.

    [RandomForest]     \\
    [GradientBoosting]  >---> [Choquet integral fusion] ---> BG output
    [Bagging]          /

The Choquet integral needs a DENSITY per model: a number in (0,1) saying how competent
that model is on its own. We estimate it as the model's out-of-fold R-squared on the
training split, which is an honest estimate because no row scores itself.

TWO LESSONS BAKED IN FROM THE EARLIER D1NAMO STUDY
---------------------------------------------------
1. THE INNER SPLITTER MUST BE EXPLICIT AND GROUP-AWARE.
   Passing an integer to `cross_val_predict(..., cv=3)` makes scikit-learn use KFold
   WITHOUT shuffling, i.e. contiguous blocks of rows. Feature tables arrive sorted by
   subject, so each "fold" became a block of whole subjects and the density silently
   measured cross-subject generalisation instead of ordinary competence. Every density
   collapsed to the floor. We therefore always pass a real splitter, and when subject
   labels are available we use GroupKFold deliberately so that the density matches the
   generalisation regime we are actually evaluating.

2. EQUAL DENSITIES DESTROY THE FUSION -- so we detect it.
   With a Sugeno lambda-measure, if every density equals the same g then the measure is
   SYMMETRIC and the Choquet integral collapses to an OWA operator with geometric
   weights (see `degeneracy_report`):

        w_j = g * beta^(j-1),   beta = 1 + lambda*g,   j sorted LARGEST -> smallest

   Since sum(g_i) < 1 implies lambda > 0 implies beta > 1, weight piles onto the
   SMALLEST prediction; as g -> 0 the "fusion" converges to the minimum operator and
   carries no information about which model is better. The general fact that a
   symmetric fuzzy measure yields an OWA operator is standard aggregation theory
   (Grabisch; Marichal). What matters in practice is that a saturating density
   estimator induces that symmetry by accident, so `degeneracy_report` computes the
   realised weights and flags it instead of letting it pass unnoticed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold, KFold, cross_val_predict

from bgfusion.base_models import build_models
from bgfusion.choquet import ChoquetFuser, solve_lambda

DENSITY_FLOOR, DENSITY_CEIL = 0.01, 0.99


def degeneracy_report(densities: np.ndarray) -> dict[str, object]:
    """Diagnose whether the Choquet integral still discriminates between models.

    Returns the solved lambda, the realised per-rank OWA weights (largest prediction
    first), the share of weight landing on the smallest prediction, and a boolean
    `degenerate` flag. `weight_on_min` near 1.0 means the fusion has become a minimum
    operator and is no longer using model competence at all.
    """
    g = np.asarray(densities, dtype=float)
    n = len(g)
    lam = solve_lambda(g)

    # Realised weights for the actual (possibly unequal) densities, obtained by walking
    # the Sugeno recursion over ranks exactly as ChoquetFuser does.
    order = np.argsort(g)[::-1]
    g_sorted = g[order]
    weights, g_prev = [], 0.0
    for j in range(n):
        g_curr = g_prev + g_sorted[j] + lam * g_prev * g_sorted[j]
        weights.append(g_curr - g_prev)
        g_prev = g_curr

    spread = float(g.max() - g.min())
    all_floor = bool(np.allclose(g, DENSITY_FLOOR, atol=1e-9))
    symmetric = bool(spread < 1e-6)

    # When the densities are equal the measure is symmetric, so the integral is an OWA
    # and cannot distinguish the models at all. WHICH OWA it becomes still depends on
    # g, and the two ends of that range behave very differently, so name it:
    #   g -> 0     : lambda -> inf, weight piles on the smallest  -> minimum operator
    #   sum(g) = 1 : lambda = 0, equal weights                    -> arithmetic mean
    if not symmetric:
        operator = "competence-weighted (non-degenerate)"
    elif weights[-1] > 0.80:
        operator = "minimum-like OWA"
    elif np.allclose(weights, 1.0 / n, atol=1e-6):
        operator = "arithmetic mean"
    else:
        operator = "rank-weighted OWA (no model discrimination)"

    return {
        "densities": g.tolist(),
        "lambda": float(lam),
        "weights_largest_to_smallest": [float(w) for w in weights],
        "weight_on_min": float(weights[-1]),
        "density_spread": spread,
        "all_at_floor": all_floor,
        "equivalent_operator": operator,
        # Degenerate = the densities carry no ordering information, so the "fusion"
        # reduces to a fixed function of the sorted predictions.
        "degenerate": bool(symmetric or all_floor),
    }


class ChoquetMultiModelFusion:
    """Train the three base models and fuse them with a Sugeno-lambda Choquet integral."""

    def __init__(self, seed: int = 42, cv_folds: int = 3, group_aware: bool = True):
        self.seed = seed
        self.cv_folds = cv_folds
        self.group_aware = group_aware
        self.models = build_models(seed)
        self.model_names_: list[str] = list(self.models.keys())
        self.densities_: np.ndarray | None = None
        self.raw_r2_: dict[str, float] = {}
        self.fuser_: ChoquetFuser | None = None
        self.degeneracy_: dict[str, object] | None = None

    def _splitter(self, groups: pd.Series | None):
        """The inner splitter used for the density estimate.

        Never an integer (see the module docstring). When subject labels are supplied
        we split BY SUBJECT, so the density answers the same question the outer
        evaluation asks.
        """
        if self.group_aware and groups is not None and groups.nunique() >= self.cv_folds:
            return GroupKFold(n_splits=self.cv_folds)
        return KFold(n_splits=self.cv_folds, shuffle=True, random_state=self.seed)

    def fit(self, X: pd.DataFrame, y: pd.Series,
            groups: pd.Series | None = None) -> "ChoquetMultiModelFusion":
        splitter = self._splitter(groups)
        split_kw = {"groups": groups} if isinstance(splitter, GroupKFold) else {}

        densities = []
        for name in self.model_names_:
            model = self.models[name]
            oof = cross_val_predict(model, X, y, cv=splitter, **split_kw)
            r2 = r2_score(y, oof)
            self.raw_r2_[name] = float(r2)
            densities.append(float(np.clip(r2, DENSITY_FLOOR, DENSITY_CEIL)))
            model.fit(X, y)

        self.densities_ = np.array(densities)
        self.fuser_ = ChoquetFuser(self.densities_, self.model_names_)
        self.degeneracy_ = degeneracy_report(self.densities_)
        return self

    def _stack(self, X: pd.DataFrame) -> np.ndarray:
        return np.column_stack([self.models[n].predict(X) for n in self.model_names_])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        assert self.fuser_ is not None, "call fit() first"
        return self.fuser_.fuse(self._stack(X))

    def predict_all(self, X: pd.DataFrame) -> dict[str, np.ndarray]:
        """Every prediction we can make, so the fusion can be judged against baselines."""
        assert self.fuser_ is not None and self.densities_ is not None
        preds = self._stack(X)
        out = {n: preds[:, i] for i, n in enumerate(self.model_names_)}
        out["PlainAverage"] = preds.mean(axis=1)
        out["WeightedAverage"] = preds @ (self.densities_ / self.densities_.sum())
        out["Choquet"] = self.fuser_.fuse(preds)
        # The order statistic the integral degenerates INTO. Carrying it as an explicit
        # column lets us show empirically how close the "fusion" is to taking a minimum.
        out["MinOfModels"] = preds.min(axis=1)
        return out


if __name__ == "__main__":
    # The degeneracy result, checked numerically against the closed form.
    print("Equal-density degeneracy of the Sugeno-lambda Choquet integral (n = 3)")
    print(f"{'g':>8s} {'lambda':>10s} {'w(largest)':>11s} {'w(mid)':>9s} "
          f"{'w(min)':>9s}   collapses to")
    for g in (0.01, 0.05, 0.10, 0.20, 1 / 3):
        rep = degeneracy_report(np.array([g, g, g]))
        w = rep["weights_largest_to_smallest"]
        print(f"{g:8.3f} {rep['lambda']:10.2f} {w[0]:11.4f} {w[1]:9.4f} "
              f"{w[2]:9.4f}   {rep['equivalent_operator']}")

    # A non-degenerate case for contrast: unequal densities DO discriminate.
    rep = degeneracy_report(np.array([0.30, 0.10, 0.25]))
    print()
    print(f"unequal densities [0.30, 0.10, 0.25] -> "
          f"{rep['equivalent_operator']}, degenerate={rep['degenerate']}")
    assert not rep["degenerate"]

    # Closed form: w_j = g * beta^(j-1), beta = 1 + lambda*g.
    g = 0.01
    rep = degeneracy_report(np.array([g, g, g]))
    beta = 1 + rep["lambda"] * g
    closed = [g * beta ** j for j in range(3)]
    assert np.allclose(closed, rep["weights_largest_to_smallest"], atol=1e-9), \
        (closed, rep["weights_largest_to_smallest"])
    print(f"\nclosed form w_j = g*beta^(j-1) with beta={beta:.3f}: "
          f"{[round(c, 4) for c in closed]}  -- matches the recursion")

    # When densities sum to 1 the measure is additive: lambda = 0, plain weighted mean.
    rep = degeneracy_report(np.array([1 / 3, 1 / 3, 1 / 3]))
    assert abs(rep["lambda"]) < 1e-9
    assert np.allclose(rep["weights_largest_to_smallest"], 1 / 3)
    print("densities summing to 1 -> lambda 0 -> equal weights (a plain average)")
    print("self-test passed")
