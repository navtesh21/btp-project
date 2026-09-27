# Presentation Guide

### What to say on every slide, and what you will be asked

**Deck:** `BTP_presentation.pptx` — 17 slides (speaker notes are in presenter view)
**Companion:** [`WRITEUP.md`](WRITEUP.md) — the full explanation of everything

---

## Before you start

**Total time:** about 16 minutes at a comfortable pace, plus questions.

**The one sentence you must land.** If the audience remembers nothing else:

> *"We rebuilt a published method for predicting blood sugar from heart signals, tested
> it honestly, and found it performs worse than a model that ignores the patient entirely
> and always guesses the average."*

**Your strongest slide is number 9** (the scatter plot). If you are running out of time,
cut slides 6 and 14 — never slide 9.

**A note on tone.** This is a negative result, and that is fine. Do not apologise for it.
A reproduction that finds where a method breaks is worth more than one that repeats a
number. Say it plainly and let the evidence do the work.

---

# Slide 1 — Title

> *"Can your heartbeat tell us your blood sugar?"*

**Time: 30 seconds**

### What to say

"People with diabetes have to measure the sugar in their blood several times a day, and
every accurate way of doing it involves breaking the skin.

My project asks whether we could measure something painless instead — the electrical
activity of the heart — and work backwards to the blood sugar.

Specifically, I rebuilt a 2024 method from a top IEEE journal and tested whether its
results hold up on data the original authors never saw."

### Do not

Don't give the conclusion yet. Let slides 2–5 set up the problem first.

---

# Slide 2 — The problem

> *"Measuring blood glucose means breaking the skin, several times a day, for life"*

**Time: 1 minute 30 seconds**

### What to say

"Glucose is the sugar your blood carries as fuel. Insulin is the hormone that moves it out
of the blood and into your cells. In Type 1 diabetes the body produces almost none, so
glucose builds up.

Both directions are dangerous, and asymmetrically so. Below 3.9 millimoles per litre you
get confusion, then seizure, then coma — within minutes. Above 10 you get nerve, eye and
kidney damage over years.

Today that's managed either by pricking a finger four to ten times a day, or by wearing a
sensor with a filament under the skin that's replaced every fortnight. About 590 million
adults worldwide live this way."

**[point to the right-hand box]**

"Now, why would the heart know anything about blood sugar? This isn't a guess — there are
two documented mechanisms.

When glucose goes low, the body releases adrenaline. Adrenaline drives potassium into
cells. Potassium is what heart muscle uses to reset electrically after each beat. Less
potassium means a slower reset, which shows up on the ECG as a longer QT interval.

When glucose stays high, it dampens the nerves that calm the heart and damages the small
vessels feeding it — which changes the same parts of the waveform."

**[point to the amber box — this is important]**

"But note carefully what the mechanism supports. It explains *detecting an event* — 'this
person is dangerously low right now.' That's a yes/no question, which we call
classification.

It does not promise you can read the *exact number* off the waveform. That's regression,
and it's much harder. Published classification work reaches 84 to 94 percent accuracy.
Regression consistently doesn't hold up.

This project attempted the number. Remember that — it explains a lot of what follows."

### Likely question

**"Why not just improve the CGM instead?"** — People are. This is a parallel line of
research aiming at zero-cost, zero-consumable monitoring using sensors people already
wear.

---

# Slide 3 — The paper

> *"A 2024 IEEE paper reports near-clinical accuracy by fusing two signals and three models"*

**Time: 1 minute 30 seconds**

### What to say

"The paper I reproduced is from IEEE Transactions on Neural Networks and Learning
Systems — a serious, highly-regarded journal.

They report an RMSE of 1.49 millimoles per litre. RMSE is just the typical size of a
prediction error, in the same units as glucose. 1.49 approaches the accuracy of approved
medical CGM devices. If it holds, it's a major result.

They also report 99.5 percent of predictions in the clinically acceptable zones, which
sounds close to device-ready."

**[point to the three stage boxes]**

"Their method has three stages. Stage one: record both signals, filter out noise, cut them
into 16-second windows, each paired with one glucose reading.

Stage two: turn each window into 193 numbers describing its properties.

Stage three: three machine-learning models each make a prediction, and a mathematical tool
called a Choquet integral combines them into one answer.

Stage three is where the paper's novelty sits."

### Why reproduce it

"The authors published their code but not their data — their recordings are private. So
nobody had ever independently checked the method on data the authors hadn't chosen.
That's what a reproduction is for."

---

# Slide 4 — What we built

> *"We rebuilt all three stages and ran them on the largest open ECG+PPG+CGM dataset"*

**Time: 1 minute 30 seconds**

### What to say

"I rebuilt all three stages from the paper's description and ran them on PhysioCGM — ten
people with Type 1 diabetes, recorded with a chest strap for ECG, a wristband for PPG, and
a Dexcom CGM for the true glucose values. It's public domain and free.

It's the only open dataset in existence carrying both signals against a CGM reference,
which is exactly what this paper needs.

That gave me 30,830 paired windows, each described by 193 numbers."

**[point to the dark box at the bottom — slow down here]**

"The most important number on this slide is the last one: 2.519.

That's the standard deviation of glucose in our dataset. Here's why it matters. Imagine
the laziest possible model — it ignores the heart signal completely and always says 7.17,
the average, no matter what.

That model's typical error would be exactly 2.519.

So 2.519 is the score you get for learning *nothing*. I call it the no-skill baseline, and
any real model has to beat it or it has achieved nothing at all.

Most papers in this field never report this number. I report it beside every single
result."

> **This is the conceptual foundation for everything after. Make sure they have it before
> you move on.**

---

# Slide 5 — The mathematics

> *"The Choquet integral assigns importance to GROUPS of models, not just to each one"*

**Time: 2 minutes** — the densest slide, take it slowly

### Open with the analogy (do this first, before the formulas)

**[point to the box at the bottom left]**

"Start with the intuition. Three doctors give you three opinions.

You could average them. But two of them trained together at the same hospital and almost
always agree — so averaging all three equally counts that shared training twice. And the
third has thirty years more experience, so should count for more.

A weighted average handles the second point — you just give the experienced doctor a
bigger weight. But it physically cannot handle the first, because it only ever assigns
importance to doctors *individually*, never to the relationship between them.

The Choquet integral fixes that by assigning importance to every possible *group*."

### Then the mathematics

**[point to the formula panel]**

"A fuzzy measure gives a number to every subset of models. With three models that's eight
subsets — each model alone, each pair, all three, and the empty set.

The first line is the Sugeno rule: the importance of two groups combined is the sum of
their individual importances, plus a correction term lambda times their product.

Lambda isn't chosen freely. It's forced by the requirement that all models together must
equal 1, which is the second line.

And the sign of lambda tells you what kind of team you have. If the densities sum to
exactly 1, lambda is zero and this reduces to an ordinary weighted average. More than 1
and lambda goes negative — an overlap penalty. Less than 1 and lambda is positive — a
synergy bonus.

Then the integral itself: sort the predictions largest first, and weight each one by how
much the group importance *grew* when that model was added."

### The worked example

**[point to the small panel bottom right]**

"With densities 0.30, 0.25, 0.20 and predictions 9, 7 and 5, lambda works out to 1.2289,
the weights come out as 0.300, 0.342, 0.358, and the answer is 6.88 — where a plain
average would have given 7.00.

Notice the weights aren't the same as the densities. That difference is the Choquet
integral doing something a weighted average cannot."

### If asked to derive λ

"It's a polynomial equation in one unknown — you expand the product and solve numerically.
I can show the code."

---

# Slide 6 — The features

> *"Before fusion: how 4000 raw samples become 193 numbers"*

**Time: 1 minute** — *cut this slide first if short on time*

### What to say

"Briefly, how we get to 193 numbers.

A model can't read a waveform directly. Sixteen seconds of ECG is 4,000 raw numbers, and
feeding those in directly would force the model to rediscover what a heartbeat even is.

So we compute features — summary numbers describing properties.

A heartbeat mixes fast things and slow things: the QRS spike lasts a tenth of a second,
the T wave is a broad bump over three tenths. Measuring 'how jagged is this' on the whole
window blends them. A wavelet transform separates them into eight layers by speed.

Then each of those eight gets the same ten measurements — spikiness, wiggle rate,
irregularity, unpredictability, and so on. Eight times ten is eighty per signal, and with
two signals that's the paper's 160.

The formulas on the left are three of the ten, in case anyone wants them."

**[point to the bottom right card]**

"Plus 33 shape-based features — QT interval, heart rate variability, PPG pulse shape.

The paper used a neural network here. I measured the quantities directly instead, because
we already know from the biology which shapes matter. Every one of my features can be
traced to a mechanism. And they check out against physiology: median corrected QT interval
0.405 seconds, where textbook normal is 0.35 to 0.44."

---

# Slide 7 — The split question

> *"Finding 1: how you split the data changes the answer more than the model does"*

**Time: 1 minute 30 seconds** — *the most important concept in the talk*

### What to say

"Now the first finding, and it's about methodology rather than models.

In machine learning you always test on data the model hasn't seen — otherwise it could
just memorise. But there are different ways to arrange that split, and they answer
different questions."

**[walk through the three boxes left to right]**

"Protocol one: shuffle all 30,830 windows and split at random. The same *person* appears
in both training and test. This is what most published work reports.

Protocol two: split so no person appears on both sides. Now the model has to generalise
across people.

Protocol three: train on nine people, test on the tenth, rotate through all ten. That's
the real-world case — a brand-new patient."

### The key insight — say this slowly

"Here's the problem with protocol one. Consecutive windows from the same person are
extremely similar. So the model can learn to recognise *the person* and recall their
typical glucose.

That is not the same as learning about glucose. But it scores beautifully."

**[point to the red box]**

"This isn't just my concern. A 2026 study re-tested five published PPG-glucose methods
this way. Under random splitting the best scored R-squared 0.60. Under participant-aware
splitting, the same method scored minus 0.08 — no better than guessing the mean."

---

# Slide 8 — The results

> *"Our result: honest splits put every method behind the baseline"*

**Time: 1 minute 30 seconds**

### First, explain R² — they may not know it

"The table uses R-squared, so let me define it. R-squared is the fraction of variation the
model explains. One is perfect. Zero means exactly as good as always guessing the average.
**Negative means worse than always guessing the average.**

It's the one metric that exposes a useless model — RMSE and the clinical scores still look
respectable when a model has learned nothing."

### Then the result

"Under the random split, the Choquet fusion scores plus 0.149 against a baseline of zero.
It genuinely learns something.

Under the subject-aware split: minus 0.223, against a baseline of minus 0.074.

Under leave-one-out: minus 0.097, against minus 0.035.

**Same data. Same model. Same code. Only the split changed.**

And in both honest protocols, every single method — including the fusion — is worse than
the baseline."

### Be honest about the ordering — they may spot it

**[point to the dark box]**

"One thing you might notice: leave-one-out at minus 0.097 is *better* than subject-aware
at minus 0.223, even though it's the stricter protocol.

That's because leave-one-out trains on nine of ten people per round, while subject-aware
trains on four of five. It just has more data. The baseline moves the same way.

So I'm not claiming results get monotonically worse as the test gets stricter. I'm
claiming the narrower thing the data supports: under either honest split, every method
falls behind the baseline."

> **Raising this yourself is much stronger than having it pointed out to you.**

---

# Slide 9 — The picture

> *"What the failure looks like: predictions form a flat band, whatever the truth"*

**Time: 1 minute 30 seconds** — **your single best slide**

### What to say

"This is the same figure the original paper uses — a Parkes error grid. True glucose runs
across the bottom, what the model predicted runs up the side.

**[trace the diagonal with your hand]**

A model that had learned anything would produce a cloud along this diagonal — low
predictions when the truth is low, high when it's high.

**[now trace the horizontal band]**

Look at what we actually get. It's a horizontal band. Whether the person's real glucose
was 4 or 20, the model predicts roughly 6 to 9.

That is what 'no better than guessing the average' looks like when you draw it."

### Then the sting

"And now look at the box in the corner. That same flat band scores 89.4 percent in zones A
and B — the clinically acceptable region.

By the headline clinical metric, this looks like a working device."

> **Pause here. Let it land. This is the moment the argument becomes undeniable.**

---

# Slide 10 — The masking

> *"Finding 2: the clinical metric everyone reports cannot tell the difference"*

**Time: 1 minute 15 seconds**

### What to say

"Which brings us to the second finding.

The Parkes grid scores predictions by whether acting on them would harm the patient. A
panel of a hundred diabetes doctors drew the zone boundaries. Zone A plus B is the
headline clinical number in this entire field."

**[point to the table, then to the last row]**

"Here are four methods under the subject-aware split. The first three are real models.
The last row is the no-skill baseline — the thing that predicts a constant.

Read that last row carefully. The baseline has the **best R-squared** at minus 0.074, and
the **best clinical score** at 90.0 percent.

A model that explains literally zero variance beats every real model on both."

### Why

"Most glucose readings sit in a narrow band around normal. So predicting a constant near
the middle already lands most points inside the acceptable zones. The grid was designed to
catch *dangerous* errors, not to detect *uselessness*.

The practical rule: never report a clinical zone score without a baseline computed on the
same data beside it."

---

# Slide 11 — The masking, as a picture

> *"The same seven models, two metrics, opposite verdicts"*

**Time: 45 seconds** — quick, visual

### What to say

"The same point as a picture.

**[point to the red bar on the left]**

On the left, Parkes zone A plus B. The red bar is the constant predictor. It's the
*longest* — the best clinical score of anything tested.

**[point to the red bar on the right]**

On the right, R-squared. Same red bar, now the *shortest* — because it's the least-bad
score.

One metric says the constant predictor is the winner. The other says nothing here works.

If you only ever report the left-hand chart, you would ship this."

---

# Slide 12 — The degeneracy

> *"Finding 3: the fusion had degenerated into a minimum operator"*

**Time: 1 minute 30 seconds**

### Start with the clues

"The third finding I found by accident, chasing something that looked wrong.

Two things in my output didn't make sense. First, the weighted average and the plain
average were giving byte-identical answers — 3.927 and 3.927. If the weights differed at
all, that's impossible.

Second, every model's density came out at exactly 0.01 — the floor value I clip to."

### Then the theorem

**[point to the formula panel]**

"Here's what was happening. If every model gets the *same* density, the fuzzy measure
becomes symmetric — it depends only on how *many* models are in a group, never on *which*
ones.

When that happens, the Choquet integral collapses to this formula. The weight on the j-th
largest prediction is g times beta to the power j minus one.

And because weak models give densities summing to less than one, lambda is positive,
therefore beta is bigger than one, therefore the weights *grow* toward the smallest
prediction."

**[point to the table]**

"At the density I observed — 0.01 — 89.5 percent of the weight lands on the minimum.

At the other extreme, when the densities sum to one, it becomes an ordinary average."

### The confirmation

**[point to the two red numbers]**

"So I checked the predictions against the minimum of the three models. Correlation: 0.998.
Average gap: 0.04 millimoles per litre — seven times closer to the minimum than to the
mean.

The published method's distinguishing component — the weight-based Choquet integral — was
returning min of the three models."

### The deeper point — do not skip this

**[point to the dark box]**

"And it's not only a bug. Under honest evaluation the models genuinely can't generalise,
so the densities floor *legitimately*.

Which means the fusion silently turns into a minimum operator exactly when you most need
it to help. With no warning at all."

---

# Slide 13 — The derivation

> *"The derivation, so you can reproduce it on a board"*

**Time: 1 minute** — *cut this if short on time; the result is on slide 12*

### What to say

"For completeness, the derivation is three substitutions.

Step one: apply the Sugeno rule j times with identical densities. That gives you the group
importance as a closed form.

Step two: the Choquet weight is the growth from one group to the next, so you subtract
consecutive terms and it simplifies to g times beta to the j minus one.

Step three: check they sum to one, which they must. That's a geometric series, and it
collapses to the boundary condition.

**[point to the red box]**

And the reason beta exceeds one is the bit that matters: weak models give densities
summing to less than one, which forces lambda positive, which forces beta above one — and
that's what piles the weight onto the smallest prediction."

---

# Slide 13 — The ablation

> *"Finding 4: no feature set works — and fewer features work better"*

**Time: 1 minute**

### What to say

"I ran every feature set separately under the strictest protocol.

**[point to the left panel]**

Every bar is past the dashed line — that's the baseline. No subset of these 193 features
recovers glucose. The whole spread, best to worst, is 0.036 in R-squared.

And look at the ordering. 33 features scores minus 0.070. 193 features scores minus 0.097.
**Fewer features do better.**

That direction is the wrong way round for a method that's learning. When adding
information makes a model worse, the model is fitting noise — more features just give it
more coincidences to latch onto.

**[point to the right panel]**

Now compare the two panels. The models with the *worst* R-squared carry the *highest*
clinical score — 91.5 percent. The relationship isn't weak, it's inverted.

That's slide 10 taken to its conclusion. A model that predicts a narrow band near the
population average is never *dangerous*, so the grid scores it well. It's just useless."

---

# Slide 14 — Non-determinism

> *"Finding 5: a standard feature library returns different answers for identical input"*

**Time: 1 minute**

### What to say

"The fourth finding came from verifying a rebuild. The numbers didn't match — and the
cause wasn't my code.

One of the ten features is correlation dimension, which is estimated as the slope of a
log-log graph. The library fits that slope with RANSAC — a method that repeatedly tries
*random* subsets of points and keeps the best fit. And it doesn't seed the randomness.

So identical input gives different output. Thirty identical calls produced five different
answers."

**[point to the two big numbers]**

"Rebuilding one person's data with a deterministic fit changed up to 72 percent of those
values.

But look at the second number: the other 177 features were bit-identical. That's the
control — it proves the differences came from the slope fit and nothing else I'd changed."

### Why it matters

"Any result computed from these features was irreproducible. Nobody re-running the
pipeline — including me — would get the same numbers twice.

I only found it because I tested whether identical input gives identical output. Almost
nobody does that."

---

# Slide 16 — Contributions and limits

> *"What this contributes, and what we cannot claim"*

**Time: 1 minute 30 seconds**

### What to say

"So, four contributions.

One: an open reproduction on open data. All three stages rebuilt, 30,830 windows, ten
patients. The original used private data, so this is the first independent check.

Two: a degeneracy theorem with a runnable diagnostic. When density estimates saturate, the
Choquet integral provably becomes a fixed order statistic — and I verified that
empirically at 0.998 correlation.

Three: evidence that the evaluation protocol dominates the model. R-squared moving from
plus 0.149 to minus 0.223 on identical data, and a constant predictor beating every model
on the clinical metric.

Four: a reproducibility failure in a standard library, changing up to 72 percent of values
between identical runs."

### Then the limits — say these confidently, not apologetically

**[point to the amber box]**

"And what I can't claim.

Not that the method never works — only that it doesn't on this dataset under honest
evaluation, and that its fusion component was inactive.

My morphological branch uses hand-crafted features rather than their neural network. Ten
patients is small. And the CGM reference has its own error of nine to ten percent.

Stating limitations isn't a weakness in a reproduction. It's the point of one."

---

# Slide 17 — References

**Time: 15 seconds**

"References are here, and the full write-up with every derivation is in the repository."

**Then stop talking.** Leave this slide up, or go back to slide 16 for questions.

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

### If you have 5 minutes instead of 15

Slides **1, 4, 8, 9, 16**. That's the problem, the baseline, the result, the picture, and
the contribution.

### If something goes wrong with the projector

The three sentences that carry the whole talk:

1. "A model that always guesses the average scores 2.519 — anything real has to beat that."
2. "Under an honest train/test split, every method we tested was *worse* than that."
3. "And the clinical metric everyone reports can't tell the difference, because a constant
   predictor scores the highest of anything we tested."
