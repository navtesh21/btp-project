"""
train.py  (project root)
========================
"Deployment, step 1": train the model ONCE and SAVE it to a file, so the app (or anyone)
can load it later and predict in milliseconds -- no retraining, no GPU.

What it does:
  1. Load the cached REAL D1NAMO features (built by src/d1namo.py).
  2. Hold out 20% to get an HONEST quality number (RMSE/MARD on data not trained on).
  3. Retrain on ALL the data for the final deployed model (more data = better model).
  4. Save everything the app needs into  bg_model.pkl  (the model + feature names + metrics).

Run it (after the feature cache exists):   python train.py
Output:                                     bg_model.pkl
"""

from __future__ import annotations

import joblib
from sklearn.model_selection import train_test_split

from src.d1namo import build_dataset
from src.fusion import ChoquetMultiModelFusion
from src.metrics import mard, rmse

MODEL_PATH = "bg_model.pkl"


def main() -> None:
    # 1. Load the real features (cached). If this errors, run `python -m src.d1namo` first
    #    (or wait for the full extraction to finish) to create the cache.
    X, y, groups = build_dataset(use_cache=True)
    print(f"Loaded {X.shape[0]} windows x {X.shape[1]} features "
          f"from {groups.nunique()} patients.")

    # 2. Honest quality check: train on 80%, measure on the unseen 20%.
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    holdout_model = ChoquetMultiModelFusion(seed=42).fit(X_tr, y_tr)
    preds = holdout_model.predict(X_te)
    metrics = {"rmse": rmse(y_te, preds), "mard": mard(y_te, preds)}
    print(f"Hold-out quality:  RMSE = {metrics['rmse']:.3f} mmol/L   "
          f"MARD = {metrics['mard']:.2f} %")

    # 3. Final model: retrain on EVERYTHING (we want the deployed model to use all data).
    final_model = ChoquetMultiModelFusion(seed=42).fit(X, y)

    # 4. Bundle everything the app needs and save to one file.
    bundle = {
        "model": final_model,                       # the trained fusion (RF+GB+Bagging+Choquet)
        "feature_names": list(X.columns),           # the 80 column names, in order
        "metrics": metrics,                         # honest hold-out RMSE/MARD
        "glucose_min": float(y.min()),
        "glucose_max": float(y.max()),
        "n_samples": int(X.shape[0]),
        "n_patients": int(groups.nunique()),
        "densities": final_model.densities_.tolist(),
        "lambda": float(final_model.fuser_.lam),
    }
    joblib.dump(bundle, MODEL_PATH)
    print(f"\nSaved trained model to {MODEL_PATH}")
    print("You can now run the demo app:   streamlit run app.py")


if __name__ == "__main__":
    main()
