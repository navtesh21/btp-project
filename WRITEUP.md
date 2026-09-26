# Noninvasive Blood Glucose Estimation from ECG and PPG

### A reproduction of the Choquet-integral multimodel approach, and four ways it silently fails

**B.Tech Final Year Project — Navtesh Maken**

---

This document explains the whole project from first principles: what the problem is, what
every piece of mathematics does, what we built, what we found, and what we can and cannot
claim. It is written so that you can read it once and then explain any part of it out loud.

**Contents**

1. [The problem](#1-the-problem)
2. [The paper we reproduced](#2-the-paper-we-reproduced)
3. [The data](#3-the-data)
4. [Stage 1 — from recordings to examples](#4-stage-1--from-recordings-to-examples)
5. [Stage 2 — describing a signal with numbers](#5-stage-2--describing-a-signal-with-numbers)
6. [Stage 3 — the Choquet integral, in full](#6-stage-3--the-choquet-integral-in-full)
7. [How we grade a prediction](#7-how-we-grade-a-prediction)
8. [Results](#8-results)
9. [The four findings](#9-the-four-findings)
10. [Limitations](#10-limitations)
11. [How to run it](#11-how-to-run-it)
12. [Glossary](#12-glossary)
13. [References](#13-references)

---

## 1. The problem

**Glucose** is the sugar your blood carries as fuel. **Insulin** is the hormone that moves
it out of the blood into cells. In **Type 1 diabetes** the body makes almost none, so
glucose accumulates in the blood.

Both directions are dangerous:

| Range (mmol/L) | Name | Consequence |
|---|---|---|
| below 3.9 | hypoglycaemia | Confusion, seizure, coma — within minutes |
| 3.9 – 10.0 | normal | The target |
| above 10.0 | hyperglycaemia | Damage to nerves, eyes, kidneys, vessels — over years |

Measuring it today means breaking the skin: a **finger-prick** 4–10 times a day, or a
**continuous glucose monitor (CGM)** whose filament sits under the skin and is replaced
every 10–14 days. Roughly 590 million adults worldwide manage diabetes this way.

**The goal of this field:** read glucose from a signal we can already measure painlessly.

### Why a heartbeat might carry the information

This is not arbitrary. There are two established mechanisms:

**When glucose is low.** The body releases adrenaline. Adrenaline activates β2-adrenergic
receptors, which stimulate the Na⁺/K⁺ ATPase pump, driving potassium *into* cells and
lowering blood potassium (hypokalaemia). Potassium governs how heart-muscle cells
repolarise — reset electrically after each beat — so this stretches the recovery phase.
Visible on an ECG as a **longer QT interval** and flattened T waves.

**When glucose is high.** Sustained hyperglycaemia suppresses vagal (parasympathetic)
activity and impairs coronary microcirculation, producing **QT prolongation, ST-segment
depression** and **reduced heart-rate variability**.

> **The caveat that shapes this entire project.** These mechanisms explain *detecting an
> event* — a dangerous low or high. They do not promise that the exact glucose number can
> be read off the waveform. Detection is **classification**; reading the number is
> **regression**, and it is far harder. Published ECG classification results reach 84–94%
> accuracy; regression results consistently do not hold up.

---

## 2. The paper we reproduced

> Li, J. et al. *"Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG
> Feature Fusion and Weight-Based Choquet Integral Multimodel Approach."*
> IEEE Transactions on Neural Networks and Learning Systems, 35(10), 2024.

**Their reported results:**

| Metric | Value |
|---|---|
| RMSE | 1.49 mmol/L |
| MARD | 13.42% |
| Parkes Zone A | 80.09% |
| Parkes Zone A+B | 99.49% |

1.49 mmol/L approaches approved CGM accuracy. If it holds, it is a major result.

**Why it needed reproducing.** The authors published their code but not their data — the
recordings are private. The claim had never been independently checked on public data.

**Their three stages:**

| Stage | What it does |
|---|---|
| **1** | Record ECG and PPG, filter, cut into windows paired with glucose readings |
| **2** | Turn each window into numbers: *temporal* features (wavelet statistics) + *morphological* features (waveform shape), then select the useful ones |
| **3** | Three ML models each predict; a **Choquet integral** fuses their answers |

We implemented all three.

---

## 3. The data

### What the signals are

**ECG (electrocardiogram)** — electrodes on the skin record the electrical wave that
drives each heartbeat. One beat has a standard shape:

```
        R
        /\
       /  \          ___
 __/\_/    \        /   \___
   P        \      /  T
             \    /
              \  /
               \/
               S
```

| Part | Meaning |
|---|---|
| **P** | Atria contract |
| **QRS** | Ventricles fire (the big spike) |
| **T** | Ventricles reset (repolarisation) |
| **QT interval** | Start of QRS to end of T — how long the reset takes. **This is what glucose affects.** |
| **RR interval** | Gap between beats; its variability is *heart-rate variability* |

**PPG (photoplethysmogram)** — an LED shines into the skin; a photodetector measures
reflected light. Each heartbeat pushes a pulse of blood through, absorbing more light, so
the signal rises and falls once per beat. This is what the green light on a smartwatch
does. The *shape* of each pulse reflects vessel tone and blood properties.

**CGM** — the reference. A Dexcom sensor reports glucose every 5 minutes. This is the
"answer key".

### PhysioCGM

> *PhysioCGM: a multimodal physiological dataset for non-invasive blood glucose
> estimation.* Scientific Data, 2025. figshare record 28136294, **CC0** (public domain).

10 participants with Type 1 diabetes:

| Signal | Rate | Device |
|---|---|---|
| ECG | 250 Hz | Zephyr BioHarness (chest strap) |
| PPG (BVP) | 64 Hz | Empatica E4 (wristband) |
| EDA, skin temp, accelerometry | 4–100 Hz | both (not used here) |
| Glucose | every 5 min | Dexcom CGM |

8.6 GB of raw recordings. **It is the only open dataset carrying ECG *and* PPG against a
CGM reference** — exactly the pair the paper needs.

*(We first used D1NAMO, which is ECG-only. Half the paper's design could not be built.
That earlier study is archived in `legacy_d1namo/`.)*

### What we ended up with

| | |
|---|---|
| Paired ECG+PPG windows | **30,830** |
| Features per window | **193** |
| Participants | 10 |
| Glucose range | 2.2 – 21.5 mmol/L |
| Mean / SD | 7.17 / **2.519** mmol/L |

**The most important number is 2.519.** That is the standard deviation of glucose, and
therefore the RMSE achieved by a model that simply guesses the average every time.
**Nothing counts as learning unless it beats that.**

---

## 4. Stage 1 — from recordings to examples

### Windowing

For each CGM reading, take the **16 seconds** of ECG and PPG recorded immediately before
it. 16 s ≈ 20 heartbeats, which is the window the paper specifies.

- ECG: 16 s × 250 Hz = **4000 samples**
- PPG: 16 s × 64 Hz = **1024 samples**

One training example = (4000 ECG samples, 1024 PPG samples) → one glucose value.

### Filtering

A raw ECG contains the heartbeat plus contaminants:

| Band | Content | Action |
|---|---|---|
| below 0.5 Hz | Baseline wander (breathing, electrode drift) | remove |
| **0.5 – 40 Hz** | **The heartbeat** | **keep** |
| above 40 Hz | Muscle activity, 50/60 Hz mains | remove |

So: a 4th-order Butterworth band-pass at **0.5–40 Hz** — the paper's Level-1 step.

**PPG needs a different band.** Sampled at 64 Hz, its Nyquist limit is 32 Hz, so a 40 Hz
cutoff is not even representable. We use **0.5–8 Hz**, which keeps the pulse (~1–2 Hz) and
its first few harmonics.

### Hazard: the two recorders do not share a clock

- The Zephyr writes **local wall-clock time**: `08/06/2022 13:32:45`
- The Empatica writes a **Unix epoch**, i.e. **UTC**

Assume they agree and every PPG window is paired with glucose from five hours away.
Nothing crashes. Features compute. Models train. Results are meaningless.

**How we resolved it.** Both devices were started by hand at roughly the same moments, so
the correct offset is the one under which their session start times line up. We score
every candidate:

```
UTC-5 : 16 of 20 sessions matched
every other offset : 0-2
```

The detector **refuses to proceed** when no candidate wins decisively, rather than picking
the best guess. That refusal caught the next problem.

### Hazard: a recording that crosses daylight saving

Participant **c2s04** was recorded 27 Oct – 17 Nov 2022. US clocks went back on
**6 November**, mid-recording:

| Sessions | Count | Correct offset |
|---|---|---|
| Before 6 Nov | 7 | UTC−5 (CDT) |
| On/after 6 Nov | 15 | UTC−6 (CST) |

**No single fixed offset is correct.** The detector scored UTC−6 at 9 and UTC−5 at 6 — no
decisive winner — and halted. Picking the winner would have misaligned 7 sessions by an
hour, silently.

**Fix:** convert through a real IANA time zone (`America/Chicago`) using `zoneinfo`, so the
offset is a function of the instant and the transition applies automatically.

Only c2s04 crosses a transition; the others sit entirely within one season. Verified by
re-extracting windows under the new path: largest difference **7.3 × 10⁻¹⁴** — pure
floating-point noise.

---

## 5. Stage 2 — describing a signal with numbers

A model cannot read a waveform. 4000 raw numbers fed directly would force it to
rediscover what a heartbeat is. Instead we compute **features**: summary numbers
describing properties of the window.

### 5a. Temporal features — the wavelet transform

A heartbeat mixes a **sharp spike** (QRS, fast) with **broad waves** (P and T, slow).
Measuring the whole thing at once blurs them together. The **Discrete Wavelet Transform
(DWT)** separates them by repeatedly splitting the signal by speed.

Using the **db4 (Daubechies-4)** wavelet to **7 levels** gives 8 signals to analyse:

| Signal | Content |
|---|---|
| `FE0` | the original window |
| `FE1` | fastest detail |
| `FE2` … `FE6` | progressively slower |
| `FE7` | slowest detail |

Why it helps: a feature measuring "irregularity" means something different for the fast
QRS than for the slow T wave. Separating them lets each be described on its own terms.

### The ten features

From **each** of the 8 sub-signals we compute the same 10 measurements:

| Symbol | Name | In plain terms |
|---|---|---|
| `Kur` | Kurtosis | How spiky — are there extreme peaks? |
| `Ske` | Skewness | Is it lopsided — do peaks lean up or down? |
| `SM` | Signal mobility | How fast it wiggles on average |
| `SC` | Signal complexity | How much that wiggle rate itself changes |
| `FD` | Fractal dimension | How jagged — does detail persist on zooming in? |
| `CD` | Correlation dimension | How many independent processes drive it |
| `C0` | C0-complexity | What fraction is irregular rather than regular |
| `PSE` | Power spectral entropy | Energy spread across frequencies, or concentrated? |
| `KE` | Kolmogorov entropy | How unpredictable the next value is |
| `SE` | Shannon entropy | How much information the value distribution carries |

**8 sub-signals × 10 features = 80 per modality.**
ECG 80 + PPG 80 = **160**, exactly the paper's count.

#### Some of these in maths

**Kurtosis** (4th standardised moment) and **skewness** (3rd):

```
Ske = E[(x - mu)^3] / sigma^3
Kur = E[(x - mu)^4] / sigma^4
```

**Hjorth parameters.** With `x'` the first derivative and `x''` the second:

```
Activity   = var(x)
Mobility   = sqrt( var(x')  / var(x)  )        <- our SM
Complexity = Mobility(x') / Mobility(x)        <- our SC
```
Mobility is a mean frequency; complexity is how much that frequency varies.

**Shannon entropy.** Bin the amplitudes into a histogram with probabilities `p_i`:

```
SE = - SUM_i  p_i * log2( p_i )
```
Maximal when all values are equally likely; zero when the signal is constant.

**Power spectral entropy.** The same formula, but over the *normalised power spectrum*
`P(f)` instead of the amplitude histogram — so it measures whether energy is spread
across many frequencies or concentrated in a few.

**Correlation dimension.** Embed the signal in `m` dimensions using delayed copies, then
count how many pairs of points fall within radius `r`:

```
C(r) = (fraction of point pairs with distance < r)
CD   = lim (r -> 0)  d log C(r) / d log r
```
In practice CD is the **slope of a log–log plot**. *That slope fit is where finding 4
comes from (§9.4).*

### 5b. Morphological features — waveform shape

The paper uses a **ResNet** here. We had no GPU, and more importantly the mechanism
linking glucose to shape is already known — so we measure it directly.

| From the ECG | Why it is in the list |
|---|---|
| QT interval, **QTc** | Lengthens when glucose is low (adrenaline → hypokalaemia) |
| ST segment level | Depressed under sustained hyperglycaemia |
| T-wave amplitude, sharpness | Flattens during dysglycaemia |
| QRS duration, amplitude | Describes the main depolarisation spike |
| SDNN, RMSSD, pNN50 | Heart-rate variability — falls with high glucose |

| From the PPG | What it captures |
|---|---|
| Systolic amplitude | Pulse strength |
| Rise time, fall time | How quickly blood arrives and drains |
| Pulse width at half height | Overall pulse shape |
| Augmentation index | Strength of the reflected wave |

**Bazett's correction** makes QT comparable across heart rates:

```
QTc = QT / sqrt(RR)
```

**HRV definitions**, over the RR interval series:

```
SDNN  = standard deviation of RR intervals
RMSSD = sqrt( mean( (RR[i+1] - RR[i])^2 ) )
pNN50 = percentage of successive RR differences exceeding 50 ms
```

**This substitution is a deliberate, documented deviation from the paper** — not a silent
shortcut. Its advantage: every feature is individually citable to a mechanism. "We
measured QT because adrenaline-driven hypokalaemia prolongs repolarisation" is a stronger
answer than "the network learned something".

**Validation.** Median heart rate 74.4 bpm; median QTc **0.405 s** against a textbook
normal of 0.35–0.44 s; over 99% of windows physiologically plausible. The extraction is
measuring real anatomy, not noise.

**Total: 80 + 80 + 19 + 14 = 193 features.**

### 5c. Feature selection

More features is not better — useless ones let a model latch onto coincidences. The paper
keeps only features surviving **three independent tests**:

| Method | What it does |
|---|---|
| **UFS** (univariate filtering) | Test each feature alone: does it correlate with glucose? |
| **RFE** (recursive elimination) | Train, drop the least useful, retrain, repeat |
| **L1** (Lasso) | Fit a model penalised for using many features; useless weights go to exactly zero |

A feature is kept only if **all three** select it. In our runs this typically reduced
193 → **10**.

> **The trap we avoided.** Selection must run on **training data only, inside each fold**.
> Selecting using the whole dataset lets test answers influence which features exist, and
> silently inflates every downstream score. Our code has *no* function that selects on a
> whole dataset, because that function would be a footgun.

---

## 6. Stage 3 — the Choquet integral, in full

### Why combine models at all

Three models, each with different failure modes:

| Model | How it works |
|---|---|
| **Random Forest** | Many trees on random resamples *and* random feature subsets, averaged |
| **Gradient Boosting** | Trees trained sequentially, each correcting the last one's errors |
| **Bagging** | Many full trees on random resamples, averaged |

Where one is wrong another may be right. The question is *how* to combine.

**The analogy.** Three doctors give three opinions. You could average them. But if two
trained together and always agree, averaging counts their shared view twice. And if one is
far more experienced, they should count for more. A good rule handles **both**.

| Rule | Formula | Limitation |
|---|---|---|
| Plain average | `(a+b+c)/3` | All equally good, all independent |
| Weighted average | `w1·a + w2·b + w3·c` | Better models count more, but still assumes independence |
| **Choquet integral** | weights on **groups** | Can express overlap *and* synergy |

### 6a. Fuzzy measures

A weighted average assigns a number to each model. A **fuzzy measure** (or *capacity*)
assigns a number to **every subset**. With 3 models there are 8 subsets:

```
g({})        = 0        nothing counts for nothing
g({A})       = 0.30
g({B})       = 0.25     each model alone
g({C})       = 0.20
g({A,B})     = 0.45     <- NOT 0.30+0.25: they overlap
g({A,C})     = 0.62     <- MORE than the sum: they complement
g({B,C})     = 0.50
g({A,B,C})   = 1        everyone together = full importance
```

Two rules define a valid fuzzy measure:

1. **Boundary:** `g(∅) = 0` and `g(X) = 1`
2. **Monotonicity:** if `A ⊆ B` then `g(A) ≤ g(B)` — adding a model can never reduce importance

**The practical problem:** for `N` models there are `2^N` subsets. For 3 that is 8; for 10
it is 1024. Choosing them all by hand is impossible.

### 6b. The Sugeno λ-measure

Supply **one density `g_i` per model** — how good it is alone — and the rest is generated:

```
For disjoint A, B:

    g(A ∪ B) = g(A) + g(B) + λ · g(A) · g(B)
```

λ is fixed by requiring `g(X) = 1`:

```
    1 + λ = ∏_i ( 1 + λ · g_i )
```

This is a polynomial in λ; we solve it numerically and keep the root with `λ > −1`.

**Everything hinges on the sign of λ:**

| Condition | λ | Meaning |
|---|---|---|
| `Σ g_i = 1` | `λ = 0` | Additive. The Choquet integral becomes an ordinary **weighted average**. |
| `Σ g_i > 1` | `λ < 0` | **Overlap penalty** — strong models that agree are not double-counted |
| `Σ g_i < 1` | `λ > 0` | **Synergy bonus** — models are worth more together than apart |

### 6c. The Choquet integral

**Step 1.** Sort the predictions, largest first: `h(1) ≥ h(2) ≥ … ≥ h(N)`

**Step 2.** Walk down the sorted list, accumulating:

```
    C = Σ_j  h(j) · [ g(A_j) − g(A_{j−1}) ]

    where A_j = { the top j models }, and A_0 = ∅
```

Each prediction is weighted by **how much the group importance grew when it was added**.

Sorting is what lets group importance enter at all: the weight a prediction receives
depends on its **rank**, not its identity. And if the measure is additive (λ = 0) this
collapses exactly to a weighted average — so the Choquet integral **generalises** the
simpler rule.

### 6d. Worked example

```
densities   = (0.30, 0.25, 0.20)  ->  λ = 1.2289
predictions = ( 9.0,  7.0,  5.0)  mmol/L

      g(top 1) = 0.300    weight on 9.0 = 0.300
      g(top 2) = 0.642    weight on 7.0 = 0.342
      g(top 3) = 1.000    weight on 5.0 = 0.358

Choquet = 0.300·9 + 0.342·7 + 0.358·5 = 6.88 mmol/L
Plain average                          = 7.00 mmol/L
```

Note the weights are **not** the densities. The integral is doing something a weighted
average cannot.

### 6e. Where densities come from

We estimate each model's competence **honestly**: train it on part of the training data,
test on the part it never saw (cross-validation), and use that out-of-fold **R²**:

```
g_i = clip( R²_out-of-fold(model i),  0.01,  0.99 )
```

The clipping keeps densities inside `(0,1)` as the measure requires.

**This is where it breaks.** Read §9.3.

---

## 7. How we grade a prediction

### RMSE — root mean square error

```
RMSE = sqrt( mean( (pred − true)^2 ) )
```

The typical size of an error, in mmol/L. Squaring punishes large misses extra. Same units
as glucose, so directly interpretable.

### MARD — mean absolute relative difference

```
MARD = mean( |pred − true| / true ) × 100%
```

The error as a **percentage** of the true value. Being off by 2 when the truth is 4 is far
worse than when it is 15 — MARD captures that; RMSE does not. This is the metric glucose
device makers quote.

### R² — coefficient of determination

```
R² = 1 − SS_residual / SS_total
```

The fraction of variance explained. **This is the metric that exposes a model performing
no better than the mean** — it goes to 0, or negative, while RMSE and MARD still look
respectable. We report it precisely for that reason.

### The Parkes error grid

Plot every prediction: true glucose on x, predicted on y. A panel of 100 diabetes
clinicians divided that plane into five zones by **clinical consequence**:

| Zone | Meaning |
|---|---|
| **A** | No effect on clinical action |
| **B** | Action changes, outcome unaffected |
| **C** | Action changes, outcome affected |
| **D** | Dangerous failure to detect |
| **E** | Opposite treatment given |

Boundaries are published coordinates (Pfützner et al. 2013) in mg/dL; we convert with
`1 mmol/L = 18.018 mg/dL`.

> **Hold this thought.** Most glucose readings sit in a narrow band. So a model predicting
> a **constant** also lands most points in A and B. A high Zone A+B score does not by
> itself prove anything. §9.2 tests exactly this.

### The three split protocols

Consecutive windows from one person are extremely similar. How you split matters:

| Protocol | Description | Question it answers |
|---|---|---|
| **1. Random window** | Shuffle all windows, split at random | *Optimistic.* The same patient appears on both sides — the model can recognise the person. This is what most published work reports. |
| **2. Subject-aware** | Split so no patient is on both sides | Can it generalise **across people**? |
| **3. Leave-one-subject-out** | Train on 9, test on the 10th, rotate | The **deployment** case: a brand-new patient |

---

## 8. Results

All numbers below are from the **fused** feature set (all 193 features), 30,830 windows,
10 participants.

### Protocol 1 — random window split

| Method | R² | RMSE | MARD | Zone A | Zone A+B |
|---|---|---|---|---|---|
| RandomForest | **0.194** | 2.262 | 25.7% | 53.0% | 93.2% |
| GradientBoosting | 0.101 | 2.389 | 27.5% | 48.8% | 92.3% |
| Bagging | **0.194** | 2.262 | 25.7% | 53.1% | 93.2% |
| PlainAverage | 0.183 | 2.278 | 26.1% | 51.9% | 93.1% |
| WeightedAverage | 0.183 | 2.278 | 26.1% | 51.9% | 93.1% |
| **Choquet** | 0.149 | 2.324 | **24.9%** | 52.9% | **93.7%** |
| *MinOfModels* (control) | 0.139 | 2.338 | 24.8% | 52.9% | 93.8% |
| **NoSkillBaseline** | **−0.000** | 2.520 | 29.1% | 45.3% | 90.9% |

Models genuinely learn here: R² 0.194 against a baseline of 0.000.

### Protocol 2 — subject-aware split

| Method | R² | RMSE | MARD | Zone A | Zone A+B |
|---|---|---|---|---|---|
| RandomForest | −0.249 | 2.815 | 33.6% | 40.4% | 88.2% |
| GradientBoosting | −0.243 | 2.809 | 32.8% | 40.4% | 88.5% |
| Bagging | −0.248 | 2.814 | 33.6% | 40.4% | 88.2% |
| PlainAverage | −0.228 | 2.791 | 33.1% | 40.6% | 88.5% |
| WeightedAverage | −0.228 | 2.791 | 33.1% | 40.6% | 88.5% |
| **Choquet** | −0.223 | 2.786 | 31.5% | 41.9% | 89.4% |
| *MinOfModels* (control) | −0.226 | 2.790 | 31.3% | 42.1% | 89.5% |
| **NoSkillBaseline** | **−0.074** | **2.610** | **30.3%** | **43.7%** | **90.0%** |

**Every model is worse than guessing.** And the baseline has the **best Zone A+B**.

### The headline comparison

| | Random split | Subject-aware split |
|---|---|---|
| Choquet R² | **+0.149** | **−0.223** |
| Best model R² | +0.194 | −0.243 |
| Baseline R² | −0.000 | −0.074 |
| Verdict | Models learn | **Every model loses to guessing** |

Same data. Same model. Same code. **Only the split changed.**

---

## 9. The four findings

### 9.1 The evaluation protocol dominates the model

Moving from a random split to a subject-aware split takes R² from **+0.149 to −0.223**.
The model did not change; only the question did.

Under a random split, windows from the same patient appear in both training and test.
Because consecutive windows from one person are highly correlated, the model can identify
*the person* and recall their typical glucose — which is not the same as learning about
glucose.

This independently replicates a 2026 finding (arXiv:2608.01820) that tested five published
PPG-glucose methods: the best scored R² 0.60 under random splitting and **−0.08** under
participant-aware splitting. **We reproduce that collapse on a different signal (ECG), a
different dataset, and a different model class (fuzzy-integral fusion, not CNNs).**

### 9.2 Clinical metrics mask the failure

Under the subject-aware split:

| | R² | Zone A+B |
|---|---|---|
| Choquet | −0.223 | 89.4% |
| RandomForest | −0.249 | 88.2% |
| **NoSkillBaseline** | **−0.074** | **90.0%** |

The baseline — which explains *zero* variance by construction — has **both the best R² and
the best clinical score**. A reader shown only the Parkes numbers would see 88–90% across
the board and conclude the method works.

**Zone metrics cannot certify a model.** They must be reported alongside a baseline
computed on the same folds.

### 9.3 The fusion degenerates into a minimum operator

#### The theorem

If all `N` densities equal the same value `g`, the Sugeno λ-measure becomes **symmetric**:
it depends only on how many models are in a group, never on which ones. The Choquet
integral then reduces to an **OWA operator** with geometric weights:

```
    w_j = g · β^(j−1)        where β = 1 + λg

    j = 1 is the LARGEST prediction, j = N the smallest
```

*Derivation.* With equal densities, `g(A_j)` depends only on `|A_j| = j`. The Sugeno
recursion gives `g(A_j) = [(1+λg)^j − 1] / λ`. Therefore

```
w_j = g(A_j) − g(A_{j−1}) = [ (1+λg)^j − (1+λg)^{j−1} ] / λ = g · (1+λg)^{j−1}
```

and `Σ_j w_j = g·(β^N − 1)/(β − 1) = (β^N − 1)/λ = g(X) = 1`. ∎

Because `Σ g_i < 1 ⟹ λ > 0 ⟹ β > 1`, the weights **grow toward the smallest prediction**.
As `g → 0`, weight concentrates entirely on the minimum.

| g | λ | w(largest) | w(middle) | w(smallest) | Collapses to |
|---|---|---|---|---|---|
| 0.010 | 846.24 | 0.010 | 0.095 | **0.895** | **minimum operator** |
| 0.050 | 57.75 | 0.050 | 0.194 | 0.756 | rank-weighted OWA |
| 0.100 | 15.41 | 0.100 | 0.254 | 0.646 | rank-weighted OWA |
| 0.200 | 2.81 | 0.200 | 0.312 | 0.488 | rank-weighted OWA |
| 0.333 | 0.00 | 0.333 | 0.333 | 0.333 | **arithmetic mean** |

#### The empirical confirmation

| | Value |
|---|---|
| `corr(Choquet output, min of the 3 models)` | **0.998** |
| Mean absolute gap to `min()` | 0.036–0.042 mmol/L |
| Mean absolute gap to the **mean** | 0.27–0.31 mmol/L (7× larger) |

**The published method's distinguishing component was returning
`min(model1, model2, model3)`.**

#### Two ways this happens

**(a) A bug.** Our first runs called `cross_val_predict(model, X, y, cv=3)` with an
*integer*. scikit-learn expands an integer to `KFold` **without shuffling** — contiguous
blocks of rows. Our table is sorted by patient, so each inner "fold" was a block of whole
patients, and the density silently measured *cross-patient* generalisation. That is near
zero, so every density hit the 0.01 floor. Fixed by passing an explicit shuffled splitter;
out-of-fold R² went from **−0.16 to +0.11** and the densities came alive (RF 0.10–0.12,
GB 0.04–0.07, Bagging 0.10–0.12).

**(b) A genuine symptom.** Under the subject-aware protocol — with the *correct*
group-aware inner CV — the out-of-fold R² values were genuinely negative:

```
r2_RandomForest      = -0.160
r2_GradientBoosting  = -0.112
r2_Bagging           = -0.160
```

so the densities floored *legitimately*, and every fold was flagged `minimum-like OWA`
with `weight_on_min = 0.895`.

> **This is the deeper point.** The degeneracy is not only a bug to fix. It is a failure
> mode that **triggers exactly when the base models cannot generalise** — precisely the
> situation where a practitioner most wants the fusion to help. The method quietly
> converts "my models are weak" into "my fusion is now a min operator", with no warning.

**Novelty boundary — state this honestly.** The equivalence *symmetric measure ⟹ OWA
operator* is standard aggregation theory (Grabisch 1995; Marichal 2000) and must be cited.
The contribution here is identifying it as a **practical failure mode** of
performance-based density estimation, giving the closed-form diagnostic, and demonstrating
it in a published biomedical pipeline.

### 9.4 A standard feature library is non-deterministic

Correlation dimension is estimated as the slope of a log–log plot. The `nolds` library
fits that slope with **RANSAC** — RANdom SAmple Consensus, which repeatedly tries random
subsets — and does **not seed it**. So identical input gives different output.

| Fitting method | Distinct values from 30 identical calls |
|---|---|
| `RANSAC` (the default) | **5** |
| `poly` (least squares) | **1** |

Rebuilding one participant with the deterministic fit changed up to **72%** of
correlation-dimension values. The other **177 features were bit-identical** — the control
proving the cause was the fit, not our changes.

**Fix:** pass `fit="poly"` explicitly. Both methods agree on the modal value; only one
always returns it.

Any result computed from these features was irreproducible — nobody re-running the
pipeline, *including us*, would get the same numbers. It was found only because we tested
whether identical input gives identical output.

### Plus: the clock and DST hazards (§4)

A fifth and sixth way to get confident wrong answers, both caught by a guard written to
refuse rather than guess.

---

## 10. Limitations

**The morphological branch is not the paper's.** They use a ResNet on signal segments; we
use hand-crafted physiological features. Defensible and more interpretable, but not
identical — so this is a reproduction of the paper's *design*, not a bit-exact replication.

**Ten patients is still small.** PhysioCGM is the largest open ECG+PPG+CGM dataset
available, but ten people cannot represent the diversity of diabetes, of body types, or of
cardiac comorbidity.

**The CGM reference is itself approximate.** It reads interstitial fluid, lags blood
glucose by 5–15 minutes, and carries ~9–10% error. Our accuracy ceiling is set by our
reference.

**We did not tune hyperparameters.** Model settings follow the paper. A tuned version
might do better — though tuning honestly requires a third data split.

**Two of three protocols completed.** Leave-one-subject-out and the ECG-vs-PPG ablation
were not finished. LOSO is stricter than subject-aware, so the trend would be expected to
continue, but we do not claim a result we did not run.

**We cannot conclude the method never works.** We can conclude it does not work *on this
dataset, under honest evaluation*, and that its fusion component was inactive.

---

## 11. How to run it

```bash
# Stage 1: extract 193 features per window for all 10 subjects (~2.5 h)
python run_stage1.py                 # per-subject checkpoints; resumable

# Stages 2+3: leakage-controlled evaluation (~15 min per configuration)
python run_evaluation.py             # all configs, in priority order
python run_evaluation.py fused       # just the headline three

# The degeneracy figures (no data needed, seconds)
python -m bgfusion.figures_theory

# Rebuild the slide deck (auto-fills results)
node deck/main.js
```

### Code layout

| Path | Contents |
|---|---|
| `bgfusion/stage1_data.py` | Loading, clock/timezone alignment, filtering, windowing |
| `bgfusion/features_temporal.py` | db4 DWT + the 10 temporal features |
| `bgfusion/stage2_morphological.py` | QT, ST, T-wave, HRV, PPG pulse shape |
| `bgfusion/stage2_fusion.py` | Feature sets + UFS ∩ RFE ∩ L1 selection |
| `bgfusion/choquet.py` | Sugeno λ solver + Choquet integral |
| `bgfusion/stage3_fusion.py` | The three models, densities, `degeneracy_report` |
| `bgfusion/evaluate.py` | Three protocols, two controls, grading |
| `bgfusion/error_grid.py` | Parkes error grid zones |
| `legacy_d1namo/` | The earlier ECG-only study (archived, not deleted) |

**Three things deliberately built to fail loudly rather than guess:**

1. `detect_timezone()` raises when no candidate zone wins decisively
2. `select_features()` takes only training data — there is no whole-dataset variant
3. `degeneracy_report()` flags every fold where the fusion stops discriminating

---

## 12. Glossary

| Term | Meaning |
|---|---|
| **BVP** | Blood volume pulse — the PPG signal as the Empatica records it |
| **CGM** | Continuous glucose monitor |
| **DWT** | Discrete wavelet transform |
| **ECG** | Electrocardiogram — the heart's electrical activity |
| **Fuzzy measure** | A function assigning importance to every *subset* of sources |
| **LOSO** | Leave-one-subject-out |
| **MARD** | Mean absolute relative difference |
| **mmol/L** | Millimoles per litre — glucose units (1 mmol/L = 18.018 mg/dL) |
| **OWA** | Ordered weighted average — weights by rank, not identity |
| **Out-of-fold** | Predicted by a model that never saw that row in training |
| **PPG** | Photoplethysmogram — blood volume measured optically |
| **QT interval** | Start of QRS to end of T; how long the heart takes to reset |
| **QTc** | QT corrected for heart rate (Bazett: `QT/√RR`) |
| **RMSE** | Root mean square error |
| **Sugeno λ-measure** | A fuzzy measure built from one density per source |

---

## 13. References

1. Li, J. et al. "Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG Feature Fusion and Weight-Based Choquet Integral Multimodel Approach." *IEEE Trans. Neural Networks and Learning Systems* 35(10), 2024.
2. *PhysioCGM: a multimodal physiological dataset for non-invasive blood glucose estimation.* Scientific Data, 2025. figshare 28136294 (CC0).
3. *Reassessing the Feasibility of PPG-Based Non-Invasive Blood Glucose Level Estimation.* arXiv:2608.01820, 2026.
4. *Advances in Electrocardiogram-Based Non-Invasive Blood Glucose Monitoring Technology.* Review, 2026.
5. Parkes, J. L. et al. "A New Consensus Error Grid to Evaluate the Clinical Significance of Inaccuracies in the Estimation of Blood Glucose." *Diabetes Care* 23(8), 2000.
6. Pfützner, A. et al. "Technical Aspects of the Parkes Error Grid." *J. Diabetes Science and Technology* 7(5), 2013.
7. Eckert, B. & Agardh, C.-D. "Hypoglycaemia leads to an increased QT interval in normal men." *Clinical Physiology* 18(6), 1998.
8. Grabisch, M. "Fuzzy integral in multicriteria decision making." *Fuzzy Sets and Systems* 69(3), 1995.
9. Marichal, J.-L. "On Choquet and Sugeno integrals as aggregation functions." In *Fuzzy Measures and Integrals*, 2000.
10. Sugeno, M. *Theory of fuzzy integrals and its applications.* PhD thesis, Tokyo Institute of Technology, 1974.
11. Hjorth, B. "EEG analysis based on time domain properties." *Electroencephalography and Clinical Neurophysiology* 29(3), 1970.
12. Bazett, H. C. "An analysis of the time-relations of electrocardiograms." *Heart* 7, 1920.
