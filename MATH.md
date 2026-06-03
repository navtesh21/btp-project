# MATH.md — Every Formula in This Project, Explained from Zero

> This is the companion to `explain.md`. Where `explain.md` explains the *code*, this file
> explains the **math**. We derive every formula, define every symbol, and end with a
> **Resources** section telling you exactly where to learn each topic properly.
>
> **How to read the formulas.** They're written in LaTeX, which renders as proper math on
> GitHub and in VS Code (install the "Markdown+Math" or use the built-in preview). If you
> ever see raw `$$...$$`, just read the plain-English breakdown right below it — every
> formula has one.

---

## Table of Contents

0. [Notation: the symbols you'll see](#0-notation-the-symbols-youll-see)
1. [The base models (RF, GB, Bagging)](#1-the-base-models)
2. [Fuzzy measures (capacities) — the axioms](#2-fuzzy-measures-capacities)
3. [The Sugeno λ-measure — and where the λ-equation comes from](#3-the-sugeno-λ-measure)
4. [The Choquet integral (paper eq. 13)](#4-the-choquet-integral-paper-eq-13)
5. [Weight-based multimodel fusion (paper eqs. 14–15)](#5-weight-based-multimodel-fusion-paper-eqs-1415)
6. [The metrics: RMSE & MARD (paper eqs. 16–17)](#6-the-metrics-rmse--mard-paper-eqs-1617)
7. [Temporal statistical features — DWT + the 10 features (paper Section II-B)](#7-temporal-statistical-features--dwt--the-10-features-paper-section-ii-b)
8. [Resources — where to actually learn all of this](#8-resources--where-to-actually-learn-all-of-this)

---

## 0. Notation: the symbols you'll see

| Symbol | Said aloud | Means |
|---|---|---|
| $x_i$ | "x sub i" | the $i$-th thing in a list (e.g. the $i$-th feature, or $i$-th model) |
| $N$, $n$ | | a count (number of models, samples, etc.) |
| $\sum_{i=1}^{N}$ | "sum from i=1 to N" | add up the expression for $i=1,2,\dots,N$ |
| $\prod_{i=1}^{N}$ | "product from i=1 to N" | **multiply** the expression for $i=1,\dots,N$ |
| $X = \{x_1,\dots,x_N\}$ | "the set X" | a **set** (an unordered bag) of $N$ items |
| $2^X$ | "power set of X" | the set of **all subsets** of $X$ (there are $2^N$ of them) |
| $A \subseteq B$ | "A is a subset of B" | every element of $A$ is also in $B$ |
| $A \cup B$ | "A union B" | the set containing everything in $A$ **or** $B$ |
| $\varnothing$ | "empty set" | the set with nothing in it |
| $\hat{y}$ | "y-hat" | a **predicted** value (the hat = "estimate of") |
| $\mathbb{R}^+$ | | the non-negative real numbers ($\ge 0$) |
| $g(\cdot)$ | "g of …" | a **function** named $g$ |

---

## 1. The base models

You don't need to derive these by hand — `scikit-learn` does — but you should know the
idea behind each. All three combine many **decision trees**.

### 1.1 A regression decision tree

A tree splits the data by asking yes/no questions like "is feature $x_j < t$?". For
**regression** (predicting a number), it picks the split that most reduces the **variance**
(spread) of the target inside the two resulting groups. For a group $S$ with target values
$\{y_k\}$, the tree's prediction for that group is just the mean, and its "impurity" is:

$$\text{MSE}(S) = \frac{1}{|S|}\sum_{k \in S}\big(y_k - \bar{y}_S\big)^2, \qquad \bar{y}_S = \frac{1}{|S|}\sum_{k\in S} y_k$$

- $|S|$ = how many samples are in group $S$.
- $\bar{y}_S$ = the average target in the group (this is what the leaf predicts).
- The split chosen is the one minimizing the **weighted** MSE of the left+right children.

One tree is **high variance** — wiggle the data a little and it changes a lot. The three
ensembles each tame this differently.

### 1.2 Bagging (Bootstrap AGGregating)

Train $B$ trees, each on a **bootstrap sample** (draw $n$ rows *with replacement* from the
$n$ training rows — some rows appear twice, some not at all). Average their predictions:

$$\hat{y}_{\text{bag}}(x) = \frac{1}{B}\sum_{b=1}^{B} T_b(x)$$

- $T_b(x)$ = the prediction of the $b$-th tree for input $x$.
- Averaging $B$ noisy-but-unbiased trees cuts the variance by roughly a factor of $B$
  (exactly $1/B$ if the trees were independent). **Why it helps:** the average of many
  independent wobbles is much steadier than any one wobble.

### 1.3 Random Forest

Exactly Bagging, **plus** at each split each tree may only consider a random subset of the
features. This **decorrelates** the trees (they're forced to be different), and the average
of less-correlated trees has even lower variance. Formula is the same as Bagging's average;
the difference is purely in *how each tree is grown*.

### 1.4 Gradient Boosting

Build trees **sequentially**, each one correcting the running total. Start from a constant,
then add a small "correction tree" times a learning rate $\nu$:

$$F_0(x) = \bar{y}, \qquad F_m(x) = F_{m-1}(x) + \nu\, h_m(x)$$

- $F_m(x)$ = the model's prediction after $m$ trees.
- $\nu$ (the **learning rate**, e.g. 0.05) = how big each correction is allowed to be.
- $h_m$ = a new tree trained to predict the **negative gradient** of the loss — for the
  squared-error loss $L=\tfrac12(y-F)^2$ that gradient is simply the **residual**
  $y - F_{m-1}(x)$ (how wrong we still are). So each tree literally learns "what's left to
  fix." This is **gradient descent, but in the space of functions.**

> Bagging & RF fight **variance** (average away the noise); boosting fights **bias** (chase
> down the error). Fusing all three (Image #1) is a bet that their errors don't overlap.

---

## 2. Fuzzy measures (capacities)

This is the math object that makes the Choquet integral smarter than an average. (Paper:
the two properties listed just before eq. 13.)

Let $X = \{x_1, x_2, \dots, x_N\}$ be our $N$ information sources (here, our $N$ models).
A **fuzzy measure** (a.k.a. **capacity**) is a function

$$g : 2^X \rightarrow \mathbb{R}^+$$

that assigns a non-negative number to **every subset** of $X$ — not just to single sources.
It must satisfy:

**(P1) Boundary conditions**
$$g(\varnothing) = 0, \qquad g(X) = 1$$
"No sources ⇒ zero importance. All sources together ⇒ full importance (=1)."

**(P2) Monotonicity**
$$A \subseteq B \implies g(A) \le g(B)$$
"Adding a source to a group can never *decrease* the group's importance."

**Why this is more powerful than weights.** An ordinary weighted average assigns one weight
$w_i$ per source and assumes the group importance is just the **sum** of the members'
weights (it's *additive*). A fuzzy measure is allowed to be **non-additive**:

$$g(\{x_1,x_2\}) \ne g(\{x_1\}) + g(\{x_2\}) \quad\text{(allowed!)}$$

- If $g(\{x_1,x_2\}) < g(\{x_1\})+g(\{x_2\})$: the two sources are **redundant** (they
  overlap — counting both fully would be double-counting).
- If $g(\{x_1,x_2\}) > g(\{x_1\})+g(\{x_2\})$: the two are **complementary / synergistic**
  (together they're worth more than the sum of parts).

A weighted average literally cannot express either situation. That extra expressiveness is
the entire reason the paper uses a fuzzy measure.

---

## 3. The Sugeno λ-measure

**Problem:** a general fuzzy measure needs a value for all $2^N$ subsets — too many numbers
to choose by hand. **Sugeno's shortcut:** choose just $N$ numbers (one **density** $g_i$
per source) and let a single parameter $\lambda$ generate all the rest.

### 3.1 The defining rule

For any two **disjoint** subsets $A, B$ (no shared elements):

$$g(A \cup B) = g(A) + g(B) + \lambda\, g(A)\, g(B), \qquad \lambda > -1$$

- The first two terms are the ordinary additive part.
- The $\lambda\, g(A)\, g(B)$ term is the **interaction**: it bends additivity up or down.
- $\lambda = 0$ recovers a plain additive measure (a weighted average — see §4.4).

Writing $g_i := g(\{x_i\})$ for the **densities** (each source's standalone importance), and
applying the rule repeatedly to build up the whole set, gives the importance of *any*
subset.

### 3.2 Where the λ-equation comes from (the one our code solves)

Apply the rule to all $N$ singletons at once. A short induction on the defining rule gives
the importance of the **whole set**:

$$g(X) = g(\{x_1,\dots,x_N\}) = \frac{1}{\lambda}\left[\prod_{i=1}^{N}\big(1 + \lambda\, g_i\big) - 1\right]$$

But boundary condition (P1) demands $g(X) = 1$. Set the right side equal to 1 and multiply
through by $\lambda$:

$$\boxed{\;1 + \lambda = \prod_{i=1}^{N}\big(1 + \lambda\, g_i\big)\;}$$

**This is the exact equation `solve_lambda()` solves in `src/choquet.py`.** Reading it:

- The right side is a **polynomial in $\lambda$** of degree $N$ (multiply out the brackets).
- We want the one root with $\lambda > -1$ and $\lambda \neq 0$ (theory guarantees it's
  unique). Our code builds the polynomial's coefficients and calls `numpy.roots`.

### 3.3 The sign of λ — what it *means*

Sum the densities, $\;S = \sum_i g_i$:

| If the densities sum to… | then λ is… | interpretation |
|---|---|---|
| $S = 1$ | $\lambda = 0$ | additive ⇒ Choquet **=** weighted average |
| $S > 1$ | $-1 < \lambda < 0$ | **redundancy penalty** — overlapping strong sources don't fully add up |
| $S < 1$ | $\lambda > 0$ | **synergy bonus** — groups worth more together |

In our run the three tree-ensembles each scored competence ≈ 0.69–0.75, summing to ≈ 2.12
> 1, so $\lambda \approx -0.97$ (the redundancy regime) — sensible, because three
tree-ensembles trained on the same features really *are* redundant.

### 3.4 Building nested subsets efficiently

The Choquet integral (next section) only needs the measure of a **growing chain** of sets
$A_{(1)} \subseteq A_{(2)} \subseteq \dots \subseteq A_{(N)} = X$. We don't need all $2^N$
subsets — we add one source at a time using the defining rule:

$$g(A_{(j)}) = g(A_{(j-1)}) + g_{(j)} + \lambda\, g(A_{(j-1)})\, g_{(j)}$$

That single line is the loop body inside `_choquet_one()` in the code.

---

## 4. The Choquet integral (paper eq. 13)

### 4.1 The formula, exactly as the paper writes it

For observations $h(x_1), \dots, h(x_N)$ (here: the $N$ models' predictions for one sample),
**first sort the sources so the observations are descending**:

$$h(x_{(1)}) \ge h(x_{(2)}) \ge \dots \ge h(x_{(N)})$$

Define the nested sets $A_{(j)} = \{x_{(1)}, x_{(2)}, \dots, x_{(j)}\}$ (the top-$j$ sources)
with $A_{(0)} = \varnothing$ so $g(A_{(0)}) = 0$. Then the Choquet integral is:

$$C_g(h) = \sum_{j=1}^{N} h(x_{(j)}) \,\Big[\, g(A_{(j)}) - g(A_{(j-1)}) \,\Big]$$

**Line-by-line:**
- $h(x_{(j)})$ — the $j$-th **largest** prediction.
- $g(A_{(j)}) - g(A_{(j-1)})$ — how much the group importance **grows** when we add the
  $j$-th source. This bracket is the **effective weight** given to that prediction.
- We sum prediction × its effective weight. Because the weights come from *group*
  importances (the fuzzy measure), interactions between models are automatically baked in.

### 4.2 Equivalent "tail" form (often easier to compute)

Algebra rearranges eq. (13) into a form that uses differences of the *predictions* instead
of the measure:

$$C_g(h) = \sum_{j=1}^{N} \big[\,h(x_{(j)}) - h(x_{(j+1)})\,\big]\; g(A_{(j)}), \qquad h(x_{(N+1)}) := 0$$

Both forms give the same number; the paper uses the first, our code uses the first too.

### 4.3 The worked example from the code (verify it yourself)

Densities $g = (0.8, 0.6, 0.4)$, so $S=1.8>1 \Rightarrow \lambda = -0.9283$ (root of
$1+\lambda = (1+0.8\lambda)(1+0.6\lambda)(1+0.4\lambda)$). Predictions already sorted:
$h = (9, 7, 5)$. Build the nested measures with §3.4, then apply eq. (13):

| $j$ | source density $g_{(j)}$ | $g(A_{(j)}) = g(A_{(j-1)})+g_{(j)}+\lambda\,g(A_{(j-1)})g_{(j)}$ | weight $\Delta g$ | $h_{(j)}\cdot \Delta g$ |
|---|---|---|---|---|
| 1 | 0.8 | $0 + 0.8 + 0 = 0.800$ | 0.800 | $9(0.800)=7.200$ |
| 2 | 0.6 | $0.8+0.6-0.9283(0.8)(0.6)=0.954$ | 0.154 | $7(0.154)=1.081$ |
| 3 | 0.4 | $0.954+0.4-0.9283(0.954)(0.4)=1.000$ | 0.046 | $5(0.046)=0.228$ |

$$C_g(h) = 7.200 + 1.081 + 0.228 = \mathbf{8.51}$$

Two checks: (1) the final measure is exactly $g(A_{(3)})=1.000=g(X)$ ✓; (2) the result 8.51
lies **above** the plain mean 7.0, pulled toward the 9 that the high-density sources backed.

### 4.4 Why a weighted average is just a special case

If $\lambda = 0$ (densities sum to 1), then $g(A_{(j)}) - g(A_{(j-1)}) = g_{(j)}$, so

$$C_g(h) = \sum_{j=1}^{N} h(x_{(j)})\, g_{(j)} = \sum_{i=1}^{N} w_i\, h(x_i)$$

— an ordinary weighted average with weights $w_i = g_i$. So the Choquet integral
**contains** the weighted average and adds the ability to model interaction on top. That's
the precise sense in which it is "smarter than an average."

---

## 5. Weight-based multimodel fusion (paper eqs. 14–15)

The full paper produces $3\times3 = 9$ models (3 algorithms × 3 feature sets), runs each
through a Choquet integral, then **combines the 9 results with adaptive weights**. The
weight of model $i$ is built from its **training-set error**.

### 5.1 The per-model reliability $R_i$ (paper's $R_k$, eq. 14 context)

$$R_i = \frac{1}{\left(\sqrt{\dfrac{1}{T}\sum_{t=1}^{T}\big(\hat{r}_t - r_t\big)^2}\right)^{2}} = \frac{1}{\text{MSE}_i^{\text{train}}}$$

- $\hat{r}_t$ = model $i$'s prediction for training sample $t$; $r_t$ = the true value.
- $T$ = number of training samples.
- The thing in the big parentheses is exactly the **training RMSE**; squaring it gives the
  **MSE**. So $R_i = 1/\text{MSE}_i$ — **smaller error ⇒ larger reliability.**

### 5.2 Normalizing into weights (paper eq. 14)

$$\omega_i = \frac{R_i}{\sum_{k=1}^{9} R_k}$$

Divide each reliability by the total so the weights are non-negative and sum to 1
($\sum_i \omega_i = 1$). More reliable models automatically get a bigger share.

### 5.3 The final fused blood glucose (paper eq. 15)

$$\text{BG}_{\text{fusion}} = \sum_{k=1}^{9} \omega_k \cdot r_k$$

- $r_k$ = the (Choquet-processed) output of model $k$ on the test sample.
- A weighted sum of the models' outputs, using the reliability weights from §5.2. This is
  the final "BG output" box of the *full* paper.

> In **our Image #1 build**, `fusion.py` uses the same idea in `predict_all()`'s
> `WeightedAverage` baseline (weights = normalized densities), so you can directly compare
> "weights only" (eqs. 14–15) against "Choquet" (eq. 13) and see what the fuzzy-measure
> interaction adds.

---

## 6. The metrics: RMSE & MARD (paper eqs. 16–17)

Let $y(j)$ be the true blood glucose and $\hat{y}(j)$ the prediction, for $j=1,\dots,N$
test samples.

### 6.1 RMSE — Root-Mean-Square Error (eq. 16)

$$\text{RMSE} = \sqrt{\frac{1}{N}\sum_{j=1}^{N}\big(\hat{y}(j) - y(j)\big)^2}$$

Read inside-out: error → **square** it (positive, and punishes big misses extra) → **mean**
of the squares → **square root** (units back to mmol/L). It's the "typical error size."
Implemented in `metrics.py::rmse`.

### 6.2 MARD — Mean Absolute Relative Difference (eq. 17)

$$\text{MARD} = \frac{1}{N}\sum_{j=1}^{N}\frac{\big|\hat{y}(j) - y(j)\big|}{y(j)} \times 100\%$$

The error as a **fraction of the true value**, averaged, as a percent. This is *the*
standard accuracy number for glucose monitors, because being off by 1 mmol/L matters more
when the true reading is low. Implemented in `metrics.py::mard`. (The paper reports
MARD = 13.42%.)

---

## 7. Temporal statistical features — DWT + the 10 features (paper Section II-B)

This is the math behind `src/features_temporal.py`. The paper takes one ECG window and
produces **80 numbers** from it. Two stages: (A) split the window into 8 signals with a
**wavelet transform**, then (B) compute the **same 10 features** on each signal
(8 × 10 = 80).

### 7.A The Discrete Wavelet Transform (DWT), db4, 7 levels

**Why.** A heartbeat mixes information at many *scales* — slow baseline drift, the broad
T-wave, the sharp narrow R-spike. A single set of statistics blurs them together. The DWT
**separates a signal by scale**, so we can measure each scale on its own.

**One level of DWT.** Pass the signal $x[n]$ through a low-pass filter $g$ and a high-pass
filter $h$, then keep every 2nd sample ("downsample by 2"). This is the paper's eq. (1):

$$cA_1[n] = \sum_{k} x[2n-k]\,g[k], \qquad cD_1[n] = \sum_{k} x[2n-k]\,h[k]$$

- $cA_1$ = **approximation** coefficients (the low-frequency, smooth part).
- $cD_1$ = **detail** coefficients (the high-frequency, fast part at this scale).
- $g, h$ are the wavelet's filter taps. The paper uses **db4** (Daubechies-4), a specific
  short filter that's good at localising sharp features like R-peaks.

**Multilevel (the paper does 7).** Feed the approximation $cA_1$ back through the same two
filters to get $cA_2, cD_2$; repeat. After 7 levels you have:

$$x \;\longrightarrow\; \{\,cA_7,\; cD_7,\; cD_6,\; cD_5,\; cD_4,\; cD_3,\; cD_2,\; cD_1\,\}$$

Each $cD_k$ captures the signal's behaviour at a different scale (small $k$ = fast wiggles,
large $k$ = slow waves).

**Reconstruction from one detail level (what the code does).** To get a full-length signal
carrying *only* scale $k$, keep $cD_k$, set every other coefficient block to zero, and run
the **inverse DWT** (`pywt.waverec`). Doing this for $k=1..7$, plus keeping the original
window, gives the paper's 8 signals (eq. 2):

$$F_{\text{ECG-temporal}} = \{FE_0, FE_1, FE_2, \dots, FE_7\}$$

where $FE_0$ is the original window and $FE_k$ is the reconstruction from $cD_k$.

### 7.B The 10 features (paper: $FE_i=\{Kur, Ske, SM, SC, FD, CD, C0, PSE, KE, SE\}$)

Below, $x$ is one of the 8 signals, with $N$ samples, mean $\mu$, std $\sigma$.

**1. Kurtosis (Kur)** — how "peaky / heavy-tailed" the amplitude distribution is. ECG scores
high because of the sharp R-spikes.
$$\text{Kur} = \frac{\tfrac1N\sum_{n}(x[n]-\mu)^4}{\sigma^4} - 3 \quad(\text{the }-3\text{ makes a Gaussian score }0)$$

**2. Skewness (Ske)** — left/right asymmetry of the amplitude distribution (0 = symmetric).
$$\text{Ske} = \frac{\tfrac1N\sum_{n}(x[n]-\mu)^3}{\sigma^3}$$

**3. Signal Mobility (SM)** — *Hjorth mobility*. Roughly the signal's dominant frequency:
the std of the slope divided by the std of the signal. ($x'$ = first difference $x[n]-x[n-1]$.)
$$\text{SM} = \sqrt{\frac{\operatorname{Var}(x')}{\operatorname{Var}(x)}}$$

**4. Signal Complexity (SC)** — *Hjorth complexity*. How much the frequency content varies
(how far from a pure sine wave). It's the mobility of the slope over the mobility of the signal:
$$\text{SC} = \frac{\text{SM}(x')}{\text{SM}(x)}$$

**5. Fractal Dimension (FD)** — *Higuchi's* method. Measures how "rough / space-filling" the
curve is (a smooth line ≈ 1.0; a very jagged one approaches 2.0). It builds shortened copies
of the series at spacing $k$, measures their average length $L(k)$, and uses the fact that
for a fractal $L(k)\propto k^{-D}$; $D$ is read off the slope of $\ln L(k)$ vs $\ln(1/k)$.

**6. Correlation Dimension (CD)** — from **chaos theory** (Grassberger–Procaccia). Embed the
1-D series into $m$-dimensional vectors (delays), then count how many pairs of points lie
within distance $r$:
$$C(r) = \frac{2}{M(M-1)}\sum_{i<j}\Theta\big(r - \lVert \mathbf{v}_i-\mathbf{v}_j\rVert\big), \qquad \text{CD} = \lim_{r\to 0}\frac{\ln C(r)}{\ln r}$$
($\Theta$ = step function: 1 if inside radius $r$, else 0.) CD estimates how many independent
variables drive the signal — its "dynamical complexity."

**7. C0-complexity (C0)** — fraction of the signal's energy that is *irregular*. Take the
FFT, treat spectral components stronger than the mean power as the "regular" part, inverse-
transform that to $\tilde{x}$, and measure the leftover:
$$\text{C0} = \frac{\sum_n \lvert x[n]-\tilde{x}[n]\rvert^2}{\sum_n \lvert x[n]\rvert^2}$$

**8. Power Spectral Entropy (PSE)** — how *spread out* the signal's energy is across
frequencies. Take the power spectrum $P(f)$, normalise it to a probability distribution
$p(f)=P(f)/\sum P$, then Shannon-entropy it (a pure tone → low PSE; white noise → high PSE):
$$\text{PSE} = -\sum_f p(f)\,\log p(f)$$

**9. Kolmogorov Entropy (KE)** — the rate at which the system produces new information /
"forgets" its past; large for chaotic signals. True KE is hard to compute from finite data,
so the standard practical estimator (and what our code uses) is **Sample Entropy**: the
negative log probability that two segments similar for $m$ samples stay similar at $m{+}1$:
$$\text{SampEn}(m,r) = -\ln\frac{A}{B}$$
where $B$ = #segment-pairs matching within tolerance $r$ over length $m$, and $A$ = those
that still match at length $m{+}1$. *(We label this KE per the paper; it's an estimate — see
the note in the code.)*

**10. Shannon Entropy (SE)** — the information content of the **amplitude distribution**.
Histogram the values into bins with probabilities $p_i$:
$$\text{SE} = -\sum_i p_i\,\log_2 p_i$$
Low when values cluster tightly, high when they're spread evenly.

> **Putting it together:** 8 signals (DWT) × 10 features = **80 features per ECG window**,
> named `FE0_Kur … FE7_SE`. That's exactly the paper's ECG temporal feature set. (The paper
> adds 80 more from PPG; D1NAMO has no PPG, so we stop at 80 — see `explain.md` §13.)

---

## 7.5 The temporal Choquet (paper stage 2, eq. 13 over time)

This is the math behind `src/temporal_choquet.py`. It is the **same Choquet integral** as
§4 — only the "sources" change from *models* to *time-points of one model's prediction
stream*.

### Setup

Glucose is autocorrelated (it drifts slowly). For one model producing predictions
$\hat{p}_1, \hat{p}_2, \dots$ over time, the paper fuses each prediction with its recent
history. With window size $N=7$ (the paper's choice: 6 history + current), the sources at
time $t$ are:

$$X_t = \{\hat{p}_{t-6},\ \hat{p}_{t-5},\ \dots,\ \hat{p}_{t-1},\ \hat{p}_t\}$$

We then apply **exactly eq. (13)** from §4 to these 7 values, with a Sugeno-λ fuzzy measure
built from per-time-lag densities $g_i$:

$$\hat{p}^{\text{smooth}}_t = C_g\big(\hat{p}_{t-6}, \dots, \hat{p}_t\big) = \sum_{j=1}^{7} \hat{p}_{(j)}\Big[g(A_{(j)}) - g(A_{(j-1)})\Big]$$

(sorted descending, nested sets, as before). That's it — the temporal Choquet is the
ordinary Choquet integral applied along the time axis.

### Why the density choice decides everything (and what we pick)

With **equal** densities $g_i = c$ for all 7 lags, the measure is symmetric and the operator
is an **OWA** (ordered weighted average). The value of $c$ sets its character via λ:

| densities sum $7c$ | λ | resulting operator | effect on a spike |
|---|---|---|---|
| $= 1$ (i.e. $c=1/7$) | $0$ | plain **average** | spike spread thin, decays out of window ✅ |
| $> 1$ ($c>1/7$) | $<0$ | leans to **max** | spike **dominates** the whole window ❌ |
| $< 1$ ($c<1/7$) | $>0$ | leans to **min** | pulled toward the lowest value |

We default to $c = 1/7$ (the **average-like** setting) because a moving-average-style
Choquet correctly *damps* noisy one-off predictions while tracking the slow drift. (We
verified this: a +4 spike in the demo gets smoothed from 12.2 → 8.06, with true 7.91.)
`run_temporal.py` also sweeps a couple of other densities to confirm empirically.

### One subtlety: idempotency requires $g(X)=1$

A proper fuzzy measure has $g(X)=1$, which makes the Choquet integral **idempotent**: a
constant stream $[a,a,\dots,a]$ returns $a$ (no distortion). The Sugeno λ is solved
precisely to enforce $g(X)=1$ (§3.2). The one degenerate case is a window of length 1 (no
history yet) — there we just return the value unchanged.

---

## 8. Resources — where to actually learn all of this

Grouped by topic, easiest first within each group. **★** = best starting point.

### Machine learning & the ensemble models (RF, GB, Bagging)
- ★ **StatQuest with Josh Starmer** (YouTube) — free, gentle, visual. Watch, in order:
  "Decision Trees", "Random Forests Part 1 & 2", "Gradient Boost Part 1–4", "Bias and
  Variance". This is the single best beginner resource for §1.
- **"An Introduction to Statistical Learning" (ISLR)** by James, Witten, Hastie, Tibshirani
  — free PDF at [statlearning.com](https://www.statlearning.com/). Chapter 8 = trees,
  bagging, random forests, boosting. Has a Python edition ("ISLP").
- **scikit-learn User Guide** — [Ensemble methods](https://scikit-learn.org/stable/modules/ensemble.html).
  The exact models we use, with the math and the knobs.
- *(Deeper)* **"The Elements of Statistical Learning" (ESL)** — same authors, free PDF,
  rigorous. Chapter 10 (boosting) and 15 (random forests).

### Fuzzy measures & the Choquet integral (the core, §2–§4)
- ★ **Survey paper:** Grabisch, "Fuzzy integral in multicriteria decision making,"
  *Fuzzy Sets and Systems* (1995) — the classic, readable introduction to Sugeno measures
  and the Choquet integral. Search the title on Google Scholar for a free PDF.
- **Murofushi & Sugeno**, "An interpretation of fuzzy measures and the Choquet integral as
  an integral with respect to a fuzzy measure" (1989) — foundational.
- **Beliakov, Pradera & Calvo, "Aggregation Functions: A Guide for Practitioners"** (book) —
  Chapter on the Choquet integral; very implementation-friendly.
- **Wikipedia:** ["Choquet integral"](https://en.wikipedia.org/wiki/Choquet_integral) and
  ["Fuzzy measure theory"](https://en.wikipedia.org/wiki/Fuzzy_measure_theory) — good for
  the definitions and notation in §2–§4; cross-check with the survey above.
- **Search terms** that find tutorials: *"Sugeno lambda fuzzy measure example"*,
  *"Choquet integral classifier fusion"*, *"fuzzy integral information fusion tutorial"*.

### Signal processing — wavelets & the entropy/fractal features (§7)
- ★ **The Wavelet Tutorial** by Robi Polikar — the classic, beginner-friendly intro to the
  DWT (search "Polikar wavelet tutorial"). Read parts I–III for §7.A.
- **PyWavelets docs** — [pywavelets.readthedocs.io](https://pywavelets.readthedocs.io/) —
  `wavedec`/`waverec`, the "db4" wavelet, and multilevel decomposition (exactly our code).
- **3Blue1Brown** "But what is the Fourier Transform?" (YouTube) — builds the spectral
  intuition behind PSE and C0-complexity.
- **antropy docs** — [raphaelvallat.com/antropy](https://raphaelvallat.com/antropy/) —
  clear definitions + references for Higuchi FD, Hjorth params, spectral & sample entropy.
- **Hjorth (1970)**, "EEG analysis based on time domain properties" — original source for
  Signal Mobility & Complexity. **Higuchi (1988)** — original fractal-dimension method.
- **Grassberger & Procaccia (1983)**, "Characterization of strange attractors" — the
  correlation dimension (CD); pair with any "intro to chaos theory / strange attractors"
  explainer for intuition.

### The application (ECG/PPG → blood glucose)
- The **paper itself** (in this folder) — now that you have §1–§6, re-read its Section II.
- The paper's **code**: [github.com/SIATCAS/SFF-WCIM](https://github.com/SIATCAS/SFF-WCIM).
- **D1NAMO dataset** docs: [Zenodo record](https://zenodo.org/records/5651217) and the
  describing paper (Dubosson et al., 2018, *Informatics in Medicine Unlocked*).

### The math prerequisites (if any formula symbol felt unfamiliar)
- **Khan Academy** — "Summation notation", "Probability and statistics" (mean, variance).
- **3Blue1Brown "Essence of Linear Algebra"** & **"Essence of Calculus"** (YouTube) — for
  the gradient idea behind gradient boosting and general mathematical maturity.

### How to study this efficiently
1. Watch StatQuest's tree/forest/boosting videos (≈2 hrs) → you'll understand §1 fully.
2. Read §2–§4 here slowly, redoing the §4.3 worked example **by hand** on paper.
3. Skim the Grabisch survey for the Choquet integral's bigger picture.
4. Re-read the paper's Section II — it will now read like familiar territory.
