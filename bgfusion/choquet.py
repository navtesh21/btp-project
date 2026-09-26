"""
src/choquet.py
==============
The heart of Image #1: the CHOQUET INTEGRAL that fuses the three models' predictions.

WHY NOT JUST AVERAGE THE THREE PREDICTIONS?
-------------------------------------------
A plain average treats the models as equally good and totally independent. But:
  * Some models are more trustworthy than others (should count more).
  * Models can be REDUNDANT (two of them basically agree -> counting both fully is
    double-counting) or COMPLEMENTARY (they shine in different situations).
A plain weighted average can handle "more trustworthy", but it CANNOT express
redundancy/teamwork between models, because it only assigns importance to each model
ALONE. The Choquet integral fixes this by using a "fuzzy measure", which assigns an
importance to *every GROUP of models*, not just to each model singly.

THE TWO INGREDIENTS
-------------------
1) FUZZY MEASURE g (also called a "capacity"):
   A function that gives a number in [0, 1] to every possible subset of models, with:
     - g(empty set) = 0            (no models -> no importance)
     - g(all models) = 1           (everybody together -> full importance)
     - if A is inside B, then g(A) <= g(B)   ("monotonic": adding a model can't hurt)
   This is exactly properties 1) and 2) the paper lists (eq. around (13)).

   Defining g for EVERY subset is a lot of numbers (2^N of them). The classic shortcut is
   the SUGENO lambda-measure: you only choose one "density" g_i per model (how good that
   model is alone), and a single number lambda then determines the importance of every
   group automatically, via:
        g(A united B) = g(A) + g(B) + lambda * g(A) * g(B)      (for disjoint A, B)
   lambda is found from the rule g(all models) = 1, which gives the equation:
        1 + lambda = product over i of (1 + lambda * g_i)        (solve for lambda)
   - If the densities sum to exactly 1  -> lambda = 0 -> g is additive -> Choquet becomes
     an ordinary weighted average. (So weighted average is just a SPECIAL CASE.)
   - If they sum to MORE than 1 -> lambda < 0 -> "super-additive penalty": overlapping/
     redundant strong models don't get to add up fully (no double-counting).
   - If they sum to LESS than 1 -> lambda > 0 -> "synergy bonus": groups are worth more
     together than apart.

2) THE CHOQUET INTEGRAL itself (paper eq. (13)):
   Given the model predictions h(1..N) for one sample, SORT them from largest to smallest,
   then accumulate:
        Choquet = sum over j of  h_sorted[j] * ( g(top j models) - g(top j-1 models) )
   Intuitively it's a weighted sum where the "weight" given to each prediction depends on
   how important the GROUP of all predictions at least that large is. Sorting is what lets
   the group-importances (the fuzzy measure) come into play.
"""

from __future__ import annotations

import numpy as np


def solve_lambda(densities: np.ndarray) -> float:
    """Find the Sugeno lambda for the given per-model densities g_i.

    Solves   1 + lambda = product_i (1 + lambda * g_i)   for the valid root lambda > -1
    (and lambda != 0 unless the densities happen to sum to 1).

    HOW: the right-hand side, product_i (1 + g_i * lambda), is a polynomial in lambda.
    Moving everything to one side gives  product_i (1 + g_i*lambda) - (1 + lambda) = 0.
    We build that polynomial's coefficients and ask numpy for its roots, then keep the
    one root that is real and > -1 and (essentially) non-zero.
    """
    g = np.asarray(densities, dtype=float)

    # Special case: if densities already sum to 1, the measure is additive and lambda = 0.
    if abs(g.sum() - 1.0) < 1e-12:
        return 0.0

    # Build the polynomial  product_i (g_i * lambda + 1).
    # np.convolve multiplies polynomials given as coefficient lists (highest power first).
    # Each factor (g_i * lambda + 1) is the list [g_i, 1].
    poly = np.array([1.0])
    for gi in g:
        poly = np.convolve(poly, [gi, 1.0])

    # Now subtract (lambda + 1): the lambda^1 coefficient is poly[-2], constant is poly[-1].
    poly[-2] -= 1.0   # subtract the "lambda" term
    poly[-1] -= 1.0   # subtract the "1" term

    # np.roots returns ALL roots (possibly complex). We want the unique meaningful one.
    roots = np.roots(poly)
    real_roots = roots[np.abs(roots.imag) < 1e-9].real  # keep (nearly) real roots
    valid = [r for r in real_roots if r > -1.0 + 1e-9 and abs(r) > 1e-9]

    if not valid:
        # Fallback: densities effectively additive; behave like a weighted average.
        return 0.0

    # Theory guarantees a unique valid root; if several survive numerically, the correct
    # sign is determined by whether the densities sum above or below 1.
    if g.sum() > 1.0:
        # super-additive region: lambda is negative, in (-1, 0)
        candidates = [r for r in valid if r < 0]
    else:
        # synergy region: lambda is positive
        candidates = [r for r in valid if r > 0]
    chosen = candidates[0] if candidates else valid[0]
    return float(chosen)


class ChoquetFuser:
    """Fuse several models' predictions with a Sugeno-lambda Choquet integral.

    Usage:
        fuser = ChoquetFuser(densities=[0.7, 0.6, 0.65])   # one density per model
        fused = fuser.fuse(pred_matrix)                    # pred_matrix shape (rows, models)

    `densities[i]` says how competent model i is on its own (a number in (0, 1)). In
    fusion.py we compute these from each model's training accuracy (its R^2 score), so
    better models get a bigger density automatically.
    """

    def __init__(self, densities: np.ndarray, model_names: list[str] | None = None):
        self.densities = np.asarray(densities, dtype=float)
        self.model_names = model_names
        # Precompute lambda ONCE; it depends only on the densities, not on the data.
        self.lam = solve_lambda(self.densities)

    # ---- the core math, for ONE sample (one row of predictions) ----------------------
    def _choquet_one(self, values: np.ndarray) -> float:
        """Choquet integral of one prediction vector (one value per model)."""
        values = np.asarray(values, dtype=float)

        # Sort predictions from LARGEST to smallest, and reorder densities the same way,
        # because eq. (13) requires h(1) >= h(2) >= ... >= h(N).
        order = np.argsort(values)[::-1]
        v_sorted = values[order]
        d_sorted = self.densities[order]

        g_prev = 0.0          # g(top 0 models) = g(empty set) = 0
        result = 0.0
        for j in range(len(values)):
            # Grow the "top group" by adding the j-th source, using the Sugeno rule:
            #   g(A united {x}) = g(A) + g_x + lambda * g(A) * g_x
            g_curr = g_prev + d_sorted[j] + self.lam * g_prev * d_sorted[j]
            # Add this prediction, weighted by how much the group importance just grew.
            result += v_sorted[j] * (g_curr - g_prev)
            g_prev = g_curr
        # After the loop, g_prev should be ~1.0 = g(all models). (Sanity property.)
        return result

    # ---- apply to MANY samples at once -----------------------------------------------
    def fuse(self, pred_matrix: np.ndarray) -> np.ndarray:
        """Fuse a whole batch.

        pred_matrix : shape (n_samples, n_models) -- column i is model i's predictions.
        returns     : shape (n_samples,)          -- one fused blood-glucose value per row.
        """
        pred_matrix = np.asarray(pred_matrix, dtype=float)
        # Run the single-sample Choquet integral on each row.
        return np.array([self._choquet_one(row) for row in pred_matrix])


if __name__ == "__main__":
    # A tiny, hand-checkable demo so you can SEE Choquet differ from a plain average.
    # Three models, with model 0 the strongest (density 0.8), model 2 the weakest (0.4).
    densities = np.array([0.8, 0.6, 0.4])
    fuser = ChoquetFuser(densities)
    print("densities          :", densities, " (sum =", densities.sum(), ")")
    print("solved lambda      :", round(fuser.lam, 4),
          "  (negative => redundancy is discounted)")

    # One sample where the three models predicted 9.0, 7.0, 5.0 mmol/L.
    sample = np.array([9.0, 7.0, 5.0])
    plain_average = sample.mean()
    fused = fuser._choquet_one(sample)
    print("\npredictions        :", sample)
    print("plain average      :", round(plain_average, 4))
    print("Choquet fusion     :", round(fused, 4),
          " (leans toward the value the more-important models support)")

    # Show it works on a batch too.
    batch = np.array([[9.0, 7.0, 5.0],
                      [4.0, 4.5, 6.0],
                      [12.0, 11.0, 11.5]])
    print("\nbatch fusion       :", np.round(fuser.fuse(batch), 4))
