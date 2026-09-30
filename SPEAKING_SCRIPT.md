# Speaking Script — 15 Minutes

For `deck/btp_midterm_review.pptx`, 17 slides. Timings add to 14:10, leaving slack.

Say the words in quotes. Everything else is stage direction.

---

## Slide 1 — Title (30 s)

> "Good morning. Our project reproduces a method published in IEEE Transactions on
> Neural Networks and Learning Systems last year, for estimating blood glucose without
> drawing blood, using only an ECG and a PPG signal. I'm [name], with Vednash, Aditya
> and Tushar, supervised by Mrs. Asha Rani."

Do not read the names off the slide. They can see them.

---

## Slide 2 — Contents (20 s)

> "Four literature and framing sections, two on methodology, five on results, then
> future work. I'll spend most of the time on the results."

Move on quickly.

---

## Slide 3 — Introduction (60 s)

> "Blood glucose has to stay between about 4 and 10 millimoles per litre. Below that
> you get seizures within minutes. Above it, over years, you lose nerves, eyes and
> kidneys. Around 590 million adults manage this, and every accurate measurement
> available today breaks the skin — a finger prick several times a day, or a sensor
> filament replaced every two weeks.
>
> The reason the heart might tell us the answer is on the right. When glucose drops,
> your body dumps adrenaline, which drives potassium into cells. Potassium is what
> heart muscle uses to reset after each beat, so the QT interval on the ECG stretches.
> When glucose is high, vagal tone drops and the ST segment and T wave change shape.
>
> One thing to note, because it governs everything after: that mechanism supports
> *detecting* a dangerous event. It does not by itself prove you can read the exact
> number off the waveform. That second claim is what we tested."

---

## Slide 4 — Literature Survey I (55 s)

> "This is the table from the paper. Five methods, theirs is the bottom row: RMSE of
> 1.49 millimoles, MARD 13.4 percent, and 99.5 percent of predictions in the clinically
> acceptable zones.
>
> That's about as good as an approved continuous glucose monitor, which is a strong
> claim. The authors released their code but not their recordings, which are private.
> So the result had never been checked on a group of people they didn't choose
> themselves. That's the gap we set out to fill."

---

## Slide 5 — Literature Survey II (50 s)

> "Three things shaped our design. First, a 2026 re-assessment of five published PPG
> glucose methods: the best of them scored 0.60 R-squared under a random split, and
> minus 0.08 when the split was made participant-aware. Same data, same model, opposite
> conclusion. That's why we evaluate under three protocols instead of one.
>
> Second, a review identifying record-level splitting as a field-wide problem. Third,
> Grabisch and Marichal, which bounds what we can claim as new in our last results
> section. I'll come back to that."

---

## Slide 6 — Research Gaps (45 s)

> "Five gaps. No independent validation. The evaluation protocol isn't controlled. The
> clinical metric is reported with no baseline next to it, so you can't tell how much
> of the score belongs to the method. The fusion step is never audited. And there's no
> check that the feature pipeline is even deterministic.
>
> Each of those five turns into one of our results."

Point at the numbers as you say them. Don't read the paragraphs.

---

## Slide 7 — Aim and Objectives (40 s)

> "The aim: does the reported accuracy survive independent reproduction on open data.
>
> Five objectives — rebuild all three stages, run on PhysioCGM, evaluate under three
> protocols with a baseline beside every result, audit the fusion operator itself, and
> check the pipeline is reproducible.
>
> Two limitations we state up front. Their dataset is private, so this reproduces the
> *method* on different data, not the experiment. And we used hand-crafted shape
> features instead of their ResNet, because we had no GPU."

---

## Slide 8 — Problem Formulation (75 s)

This is the mathematics slide. Slow down.

> "Three models each predict a glucose value. We need one number out.
>
> A weighted average gives each model an importance and adds them up. The problem is it
> can't express overlap — if two of your three models are nearly the same model, a
> weighted average counts that evidence twice.
>
> A fuzzy measure fixes this by assigning importance to every *subset*, not every model.
> The Sugeno lambda-measure, top left, generates all those subset values from one number
> per model. Lambda, top right, is not free — it's forced by requiring that all three
> models together have importance exactly one.
>
> The Choquet integral, in the middle, sorts the predictions largest to smallest, then
> weights each one by how much the group importance grows when you add it.
>
> The intuition is in the box. If the densities sum to one, lambda is zero and this
> collapses to an ordinary weighted average. Sum above one, lambda goes negative, and
> you get a penalty for redundancy. Sum below one, lambda is positive, a bonus for
> complementary models. Sorting is what lets subset importance matter at all."

---

## Slide 9 — Methodology I (55 s)

> "Three levels. Level one: for every glucose reading we take the 16 seconds of signal
> just before it. At 250 hertz that's 4,000 ECG samples; at 64 hertz, 1,024 PPG samples.
> Sixteen seconds is about 20 heartbeats, and 1,024 is a power of two, which matters for
> the wavelet step.
>
> Level two, feature extraction. Level three, three tree models fused by the Choquet
> integral.
>
> The dataset is PhysioCGM: ten Type-1 participants, chest strap, wristband and a Dexcom
> monitor. 30,830 paired windows.
>
> The number to remember on this slide is the last one: 2.519. That's the standard
> deviation of glucose in our data, which means it's the error you get from a model that
> ignores the heart completely and always guesses the average. Anything real has to beat
> it. We report it beside every single result."

---

## Slide 10 — Methodology II (55 s)

> "Two families of features. On top, wavelet features: we split each signal seven times
> into eight frequency bands, and take ten statistical measurements from each — those
> are the ten on the slide, kurtosis through Shannon entropy. Eight bands times ten
> measurements times two signals is 160.
>
> Below, shape features measured directly off the waveform: QT interval, corrected QT,
> ST level, T-wave shape, heart rate variability. 33 of those. 193 in total.
>
> At the bottom, selection. A feature is kept only if all three criteria agree —
> univariate, recursive elimination, and L1. Typically about ten survive. Crucially,
> selection runs *inside* each training fold, never on the whole dataset, or we'd be
> leaking test information into the choice of features.
>
> One validation: our median corrected QT is 0.405 seconds. The textbook normal range is
> 0.35 to 0.44. The features are measuring real physiology."

---

## Slide 11 — Results I (70 s) — **this is your headline**

> "This is the reproduction, run under the paper's own protocol: a random split at the
> window level.
>
> Every model has a positive R-squared. Random Forest and Bagging reach 0.194, the
> Choquet fusion 0.149, and all of them clear the no-skill baseline at zero. So the
> pipeline is genuinely learning a relationship between the waveform and glucose — it
> is not guessing.
>
> The fusion also carries our best clinical score, 93.75 percent in Zones A and B,
> which is the ordering the paper reports.
>
> Now the honest part, on the right. Our RMSE is 2.26 against their 1.49, and our Zone
> A+B is 93.8 against their 99.5. So we reproduce the *behaviour* but not the
> *magnitude*. Two reasons: different people, because their cohort is private and we
> couldn't get it, and we substituted hand-crafted features for their ResNet because we
> had no GPU."

If you only land one slide, land this one.

---

## Slide 12 — Results II (65 s)

> "Then we asked a second question. Same data, same models, but split three different
> ways.
>
> Protocol one is the paper's: a random split, which lets windows from the same person
> land in both training and test. That's the plus 0.149 you just saw.
>
> Protocols two and three never do that — a person is either entirely in training or
> entirely in test. Under those, the numbers go negative: minus 0.223 and minus 0.097.
>
> The box on the right is the point. These protocols ask different questions. The first
> asks how well this works for someone the model has already seen. The second asks how
> well it works for a brand new person. Both are fair questions to ask. The published
> result answers the first one, and we reproduce it. We're adding the answer to the
> second."

If asked "so does it work?" — "For a person it has calibrated on, yes. For a stranger,
not yet. Those are different products."

---

## Slide 13 — Results III (60 s)

> "Here's the same thing as a picture, one participant over seventeen days. Red is the
> real glucose from the CGM, blue is our prediction.
>
> On the left, the random split. The blue tracks the red — you can see it rise and fall
> with the daily pattern. That's the condition the published result is obtained under.
>
> On the right, the same participant held out entirely. The blue flattens into a band
> around 7, the population average.
>
> Bottom left is the Parkes error grid for the left-hand case: 93.7 percent in Zones A
> and B, which is the clinical acceptability standard."

Point at the left panel, then the right. The contrast does the work.



## Slide 14 — Future Work (45 s)

> "Four directions. Reframe from regression to classification, because the biology
> supports detecting dangerous highs and lows better than reading exact numbers, and
> published ECG classifiers get 84 to 94 percent. Test per-participant calibration,
> which is how CGMs are actually deployed anyway. Implement the ResNet branch properly
> once we have GPU access. And apply the degeneracy diagnostic to other fusion
> pipelines, because that failure isn't specific to glucose."

---

## Slide 15 — Conclusion and References (40 s) Spatio Temporal Feature Fusion + Weight Based Croquet Integral Multimodel

> "To summarise. We rebuilt the method in full and ran it on 30,830 windows from ten
> people. Under the paper's protocol we reproduce a positive result, somewhat below the
> accuracy they report, and we've explained why. Under stricter protocols the
> performance does not hold, which tells us the method currently works per-person rather
> than across people. And we found the fusion operator had degenerated into a minimum.
> 
> Thank you — happy to take questions."

---

## Questions you will get

**"Why is R-squared negative in that second table?"**
> "Because R-squared is measured against always guessing the average. Zero means you've
> matched that; negative means you've done worse. Under the strict split the model is
> being asked about a person it has never seen, and it does worse than the average for
> that person. Under the paper's protocol, which is the comparable one, ours is
> positive."

**"So did you reproduce the paper or not?"**
> "Under their protocol, yes, directionally — positive R-squared, fusion ahead on the
> clinical metric. Our absolute numbers are worse, on a different cohort and without the
> ResNet. What we add is what happens when you change the split."

**"Why is the ablation only under one protocol?"**
> "Time. We ran the fused set under all three, and the four individual feature sets
> under the strictest one only, because that's the one that answers whether a feature
> family generalises to a new person. The remaining eight runs are about two and a half
> hours and they're queued."

**"Ten people is very small."**
> "It is, and we say so. It's the same order as most studies in this area — the review
> we cite notes most use under 30. More people would firm up our conclusion rather than
> reverse it."

**"Why didn't you use their dataset?"**
> "It's private. They released code, not recordings. That's precisely why an independent
> check was worth doing."

**"Is 93.7 percent in Zone A+B good?"**
> "It's the standard the field quotes. But we'd point out the no-skill baseline scores
> 90.9 on the same metric, which is why we always print it alongside."

---

## If you are running over

Cut slide 14 (ablation) and compress slide 6 to fifteen seconds. Never cut 11, 12 or 13.

## If the projector dies

> "We rebuilt a published method for reading blood sugar from heart signals. Under the
> original evaluation we reproduce a positive result, a bit below what they report.
> Under a stricter evaluation, where the model has never seen the person before, it
> doesn't hold up. And the fusion step we were testing had collapsed into a minimum
> function without anyone noticing."
