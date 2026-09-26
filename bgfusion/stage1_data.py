"""
src/physiocgm.py
================
Turn the raw PhysioCGM recordings into the (X, y) tables our models need -- the same job
src/d1namo.py does, but for a dataset that has BOTH ECG and PPG.

WHY THIS DATASET
----------------
D1NAMO gave us ECG only, so we could reproduce just the ECG half of the paper's feature
set (80 of its 160 temporal features). PhysioCGM carries ECG *and* PPG against a CGM
reference, so the paper's full Level-1/Level-2 design becomes reproducible:

    80 ECG temporal features  +  80 PPG temporal features  =  160

Reference:
  "PhysioCGM: a multimodal physiological dataset for non-invasive blood glucose
  estimation", Scientific Data (2025). Data: figshare record 28136294 (CC0).
  10 participants with Type 1 diabetes, ids c1s01..c1s05 and c2s01..c2s05.

DATA LAYOUT (inside each <subject>_raw.zip)
-------------------------------------------
  cgm.csv
      A Dexcom export. Many row types; the glucose readings are the rows whose
      'Event Type' is 'EGV'. Value column is 'Glucose Value (mg/dL)'  <-- mg/dL!
  zephyr/<session>/Record N_<stamp>_ECG.csv
      columns: Time ("dd/mm/YYYY HH:MM:SS.fff"), EcgWaveform (int)  @ 250 Hz
      -- byte-for-byte the same shape as D1NAMO's ECG, so the same parsing works.
  e4/<session>/BVP.csv
      Empatica E4 format: line 1 = start time as a UNIX epoch, line 2 = sample rate
      (64.0), then one sample per line. BVP ("blood volume pulse") IS the PPG signal.

TWO TRAPS THIS MODULE HANDLES
-----------------------------
1. UNITS. PhysioCGM's CGM is in mg/dL; D1NAMO and the paper are in mmol/L. We convert
   on load (divide by 18.018) so every downstream metric, and the Parkes error grid,
   keeps working unchanged.

2. CLOCKS. The two recorders do NOT share a clock:
       * Zephyr writes LOCAL wall-clock time strings.
       * The Empatica E4 writes a UNIX epoch, i.e. UTC.
   For the June-2022 Texas recordings the difference is 5 hours (CDT = UTC-5). Pairing
   the two without correcting this silently attaches every PPG window to glucose from
   five hours earlier -- the features still compute, the models still train, and the
   results are quietly meaningless. So we do not hardcode the offset: `detect_utc_offset`
   RECOVERS it per subject by testing which whole-hour shift makes the E4 session starts
   line up with the Zephyr session starts, and we assert that the winner is unambiguous.
"""

from __future__ import annotations

import datetime as dt
import io
import os
import re
import zipfile
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.signal import butter, filtfilt

from bgfusion.features_temporal import extract_temporal_features
from bgfusion.stage2_morphological import (
    ecg_morphological_features,
    ppg_morphological_features,
)

DATA_ROOT = os.path.join("data", "physiocgm")
SUBJECTS = [f"c{c}s{s:02d}" for c in (1, 2) for s in range(1, 6)]

MGDL_PER_MMOL = 18.018          # same constant the error grid uses

ECG_FS = 250.0                  # Zephyr Bioharness
PPG_FS = 64.0                   # Empatica E4 BVP

# The paper's window: 20 consecutive cardiac cycles, about 16 s.
WINDOW_SEC = 16.0
ECG_WINDOW = int(WINDOW_SEC * ECG_FS)       # 4000 samples
PPG_WINDOW = int(WINDOW_SEC * PPG_FS)       # 1024 samples

# How many windows to hold in flight during parallel feature extraction. Each
# window is ~40 KB of raw signal and joblib pickles the whole batch out to the
# workers, so this directly bounds peak memory.
CHUNK = 400

# Paper's Level-1 band-pass for ECG: 0.5-40 Hz.
_ECG_B, _ECG_A = butter(4, [0.5, 40.0], btype="band", fs=ECG_FS)
# PPG carries its information much lower down (pulse rate ~1-3 Hz plus harmonics), and
# 64 Hz sampling puts Nyquist at 32 Hz, so a 0.5-40 Hz band is not even representable.
# 0.5-8 Hz is the standard PPG band: it keeps the pulse and its first few harmonics
# while removing baseline wander below and high-frequency noise above.
_PPG_B, _PPG_A = butter(4, [0.5, 8.0], btype="band", fs=PPG_FS)


def _zip_path(subject: str) -> str:
    return os.path.join(DATA_ROOT, f"{subject}_raw.zip")


# ----------------------------------------------------------------------------------
# Clock alignment
# ----------------------------------------------------------------------------------
def _e4_session_starts(z: zipfile.ZipFile) -> list[float]:
    """UNIX epoch start time of every E4 session (read from each BVP.csv's first line)."""
    starts = []
    for name in sorted({n for n in z.namelist() if n.endswith("BVP.csv")}):
        with z.open(name) as f:
            try:
                starts.append(float(f.readline().decode().strip()))
            except ValueError:
                continue
    return starts


def _zephyr_session_starts(z: zipfile.ZipFile) -> list[dt.datetime]:
    """Local start time of every Zephyr session, parsed from its folder name."""
    out = []
    for folder in sorted({n.split("/")[1] for n in z.namelist()
                          if n.startswith("zephyr/") and n.count("/") >= 2 and n.split("/")[1]}):
        m = re.match(r"(\d{4})_(\d{2})_(\d{2})-(\d{2})_(\d{2})_(\d{2})", folder)
        if m:
            out.append(dt.datetime(*map(int, m.groups())))
    return out


# Candidate recording time zones, tried in order of prior plausibility. PhysioCGM was
# collected at Texas A&M, so America/Chicago is expected; the others are here so the
# detector can prove that rather than assume it.
CANDIDATE_TIMEZONES = ("America/Chicago", "America/New_York", "America/Denver",
                       "America/Los_Angeles", "UTC")

# Absolute floor on matched session pairs, so a subject with almost no overlap between
# the two recorders cannot pick a zone on one or two coincidences.
MIN_TZ_MATCHES = 5


def _to_local(unix_ts: float, tz: ZoneInfo) -> dt.datetime:
    """UNIX epoch (UTC) -> naive local wall-clock time in `tz`, DST-aware."""
    return (dt.datetime.fromtimestamp(unix_ts, tz=dt.timezone.utc)
            .astimezone(tz).replace(tzinfo=None))


def detect_timezone(z: zipfile.ZipFile, tolerance_s: int = 1200) -> ZoneInfo:
    """Recover the TIME ZONE that maps E4 UTC timestamps onto Zephyr local wall time.

    WHY A ZONE AND NOT A FIXED OFFSET
    ---------------------------------
    An earlier version searched for a single whole-hour offset. That is wrong for any
    recording spanning a daylight-saving transition. Subject c2s04 runs 2022-10-27 to
    2022-11-17 and US DST ended on 2022-11-06, so 7 of its sessions are CDT (UTC-5)
    and 15 are CST (UTC-6). No constant offset fits: the fixed-offset detector scored
    UTC-6 at 9 sessions and UTC-5 at 6, and correctly refused to guess rather than
    silently misalign a third of the subject's data by an hour.

    A time zone handles this because the offset is a function of the instant, so the
    transition is applied automatically.

    Both recorders were started by hand at roughly the same moments, so the correct
    zone is the one under which E4 session starts cluster around Zephyr session starts.
    We score every candidate and require a decisive winner.
    """
    e4 = _e4_session_starts(z)
    zeph = _zephyr_session_starts(z)
    if not e4 or not zeph:
        raise ValueError("cannot detect timezone: missing E4 or Zephyr sessions")

    scores: dict[str, int] = {}
    for name in CANDIDATE_TIMEZONES:
        tz = ZoneInfo(name)
        scores[name] = sum(
            any(abs((_to_local(t0, tz) - t).total_seconds()) < tolerance_s for t in zeph)
            for t0 in e4)

    best = max(scores, key=scores.get)
    ranked = sorted(scores.values(), reverse=True)
    runner_up = ranked[1] if len(ranked) > 1 else 0

    # The test is the MARGIN over the next-best zone, not the absolute match count.
    # Requiring some fraction of E4 sessions to match would be wrong: the two devices
    # were worn independently, so plenty of E4 sessions have no Zephyr session started
    # near them and can never match under ANY zone. What identifies the zone is that
    # one candidate explains far more pairings than the others -- e.g. c1s02 scores
    # Chicago 10 against Denver 3, which is decisive even though 10 is well under half
    # of its 27 E4 sessions.
    #
    # A 2x margin still catches the case this guard exists for: a recording spanning a
    # DST transition splits its evidence between two adjacent offsets (c2s04 scored 9
    # and 6 under the old fixed-offset search), which fails 2x and is correctly
    # refused rather than silently misaligning half the subject by an hour.
    if ranked[0] < MIN_TZ_MATCHES or ranked[0] < 2 * max(runner_up, 1):
        raise ValueError(f"timezone is ambiguous (scores={scores}); refusing to guess")
    return ZoneInfo(best)


# ----------------------------------------------------------------------------------
# Loaders
# ----------------------------------------------------------------------------------
def load_cgm(z: zipfile.ZipFile) -> pd.DataFrame:
    """Glucose readings from the Dexcom export, converted to mmol/L.

    The export mixes alerts, device notes and readings in one file; the actual glucose
    values are the rows whose 'Event Type' is 'EGV' (estimated glucose value).
    """
    with z.open("cgm.csv") as f:
        raw = pd.read_csv(io.BytesIO(f.read()), low_memory=False)

    ts_col = [c for c in raw.columns if c.startswith("Timestamp")][0]
    gl_col = [c for c in raw.columns if c.startswith("Glucose Value")][0]

    df = raw[raw["Event Type"] == "EGV"][[ts_col, gl_col]].copy()
    df.columns = ["timestamp", "glucose_mgdl"]
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    # Dexcom writes "Low"/"High" instead of a number outside the sensor's range; those
    # rows carry no usable value, so drop them rather than invent a number.
    df["glucose_mgdl"] = pd.to_numeric(df["glucose_mgdl"], errors="coerce")
    df = df.dropna()
    df["glucose"] = df["glucose_mgdl"] / MGDL_PER_MMOL      # -> mmol/L
    return df[["timestamp", "glucose"]].sort_values("timestamp").reset_index(drop=True)


def load_ecg_session(z: zipfile.ZipFile, name: str) -> tuple[np.ndarray, dt.datetime]:
    """Read one Zephyr ECG csv -> (waveform, first-sample local time).

    Deliberately does NOT parse the Time column. A session file holds ~11 million rows,
    and letting pandas build that column costs 11 million Python strings -- of order a
    gigabyte -- when all we need from it is the FIRST timestamp; the rest is implied by
    the 250 Hz sample rate. Reading the first data line by hand and then loading only
    `EcgWaveform` as float32 cuts the peak from ~1 GB to ~45 MB per session, which is
    what stops this phase exhausting memory.
    """
    # First data line -> the session's start time.
    with z.open(name) as f:
        f.readline()                                   # header
        first = f.readline().decode("utf-8", "replace").strip()
    t0 = dt.datetime.strptime(first.split(",")[0], "%d/%m/%Y %H:%M:%S.%f")

    # Second pass for the waveform alone. The file object is streamed straight into
    # pandas rather than through an in-memory copy of the whole decompressed file.
    #
    # float64, NOT float32. An earlier version stored the waveform as float32 to halve
    # it (88 MB -> 44 MB) and that silently corrupted the correlation-dimension
    # features: CD is estimated from pairwise distances between delay-embedded points,
    # so float32 rounding perturbs the small distances and the log-log slope fit
    # amplifies it. Measured on one window, FE0_CD moved from 4.021 to 0.713 (-82%),
    # while every non-CD feature changed by under 0.001%. The memory problem was never
    # the waveform dtype -- it was parsing the Time column into 11 million strings.
    with z.open(name) as f:
        wave = pd.read_csv(f, usecols=["EcgWaveform"],
                           dtype={"EcgWaveform": "float64"})["EcgWaveform"].to_numpy()
    return wave, t0


def load_ppg_session(z: zipfile.ZipFile, name: str, tz: ZoneInfo
                     ) -> tuple[np.ndarray, dt.datetime]:
    """Read one Empatica BVP.csv -> (waveform, first-sample time in LOCAL clock).

    The E4 stamps its start as a UNIX epoch, i.e. UTC, while the Zephyr and the CGM
    both use local wall-clock time. Converting through a ZONE rather than a fixed
    offset is what makes this correct across a daylight-saving transition -- see
    detect_timezone.
    """
    with z.open(name) as f:
        lines = f.read().decode().splitlines()
    start_unix = float(lines[0].strip())
    # line 1 is the sample rate; we assert rather than trust it blindly
    fs = float(lines[1].strip())
    if abs(fs - PPG_FS) > 1e-6:
        raise ValueError(f"{name}: expected {PPG_FS} Hz BVP, found {fs}")
    values = np.array([float(v) for v in lines[2:] if v.strip()], dtype=float)
    return values, _to_local(start_unix, tz)


# ----------------------------------------------------------------------------------
# Window extraction
# ----------------------------------------------------------------------------------
def _window_before(signal: np.ndarray, sig_start: dt.datetime, fs: float,
                   target: pd.Timestamp, n_samples: int) -> np.ndarray | None:
    """The `n_samples` samples ending at `target`, or None if not fully covered."""
    offset_s = (target.to_pydatetime() - sig_start).total_seconds()
    end = int(round(offset_s * fs))
    start = end - n_samples
    if start < 0 or end > len(signal):
        return None
    return signal[start:end]


def _features_for_window(e_win: np.ndarray, p_win: np.ndarray) -> dict[str, float] | None:
    """All Level-2 features for one paired ECG+PPG window, or None if unusable.

    This is the expensive call (the nonlinear temporal features dominate), so it is
    written as a standalone top-level function: joblib can then ship it to worker
    processes, which is what makes the extraction parallel.
    """
    e_clean = filtfilt(_ECG_B, _ECG_A, e_win)
    p_clean = filtfilt(_PPG_B, _PPG_A, p_win)

    feats: dict[str, float] = {}
    # --- Level 2a: temporal statistical features (80 per modality) ----------------
    for prefix, sig, fs in (("ECG_", e_clean, ECG_FS), ("PPG_", p_clean, PPG_FS)):
        for k, v in extract_temporal_features(sig, fs).items():
            feats[prefix + k] = v
    # --- Level 2b: spatial morphological features ---------------------------------
    for k, v in ecg_morphological_features(e_clean, ECG_FS).items():
        feats["ECGm_" + k] = v
    for k, v in ppg_morphological_features(p_clean, PPG_FS).items():
        feats["PPGm_" + k] = v

    if any(not np.isfinite(v) for v in feats.values()):
        return None
    return feats


def collect_windows(subject: str, verbose: bool = True) -> tuple[list, list, list]:
    """Pass 1: pull out every paired ECG+PPG window. I/O bound, no feature maths.

    Returns (ecg_windows, ppg_windows, meta) where meta holds timestamp + glucose.
    Separating this from feature extraction is what lets pass 2 run in parallel.
    """
    path = _zip_path(subject)
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    e_wins, p_wins, meta = [], [], []
    with zipfile.ZipFile(path) as z:
        tz = detect_timezone(z)
        cgm = load_cgm(z)
        if verbose:
            print(f"[{subject}] timezone {tz.key}, {len(cgm)} CGM readings "
                  f"({cgm['glucose'].min():.1f}-{cgm['glucose'].max():.1f} mmol/L)",
                  flush=True)

        ppg_sessions = []
        for name in sorted({n for n in z.namelist() if n.endswith("BVP.csv")}):
            try:
                ppg_sessions.append(load_ppg_session(z, name, tz))
            except Exception as exc:                       # noqa: BLE001
                if verbose:
                    print(f"   skip PPG {name}: {exc}", flush=True)

        for ecg_name in sorted(n for n in z.namelist() if n.endswith("_ECG.csv")):
            try:
                ecg, ecg_t0 = load_ecg_session(z, ecg_name)
            except Exception as exc:                       # noqa: BLE001
                if verbose:
                    print(f"   skip ECG {ecg_name}: {exc}", flush=True)
                continue

            ecg_end = ecg_t0 + dt.timedelta(seconds=len(ecg) / ECG_FS)
            in_span = cgm[(cgm["timestamp"] >= ecg_t0) & (cgm["timestamp"] <= ecg_end)]
            kept = 0
            for _, r in in_span.iterrows():
                e_win = _window_before(ecg, ecg_t0, ECG_FS, r["timestamp"], ECG_WINDOW)
                if e_win is None:
                    continue
                p_win = None
                for ppg, ppg_t0 in ppg_sessions:
                    p_win = _window_before(ppg, ppg_t0, PPG_FS, r["timestamp"], PPG_WINDOW)
                    if p_win is not None:
                        break
                if p_win is None:
                    continue                                # need BOTH modalities
                # A flat/dead channel yields NaN features; reject it here.
                if np.ptp(e_win) < 1e-9 or np.ptp(p_win) < 1e-9:
                    continue
                e_wins.append(e_win)
                p_wins.append(p_win)
                meta.append({"subject": subject, "timestamp": r["timestamp"],
                             "glucose": r["glucose"]})
                kept += 1
            if verbose and kept:
                print(f"   {os.path.basename(ecg_name)[:40]:>42s}: {kept} windows", flush=True)
            del ecg
    return e_wins, p_wins, meta


def build_subject(subject: str, verbose: bool = True, n_jobs: int = -1) -> pd.DataFrame:
    """Extract every Level-2 feature for one subject, streaming SESSION BY SESSION.

    An earlier version collected every window for the subject first and only then
    computed features. That holds a few thousand windows (~40 KB each) live in the
    parent process for the whole subject, on top of whatever the ECG parse costs, and
    it is what ran the machine out of memory twice. Here each ECG session is loaded,
    turned into windows, reduced to features and discarded before the next session is
    touched, so peak memory is set by the largest single session rather than by the
    subject.

    The worker pool is created ONCE for the subject and reused across sessions:
    respawning eight processes per session would otherwise dominate the cost of the
    many short sessions in this dataset.
    """
    path = _zip_path(subject)
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    rows: list[dict] = []
    n_windows = 0

    with zipfile.ZipFile(path) as z:
        tz = detect_timezone(z)
        cgm = load_cgm(z)
        if verbose:
            print(f"[{subject}] timezone {tz.key}, {len(cgm)} CGM readings "
                  f"({cgm['glucose'].min():.1f}-{cgm['glucose'].max():.1f} mmol/L)",
                  flush=True)

        # PPG sessions are a few MB each, so they stay resident for the whole subject.
        ppg_sessions = []
        for name in sorted({n for n in z.namelist() if n.endswith("BVP.csv")}):
            try:
                ppg_sessions.append(load_ppg_session(z, name, tz))
            except Exception as exc:                       # noqa: BLE001
                if verbose:
                    print(f"   skip PPG {name}: {exc}", flush=True)

        ecg_files = sorted(n for n in z.namelist() if n.endswith("_ECG.csv"))
        with Parallel(n_jobs=n_jobs, batch_size=4) as parallel:
            for ecg_name in ecg_files:
                try:
                    ecg, ecg_t0 = load_ecg_session(z, ecg_name)
                except Exception as exc:                   # noqa: BLE001
                    if verbose:
                        print(f"   skip ECG {ecg_name}: {exc}", flush=True)
                    continue

                ecg_end = ecg_t0 + dt.timedelta(seconds=len(ecg) / ECG_FS)
                in_span = cgm[(cgm["timestamp"] >= ecg_t0) & (cgm["timestamp"] <= ecg_end)]

                e_wins, p_wins, meta = [], [], []
                for _, r in in_span.iterrows():
                    e_win = _window_before(ecg, ecg_t0, ECG_FS, r["timestamp"], ECG_WINDOW)
                    if e_win is None:
                        continue
                    p_win = None
                    for ppg, ppg_t0 in ppg_sessions:
                        p_win = _window_before(ppg, ppg_t0, PPG_FS,
                                               r["timestamp"], PPG_WINDOW)
                        if p_win is not None:
                            break
                    if p_win is None:
                        continue                            # need BOTH modalities
                    # A flat/dead channel yields NaN features; reject it here.
                    if np.ptp(e_win) < 1e-9 or np.ptp(p_win) < 1e-9:
                        continue
                    # Keep full precision: see the note in load_ecg_session about what
                    # float32 does to the correlation-dimension features. A window is
                    # only ~32 KB, so there is nothing to save here anyway.
                    e_wins.append(np.asarray(e_win, dtype=np.float64))
                    p_wins.append(np.asarray(p_win, dtype=np.float64))
                    meta.append({"subject": subject, "timestamp": r["timestamp"],
                                 "glucose": r["glucose"]})

                del ecg                                     # free before extracting
                if not meta:
                    continue

                feats = parallel(delayed(_features_for_window)(e, p)
                                 for e, p in zip(e_wins, p_wins))
                kept = sum(f is not None for f in feats)
                rows.extend({**m, **f} for m, f in zip(meta, feats) if f is not None)
                n_windows += len(meta)
                del e_wins, p_wins, meta, feats

                if verbose:
                    print(f"   {os.path.basename(ecg_name)[:38]:>40s}: {kept:4d} windows"
                          f"  (running total {len(rows)})", flush=True)

    df = pd.DataFrame(rows)
    if verbose:
        dropped = n_windows - len(rows)
        print(f"[{subject}] TOTAL {len(df)} usable windows"
              + (f" ({dropped} dropped for non-finite features)" if dropped else ""),
              flush=True)
    return df


def _subject_cache(subject: str) -> str:
    return os.path.join(DATA_ROOT, f"_features_{subject}.csv")


def build_dataset(subjects: list[str] | None = None, cache: bool = True,
                  verbose: bool = True, n_jobs: int = -1) -> pd.DataFrame:
    """Build (and cache) the feature table across subjects.

    Each subject is checkpointed to its own CSV as soon as it finishes, and a subject
    whose checkpoint already exists is skipped. Extraction takes hours, so a crash,
    a reboot or an out-of-memory kill must not throw away the subjects that already
    succeeded -- an earlier version wrote the cache only at the very end and lost four
    completed subjects when the run was killed.
    """
    cache_path = os.path.join(DATA_ROOT, "features_ecg_ppg.csv")
    if cache and os.path.exists(cache_path):
        df = pd.read_csv(cache_path, dtype={"subject": str})
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        if verbose:
            print(f"Loaded cached features: {df.shape[0]} windows "
                  f"x {sum(c.startswith(('ECG_', 'PPG_')) for c in df.columns)} features "
                  f"from {df['subject'].nunique()} subjects")
        return df

    os.makedirs(DATA_ROOT, exist_ok=True)
    subjects = subjects or [s for s in SUBJECTS if os.path.exists(_zip_path(s))]

    frames = []
    for s in subjects:
        part = _subject_cache(s)
        if os.path.exists(part):
            if verbose:
                print(f"[{s}] checkpoint exists, skipping", flush=True)
            frames.append(pd.read_csv(part, dtype={"subject": str}))
            continue
        df_s = build_subject(s, verbose, n_jobs=n_jobs)
        if len(df_s):
            # Write to a temp name first, then rename: a checkpoint must never be
            # half-written if the process dies mid-save.
            tmp = part + ".part"
            df_s.to_csv(tmp, index=False)
            os.replace(tmp, part)
            frames.append(df_s)

    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Drop repeated (subject, timestamp) rows.
    #
    # Some subjects have OVERLAPPING Zephyr session files covering the same period, so a
    # single CGM reading falls inside more than one recording and its window is
    # extracted once per file. The resulting rows are byte-identical (verified: all 239
    # duplicate groups in the 10-subject build had identical features), so keeping the
    # first loses nothing.
    #
    # This is not cosmetic. An exact duplicate landing on both sides of a random split
    # puts a test row verbatim into training, which inflates exactly the optimistic
    # random-split score this study exists to measure. Leaving them in would manufacture
    # a small version of the effect we are reporting.
    before = len(df)
    df = df.drop_duplicates(subset=["subject", "timestamp"], keep="first").reset_index(drop=True)
    if verbose and before != len(df):
        print(f"removed {before - len(df)} duplicate (subject, timestamp) rows "
              f"from overlapping recordings", flush=True)

    if cache:
        df.to_csv(cache_path, index=False)
        if verbose:
            print(f"Cached {df.shape[0]} windows to {cache_path}")
    return df


if __name__ == "__main__":
    import sys
    subs = sys.argv[1:] or None
    build_dataset(subs, cache=True, verbose=True)
