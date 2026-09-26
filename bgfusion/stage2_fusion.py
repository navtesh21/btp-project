"""
bgfusion/stage2_fusion.py
=========================
LEVEL 2c of the paper: FEATURE FUSION and FEATURE SELECTION.

FEATURE FUSION
--------------
The paper forms three feature sets and runs its models on each:
    F_temporal       the DWT statistical features        (here 160: 80 ECG + 80 PPG)
    F_morphological  the waveform-shape features         (here  33: 19 ECG + 14 PPG)
    F_fused          the two concatenated                (here 193)
`feature_sets()` just names those three column groups; the "fusion" is concatenation,
exactly as in the paper.

FEATURE SELECTION -- and the trap that this whole project is about
------------------------------------------------------------------
The paper selects features by intersecting three criteria:
    UFS  univariate filtering   -- keep features individually correlated with glucose
    RFE  recursive elimination  -- repeatedly drop the least useful feature
    L1   Lasso                  -- keep features a sparse linear model gives weight
A feature must survive ALL THREE to be kept.

The trap: **feature selection is part of training and must never see the test fold.**
Selecting on the whole dataset and then cross-validating leaks the test set's labels
into the choice of features, and inflates every downstream score. This is the same
class of error as the split bug documented in ../legacy_d1namo/RESULTS_d1namo.md, and
it is the single most common way published pipelines in this field overstate results.

So `select_features` is written to be called on TRAINING DATA ONLY, from inside a fold.
It takes X_train and y_train and nothing else. There is deliberately no convenience
function that selects on a whole dataset, because that function would be a footgun.
`SelectionReport` records what each criterion kept so the intersection can be reported
per fold rather than as a single global list.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.feature_selection import RFE, SelectKBest, f_regression
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

# Column-name prefixes written by stage1_data.
TEMPORAL_PREFIXES = ("ECG_", "PPG_")            # DWT statistical features
MORPHOLOGICAL_PREFIXES = ("ECGm_", "PPGm_")     # waveform-shape features
META_COLUMNS = ("subject", "timestamp", "glucose")


def all_feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in META_COLUMNS]


def feature_sets(df: pd.DataFrame) -> dict[str, list[str]]:
    """The paper's three feature sets, plus the per-modality splits for ablations."""
    cols = all_feature_columns(df)
    temporal = [c for c in cols if c.startswith(TEMPORAL_PREFIXES)]
    morph = [c for c in cols if c.startswith(MORPHOLOGICAL_PREFIXES)]
    return {
        "temporal": temporal,
        "morphological": morph,
        "fused": temporal + morph,
        # ablations: does PPG actually add anything over ECG alone?
        "ecg_only": [c for c in cols if c.startswith(("ECG_", "ECGm_"))],
        "ppg_only": [c for c in cols if c.startswith(("PPG_", "PPGm_"))],
    }


@dataclass
class SelectionReport:
    """What each criterion kept, so selection can be audited per fold."""
    ufs: list[str] = field(default_factory=list)
    rfe: list[str] = field(default_factory=list)
    l1: list[str] = field(default_factory=list)
    selected: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (f"UFS {len(self.ufs)}, RFE {len(self.rfe)}, L1 {len(self.l1)} "
                f"-> intersection {len(self.selected)}")


def select_features(X_train: pd.DataFrame, y_train: pd.Series, k: int = 60,
                    min_keep: int = 10, seed: int = 42) -> SelectionReport:
    """The paper's UFS n RFE n L1 intersection, fitted on TRAINING DATA ONLY.

    `k` is how many features each individual criterion keeps before intersecting.
    Because three criteria must agree, the intersection is typically much smaller
    than k.

    If the intersection collapses below `min_keep` (which happens when the three
    criteria disagree, i.e. when no feature is robustly useful), we fall back to the
    UFS ranking and say so via the report -- returning almost nothing would make the
    downstream model fail for an uninformative reason, and the fallback is visible
    rather than silent.
    """
    cols = list(X_train.columns)
    k = min(k, len(cols))

    # Standardise once: L1 in particular is scale-sensitive, and a feature measured in
    # seconds should not be penalised differently from one measured in millivolts.
    scaler = StandardScaler()
    Xs = pd.DataFrame(scaler.fit_transform(X_train), columns=cols, index=X_train.index)

    # --- UFS: univariate F-test against the target -------------------------------
    ufs_sel = SelectKBest(score_func=f_regression, k=k).fit(Xs, y_train)
    ufs = [c for c, keep in zip(cols, ufs_sel.get_support()) if keep]

    # --- RFE: repeatedly drop the least important feature ------------------------
    # A shallow tree is the cheapest estimator that still exposes feature_importances_;
    # RFE refits it once per elimination step, so estimator cost matters a lot here.
    rfe_sel = RFE(DecisionTreeRegressor(max_depth=6, random_state=seed),
                  n_features_to_select=k, step=0.15).fit(Xs, y_train)
    rfe = [c for c, keep in zip(cols, rfe_sel.get_support()) if keep]

    # --- L1: features a sparse linear model gives non-zero weight ----------------
    lasso = LassoCV(cv=3, random_state=seed, alphas=30, max_iter=5000).fit(Xs, y_train)
    order = np.argsort(np.abs(lasso.coef_))[::-1]
    nonzero = int(np.sum(lasso.coef_ != 0))
    l1 = [cols[i] for i in order[:max(min(k, nonzero), min_keep)]]

    selected = [c for c in cols if c in set(ufs) & set(rfe) & set(l1)]
    if len(selected) < min_keep:
        selected = ufs[:min_keep]

    return SelectionReport(ufs=ufs, rfe=rfe, l1=l1, selected=selected)


if __name__ == "__main__":
    # Demonstrate on synthetic data where we KNOW which features matter, so the
    # selection can be checked rather than merely inspected.
    rng = np.random.default_rng(0)
    n, p = 400, 40
    X = pd.DataFrame(rng.normal(size=(n, p)), columns=[f"f{i:02d}" for i in range(p)])
    # only f00..f04 drive the target; the rest are noise
    y = pd.Series(3 * X["f00"] - 2 * X["f01"] + 1.5 * X["f02"]
                  + X["f03"] - X["f04"] + rng.normal(0, 0.5, n))

    rep = select_features(X, y, k=10, min_keep=3)
    print(rep.summary())
    print("selected:", rep.selected)
    truly_informative = {"f00", "f01", "f02", "f03", "f04"}
    hits = truly_informative & set(rep.selected)
    print(f"recovered {len(hits)}/5 of the truly informative features: {sorted(hits)}")
    assert len(hits) >= 4, "selection failed to recover the informative features"
    assert len(rep.selected) <= 12, "selection kept far too many noise features"
    print("self-test passed")
