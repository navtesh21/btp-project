"""
src/metrics.py
==============
The two accuracy numbers the paper reports (its Section II-E, "Assessment Metrics").
A "metric" is just a single number that summarises how wrong our predictions are.

  * RMSE  -- Root-Mean-Square Error   (paper eq. 16)
  * MARD  -- Mean Absolute Relative Difference  (paper eq. 17), the standard glucose metric

Lower is better for BOTH. We keep them in their own tiny file so every other file can
import and reuse them, and so this is the single place that defines "how we grade".
"""

from __future__ import annotations

import numpy as np


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root-Mean-Square Error, in the same units as blood glucose (mmol/L).

    Steps (this IS the paper's eq. 16):
      1. error of each prediction   = y_pred - y_true
      2. square each error          (makes them positive; punishes big misses extra)
      3. take the MEAN of the squares
      4. take the square ROOT       (brings units back to mmol/L)

    So RMSE ~ "the typical size of a prediction error, in mmol/L".
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_pred - y_true) ** 2)))


def mard(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Relative Difference, as a PERCENT (paper eq. 17).

    For each sample: |y_pred - y_true| / y_true  (the error as a FRACTION of the true
    value), then average and multiply by 100. This is the metric glucose-monitor makers
    quote, because being "off by 1 mmol/L" matters more when the true value is small.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_pred - y_true) / y_true) * 100.0)
