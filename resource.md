# resource.md — All Learning Resources for This Project (one place)

> Everything you need to learn this project from zero, in one file. **Part A** is a
> watch-in-order YouTube study path. **Part B** is the complete reference library (books,
> papers, docs, the dataset, the original code). **Part C** is a 1-week schedule.
>
> How to use it: follow Part A phase by phase, and after each phase re-read the matching
> chapter in `explain.md` (the code) and section in `MATH.md` (the formulas). The video
> builds intuition; our docs connect it to the actual code.

---

## How the topics fit together (the map)

```
Phase 0  Python + ML basics ───────────────► everything
Phase 1  Trees: RF / GB / Bagging ──────────► src/base_models.py   · MATH.md §1
Phase 2  Fuzzy measures + Choquet integral ─► src/choquet.py       · MATH.md §2–4   ★ the core
Phase 3  Fourier → Wavelets (DWT) ──────────► src/features_temporal.py (stage 1) · MATH.md §7.A
Phase 4  ECG signals & cleaning ────────────► src/d1namo.py        · paper Level 1
Phase 5  Entropy / fractal features ────────► src/features_temporal.py (stage 2) · MATH.md §7.B
Phase 6  The metrics + the paper ───────────► src/metrics.py, the PDF
```

---
---

# PART A — YouTube study path (watch in this order)

## Phase 0 — Python + Machine-Learning foundations  (~3–18 h, pick your depth)
- ★ **freeCodeCamp — "Machine Learning with Python and Scikit-Learn – Full Course"** (18 h;
  regression → decision trees → random forests → gradient boosting, in the *exact* library
  we use): https://www.youtube.com/watch?v=hDKCxebp88A
  *(Watch the intro + tree sections now; the rest later.)*
- **3Blue1Brown — "Essence of Calculus" & "Essence of Linear Algebra"** (math comfort; the
  gradient idea returns in gradient boosting): https://www.youtube.com/c/3blue1brown
- **Khan Academy — Statistics & Probability** (mean, variance, distributions):
  https://www.youtube.com/c/khanacademy

➡️ Then read `explain.md` §1–5.

## Phase 1 — Random Forest, Gradient Boosting, Bagging  (~2 h)  ★
**Channel: StatQuest with Josh Starmer** (best beginner ML explainer).
All playlists: https://www.youtube.com/c/joshstarmer/playlists
1. **Decision Trees** (search "StatQuest Decision Trees") — the building block.
2. **"10 Decision Trees are Better Than 1 — Random Forest & AdaBoost"**:
   https://www.youtube.com/watch?v=ZaXpMou55lw
3. **Random Forests, Part 1 — Building, Using, Evaluating**:
   https://www.youtube.com/watch?v=J4Wdy0Wc_xQ  (Part 2 is linked there)
4. **Gradient Boost (playlist, Parts 1–4)**, start with regression:
   https://www.youtube.com/playlist?list=PLblh5JKOoLUJjeXUvUE0maghNuY2_5fY6
5. **AdaBoost, Clearly Explained**: https://www.youtube.com/watch?v=LsK-xG1cLYA
6. **"Bias and Variance"** (search StatQuest) — *why* bagging vs boosting exist.

➡️ Then read `explain.md` §8 and `MATH.md` §1.

## Phase 2 — Fuzzy measures & the Choquet integral  (~2–3 h)  ★ THE HEART
This topic is niche on YouTube — use a mix:
- **Search YouTube:** *"Choquet integral explained"*, *"Sugeno fuzzy measure example"*,
  *"fuzzy integral information fusion"* (look for lecture-style talks).
- **Foundations first:** any clear video on **"weighted average"** (the Choquet integral
  generalises it — see `MATH.md` §4.4), and a **"fuzzy logic / fuzzy sets introduction"**.
- **Lean on our `MATH.md` §2–4** — written specifically for this gap, with a worked example
  you can do on paper. **Redo that example by hand** — that's the real learning moment.
- Written gold standard (skim): **Grabisch (1995)**, "Fuzzy integral in multicriteria
  decision making" (Google Scholar).

➡️ Then read `explain.md` §9, `MATH.md` §2–4, and run `python -m src.choquet`.

## Phase 3 — Fourier → Wavelets (the DWT)  (~2 h)
1. **3Blue1Brown — "But what is the Fourier Transform?"**:
   https://www.youtube.com/c/3blue1brown
2. **"The Wavelet Transform for Beginners"**: https://www.youtube.com/watch?v=kuuUaqAjeoA
3. **MATLAB — "Understanding Wavelets" series** (Part 3 = applied example; watch 1–2 first):
   https://www.youtube.com/watch?v=-OhibnAXBEM
4. **Steve Brunton** (advanced, excellent Fourier & wavelet lectures):
   https://www.youtube.com/c/Eigensteve

➡️ Then read `MATH.md` §7.A and `explain.md` §13 (stage 1). PyWavelets docs:
https://pywavelets.readthedocs.io/

## Phase 4 — ECG signals & cleaning  (~1.5 h)
- **Search YouTube:** *"ECG basics P QRS T explained"*, *"ECG signal processing python"*,
  *"ECG filtering baseline wander powerline"*.
- **Hands-on Python libraries (optional):** NeuroKit2 (beginner-friendly biosignals),
  BioSPPy: https://pypi.org/project/biosppy/

➡️ Then read `explain.md` §12 & §14.

## Phase 5 — Entropy & fractal features  (~2 h, deeper)
- **Shannon entropy / information theory:** Artem Kirsanov, or *"Shannon entropy explained"*.
- **Fractal dimension:** *"fractal dimension explained"* (relates to Higuchi FD).
- **Chaos / correlation dimension & sample entropy:** *"strange attractor chaos theory"*,
  *"sample entropy approximate entropy explained"*.
- **Hjorth parameters:** *"Hjorth parameters EEG"* (short, easy).
- **antropy docs:** https://raphaelvallat.com/antropy/

➡️ Then read `MATH.md` §7.B (all 10 feature formulas).

## Phase 6 — Metrics & re-reading the paper  (~1 h)
- **RMSE:** search *"RMSE explained"* (StatQuest).
- **MARD:** `MATH.md` §6 defines it; search *"MARD glucose monitoring accuracy"* for context.
- **Re-read the paper PDF** (this folder), Section II — it'll now read like familiar ground.

➡️ Then read `MATH.md` §6 and `explain.md` §10–11; run `python -m src.run_d1namo`.

---
---

# PART B — Complete reference library (books, papers, docs, data)

### Machine learning & ensembles (RF, GB, Bagging) — `MATH.md` §1
- ★ **StatQuest** channel (videos above): https://www.youtube.com/c/joshstarmer/playlists
- **"An Introduction to Statistical Learning" (ISLR/ISLP)** — free PDF, Chapter 8 = trees,
  bagging, forests, boosting: https://www.statlearning.com/
- **scikit-learn — Ensemble methods (User Guide):**
  https://scikit-learn.org/stable/modules/ensemble.html
- *(Advanced)* **"The Elements of Statistical Learning" (ESL)** — free PDF; Ch. 10 boosting,
  Ch. 15 random forests: https://hastie.su.domains/ElemStatLearn/

### Fuzzy measures & Choquet integral — `MATH.md` §2–4  (the core)
- ★ **Grabisch (1995)**, "Fuzzy integral in multicriteria decision making," *Fuzzy Sets and
  Systems* — the classic readable intro (Google Scholar).
- **Murofushi & Sugeno (1989)** — foundational interpretation of fuzzy measures & the
  Choquet integral.
- **Beliakov, Pradera & Calvo — "Aggregation Functions: A Guide for Practitioners"** (book;
  implementation-friendly Choquet chapter).
- **Wikipedia:** [Choquet integral](https://en.wikipedia.org/wiki/Choquet_integral) ·
  [Fuzzy measure theory](https://en.wikipedia.org/wiki/Fuzzy_measure_theory)
- **arXiv survey:** "A special class of fuzzy measures: Choquet integral and applications":
  https://arxiv.org/pdf/1711.08602

### Signal processing — wavelets & spectral — `MATH.md` §7.A
- **The Wavelet Tutorial (Robi Polikar)** — classic beginner text (search the title).
- **PyWavelets docs:** https://pywavelets.readthedocs.io/
- **Discrete Wavelet Transform — Wikipedia:**
  https://en.wikipedia.org/wiki/Discrete_wavelet_transform
- **3Blue1Brown — Fourier Transform** (intuition for PSE/C0): https://www.youtube.com/c/3blue1brown

### Entropy / fractal / nonlinear features — `MATH.md` §7.B
- **antropy docs (definitions + references):** https://raphaelvallat.com/antropy/
- **Hjorth (1970)** — Signal Mobility & Complexity (original).
- **Higuchi (1988)** — fractal dimension method (original).
- **Grassberger & Procaccia (1983)** — correlation dimension.
- **Richman & Moorman (2000)** — Sample Entropy (our KE estimator).

### ECG signal processing (Python, hands-on)
- **NeuroKit2** (biosignal toolkit, great docs/examples): https://neuropsychology.github.io/NeuroKit/
- **BioSPPy:** https://pypi.org/project/biosppy/
- **Pan–Tompkins QRS detection** (classic R-peak algorithm): https://arxiv.org/pdf/2211.03171

### The application (ECG/PPG → blood glucose)
- **The paper itself** (PDF in this folder): Li et al., 2024, *IEEE TNNLS* — re-read Section II.
- **Authors' code (no data):** https://github.com/SIATCAS/SFF-WCIM
- **D1NAMO dataset (what we use):** https://zenodo.org/records/5651217 ·
  Kaggle mirror: https://www.kaggle.com/datasets/sarabhian/d1namo-ecg-glucose-data ·
  describing paper: Dubosson et al., 2018, *Informatics in Medicine Unlocked*.
- **PhysioCGM (has ECG+PPG+CGM; access by email)** — the closest match if you want PPG too:
  https://github.com/PSI-TAMU/PhysioCGM · https://www.nature.com/articles/s41597-025-06090-6

### Math prerequisites (if any symbol felt unfamiliar)
- **Khan Academy** — summation notation, probability, statistics: https://www.youtube.com/c/khanacademy
- **3Blue1Brown** — "Essence of Calculus" & "Essence of Linear Algebra":
  https://www.youtube.com/c/3blue1brown

### Our own docs (don't forget these!)
- **`explain.md`** — the code, chapter by chapter (plain English).
- **`MATH.md`** — every formula derived from scratch, with a worked Choquet example.

---
---

# PART B+ — Full-length structured courses (if you want depth, not just clips)

These are complete university-style courses. **NPTEL** ones are free, in English, and made
by Indian institutes (IITs) — they map almost perfectly onto this project's topics.

### ★ NPTEL (free, IIT-taught) — best match for this project
- **Introduction to Machine Learning** — IIT Madras, Prof. Balaraman Ravindran (covers
  decision trees, ensembles, the lot). Playlist:
  https://www.youtube.com/playlist?list=PLSIm6F6G8CqZgbPTCs6O0Bfe22Am180l_ ·
  course page: https://nptel.ac.in/courses/106106139
- **Biomedical Signal Processing** — directly covers ECG and **QRS (R-peak) detection**,
  power spectra, matched filters: https://onlinecourses.nptel.ac.in/noc20_ee41/preview ·
  videos: https://nptel.ac.in/courses/108105101
- **Advanced Digital Signal Processing — Multirate & Wavelets** — the theory behind our
  **db4 DWT** (filter banks, multiresolution):
  https://www.classcentral.com/course/youtube-electronics-adv-digital-signal-processing-multirate-and-wavelets-47534
- **Digital Signal Processing and Its Applications** (foundations: Z-transform, filters):
  https://www.youtube.com/playlist?list=PLULQVvZuQOEZUfGtIb_cnzt0xG31pi4ka

### Andrew Ng — the canonical beginner ML course (free to audit)
- **Machine Learning Specialization** (Stanford / DeepLearning.AI; 4.8M+ learners). Audit
  for free (videos, no certificate): https://www.coursera.org/specializations/machine-learning-introduction ·
  overview: https://www.deeplearning.ai/courses/machine-learning-specialization/

### Krish Naik — practical, project-and-deployment focused (great for the BTP demo)
- **Channel & playlists:** https://www.youtube.com/@krishnaik06/playlists
- **Complete Machine Learning playlist:**
  https://www.youtube.com/playlist?list=PLZoTAELRMXVPBTrWtJkn3wWQxZkmTXGwe
- **End-to-End ML Project (build → save model → deploy):**
  https://www.youtube.com/playlist?list=PLZoTAELRMXVPS-dOaVbAux22vzqdgoGhG
  *(This is the closest match to our `train.py` + `app.py` deployment step.)*

---
---

# PART C — A realistic 1-week schedule (≈2 h/day)

| Day | Focus | Watch (Part A) | Then read |
|---|---|---|---|
| 1 | ML basics | Phase 0 (intro parts) | `explain.md` §1–5 |
| 2 | Trees | Phase 1 (StatQuest) | `explain.md` §8, `MATH.md` §1 |
| 3 | **Choquet** ★ | Phase 2 | `explain.md` §9, `MATH.md` §2–4 (redo the example!) |
| 4 | Wavelets | Phase 3 | `MATH.md` §7.A, `explain.md` §13 |
| 5 | ECG | Phase 4 | `explain.md` §12, §14 |
| 6 | Entropy/fractal | Phase 5 | `MATH.md` §7.B |
| 7 | Metrics + paper | Phase 6 | `MATH.md` §6; re-read the PDF |

> Tip: keep `MATH.md` open in a split window while watching. Whenever a symbol appears,
> pause and find it in `MATH.md` §0 (the notation table). That single habit makes the math
> feel approachable fast.
