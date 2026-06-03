"""
src/main.py
===========
Run the complete Image #1 pipeline end-to-end and print a results table.

Pipeline:
    synthetic features  ->  train RF / GB / Bagging  ->  Choquet fusion  ->  BG output
                                                                  |
                              compare against best-single / plain-avg / weighted-avg

NOTE ON DATA: right now this uses the SYNTHETIC scaffolding from src/data.py so we can
verify the machinery. Once the real D1NAMO features are built (the "go backwards" step),
we swap the two lines marked `# <-- DATA SOURCE` and nothing else changes.

Run it:   python -m src.main
"""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import train_test_split

from src.data import make_bg_dataset          # <-- DATA SOURCE (synthetic for now)
from src.fusion import ChoquetMultiModelFusion
from src.metrics import mard, rmse


def main(seed: int = 42) -> None:
    # 1. Get the data. ----------------------------------------------------------------
    X, y = make_bg_dataset(seed=seed)          # <-- DATA SOURCE (swap for real later)

    # 2. Split into train (learn from) and test (graded on, never seen during training).
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed
    )
    print(f"Training rows: {len(X_train)}   Test rows: {len(X_test)}   Features: {X.shape[1]}\n")

    # 3. Train the three models and build the Choquet fusion. -------------------------
    fusion = ChoquetMultiModelFusion(seed=seed).fit(X_train, y_train)

    # Show the densities (per-model competence) and the solved lambda.
    print("Per-model density (cross-validated competence, 0..1):")
    for name, d in zip(fusion.model_names_, fusion.densities_):
        print(f"   {name:>16s} : {d:.3f}")
    print(f"   sum of densities : {fusion.densities_.sum():.3f}")
    print(f"   solved lambda    : {fusion.fuser_.lam:.4f}   "
          f"({'redundancy-penalty (<0)' if fusion.fuser_.lam < 0 else 'synergy-bonus (>0)'})\n")

    # 4. Predict on the test set with every method and grade them. --------------------
    all_preds = fusion.predict_all(X_test)

    print(f"{'METHOD':>16s} | {'RMSE (mmol/L)':>13s} | {'MARD (%)':>9s}")
    print("-" * 46)
    # Order: the 3 base models, then the 3 ways of combining them.
    order = fusion.model_names_ + ["PlainAverage", "WeightedAverage", "Choquet"]
    results = {}
    for name in order:
        preds = all_preds[name]
        r = rmse(y_test, preds)
        m = mard(y_test, preds)
        results[name] = r
        star = "  <-- Image #1 output" if name == "Choquet" else ""
        print(f"{name:>16s} | {r:13.3f} | {m:9.2f}{star}")

    # 5. A one-line verdict. ----------------------------------------------------------
    best_single = min(fusion.model_names_, key=lambda n: results[n])
    print("\nVerdict:")
    print(f"   best single model : {best_single}  (RMSE {results[best_single]:.3f})")
    print(f"   Choquet fusion    : RMSE {results['Choquet']:.3f}")
    if results["Choquet"] <= results[best_single]:
        gain = results[best_single] - results["Choquet"]
        print(f"   --> Choquet fusion improved RMSE by {gain:.3f} mmol/L over the best single model.")
    else:
        print("   --> Choquet did not beat the best single model on this split "
              "(can happen on easy/synthetic data; the real test is on D1NAMO).")


if __name__ == "__main__":
    main()
