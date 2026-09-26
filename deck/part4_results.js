/* Part 6b-9: the degeneracy theorem, grading, results, conclusions. Slides 34-46. */
const D = require("./build_deck");
const {
  pres, INK, TEAL, MINT, RED, PAPER, MUTED, LIGHT, HEAD, BODY, W, H, M,
  ecgTrace, sectionSlide, contentSlide, bullets, card, stat, formula, note, table,
} = D;

module.exports = function build(R) {
  R = R || {};

  // ---- THE DEGENERACY SETUP ---------------------------------------------
  {
    const s = contentSlide("Finding 2: in our runs, the fusion had quietly stopped fusing");
    s.addText("Two clues appeared in the output before we understood why:", {
      x: M, y: 1.45, w: W - 2 * M, h: 0.35, isTextBox: true,
      fontFace: BODY, fontSize: 15, color: INK,
    });
    card(s, M, 1.9, 6.0, 1.55, "Clue 1",
      "The weighted average and the plain average produced byte-identical results - " +
      "3.927 and 3.927. If the weights differed at all, the two could not agree exactly.",
      { headSize: 13.5, size: 12.5, fill: "FBEFEF", headColor: RED });
    card(s, 6.8, 1.9, 6.0, 1.55, "Clue 2",
      "Every model's fuzzy density came out at exactly 0.01 - the floor we clip to. " +
      "All three models looked identically, minimally competent.",
      { headSize: 13.5, size: 12.5, fill: "FBEFEF", headColor: RED });

    s.addText("Why were the densities at the floor?", {
      x: M, y: 3.65, w: W - 2 * M, h: 0.35, isTextBox: true,
      fontFace: BODY, fontSize: 15, bold: true, color: INK,
    });
    const chain = [
      "cross_val_predict(model, X, y, cv=3)",
      "an integer cv means KFold WITHOUT shuffling",
      "our rows are sorted by patient",
      "so each 'fold' was a block of whole patients",
      "the density measured cross-PATIENT skill, not ordinary skill",
      "which is near zero, so every density hit the floor",
    ];
    chain.forEach((t, i) => {
      const y = 4.1 + i * 0.36;
      s.addText((i === 0 ? "" : "->  ") + t, {
        x: M + (i === 0 ? 0 : 0.35), y, w: 8.5, h: 0.32, isTextBox: true, margin: 0,
        fontFace: i === 0 ? "Courier New" : BODY, fontSize: i === 0 ? 12.5 : 13,
        color: i === 0 ? RED : INK, bold: i === 0 || i === chain.length - 1,
      });
    });
    card(s, 9.3, 4.05, 3.5, 2.05, "One character",
      "Passing an integer instead of an explicit splitter. That is the entire cause - " +
      "and it changes the behaviour of the algorithm itself, not merely the reported " +
      "score.", { headSize: 13, size: 12 });
  }

  // ---- THE THEOREM -------------------------------------------------------
  {
    const s = contentSlide("The theorem: equal densities turn the Choquet integral into a fixed order statistic");
    s.addText(
      "If all N densities equal the same value g, the fuzzy measure becomes SYMMETRIC - " +
      "it depends only on how many models are in a group, never on which ones. The " +
      "Choquet integral then reduces to a weighted sum of the SORTED predictions:",
      { x: M, y: 1.4, w: W - 2 * M, h: 0.62, isTextBox: true,
        fontFace: BODY, fontSize: 14, color: INK }
    );
    formula(s, M, 2.05, 7.5, [
      "     w_j  =  g * beta^(j-1)        beta = 1 + lambda*g",
      "",
      "     j = 1 is the LARGEST prediction, j = N the smallest",
      "",
      "Because sum(g_i) < 1  =>  lambda > 0  =>  beta > 1,",
      "the weights GROW toward the smallest prediction.",
      "",
      "As g -> 0 the weight collapses entirely onto the minimum.",
    ], 12);

    card(s, 8.25, 2.05, 4.55, 2.0, "In words",
      "When every model looks equally competent, the integral can no longer tell them " +
      "apart. All it has left is their ranking - so it becomes a fixed function of the " +
      "sorted values, carrying no information about which model was better.",
      { headSize: 13.5, size: 12 });

    s.addText("What that means at the density we actually observed, g = 0.01:", {
      x: M, y: 4.55, w: W - 2 * M, h: 0.35, isTextBox: true,
      fontFace: BODY, fontSize: 14, bold: true, color: INK,
    });
    table(s, [
      ["g", "lambda", "w(largest)", "w(middle)", "w(smallest)", "Collapses to"],
      ["0.010", "846.24", "0.010", "0.095", "0.895", "minimum operator"],
      ["0.050", "57.75", "0.050", "0.194", "0.756", "rank-weighted"],
      ["0.100", "15.41", "0.100", "0.254", "0.646", "rank-weighted"],
      ["0.200", "2.81", "0.200", "0.312", "0.488", "rank-weighted"],
      ["0.333", "0.00", "0.333", "0.333", "0.333", "arithmetic mean"],
    ], M, 4.95, 12.1, { colW: [1.3, 1.5, 2.0, 2.0, 2.0, 3.3], rowH: 0.28, size: 11.5 });
    note(s, "The symmetric-measure/OWA equivalence is standard aggregation theory (Grabisch; Marichal). What is new here is that a saturating density estimator induces it by accident.");
  }

  // ---- EMPIRICAL PROOF ---------------------------------------------------
  {
    const s = contentSlide("And the data agrees: the 'fusion' was computing the minimum");
    s.addText(
      "The theorem predicts that at g = 0.01, 89.5% of the weight sits on the smallest " +
      "prediction - so the output should be almost exactly the minimum of the three " +
      "models. We checked that against the saved predictions:",
      { x: M, y: 1.42, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 15, color: INK }
    );
    stat(s, M, 2.2, 4.0, "0.9993", "correlation between the\nChoquet output and min()", RED);
    stat(s, M + 4.2, 2.2, 4.0, "0.042", "mean gap to min()\n(mmol/L)", RED);
    stat(s, M + 8.4, 2.2, 3.7, "0.310", "mean gap to the mean\n(7x larger)", TEAL);

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 3.95, w: W - 2 * M, h: 1.35, rectRadius: 0.06,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText(
      "The published method's distinguishing component - the weight-based Choquet " +
      "integral - was, in our runs, returning min(model1, model2, model3).",
      { x: M + 0.3, y: 4.2, w: W - 2 * M - 0.6, h: 0.9, isTextBox: true, margin: 0,
        fontFace: HEAD, fontSize: 19, bold: true, color: PAPER }
    );

    s.addText("The fix, and what it restored", {
      x: M, y: 5.45, w: 5, h: 0.32, isTextBox: true,
      fontFace: BODY, fontSize: 13.5, bold: true, color: INK,
    });
    table(s, [
      ["Model", "Density before", "Density after"],
      ["Random Forest", "0.01 (floor)", "0.10 - 0.12"],
      ["Gradient Boosting", "0.01 (floor)", "0.04 - 0.07"],
      ["Bagging", "0.01 (floor)", "0.10 - 0.12"],
    ], M, 5.8, 7.0, { colW: [2.6, 2.2, 2.2], rowH: 0.27, size: 11 });

    card(s, 7.9, 5.45, 4.9, 1.55, "Now it discriminates",
      "The integral correctly gives Gradient Boosting - the weakest model - about half " +
      "the weight of the other two. That is the paper's mechanism finally doing its job.",
      { headSize: 12.5, size: 11.5 });
  }

  // ---- SECTION: GRADING --------------------------------------------------
  sectionSlide("PART 7", "How we grade a prediction",
    "Three metrics - and why the split you choose matters more than any of them");

  // ---- RMSE AND MARD -----------------------------------------------------
  {
    const s = contentSlide("Two error measures, because being wrong by 2 mmol/L means different things at different levels");
    card(s, M, 1.45, 6.0, 2.4, "RMSE - root mean square error", "", { fill: LIGHT });
    formula(s, M + 0.25, 1.95, 5.5, [
      "RMSE = sqrt( mean( (pred - true)^2 ) )",
    ], 12);
    s.addText(
      "The typical size of an error, in mmol/L. Squaring punishes large misses extra. " +
      "Same units as glucose, so it is directly interpretable.",
      { x: M + 0.25, y: 2.65, w: 5.5, h: 1.0, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: INK }
    );

    card(s, 6.8, 1.45, 6.0, 2.4, "MARD - mean absolute relative difference", "", { fill: LIGHT });
    formula(s, 7.05, 1.95, 5.5, [
      "MARD = mean( |pred - true| / true ) * 100%",
    ], 12);
    s.addText(
      "The error as a PERCENTAGE of the true value. Being off by 2 when the truth is 4 " +
      "is far worse than when it is 15 - MARD captures that; RMSE does not.",
      { x: 7.05, y: 2.65, w: 5.5, h: 1.0, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: INK }
    );

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.05, w: W - 2 * M, h: 1.0, rectRadius: 0.05,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText(
      "Reference point: guessing the average glucose every single time scores " +
      "RMSE = 2.519 mmol/L on our data. No model has learned anything unless it beats that.",
      { x: M + 0.3, y: 4.25, w: W - 2 * M - 0.6, h: 0.65, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 15, color: PAPER, bold: true }
    );

    s.addText(
      "We also report R-squared: the fraction of variation the model explains. It is the " +
      "one metric that clearly exposes a model doing no better than the average - it goes " +
      "to zero, or negative, while RMSE and MARD still look respectable.",
      { x: M, y: 5.25, w: W - 2 * M, h: 0.7, isTextBox: true,
        fontFace: BODY, fontSize: 13.5, color: INK }
    );
  }

  // ---- PARKES GRID -------------------------------------------------------
  {
    const s = contentSlide("The Parkes error grid asks a different question: would acting on this prediction hurt the patient?");
    bullets(s, [
      "Plot every prediction: true glucose on one axis, predicted on the other.",
      "A panel of 100 diabetes clinicians divided that plane into five zones by CLINICAL consequence.",
      "The boundaries are not arbitrary maths - they encode what a doctor would actually do with the number.",
    ], M, 1.45, 6.6, 1.7, 14);

    const zones = [
      ["A", "No effect on clinical action", "1B7F5E"],
      ["B", "Action changes, outcome unaffected", "6A9E2F"],
      ["C", "Action changes, outcome affected", "B26A00"],
      ["D", "Dangerous failure to detect", "C25E00"],
      ["E", "Opposite treatment given", RED],
    ];
    zones.forEach(([z, desc, col], i) => {
      const y = 3.3 + i * 0.52;
      s.addShape(pres.ShapeType.roundRect, {
        x: M, y, w: 6.6, h: 0.45, rectRadius: 0.04,
        fill: { color: PAPER }, line: { color: col, width: 1.3 },
      });
      s.addText(z, { x: M + 0.15, y: y + 0.07, w: 0.4, h: 0.3, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 14, bold: true, color: col, align: "center" });
      s.addText(desc, { x: M + 0.65, y: y + 0.08, w: 5.7, h: 0.3, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12, color: INK });
    });

    card(s, 7.55, 1.45, 5.25, 2.1, "The paper's headline clinical claim",
      "80.1% of its predictions in Zone A, and 99.5% in Zone A+B - essentially everything " +
      "clinically acceptable. This is the number that makes the method sound " +
      "device-ready.", { headSize: 13.5, size: 12.5 });

    s.addShape(pres.ShapeType.roundRect, {
      x: 7.55, y: 3.75, w: 5.25, h: 2.4, rectRadius: 0.06,
      fill: { color: "FFF6E5" }, line: { color: "FFF6E5" },
    });
    s.addText("But hold this thought", {
      x: 7.8, y: 3.93, w: 4.75, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: "8A5A00",
    });
    s.addText(
      "Most glucose readings sit in a narrow band around normal. So a model that predicts " +
      "a CONSTANT - the average - also lands most of its points in zones A and B.\n\n" +
      "A high Zone A+B score therefore does not, by itself, prove a model learned " +
      "anything. We test exactly this later.",
      { x: 7.8, y: 4.27, w: 4.75, h: 1.75, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12, color: INK }
    );
  }

  // ---- THE THREE PROTOCOLS ----------------------------------------------
  {
    const s = contentSlide("Finding 3: how you split the data changes the answer more than the model does");
    s.addText(
      "Consecutive windows from one person are extremely similar. If you shuffle all " +
      "windows and split at random, the SAME patient appears in both training and test - " +
      "so the model can recognise the person rather than learn about glucose.",
      { x: M, y: 1.42, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 15, color: INK }
    );
    const prot = [
      ["1. Random window", "Shuffle everything, split at random",
       "The same patient appears on both sides. This is what most published work reports.", LIGHT],
      ["2. Subject-aware", "Split so no patient is on both sides",
       "Now the model must generalise across people, not memorise them.", "E3EEF0"],
      ["3. Leave-one-subject-out", "Train on 9 patients, test on the 10th, rotate",
       "The deployment case: a brand-new patient the model has never seen.", INK],
    ];
    prot.forEach(([t, how, why, fill], i) => {
      const x = M + i * 4.12;
      const dark = i === 2;
      s.addShape(pres.ShapeType.roundRect, {
        x, y: 2.15, w: 3.85, h: 2.5, rectRadius: 0.06,
        fill: { color: fill }, line: { color: fill },
      });
      s.addText(t, { x: x + 0.24, y: 2.34, w: 3.4, h: 0.35, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 14, bold: true, color: dark ? MINT : INK });
      s.addText(how, { x: x + 0.24, y: 2.72, w: 3.4, h: 0.6, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12, color: dark ? PAPER : TEAL, italic: true });
      s.addText(why, { x: x + 0.24, y: 3.32, w: 3.4, h: 1.15, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12, color: dark ? "D6E6EA" : INK });
    });
    s.addText("Increasingly strict  ->", {
      x: M, y: 4.75, w: 12.1, h: 0.3, isTextBox: true,
      fontFace: BODY, fontSize: 12, color: MUTED, italic: true, align: "right",
    });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 5.15, w: W - 2 * M, h: 1.05, rectRadius: 0.05,
      fill: { color: "FBEFEF" }, line: { color: "FBEFEF" },
    });
    s.addText(
      "A 2026 study re-tested five published PPG-glucose methods this way. Under random " +
      "splitting the best scored R-squared 0.60; under subject-aware splitting the same " +
      "method scored -0.08 - no better than guessing the mean.",
      { x: M + 0.3, y: 5.33, w: W - 2 * M - 0.6, h: 0.75, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 13, color: INK }
    );
    note(s, "Reassessing the Feasibility of PPG-Based Non-Invasive Blood Glucose Level Estimation, arXiv:2608.01820 (2026).");
  }

  // ---- SECTION: RESULTS --------------------------------------------------
  sectionSlide("PART 8", "Results",
    "What the method actually achieves on 30,830 windows from 10 patients");

  // ---- RESULTS PLACEHOLDER / FILLED -------------------------------------
  {
    const s = contentSlide("Headline: the same method, the same data, three different splits");
    if (R.headline) {
      table(s, R.headline, M, 1.6, 12.1, {
        colW: [3.0, 1.5, 1.6, 1.6, 1.7, 2.7], rowH: 0.34, size: 12.5 });
      s.addText(R.headlineNote || "", {
        x: M, y: 4.4, w: W - 2 * M, h: 1.5, isTextBox: true,
        fontFace: BODY, fontSize: 14, color: INK });
    } else {
      s.addText("[ Results table - generated from results/summary_*.csv once the evaluation completes ]", {
        x: M, y: 3.2, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 14, color: MUTED, italic: true, align: "center" });
    }
  }

  // ---- CONCLUSIONS -------------------------------------------------------
  {
    const s = contentSlide("What this project contributes");
    const items = [
      ["1", "An open reproduction on open data",
       "The full three-stage pipeline rebuilt from the paper and run on PhysioCGM - 30,830 windows, 193 features, 10 patients. The original used private data, so this is the first independent check."],
      ["2", "A degeneracy theorem with a diagnostic",
       "When density estimates saturate, the Sugeno-lambda Choquet integral provably reduces to a fixed order statistic - w_j = g*beta^(j-1) - and at the floor it becomes min(). Verified empirically at correlation 0.9993."],
      ["3", "Evidence that evaluation protocol dominates",
       "The same model, same data, three splits. Random splitting flatters; subject-wise splitting exposes. We report all three rather than the flattering one."],
      ["4", "A reproducibility failure in a standard library",
       "nolds.corr_dim defaults to an unseeded random fit, changing up to 72% of values between identical runs. Any result built on it was irreproducible."],
    ];
    items.forEach(([n, t, d], i) => {
      const y = 1.45 + i * 1.28;
      s.addShape(pres.ShapeType.ellipse, {
        x: M, y: y + 0.04, w: 0.46, h: 0.46,
        fill: { color: INK }, line: { color: INK },
      });
      s.addText(n, { x: M, y: y + 0.11, w: 0.46, h: 0.32, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 14, bold: true, color: MINT, align: "center" });
      s.addText(t, { x: M + 0.66, y: y + 0.02, w: 11.4, h: 0.33, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 15, bold: true, color: INK });
      s.addText(d, { x: M + 0.66, y: y + 0.37, w: 11.4, h: 0.78, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: MUTED });
    });
    s.addText(
      "The unifying point: at three different layers - the fusion operator, the evaluation " +
      "protocol, and the feature library - this pipeline produced confident numbers that " +
      "were wrong, while appearing to work.",
      { x: M, y: 6.6, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 13.5, color: INK, italic: true }
    );
  }

  // ---- LIMITATIONS -------------------------------------------------------
  {
    const s = contentSlide("What we did not do, stated plainly");
    const lims = [
      ["The morphological branch is not the paper's",
       "They use a ResNet on signal segments; we use hand-crafted physiological features. Defensible and interpretable, but not identical."],
      ["Ten patients is still small",
       "PhysioCGM is the largest open ECG+PPG+CGM dataset available, but ten people cannot represent the diversity of diabetes."],
      ["The CGM reference is itself approximate",
       "It lags blood glucose by 5-15 minutes and carries ~9-10% error of its own. Our ceiling is set by our reference."],
      ["We did not tune hyperparameters",
       "Model settings follow the paper. A tuned version might do better - though tuning honestly requires a third data split."],
    ];
    lims.forEach(([t, d], i) => {
      const x = M + (i % 2) * 6.25;
      const y = 1.55 + Math.floor(i / 2) * 2.15;
      card(s, x, y, 5.85, 1.85, t, d, { headSize: 14, size: 12.5 });
    });
    s.addText(
      "Stating limitations is not a weakness in a reproduction - it is the point of one.",
      { x: M, y: 6.1, w: W - 2 * M, h: 0.4, isTextBox: true,
        fontFace: BODY, fontSize: 14, color: INK, bold: true }
    );
  }

  // ---- REFERENCES --------------------------------------------------------
  {
    const s = contentSlide("References");
    const refs = [
      "Li, J. et al. \"Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG Feature Fusion and Weight-Based Choquet Integral Multimodel Approach.\" IEEE Transactions on Neural Networks and Learning Systems, 35(10), 2024.",
      "PhysioCGM: a multimodal physiological dataset for non-invasive blood glucose estimation. Scientific Data, 2025. figshare record 28136294 (CC0).",
      "Reassessing the Feasibility of PPG-Based Non-Invasive Blood Glucose Level Estimation. arXiv:2608.01820, 2026.",
      "Advances in Electrocardiogram-Based Non-Invasive Blood Glucose Monitoring Technology. Review, 2026.",
      "Parkes, J. L. et al. \"A New Consensus Error Grid to Evaluate the Clinical Significance of Inaccuracies in the Estimation of Blood Glucose.\" Diabetes Care, 23(8), 2000.",
      "Pfutzner, A. et al. \"Technical Aspects of the Parkes Error Grid.\" Journal of Diabetes Science and Technology, 7(5), 2013.",
      "Eckert, B. & Agardh, C.-D. \"Hypoglycaemia leads to an increased QT interval in normal men.\" Clinical Physiology, 18(6), 1998.",
      "Grabisch, M. \"Fuzzy integral in multicriteria decision making.\" Fuzzy Sets and Systems, 69(3), 1995.",
      "Marichal, J.-L. \"On Choquet and Sugeno integrals as aggregation functions.\" Fuzzy Measures and Integrals, 2000.",
      "Sugeno, M. \"Theory of fuzzy integrals and its applications.\" PhD thesis, Tokyo Institute of Technology, 1974.",
    ];
    s.addText(
      refs.map((t, i) => ({ text: t, options: { bullet: false, breakLine: i !== refs.length - 1 } })),
      { x: M, y: 1.4, w: W - 2 * M, h: 5.1, isTextBox: true,
        fontFace: BODY, fontSize: 11.5, color: INK, paraSpaceAfter: 7 }
    );
  }

  // ---- CLOSING -----------------------------------------------------------
  {
    const s = pres.addSlide();
    s.background = { color: INK };
    s.addText("The honest result is the useful one", {
      x: M, y: 2.5, w: W - 2 * M - 1.0, h: 0.9, isTextBox: true,
      fontFace: HEAD, fontSize: 34, color: PAPER, bold: true,
    });
    s.addText(
      "Reproducing a method carefully enough to find where it breaks is worth more than " +
      "reproducing a number.",
      { x: M, y: 3.5, w: W - 2 * M - 2.5, h: 0.9, isTextBox: true,
        fontFace: BODY, fontSize: 17, color: "AEC6CC" }
    );
    s.addText("Navtesh Maken   |   B.Tech Final Year Project", {
      x: M, y: 5.5, w: 8, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 13, color: MINT,
    });
    ecgTrace(s, W - 4.6, 5.4, 4.0, 0.9, MINT, 2);
  }
};
