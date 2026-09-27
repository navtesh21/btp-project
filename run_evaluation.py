"""
run_evaluation.py
=================
Run the leakage-controlled evaluation over the PhysioCGM feature table.

WHAT IT PRODUCES
----------------
For each (feature set, protocol) configuration:
    results/preds_<featureset>_<protocol>.csv    every out-of-fold prediction
    results/diag_<featureset>_<protocol>.csv     per-fold selection + degeneracy report
    results/summary_<featureset>_<protocol>.csv  every method graded

ORDER MATTERS
-------------
Configurations run in priority order and each is checkpointed as it finishes, so partial
results are usable and a crash costs at most one configuration:

  1. fused x {random_window, subject_aware, loso}
        The headline. The same feature set under three progressively stricter splits is
        what demonstrates the leakage effect.
  2. {ecg_only, ppg_only, temporal, morphological} x loso
        The ablation. Does PPG actually add anything over ECG? This is the comparison
        the original paper could make and D1NAMO could not, because D1NAMO has no PPG.

Everything else (all five feature sets under all three protocols) is a superset of
these and can be run later; these seven answer the questions the paper asks.

Run:  python run_evaluation.py            (all seven, in order)
      python run_evaluation.py fused      (just the fused configurations)
"""

from __future__ import annotations

import os
import sys

# Thread pinning, exactly as in run_stage1.py: the models are fitted inside joblib
# workers and an unpinned BLAS oversubscribes the machine badly. Must precede numpy.
for _var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "2")

_SCRATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".joblib_tmp")
os.makedirs(_SCRATCH, exist_ok=True)
os.environ["JOBLIB_TEMP_FOLDER"] = _SCRATCH
os.environ["TMP"] = os.environ["TEMP"] = _SCRATCH

import time  # noqa: E402
import warnings  # noqa: E402

import joblib  # noqa: E402
import pandas as pd  # noqa: E402

from bgfusion.evaluate import choquet_vs_min, run_protocol, summarise  # noqa: E402
from bgfusion.stage1_data import build_dataset  # noqa: E402
from bgfusion.stage2_fusion import feature_sets  # noqa: E402

warnings.filterwarnings("ignore")

RESULTS = "results"

# (feature set, protocol) in priority order -- see the module docstring.
CONFIGS = [
    ("fused", "random_window"),
    ("fused", "subject_aware"),
    ("fused", "loso"),
    ("ecg_only", "loso"),
    ("ppg_only", "loso"),
    ("temporal", "loso"),
    ("morphological", "loso"),
]


# RandomForest and Bagging are built with n_jobs=-1, so each one spawns a worker per
# core (16 here) and holds a copy of the working set in every worker. On a 15.7 GB
# machine that is what got this run OS-killed for low memory partway through the
# ablations. Capping joblib globally bounds it without touching the model definitions,
# which must stay as the paper specifies them.
MODEL_N_JOBS = 6


def main() -> None:
    os.makedirs(RESULTS, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None

    df = build_dataset(cache=True, verbose=True)
    sets = feature_sets(df)
    print(f"\nfeature sets: " + ", ".join(f"{k}={len(v)}" for k, v in sets.items()))
    print(f"no-skill baseline RMSE (sd of glucose) = {df.glucose.std():.3f} mmol/L\n")

    for fs_name, protocol in CONFIGS:
        if only and fs_name != only:
            continue
        tag = f"{fs_name}_{protocol}"
        out = os.path.join(RESULTS, f"summary_{tag}.csv")
        if os.path.exists(out):
            print(f"[{tag}] already done, skipping", flush=True)
            continue

        print(f"\n{'='*72}\n[{tag}] {len(sets[fs_name])} features\n{'='*72}", flush=True)
        t0 = time.time()
        preds, diags = run_protocol(df, protocol, sets[fs_name], do_selection=True,
                                    n_splits=5, verbose=True)
        summary = summarise(preds)

        preds.to_csv(os.path.join(RESULTS, f"preds_{tag}.csv"), index=False)
        pd.DataFrame(diags).to_csv(os.path.join(RESULTS, f"diag_{tag}.csv"), index=False)
        # summary last: its presence is the "this config is complete" marker above.
        summary.to_csv(out, index=False)

        print(f"\n[{tag}] done in {(time.time()-t0)/60:.1f} min")
        print(summary.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
        cvm = choquet_vs_min(preds)
        if cvm:
            print(f"  Choquet vs min-operator: corr={cvm['corr_choquet_min']:.4f}, "
                  f"MAD={cvm['mad_choquet_min']:.4f} "
                  f"(vs MAD to the mean {cvm['mad_choquet_mean']:.4f})")

    print("\nALL REQUESTED CONFIGURATIONS COMPLETE")


if __name__ == "__main__":
    # Bound every joblib pool underneath this run, including the ones sklearn creates
    # inside RandomForest and Bagging.
    with joblib.parallel_config(n_jobs=MODEL_N_JOBS):
        main()
