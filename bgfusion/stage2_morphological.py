"""
bgfusion/stage2_morphological.py
================================
LEVEL 2b of the paper: the SPATIAL MORPHOLOGICAL feature branch.

WHAT THE PAPER DOES, AND WHAT WE DO INSTEAD (stated plainly)
------------------------------------------------------------
The paper feeds individual ECG/PPG segments to a ResNet and uses the learned embedding
as its "spatial morphological" feature vector. We do not reproduce that literally, for
two reasons:

  1. PRACTICAL: a ResNet over every segment, retrained inside each leave-one-subject-out
     fold, is not feasible on CPU-only hardware.
  2. SCIENTIFIC: the mechanism linking blood glucose to waveform SHAPE is known and
     specific, so we can measure it directly instead of hoping a network rediscovers it.
     Hypoglycaemia triggers adrenaline release, which drives potassium into cells
     (via beta-2 stimulated Na+/K+ ATPase). The resulting hypokalaemia prolongs
     myocardial repolarisation, which shows up as a LONGER QT INTERVAL and flattened /
     altered T waves. Hyperglycaemia suppresses vagal tone and impairs coronary
     microcirculation, producing QT prolongation, ST depression, T-wave change and
     reduced heart-rate variability.
     (See Advances in ECG-Based Non-Invasive Blood Glucose Monitoring Technology, 2026,
     and Eckert & Agardh, Clin Physiol 1998, for the QT/hypoglycaemia link.)

So this module extracts the morphological quantities the physiology actually predicts,
rather than a learned embedding. They are interpretable, each one is individually
citable to a mechanism, and they cost milliseconds instead of GPU-hours. The substitution
is a deliberate, documented deviation from the paper -- not a silent shortcut.

WHAT IS MEASURED
----------------
ECG (per beat, then summarised over the window by mean and standard deviation):
    RR interval, heart rate, QRS duration and amplitude, QT interval, corrected QT
    (Bazett), ST-segment level, T-wave amplitude and sharpness,
    plus HRV summaries SDNN, RMSSD, pNN50.

PPG (per pulse, then summarised the same way):
    systolic amplitude, pulse width at half height, rise time, fall time,
    rise/fall ratio, pulse area, and the augmentation index.

Every function returns NaN rather than a guess when a wave cannot be located; the caller
(stage1_data.build_subject) drops any window containing a non-finite feature.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

# --- fiducial search windows, in seconds relative to the R peak --------------------
# These are standard physiological ranges for an adult resting ECG.
_Q_SEARCH = 0.06        # Q is within 60 ms before R
_S_SEARCH = 0.06        # S is within 60 ms after R
_T_START, _T_END = 0.10, 0.40    # the T wave sits 100-400 ms after R
_ST_OFFSET = 0.08       # the ST level is read 80 ms after R (the classic "J+80" point)


def _safe(values: list[float]) -> tuple[float, float]:
    """Mean and standard deviation of a list, as (nan, nan) when there is nothing to average."""
    arr = np.asarray([v for v in values if np.isfinite(v)], dtype=float)
    if arr.size == 0:
        return float("nan"), float("nan")
    return float(arr.mean()), float(arr.std())


def detect_r_peaks(ecg: np.ndarray, fs: float) -> np.ndarray:
    """Locate R peaks.

    The R wave is the tallest, sharpest deflection in the beat, so we square the
    first difference to emphasise steep slopes (this is the core idea of the classic
    Pan-Tompkins detector), smooth it, then take peaks that are both tall enough and
    far enough apart to be separate beats.
    """
    if len(ecg) < int(0.5 * fs):
        return np.array([], dtype=int)

    diff = np.diff(ecg, prepend=ecg[0])
    energy = diff ** 2
    # ~100 ms moving average: wide enough to merge one QRS into a single bump.
    win = max(1, int(0.10 * fs))
    smooth = np.convolve(energy, np.ones(win) / win, mode="same")

    # A beat cannot repeat faster than ~200 bpm, so peaks must be >= 300 ms apart.
    peaks, _ = find_peaks(smooth, distance=int(0.30 * fs),
                          height=np.percentile(smooth, 90) * 0.4)
    # The energy peak sits on the QRS slope; snap to the true local extremum nearby.
    refined = []
    half = int(0.05 * fs)
    for p in peaks:
        lo, hi = max(0, p - half), min(len(ecg), p + half)
        if hi > lo:
            refined.append(lo + int(np.argmax(np.abs(ecg[lo:hi] - np.median(ecg)))))
    return np.unique(refined)


def ecg_morphological_features(ecg: np.ndarray, fs: float) -> dict[str, float]:
    """Per-beat ECG morphology, summarised over the window."""
    r = detect_r_peaks(ecg, fs)
    baseline = float(np.median(ecg))

    rr, qrs_dur, qrs_amp, qt, st_level, t_amp, t_sharp = [], [], [], [], [], [], []

    for i, rp in enumerate(r):
        # ---- RR interval (needs a following beat) --------------------------------
        if i + 1 < len(r):
            rr.append((r[i + 1] - rp) / fs)

        # ---- Q and S: the minima flanking R --------------------------------------
        q_lo = max(0, rp - int(_Q_SEARCH * fs))
        s_hi = min(len(ecg), rp + int(_S_SEARCH * fs))
        if q_lo >= rp or s_hi <= rp + 1:
            continue
        q_idx = q_lo + int(np.argmin(ecg[q_lo:rp]))
        s_idx = rp + int(np.argmin(ecg[rp:s_hi]))

        qrs_dur.append((s_idx - q_idx) / fs)
        qrs_amp.append(float(ecg[rp] - min(ecg[q_idx], ecg[s_idx])))

        # ---- ST level, read at J+80 ms -------------------------------------------
        st_idx = rp + int(_ST_OFFSET * fs)
        if st_idx < len(ecg):
            st_level.append(float(ecg[st_idx] - baseline))

        # ---- T wave: largest deflection in the repolarisation window -------------
        t_lo = rp + int(_T_START * fs)
        t_hi = min(len(ecg), rp + int(_T_END * fs))
        if t_hi - t_lo < 3:
            continue
        seg = ecg[t_lo:t_hi]
        t_idx = t_lo + int(np.argmax(np.abs(seg - baseline)))
        t_amp.append(float(ecg[t_idx] - baseline))
        # "Sharpness": how fast the T wave rises and falls. Flattening of the T wave is
        # one of the reported dysglycaemia markers, and a flatter wave has a smaller
        # peak second derivative.
        if 1 <= t_idx - t_lo < len(seg) - 1:
            t_sharp.append(float(abs(ecg[t_idx - 1] - 2 * ecg[t_idx] + ecg[t_idx + 1])))

        # ---- QT interval: Q onset to the end of the T wave -----------------------
        # T end is approximated as the point where the wave returns towards baseline.
        tail = ecg[t_idx:t_hi]
        if tail.size:
            back = np.where(np.abs(tail - baseline) < 0.25 * abs(t_amp[-1] or 1))[0]
            t_end = t_idx + (int(back[0]) if back.size else tail.size - 1)
            qt.append((t_end - q_idx) / fs)

    feats: dict[str, float] = {}
    for name, seq in (("RR", rr), ("QRSdur", qrs_dur), ("QRSamp", qrs_amp),
                      ("QT", qt), ("STlevel", st_level), ("Tamp", t_amp),
                      ("Tsharp", t_sharp)):
        m, s = _safe(seq)
        feats[f"{name}_mean"] = m
        feats[f"{name}_std"] = s

    # ---- derived: heart rate and corrected QT ------------------------------------
    rr_mean = feats["RR_mean"]
    feats["HR_mean"] = 60.0 / rr_mean if rr_mean and np.isfinite(rr_mean) and rr_mean > 0 else float("nan")
    # Bazett's correction removes the dependence of QT on heart rate, which is what
    # makes QTc comparable across beats: QTc = QT / sqrt(RR).
    feats["QTc"] = (feats["QT_mean"] / np.sqrt(rr_mean)
                    if rr_mean and np.isfinite(rr_mean) and rr_mean > 0
                    and np.isfinite(feats["QT_mean"]) else float("nan"))

    # ---- heart-rate variability ---------------------------------------------------
    rr_arr = np.asarray(rr, dtype=float)
    if rr_arr.size >= 2:
        diffs = np.diff(rr_arr)
        feats["SDNN"] = float(rr_arr.std())
        feats["RMSSD"] = float(np.sqrt(np.mean(diffs ** 2)))
        feats["pNN50"] = float(np.mean(np.abs(diffs) > 0.050) * 100.0)
    else:
        feats["SDNN"] = feats["RMSSD"] = feats["pNN50"] = float("nan")

    return feats


def ppg_morphological_features(ppg: np.ndarray, fs: float) -> dict[str, float]:
    """Per-pulse PPG (blood volume pulse) morphology, summarised over the window."""
    if len(ppg) < int(1.0 * fs):
        return {f"{n}_{s}": float("nan")
                for n in ("Samp", "Pwidth", "Rise", "Fall", "RFratio", "Parea", "AI")
                for s in ("mean", "std")}

    baseline = float(np.median(ppg))
    # Systolic peaks: one per heartbeat, so at least 300 ms apart.
    peaks, _ = find_peaks(ppg, distance=int(0.30 * fs),
                          height=baseline + 0.2 * np.std(ppg))

    samp, width, rise, fall, ratio, area, aug = [], [], [], [], [], [], []

    for i, p in enumerate(peaks):
        # Foot of this pulse = the minimum between the previous peak and this one.
        lo = peaks[i - 1] if i else max(0, p - int(1.0 * fs))
        hi = peaks[i + 1] if i + 1 < len(peaks) else min(len(ppg) - 1, p + int(1.0 * fs))
        if p - lo < 2 or hi - p < 2:
            continue
        foot = lo + int(np.argmin(ppg[lo:p]))
        nxt_foot = p + int(np.argmin(ppg[p:hi]))
        if p - foot < 2 or nxt_foot - p < 2:
            continue

        amp = float(ppg[p] - ppg[foot])
        if amp <= 0:
            continue
        samp.append(amp)
        rise.append((p - foot) / fs)                 # systolic upstroke time
        fall.append((nxt_foot - p) / fs)             # diastolic decay time
        ratio.append(rise[-1] / fall[-1] if fall[-1] > 0 else float("nan"))
        area.append(float(np.trapezoid(ppg[foot:nxt_foot] - ppg[foot])) / fs)

        # Pulse width at half the systolic height -- a standard shape descriptor that
        # widens when peripheral vascular tone changes.
        half = ppg[foot] + amp / 2.0
        seg = ppg[foot:nxt_foot]
        above = np.where(seg >= half)[0]
        width.append((above[-1] - above[0]) / fs if above.size >= 2 else float("nan"))

        # Augmentation index: the reflected (diastolic) wave relative to the systolic
        # peak. It is read from the second derivative, where the reflection shows up
        # as a local maximum after the systolic peak.
        tail = ppg[p:nxt_foot]
        if tail.size > 4:
            d2 = np.diff(tail, n=2)
            if d2.size:
                aug.append(float(np.max(d2) / amp))

    feats: dict[str, float] = {}
    for name, seq in (("Samp", samp), ("Pwidth", width), ("Rise", rise),
                      ("Fall", fall), ("RFratio", ratio), ("Parea", area), ("AI", aug)):
        m, s = _safe(seq)
        feats[f"{name}_mean"] = m
        feats[f"{name}_std"] = s
    return feats


if __name__ == "__main__":
    # Sanity check on a synthetic beat train: features must be finite and the recovered
    # heart rate must match the rate we synthesised.
    fs = 250.0
    t = np.arange(0, 16.0, 1 / fs)
    hr_true = 72.0
    beat = hr_true / 60.0
    # crude ECG-like signal: sharp R spike plus a broad T bump, once per beat
    phase = (t * beat) % 1.0
    ecg = (np.exp(-((phase - 0.10) ** 2) / 2e-5) * 1.0        # R
           + np.exp(-((phase - 0.32) ** 2) / 8e-4) * 0.25)    # T
    f = ecg_morphological_features(ecg, fs)
    print(f"synthetic HR = {hr_true}, recovered = {f['HR_mean']:.1f}")
    assert abs(f["HR_mean"] - hr_true) < 5, f
    assert np.isfinite(f["QT_mean"]) and np.isfinite(f["QTc"])

    # The PPG runs at its OWN sample rate, so it needs its own time vector -- reusing
    # the 250 Hz ECG vector here would silently scale every PPG duration by 250/64.
    ppg_fs = 64.0
    t_ppg = np.arange(0, 16.0, 1 / ppg_fs)
    ppg = (np.sin(2 * np.pi * beat * t_ppg)
           + 0.3 * np.sin(4 * np.pi * beat * t_ppg) + 1.5)
    g = ppg_morphological_features(ppg, ppg_fs)
    assert np.isfinite(g["Samp_mean"]) and np.isfinite(g["Rise_mean"]), g
    # A systolic upstroke is a fraction of a beat; anything near a whole beat period
    # (0.83 s here) means the pulse boundaries were mis-detected.
    assert 0.05 < g["Rise_mean"] < 0.50, f"implausible rise time: {g['Rise_mean']}"
    print(f"PPG systolic amplitude = {g['Samp_mean']:.3f}, rise time = {g['Rise_mean']:.3f}s")
    print(f"ECG morphological features: {len(f)}   PPG: {len(g)}   TOTAL: {len(f)+len(g)}")
    print("self-test passed")
