# explain.md: learning the Choquet-integral blood-glucose project from zero

> This file is your textbook for this project. We assume you know **nothing** about
> machine learning, signal processing, or the math involved. Every term is defined the
> first time it appears. Read it top to bottom like a story. Each time we write a new
> code file, we add a new chapter here explaining *what* the file does, *why* it exists,
> and *how every important line works*.
>
> ** The math lives in its own file: [`MATH.md`](MATH.md).** Every formula in the
> project and the paper (the ensembles, fuzzy measures, the Sugeno-λ derivation, the
> Choquet integral eq. 13, the weight fusion eqs. 14 to 15, and RMSE/MARD eqs. 16 to 17) is
> derived there from scratch, with a worked example you can check by hand and a full
> **list of learning resources** at the end. Read `explain.md` for the *code*, `MATH.md`
> for the *math*, they're meant to be read side by side.

---

## Table of Contents

1. [What are we building, and why?](#1-what-are-we-building-and-why)
2. [The paper in plain English](#2-the-paper-in-plain-english)
3. [The big architecture (the 3 levels)](#3-the-big-architecture-the-3-levels)
4. [Where Image #1 fits, and our plan](#4-where-image-1-fits-and-our-plan)
5. [A glossary you can come back to](#5-a-glossary-you-can-come-back-to)
6. [Chapter: `requirements.txt`](#6-chapter-requirementstxt) *(added as we build)*
7. [Chapter: `src/data.py`](#7-chapter-srcdatapy) *(added as we build)*
8. [Chapter: `src/base_models.py`](#8-chapter-srcbase_modelspy) *(added as we build)*
9. [Chapter: `src/choquet.py`](#9-chapter-srcchoquetpy) *(added as we build)*
10. [Chapter: `src/fusion.py`](#10-chapter-srcfusionpy) *(added as we build)*
11. [Chapter: `src/main.py`](#11-chapter-srcmainpy) *(added as we build)*

---

## 1. What are we building, and why?

We are re-creating (the technical word your professor used is **"mimicking"**) the method
from this research paper:

> **"Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG Feature
> Fusion and Weight-Based Choquet Integral Multimodel Approach"**, Li et al.,
> *IEEE Transactions on Neural Networks and Learning Systems*, 2024.

**The problem the paper solves:** People with diabetes need to measure their **blood
glucose (BG)**, the amount of sugar in their blood, many times a day. The usual ways
are either painful (a finger-prick that draws blood) or invasive (a sensor stuck under
the skin that must be replaced every 1 to 2 weeks). The paper asks: *can we estimate blood
glucose **without** drawing blood?*

**Their idea:** When your blood sugar changes, your **nervous system** reacts, and that
reaction subtly changes two signals that are easy to measure with cheap wearable
sensors:

- **ECG** (electrocardiogram), the electrical activity of your heart.
- **PPG** (photoplethysmogram), a light-based sensor (like the green light on a
  smartwatch) that measures blood-volume changes in your skin.

So the pipeline is: *measure ECG + PPG → extract numbers ("features") that describe them
→ feed those numbers to machine-learning models → predict the blood-glucose value.*

**Why "BG output" in the diagram = blood glucose.** In the picture your professor gave
you, the final box says **"BG output."** BG is just the paper's shorthand for **Blood
Glucose**. That box is the number we ultimately want to predict (e.g. "7.4 mmol/L").

---

## 2. The paper in plain English

A few vocabulary words from the abstract, decoded:

| Paper's word | Plain meaning |
|---|---|
| *Noninvasive* | Doesn't break the skin / draw blood. |
| *Spatiotemporal* | "Space + time." They pull out two **kinds** of features: **temporal** (statistics over time, like average heart rate) and **spatial/morphological** (the *shape* of one heartbeat waveform). |
| *Feature fusion* | Combining the two kinds of features into one big table of numbers. |
| *Multimodel* | They don't trust one model; they use several models and combine their answers. |
| *Choquet integral* | A clever mathematical way to **combine** several models' answers that is smarter than a plain average. (We dedicate a whole chapter to this, chapter 9.) |
| *Weight-based* | Each model gets a **weight** (an importance score). Models that were more accurate during training count for more. |

**The headline result they achieved:** an RMSE of 1.49 mmol/L. (RMSE = Root-Mean-Square
Error, a measure of "how far off, on average, were the predictions." Smaller is better.
We define it precisely in the glossary and use it in our code.)

---

## 3. The big architecture (the 3 levels)

The full paper is a 3-level pipeline. You don't need to build it all at once, and your
professor told you not to. But you should know the whole map so you understand where each
piece fits:

```
                         THE FULL PAPER (3 levels)

  Level 1: SIGNALS              Level 2: FEATURES                 Level 3: FUSION  <-- Image #1 lives here
  ----------------              -----------------                 ----------------
  Raw ECG sensor   ─┐           Temporal features (statistics)    Random Forest  ─┐
                    ├─ clean ─►  Morphological features (shape, ─► Gradient Boost ─┼─► Choquet ─► BG
  Raw PPG sensor   ─┘           via a "ResNet" neural net)        Bagging         ─┘   fusion   output
                                + feature selection (pick best)
```

- **Level 1, Signal collection & cleaning.** Record ECG and PPG, filter out noise
  (movement, electrical hum). *We will build this LATER ("going backwards").*
- **Level 2, Feature extraction & selection.** Turn the messy waveforms into a tidy
  table of numbers, and keep only the useful columns. *Also LATER.*
- **Level 3, Decision fusion (THIS IS IMAGE #1).** Take a table of features, run three
  machine-learning models on it, and **fuse** their predictions with the Choquet integral
  to get the final blood-glucose number. **This is what we build FIRST.**

---

## 4. Where Image #1 fits, and our plan

Image #1 (which is **Fig. 6** in the paper) is the **Level-3 decision-fusion block**:

```
   ┌─────────────────┐
   │  Random Forest  │──┐
   └─────────────────┘  │
   ┌─────────────────┐  │   ┌──────────────────┐   ┌───────────┐
   │ Gradient Boost  │──┼──►│ Choquet integral │──►│ BG output │
   └─────────────────┘  │   │      fusion      │   └───────────┘
   ┌─────────────────┐  │   └──────────────────┘
   │     Bagging     │──┘
   └─────────────────┘
        Choquet integral multi-model fusion
```

Your professor's strategy is smart: **build the *end* of the pipeline first**, get it
working and understood, then work *backwards* to add the feature extraction and signal
processing that feed it. That way you always have a runnable program.

**Our problem right now:** the real ECG/PPG data and features don't exist on our computer
yet (that's Levels 1 to 2, which come later). So to build and test Level 3 *today*, we will
**simulate** a realistic feature table and blood-glucose values. This lets the fusion
code run end-to-end immediately. When we later build the real feature extraction, we just
swap the simulated table for the real one, **the fusion code won't have to change.** That
is the whole point of building it modularly.

**Build order for this first step (matches Image #1):**

1. `src/data.py`, make a fake-but-realistic dataset (features → blood glucose).
2. `src/base_models.py`, the three models: Random Forest, Gradient Boosting, Bagging.
3. `src/choquet.py`, the fuzzy measure + Choquet integral that fuses the three.
4. `src/fusion.py`, glue: train models, get predictions, fuse them, weight them.
5. `src/main.py`, run the whole thing and print how well it did.

Each gets its own chapter below as we write it.

---

## 5. A glossary you can come back to

- **Feature:** one measured number describing the signal (e.g. "average heart rate").
  A row of features describes one moment; a **feature matrix** is many such rows stacked.
- **Target / label (`y`):** the correct answer we want to predict, here, the blood
  glucose value measured by a medical device.
- **Model:** a program that learns the relationship "features → target" from examples.
- **Training:** showing the model many (features, target) pairs so it can learn.
- **Prediction / inference:** giving the trained model new features and asking for `y`.
- **Regression:** predicting a *number* (blood glucose), as opposed to a category.
- **Ensemble:** a model made of many small models combined (Random Forest, Gradient
  Boosting, and Bagging are all ensembles, chapter 8 explains each).
- **RMSE (Root-Mean-Square Error):** `sqrt(mean((prediction - truth)^2))`. The typical
  size of the error, in the same units as blood glucose (mmol/L). Lower = better.
- **MARD (Mean Absolute Relative Difference):** `mean(|prediction - truth| / truth)`,
  usually shown as a %. The standard accuracy metric for glucose monitors. Lower = better.
- **Fuzzy measure (capacity):** a function that assigns an "importance" to *every group*
  of models, not just to each model alone, this lets it capture **teamwork** between
  models. Defined carefully in chapter 9.
- **Choquet integral:** the operation that combines the models' predictions using that
  fuzzy measure. A weighted average is a special, simpler case of it.

---

*(Chapters 6 to 11 are written below as we create each file. Keep scrolling after each build.)*

---

## 6. Chapter: `requirements.txt`

This is just a shopping list of the external Python libraries the project needs. Anyone
who downloads our project runs `pip install -r requirements.txt` and `pip` (Python's
package installer) fetches them all. We use four:

- **numpy**, the foundation for fast math on big arrays of numbers.
- **pandas**, tables ("DataFrames") with named columns; how we hold our features.
- **scikit-learn**, a library of ready-made machine-learning models and metrics. We do
  *not* hand-code Random Forest from scratch; scikit-learn gives us a tested version.
- **matplotlib**, for drawing charts (we'll use it later for the medical "error grid").

---

## 7. Chapter: `src/data.py`

**Its job:** invent a realistic dataset so we can build Image #1 today, before the real
ECG/PPG features exist. It outputs `X` (the feature table) and `y` (the blood-glucose
answers).

**The mental model:** a machine-learning dataset is two things:
- `X`, a table where every **row** is one example and every **column** is one feature.
- `y`, a list with one correct answer per row.

Our `X` has 2000 rows and 20 columns; `y` has 2000 blood-glucose numbers. The model's
job is to learn the hidden rule that turns a row of `X` into its `y`.

**How the file works, part by part:**

1. **`rng = np.random.default_rng(seed)`**, creates a random-number generator with a
   fixed *seed*. A seed makes "random" numbers come out identical every run, so your
   results are **reproducible** (you and your professor see the same numbers). This is a
   non-negotiable habit in science.

2. **Make raw features**, `rng.standard_normal((rows, cols))` fills a table with numbers
   drawn from the classic bell curve (mean 0, spread 1). We make two blocks, `temporal`
   and `morphological`, to mirror the paper's two feature families.

3. **Invent the hidden rule**, we decide *how* blood glucose depends on the features. We
   deliberately make it **curvy** (non-linear): a squared term (`temporal[:,1]**2`), a
   sine wave, and an **interaction** (`morph[:,1] * morph[:,2]`, which only matters when
   *both* are large). Why curvy? Because if the rule were a simple straight line, every
   model would solve it perfectly and we'd learn nothing about which model is better.
   Real biology is curvy, so this is also more honest. Crucially, only the first few
   columns matter, the rest are **distractors** (useless noise features), exactly like
   real measured data. That sets up the "feature selection" step we'll build later.

4. **Add noise & clip**, we add random wobble (real measurements are never perfect) and
   then `np.clip(raw, 2.2, 21.8)` forces every value into the real CGM device's range of
   2.2 to 21.8 mmol/L (matching the paper's Dexcom G6 device).

5. **Label & package**, we name the columns `temporal_00`, `morph_03`, … and wrap
   everything in a pandas DataFrame/Series so the rest of the code can refer to columns
   by name.

**`feature_groups(X)`** is a small helper that, given the table, tells you which columns
are temporal and which are morphological. We'll need this later to build the paper's
*three* feature sets (temporal-only, morphological-only, and both fused).

**The `if __name__ == "__main__":` block** at the bottom runs only when you execute the
file directly (`python -m src.data`). It prints a preview so you can *see* the data. When
another file *imports* this module, that block is skipped.

> Run it yourself: `python -m src.data`, you'll see a 2000×20 table and glucose values.

---

## 8. Chapter: `src/base_models.py`

**Its job:** create the three left-hand boxes of Image #1, **Random Forest**, **Gradient
Boosting**, and **Bagging**. Each is a complete model that, on its own, can predict blood
glucose from the features. The Choquet integral will later combine their three answers.

**First, what is a "decision tree"?** Imagine a flowchart: "Is `temporal_00` > 0.5? If
yes, go left; if no, go right…" After a few such yes/no questions you land in a bucket
that says "predict 8.1 mmol/L." That flowchart, learned automatically from data, is a
**decision tree**. One tree alone is twitchy, change a little data and it changes a lot,
and it loves to memorise noise. The fix is to combine **many** trees. A model made of
many sub-models is an **ensemble**. All three of our models are tree ensembles; they
differ in *how* they build and combine the trees:

| Model | How it builds trees | What problem it fights |
|---|---|---|
| **Bagging** | Many trees, each trained on a random **resample** of the rows, then averaged. | **Variance**, stops the model over-reacting to noisy rows. |
| **Random Forest** | Like Bagging, *plus* each tree may only consider a random **subset of features** at each split. The extra randomness makes trees more different, so their average is steadier. | **Variance**, even more so. |
| **Gradient Boosting** | Trees built **one at a time**; each new tree is trained to fix the **errors** left by the trees so far. | **Bias**, chases higher accuracy by relentlessly correcting mistakes. |

The first two build trees **in parallel and vote**; boosting builds them **in sequence,
each correcting the last**. Because they fail in different ways, fusing all three (the
whole point of Image #1) tends to beat any one alone.

**How the code works:**

- We import three ready-made models from **scikit-learn**. We don't code trees by hand,
  scikit-learn's versions are tested and fast.
- We use the `…Regressor` variants (not `…Classifier`) because blood glucose is a
  **number** to predict, which is called **regression**.
- `build_models(seed)` returns a dictionary `{name: model}` of three *untrained* models.
  Training happens later in `fusion.py`.
- **The knobs (hyperparameters) we set, in plain words:**
  - `n_estimators=200`, use 200 trees. More = steadier but slower.
  - `max_depth`, how many questions deep a tree may go. Shallower = less memorising of
    noise. Boosting likes shallow trees (`max_depth=3`) because each only fixes a sliver
    of the leftover error.
  - `learning_rate=0.05` (boosting only), how big a correction each new tree may make.
    Smaller = more careful and usually more accurate, but needs more trees.
  - `random_state=seed`, reproducibility again (these models use randomness inside).
  - `n_jobs=-1`, use all CPU cores to train trees in parallel.

**The self-test at the bottom** splits the data into a **training** part (the model learns
from it) and a **test** part (unseen data we grade it on). Testing on unseen data is the
*only* honest way to measure a model, otherwise it could just memorise the answers. When
you run `python -m src.base_models` you get each model's solo RMSE:

```
    RandomForest  RMSE = 1.375 mmol/L
GradientBoosting  RMSE = 1.234 mmol/L
         Bagging  RMSE = 1.369 mmol/L
```

These are the three numbers the Choquet integral will fuse. Notice they're already close
to the paper's headline 1.49 mmol/L, and our next step (fusion) aims to beat the best
single model by combining them.

---

## 9. Chapter: `src/choquet.py` (the heart of the project)

This is the box in the middle of Image #1. Read this chapter slowly; it's the one new
idea you really must own.

### 9.1 Why not just average the three predictions?

Say the three models predict 9.0, 7.0, and 5.0 mmol/L. The plain average is 7.0. But what
if the model that said *9.0* is the most reliable one? Then 7.0 under-weights the best
guess. A **weighted average** could fix *that*. But a weighted average still can't express
one more thing: **teamwork between models**. Two of our models might be near-duplicates
(they almost always agree), counting both at full strength is double-counting. Or two
models might be **complementary**, each strong where the other is weak, so *together* they
deserve more credit than apart. A weighted average gives each model a fixed importance **on
its own** and literally has no way to say "these two *together* are worth X." The Choquet
integral can.

### 9.2 Ingredient 1, the fuzzy measure (a.k.a. "capacity")

A **fuzzy measure** `g` assigns an importance (a number in [0, 1]) to **every group** of
models, not just to each model alone. It must obey the two rules the paper states:

- `g(∅) = 0`, no models, no importance.
- `g(all models) = 1`, everyone together = full importance.
- **monotonic**: if group A ⊆ group B, then `g(A) ≤ g(B)`, adding a model never lowers
  importance.

With 3 models there are 2³ = 8 groups to assign, manageable, but it explodes for more
models. The classic shortcut is the **Sugeno λ-measure**: you pick just **one density
`gᵢ` per model** (how good model *i* is alone), and a single number **λ** then fixes the
importance of *every* group automatically through this rule (for non-overlapping groups
A, B):

```
g(A ∪ B) = g(A) + g(B) + λ · g(A) · g(B)
```

λ is pinned down by forcing `g(all models) = 1`, which rearranges to the equation our
`solve_lambda()` solves:

```
1 + λ = (1 + λ·g₁) · (1 + λ·g₂) · … · (1 + λ·gₙ)
```

The **sign of λ tells the whole story**:

| Densities sum to… | λ is… | Meaning |
|---|---|---|
| exactly 1 | 0 | measure is additive → **Choquet = ordinary weighted average** (the simple case is included!) |
| more than 1 | negative | **redundancy penalty**: strong overlapping models don't fully add up (no double-counting) |
| less than 1 | positive | **synergy bonus**: groups are worth more together than apart |

### 9.3 Ingredient 2, the Choquet integral itself (paper eq. 13)

For one sample, take the model predictions, **sort them largest → smallest**, then walk
down the sorted list accumulating:

```
Choquet = Σⱼ  prediction_sorted[j] · ( g(top j models) − g(top j−1 models) )
```

Each prediction is weighted by **how much the group importance grows** when you add it.
The sorting is the trick that lets the *group* importances (the fuzzy measure) influence
the result, that's what an ordinary weighted sum can't do.

### 9.4 A worked example you can verify by hand

This is exactly what `python -m src.choquet` prints. Densities `[0.8, 0.6, 0.4]`
(model 0 strongest), which sum to 1.8 > 1, so λ comes out **negative** (−0.9283).
Predictions `[9, 7, 5]` (already sorted largest→smallest). Build the cumulative group
importances with the Sugeno rule:

| step j | add density | `g(top j)` = `g_prev + gⱼ + λ·g_prev·gⱼ` | weight = Δg | contribution |
|---|---|---|---|---|
| 1 | 0.8 | `0 + 0.8 + 0` = **0.800** | 0.800 | 9 × 0.800 = 7.200 |
| 2 | 0.6 | `0.8 + 0.6 − 0.9283·0.8·0.6` = **0.954** | 0.154 | 7 × 0.154 = 1.081 |
| 3 | 0.4 | `0.954 + 0.4 − 0.9283·0.954·0.4` = **1.000** | 0.046 | 5 × 0.046 = 0.228 |

Sum = **8.51 mmol/L**. Two sanity checks that prove the code is right:
- The final `g(top 3)` lands exactly on **1.000** = `g(all models)`, as required.
- The fused value **8.51** sits *above* the plain average **7.0**, pulled toward the 9.0
  that the strong models support. That pull is the Choquet integral earning its keep.

### 9.5 How the code is organised

- **`solve_lambda(densities)`**, turns the λ equation above into a polynomial, asks
  numpy for its roots (`np.roots`), and keeps the one valid root (real, `> −1`, non-zero).
  If the densities already sum to 1 it short-circuits to λ = 0 (weighted-average mode).
- **`class ChoquetFuser`**, you build it once with the densities; it solves λ in its
  constructor (λ depends only on densities, not on the data, so compute it once).
  - `_choquet_one(values)`, the table above, in code, for a single sample.
  - `fuse(pred_matrix)`, runs `_choquet_one` on every row of a `(samples × models)`
    table and returns one fused blood-glucose value per row.

Where do the densities come from? From each model's **training accuracy**, we'll compute
that in the next file (`fusion.py`) so that better models automatically get bigger
densities.

---

## 10. Chapter: `src/fusion.py`, assembling all of Image #1

**Its job:** put the three models and the Choquet integral together into one object you
can `.fit()` (train) and `.predict()` (use), and also compute simpler baselines so we can
*prove* whether Choquet actually helped.

**The one subtle, important idea: where do the densities come from?** The Choquet integral
needs a "density" (competence score) per model. We must measure competence **fairly**:

- *Not* on the **test set**, that set is sacred; touching it before the final grade is
  cheating (it would leak the answers).
- *Not* on the **training set directly**, a strong model can nearly *memorise* the
  training data, so every model looks equally perfect and the densities become useless.
- **Cross-validation on the training data.** Split the training rows into k parts
  (we use 5). Train on 4 parts, predict the held-out part; rotate until every training row
  has a prediction made by a model that *never saw that row*. Those "out-of-fold"
  predictions are a fair preview of real-world competence, and they **separate** the
  models (the genuinely better one scores higher). We score them with **R²** ("fraction
  of variance explained": 1.0 = perfect, 0 = no better than guessing the average).

That R² (clipped into the (0, 1) range the fuzzy measure needs) becomes each model's
density. `scikit-learn`'s `cross_val_predict` does the rotation for us.

**The class `ChoquetMultiModelFusion`:**
- `fit(X, y)`, for each model: (a) cross-validate to get its density, then (b) retrain it
  on *all* the training data for real use. Finally build the `ChoquetFuser` from the three
  densities.
- `predict(X)`, stack the three models' predictions into a `(rows × 3)` table and run the
  Choquet integral on it. **This is the literal "BG output" box of Image #1.**
- `predict_all(X)`, returns *every* prediction for comparison: each model alone, plus
  three ways of combining them: **PlainAverage** (all models equal, no teamwork),
  **WeightedAverage** (importance per model, still no teamwork), and **Choquet** (teamwork
  via the fuzzy measure). Comparing these three is how we judge if Choquet was worth it.

---

## 11. Chapter: `src/main.py`, the runner, and reading the results

**Its job:** run the whole thing and print a scoreboard. Steps: load data → split
train/test → `fit` the fusion → `predict_all` on the test set → grade everything with RMSE
and MARD → print a one-line verdict.

The two lines marked `# <-- DATA SOURCE` are the *only* lines that change when we move from
synthetic scaffolding to the real D1NAMO features. That isolation is the whole reason we
built it modularly.

**A real run looks like this:**

```
Per-model density (cross-validated competence, 0..1):
       RandomForest : 0.689
   GradientBoosting : 0.745
            Bagging : 0.689
   sum of densities : 2.123
   solved lambda    : -0.9694   (redundancy-penalty (<0))

          METHOD | RMSE (mmol/L) |  MARD (%)
----------------------------------------------
    RandomForest |         1.376 |     16.01
GradientBoosting |         1.204 |     13.79
         Bagging |         1.377 |     16.06
    PlainAverage |         1.294 |     15.03
 WeightedAverage |         1.290 |     14.98
         Choquet |         1.267 |     15.12  <-- Image #1 output
```

**How to read this (and an honest caveat):**
- The densities differ (GradientBoosting is the most competent, 0.745), so the fusion knows
  to trust it more. They sum to 2.12 > 1, so λ is negative, the redundancy-penalty regime
  (our three tree-ensembles overlap a lot, so the measure avoids double-counting them).
- **Choquet (1.267) beats both averaging baselines** (PlainAverage 1.294, WeightedAverage
  1.290) and beats two of the three models. That is the meaningful comparison: as a *way of
  combining*, the Choquet integral is doing better than naïve averaging.
- It does **not** beat GradientBoosting *alone* here. That's expected on this synthetic
  data: one model happens to dominate, and no fusion can do much when the others only add
  noise. `main.py` says this out loud rather than hiding it, honest reporting matters more
  than a flattering number. Fusion has the most to gain when the models are genuinely
  *diverse* (each best in different situations), which is exactly what we expect from the
  **real D1NAMO data**. That's the real test, coming next.

---

## 12. Moving to REAL data: the D1NAMO dataset

We've finished and verified Image #1 (the professor's first milestone). Now we begin
"going backwards", building the real signal→feature pipeline that feeds it, using the
**D1NAMO** dataset (real ECG + real glucose from Type-1 diabetes patients).

### 12.1 What's in D1NAMO

We downloaded the **diabetes subset**: 9 Type-1 diabetes patients (`001`, `009`). For each:
- **ECG**: one CSV per recording session (≈12 h each), columns `Time, EcgWaveform`, sampled
  at **250 Hz** (so ~11 million rows per file). 47 sessions total across the 9 patients.
- **Glucose**: a `glucose.csv` with a reading roughly every 5 minutes (mostly CGM, in
  **mmol/L**), these are our **targets** (`y`).

### 12.2 The honest limitation (read this)

The paper uses **ECG *and* PPG** and extracts **160** temporal features (80 ECG + 80 PPG),
plus a deep-learning **ResNet** morphological branch. **D1NAMO has no PPG.** So our faithful
reproduction covers the **80 ECG temporal features exactly as specified**, and omits the
PPG half and the ResNet branch because the data to compute them doesn't exist here. This is
a dataset constraint, not a shortcut, and the code is written so adding PPG later is just
"run the same extractor on the PPG channel."

### 12.3 How a glucose reading becomes a training row

```
   glucose reading at time t (e.g. 9.4 mmol/L)
                │
                ▼
   take the 16 s of ECG ending at t   ──►  band-pass filter 0.5 to 40 Hz  (Level 1 cleaning)
                                                      │
                                                      ▼
                                      80 temporal features (DWT + 10 features, Level 2)
                                                      │
                                                      ▼
                       one row of X  +  y = 9.4  +  remember it's patient 003
```

The **16 s window** matches the paper's "20 cardiac cycles" (≈16 s at 75 bpm). We do this for
every glucose reading that has enough ECG before it → **3,682 rows** across the 9 patients.

---

## 13. Chapter: `src/features_temporal.py`, the paper's 80 ECG features

**Its job:** take one 16 s ECG window and produce the paper's **80 temporal statistical
features**, exactly as Section II-B specifies. *The math (every formula) is in
[`MATH.md` §7](MATH.md#7-temporal-statistical-features--dwt--the-10-features-paper-section-ii-b);
this chapter explains the code.*

**Two stages, straight from the paper:**

1. **`dwt_reconstructions(x)`, split the window into 8 signals by scale.** Heartbeats mix
   slow drift, broad waves, and sharp spikes. The **Discrete Wavelet Transform (DWT)**
   separates a signal by *scale*. Using the **db4** wavelet and **7 levels** (the paper's
   exact choices), we get detail coefficients `cD1…cD7`; reconstructing the signal from each
   one (zeroing the others, then inverse-transforming) yields 7 scale-specific signals, plus
   the original = **8 signals** (`FE0…FE7`). We use the `PyWavelets` library (`wavedec` /
   `waverec`).

2. **`ten_features(x, fs)`, the same 10 features on each signal.** The paper's list:
   Kurtosis, Skewness, Signal Mobility & Complexity (Hjorth), Fractal Dimension (Higuchi),
   Correlation Dimension, C0-complexity, Power Spectral Entropy, Kolmogorov Entropy
   (estimated by Sample Entropy), and Shannon Entropy. We use `scipy.stats` for kurtosis/
   skew, `antropy` for the Hjorth/fractal/spectral/sample-entropy measures, `nolds` for the
   correlation dimension, and hand-written functions for C0-complexity and amplitude Shannon
   entropy. **8 signals × 10 features = 80.**

`extract_temporal_features(window, fs)` runs both stages and returns a dict
`{"FE0_Kur": …, …, "FE7_SE": …}`, 80 named numbers.

**Two practical engineering notes (both visible in the code):**
- **Contiguous arrays:** the `antropy` functions are compiled with `numba`, which *rejects*
  non-contiguous arrays (the DWT slices and decimated views are non-contiguous). So
  `ten_features` does `x = np.ascontiguousarray(x)` once at the top. (We hit this exact bug
  and fixed it, zero-valued features were the symptom.)
- **Speed of the O(N²) features:** Correlation Dimension and Sample Entropy compare every
  pair of points, so they cost ~N² operations. For long windows we **decimate** the signal
  to ≤1024 points before *only* those two measures (the other 8 use the full window). This is
  a documented approximation that keeps each window at ~1 s instead of many seconds.

Run `python -m src.features_temporal` to see all 80 features computed on a test window and
the per-window timing.

---

## 14. Chapter: `src/d1namo.py`, from raw recordings to (X, y)

**Its job:** orchestrate Levels 1 to 2 on the real files, find each glucose reading, grab the
ECG before it, clean it, extract the 80 features, and build the `(X, y, groups)` tables.

**The pieces:**
- **`load_glucose(subject)`**, reads `glucose.csv`, combines its `date` + `time` columns
  into a real timestamp, and returns `(timestamp, glucose, type)`. These glucose values are
  the targets `y`.
- **`read_ecg_session(path)`**, loads one ECG file. Two clever bits:
  - We **don't parse all 11 million timestamps** (that's slow). The signal is uniformly
    sampled, so we read only the **first and last** timestamps and compute the per-sample
    period; then "row *i* = start + *i* × period". `_read_last_data_line` grabs the final
    line by seeking to the end of the file instead of reading the whole thing.
  - We apply the paper's **Level-1 band-pass filter (0.5 to 40 Hz)** with `filtfilt`
    (forward-and-backward filtering, which removes phase lag). 0.5 Hz kills slow baseline
    wander; 40 Hz kills power-line/muscle noise, exactly the paper's preprocessing.
- **`build_dataset(...)`**, the main loop. For each subject → each ECG session → each
  glucose reading inside that session's time span: compute the window's sample range, slice
  the 16 s of ECG, call `extract_temporal_features`, and store the row with its glucose value
  and **subject id**. Results are cached to `features_temporal.csv` so the slow (~1 h)
  extraction runs only once. A `max_windows_per_session` argument lets us do a fast trial.

**Why we keep `groups` (the subject id per row):** when we evaluate, we must **not** train
and test on the *same patient*, that leaks information and flatters the score. Keeping the
patient id lets us split **by patient** (train on some people, test on others), which is the
honest medical-ML way and mirrors the paper's day-based split. We'll use this next.

> Current status: the full extraction (3,682 windows) is running and caching to disk. Once
> it finishes, we point `main.py` at these real features instead of the synthetic ones,
> changing only the two `# <-- DATA SOURCE` lines, and evaluate Image #1 on real data with
> patient-wise splitting. *(this chapter's evaluation results added next)*

---

## 15. Running, training, and deploying, without a GPU

A few questions that matter when you're new, answered plainly.

### 15.1 Do I need a GPU? No.

A **GPU** (graphics card) only speeds up **deep learning**, huge neural networks with
millions of parameters. Our models (Random Forest, Gradient Boosting, Bagging) are
**classical machine learning**: they run on your normal **CPU** and are fast. The only
GPU-hungry piece in the original paper is the **ResNet** morphological branch, which we are
**not** building (and couldn't, without PPG). So: **no GPU anywhere in this project.**

### 15.2 What "training" actually is here

Training = the model learning the pattern from examples. In our code it's one line:
`model.fit(X_train, y_train)`. On a few thousand rows it takes **seconds on a CPU**. The
~1-hour step you saw was **feature extraction** (raw ECG → 80 numbers), not training, and
it's a **one-time** cost because we cache the result to `features_temporal.csv`. After that,
training and predicting are quick.

### 15.3 How to run everything

```bash
pip install -r requirements.txt     # one-time setup

python -m src.main                  # Image #1 demo on synthetic data (instant)
python -m src.d1namo                # build the real feature cache (one-time, ~1h)
python -m src.run_d1namo            # evaluate on real data (RMSE/MARD tables)
python train.py                     # train once and SAVE the model to bg_model.pkl
streamlit run app.py                # launch the demo web app in your browser
```

### 15.4 Chapter: `train.py`, "deployment step 1: save the model"

**Deploying** a model just means making it reusable without re-running the project.
`train.py`:
1. loads the cached real features,
2. holds out 20% to measure honest quality (RMSE/MARD on unseen rows),
3. retrains on **all** the data for the final model,
4. saves the model + the 80 feature names + the metrics into a single file `bg_model.pkl`
   using `joblib` (Python's tool for saving objects to disk).

Later, *any* program can do `joblib.load("bg_model.pkl")` and call `.predict(...)` in
milliseconds, no retraining, no GPU.

### 15.5 Chapter: `app.py`, the Streamlit demo

**Streamlit** turns a Python script into a local web page with almost no web code. `app.py`
loads `bg_model.pkl` and gives you two tabs:
- **Try a real example:** pick a patient and one of their real ECG windows; the app shows
  each model's prediction, the Choquet fusion, and the *true* glucose the CGM measured, so
  you can literally watch the fusion at work versus reality.
- **Upload an ECG window:** drop in a CSV with an `EcgWaveform` column; the app band-pass
  filters it (Level 1), extracts the 80 features (Level 2), and predicts glucose, the same
  pipeline, end to end, on your own data.

It runs entirely on your laptop (`streamlit run app.py` opens it in your browser at
`localhost:8501`). That's the whole "deployment" story for a project like this: **save the
model once, load it in a small app.** No servers or GPUs required. (If you ever want a
shareable URL or a phone app, those are extra steps on top, but not needed for a BTP.)

---

## 16. REAL results on D1NAMO, and an honest reading

We ran `src/run_d1namo.py` on the **4,054 real ECG windows** (80 features each, 9 patients).
The single most important reference number first:

> **No-skill baseline:** always predicting the *average* glucose gives **RMSE = 4.19 mmol/L**
> (that's just the standard deviation of glucose). Any real model must beat 4.19 to have
> *any* skill. Glucose mean = 8.58, range 2.2 to 22.2 mmol/L.

**Protocol A, pooled 5-fold** (same patient may appear in train & test, like the paper):

| METHOD | RMSE (mmol/L) | MARD (%) |
|---|---|---|
| RandomForest | **3.901** | 45.79 |
| GradientBoosting | 4.032 | 47.36 |
| Bagging | 3.905 | 45.80 |
| PlainAverage | 3.927 | 46.16 |
| WeightedAverage | 3.927 | 46.16 |
| **Choquet (fusion)** | 3.951 | **44.19** |

**Protocol B, leave-one-subject-out** (test patient is a complete stranger):

| METHOD | RMSE (mmol/L) | MARD (%) |
|---|---|---|
| RandomForest | 4.410 | 53.92 |
| GradientBoosting | 4.431 | 52.58 |
| Bagging | 4.415 | 53.90 |
| PlainAverage | 4.399 | 53.27 |
| WeightedAverage | 4.399 | 53.27 |
| **Choquet (fusion)** | 4.409 | **51.13** |

### What these numbers honestly mean

1. **There is only weak signal in ECG-temporal features alone.** In Protocol A the best model
   (RMSE 3.90) beats the no-skill baseline (4.19) by only **~7%**. So ECG timing/shape
   statistics carry *a little* information about glucose, but not much.
2. **It does not generalise to unseen patients.** In Protocol B every method (~4.4) is
   *worse* than the 4.19 baseline, the models lean on patient-specific quirks that don't
   transfer to a new person. (Per-patient mean glucose ranges 4.1→11.2 mmol/L, so a lot of
   the variation *is* "which patient," which ECG morphology can't recover.)
3. **The Choquet fusion behaves correctly, but can't create signal that isn't there.** It
   ties the averaging baselines on RMSE and actually gives the **best MARD** in both
   protocols (44.2% and 51.1%). But it doesn't beat the best single model on RMSE, because
   our three tree-ensembles are **highly redundant** (all trained on the same 80 features),
   so there's little independent information for the fuzzy measure to combine. Fusion helps
   most when the models are *diverse*; here they aren't.
4. **This is exactly why the paper is built the way it is.** Their 1.49 mmol/L came from
   things we deliberately don't have here: **PPG** (a second modality), **ResNet
   morphological** features, **feature selection**, **9 diverse models** (3 algorithms × 3
   feature sets), and, crucially, a **temporal Choquet** that fuses each model's *recent
   history* of predictions (glucose changes slowly, so the last few minutes strongly predict
   now). Our reproduction isolates the **ECG-temporal slice** of that, and the modest result
   is the honest, expected consequence.

> **Bottom line:** the machinery (Image #1) is correct and verified; the ceiling is set by
> the input. With only ECG-temporal features, about 3.9 mmol/L is what's achievable.

---

## 17. Chapter: the temporal Choquet (`src/temporal_choquet.py`, `src/run_temporal.py`)

This is the paper's **stage 2**, the *other* place it uses the Choquet integral. (Math:
[`MATH.md` §7.5](MATH.md#75-the-temporal-choquet-paper-stage-2-eq-13-over-time).)

### 17.1 The idea in one sentence

Blood glucose changes slowly, so a model's prediction for "now" should agree with its
recent predictions, the temporal Choquet **fuses each model's last 7 predictions
(6 history + current)** to produce a smoothed, more stable value.

It's the **same Choquet integral** as Image #2, but the "sources" being combined are no
longer the 3 *models*; they're the 7 *time-points* of one model's own prediction stream.
So `temporal_choquet.py` simply **reuses `ChoquetFuser`** from `choquet.py`.

### 17.2 `temporal_choquet.py`, how it works

- `temporal_choquet_smooth(preds, timestamps, n=7, density, max_gap_min=15)` takes **one
  model's predictions in time order** and returns a smoothed stream.
- For each reading it walks backwards collecting up to `n` **consecutive-in-time**
  predictions (it stops if there's a time gap bigger than `max_gap_min`, so a window never
  jumps across an overnight gap between recording sessions), then runs the Choquet integral
  on that window.
- **The density knob is the whole story** (explained in `MATH.md` §7.5): equal density
  `1/n` makes the integral behave like a **moving average** (damps spikes, tracks the
  drift). Bigger density makes it lean toward the *maximum*, which we saw *propagates*
  spikes (bad). So we default to the average-like `1/7`.
- We verified it on a noisy demo stream: a `+4` spike (12.2) was smoothed to 8.06 with the
  true value 7.91, and its influence faded as it left the window.

### 17.3 `run_temporal.py`, does it actually help?

Honest test, leave-one-subject-out (each held-out patient is a full time-ordered sequence,
which is what smoothing needs). Per fold: train the models + multi-model fusion on the other
8 patients, predict the held-out patient's readings in time order, then compare:
- **RAW** = multi-model Choquet only (Image #2), vs
- **TEMPORAL** = smooth each model's stream first (stage 2), then multi-model fuse.

It sweeps a few density settings (the paper leaves this open) and prints RMSE/MARD for each.

> **Expectation, stated honestly up front:** our errors on D1NAMO are mostly **between-patient
> bias** (the model gets a new patient's baseline wrong), not minute-to-minute noise.
> Temporal smoothing removes *variance*, not *bias*, so on this ECG-only data we expect a
> **modest** gain at best. The big wins the paper got from stage 2 came on top of much
> stronger features (PPG + morphological) where the remaining error was more noise-like.

### 17.4 The real result (leave-one-subject-out, 4,054 windows)

| Method | RMSE (mmol/L) | MARD (%) |
|---|---|---|
| RAW (multi-model Choquet only) | 4.409 | 51.13 |
| **temporal d=1/7 (mean-like)** | **4.318** | 51.15 |
| temporal d=0.20 | 4.320 | 52.43 |
| temporal d=0.35 (more max-leaning) | 4.352 | 55.16 |

**It worked, modestly, and exactly as predicted.** Adding the temporal Choquet lowered RMSE
from **4.409 → 4.318** (a ~2% improvement). Three honest takeaways:

1. **The smoothing helps**, confirming glucose's slow drift is real, usable signal.
2. **The mean-like density (1/7) was best**, and pushing toward the max-leaning setting
   (0.35) made it *worse*, precisely what the §7.5 density analysis predicted. Theory and
   experiment agree.
3. **The gain is small (~2%) because our errors are bias-dominated**, not noise-dominated
   (we predict the wrong *baseline* for an unseen patient, and smoothing can't fix a biased
   baseline). This is consistent with our up-front expectation. The paper's larger stage-2
   gains rode on top of much stronger PPG + morphological features, where the leftover error
   was more noise-like and thus more smoothable.

**Net:** stage 2 is now built, faithful to the paper, documented, and shown to help. The
remaining gap to the paper's 1.49 mmol/L is dominated by the missing modalities (PPG) and
features (morphological / feature selection), not by the fusion math, which now matches the
paper on both axes (across models *and* across time).
