/* Part 5-6: features and the Choquet mathematics. Slides 20-33. */
const D = require("./build_deck");
const {
  pres, INK, TEAL, MINT, RED, PAPER, MUTED, LIGHT, HEAD, BODY, W, H, M,
  ecgTrace, sectionSlide, contentSlide, bullets, card, stat, formula, note, table,
} = D;

module.exports = function build() {

  sectionSlide("PART 5", "Stage 2: describing the signal with numbers",
    "Wavelets, the ten statistical features, waveform shape - and a library that gives different answers each time");

  // ---- WHAT IS A FEATURE -------------------------------------------------
  {
    const s = contentSlide("A model cannot read a waveform, so we describe each window with numbers");
    bullets(s, [
      "A 16-second ECG window is 4000 raw numbers. Feeding those directly to a model works poorly: the model would have to rediscover what a heartbeat is.",
      "Instead we compute FEATURES - summary numbers describing properties of the window.",
      "A simple feature: the average. A better one: how irregular the signal is, or how long the heart takes to reset.",
      "Choosing good features is most of the craft. The paper specifies exactly which ones, so we use exactly those.",
    ], M, 1.5, 7.2, 2.7, 15);

    card(s, 8.0, 1.45, 4.8, 1.55, "The paper's recipe",
      "Two families of features, computed for BOTH signals: statistical 'temporal' " +
      "features and shape-based 'morphological' features.", { headSize: 14, size: 12.5 });

    s.addShape(pres.ShapeType.roundRect, {
      x: 8.0, y: 3.2, w: 4.8, h: 2.1, rectRadius: 0.06,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText("Our totals", {
      x: 8.25, y: 3.38, w: 4.3, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: MINT,
    });
    [["80", "ECG temporal"], ["80", "PPG temporal"],
     ["33", "morphological"], ["193", "TOTAL per window"]].forEach(([n, l], i) => {
      s.addText(n, {
        x: 8.25, y: 3.72 + i * 0.37, w: 0.75, h: 0.32, isTextBox: true, margin: 0,
        fontFace: "Courier New", fontSize: 14, bold: true,
        color: i === 3 ? MINT : PAPER, align: "right",
      });
      s.addText(l, {
        x: 9.1, y: 3.72 + i * 0.37, w: 3.4, h: 0.32, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: i === 3 ? MINT : "D6E6EA",
      });
    });
  }

  // ---- WAVELETS ----------------------------------------------------------
  {
    const s = contentSlide("A wavelet transform splits the signal into fast and slow parts, so each can be described separately");
    s.addText(
      "A heartbeat mixes a sharp spike (the QRS, very fast) with broad waves (P and T, " +
      "much slower). Measuring the whole thing at once blurs them together. The Discrete " +
      "Wavelet Transform separates them.",
      { x: M, y: 1.42, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 14.5, color: INK }
    );
    s.addText("Think of it as repeatedly splitting the signal in half by speed:", {
      x: M, y: 2.05, w: 7.2, h: 0.32, isTextBox: true,
      fontFace: BODY, fontSize: 13.5, color: INK, bold: true,
    });

    const levels = [
      ["Original", "the full window", "FE0"],
      ["Level 1", "fastest detail", "FE1"],
      ["Level 2", "a bit slower", "FE2"],
      ["...", "", ""],
      ["Level 7", "slowest detail", "FE7"],
    ];
    levels.forEach(([a, b, c], i) => {
      const y = 2.5 + i * 0.52;
      if (a === "...") {
        s.addText("...", { x: M + 0.3, y, w: 1.2, h: 0.35, isTextBox: true, margin: 0,
          fontFace: BODY, fontSize: 15, color: MUTED });
        return;
      }
      s.addShape(pres.ShapeType.roundRect, {
        x: M, y, w: 6.9, h: 0.45, rectRadius: 0.04,
        fill: { color: i === 0 ? INK : LIGHT }, line: { color: i === 0 ? INK : LIGHT },
      });
      s.addText(a, { x: M + 0.18, y: y + 0.06, w: 1.3, h: 0.32, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, bold: true, color: i === 0 ? PAPER : INK });
      s.addText(b, { x: M + 1.55, y: y + 0.06, w: 3.6, h: 0.32, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12, color: i === 0 ? "D6E6EA" : MUTED });
      s.addText(c, { x: M + 5.6, y: y + 0.06, w: 1.1, h: 0.32, isTextBox: true, margin: 0,
        fontFace: "Courier New", fontSize: 12, bold: true, color: i === 0 ? MINT : TEAL });
    });

    card(s, 7.75, 2.5, 5.05, 1.5, "The paper's exact choice",
      "The 'db4' (Daubechies-4) wavelet, decomposed to 7 levels. We use precisely this - " +
      "not a substitute.", { headSize: 13.5, size: 12 });
    card(s, 7.75, 4.15, 5.05, 1.5, "The result",
      "8 signals to analyse: the original plus 7 detail levels. Each gets the same 10 " +
      "measurements, giving 8 x 10 = 80 features per signal.",
      { headSize: 13.5, size: 12 });
    note(s, "Why it helps: a feature measuring 'irregularity' means something different for the fast QRS than for the slow T wave.");
  }

  // ---- THE TEN FEATURES --------------------------------------------------
  {
    const s = contentSlide("From each of the 8 sub-signals we compute the same 10 statistical measurements");
    table(s, [
      ["Symbol", "Name", "What it measures, in plain terms"],
      ["Kur", "Kurtosis", "How spiky the signal is - are there extreme peaks?"],
      ["Ske", "Skewness", "Is it lopsided - do peaks lean up or down?"],
      ["SM", "Signal mobility", "How fast it wiggles on average"],
      ["SC", "Signal complexity", "How much that wiggle rate itself changes"],
      ["FD", "Fractal dimension", "How jagged the line is - does detail persist on zooming in?"],
      ["CD", "Correlation dimension", "How many independent things drive the signal"],
      ["C0", "C0-complexity", "What fraction is irregular rather than regular"],
      ["PSE", "Power spectral entropy", "Is energy spread over many frequencies or concentrated?"],
      ["KE", "Kolmogorov entropy", "How unpredictable the next value is"],
      ["SE", "Shannon entropy", "How much information the value distribution carries"],
    ], M, 1.5, 8.6, { colW: [1.1, 2.2, 5.3], rowH: 0.315, size: 11.5 });

    card(s, 9.4, 1.5, 3.4, 1.9, "The arithmetic",
      "8 sub-signals x 10 features = 80 per modality.\n\nECG 80 + PPG 80 = 160, exactly " +
      "the paper's count.", { headSize: 13, size: 12 });

    s.addShape(pres.ShapeType.roundRect, {
      x: 9.4, y: 3.55, w: 3.4, h: 2.35, rectRadius: 0.06,
      fill: { color: "FBEFEF" }, line: { color: "FBEFEF" },
    });
    s.addText("Remember CD", {
      x: 9.62, y: 3.72, w: 3.0, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: RED,
    });
    s.addText(
      "Correlation dimension is the most expensive of the ten to compute - and it turned " +
      "out to be the source of a serious reproducibility problem. We return to it in " +
      "three slides.",
      { x: 9.62, y: 4.06, w: 3.0, h: 1.6, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12, color: INK }
    );
  }

  // ---- MORPHOLOGICAL -----------------------------------------------------
  {
    const s = contentSlide("We also measure waveform SHAPE - the quantities the physiology actually predicts");
    s.addText(
      "The paper uses a neural network (ResNet) here. We had no GPU, and more " +
      "importantly, the mechanism linking glucose to waveform shape is already known - " +
      "so we measure it directly instead of hoping a network rediscovers it.",
      { x: M, y: 1.42, w: W - 2 * M, h: 0.62, isTextBox: true,
        fontFace: BODY, fontSize: 14.5, color: INK }
    );
    table(s, [
      ["From the ECG", "Why it is in the list"],
      ["QT interval, corrected QT", "Lengthens when glucose is low (adrenaline -> low potassium)"],
      ["ST segment level", "Depressed under sustained high glucose"],
      ["T-wave amplitude and sharpness", "Flattens during dysglycaemia"],
      ["QRS duration and amplitude", "Describes the main depolarisation spike"],
      ["SDNN, RMSSD, pNN50", "Heart-rate variability - falls with high glucose"],
    ], M, 2.15, 7.4, { colW: [3.0, 4.4], rowH: 0.35, size: 11.5 });

    table(s, [
      ["From the PPG", "What it captures"],
      ["Systolic amplitude", "Pulse strength"],
      ["Rise and fall time", "How quickly blood arrives and drains"],
      ["Pulse width at half height", "Overall pulse shape"],
      ["Augmentation index", "Strength of the reflected wave"],
    ], M, 4.35, 7.4, { colW: [3.0, 4.4], rowH: 0.35, size: 11.5 });

    card(s, 8.2, 2.15, 4.6, 1.85, "Why hand-crafted beats a black box here",
      "Each feature is individually citable to a mechanism. In a viva, \"we measured QT " +
      "because adrenaline-driven low potassium prolongs repolarisation\" is a far " +
      "stronger answer than \"the network learned something\".",
      { headSize: 13, size: 12 });

    s.addShape(pres.ShapeType.roundRect, {
      x: 8.2, y: 4.15, w: 4.6, h: 1.7, rectRadius: 0.06,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText("Validated against physiology", {
      x: 8.45, y: 4.32, w: 4.1, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12.5, bold: true, color: MINT,
    });
    s.addText(
      "Median heart rate 74.4 bpm, median QTc 0.405 s - textbook normal is 0.35-0.44 s. " +
      "Over 99% of windows fall in physiologically plausible ranges, which tells us the " +
      "extraction is measuring real anatomy, not noise.",
      { x: 8.45, y: 4.66, w: 4.1, h: 1.05, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11.5, color: "D6E6EA" }
    );
    s.addText("This substitution is a deliberate, documented deviation from the paper - not a silent shortcut.", {
      x: M, y: 6.1, w: W - 2 * M, h: 0.35, isTextBox: true,
      fontFace: BODY, fontSize: 12.5, color: MUTED, italic: true,
    });
  }

  // ---- FEATURE SELECTION -------------------------------------------------
  {
    const s = contentSlide("With 193 features, most are noise - so three methods must agree before one is kept");
    s.addText(
      "More features is not better. Useless features let a model latch onto coincidences. " +
      "The paper keeps only features that survive three independent tests:",
      { x: M, y: 1.45, w: W - 2 * M, h: 0.5, isTextBox: true,
        fontFace: BODY, fontSize: 15, color: INK }
    );
    const methods = [
      ["UFS", "Univariate filtering",
       "Test each feature on its own: does it correlate with glucose at all? Keeps the individually promising ones."],
      ["RFE", "Recursive elimination",
       "Train a model, drop the least useful feature, retrain, repeat. Catches features that only matter in combination."],
      ["L1", "Lasso regression",
       "Fit a model penalised for using many features. It is forced to set useless weights to exactly zero."],
    ];
    methods.forEach(([tag, name, body], i) => {
      const x = M + i * 4.12;
      card(s, x, 2.1, 3.85, 2.15, " ", body, { size: 12 });
      // Heading and tag share a row, so the heading is explicitly narrowed to stop
      // short of the tag rather than relying on the card's default full width.
      s.addText(name, {
        x: x + 0.22, y: 2.26, w: 2.6, h: 0.32, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 14, bold: true, color: INK,
      });
      s.addText(tag, {
        x: x + 2.9, y: 2.26, w: 0.73, h: 0.3, isTextBox: true, margin: 0,
        fontFace: "Courier New", fontSize: 13, bold: true, color: TEAL, align: "right",
      });
    });
    s.addText("A feature is kept only if ALL THREE select it.", {
      x: M, y: 4.45, w: 6.5, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 15, bold: true, color: INK,
    });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.95, w: W - 2 * M, h: 1.35, rectRadius: 0.06,
      fill: { color: "FBEFEF" }, line: { color: "FBEFEF" },
    });
    s.addText("A trap we deliberately avoided", {
      x: M + 0.28, y: 5.12, w: 6, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: RED,
    });
    s.addText(
      "Selection must run on the TRAINING data only, inside each fold. Choosing features " +
      "using the whole dataset lets the test answers influence which features exist - " +
      "and silently inflates every score that follows. Our code has no function that " +
      "selects on a whole dataset, because that function would be a footgun.",
      { x: M + 0.28, y: 5.44, w: W - 2 * M - 0.56, h: 0.8, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: INK }
    );
  }

  // ---- FINDING: RANSAC ---------------------------------------------------
  {
    const s = contentSlide("Finding 1: a standard library returns a different answer every time you ask it");
    s.addText(
      "While verifying that a rebuild matched our earlier results, they did not match. " +
      "The cause was not our code.",
      { x: M, y: 1.42, w: W - 2 * M, h: 0.4, isTextBox: true,
        fontFace: BODY, fontSize: 15, color: INK }
    );
    s.addText(
      "Correlation dimension is estimated as the slope of a log-log plot. The library " +
      "fits that slope with RANSAC - a method that repeatedly tries RANDOM subsets and " +
      "keeps the best. It is not seeded. So identical input gives different output.",
      { x: M, y: 1.9, w: 7.3, h: 0.9, isTextBox: true,
        fontFace: BODY, fontSize: 14, color: INK }
    );
    table(s, [
      ["Fitting method", "Distinct values from identical input"],
      ["RANSAC (the default)", "5 different answers in 30 calls"],
      ["Ordinary least squares", "1 - always the same"],
    ], M, 2.95, 7.3, { colW: [3.4, 3.9], rowH: 0.38, size: 12.5 });

    card(s, 7.85, 1.9, 4.95, 1.75, "How bad was it?",
      "Rebuilding one participant with the deterministic fit changed up to 72% of " +
      "correlation-dimension values. The other 177 features were bit-identical - which " +
      "is the control proving the cause was the fit, not our changes.",
      { headSize: 13, size: 12, fill: "FBEFEF", headColor: RED });

    card(s, 7.85, 3.8, 4.95, 1.35, "The fix",
      "One argument: fit the slope with least squares instead. Both methods agree on the " +
      "typical value; only one always returns it.", { headSize: 13, size: 12 });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.5, w: 7.3, h: 1.6, rectRadius: 0.06,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText("Why this belongs in the paper", {
      x: M + 0.28, y: 4.68, w: 6.7, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: MINT,
    });
    s.addText(
      "Any result computed from these features was irreproducible - nobody re-running " +
      "the pipeline, including us, would get the same numbers. It was found only because " +
      "we tested whether identical input gives identical output, which almost nobody does.",
      { x: M + 0.28, y: 5.0, w: 6.7, h: 1.0, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: "D6E6EA" }
    );
  }

  sectionSlide("PART 6", "Stage 3: the Choquet integral",
    "The mathematics at the heart of the paper - and the theorem that explains why it stopped working");

  // ---- WHY COMBINE -------------------------------------------------------
  {
    const s = contentSlide("Three models are used instead of one, because they make different mistakes");
    bullets(s, [
      "Random Forest - many decision trees trained on random resamples, then averaged. Stable, resists noise.",
      "Gradient Boosting - trees trained one after another, each correcting the previous one's errors. Chases accuracy.",
      "Bagging - many full trees on random resamples, averaged. Reduces variance.",
      "Where one is wrong another may be right, so combining them should beat any one alone. The question is HOW to combine.",
    ], M, 1.5, 7.3, 2.6, 15);

    card(s, 8.05, 1.45, 4.75, 2.5, "The everyday analogy",
      "Three doctors give three opinions. You could average them. But if two trained " +
      "together and always agree, averaging counts their shared view twice. And if one " +
      "is far more experienced, they should count for more.\n\nA good combination rule " +
      "handles BOTH.", { headSize: 14, size: 12.5 });

    s.addText("Three ways to combine, in increasing sophistication:", {
      x: M, y: 4.25, w: W - 2 * M, h: 0.35, isTextBox: true,
      fontFace: BODY, fontSize: 14, bold: true, color: INK,
    });
    const combos = [
      ["Plain average", "(a + b + c) / 3", "Treats all three as equally good and unrelated"],
      ["Weighted average", "w1*a + w2*b + w3*c", "Better models count more - but still assumes independence"],
      ["Choquet integral", "weights on GROUPS", "Can express that two models overlap, or work well together"],
    ];
    combos.forEach(([t, f, d], i) => {
      const x = M + i * 4.12;
      const last = i === 2;
      s.addShape(pres.ShapeType.roundRect, {
        x, y: 4.7, w: 3.85, h: 1.45, rectRadius: 0.05,
        fill: { color: last ? INK : LIGHT }, line: { color: last ? INK : LIGHT },
      });
      s.addText(t, { x: x + 0.22, y: 4.85, w: 3.4, h: 0.3, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 13, bold: true, color: last ? MINT : INK });
      s.addText(f, { x: x + 0.22, y: 5.17, w: 3.4, h: 0.3, isTextBox: true, margin: 0,
        fontFace: "Courier New", fontSize: 11.5, color: last ? PAPER : TEAL });
      s.addText(d, { x: x + 0.22, y: 5.5, w: 3.4, h: 0.55, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11, color: last ? "D6E6EA" : MUTED });
    });
  }

  // ---- FUZZY MEASURE -----------------------------------------------------
  {
    const s = contentSlide("The key idea: assign importance to every GROUP of models, not just to each one");
    s.addText(
      "A weighted average gives each model a number. A fuzzy measure gives every possible " +
      "SUBSET a number. With three models there are eight subsets:",
      { x: M, y: 1.42, w: W - 2 * M, h: 0.5, isTextBox: true,
        fontFace: BODY, fontSize: 15, color: INK }
    );
    formula(s, M, 2.0, 7.3, [
      "g({})        = 0      nothing counts for nothing",
      "g({A})       = 0.30",
      "g({B})       = 0.25       each model alone",
      "g({C})       = 0.20",
      "g({A,B})     = 0.45   <- NOT 0.30+0.25: they overlap",
      "g({A,C})     = 0.62   <- MORE than the sum: they complement",
      "g({B,C})     = 0.50",
      "g({A,B,C})   = 1      everyone together = full importance",
    ], 12.5);

    bullets(s, [
      "Two rules define a valid fuzzy measure:",
      "   g(empty) = 0 and g(everything) = 1",
      "   Adding a model can never reduce importance (monotonicity)",
      "That is it. Any function obeying those two is allowed.",
    ], 8.1, 2.0, 4.7, 1.9, 13);

    s.addShape(pres.ShapeType.roundRect, {
      x: 8.1, y: 4.05, w: 4.7, h: 2.05, rectRadius: 0.06,
      fill: { color: "FFF6E5" }, line: { color: "FFF6E5" },
    });
    s.addText("The practical problem", {
      x: 8.35, y: 4.22, w: 4.2, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: "8A5A00",
    });
    s.addText(
      "For N models there are 2^N subsets. For 3 that is 8; for 10 it is 1024. " +
      "Choosing all of them by hand is impossible.\n\nThe Sugeno lambda-measure solves " +
      "this: give it one number per model, and it generates all the rest.",
      { x: 8.35, y: 4.56, w: 4.2, h: 1.4, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12, color: INK }
    );
  }

  // ---- SUGENO LAMBDA -----------------------------------------------------
  {
    const s = contentSlide("The Sugeno lambda-measure builds all the group importances from one number per model");
    s.addText("You supply a 'density' g-i for each model: how good it is on its own. Then:", {
      x: M, y: 1.42, w: W - 2 * M, h: 0.35, isTextBox: true,
      fontFace: BODY, fontSize: 15, color: INK,
    });
    formula(s, M, 1.85, 7.6, [
      "Combining two disjoint groups A and B:",
      "",
      "    g(A u B)  =  g(A) + g(B) + lambda * g(A) * g(B)",
      "",
      "lambda is fixed by requiring g(everything) = 1:",
      "",
      "    1 + lambda  =  PRODUCT over i of (1 + lambda * g_i)",
    ], 13);

    s.addText("Everything hinges on the sign of lambda:", {
      x: M, y: 4.45, w: 7.6, h: 0.35, isTextBox: true,
      fontFace: BODY, fontSize: 14, bold: true, color: INK,
    });
    const cases = [
      ["sum of densities = 1", "lambda = 0", "Groups just add up. The Choquet integral becomes an ordinary weighted average."],
      ["sum > 1", "lambda < 0", "Overlap penalty: strong models that agree are not counted twice."],
      ["sum < 1", "lambda > 0", "Synergy bonus: models are worth more together than apart."],
    ];
    cases.forEach(([cond, lam, meaning], i) => {
      const y = 4.9 + i * 0.6;
      s.addShape(pres.ShapeType.roundRect, {
        x: M, y, w: 7.6, h: 0.52, rectRadius: 0.04,
        fill: { color: LIGHT }, line: { color: LIGHT },
      });
      s.addText(cond, { x: M + 0.2, y: y + 0.11, w: 2.1, h: 0.3, isTextBox: true, margin: 0,
        fontFace: "Courier New", fontSize: 11, color: TEAL, bold: true });
      s.addText(lam, { x: M + 2.35, y: y + 0.11, w: 1.1, h: 0.3, isTextBox: true, margin: 0,
        fontFace: "Courier New", fontSize: 11, color: RED, bold: true });
      s.addText(meaning, { x: M + 3.5, y: y + 0.11, w: 3.95, h: 0.32, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 10.5, color: INK });
    });

    card(s, 8.35, 1.85, 4.45, 2.2, "Where do densities come from?",
      "We measure each model's competence honestly: train it on part of the training " +
      "data, test on the rest it never saw, and use that score.\n\nThis matters enormously " +
      "- and getting it wrong is what broke the method.",
      { headSize: 13.5, size: 12 });

    card(s, 8.35, 4.2, 4.45, 2.0, "Worth noticing now",
      "If every model gets the SAME density, the measure treats all models alike - it can " +
      "no longer tell them apart. Hold that thought.",
      { headSize: 13.5, size: 12, fill: "FFF6E5", headColor: "8A5A00" });
  }

  // ---- THE CHOQUET INTEGRAL ----------------------------------------------
  {
    const s = contentSlide("The Choquet integral sorts the predictions, then weights each by how much the group importance grows");
    formula(s, M, 1.4, 7.6, [
      "1. Sort the predictions, largest first:",
      "       h(1) >= h(2) >= ... >= h(N)",
      "",
      "2. Walk down the sorted list, accumulating:",
      "",
      "   C  =  SUM over j of  h(j) * [ g(A_j) - g(A_j-1) ]",
      "",
      "   where A_j = the top j models",
    ], 12.5);

    bullets(s, [
      "Sorting is what lets group importance enter at all - the weight a prediction gets depends on its RANK, not its identity.",
      "If the measure is additive (lambda = 0) this reduces exactly to a weighted average.",
      "So the Choquet integral GENERALISES the weighted average - it can do everything the simpler rule can, plus express interaction.",
    ], 8.35, 1.4, 4.45, 2.5, 12.5);

    card(s, M, 4.75, 7.6, 1.35, "Read it this way",
      "Go down the sorted predictions. Each one is weighted by how much the group's " +
      "importance GREW when it was added. A model that adds little when included gets " +
      "little weight - regardless of what it predicted.",
      { headSize: 13.5, size: 12.5 });
  }

  // ---- WORKED EXAMPLE ----------------------------------------------------
  {
    const s = contentSlide("A worked example, with real numbers");
    s.addText("Three models predict glucose for one window. Their densities differ, so the integral should favour the better-supported values.", {
      x: M, y: 1.42, w: W - 2 * M, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 14.5, color: INK,
    });
    formula(s, M, 1.95, 7.6, [
      "densities   = (0.30, 0.25, 0.20)  ->  lambda = 1.2289",
      "predictions = ( 9.0,  7.0,  5.0)  mmol/L",
      "",
      "      g(top 1) = 0.300    weight on 9.0 = 0.300",
      "      g(top 2) = 0.642    weight on 7.0 = 0.342",
      "      g(top 3) = 1.000    weight on 5.0 = 0.358",
      "",
      "Choquet = 0.300*9 + 0.342*7 + 0.358*5 = 6.88 mmol/L",
      "Plain average                          = 7.00 mmol/L",
    ], 12);

    bullets(s, [
      "The weights come from how much each addition grows the group importance - not from the predictions themselves.",
      "They always sum to exactly 1, because g(everything) = 1.",
      "Here the fused value sits below the plain average, pulled toward the lower predictions.",
      "Notice the weights are not equal to the densities. The integral is doing something a weighted average cannot.",
    ], 8.35, 1.95, 4.45, 2.9, 12.5);

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 5.15, w: W - 2 * M, h: 1.05, rectRadius: 0.05,
      fill: { color: "FFF6E5" }, line: { color: "FFF6E5" },
    });
    s.addText(
      "Now ask the question that breaks it: what happens when all three densities are " +
      "the SAME? The next slides answer that, and it is the central finding of this project.",
      { x: M + 0.3, y: 5.36, w: W - 2 * M - 0.6, h: 0.7, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 14, color: INK, bold: true }
    );
  }
};
