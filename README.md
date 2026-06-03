# Noninvasive Blood Glucose Monitoring — Choquet-Integral Multimodel Fusion

A from-scratch, learning-focused reproduction of the decision-fusion method in:

> **J. Li et al., "Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG
> Feature Fusion and Weight-Based Choquet Integral Multimodel Approach,"** *IEEE
> Transactions on Neural Networks and Learning Systems*, vol. 35, no. 10, 2024.

The goal: estimate **blood glucose (BG)** from physiological signals **without** a finger
prick, by running several machine-learning models and fusing their predictions with a
**Choquet integral**.

```
   ┌───────────────┐
   │ Random Forest │──┐
   └───────────────┘  │
   ┌───────────────┐  │   ┌──────────────────┐   ┌───────────┐
   │ Gradient Boost│──┼──►│ Choquet integral │──►│ BG output │
   └───────────────┘  │   │      fusion      │   └───────────┘
   ┌───────────────┐  │   └──────────────────┘
   │    Bagging    │──┘
   └───────────────┘
        Choquet integral multi-model fusion   (the paper's Fig. 6)
```

This repo implements that fusion block **and** the paper's *temporal* Choquet (smoothing
each model's prediction stream over time), plus the ECG feature-extraction pipeline that
feeds them.

---

## What's implemented (faithful to the paper)

| Part | Paper section | Status |
|---|---|---|
| RF + Gradient Boosting + Bagging base models | II-D | ✅ |
| Sugeno-λ fuzzy measure + Choquet integral (multimodel fusion) | II-D, eq. 13 | ✅ |
| **Temporal Choquet** (fuse each model's last N=7 predictions over time) | II-D | ✅ |
| Level-1 signal cleaning (0.5–40 Hz band-pass) | II-A | ✅ |
| Level-2 temporal features: db4 DWT (7 levels) → 8 signals × 10 features = **80** | II-B | ✅ |
| RMSE & MARD metrics | II-E | ✅ |
| Feature selection (UFS / RFE / L1) | II-B-3 | ⬜ next |
| PPG features + ResNet morphological branch | II-B | ⬜ needs PPG data |

**Honest scope:** the paper uses **ECG + PPG** (160 temporal features) + a ResNet
morphological branch. This reproduction runs on the **D1NAMO** dataset, which is **ECG-only**,
so it faithfully reproduces the **80 ECG temporal features** and both Choquet fusions, and
omits the PPG/ResNet parts because that data isn't available here.

---

## Results (real, on D1NAMO — 4,054 ECG windows, 9 patients)

No-skill baseline (always predict the mean) = **4.19 mmol/L** RMSE.

| Setting | RMSE (mmol/L) | MARD (%) |
|---|---|---|
| Pooled 5-fold — best single model (RF) | 3.90 | 45.8 |
| Pooled 5-fold — Choquet fusion | 3.95 | **44.2** |
| Leave-one-subject-out — Choquet fusion | 4.41 | 51.1 |
| Leave-one-subject-out — **+ temporal Choquet** | **4.32** | 51.2 |

**Reading it honestly:** ECG-temporal features alone carry only weak signal for *absolute*
glucose (best model beats the no-skill baseline by ~7%); the temporal Choquet adds a further
~2%. The fusion machinery is correct — the ceiling is set by the missing modalities (PPG) and
features, which is exactly why the original paper needed them to reach 1.49 mmol/L. Full
discussion in [`explain.md`](explain.md) §16–17.

---

## Repository layout

```
src/
  data.py               # synthetic dataset (scaffolding to unit-test the fusion)
  base_models.py        # RandomForest, GradientBoosting, Bagging
  choquet.py            # Sugeno-λ fuzzy measure + Choquet integral (the core)
  fusion.py             # assembles the multimodel fusion (Image #2)
  metrics.py            # RMSE, MARD
  main.py               # run Image #2 on synthetic data (instant demo)
  features_temporal.py  # paper's 80 ECG temporal features (db4 DWT + 10 features)
  d1namo.py             # load real D1NAMO ECG/glucose → feature table (cached)
  run_d1namo.py         # evaluate fusion on real data (pooled + leave-one-subject-out)
  temporal_choquet.py   # the paper's temporal Choquet (stage 2)
  run_temporal.py       # evaluate raw vs temporal-smoothed fusion
train.py                # train once, save model → bg_model.pkl
app.py                  # Streamlit demo web app
explain.md              # plain-English walkthrough of every file (the "textbook")
MATH.md                 # every formula derived from scratch, with a worked example
resource.md             # curated YouTube + course + reference learning path
```

> **No GPU required.** Everything is classical ML and runs on a normal CPU.

---

## Setup

```bash
pip install -r requirements.txt
```

## Getting the data (not in this repo)

The D1NAMO data (~10 GB) and the IEEE PDF are intentionally **not** committed. To reproduce
the real-data results, download the D1NAMO **diabetes subset** from Zenodo
(<https://zenodo.org/records/5651217>) and unzip it into:

```
data/d1namo/diabetes_subset_ecg_data/...
data/d1namo/diabetes_subset_pictures-glucose-food-insulin/...
```

## Running

```bash
python -m src.main          # Image #2 fusion on synthetic data (instant sanity demo)
python -m src.d1namo        # build the real feature cache (one-time, ~60–90 min on CPU)
python -m src.run_d1namo    # evaluate the fusion on real data (RMSE/MARD)
python -m src.run_temporal  # evaluate the temporal Choquet (stage 2)
python train.py             # train + save the model → bg_model.pkl
streamlit run app.py        # launch the demo web app at http://localhost:8501
```

---

## Learning the project

This repo is written to be **learned from**, not just run:
- **[`explain.md`](explain.md)** — every file explained in plain English, assuming no ML background.
- **[`MATH.md`](MATH.md)** — every formula (ensembles, fuzzy measures, Sugeno-λ, Choquet
  integral, DWT + the 10 features, RMSE/MARD) derived from zero, with a hand-checkable example.
- **[`resource.md`](resource.md)** — an ordered YouTube + course study path (StatQuest, NPTEL,
  Andrew Ng, …) mapped to each part of the code.

---

## Status & next steps

Done: both Choquet fusions (across models *and* across time), the ECG feature pipeline,
metrics, a trained-model demo app, and full docs. Next, in order of expected impact:
1. **Feature selection** (UFS / RFE / L1 intersection) — paper Section II-B-3.
2. **Add PPG + morphological features** — needs a dataset with PPG (e.g. PhysioCGM).

## Acknowledgements

- Method: Li et al., *IEEE TNNLS* 2024 (see citation above). Authors' code:
  <https://github.com/SIATCAS/SFF-WCIM>.
- Data: the open **D1NAMO** dataset — Dubosson et al., *Informatics in Medicine Unlocked*, 2018.

*Built as a B.Tech project, with an emphasis on understanding every step.*
