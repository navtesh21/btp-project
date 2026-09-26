"""
src/base_models.py
==================
The THREE base models from Image #1: Random Forest, Gradient Boosting, and Bagging.

These three are the left-hand boxes in the diagram. Each one is trained on the features
and produces its own blood-glucose prediction. Later, the Choquet integral (chapter 9)
will FUSE these three predictions into one.

All three are "ensembles" -- a model made of many small models (here, many decision
TREES) combined. A single decision tree is just a flowchart of yes/no questions on the
features that ends in a predicted number. One tree alone is weak and easily fooled by
noise; combining hundreds of them is strong. The three ensembles differ in *how* they
combine their trees:

  * Bagging        : train many trees on random RESAMPLES of the data, then AVERAGE them.
                     (Reduces variance -- stops the model over-reacting to noise.)
  * Random Forest  : like Bagging, but each tree also only looks at a random SUBSET of
                     features at each split. This makes the trees more different from each
                     other, which makes the average even more robust.
  * Gradient Boost : train trees ONE AT A TIME, where each new tree focuses on fixing the
                     mistakes the previous trees made. (Reduces bias -- chases accuracy.)

Bagging & Random Forest build trees in PARALLEL and vote; Gradient Boosting builds them
SEQUENTIALLY, each correcting the last. Using all three and fusing them is exactly the
paper's bet: their different strengths cover each other's weaknesses.
"""

from __future__ import annotations

from sklearn.ensemble import (
    BaggingRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)

# We say "Regressor" (not "Classifier") because blood glucose is a NUMBER to predict,
# not a category. Predicting a number = "regression".


def build_models(seed: int = 42) -> dict[str, object]:
    """Create the three (untrained) base models with sensible default settings.

    Returns a dict mapping a human name -> a fresh scikit-learn model object.
    They are NOT trained yet; training happens later in fusion.py.

    `random_state=seed` again makes results reproducible (these models use randomness
    internally -- e.g. which data rows / features each tree sees).
    """
    models = {
        # ---- Random Forest -------------------------------------------------------
        # n_estimators = how many trees. More trees = steadier, but slower. 200 is a
        #   solid default.
        # max_depth = how many yes/no questions deep each tree may go. Limiting depth
        #   stops a tree from memorising noise (called "overfitting").
        # n_jobs=-1 = use all CPU cores to train trees in parallel (faster).
        "RandomForest": RandomForestRegressor(
            n_estimators=200,
            max_depth=None,      # None = grow until leaves are pure; the forest average
            #                      tames the overfitting this would cause in a single tree
            random_state=seed,
            n_jobs=-1,
        ),
        # ---- Gradient Boosting ---------------------------------------------------
        # learning_rate = how big a correction each new tree is allowed to make. Smaller
        #   = more careful, usually more accurate, but needs more trees.
        # max_depth=3 = boosting prefers many SHALLOW trees ("weak learners") because each
        #   only needs to fix a little of the leftover error.
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=3,
            random_state=seed,
        ),
        # ---- Bagging -------------------------------------------------------------
        # By default each "estimator" inside is a full decision tree. Bagging trains each
        # on a random resample (with replacement) of the rows, then averages them.
        "Bagging": BaggingRegressor(
            n_estimators=200,
            random_state=seed,
            n_jobs=-1,
        ),
    }
    return models
