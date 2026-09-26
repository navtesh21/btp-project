"""
src/features_temporal.py
========================
FAITHFUL implementation of the paper's "Temporal Statistical Feature Extraction"
(Section II-B, Level 2). We follow the paper step by step:

  STEP 1 (Data preprocessing based on DWT, eq. 1 & Fig. 3):
     Decompose the ECG window with the Discrete Wavelet Transform (DWT) using the
     "db4" (Daubechies-4) mother wavelet, up to 7 levels. Reconstruct the signal from
     each detail coefficient cD1..cD7. This yields 8 signals to analyse:
        FE0 = the ORIGINAL ECG window
        FE1..FE7 = reconstructions from detail levels cD1..cD7
     (Paper eq. 2:  F_ECG_temporal = {FE0, FE1, ..., FE7}.)

  STEP 2 (Feature calculation):
     From EACH of those 8 signals, extract the SAME 10 features the paper lists
     (paper, text around eqs. 2-3):
        Kur = Kurtosis            Ske = Skewness
        SM  = Signal Mobility     SC  = Signal Complexity   (Hjorth parameters)
        FD  = Fractal Dimension   CD  = Correlation Dimension
        C0  = C0-complexity       PSE = Power Spectral Entropy
        KE  = Kolmogorov Entropy  SE  = Shannon Entropy
     8 signals x 10 features = 80 ECG temporal features  (paper: "80 from ECG").

NOTE ON FIDELITY: the paper extracts 80 from ECG AND 80 from PPG (160 total). The D1NAMO
dataset has ECG only, so we reproduce the 80 ECG features exactly; the PPG half is absent
because the data is. Every feature name below matches the paper's notation (FEi_<feat>).

The precise mathematical definition of each of the 10 features is in MATH.md, Section on
temporal features. Read that alongside this file.
"""

from __future__ import annotations

import warnings

import numpy as np
import pywt
from scipy.stats import kurtosis, skew

import antropy
import nolds

# The paper's exact choices:
WAVELET = "db4"          # Daubechies-4 mother wavelet (paper Section II-B-1)
DWT_LEVELS = 7           # decompose up to 7 levels (paper Section II-B-1)

# The 10 feature short-names, in the paper's order (used to build column names).
FEATURE_NAMES = ["Kur", "Ske", "SM", "SC", "FD", "CD", "C0", "PSE", "KE", "SE"]


# ----------------------------------------------------------------------------------
# STEP 1: DWT decomposition + per-detail-level reconstruction (paper eq. 1, Fig. 3)
# ----------------------------------------------------------------------------------
def dwt_reconstructions(x: np.ndarray) -> list[np.ndarray]:
    """Return [original, recon(cD1), recon(cD2), ..., recon(cD7)] -> 8 signals.

    `pywt.wavedec` splits the signal into coefficients:
        [cA7, cD7, cD6, cD5, cD4, cD3, cD2, cD1]
    (cA7 = coarse approximation; cD_k = detail at level k).
    To "reconstruct from cD_k only", we keep cD_k and zero everything else, then run the
    inverse transform `pywt.waverec`. The result is a same-length signal carrying only the
    wiggles that live at scale k -- this is the paper's reconstruction at detail level k.
    """
    x = np.asarray(x, dtype=float)
    coeffs = pywt.wavedec(x, WAVELET, level=DWT_LEVELS)

    signals = [x]  # FE0 = the original window itself
    for k in range(1, DWT_LEVELS + 1):
        # position of cD_k inside the coeffs list: cD7 is at index 1, ... cD1 at index 7.
        idx = DWT_LEVELS - k + 1
        masked = [np.zeros_like(c) for c in coeffs]  # all-zero copy
        masked[idx] = coeffs[idx]                    # keep ONLY detail level k
        rec = pywt.waverec(masked, WAVELET)
        signals.append(rec[: len(x)])                # waverec may add 1 sample; trim it
    return signals


# ----------------------------------------------------------------------------------
# STEP 2: the 10 features (definitions detailed in MATH.md)
# ----------------------------------------------------------------------------------
def _shannon_entropy_amplitude(x: np.ndarray, bins: int = 64) -> float:
    """SE: Shannon entropy of the signal's amplitude distribution.
    Histogram the values into `bins`, turn counts into probabilities p_i, then
    H = -sum p_i * log2(p_i).  High H = values spread evenly; low H = concentrated.
    """
    counts, _ = np.histogram(x, bins=bins)
    p = counts.astype(float)
    p = p[p > 0]              # 0*log0 = 0, so drop empty bins
    p /= p.sum()
    return float(-np.sum(p * np.log2(p)))


def _c0_complexity(x: np.ndarray) -> float:
    """C0: the C0-complexity. Idea: split the signal into a "regular" part (the strong
    spectral lines) and an "irregular" part (everything below the mean power). C0 is the
    energy fraction carried by the irregular part -- bigger = more random/complex.

    Steps: FFT -> power per frequency -> zero out components with power <= mean power
    (these are the "regular" dominant components) -> inverse FFT gives the irregular part
    y -> C0 = ||x - y||^2 / ||x||^2.  (Standard definition; see MATH.md.)
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    fft = np.fft.fft(x)
    power = np.abs(fft) ** 2
    mean_power = power.mean()
    # Keep only the dominant ("regular") spectral components; zero the rest.
    regular_fft = np.where(power > mean_power, fft, 0.0)
    regular = np.fft.ifft(regular_fft).real      # the regular part of the signal
    irregular_energy = np.sum((x - regular) ** 2)
    total_energy = np.sum(x ** 2)
    if total_energy == 0:
        return 0.0
    return float(irregular_energy / total_energy)


def ten_features(x: np.ndarray, fs: float, nonlinear_len: int = 1024) -> list[float]:
    """Compute the paper's 10 features for ONE signal.

    `nonlinear_len`: the correlation dimension (CD) and Kolmogorov/sample entropy (KE) are
    O(n^2) to compute. For long windows we decimate the signal to at most this many points
    before those two measures, to keep runtime sane. (Documented approximation; the other
    8 features use the full signal.)
    """
    # Force a C-contiguous float array: the numba-backed antropy functions (higuchi_fd,
    # hjorth_params, sample_entropy) reject non-contiguous arrays (DWT slices / decimated
    # views), so we normalise once here.
    x = np.ascontiguousarray(x, dtype=float)

    # 1) Kurtosis, 2) Skewness  -- shape of the amplitude distribution.
    kur = float(kurtosis(x))     # 0 for a normal distribution (Fisher definition)
    ske = float(skew(x))         # 0 for a symmetric distribution

    # 3) SM = Hjorth mobility, 4) SC = Hjorth complexity.
    #    antropy.hjorth_params returns (mobility, complexity) in one shot.
    sm, sc = antropy.hjorth_params(x)
    sm, sc = float(sm), float(sc)

    # 5) FD = Higuchi fractal dimension (a standard FD for biosignals).
    fd = float(antropy.higuchi_fd(x))

    # 8) PSE = power spectral entropy (entropy of the normalized power spectrum).
    pse = float(antropy.spectral_entropy(x, sf=fs, method="fft", normalize=True))

    # 10) SE = Shannon entropy of the amplitude histogram.
    se = _shannon_entropy_amplitude(x)

    # 7) C0 = C0-complexity (FFT-based, defined above).
    c0 = _c0_complexity(x)

    # 6) CD = correlation dimension, 9) KE ~ Kolmogorov entropy (estimated by sample
    #    entropy -- the common practical proxy; see MATH.md note). Both are O(n^2), so we
    #    decimate long signals first.
    xs = x
    if len(x) > nonlinear_len:
        step = int(np.ceil(len(x) / nonlinear_len))
        xs = x[::step]
    # numba-backed sample_entropy needs a C-contiguous array; a strided slice (x[::step])
    # is NOT contiguous, so make a clean copy.
    xs = np.ascontiguousarray(xs, dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")          # these libs warn on edge cases; ignore
        try:
            cd = float(nolds.corr_dim(xs, emb_dim=10))
        except Exception:
            cd = 0.0                              # degenerate window -> neutral value
        try:
            ke = float(antropy.sample_entropy(xs))
        except Exception:
            ke = 0.0
    # Guard against inf/nan from degenerate signals (e.g. a flat reconstruction).
    cd = cd if np.isfinite(cd) else 0.0
    ke = ke if np.isfinite(ke) else 0.0

    return [kur, ske, sm, sc, fd, cd, c0, pse, ke, se]


def extract_temporal_features(window: np.ndarray, fs: float) -> dict[str, float]:
    """Full paper pipeline for one ECG window -> 80 named features.

    Returns a dict {"FE0_Kur": ..., "FE0_Ske": ..., ..., "FE7_SE": ...} (8x10 = 80).
    """
    signals = dwt_reconstructions(window)          # 8 signals (FE0..FE7)
    out: dict[str, float] = {}
    for i, sig in enumerate(signals):
        feats = ten_features(sig, fs)
        for name, val in zip(FEATURE_NAMES, feats):
            out[f"FE{i}_{name}"] = val
    return out


if __name__ == "__main__":
    # Self-test + benchmark on a synthetic ECG-like window so we can see it works and how
    # long it takes (important, because we'll run it on thousands of real windows).
    import time

    fs = 250.0
    n = 4000                                       # ~16 s window = paper's ~20 beats
    t = np.arange(n) / fs
    # Fake ECG: a periodic spike train (~75 bpm) plus noise -- just to exercise the code.
    rng = np.random.default_rng(0)
    ecg = np.sin(2 * np.pi * 1.25 * t) + 0.3 * rng.standard_normal(n)

    start = time.time()
    feats = extract_temporal_features(ecg, fs)
    elapsed = time.time() - start

    print(f"Extracted {len(feats)} features in {elapsed:.2f} s for one {n}-sample window.")
    print("First signal's 10 features (FE0_*):")
    for name in FEATURE_NAMES:
        print(f"   FE0_{name:<3s} = {feats['FE0_' + name]:.4f}")
