# Noninvasive blood glucose monitoring with Choquet-integral model fusion

A from-scratch reproduction of the decision-fusion method in:

> J. Li et al., "Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG
> Feature Fusion and Weight-Based Choquet Integral Multimodel Approach," IEEE
> Transactions on Neural Networks and Learning Systems, vol. 35, no. 10, 2024.

The aim is to estimate blood glucose (BG) from physiological signals without a finger
prick, by running several machine-learning models and combining their predictions with a
Choquet integral.

```
   ┌───────────────┐
   │ Random Forest │──┐
   └───────────────┘  │
   ┌───────────────┐  │   ┌──────────────────┐   ┌───────────┐
   │ Gradient Boost│──┼──>│ Choquet integral │──>│ BG output │
   └───────────────┘  │   │      fusion      │   └───────────┘
   ┌───────────────┐  │   └──────────────────┘
   │    Bagging    │──┘
   └───────────────┘
        Choquet integral multi-model fusion   (the paper's Fig. 6)
```

This repository implements that fusion block, the paper's temporal Choquet (which smooths
each model's prediction stream over time), and the ECG feature-extraction pipeline that
feeds them.

## What is implemented

| Part | Paper section |
|---|---|
| Random Forest, Gradient Boosting, and Bagging base models | II-D |
| Sugeno-λ fuzzy measure and Choquet integral (multimodel fusion) | II-D, eq. 13 |
| Temporal Choquet (fuse each model's last N=7 predictions over time) | II-D |
| Level-1 signal cleaning (0.5 to 40 Hz band-pass) | II-A |
| Level-2 temporal features: db4 DWT (7 levels), 8 signals × 10 features = 80 | II-B |
| RMSE and MARD metrics | II-E |

The paper uses ECG and PPG together (160 temporal features) plus a ResNet morphological
branch. This reproduction runs on the D1NAMO dataset, which records ECG only. It reproduces
the 80 ECG temporal features and both Choquet fusions. The PPG and ResNet parts are not
included because that data is not present in D1NAMO.

## Results on D1NAMO (4,054 ECG windows, 9 patients)

Always predicting the mean glucose gives an RMSE of 4.19 mmol/L, which is the no-skill
baseline any model has to beat.

| Setting | RMSE (mmol/L) | MARD (%) |
|---|---|---|
| Pooled 5-fold, best single model (Random Forest) | 3.90 | 45.8 |
| Pooled 5-fold, Choquet fusion | 3.95 | 44.2 |
| Leave-one-subject-out, Choquet fusion | 4.41 | 51.1 |
| Leave-one-subject-out, with temporal Choquet | 4.32 | 51.2 |

How to read these: ECG-temporal features alone carry only weak signal for absolute glucose,
so the best model beats the no-skill baseline by about 7%, and the temporal Choquet adds
about another 2%. The fusion code is correct; the ceiling comes from the missing modalities
(PPG) and features, which is why the original paper needed them to reach 1.49 mmol/L. The
full discussion is in [`explain.md`](explain.md), sections 16 and 17.

## Repository layout

```
src/
  data.py               synthetic dataset (scaffolding to unit-test the fusion)
  base_models.py        RandomForest, GradientBoosting, Bagging
  choquet.py            Sugeno-λ fuzzy measure and Choquet integral (the core)
  fusion.py             assembles the multimodel fusion
  metrics.py            RMSE, MARD
  main.py               run the fusion on synthetic data (instant demo)
  features_temporal.py  the paper's 80 ECG temporal features (db4 DWT and 10 features)
  d1namo.py             load real D1NAMO ECG/glucose into a feature table (cached)
  run_d1namo.py         evaluate the fusion on real data (pooled and leave-one-subject-out)
  temporal_choquet.py   the paper's temporal Choquet
  run_temporal.py       evaluate raw vs temporal-smoothed fusion
train.py                train once, save the model to bg_model.pkl
app.py                  Streamlit demo web app
explain.md              plain-English walkthrough of every file
MATH.md                 every formula derived from scratch, with a worked example
resource.md             curated YouTube and course learning path
```

The whole thing is classical machine learning and runs on a normal CPU. No GPU is needed.

## Setup

```bash
pip install -r requirements.txt
```

## Getting the data (not in this repo)

The D1NAMO data (about 10 GB) and the IEEE PDF are not committed. To reproduce the
real-data results, download the D1NAMO diabetes subset from Zenodo
(<https://zenodo.org/records/5651217>) and unzip it into:

```
data/d1namo/diabetes_subset_ecg_data/...
data/d1namo/diabetes_subset_pictures-glucose-food-insulin/...
```

## Running

```bash
python -m src.main          # fusion on synthetic data (instant sanity demo)
python -m src.d1namo        # build the real feature cache (one-time, ~60 to 90 min on CPU)
python -m src.run_d1namo    # evaluate the fusion on real data (RMSE/MARD)
python -m src.run_temporal  # evaluate the temporal Choquet
python train.py             # train and save the model to bg_model.pkl
streamlit run app.py        # launch the demo web app at http://localhost:8501
```

## Learning the project

The repository is written to be read, not just run:

- [`explain.md`](explain.md) explains every file in plain English, assuming no machine-learning background.
- [`MATH.md`](MATH.md) derives every formula from zero (ensembles, fuzzy measures, the Sugeno-λ measure, the Choquet integral, the DWT and the 10 features, RMSE/MARD), with a hand-checkable example.
- [`resource.md`](resource.md) is an ordered YouTube and course study path (StatQuest, NPTEL, Andrew Ng) mapped to each part of the code.

## Acknowledgements

- Method: Li et al., IEEE TNNLS 2024 (cited above). Authors' code: <https://github.com/SIATCAS/SFF-WCIM>.
- Data: the open D1NAMO dataset, Dubosson et al., Informatics in Medicine Unlocked, 2018.

Built as a B.Tech project, with an emphasis on understanding every step.
