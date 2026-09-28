# Presentation Guide

### What to say on every slide, and what you will be asked

**Deck:** `nsut_deck.pptx` — 18 slides, built on the department's Mid-Term-Review
template. Speaker notes are attached to each slide and show in presenter view.
**Companion:** [`WRITEUP.md`](WRITEUP.md) — the full explanation of everything.

*(An earlier free-form 17-slide version is kept as `BTP_presentation.pptx`. The NSUT
deck is the one to present, because it follows the prescribed section structure.)*

---

## Before you start

**Total time:** about 18 minutes at a comfortable pace, plus questions.

**Fill in your roll number.** `deck/fill_nsut.py` has `ROLL = "<ROLL NO.>"` near the top —
set it and rebuild, or just edit the two table cells on slides 1 and 18 in PowerPoint.

**The one sentence you must land.** If the audience remembers nothing else:

> *"We rebuilt a published method for predicting blood sugar from heart signals, tested
> it honestly, and found it performs worse than a model that ignores the patient entirely
> and always guesses the average."*

**Four slides carry the argument: 8, 11, 12 and 14.** Slide 12 (the Parkes grid and the
prediction trace) is the strongest single slide in the deck. If you are running out of
time, cut slides 7 and 10 — never 12.

**A note on tone.** This is a negative result, and that is fine. Do not apologise for it.
A reproduction that finds where a method breaks is worth more than one that repeats a
number. Say it plainly and let the evidence do the work.

---

## Slide map

| # | Slide | Time | Notes |
|---|---|---|---|
| 1 | Title | 0:30 | Say "this is a reproduction" in the first sentence |
| 2 | Contents | 0:15 | Read the headings, do not elaborate |
| 3 | Introduction | 1:30 | End on the classification-vs-regression caveat |
| 4 | Literature Survey (1/2) | 1:15 | The paper's own comparison table |
| 5 | Gaps Identified | 1:15 | Five gaps — each became a finding |
| 6 | Aims / Objectives | 1:15 | Be explicit that their data is private |
| 7 | Literature Survey (2/2) | 1:15 | *cuttable* |
| 8 | **Problem Formulation** | 2:00 | **Start with the doctors analogy, then the maths** |
| 9 | Solution Methodology (1/2) | 1:30 | Slow down on 2.519 |
| 10 | Solution Methodology (2/2) | 1:30 | *cuttable* |
| 11 | **Results (1/4)** | 2:00 | **Define R² first. Raise the LOSO ordering yourself** |
| 12 | **Results (2/4)** | 1:30 | **Your best slide. Trace the diagonal, then the flat band. Pause** |
| 13 | Results (3/4) | 1:15 | Fewer features do better; clinical score inverted |
| 14 | **Results (4/4)** | 2:00 | **Two clues → theorem → corr 0.998** |
| 15 | Future work | 1:00 | Classification is the defensible next step |
| 16 | Expected Outputs | 1:15 | The diagnostic is reusable outside this problem |
| 17 | References | 0:15 | Do not read aloud |
| 18 | Thank You | — | Leave up, or return to slide 14 |

---

# Slide 1 — Title

**0:30** · "This project reproduces a 2024 IEEE method for estimating blood glucose from
ECG and PPG signals. The authors report 1.49 millimoles per litre, which approaches
approved CGM accuracy. My work rebuilt their method and tested whether that result
survives on data they never saw."

Say **"this is a reproduction"** in the first sentence. It frames everything.

---

# Slide 2 — Contents

**0:15** · Read the headings. Do not elaborate.

---

# Slide 3 — Introduction

**1:30** · Three beats.

"Glucose is the sugar your blood carries as fuel. In Type 1 diabetes the body makes almost
no insulin, so it builds up. Below 3.9 you get seizure and coma within minutes; above 10
you get nerve, eye and kidney damage over years.

Measuring it today means breaking the skin — a finger-prick four to ten times daily, or a
sensor filament replaced every fortnight. About 590 million adults live this way.

Now, why would the heart know? Low glucose releases adrenaline, which drives potassium
into cells. Potassium is what heart muscle uses to reset after each beat — so the ECG's QT
interval lengthens. High glucose alters ST and T-wave shape by a different route."

**Then the caveat, which sets up the whole result:**

"But note what that mechanism supports. It explains *detecting* a dangerous event — a
yes/no question, which we call classification. It does not promise you can read the exact
number, which is regression and much harder. Published classification reaches 84 to 94
percent. Regression doesn't replicate. This project attempted the number."

---

# Slide 4 — Literature Survey (1/2)

**1:15** · "This is the paper's own comparison table. The bottom row, SFF-WCIM, is the
method I reproduced — 1.49 millimoles per litre, the best of the five.

They published their code but not their data; the recordings are private. So the result
had never been checked by anyone outside their lab. That's what makes it worth
reproducing."

---

# Slide 5 — Gaps Identified

**1:15** · "Five gaps, and each one became a finding.

No independent validation, because the data is private.

The evaluation protocol isn't controlled — results come from a random window-level split,
where the same participant appears in both training and test. Windows from one person are
highly correlated, so a model can identify the *person* rather than learn about glucose.

Clinical metrics are reported without a reference point — Zone A+B is quoted as evidence
of readiness, with no baseline beside it.

The fusion operator is never audited. The densities aren't reported, and nothing checks
that the integral is still discriminating between models.

And the feature pipeline's determinism was never verified."

---

# Slide 6 — Aims / Objectives

**1:15** · "The aim, stated as a question: does the reported accuracy survive independent
reproduction under leakage-controlled evaluation?

Five objectives — rebuild all three stages; run on open data; evaluate under three
progressively stricter protocols with a baseline beside every number; audit the fusion
operator itself; and verify the pipeline is deterministic."

**Be explicit about scope:** "Their dataset is private, so this reproduces the *method* on
different data, not the experiment. And the morphological branch uses hand-crafted
physiological features rather than their ResNet, because we had no GPU. Both are
documented."

---

# Slide 7 — Literature Survey (2/2)

**1:15** · *cuttable if short*

"Three pieces of relevant work.

The first is the study I independently replicate. They re-tested five published
PPG-glucose methods: R-squared 0.60 under a random split, minus 0.08 under a
participant-aware split. And over 90 percent of predictions landed in the acceptable
clinical zones *including the baseline*.

The second is a 2026 review identifying record-level splitting as a field-wide source of
leakage.

The third bounds what I claim as new. The fact that a Choquet integral with a symmetric
measure becomes an ordered weighted average is established theory. My contribution is
showing it happens *by accident* in practice."

---

# Slide 8 — Problem Formulation

**2:00** · The densest slide. **Open with the analogy, before any symbol.**

"Three doctors give three opinions. You could average them. But two trained together and
almost always agree — averaging counts that shared training twice. And the third has
thirty years more experience, so should count for more.

A weighted average handles the second. It physically cannot handle the first, because it
only assigns importance to doctors *individually*."

**Then the mathematics:**

"So instead of a number per model, a fuzzy measure gives a number to every *subset*. The
first equation is the Sugeno rule: two groups combined equal the sum of their importances
plus a correction, lambda times their product.

Lambda isn't free — it's forced by requiring that all models together equal one. That's
the second equation.

And the third is the integral itself: sort the predictions largest first, then weight each
by how much the group importance *grew* when that model joined."

**The footnote matters:** "If the densities sum to exactly one, lambda is zero and this
reduces to an ordinary weighted average. More than one gives an overlap penalty; less
gives a synergy bonus."

---

# Slide 9 — Solution Methodology (1/2)

**1:30** · "Three levels. Level one: sixteen-second windows before each CGM reading,
band-pass filtered — 0.5 to 40 hertz for ECG, 0.5 to 8 for PPG, because PPG is sampled at
64 hertz so it can only represent up to 32.

Level two: a db4 wavelet to seven levels gives eight sub-signals per modality, ten
features each — that's the paper's 160 — plus 33 shape features.

Level three: three models, combined by the Choquet integral.

The data is PhysioCGM: ten Type-1 participants, public domain, the only open dataset with
both signals against a CGM reference."

**Slow down on the last row of the right-hand table:**

"The most important number here is 2.519. That's the standard deviation of glucose — and
therefore the error of a model that ignores the signal and always predicts the average.
It's the score for learning *nothing*. Every result after this is measured against it."

---

# Slide 10 — Solution Methodology (2/2)

**1:30** · *cuttable if short*

"Three groups of features.

The temporal statistical ones, computed on each wavelet sub-signal. Hjorth mobility is
essentially an average frequency; complexity is how much that frequency varies. Shannon
entropy measures unpredictability. Correlation dimension is the slope of a log-log plot —
remember that, it matters later.

The morphological ones, measured directly rather than learned, because we already know
which shapes matter. Corrected QT removes the dependence on heart rate.

And selection: equations five and six are the paper's own numbering, so you can follow in
the PDF. A feature is kept only if all three criteria agree — and selection runs *inside*
each fold, because selecting on the whole dataset leaks test information into the feature
choice."

---

# Slide 11 — Results (1/4)

**2:00** · **Define R-squared before showing the table.**

"R-squared is the fraction of variation explained. One is perfect. Zero means exactly as
good as predicting the average. Negative means *worse* than predicting the average. It's
the only metric here that exposes a model which has learned nothing — RMSE and the
clinical scores still look respectable.

Now the table. Under the random split — the paper's protocol — the fusion scores plus
0.149 against a baseline of zero. It genuinely learns.

Under subject-aware splitting: minus 0.223, against a baseline of minus 0.074.

Under leave-one-subject-out: minus 0.097, against minus 0.035.

Same data. Same code. Only the split changed. And in both honest protocols every method,
including the fusion, is behind the baseline."

**Raise the ordering yourself — do not wait to be asked:**

"You'll notice leave-one-out is *better* than subject-aware, even though it's stricter.
That's because it trains on nine of ten people rather than four of five — more data. The
baseline moves the same way. So I'm not claiming monotonic degradation. I'm claiming the
narrower thing: under either honest split, everything falls behind the baseline."

---

# Slide 12 — Results (2/4)

**1:30** · **Your strongest slide.**

**[trace the diagonal on the left figure]**

"This is the paper's Figure 10 — the Parkes error grid. True glucose across, predicted up.
A working model produces a cloud along this diagonal."

**[trace the horizontal band]**

"Ours is a horizontal band. Whether the person's real glucose was 4 or 20, the model says
roughly 6 to 9."

**[point to the right figure]**

"And here's the same thing over time — the paper's Figure 9. Red is the real glucose from
the CGM, swinging between 3 and 16 across seventeen days. Blue is our prediction: a flat
line at about 7.

That is what 'no better than guessing the average' looks like."

**Then the sting:**

"And look at the box in the corner of the grid. That flat band still scores 89.4 percent
in zones A and B. By the headline clinical metric, this looks like a working device."

**Pause. Let it land.**

---

# Slide 13 — Results (3/4)

**1:15** · "Every feature set, under the strictest protocol.

Every one is behind the baseline — the whole spread is 0.036 in R-squared.

Fusing the two signals is *worse* than the better one alone: PPG by itself beats the fused
set. The paper found the opposite. I don't read a 0.03 gap between two failing
configurations as evidence either way.

Two things worth noticing. Fewer features score better — 33 beats 193. When adding
information makes a model worse, it's fitting noise.

And the clinical score runs backwards. The models with the *worst* R-squared carry the
*highest* Zone A+B. Not weakly related — inverted."

---

# Slide 14 — Results (4/4)

**2:00** · "The last finding I found by accident, chasing something that looked wrong.

Two anomalies. The weighted average and the plain average were giving identical answers —
impossible if the weights differ. And every fuzzy density sat at exactly 0.01, the floor.

Here's why. If every model gets the same density, the fuzzy measure becomes *symmetric* —
it depends only on how many models are in a group, never which ones. And then the integral
collapses to this closed form: the weight on the j-th largest prediction is g times beta
to the power j minus one.

Because weak models give densities summing to less than one, lambda is positive, beta
exceeds one, and the weights *grow* toward the smallest prediction. At the density we
observed, 89.5 percent of the weight lands on the minimum.

So I checked against the actual predictions. Correlation with the minimum: 0.998. The
method's distinguishing component was returning min of the three models."

**Do not skip the last line:**

"And it's not only a bug. Under honest evaluation the models genuinely can't generalise,
so the densities floor legitimately — the fusion degenerates exactly when you most need it
to help, with no warning at all."

---

# Slide 15 — Future work

**1:00** · "Four directions. The most important is reframing from regression to
classification — the biology supports detecting dangerous lows, not reading exact numbers,
and published ECG classification reaches 84 to 94 percent.

Then personalisation, since the gap between protocols shows the models lean on
person-specific structure. Implementing the ResNet branch properly, given GPU access. And
testing the degeneracy diagnostic on other fusion pipelines — the failure mode isn't
specific to glucose."

---

# Slide 16 — Expected Outputs / Outcomes

**1:15** · "Five outcomes.

An open, reproducible implementation — everything is public.

A degeneracy theorem with a runnable diagnostic. This one is reusable by anyone using
fuzzy-integral fusion, in any domain at all.

Evidence that evaluation protocol dominates model choice here, and that clinical zone
metrics can't certify a model without a baseline.

A reproducibility defect reported in a widely-used library.

And three guards that fail loudly rather than guess — a timezone detector that refuses
when ambiguous, feature selection with no whole-dataset variant, and a per-fold degeneracy
report."

---

# Slide 17 — References

**0:15** · Do not read aloud.

---

# Slide 18 — Thank You

Leave it up, or return to slide 14 for questions.

---

# Questions you will probably get

**"Did you just implement it wrong?"**

"Possible, and I can't fully rule it out. But three things argue against it. My
morphological features match textbook physiology — median corrected QT of 0.405 seconds
against a normal range of 0.35 to 0.44. The pipeline reproduces its own results exactly
after the determinism fix. And under the random-split protocol — the one the paper uses —
my models *do* learn, scoring plus 0.194. The machinery works. It's the honest evaluation
it doesn't survive."

**"Ten patients is too few."**

"Agreed, and I say so in the limitations. But PhysioCGM is the largest open dataset with
all three required signals, and 30,830 windows is more than most published work in this
area uses. More people would strengthen the conclusion — they wouldn't reverse a negative
R-squared."

**"You didn't use their neural network."**

"That's the most substantial difference and I flag it prominently. Two things soften it.
My hand-crafted features measure exactly the quantities the biology predicts. And the
wavelet features — which I reproduced exactly as specified — perform the same as
everything else, at minus 0.102. The failure isn't localised to the part I changed."

**"So is noninvasive glucose monitoring impossible?"**

"I'm not claiming that. I'm claiming this method, on this data, under honest evaluation,
doesn't work — and that four specific mechanisms can make such a method look like it does.
Detecting *events* — dangerous highs and lows — is a different and more promising problem,
well supported by the biology."

**"What would you do next?"**

"Reframe from regression to classification. The biology supports detecting dangerous lows,
not reading exact numbers off a waveform. That's a different question with a real chance
of a positive answer."

**"Why is your accuracy so much worse than the paper's?"**

"Different data, and different evaluation. On their protocol — random splitting — I get a
positive R-squared. I simply also ran the protocols they didn't."

**"Is a negative result good enough for a final-year project?"**

"The negative result isn't the contribution — the four mechanisms are. A degeneracy
theorem with a closed-form diagnostic, evidence that split protocol dominates model
choice, proof that the field's headline clinical metric can't distinguish a real model
from a constant, and a reproducibility failure in a widely-used library. Any one of those
is reusable by someone else working on a completely different problem."

---

# Quick reference card

*Numbers you should be able to state without looking.*

| Quantity | Value |
|---|---|
| Windows | 30,830 |
| Features | 193 (80 ECG + 80 PPG wavelet, 33 shape) |
| Patients | 10 |
| **No-skill baseline RMSE** | **2.519 mmol/L** |
| Choquet R², random split | **+0.149** |
| Choquet R², subject-aware | **−0.223** |
| Choquet R², leave-one-out | −0.097 |
| Baseline R², subject-aware | −0.074 |
| Baseline Zone A+B, subject-aware | **90.0%** (the best of any method) |
| corr(Choquet, min) | **0.998** |
| Weight on minimum at g=0.01 | **89.5%** |
| CD values changed by the RANSAC fix | **up to 72%** |
| Other features changed | **0 of 177** |
| The paper's claim | 1.49 mmol/L RMSE, 99.49% Zone A+B |
| Ablation spread (5 feature sets) | 0.036 R2, **all behind the baseline** |
| Fewest features (33) vs most (193) | **-0.070 vs -0.097** - fewer is better |
| Worst R2 model's Zone A+B | **91.5%** (the highest of any) |

### If you have 5 minutes instead of 15

Slides **1, 3, 9, 11, 12, 16**. That is the framing, the problem, the baseline, the result, the picture, and the
contribution.

### If something goes wrong with the projector

The three sentences that carry the whole talk:

1. "A model that always guesses the average scores 2.519 — anything real has to beat that."
2. "Under an honest train/test split, every method we tested was *worse* than that."
3. "And the clinical metric everyone reports can't tell the difference, because a constant
   predictor scores the highest of anything we tested."
