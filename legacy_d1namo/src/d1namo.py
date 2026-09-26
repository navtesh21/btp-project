"""
src/d1namo.py
=============
Turn the RAW D1NAMO recordings into the (X, y) tables our models need -- i.e. the paper's
Level 1 (signal cleaning) + Level 2 (temporal feature extraction), on real data.

For each blood-glucose reading at time t, we:
  1. find the ECG recorded in the WINDOW just before t,
  2. clean it (band-pass filter 0.5-40 Hz -- the paper's Level-1 preprocessing),
  3. extract the paper's 80 temporal statistical features (src/features_temporal.py),
  4. pair those features with the glucose value (the target y) and remember which patient
     it came from (so we can later split train/test BY PATIENT and avoid cheating).

The result is cached to a CSV so the slow extraction runs only once.

DATA LAYOUT (discovered by inspecting the download):
  ECG :  data/d1namo/diabetes_subset_ecg_data/<subj>/sensor_data/<session>/<session>_ECG.csv
         columns: Time ("dd/mm/YYYY HH:MM:SS.fff"), EcgWaveform (integer)   @ 250 Hz
  GLU :  data/d1namo/diabetes_subset_pictures-glucose-food-insulin/<subj>/glucose.csv
         columns: date ("YYYY-MM-DD"), time ("HH:MM:SS"), glucose (mmol/L), type, comments
"""

from __future__ import annotations

import glob
import os
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

from src.features_temporal import extract_temporal_features

# ---- fixed facts about the dataset ----------------------------------------------------
DATA_ROOT = os.path.join("data", "d1namo")
ECG_ROOT = os.path.join(DATA_ROOT, "diabetes_subset_ecg_data")
GLU_ROOT = os.path.join(DATA_ROOT, "diabetes_subset_pictures-glucose-food-insulin")
SUBJECTS = [f"{i:03d}" for i in range(1, 10)]      # '001'..'009'
FS = 250.0                                          # ECG sampling rate (Hz)

# Paper's Level-1 band-pass: high-pass 0.5 Hz (remove baseline wander) + low-pass 40 Hz
# (remove power-line/muscle noise). We realise it as one Butterworth band-pass.
_BP_B, _BP_A = butter(4, [0.5, 40.0], btype="band", fs=FS)

# Paper's window: 20 consecutive cardiac cycles ~= 16 s. At 250 Hz that's 4000 samples.
WINDOW_SEC = 16.0
WINDOW_SAMPLES = int(WINDOW_SEC * FS)


# ----------------------------------------------------------------------------------
# Glucose targets
# ----------------------------------------------------------------------------------
def load_glucose(subject: str) -> pd.DataFrame:
    """Read a subject's glucose.csv -> DataFrame with a real datetime and the value."""
    path = os.path.join(GLU_ROOT, subject, "glucose.csv")
    df = pd.read_csv(path)
    # Combine the separate date + time columns into one timestamp we can compare to ECG.
    df["timestamp"] = pd.to_datetime(df["date"] + " " + df["time"],
                                     format="%Y-%m-%d %H:%M:%S")
    df["glucose"] = pd.to_numeric(df["glucose"], errors="coerce")
    df = df.dropna(subset=["glucose"]).sort_values("timestamp").reset_index(drop=True)
    return df[["timestamp", "glucose", "type"]]


# ----------------------------------------------------------------------------------
# ECG sessions
# ----------------------------------------------------------------------------------
def ecg_session_files(subject: str) -> list[str]:
    """All ECG csv files for a subject (one per recording session/day)."""
    pattern = os.path.join(ECG_ROOT, subject, "sensor_data", "*", "*_ECG.csv")
    return sorted(glob.glob(pattern))


def _parse_ecg_time(s: str) -> datetime:
    """Parse an ECG timestamp like '01/10/2014 10:09:39.417' (day/month/year)."""
    return datetime.strptime(s.strip(), "%d/%m/%Y %H:%M:%S.%f")


def _read_last_data_line(path: str) -> str:
    """Read the final non-empty line of a (possibly huge) file without loading it all."""
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        chunk = min(8192, size)
        f.seek(size - chunk)
        tail = f.read().decode("utf-8", errors="ignore").strip().split("\n")
        return tail[-1]


def read_ecg_session(path: str) -> tuple[np.ndarray, datetime, float]:
    """Load one ECG session: return (filtered_signal, start_time, sample_period_seconds).

    We avoid parsing all ~11 million timestamps: the signal is uniformly sampled, so we
    read ONLY the first and last timestamps and infer the per-sample period from them.
    Then row i corresponds to  start_time + i * period.
    """
    # The waveform itself (just the one column, as floats).
    sig = pd.read_csv(path, usecols=["EcgWaveform"])["EcgWaveform"].to_numpy(dtype=float)
    n = len(sig)

    # First timestamp (row 2 of the file) and last timestamp (read the tail).
    first_line = pd.read_csv(path, nrows=1)
    start_time = _parse_ecg_time(str(first_line["Time"].iloc[0]))
    end_time = _parse_ecg_time(_read_last_data_line(path).split(",")[0])
    period = (end_time - start_time).total_seconds() / (n - 1)

    # Level-1 cleaning: zero-phase band-pass filter (filtfilt = forward+backward, no lag).
    sig = filtfilt(_BP_B, _BP_A, sig)
    return sig, start_time, period


# ----------------------------------------------------------------------------------
# Build the full (X, y, groups) dataset
# ----------------------------------------------------------------------------------
def build_dataset(
    subjects: list[str] | None = None,
    cache_path: str = os.path.join(DATA_ROOT, "features_temporal.csv"),
    use_cache: bool = True,
    max_windows_per_session: int | None = None,
    verbose: bool = True,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Extract features for every glucose reading that has ECG before it.

    Returns:
      X      : DataFrame of 80 temporal features per glucose reading
      y      : Series of glucose values (mmol/L)  -- the targets
      groups : Series of subject ids per row       -- for patient-wise cross-validation

    Set `max_windows_per_session` (e.g. 30) for a quick trial run; None = use everything.
    """
    subjects = subjects or SUBJECTS

    # Reuse a previous extraction if present (this step is slow).
    if use_cache and os.path.exists(cache_path):
        if verbose:
            print(f"Loading cached features from {cache_path}")
        # IMPORTANT: read `subject` as a string. Otherwise pandas parses "001" as the
        # integer 1 and we lose the leading zeros, which made the cache-match below fail
        # and silently triggered a full ~90-min re-extraction. zfill(3) re-pads just in case.
        cached = pd.read_csv(cache_path, dtype={"subject": str})
        cached["subject"] = cached["subject"].str.zfill(3)
        if set(cached["subject"].unique()) >= set(subjects):
            cached = cached[cached["subject"].astype(str).isin(subjects)]
            y = cached["glucose"]
            groups = cached["subject"].astype(str)
            X = cached.drop(columns=["glucose", "subject", "timestamp"], errors="ignore")
            return X, y, groups

    rows: list[dict] = []
    for subject in subjects:
        glucose = load_glucose(subject)
        sessions = ecg_session_files(subject)
        if verbose:
            print(f"[{subject}] {len(glucose)} glucose readings, {len(sessions)} ECG sessions")

        for sess_path in sessions:
            sig, start_time, period = read_ecg_session(sess_path)
            n = len(sig)
            sess_end = start_time.timestamp() + n * period

            made = 0
            for _, g in glucose.iterrows():
                t = g["timestamp"].to_pydatetime().timestamp()
                # Is this glucose reading inside this session's time span?
                if not (start_time.timestamp() <= t <= sess_end):
                    continue
                end_idx = int(round((t - start_time.timestamp()) / period))
                start_idx = end_idx - WINDOW_SAMPLES
                if start_idx < 0 or end_idx > n:        # not enough ECG before the reading
                    continue

                window = sig[start_idx:end_idx]
                feats = extract_temporal_features(window, FS)
                feats["glucose"] = float(g["glucose"])
                feats["subject"] = subject
                feats["timestamp"] = g["timestamp"]
                rows.append(feats)

                made += 1
                if max_windows_per_session and made >= max_windows_per_session:
                    break
            if verbose:
                print(f"    {os.path.basename(sess_path)}: +{made} windows "
                      f"(running total {len(rows)})")

    if not rows:
        raise RuntimeError("No (ECG-window, glucose) pairs were built. Check data paths.")

    full = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    full.to_csv(cache_path, index=False)
    if verbose:
        print(f"\nSaved {len(full)} samples x {full.shape[1]} cols to {cache_path}")

    y = full["glucose"]
    groups = full["subject"].astype(str)
    X = full.drop(columns=["glucose", "subject", "timestamp"])
    return X, y, groups


if __name__ == "__main__":
    # QUICK TRIAL: just subject 001, a handful of windows per session, no cache -- to prove
    # the whole real pipeline runs end to end before we commit to the long full build.
    X, y, groups = build_dataset(
        subjects=["001"],
        use_cache=False,
        cache_path=os.path.join(DATA_ROOT, "_trial_features.csv"),
        max_windows_per_session=5,
    )
    print("\nTRIAL RESULT")
    print("X shape:", X.shape, "| y shape:", y.shape)
    print("glucose range: %.1f - %.1f mmol/L" % (y.min(), y.max()))
    print("first few feature columns:", list(X.columns[:6]))
