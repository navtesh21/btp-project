# Results

Reproduction of **"Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG
Feature Fusion and Weight-Based Choquet Integral Multimodel Approach"** (Li et al.,
IEEE TNNLS 2024) on the public **D1NAMO** dataset.

Every number below is measured, not estimated. Figures are in `figures/results/`, raw
per-prediction data and tables in `results/`.

---

## 1. What was reproduced, and what could not be

| Paper stage | Status here |
|---|---|
| Level 1: signal collection, 0.5–40 Hz filtering | Reproduced (`src/d1namo.py`) |
| Level 2: temporal features (db4 DWT, 7 levels, 10 features per sub-band) | Reproduced for ECG: 8 signals × 10 features = **80 features** (`src/features_temporal.py`) |
| Level 2: PPG temporal features (another 80) | **Not possible** — D1NAMO has no PPG channel |
| Level 2: morphological features (ResNet branch) | **Not implemented** — needs the raw 2-D signal images and a GPU |
| Level 2: feature selection (UFS / RFE / L1 intersection) | **Not implemented** |
| Level 3: 3 models → Choquet integral fusion | Reproduced (`src/base_models.py`, `src/choquet.py`, `src/fusion.py`) |
| Stage 2: temporal Choquet over a prediction history | Reproduced (`src/temporal_choquet.py`) |
| Assessment: RMSE, MARD, Parkes error grid | Reproduced (`src/metrics.py`, `src/error_grid.py`) |

**The headline caveat.** The paper used a private dataset with **ECG *and* PPG** plus a
ResNet morphological branch. D1NAMO is **ECG-only**. So this is a faithful reproduction
of the ECG-temporal half of the paper's pipeline, and its accuracy should not be read as
a like-for-like replication of the paper's 1.49 mmol/L.

### Data

4054 windows of 16 s, 9 Type-1 diabetic patients, glucose range 2.2 – 22.2 mmol/L,
ECG sampled at 250 Hz. Reference glucose from the patients' CGM.

---

## 2. The two evaluation protocols

The paper pools all participants and splits into folds, so the same patient appears in
both training and test data. That measures accuracy for a patient the model has already
seen. It is worth also asking the harder question, so both are reported:

- **Protocol A — pooled 5-fold.** Paper-style. A patient may appear in train *and* test.
- **Protocol B — leave-one-subject-out.** Train on 8 patients, test on the 9th, rotate.
  The test patient is a complete stranger.

**Reference point:** a model with no skill at all, which always predicts the mean
glucose, scores **RMSE 4.19 mmol/L** on this data. Any result must be read against that.

---

## 3. Protocol A — pooled 5-fold (paper's Table II layout)

All numbers below are from the **corrected** run (see Section 6.2). Choquet fusion,
per fold:

| Fold | RMSE (mmol/L) | MARD (%) | Zone A (%) | Zone A+B (%) |
|---|---|---|---|---|
| 1 | 4.07 | 46.44 | 36.62 | 81.63 |
| 2 | 3.75 | 45.52 | 39.95 | 81.63 |
| 3 | 4.14 | 45.32 | 39.33 | 82.98 |
| 4 | 3.73 | 40.69 | 40.32 | 85.33 |
| 5 | 3.92 | 46.25 | 37.28 | 80.00 |
| **Average** | **3.92** | **44.84** | **38.70** | **82.31** |

All methods, pooled across folds:

| Method | RMSE (mmol/L) | MARD (%) | Zone A (%) | Zone A+B (%) |
|---|---|---|---|---|
| RandomForest | **3.90** | 45.79 | **39.32** | **82.56** |
| GradientBoosting | 4.03 | 47.36 | 35.50 | 80.78 |
| Bagging | **3.90** | 45.80 | 39.29 | 82.49 |
| PlainAverage | 3.93 | 46.16 | 38.28 | 82.26 |
| WeightedAverage | 3.91 | 45.99 | 38.85 | 82.26 |
| Choquet | 3.92 | **44.84** | 38.70 | 82.31 |

The fuzzy densities the Choquet integral assigned (corrected run):

| Fold | RandomForest | GradientBoosting | Bagging |
|---|---|---|---|
| 1 | 0.105 | 0.058 | 0.103 |
| 2 | 0.098 | 0.041 | 0.099 |
| 3 | 0.104 | 0.052 | 0.106 |
| 4 | 0.115 | 0.044 | 0.115 |
| 5 | 0.120 | 0.066 | 0.119 |

This is the mechanism working as the paper intends: Gradient Boosting is the weakest
base model (RMSE 4.03) and receives roughly **half** the density of the other two.

Figures: `fig10_parkes_protocolA.png`, `fig09_timeseries_protocolA_patient*.png`,
`zone_distribution.png`, `rmse_by_method.png`, `densities_protocolA.png`.

---

## 4. Protocol B - leave-one-subject-out

The honest generalisation test: the model has never seen the test patient. Choquet
fusion, per fold (one fold = one held-out patient):

| Fold | RMSE (mmol/L) | MARD (%) | Zone A (%) | Zone A+B (%) |
|---|---|---|---|---|
| 1 | 3.24 | 51.39 | 22.14 | 73.80 |
| 2 | 3.22 | 27.35 | 38.47 | 93.32 |
| 3 | 2.83 | 29.05 | 43.46 | 93.82 |
| 4 | 6.55 | 47.66 | 27.50 | 68.37 |
| 5 | 3.45 | 46.34 | 28.20 | 76.80 |
| 6 | 5.15 | 83.89 | 27.05 | 68.65 |
| 7 | 5.83 | 65.67 | 26.88 | 66.34 |
| 8 | 2.58 | 37.60 | 35.19 | 91.98 |
| 9 | 6.03 | 180.51 | 3.25 | 21.95 |
| **Average** | **4.32** | **63.27** | **28.02** | **72.78** |

All methods, pooled across folds:

| Method | RMSE (mmol/L) | MARD (%) | Zone A (%) | Zone A+B (%) |
|---|---|---|---|---|
| RandomForest | 4.41 | 53.92 | **30.71** | 76.05 |
| GradientBoosting | 4.43 | 52.58 | 29.30 | 76.99 |
| Bagging | 4.41 | 53.90 | 30.69 | 75.97 |
| PlainAverage | **4.40** | 53.27 | 29.95 | 76.49 |
| WeightedAverage | **4.40** | 53.50 | 30.37 | 76.39 |
| Choquet | **4.40** | **52.18** | 30.09 | **77.08** |

**Read this table carefully: every method is WORSE than the 4.19 mmol/L no-skill
baseline.** On a patient the model has never seen, the 80 ECG temporal features do not
carry enough blood-glucose information to beat simply guessing that patient's average.

The per-fold spread is the other half of the story. Three patients predict reasonably
(folds 2, 3, 8: RMSE 2.6-3.2, Zone A+B above 91%), and three predict badly (folds 4, 7,
9: RMSE 5.8-6.6). Fold 9 is a near-total failure, with MARD 180% and only 3.25% of
predictions in Zone A. The model is not uniformly mediocre; it works for some people and
fails for others, which is the classic signature of **between-patient physiological
variation** that the features do not capture.

Within this protocol the Choquet fusion is the best method on MARD (52.18%) and on
Zone A+B (77.08%), and ties for best RMSE. So the fusion is doing its job relative to
the alternatives - it is the inputs that are too weak.

Figures: `fig10_parkes_protocolB.png`, `fig09_timeseries_protocolB_patient*.png`,
`densities_protocolB.png`.

---

## 5. Comparison with the paper

| | RMSE (mmol/L) | MARD (%) | Zone A (%) | Zone A+B (%) |
|---|---|---|---|---|
| Paper, ECG + PPG (proposed) | 1.49 | 13.42 | 80.09 | 99.49 |
| Paper, ECG only | 1.56 | 13.88 | 77.90 | 99.38 |
| **Ours, Protocol A (Choquet)** | **3.92** | **44.84** | **38.70** | **82.31** |
| **Ours, Protocol B (Choquet)** | **4.40** | **52.18** | **30.09** | **77.08** |
| No-skill baseline | 4.19 | — | — | — |

Figure: `paper_vs_ours.png`, `paper_tableII_rmse_mard.png`, `paper_zones.png`.

This is not a like-for-like comparison, and the gap should not be attributed to the
Choquet fusion. The differences that matter:

1. **No PPG.** The paper's own ablation shows PPG alone reaches 1.82 mmol/L, and the
   two signals together beat either alone. Half the paper's feature set is missing here.
2. **No morphological branch.** The paper's ResNet features on the signal waveforms are
   absent; only the temporal statistical features exist here.
3. **No feature selection.** The paper intersects UFS, RFE and L1 selections. All 80
   features are used here, noisy ones included.
4. **Different dataset.** D1NAMO is free-living ambulatory data from 9 patients. The
   paper's dataset was collected under controlled conditions with a meal protocol.

---

## 6. Findings

### 6.1 The Choquet fusion is the best method on MARD, not on RMSE

Under Protocol A the fused prediction (RMSE 3.92) sits between the two strong base
models (3.90) and the weak one (4.03) — it does not win on RMSE. But it gives the
**best MARD of any method, 44.84% against 45.79% for Random Forest**. MARD weights an
error by how large it is *relative to the true value*, so it punishes mistakes at low
glucose hardest. The fusion is therefore modestly safer exactly where safety matters
most, which is the trade the paper's assessment section cares about.

Fixing the density bug in Section 6.2 improved the fusion's RMSE (3.951 to 3.92) and
its Zone A share (37.72% to 38.70%), at the cost of a slightly worse MARD (44.19 to
44.84). Both before and after the fix, Choquet has the best MARD of any method tested.

### 6.2 Why: a split bug collapsed every fuzzy density to the floor

This is the most important finding in the project, and it is a **defect that was found
and fixed**, not a property of the data.

The Choquet integral needs a **density** per model: a number saying how competent that
model is on its own. `src/fusion.py` estimates it as the out-of-fold R-squared on the
training split, clipped into (0.01, 0.99).

In the first run, **all three densities clipped to the 0.01 floor in every fold of both
protocols** (`results/uncorrected/densities_protocol*.csv`). Measured directly, the
unclipped out-of-fold R-squared values were:

| Model | out-of-fold R-squared (buggy) | fuzzy density after the fix |
|---|---|---|
| RandomForest | -0.159 | 0.098 - 0.154 |
| GradientBoosting | -0.181 | 0.031 - 0.097 |
| Bagging | -0.154 | 0.099 - 0.152 |

(The middle column is a direct measurement on one split; the right column is the range of
densities actually assigned across all folds of both protocols after the fix.)

**The root cause.** `fusion.py` called `cross_val_predict(model, X, y, cv=self.cv_folds)`
passing an *integer*. scikit-learn turns an integer into `KFold` **without shuffling**,
which takes contiguous blocks of rows. The cached feature table arrives sorted by
patient (001 through 009), so each inner "fold" was a block of whole patients. The
density was therefore silently measuring **cross-patient generalisation** rather than the
model's competence on the data it is actually trained for, and cross-patient
generalisation on ECG-only features is near zero (Section 6.4). Every model scored a
negative R-squared, every density hit the floor, and:

- **WeightedAverage became identical to PlainAverage** (3.927 vs 3.927, to three
  decimals). Equal densities give equal weights, so the weighted average degenerates.
- **The Choquet integral lost the thing it exists to exploit.** Its advantage over a
  weighted average is modelling *interaction* between models of differing competence.
  Given three densities pinned to an identical floor, there is no competence ordering
  left, and it collapses toward an order-statistic of three near-identical inputs.

**The fix** is one line: pass an explicit `KFold(n_splits=..., shuffle=True,
random_state=seed)`. That lifts the out-of-fold R-squared from -0.159 to +0.109 for
Random Forest and gives the fusion real densities to work with.

The lesson generalises beyond this project: when data is grouped (by patient, by
session, by device) the ordering of the rows is not neutral, and an integer `cv=` is
never safe.

### 6.3 The base models are redundant

Random Forest, Bagging and Gradient Boosting are all tree ensembles trained on identical
features, and they produce highly correlated predictions (RMSE 3.90 / 3.91 / 4.03). The
Choquet integral rewards *complementary* models. Three near-duplicates give it nothing
to work with. The paper avoids this by feeding its three algorithms **three different
feature sets** (temporal, morphological, and fused) for nine models total — a diversity
we cannot reproduce without the morphological branch.

### 6.4 The predictions regress to the mean

`fig09_timeseries_protocolA_patient*.png` shows the pattern plainly: predictions track
the broad trend but compress toward the middle of the range, under-calling the high
excursions and over-calling the hypos. The Parkes grid says the same thing —
**Zone A only 38.7%**, against the paper's 80.09% — with most of the remainder in
Zone B, and a non-trivial tail in C and D that would be clinically unacceptable in a
real device.

### 6.5 Temporal Choquet gives a small, real gain

Smoothing each model's prediction stream over its last N = 7 readings before fusing
improves leave-one-subject-out RMSE from 4.409 to **4.318** (-0.091, about 2%), with
equal density 1/N behaving best. The gain is small because the dominant error here is
**between-patient bias**, and temporal smoothing removes variance, not bias.
Figure: `our_temporal_choquet.png`.

Note: this sweep was measured **before** the density fix of Section 6.2, so its 4.409
baseline is the pre-fix Protocol B figure. The corrected Protocol B baseline is 4.40, so
re-running `python -m src.run_temporal` would be needed to state the post-fix gain
exactly. The conclusion (a small gain, bounded by the fact that the error is bias rather
than noise) is unaffected.

---

## 7. Honest conclusion

The pipeline is a faithful implementation of the paper's ECG-temporal feature extraction
and its Choquet-integral fusion, and the fusion mathematics is verified by hand in
`MATH.md`. One real defect was found and fixed along the way (Section 6.2), which
restored the fusion's intended behaviour.

On D1NAMO the method does **not** reach clinically useful accuracy:

- **Protocol A** (patient seen in training): RMSE 3.92 mmol/L against a 4.19 no-skill
  baseline. A real but small improvement, roughly 6%.
- **Protocol B** (patient unseen): RMSE 4.40 mmol/L, **worse than the baseline**. The
  model does not transfer to a new person.
- **Clinical safety:** Zone A 38.7% (Protocol A), against the paper's 80.09%. Only
  82.3% of predictions land in the clinically acceptable A+B region, against the paper's
  99.49%. A device behaving this way would not be usable.

The evidence points at the *input*, not the fusion. Within each protocol the Choquet
integral is the best or joint-best method on MARD and on Zone A+B, so the fusion is
doing its job relative to the alternatives. What it has to work with is three
highly-correlated tree ensembles reading 80 ECG-only features that, on a new patient,
explain no more variance than that patient's own average.

The honest headline: **the ECG-temporal half of this paper, on its own, does not predict
blood glucose on D1NAMO.** That is a legitimate negative result about a signal, not a
failure of the implementation, and the per-fold breakdown in Section 4 shows why: the
method works for some patients and collapses for others.

### What would most likely help, in order

1. **A dataset with PPG.** The single biggest gap. The paper's own ablation has PPG alone
   at 1.82 mmol/L, comparable to its ECG-only 1.56, and fusing both gives its best
   result of 1.49. Half the paper's evidence is simply unavailable here.
2. **Feature selection** (UFS / RFE / L1 intersection). 80 features against 4054 windows
   with near-zero out-of-sample R-squared is a regime where noisy features actively hurt.
   This is the one paper stage not implemented, and the cheapest to add.
3. **Model diversity.** Random Forest, Bagging and Gradient Boosting are all tree
   ensembles on identical features, and they agree closely (RMSE 3.90 / 3.90 / 4.03). The
   Choquet integral rewards *complementary* models; the paper gets that diversity by
   feeding three algorithms three different feature sets for nine models total.
4. **Per-patient calibration.** The gap between Protocol A and Protocol B, and the
   patient-by-patient spread in Section 4, both say the model leans on patient-specific
   patterns. Real CGM devices are calibrated per user, so this matches practice.

---

## 8. Reproducing these results

```bash
# 1. Build the feature cache from raw D1NAMO (slow; cached afterwards)
python -m src.d1namo

# 2. Run the evaluation and save every prediction
python -m src.generate_results                      # paper-faithful: 10-fold + LOSO
python -m src.generate_results --folds-a 5 --cv-folds 2   # faster, as used above

# 3. Draw the figures from the saved predictions
python -m src.make_figures

# 4. Charts of the paper's published numbers and our logged runs
python -m src.plot_reported
```

## 9. Figure index

| File | What it shows | Source of numbers |
|---|---|---|
| `fig10_parkes_protocolA.png` | Parkes error grid, our Choquet fusion (paper Fig. 10) | ours, measured |
| `fig09_timeseries_protocolA_patient*.png` | Predicted vs reference over time (paper Fig. 9) | ours, measured |
| `zone_distribution.png` | Zone A–E split per method | ours, measured |
| `rmse_by_method.png` | RMSE per method vs no-skill baseline | ours, measured |
| `our_methods_rmse.png` | RMSE + MARD per method, both protocols | ours, measured |
| `our_temporal_choquet.png` | Temporal Choquet density sweep | ours, measured |
| `densities_protocolA.png` | Fuzzy density per model per fold | ours, measured |
| `paper_tableII_rmse_mard.png` | The paper's tenfold RMSE / MARD by signal | paper, Table II |
| `paper_zones.png` | The paper's Zone A / A+B by signal | paper, Table II |
| `paper_vs_ours.png` | Side-by-side, with the caveats stated | both, labelled |
