# Predicting Blood Sugar From a Heartbeat

### A complete explanation of this project, assuming you know nothing about it

**B.Tech Final Year Project — Navtesh Maken**

---

## How to read this document

This document assumes **no prior knowledge**. Not of medicine, not of machine learning,
not of mathematics beyond school algebra. Every technical word is explained the first
time it is used.

It is written in the order the project actually happened, so you can follow the reasoning
rather than just the conclusions.

If you only have five minutes, read [Part 1](#part-1--what-this-project-was-trying-to-do)
and [Part 9](#part-9--what-we-found).

**Contents**

- [Part 1 — What this project was trying to do](#part-1--what-this-project-was-trying-to-do)
- [Part 2 — The words you need](#part-2--the-words-you-need)
- [Part 3 — What machine learning actually is](#part-3--what-machine-learning-actually-is)
- [Part 4 — The paper we copied](#part-4--the-paper-we-copied)
- [Part 5 — Getting the data](#part-5--getting-the-data)
- [Part 6 — Step one: turning recordings into examples](#part-6--step-one-turning-recordings-into-examples)
- [Part 7 — Step two: turning a squiggle into numbers](#part-7--step-two-turning-a-squiggle-into-numbers)
- [Part 8 — Step three: the Choquet integral](#part-8--step-three-the-choquet-integral)
- [Part 9 — What we found](#part-9--what-we-found)
- [Part 10 — Answering hard questions](#part-10--answering-hard-questions)
- [Part 11 — Glossary](#part-11--glossary)

---

# Part 1 — What this project was trying to do

## The problem in one paragraph

People with diabetes have to measure the sugar in their blood several times every day.
The only accurate ways to do this involve **breaking the skin** — pricking a finger, or
wearing a sensor with a filament pushed under the skin. This is painful, expensive, and
never stops. About **590 million adults** worldwide live like this.

## The idea

Your heart is affected by your blood sugar. We can measure your heart's activity
painlessly, with a strap or a smartwatch. **So could we measure the heart instead, and
work backwards to the blood sugar?**

If yes, diabetes monitoring becomes free and painless. That is why many research groups
are trying.

## What we did

In 2024 a research paper claimed to have solved a large part of this. We **rebuilt their
method from scratch** and **tested it on different data** to see whether the claim holds
up.

It did not. And the reasons why turned out to be more interesting than the original claim.

## The one-sentence answer

> We rebuilt a published method for predicting blood sugar from heart signals, tested it
> honestly, and found that **it performs worse than a "model" that ignores the patient
> entirely and always guesses the average** — plus four specific, reusable reasons why
> methods like it can look like they work when they don't.

---

# Part 2 — The words you need

Read this part once. Everything later builds on it.

## 2.1 Blood glucose

**Glucose** is a type of sugar. It is the fuel your cells burn. It comes from food,
travels in your blood, and is delivered to every cell in your body.

**"Blood glucose"** means: *how much glucose is currently in your blood.*

We measure it in **millimoles per litre**, written **mmol/L**. You do not need to know
what a millimole is. Treat "mmol/L" the same way you treat "km/h" — just the unit the
number comes in.

| Blood glucose | What it means |
|---|---|
| Below 3.9 mmol/L | **Too low.** Confusion, then seizure, then coma — within minutes. |
| 3.9 to 10.0 mmol/L | **Normal.** Where a healthy body keeps it. |
| Above 10.0 mmol/L | **Too high.** Slowly damages nerves, eyes, kidneys, blood vessels. |

Note the asymmetry: **too low kills you today; too high kills you over twenty years.**
Both matter, for different reasons.

## 2.2 Insulin and diabetes

**Insulin** is a hormone — a chemical messenger. Its job is to unlock cells so glucose can
get in. No insulin means glucose stays stuck in the blood, piling up.

**Type 1 diabetes** is when the body stops producing insulin almost entirely. The immune
system has destroyed the cells that make it. It is not caused by lifestyle and cannot be
reversed.

So a person with Type 1 diabetes must:
1. Measure their blood glucose,
2. Calculate how much insulin they need,
3. Inject it,
4. Repeat, forever, several times a day.

Step 1 is what this project is about.

## 2.3 How blood glucose is measured today

**Finger-prick test.** A small spring-loaded needle (a *lancet*) punctures a fingertip. A
drop of blood goes onto a test strip. A meter reads it. Accurate, but painful, and done
4–10 times a day.

**Continuous glucose monitor (CGM).** A patch worn on the skin with a tiny filament
sitting just underneath. It reports a glucose value **every 5 minutes**, automatically.
Much better — but still invasive, the sensor must be replaced every 10–14 days, and it is
expensive.

In this project, **the CGM is our source of truth**. It tells us what the glucose actually
was, so we can check whether our predictions were right.

## 2.4 A signal

A **signal** is just *a measurement taken repeatedly over time*.

If you measured the temperature of a room every second and wrote down the numbers, that
list of numbers is a signal.

Two words you will see:

- **Sampling rate** — how many measurements per second. Measured in **Hertz (Hz)**.
  250 Hz means 250 measurements every second.
- **Waveform** — what the signal looks like when you draw it as a line graph.

## 2.5 ECG — the electrical signal of the heart

Every heartbeat starts as a small electrical pulse that spreads through the heart muscle
and makes it squeeze. That electricity is strong enough to be detected on the skin.

An **ECG** (electrocardiogram) is a recording of that electricity. Stick electrodes on
someone's chest, and you get a signal.

One heartbeat has a shape that is the same in every healthy person, and its parts have
names:

```
                R
                /\                      <-- tall sharp spike
               /  \
              /    \        ___
    ____/\___/      \      /   \___     <-- broad slow bump
        P            \    /  T
                      \  /
                       \/
                       S
        |----------------------|
              QT interval
```

| Part | What is happening in the heart |
|---|---|
| **P** | The upper chambers (atria) squeeze |
| **QRS** | The lower chambers (ventricles) squeeze — this is the big spike |
| **T** | The ventricles electrically reset, ready for the next beat |
| **QT interval** | The time from the start of QRS to the end of T — **how long the reset takes** |
| **RR interval** | The gap from one beat to the next |

**The QT interval is the important one for us.** Remember it.

## 2.6 PPG — the light signal of blood flow

**PPG** (photoplethysmogram) works completely differently.

Shine a light into the skin. Some of it bounces back. Blood absorbs light, so when a pulse
of blood arrives with each heartbeat, *less* light comes back. Measure the returning light
and you get a signal that rises and falls once per heartbeat.

**This is exactly what the green flashing light on a smartwatch is doing.**

The *shape* of each pulse — how fast it rises, how it falls, whether you can see a small
secondary bump from blood reflecting off the body — depends on how stiff or relaxed the
blood vessels are.

## 2.7 Why the heart would know anything about blood sugar

This is not a wild guess. There are two documented biological mechanisms.

**When blood sugar goes too LOW:**

1. The body panics and releases **adrenaline**.
2. Adrenaline activates receptors that pump **potassium** out of the blood and into cells.
3. Potassium is what heart muscle cells use to reset electrically after each beat.
4. Less potassium in the blood → the reset takes longer.
5. **A longer reset = a longer QT interval, visible on the ECG.**

**When blood sugar stays too HIGH:**

Sustained high glucose damages the tiny blood vessels feeding the heart and dampens the
nerve signals that calm it. This also stretches the QT interval, pushes the ST segment
down, and makes the gaps between heartbeats more uniform than they should be.

> ### The crucial caveat
>
> These mechanisms explain **detecting an event** — "this person is dangerously low right
> now". They do **not** promise you can read the exact number off the waveform.
>
> - *"Is this person below 3.9?"* — a **yes/no** question. Called **classification**.
> - *"What exactly is this person's glucose?"* — a **number** question. Called
>   **regression**.
>
> Published work detecting events reaches 84–94% accuracy. Published work predicting the
> exact number consistently fails to hold up.
>
> **This project attempted the number.** Keep that in mind — it explains a lot of what
> follows.

---

# Part 3 — What machine learning actually is

If you already know this, skip to Part 4.

## 3.1 The basic idea

Normally you program a computer by telling it the rules:

> "If the temperature is above 30, turn on the fan."

**Machine learning is different.** You do not write the rules. Instead you show the
computer thousands of **examples**, and it works out the rules itself.

```
        EXAMPLES                              WHAT IT LEARNS
  ┌──────────────────────┐              ┌──────────────────────┐
  │ heart signal → 5.2   │              │                      │
  │ heart signal → 8.9   │  ────────>   │  some rule mapping   │
  │ heart signal → 4.1   │              │  signal to glucose   │
  │   ... 30,000 more    │              │                      │
  └──────────────────────┘              └──────────────────────┘
```

Then you give it a **new** heart signal it has never seen, and it produces a number.

## 3.2 The words

| Word | Meaning |
|---|---|
| **Example** (or *sample*) | One piece of data: one heart-signal snippet and its true glucose |
| **Feature** | One measurable property of that snippet (e.g. "the average heart rate was 74") |
| **Label** (or *target*) | The right answer we are trying to predict — here, the glucose value |
| **Model** | The thing that learns the rule |
| **Training** | Showing the model examples so it can learn |
| **Prediction** | The model's guess on a new example |

## 3.3 The single most important idea: train and test must be separate

Imagine a student who memorises the answers to a practice exam. They score 100%. Have
they learned anything? You cannot tell — until you give them **different questions**.

Machine learning has exactly this problem. A model can **memorise** its training examples
and look perfect, while having learned nothing general.

So we always split the data:

- **Training set** — the model sees these and learns from them.
- **Test set** — the model has **never seen these**. We score it only on these.

**How you make that split turns out to be the single most important decision in this
entire project.** Part 9 explains why.

## 3.4 The three models we used

All three are built from **decision trees**. A decision tree is a flowchart of yes/no
questions:

```
                Is the QT interval > 0.42s?
                  /                    \
                yes                     no
                /                        \
    Is heart rate > 80?              predict 7.1
        /          \
      yes           no
      /              \
  predict 9.2     predict 6.4
```

One tree alone is weak and easily fooled by noise. So all three of our models build
**many** trees and combine them — differently:

| Model | How it works |
|---|---|
| **Random Forest** | Builds hundreds of trees, each on a random subset of the data *and* a random subset of the features, then averages them. Randomness makes trees disagree, and averaging disagreeing trees is robust. |
| **Bagging** | Similar, but each tree sees all features. Only the data rows are randomised. |
| **Gradient Boosting** | Builds trees **one at a time**, where each new tree focuses on fixing the mistakes the previous trees made. |

Random Forest and Bagging reduce **variance** (over-reacting to noise). Gradient Boosting
reduces **bias** (systematically missing). Using all three and combining them is the
paper's bet — their strengths cover each other's weaknesses.

**How to combine their three answers is what the Choquet integral does.** That is Part 8.

---

# Part 4 — The paper we copied

## The paper

> J. Li et al., *"Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG
> Feature Fusion and Weight-Based Choquet Integral Multimodel Approach."*
> IEEE Transactions on Neural Networks and Learning Systems, volume 35, issue 10, 2024.

IEEE TNNLS is a serious, highly-regarded journal. This is not a fringe paper.

## What they claimed

| Measure | Their result | What it means |
|---|---|---|
| RMSE | **1.49 mmol/L** | Typical prediction error |
| MARD | **13.42%** | Typical error as a percentage |
| Zone A | **80.09%** | 80% of predictions clinically harmless |
| Zone A+B | **99.49%** | 99.5% clinically acceptable |

(Those measures are all explained in Part 9.)

**1.49 mmol/L approaches the accuracy of approved medical CGM devices.** If true, it is a
major result.

## Why it needed checking

The authors published their **code** but not their **data** — their recordings are
private. Nobody had ever independently tested the method on data the authors had not
chosen.

That is what a **reproduction** is: rebuild the method from the description, run it on
different data, see if the result survives.

## Their three-stage design

| Stage | What it does |
|---|---|
| **1. Collect and clean** | Record ECG and PPG. Remove noise. Cut into short windows, each paired with one glucose reading. |
| **2. Describe the signal** | Turn each window into a list of numbers (features) describing its properties. |
| **3. Predict and fuse** | Three models each predict a glucose value. A **Choquet integral** combines the three into one. |

We built all three.

---

# Part 5 — Getting the data

## 5.1 The first attempt, and why it failed

We started with a public dataset called **D1NAMO** — 9 people with Type 1 diabetes, with
ECG recordings and CGM glucose readings.

**Problem: D1NAMO has ECG only. No PPG.**

The paper's whole design uses *both* signals. With D1NAMO we could only build half of it.
We did that work anyway (it is archived in `legacy_d1namo/`), but it could never be a
fair test of the paper.

## 5.2 The dataset we actually used

> **PhysioCGM: a multimodal physiological dataset for non-invasive blood glucose
> estimation.** Scientific Data, 2025.

**10 people with Type 1 diabetes**, recorded with several devices simultaneously:

| Signal | Device | Sampling rate |
|---|---|---|
| **ECG** | Zephyr BioHarness (chest strap) | 250 Hz |
| **PPG** | Empatica E4 (wristband) | 64 Hz |
| Skin conductance, temperature, movement | both | 4–100 Hz (we did not use these) |
| **Glucose** | Dexcom CGM | every 5 minutes |

It is released under **CC0** — public domain, completely free to use. It is 8.6 GB of raw
recordings.

**This is the only open dataset in existence with ECG *and* PPG *and* a CGM reference** —
exactly the combination the paper requires.

## 5.3 What we ended up with

| | |
|---|---|
| Paired windows of ECG + PPG | **30,830** |
| Numbers describing each window | **193** |
| People | 10 |
| Glucose range | 2.2 to 21.5 mmol/L |
| Average glucose | 7.17 mmol/L |
| **Standard deviation** | **2.519 mmol/L** |

> ### The most important number in this document: 2.519
>
> **Standard deviation** measures how spread out a set of numbers is. If everyone's
> glucose were identical, it would be 0. The more they vary, the bigger it gets.
>
> Here is why it matters. Imagine the laziest possible "model": it ignores the heart
> signal completely and **always says 7.17** (the average), no matter what.
>
> That model's typical error would be exactly **2.519 mmol/L** — the standard deviation.
>
> We call this the **no-skill baseline**. It is the score you get for learning *nothing*.
> **Any real model must beat 2.519 or it has achieved nothing at all.**
>
> Most published papers in this field never report this number. We report it beside
> every single result.

---

# Part 6 — Step one: turning recordings into examples

## 6.1 Making one example

We have hours of continuous ECG and PPG, and a glucose reading every 5 minutes. We need
discrete training examples.

**For each glucose reading, take the 16 seconds of signal recorded immediately before
it.**

Why 16 seconds? That is about 20 heartbeats, which is what the paper specifies.

```
    ...ECG and PPG recorded continuously...
    
         |<--- 16 seconds --->|
    ─────────────────────────────●──────────────
                                 ↑
                         a CGM glucose reading
                              (e.g. 8.3)

    One example = (those 16 seconds of ECG,
                   those 16 seconds of PPG,
                   the number 8.3)
```

At 250 Hz, 16 seconds of ECG is **4,000 numbers**. At 64 Hz, 16 seconds of PPG is
**1,024 numbers**.

We did this for every usable glucose reading across all 10 people: **30,830 examples**.

## 6.2 Cleaning the signal

A raw ECG contains the heartbeat **plus rubbish**:

| Frequency | What it is | Keep? |
|---|---|---|
| Below 0.5 Hz | Slow drift as the person breathes and the electrode shifts | ✂ remove |
| **0.5 to 40 Hz** | **The actual heartbeat** | ✓ **keep** |
| Above 40 Hz | Electrical interference from mains power, signals from other muscles | ✂ remove |

A **filter** is a mathematical operation that removes unwanted frequencies. We keep only
0.5–40 Hz. This is exactly what the paper specifies.

**PPG needs a different range.** It is sampled at only 64 Hz, and there is a hard rule
(the *Nyquist limit*) that you can only represent frequencies up to **half** your sampling
rate — so 32 Hz maximum. A 40 Hz cutoff is not even expressible. We use **0.5–8 Hz**,
which keeps the pulse and its first few harmonics.

## 6.3 Problem: the two devices disagree about what time it is

This one nearly ruined everything, silently.

- The **Zephyr** chest strap writes times like `08/06/2022 13:32:45` — **local time**.
- The **Empatica** wristband writes a Unix timestamp — which is **UTC**, the global
  reference.

Texas in June is 5 hours behind UTC.

**If you assume they agree, every PPG measurement gets paired with a glucose reading from
five hours earlier.** Nothing crashes. The features compute. The models train. The results
look completely normal — and are meaningless.

**How we solved it.** Both devices were switched on by hand at roughly the same moments.
So the correct time offset is the one that makes their start times line up. We tested
every possibility:

```
UTC-5  : 16 of 20 sessions matched
every other offset : 0 to 2 sessions matched
```

Unambiguous. **And we wrote the code to refuse to run if no answer wins clearly**, rather
than silently picking the best guess.

That refusal caught the next problem.

## 6.4 Problem: one person's recording crosses a daylight-saving change

Person **c2s04** was recorded from **27 October to 17 November 2022**. American clocks
went back an hour on **6 November** — in the middle of their recording.

| Their sessions | Count | Correct offset |
|---|---|---|
| Before 6 November | 7 | UTC−5 |
| On or after 6 November | 15 | UTC−6 |

**There is no single correct offset for this person.**

Our checker scored UTC−6 at 9 sessions and UTC−5 at 6 — no clear winner — and **stopped
the program** rather than guessing. Had it guessed the winner, 7 sessions would have been
silently mismatched by an hour.

**The fix:** instead of a fixed offset, convert through a real time zone
(`America/Chicago`), which knows about daylight saving and applies it automatically to
each moment.

Only that one person crosses a transition. We verified the other nine were unaffected by
recomputing their features under the new code: largest difference **0.000000000000073** —
pure rounding noise.

---

# Part 7 — Step two: turning a squiggle into numbers

## 7.1 Why not just feed in the raw signal?

We have 4,000 raw numbers per ECG window. Why not hand those to the model?

Because the model would have to work out, from scratch, what a heartbeat even *is* —
where one beat ends and the next begins, which wiggle is the QRS. With 30,000 examples
that is hopeless.

Instead we compute **features**: summary numbers describing properties of the window.

A trivial feature would be "the average value". A useful one is "how long the QT interval
was".

## 7.2 The wavelet transform, explained

A heartbeat is a **mixture of fast and slow things happening at once**:

- The QRS spike is **fast** — it comes and goes in about 0.1 seconds.
- The T wave is **slow** — a broad bump lasting 0.3 seconds.

If you measure "how jagged is this signal?" on the whole window at once, the fast spike
and slow bump get blended and you learn little about either.

**A wavelet transform separates them.** It repeatedly splits the signal into a faster half
and a slower half:

```
            ORIGINAL SIGNAL
                  │
        ┌─────────┴─────────┐
      fast                slow
        │                   │
      (keep)        ┌───────┴───────┐
                  fast            slow
                    │               │
                  (keep)     ┌──────┴──────┐
                           fast          slow
                             │             │
                           (keep)       ... 7 times
```

We use the **db4 wavelet** (a specific mathematical shape called Daubechies-4), split
**7 times**, exactly as the paper specifies. That gives **8 signals** to analyse: the
original plus 7 increasingly-slow detail layers. They are labelled `FE0` (original)
through `FE7` (slowest).

## 7.3 The ten measurements

From **each** of those 8 signals we compute **the same 10 numbers**:

| Symbol | Name | In plain English |
|---|---|---|
| `Kur` | Kurtosis | How **spiky** — are there extreme peaks? |
| `Ske` | Skewness | How **lopsided** — do peaks lean up or down? |
| `SM` | Signal mobility | How **fast** it wiggles on average |
| `SC` | Signal complexity | How much that **wiggle rate itself changes** |
| `FD` | Fractal dimension | How **jagged** — does detail persist as you zoom in? |
| `CD` | Correlation dimension | How many **independent processes** drive it |
| `C0` | C0-complexity | What **fraction is irregular** rather than repeating |
| `PSE` | Power spectral entropy | Is energy **spread across frequencies** or concentrated? |
| `KE` | Kolmogorov entropy | How **unpredictable** the next value is |
| `SE` | Shannon entropy | How much **information** the values carry |

**8 signals × 10 measurements = 80 numbers per signal type.**
ECG gives 80, PPG gives 80 → **160**, exactly the paper's count.

### A few of these in actual mathematics

You can present these without deriving them, but here they are.

**Skewness and kurtosis.** Take every value in the signal. Call the average `μ` (mu) and
the standard deviation `σ` (sigma). Then:

```
Skewness  =  average of  (x − μ)³  divided by  σ³
Kurtosis  =  average of  (x − μ)⁴  divided by  σ⁴
```

The cube keeps the sign — so skewness tells you which *direction* the signal leans. The
fourth power makes everything positive and hugely amplifies extreme values — so kurtosis
detects rare big spikes.

**Hjorth parameters (our SM and SC).** Let `x′` be how fast the signal is changing (its
*derivative*) and `x″` how fast *that* is changing.

```
Mobility(x)   =  √( variance(x′) / variance(x) )
Complexity(x) =  Mobility(x′) / Mobility(x)
```

Mobility is essentially "the average frequency". Complexity is "how much that frequency
varies".

**Shannon entropy.** Sort the signal's values into bins, like a histogram. Let `pᵢ` be the
fraction of values in bin `i`. Then:

```
SE  =  − Σ  pᵢ · log₂(pᵢ)
```

This is **maximum** when all bins are equally full (totally unpredictable) and **zero**
when everything is in one bin (totally predictable). It is the same formula that underlies
all of information theory.

**Correlation dimension.** Take the signal and plot it against delayed copies of itself in
`m`-dimensional space. Count what fraction of point-pairs lie within distance `r` of each
other — call it `C(r)`. Then:

```
CD  =  the slope of  log C(r)  plotted against  log r,  as r shrinks
```

Remember that it is **a slope fitted to a graph**. That detail becomes important in
Part 9.

## 7.4 Waveform-shape features

The paper uses a **neural network** for this part. We did something different, and it is
worth being clear about why.

A neural network would need a graphics card we do not have. But more importantly, **we
already know which shapes matter** — Part 2.7 explained the biology. So rather than hope a
network rediscovers the QT interval, we measured it directly.

| From the ECG | Why |
|---|---|
| QT interval, **QTc** | Lengthens when glucose is low — the adrenaline/potassium mechanism |
| ST segment level | Pushed down by sustained high glucose |
| T-wave height and sharpness | Flattens during abnormal glucose |
| QRS width and height | Describes the main spike |
| SDNN, RMSSD, pNN50 | **Heart rate variability** — how irregular the beat spacing is |

| From the PPG | Why |
|---|---|
| Pulse height | How strong the pulse is |
| Rise time, fall time | How quickly blood arrives and drains |
| Pulse width at half height | Overall pulse shape |
| Augmentation index | Strength of the reflected wave from the body |

**QTc** deserves an explanation. The QT interval naturally gets shorter when your heart
beats faster, which would confuse any comparison. **Bazett's correction** removes that:

```
QTc  =  QT / √RR
```

where `RR` is the gap between beats. Now QTc is comparable across heart rates.

**Heart rate variability:**

```
SDNN   =  standard deviation of the gaps between beats
RMSSD  =  √( average of (gap[i+1] − gap[i])² )
pNN50  =  percentage of consecutive gaps differing by more than 50 milliseconds
```

### Did our measurements actually work?

We checked them against textbook physiology:

| Feature | Our median | Textbook normal | Verdict |
|---|---|---|---|
| Heart rate | 74.4 bpm | 60–100 | ✓ |
| **QTc** | **0.405 s** | **0.35–0.44** | ✓ |
| RR interval | 0.806 s | 0.6–1.0 | ✓ |

Over 99% of our windows fall in physiologically plausible ranges. **The extraction is
measuring real anatomy, not noise.**

**Final count: 80 (ECG wavelet) + 80 (PPG wavelet) + 19 (ECG shape) + 14 (PPG shape) =
193 features per window.**

## 7.5 Choosing which features to keep

193 features is too many. Useless features let a model latch onto coincidences.

The paper keeps only features that survive **three different tests**:

| Test | What it does |
|---|---|
| **UFS** (univariate filtering) | Check each feature alone — does it correlate with glucose at all? |
| **RFE** (recursive elimination) | Train a model, delete the least useful feature, retrain, repeat |
| **L1** (Lasso) | Train a model that is *penalised* for using many features, forcing useless ones to exactly zero |

**A feature is kept only if all three choose it.** In our runs this narrowed 193 down to
about **10**.

> ### A trap we deliberately avoided
>
> Feature selection must use **only the training data**, and must be redone separately for
> every train/test split.
>
> If you pick features by looking at the whole dataset, the test answers have influenced
> which features exist — and every score afterwards is inflated.
>
> Our code contains **no function** that selects features on a whole dataset. We left it
> out on purpose, because having it available would eventually get it used.

---

# Part 8 — Step three: the Choquet integral

This is the mathematical heart of the paper. Take it slowly; each step is small.

## 8.1 The problem being solved

Three models each produce a glucose prediction. Say:

```
Random Forest     : 9.0
Gradient Boosting : 7.0
Bagging           : 5.0
```

**What single number should we report?**

**Option 1 — the plain average.** `(9 + 7 + 5) / 3 = 7.0`

Simple, but it assumes all three models are equally good and completely independent.

**Option 2 — a weighted average.** Give better models more say:

```
0.5 × 9  +  0.3 × 7  +  0.2 × 5  =  7.6
```

Better. But still limited, and here is why.

## 8.2 What a weighted average cannot express

> **Three doctors give you three opinions.**
>
> You could average them. But:
>
> - Two of them **trained together at the same hospital** and almost always agree. If you
>   average all three equally, you are counting that shared training **twice**.
> - The third has **thirty years more experience**, so should count for more.
>
> A weighted average handles the second point. **It cannot handle the first**, because it
> only ever assigns importance to doctors *individually* — never to the relationship
> between them.

The Choquet integral fixes this by assigning importance to **every possible group**.

## 8.3 Fuzzy measures

A **fuzzy measure** (written `g`) gives a number to every possible *subset* of models. For
three models labelled A, B, C, there are 8 subsets:

```
g({})        = 0        no models, no importance
g({A})       = 0.30
g({B})       = 0.25     each model by itself
g({C})       = 0.20
g({A,B})     = 0.45     <-- NOT 0.30+0.25=0.55, because A and B overlap
g({A,C})     = 0.62     <-- MORE than 0.30+0.20=0.50, because they complement
g({B,C})     = 0.50
g({A,B,C})   = 1        everyone together = full importance
```

**That is the whole idea.** `g({A,B}) = 0.45` says "A and B together are worth less than
the sum of their parts, because they overlap". A weighted average physically cannot say
this.

Only two rules make a fuzzy measure valid:

1. **Boundaries:** `g(nothing) = 0` and `g(everything) = 1`
2. **Monotonicity:** adding a model can never *decrease* importance

**The practical problem:** with `N` models there are `2^N` subsets. For 3 that's 8. For 10
it's 1,024. You cannot choose them all by hand.

## 8.4 The Sugeno λ-measure

The Sugeno λ-measure solves this. You supply just **one number per model** — called its
**density**, `gᵢ`, meaning "how good is this model on its own" — and a formula generates
all the rest:

```
g(A ∪ B)  =  g(A) + g(B) + λ · g(A) · g(B)
```

Read that as: *the importance of two groups combined equals the sum of their individual
importances, plus a correction term.*

**λ (lambda) is that correction.** It is not chosen freely — it is forced by the rule that
everything together must equal 1:

```
1 + λ  =  ∏ᵢ (1 + λ · gᵢ)
```

(`∏` means "multiply all of these together", like `Σ` means "add all of these together".)

This is an equation in one unknown. We solve it numerically.

**The sign of λ tells you what kind of team you have:**

| If the densities... | Then λ is... | Meaning |
|---|---|---|
| sum to exactly 1 | `λ = 0` | Simply additive. **The Choquet integral becomes an ordinary weighted average.** |
| sum to more than 1 | `λ < 0` | **Overlap penalty** — strong models that agree don't get counted twice |
| sum to less than 1 | `λ > 0` | **Synergy bonus** — models are worth more together than apart |

## 8.5 The Choquet integral itself

Now we combine the predictions. Two steps.

**Step 1 — sort the predictions, largest first:**

```
h(1) = 9.0     (the largest)
h(2) = 7.0
h(3) = 5.0     (the smallest)
```

**Step 2 — walk down the sorted list, and weight each prediction by how much the group
importance grew when it was added:**

```
C  =  Σⱼ  h(j) · [ g(top j models) − g(top j−1 models) ]
```

In words: *give each prediction the weight equal to how much importance that model added
when it joined the group.*

## 8.6 A complete worked example

```
densities    = (0.30, 0.25, 0.20)
predictions  = ( 9.0,  7.0,  5.0)
```

**First, solve for λ.** Using `1 + λ = (1+0.30λ)(1+0.25λ)(1+0.20λ)`, we get:

```
λ = 1.2289
```

(Densities sum to 0.75, which is less than 1, so λ is positive — a synergy bonus, as
Part 8.4 said.)

**Now build the cumulative group importances:**

```
g(top 1) = 0.300
g(top 2) = 0.300 + 0.25 + 1.2289×0.300×0.25 = 0.642
g(top 3) = 1.000                                      (by definition)
```

**The weights are the growth at each step:**

```
weight on 9.0  =  0.300 − 0     =  0.300
weight on 7.0  =  0.642 − 0.300 =  0.342
weight on 5.0  =  1.000 − 0.642 =  0.358
```

**And the answer:**

```
Choquet  =  0.300×9.0 + 0.342×7.0 + 0.358×5.0  =  6.88 mmol/L

(a plain average would have given 7.00)
```

**Notice the weights (0.300, 0.342, 0.358) are not the densities (0.30, 0.25, 0.20).**
That difference is the Choquet integral doing something a weighted average cannot.

## 8.7 Where densities come from — and why this matters enormously

We need one density per model: "how good is this model on its own?"

We measure it **honestly**, using cross-validation:

1. Split the training data into 3 parts.
2. Train on parts 1 and 2, predict part 3. Train on 1 and 3, predict 2. And so on.
3. Every row now has a prediction made by a model that **never saw it during training**.
4. Score those predictions. That score becomes the density.

The score we use is **R²** (explained in Part 9.1). It is clipped into the range
(0.01, 0.99) because densities must sit strictly between 0 and 1.

**That clipping is where everything breaks.** Part 9.4.

---

# Part 9 — What we found

## 9.1 How we score a prediction

Four measures. You need all four, and the reason why is itself a finding.

### RMSE — root mean square error

```
RMSE = √( average of (prediction − truth)² )
```

Take every error, square it, average, square-root. **Squaring punishes large mistakes
extra.** The result is in mmol/L, so it is directly comparable to glucose values.

*Our baseline: 2.519 mmol/L.*

### MARD — mean absolute relative difference

```
MARD = average of ( |prediction − truth| / truth ) × 100%
```

The error as a **percentage of the true value**. Being wrong by 2 when the truth is 4 is
far worse than being wrong by 2 when the truth is 15. RMSE treats those identically; MARD
does not. This is the measure glucose-device manufacturers quote.

### R² — the fraction of variation explained

```
R² = 1 − (how wrong the model is) / (how wrong the baseline is)
```

| R² | Meaning |
|---|---|
| 1.0 | Perfect prediction |
| 0.5 | Explains half the variation |
| **0.0** | **Exactly as good as always guessing the average** |
| **negative** | **WORSE than always guessing the average** |

**R² is the metric that exposes a useless model.** RMSE and MARD still look respectable
when a model has learned nothing; R² goes to zero or below. This is exactly why we report
it, and why we report the baseline's score beside every model's.

### The Parkes error grid — does the error actually harm the patient?

The three measures above are mathematical. This one is clinical.

Plot every prediction: **true glucose across, predicted glucose up**. A panel of 100
diabetes doctors divided that plane into five zones by **how much harm acting on that
prediction would cause**:

| Zone | Meaning |
|---|---|
| **A** | No effect on treatment — harmless |
| **B** | Treatment changes, but the patient is fine |
| **C** | Treatment changes and the outcome is affected |
| **D** | Dangerous failure to detect a real problem |
| **E** | Exactly the wrong treatment given |

"Zone A+B percent" is **the headline clinical number** in this entire research field.

> **Hold on to this.** Most glucose readings cluster in a narrow band around normal. So a
> model that always predicts a **constant** will *still* land most of its points inside
> zones A and B. **A high Zone A+B score therefore does not prove a model works.**
> Section 9.3 tests exactly this.

## 9.2 Finding 1 — How you split the data matters more than the model

Remember Part 3.3: the model must be tested on data it has never seen. **But there are
different ways to arrange that**, and they answer different questions.

| Protocol | How it splits | The question it answers |
|---|---|---|
| **1. Random window** | Shuffle all 30,830 windows, split at random | The **same person** appears in both training and test. Can the model do well on someone it has already studied? |
| **2. Subject-aware** | Split so no person is on both sides | Can it generalise to **different people**? |
| **3. Leave-one-subject-out** | Train on 9 people, test on the 10th, rotate through all 10 | The **real-world** case: a brand-new patient |

**Protocol 1 is what most published work reports.** And here is the problem with it:
consecutive windows from the same person are extremely similar. The model can learn to
*recognise the person* and recall their typical glucose — which is not at all the same as
learning about glucose.

### The results

| | Random window | Subject-aware | Leave-one-out |
|---|---|---|---|
| Best single model R² | +0.194 | −0.243 | −0.092 |
| **Choquet fusion R²** | **+0.149** | **−0.223** | **−0.097** |
| No-skill baseline R² | −0.000 | −0.074 | −0.035 |
| Choquet RMSE | 2.324 | 2.786 | 2.639 |
| Baseline RMSE | 2.520 | 2.610 | 2.564 |
| **Beat the baseline?** | **yes** | **no** | **no** |

**Same data. Same code. Same models. Only the split changed.**

Under the random split, the model genuinely learns something (R² = +0.149). Under either
honest split, **every method — including the fusion — is worse than a model that ignores
the patient and guesses the average.**

> ### An honest note about the ordering
>
> Leave-one-out (−0.097) is **not worse** than subject-aware (−0.223), even though it is
> the stricter protocol. That might look inconsistent, so here is the reason: leave-one-out
> trains on 9 of 10 people per round, while subject-aware trains on 4 of 5. It simply has
> more data. The baseline shifts the same way (−0.035 versus −0.074).
>
> So we do **not** claim "results get monotonically worse as the test gets stricter". We
> claim the narrower thing the data actually supports: **under either honest split, every
> method falls behind the baseline.**

This independently confirms a 2026 study (arXiv:2608.01820) that re-tested five published
PPG-glucose methods and found the best scored R² = 0.60 under random splitting and −0.08
under participant-aware splitting. **We reproduce that collapse on a different signal
(ECG), a different dataset, and a different kind of model.**

## 9.3 Finding 2 — The clinical metric cannot tell a real model from a constant

Under the subject-aware split:

| Method | R² | Zone A+B |
|---|---|---|
| Choquet fusion | −0.223 | 89.4% |
| Random Forest | −0.249 | 88.2% |
| Gradient Boosting | −0.243 | 88.5% |
| **No-skill baseline** | **−0.074** | **90.0%** |

**Read that last row again.** The baseline — which predicts a constant and explains
literally zero variance — has **both the best R² and the best clinical score of anything
tested.**

Someone shown only the Zone A+B column sees 88–90% across the board and concludes the
method works.

### Why this happens

Most glucose readings sit in a narrow band. Predicting a constant near the middle of that
band already lands the large majority of points inside the acceptable zones. The grid was
designed to catch *dangerous* errors, not to detect *uselessness*.

### The picture that shows it

![Parkes error grid](figures/results/fig10_parkes_subject_aware.png)

Look at the shape of the cloud. A model that had learned anything would produce points
along the **diagonal** — low predictions for low true values, high for high.

Ours is a **horizontal band**. Whether the person's real glucose was 4 or 20, the model
says roughly 6 to 9.

**That is what "no better than guessing the average" looks like.** And it still scores
89.4% on the clinical metric.

> **The practical rule:** never report a clinical zone score without reporting a baseline
> computed on the same data beside it.

## 9.4 Finding 3 — The fusion had quietly stopped fusing

### The clues

Two things in our output did not make sense:

1. **The weighted average and the plain average gave byte-identical answers** — 3.927 and
   3.927. If the weights differed at all, that is impossible.
2. **Every model's density came out at exactly 0.01** — the floor value we clip to.

### The theorem

Suppose all `N` densities equal the same value `g`. Then the fuzzy measure becomes
**symmetric** — it depends only on *how many* models are in a group, never *which* ones.

When that happens, the Choquet integral collapses into a fixed formula:

```
wⱼ  =  g · β^(j−1),    where  β = 1 + λg

and  j = 1  is the LARGEST prediction,  j = N  the smallest
```

**Derivation** (three substitutions):

```
Step 1.  Apply the Sugeno rule j times with identical densities:
             g(top j)  =  [ (1 + λg)^j − 1 ] / λ

Step 2.  The weight is the growth at each step:
             wⱼ  =  g(top j) − g(top j−1)
                 =  [ β^j − β^(j−1) ] / λ
                 =  g · β^(j−1)

Step 3.  Check they sum to 1, as they must:
             Σⱼ wⱼ  =  g(β^N − 1)/(β − 1)  =  (β^N − 1)/λ  =  g(everything)  =  1  ✓
```

**Now the crucial consequence.** Because weak models give densities summing to less than
1, we get `λ > 0`, therefore `β > 1`, therefore **wⱼ grows as j grows** — piling weight
onto the *smallest* prediction.

| g | λ | weight on largest | on middle | **on smallest** | It becomes |
|---|---|---|---|---|---|
| **0.010** | 846.24 | 0.010 | 0.095 | **0.895** | **the minimum** |
| 0.050 | 57.75 | 0.050 | 0.194 | 0.756 | rank-weighted |
| 0.100 | 15.41 | 0.100 | 0.254 | 0.646 | rank-weighted |
| 0.200 | 2.81 | 0.200 | 0.312 | 0.488 | rank-weighted |
| 0.333 | 0.00 | 0.333 | 0.333 | 0.333 | **the plain average** |

At our observed density of 0.01, **89.5% of the weight sits on the smallest prediction**.

### Confirming it on the actual data

The theorem predicts the output should be almost exactly `min(model1, model2, model3)`. We
checked:

| | Value |
|---|---|
| Correlation between Choquet output and `min()` | **0.998** |
| Average gap to `min()` | 0.04 mmol/L |
| Average gap to the **mean** | 0.27 mmol/L (7× larger) |

> **The published method's distinguishing component — the weight-based Choquet integral —
> was returning `min(m1, m2, m3)`.**

### Two ways this happens, and the second is worse

**(a) A programming bug.** Our first runs called `cross_val_predict(model, X, y, cv=3)`
passing the number 3. The library turns a bare number into a splitter that takes
**consecutive blocks** of rows. Our table is sorted by person — so each "fold" was a block
of whole people, and the density was accidentally measuring cross-person generalisation
instead of ordinary skill. That is near zero, so every density hit the floor.

Fixed by passing a proper shuffled splitter. The out-of-fold R² went from **−0.16 to
+0.11** and the densities came alive: Random Forest 0.10–0.12, Gradient Boosting
0.04–0.07, Bagging 0.10–0.12. The integral then correctly gave the weakest model about
half the weight of the others.

**(b) A genuine symptom — and this is the deeper point.** Under the honest subject-aware
protocol, with the *correct* splitter, the out-of-fold scores were genuinely negative:

```
Random Forest      −0.160
Gradient Boosting  −0.112
Bagging            −0.160
```

So the densities floored **legitimately**, and every single fold was flagged
`minimum-like OWA` with 89.5% of weight on the minimum.

> **The degeneracy is not merely a bug to fix. It is a failure mode that triggers exactly
> when the base models cannot generalise — which is precisely the situation in which a
> practitioner most wants the fusion to help. The method silently converts "my models are
> weak" into "my fusion is now a minimum operator", with no warning of any kind.**

**Being honest about what is new here.** The mathematical fact that a symmetric measure
gives an OWA operator is standard, established theory (Grabisch 1995; Marichal 2000) and
must be cited as such. Our contribution is identifying it as a **practical failure mode**
of performance-based density estimation, providing the closed-form diagnostic, and
demonstrating it in a published biomedical pipeline.

## 9.5 Finding 4 — A standard library gives different answers every time

While verifying that a rebuild matched our earlier results, **they did not match**. The
cause was not our code.

Recall from Part 7.3 that correlation dimension is **the slope of a log-log graph**. The
library we use (`nolds`) fits that slope with **RANSAC** — a method that repeatedly tries
**random** subsets of points and keeps the best. And it does not seed the randomness.

**So identical input produces different output.**

| Fitting method | Distinct values from 30 identical calls |
|---|---|
| RANSAC (the library's default) | **5** |
| Ordinary least squares | **1** |

Rebuilding one person's data with the deterministic fit changed **up to 72%** of the
correlation-dimension values. Meanwhile **all 177 other features were bit-identical** —
which is the control proving the cause was the slope fit and nothing else we changed.

**The fix is one argument:** `fit="poly"`. Both methods agree on the typical value; only
one always returns it.

**Why this matters:** any result computed from these features was **irreproducible**.
Nobody re-running the pipeline — including us — would get the same numbers twice. We only
found it because we tested whether identical input gives identical output, which almost
nobody does.

## 9.6 Finding 5 — Adding a second signal does not help

The paper's own ablation showed ECG alone at 1.56, PPG alone at 1.82, and both fused at
1.49 — fusion best. We tested the same thing:

| Feature set | Features | R² | RMSE |
|---|---|---|---|
| PPG only | 94 | −0.075 | 2.612 |
| Fused (ECG + PPG) | 193 | −0.097 | 2.639 |
| Temporal only | 160 | −0.102 | 2.645 |
| ECG only | 99 | −0.106 | 2.650 |
| **No-skill baseline** | — | **−0.035** | **2.564** |

Two observations:

1. **Fusing the two signals is *worse* than the better one alone.** PPG-only (−0.075)
   beats the fused set (−0.097). The paper found the opposite.
2. **Every feature set lands within 0.031 R² of every other, and all are behind the
   baseline.** Halving the feature count moves the number by 0.009. Dropping 33 features
   moves it by 0.005.

**That flatness is the real result.** When feature choice barely moves the number and
nothing beats a constant predictor, the ranking between configurations carries no
information — it is variation around a null. We therefore do **not** claim "PPG is better
than ECG" from a 0.03 gap between two failing models.

## 9.7 The findings together

| # | Finding | The evidence |
|---|---|---|
| **1** | The evaluation protocol dominates the model | R² +0.149 → −0.223 on identical data |
| **2** | Clinical metrics mask failure | A constant predictor scores best on **both** R² and Zone A+B |
| **3** | The fusion degenerates into `min()` | `corr = 0.998`, in every configuration tested |
| **4** | A standard library is non-deterministic | Up to 72% of values change between identical runs |
| **5** | The second signal adds nothing | All feature sets within 0.031 R², all behind the baseline |

Plus the two data hazards from Part 6 — mismatched clocks and a daylight-saving
transition — both caught by checks written to **refuse rather than guess**.

**The unifying point:** at five different layers of the same pipeline — the data
alignment, the feature library, the fusion operator, the evaluation protocol, and the
reporting metric — this method produced confident, plausible numbers that were wrong,
while appearing to work perfectly.

---

# Part 10 — Answering hard questions

Likely questions, with honest answers.

**"Did you just fail to implement it properly?"**

Possible, and we cannot fully rule it out. But: our morphological features match textbook
physiology (QTc median 0.405 s against a normal range of 0.35–0.44); our pipeline
reproduces its own results exactly after the determinism fix; and under the random-split
protocol — the one the paper uses — our models *do* learn (R² = +0.194). The machinery
works. It is the honest evaluation it does not survive.

**"Isn't 10 people too few?"**

Yes, and we say so. But PhysioCGM is the **largest open dataset in existence** with all
three required signals, and 30,830 windows is substantially more than most published work
in this area uses. More people would strengthen the conclusion; they would not reverse a
negative R².

**"You didn't use their neural network. Isn't that the problem?"**

It is the most substantial difference, and we flag it prominently. Two things soften it:
our hand-crafted features measure exactly the quantities the biology predicts, and the
*wavelet* features — which we reproduced exactly as specified — perform the same as
everything else (−0.102). The failure is not localised to the part we changed.

**"Why is your accuracy so much worse than the paper's?"**

Different data, and different evaluation. On their protocol (random splitting) we get a
positive R². We simply also ran the protocols they did not.

**"So is noninvasive glucose monitoring impossible?"**

We are not claiming that. We are claiming that **this method, on this data, under honest
evaluation, does not work** — and that four specific mechanisms can make such a method
look like it does. Detecting *events* (hypo/hyper) is a different and more promising
problem, well supported by the biology in Part 2.7.

**"What would you do next?"**

Reframe from regression to classification. The biology supports detecting dangerous lows,
not reading exact numbers. That is a different question with a real chance of a positive
answer.

## What we cannot claim

- That the method never works — only that it does not here, under honest evaluation.
- That PPG is worse than ECG — the gap is noise between two failing configurations.
- That our morphological features are equivalent to the paper's neural network.
- That 10 people represent the diversity of diabetes.

---

# Part 11 — Glossary

| Term | Meaning |
|---|---|
| **Bagging** | A model that builds many trees on random data samples and averages them |
| **Baseline (no-skill)** | A "model" that always predicts the average; the score to beat |
| **BVP** | Blood volume pulse — the PPG signal as the Empatica device records it |
| **CGM** | Continuous glucose monitor — the under-skin sensor giving our true values |
| **Choquet integral** | A way of combining predictions that accounts for overlap between models |
| **Classification** | Predicting a category (e.g. "low / normal / high") |
| **Cross-validation** | Repeatedly training on part of the data and testing on the rest |
| **Density** (fuzzy) | A number saying how good one model is on its own |
| **DWT** | Discrete wavelet transform — splits a signal into fast and slow layers |
| **ECG** | Electrocardiogram — a recording of the heart's electrical activity |
| **Feature** | One measurable property of a signal window |
| **Fuzzy measure** | A function giving an importance to every *group* of models |
| **Gradient Boosting** | A model that builds trees in sequence, each fixing the last one's errors |
| **Hz (Hertz)** | Measurements per second |
| **LOSO** | Leave-one-subject-out — train on all people but one, test on that one |
| **MARD** | Mean absolute relative difference — error as a percentage of the true value |
| **mmol/L** | The unit of blood glucose (1 mmol/L = 18.018 mg/dL) |
| **OWA** | Ordered weighted average — weights depend on rank, not on which model |
| **Out-of-fold** | A prediction made by a model that never saw that row during training |
| **Overfitting** | Memorising the training data instead of learning a general rule |
| **Parkes error grid** | A chart scoring predictions by how much clinical harm they'd cause |
| **PPG** | Photoplethysmogram — blood flow measured with light |
| **QT interval** | Time from the start of QRS to the end of T; how long the heart takes to reset |
| **QTc** | QT corrected for heart rate, via `QT/√RR` |
| **R²** | Fraction of variation explained; 0 = no better than the average, negative = worse |
| **Random Forest** | A model using many trees on random data *and* random feature subsets |
| **Regression** | Predicting a number (as opposed to a category) |
| **RMSE** | Root mean square error — typical error size, in the original units |
| **Sampling rate** | How many measurements per second |
| **Standard deviation** | A measure of how spread out a set of numbers is |
| **Sugeno λ-measure** | A fuzzy measure generated from one density per model |
| **Training / test set** | Data the model learns from / data used only to score it |

---

# References

1. Li, J. et al. "Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG Feature Fusion and Weight-Based Choquet Integral Multimodel Approach." *IEEE Transactions on Neural Networks and Learning Systems* 35(10), 2024.
2. *PhysioCGM: a multimodal physiological dataset for non-invasive blood glucose estimation.* Scientific Data, 2025. figshare 28136294 (CC0).
3. *Reassessing the Feasibility of PPG-Based Non-Invasive Blood Glucose Level Estimation.* arXiv:2608.01820, 2026.
4. *Advances in Electrocardiogram-Based Non-Invasive Blood Glucose Monitoring Technology.* Review, 2026.
5. Parkes, J. L. et al. "A New Consensus Error Grid to Evaluate the Clinical Significance of Inaccuracies in the Estimation of Blood Glucose." *Diabetes Care* 23(8), 2000.
6. Pfützner, A. et al. "Technical Aspects of the Parkes Error Grid." *Journal of Diabetes Science and Technology* 7(5), 2013.
7. Eckert, B. & Agardh, C.-D. "Hypoglycaemia leads to an increased QT interval in normal men." *Clinical Physiology* 18(6), 1998.
8. Grabisch, M. "Fuzzy integral in multicriteria decision making." *Fuzzy Sets and Systems* 69(3), 1995.
9. Marichal, J.-L. "On Choquet and Sugeno integrals as aggregation functions." In *Fuzzy Measures and Integrals*, 2000.
10. Sugeno, M. *Theory of fuzzy integrals and its applications.* PhD thesis, Tokyo Institute of Technology, 1974.
11. Hjorth, B. "EEG analysis based on time domain properties." *Electroencephalography and Clinical Neurophysiology* 29(3), 1970.
12. Bazett, H. C. "An analysis of the time-relations of electrocardiograms." *Heart* 7, 1920.
