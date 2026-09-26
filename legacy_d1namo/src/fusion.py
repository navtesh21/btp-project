"""
src/fusion.py
=============
The glue that assembles the WHOLE of Image #1:

      [RandomForest]        \\
      [GradientBoosting]     >--->  [Choquet integral fusion]  --->  BG output
      [Bagging]             /

This file:
  1. trains the three base models,
  2. measures how good each model is (its "density" for the Choquet integral),
  3. fuses their predictions with the Choquet integral,
  4. also computes simpler baselines (best single model, plain average, weighted average)
     so we can PROVE whether the Choquet fusion actually helped.

HOW WE CHOOSE THE DENSITIES (important!)
----------------------------------------
The Choquet integral needs one "density" per model = how competent that model is alone.
We must NOT measure competence on the test set (that would be cheating -- the test set is
sacred and only used at the very end). We also should not measure it on the training set
directly, because a strong model can almost MEMORISE the training set, making every model
look equally perfect.

The honest trick is CROSS-VALIDATION on the training data: we split the training data into
k parts, train on k-1 parts and predict the held-out part, rotate until every training row
has an "out-of-fold" prediction made by a model that did NOT see that row. The accuracy of
those out-of-fold predictions is a fair estimate of real-world competence, and it
DIFFERENTIATES the models (the genuinely better model gets a higher density). We use R^2,
the "fraction of variance explained" (1.0 = perfect, 0 = no better than guessing the mean).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold, cross_val_predict

from src.base_models import build_models
from src.choquet import ChoquetFuser


class ChoquetMultiModelFusion:
    """Train three models and fuse them with a Choquet integral (Image #1)."""

    def __init__(self, seed: int = 42, cv_folds: int = 5):
        self.seed = seed
        self.cv_folds = cv_folds
        self.models = build_models(seed)        # {name: untrained model}
        self.model_names_: list[str] = list(self.models.keys())
        self.densities_: np.ndarray | None = None
        self.fuser_: ChoquetFuser | None = None

    # ---- training --------------------------------------------------------------------
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "ChoquetMultiModelFusion":
        densities = []
        for name in self.model_names_:
            model = self.models[name]

            # (a) honest competence via cross-validation (used ONLY to set the density).
            #     cross_val_predict returns an out-of-fold prediction for every train row.
            #
            #     The inner splitter MUST shuffle. Passing an integer here (cv=3) makes
            #     scikit-learn use KFold WITHOUT shuffling, which takes three contiguous
            #     blocks of rows -- and our feature table arrives sorted by patient
            #     (001..009). Each "fold" was therefore a block of whole patients, so the
            #     density was silently measuring cross-PATIENT generalisation instead of
            #     the model's competence on the data it is actually being trained for.
            #     That scored R^2 ~ -0.16, every density clipped to the 0.01 floor, all
            #     three models looked identically useless, and the Choquet integral lost
            #     the competence ordering it exists to exploit. Shuffling gives
            #     R^2 ~ +0.11 and restores a real ordering between the models.
            splitter = KFold(n_splits=self.cv_folds, shuffle=True, random_state=self.seed)
            oof_pred = cross_val_predict(model, X_train, y_train, cv=splitter)
            competence = r2_score(y_train, oof_pred)          # in (-inf, 1]; ~0.4-0.7 typical
            # densities must live in (0, 1); clip away the extremes for numerical safety.
            densities.append(float(np.clip(competence, 0.01, 0.99)))

            # (b) now train the model on ALL the training data for real predictions later.
            model.fit(X_train, y_train)

        self.densities_ = np.array(densities)
        # Build the Choquet fuser from these densities (it solves lambda internally).
        self.fuser_ = ChoquetFuser(self.densities_, self.model_names_)
        return self

    # ---- helpers ---------------------------------------------------------------------
    def _stack_predictions(self, X: pd.DataFrame) -> np.ndarray:
        """Return a (n_samples, n_models) array: column i = model i's predictions."""
        cols = [self.models[name].predict(X) for name in self.model_names_]
        return np.column_stack(cols)

    # ---- prediction ------------------------------------------------------------------
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """The Image #1 output: Choquet-fused blood-glucose predictions."""
        assert self.fuser_ is not None, "Call .fit() before .predict()."
        return self.fuser_.fuse(self._stack_predictions(X))

    def predict_all(self, X: pd.DataFrame) -> dict[str, np.ndarray]:
        """Return EVERY prediction we can make, for comparison.

        Keys: each model name, plus 'PlainAverage', 'WeightedAverage', and 'Choquet'.
        This lets main.py show whether Choquet beats the simpler ways of combining.
        """
        assert self.fuser_ is not None and self.densities_ is not None
        preds = self._stack_predictions(X)

        out: dict[str, np.ndarray] = {
            name: preds[:, i] for i, name in enumerate(self.model_names_)
        }
        # Baseline 1: plain average -- treats all models as equal and independent.
        out["PlainAverage"] = preds.mean(axis=1)
        # Baseline 2: weighted average -- importance per model, but NO teamwork modelling.
        weights = self.densities_ / self.densities_.sum()
        out["WeightedAverage"] = preds @ weights
        # The star of the show: Choquet integral fusion.
        out["Choquet"] = self.fuser_.fuse(preds)
        return out
