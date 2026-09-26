"""
run_stage1.py
=============
Runner for the Level-1/Level-2 feature extraction.

This exists as a separate script, rather than as `python -m bgfusion.stage1_data`,
because two things MUST be configured before numpy is imported anywhere, and a module
cannot do that for its own importer.

1. THREAD PINNING -- the single biggest win.
   numpy/scipy link against a threaded BLAS which, by default, spawns one thread per
   core. Inside joblib that means every worker starts its own full-size thread pool:
   8 workers x 16 threads = 128 threads contending for 16 cores. The arrays here are
   small (4000 samples), so the threading overhead dwarfs the arithmetic and the whole
   run goes SLOWER than single-threaded. Measured on this machine:

       one window, BLAS unpinned : 5.16 s
       one window, 1 thread      : 1.22 s      (4.2x faster)

   Each worker gets one thread; parallelism comes from joblib, not from BLAS.

2. SCRATCH ON THE BIG DISK.
   joblib memory-maps large arrays through a temp directory, which defaults to
   %LOCALAPPDATA%\\Temp on C:. On this machine C: is ~90% full while D: has plenty of
   room, and a full scratch disk is what turns memory pressure into thrashing. We point
   joblib at a scratch folder next to the data instead.

Run:  python run_stage1.py            (all subjects with a checkpoint each)
      python run_stage1.py c1s02 c1s03
"""

from __future__ import annotations

import os
import sys

# --- must happen BEFORE numpy/scipy/joblib are imported ---------------------------
for _var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_var] = "1"

# Keep ALL scratch on the project's drive. C: on this machine is ~90% full (23 GB free)
# while D: has ~210 GB, and Python's temp dir, joblib's memmap folder and anything a
# library writes via tempfile all default to %LOCALAPPDATA%\Temp on C:. A full scratch
# disk is what turns ordinary memory pressure into thrashing, so point every one of
# them at the data drive.
#
# Note this does NOT add RAM: the out-of-memory kills were physical-memory pressure on
# a 15.7 GB machine, and the fixes for that are elsewhere (streaming one ECG session at
# a time, not parsing the Time column, and a smaller worker pool). This only guarantees
# that nothing spills onto the full disk.
_SCRATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".joblib_tmp")
os.makedirs(_SCRATCH, exist_ok=True)
os.environ["JOBLIB_TEMP_FOLDER"] = _SCRATCH
os.environ["TMP"] = _SCRATCH
os.environ["TEMP"] = _SCRATCH
os.environ["TMPDIR"] = _SCRATCH

import time  # noqa: E402

from bgfusion.stage1_data import build_dataset  # noqa: E402

# Worker count has been tuned down twice, for two different reasons:
#   8 -> 6  memory. Each worker carries its own numpy/scipy/nolds import (~150 MB), so
#           the pool is the dominant consumer on a 15.7 GB machine; 8 got the run
#           OS-killed twice.
#   6 -> 4  heat. Sustained 100% CPU across six workers left the laptop very hot, and
#           throughput degraded steadily across consecutive subjects (3.5 -> 4.7 -> 5.9
#           minutes per ECG GB), which is the signature of thermal throttling. A
#           throttled core does not deliver its nominal speed, so fewer workers can
#           finish in comparable wall time while running cooler.
N_JOBS = 4


def main() -> None:
    subjects = sys.argv[1:] or None
    print(f"threads pinned to 1 per worker | joblib scratch: {_SCRATCH}")
    print(f"n_jobs = {N_JOBS}\n", flush=True)

    t0 = time.time()
    df = build_dataset(subjects, cache=True, verbose=True, n_jobs=N_JOBS)
    mins = (time.time() - t0) / 60

    print(f"\nDONE in {mins:.0f} min   shape = {df.shape}")
    if len(df):
        print(df.groupby("subject").size().to_string())
        print(f"glucose {df.glucose.min():.1f} - {df.glucose.max():.1f} mmol/L")


if __name__ == "__main__":
    main()
