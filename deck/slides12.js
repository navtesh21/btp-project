/*
 * slides12.js — the 12-slide presentation.
 *
 * Ghost-deck test (read the titles alone and the argument must stand):
 *   1  title
 *   2  measuring glucose means breaking skin, so people want a painless signal
 *   3  a 2024 paper claims near-clinical accuracy by fusing ECG+PPG with a Choquet integral
 *   4  we rebuilt all three stages on the largest open ECG+PPG+CGM dataset
 *   5  the mathematics: importance on GROUPS, not just individual models
 *   6  how you split the data changes the answer more than the model does
 *   7  our result: the same model collapses from R2 +0.15 to -0.22
 *   8  the clinical metric everyone reports cannot tell the difference
 *   9  the fusion had degenerated into a minimum operator
 *  10  a standard feature library returns different answers for identical input
 *  11  what this contributes, and what we cannot claim
 *  12  references
 */
const D = require("./build_deck");
const {
  pres, INK, TEAL, MINT, RED, PAPER, MUTED, LIGHT, HEAD, BODY, W, H, M,
  ecgTrace, annotatedBeat, contentSlide, bullets, card, stat, formula, note, table,
} = D;

module.exports = function build() {

  // ---- 1. TITLE ----------------------------------------------------------
  {
    const s = pres.addSlide();
    s.background = { color: INK };
    s.addText("Can your heartbeat tell us your blood sugar?", {
      x: M, y: 1.75, w: W - 2 * M - 1.2, h: 1.5, isTextBox: true,
      fontFace: HEAD, fontSize: 42, color: PAPER, bold: true,
    });
    s.addText(
      "Reproducing a Choquet-integral multimodel approach to noninvasive blood glucose " +
      "estimation from ECG and PPG",
      { x: M, y: 3.3, w: W - 2 * M - 2.2, h: 0.9, isTextBox: true,
        fontFace: BODY, fontSize: 17, color: "AEC6CC" }
    );
    s.addText("B.Tech Final Year Project", {
      x: M, y: 4.5, w: 6, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 13, color: MINT, bold: true, charSpacing: 2,
    });
    s.addText("Navtesh Maken", {
      x: M, y: 4.95, w: 6, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 15, color: PAPER,
    });
    ecgTrace(s, M, 6.0, W - 2 * M, 1.0, MINT, 2.5);
    s.addNotes("We reproduce a 2024 IEEE method on open data. The headline is not the accuracy - it is four ways this kind of pipeline produces confident wrong answers.");
  }

  // ---- 2. THE PROBLEM ----------------------------------------------------
  {
    const s = contentSlide("Measuring blood glucose means breaking the skin, several times a day, for life");
    bullets(s, [
      "Glucose is the fuel every cell runs on. In Type 1 diabetes the body makes almost no insulin, so it builds up in the blood.",
      "Below 3.9 mmol/L: confusion, seizure, coma - within minutes. Above 10.0: nerve, eye and kidney damage over years.",
      "Today that is managed with finger-pricks 4-10 times daily, or a sensor worn under the skin and replaced fortnightly.",
      "About 590 million adults live with diabetes. All of them manage it by repeatedly breaking their own skin.",
    ], M, 1.5, 7.2, 2.9, 15);

    card(s, 8.05, 1.45, 4.75, 2.35, "Why a heartbeat might know",
      "Low glucose triggers adrenaline, which drives potassium into cells. Potassium " +
      "controls how heart cells reset after each beat - so the ECG's QT interval " +
      "lengthens. High glucose suppresses vagal tone and alters ST and T waves.\n\n" +
      "The mechanism is real and well documented.", { headSize: 14, size: 12.5 });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.55, w: W - 2 * M, h: 1.45, rectRadius: 0.06,
      fill: { color: "FFF6E5" }, line: { color: "FFF6E5" },
    });
    s.addText("But note what the mechanism actually supports", {
      x: M + 0.3, y: 4.74, w: 8, h: 0.32, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: "8A5A00",
    });
    s.addText(
      "It explains DETECTING a dangerous low or high - a classification problem. It does " +
      "not promise that the exact number can be read off the waveform, which is " +
      "regression, and far harder. Published ECG classification reaches 84-94% accuracy; " +
      "regression consistently does not hold up.",
      { x: M + 0.3, y: 5.08, w: W - 2 * M - 0.6, h: 0.8, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 13, color: INK }
    );
    s.addNotes("Open here. The audience needs to know what glucose is, why it matters, and that there IS a real reason to look at the heart - before any maths.");
  }

  // ---- 3. THE PAPER ------------------------------------------------------
  {
    const s = contentSlide("A 2024 IEEE paper reports near-clinical accuracy by fusing two signals and three models");
    s.addText(
      "Li et al., \"Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG " +
      "Feature Fusion and Weight-Based Choquet Integral Multimodel Approach\", " +
      "IEEE TNNLS 35(10), 2024.",
      { x: M, y: 1.42, w: W - 2 * M, h: 0.55, isTextBox: true,
        fontFace: BODY, fontSize: 13.5, color: INK, italic: true }
    );
    stat(s, M, 2.1, 3.0, "1.49", "RMSE (mmol/L)", TEAL);
    stat(s, M + 3.15, 2.1, 3.0, "13.42%", "MARD", TEAL);
    stat(s, M + 6.3, 2.1, 3.0, "80.1%", "Parkes Zone A", TEAL);
    stat(s, M + 9.45, 2.1, 3.0, "99.5%", "Zone A+B", TEAL);

    const stages = [
      ["STAGE 1", "Collect and clean", "Record ECG + PPG, filter, cut into 16-second windows paired with a glucose reading"],
      ["STAGE 2", "Describe the signal", "Wavelet statistics plus waveform-shape measurements: 193 numbers per window"],
      ["STAGE 3", "Predict and fuse", "Three models each predict; a Choquet integral combines their answers"],
    ];
    stages.forEach(([tag, title, body], i) => {
      const x = M + i * 4.12;
      const dark = i === 2;
      s.addShape(pres.ShapeType.roundRect, {
        x, y: 3.9, w: 3.85, h: 2.1, rectRadius: 0.06,
        fill: { color: dark ? INK : LIGHT }, line: { color: dark ? INK : LIGHT },
      });
      s.addText(tag, { x: x + 0.24, y: 4.06, w: 3.4, h: 0.28, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11, bold: true, charSpacing: 2, color: dark ? MINT : TEAL });
      s.addText(title, { x: x + 0.24, y: 4.36, w: 3.4, h: 0.38, isTextBox: true, margin: 0,
        fontFace: HEAD, fontSize: 17, bold: true, color: dark ? PAPER : INK });
      s.addText(body, { x: x + 0.24, y: 4.82, w: 3.4, h: 1.0, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11.5, color: dark ? "D6E6EA" : INK });
    });
    note(s, "1.49 mmol/L approaches approved CGM accuracy. The authors published code but not data, so the claim had never been independently checked.");
  }

  // ---- 4. WHAT WE BUILT --------------------------------------------------
  {
    const s = contentSlide("We rebuilt all three stages and ran them on the largest open ECG+PPG+CGM dataset");
    stat(s, M, 1.5, 3.0, "30,830", "paired ECG+PPG windows", TEAL);
    stat(s, M + 3.15, 1.5, 3.0, "193", "features per window", TEAL);
    stat(s, M + 6.3, 1.5, 3.0, "10", "Type-1 patients", TEAL);
    stat(s, M + 9.45, 1.5, 3.0, "2.519", "baseline RMSE to beat", RED);

    table(s, [
      ["Signal", "Rate", "Device"],
      ["ECG", "250 Hz", "Zephyr BioHarness chest strap"],
      ["PPG", "64 Hz", "Empatica E4 wristband"],
      ["Glucose", "every 5 min", "Dexcom CGM - the reference"],
    ], M, 3.3, 6.3, { colW: [1.4, 1.5, 3.4], rowH: 0.33, size: 12 });

    card(s, 7.25, 3.3, 5.55, 1.45, "PhysioCGM (Scientific Data, 2025)",
      "Public domain, CC0. The only open dataset carrying ECG AND PPG against a CGM " +
      "reference - exactly the pair this paper needs.", { headSize: 13, size: 12 });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.95, w: W - 2 * M, h: 1.2, rectRadius: 0.05,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText(
      "The number that matters most is 2.519 mmol/L - the standard deviation of glucose, " +
      "and therefore the error of a model that simply guesses the average every time. " +
      "Nothing counts as learning unless it beats that.",
      { x: M + 0.3, y: 5.16, w: W - 2 * M - 0.6, h: 0.85, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 14, color: PAPER }
    );
    s.addNotes("193 features = 80 ECG wavelet + 80 PPG wavelet + 33 morphological (QT, QTc, ST level, T-wave shape, HRV, PPG pulse shape).");
  }

  // ---- 5. THE MATHEMATICS ------------------------------------------------
  {
    const s = contentSlide("The Choquet integral assigns importance to GROUPS of models, not just to each one");
    s.addText(
      "A weighted average gives each model a number. A fuzzy measure gives every SUBSET a " +
      "number - so it can say two models overlap, or that two work well together. The " +
      "Sugeno lambda-measure builds all of them from one density per model:",
      { x: M, y: 1.4, w: W - 2 * M, h: 0.62, isTextBox: true,
        fontFace: BODY, fontSize: 14, color: INK }
    );
    formula(s, M, 2.1, 7.5, [
      "g(A u B) = g(A) + g(B) + lambda*g(A)*g(B)",
      "",
      "lambda fixed by   1 + lambda = PROD (1 + lambda*g_i)",
      "",
      "Sort predictions largest first, then",
      "",
      "   C = SUM_j  h(j) * [ g(top j) - g(top j-1) ]",
    ], 12.5);

    bullets(s, [
      "Each prediction is weighted by how much the group's importance GREW when it was added.",
      "If the densities sum to 1 then lambda = 0 and this is exactly a weighted average - so the Choquet integral generalises it.",
      "Densities come from each model's honest out-of-fold accuracy.",
    ], 8.3, 2.1, 4.5, 2.2, 12.5);

    s.addText("Worked example", {
      x: 8.3, y: 4.4, w: 4.5, h: 0.3, isTextBox: true,
      fontFace: BODY, fontSize: 13, bold: true, color: INK,
    });
    formula(s, 8.3, 4.75, 4.5, [
      "g   = (.30, .25, .20)",
      "h   = (9.0, 7.0, 5.0)",
      "w   = (.300,.342,.358)",
      "C   = 6.88   mean 7.00",
    ], 11);

    // The lower-left was empty; use it for the intuition the formulae do not convey.
    card(s, M, 4.45, 7.5, 1.65, "The intuition, in one sentence",
      "Three doctors give three opinions. Averaging counts a shared view twice if two of " +
      "them trained together, and ignores that one is far more experienced. A fuzzy " +
      "measure can express BOTH - because it scores every combination of doctors, not " +
      "just each doctor.", { headSize: 14, size: 12.5 });
    s.addNotes("Do not rush this slide. The key intuition: a weighted average cannot express that two models overlap. The Choquet integral can, because it scores every subset.");
  }

  // ---- 5b. THE FEATURE MATHEMATICS ---------------------------------------
  {
    const s = contentSlide("Before fusion: how 4000 raw samples become 193 numbers");
    s.addText(
      "A heartbeat mixes a sharp spike (QRS) with broad waves (P and T). The db4 wavelet " +
      "transform splits the window into 8 sub-signals by speed, and each gets the same " +
      "10 measurements: 8 x 10 = 80 per signal, x2 signals = the paper's 160.",
      { x: M, y: 1.4, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 14, color: INK }
    );
    formula(s, M, 2.05, 6.6, [
      "Hjorth parameters (SM, SC):",
      "  Mobility   = sqrt( var(x') / var(x) )",
      "  Complexity = Mobility(x') / Mobility(x)",
      "",
      "Shannon entropy (SE), over amplitude bins p_i:",
      "  SE = - SUM_i  p_i * log2(p_i)",
      "",
      "Correlation dimension (CD), the log-log slope:",
      "  CD = lim(r->0)  d log C(r) / d log r",
    ], 11.5);

    table(s, [
      ["Symbol", "What it measures"],
      ["Kur, Ske", "How spiky / how lopsided"],
      ["SM, SC", "Wiggle rate, and its variation"],
      ["FD", "How jagged the line is"],
      ["CD", "How many processes drive it"],
      ["C0", "Fraction that is irregular"],
      ["PSE", "Energy spread across frequencies"],
      ["KE, SE", "How unpredictable / how informative"],
    ], 7.4, 2.05, 5.25, { colW: [1.4, 3.85], rowH: 0.3, size: 11 });

    card(s, 7.4, 4.65, 5.25, 1.45, "Plus 33 morphological features",
      "QT and QTc = QT/sqrt(RR), ST level, T-wave amplitude and sharpness, SDNN, RMSSD, " +
      "pNN50, and PPG pulse shape. Each is citable to the glucose mechanism.",
      { headSize: 13, size: 11.5 });
    note(s, "We use the paper's exact choices: db4 wavelet, 7 decomposition levels, these ten features.");
    s.addNotes("If asked why a wavelet: measuring 'irregularity' means something different for the fast QRS than for the slow T wave. Separating them lets each be described on its own terms.");
  }

  // ---- 6. THE SPLIT QUESTION ---------------------------------------------
  {
    const s = contentSlide("Finding 1: how you split the data changes the answer more than the model does");
    s.addText(
      "Consecutive windows from one person are extremely similar. Shuffle them all and " +
      "split at random, and the SAME patient appears in training and test - so a model " +
      "can recognise the person instead of learning about glucose.",
      { x: M, y: 1.42, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 15, color: INK }
    );
    const prot = [
      ["1. Random window", "Shuffle everything, split at random",
       "The same patient on both sides. This is what most published work reports.", LIGHT],
      ["2. Subject-aware", "No patient on both sides",
       "The model must now generalise across people, not memorise them.", "E3EEF0"],
      ["3. Leave-one-subject-out", "Train on 9, test on the 10th",
       "The deployment case: a brand-new patient. (Not completed - we do not claim it.)", INK],
    ];
    prot.forEach(([t, how, why, fill], i) => {
      const x = M + i * 4.12;
      const dark = i === 2;
      s.addShape(pres.ShapeType.roundRect, {
        x, y: 2.15, w: 3.85, h: 2.4, rectRadius: 0.06,
        fill: { color: fill }, line: { color: fill },
      });
      s.addText(t, { x: x + 0.24, y: 2.33, w: 3.4, h: 0.33, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 14, bold: true, color: dark ? MINT : INK });
      s.addText(how, { x: x + 0.24, y: 2.7, w: 3.4, h: 0.5, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11.5, color: dark ? PAPER : TEAL, italic: true });
      s.addText(why, { x: x + 0.24, y: 3.22, w: 3.4, h: 1.15, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11.5, color: dark ? "D6E6EA" : INK });
    });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.85, w: W - 2 * M, h: 1.25, rectRadius: 0.05,
      fill: { color: "FBEFEF" }, line: { color: "FBEFEF" },
    });
    s.addText(
      "A 2026 study re-tested five published PPG-glucose methods this way. The best scored " +
      "R-squared 0.60 under random splitting and -0.08 under participant-aware splitting - " +
      "no better than guessing the mean.",
      { x: M + 0.3, y: 5.07, w: W - 2 * M - 0.6, h: 0.85, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 13.5, color: INK }
    );
    note(s, "Reassessing the Feasibility of PPG-Based Non-Invasive Blood Glucose Level Estimation, arXiv:2608.01820 (2026).");
  }

  // ---- 7. THE RESULT -----------------------------------------------------
  {
    const s = contentSlide("Our result: the same model, the same data, collapses from R2 +0.15 to -0.22");
    table(s, [
      ["", "Random split", "Subject-aware split"],
      ["Best single model (R2)", "+0.194", "-0.243"],
      ["Choquet fusion (R2)", "+0.149", "-0.223"],
      ["No-skill baseline (R2)", "-0.000", "-0.074"],
      ["Choquet RMSE (mmol/L)", "2.324", "2.786"],
      ["Baseline RMSE (mmol/L)", "2.520", "2.610"],
    ], M, 1.6, 7.6, { colW: [3.2, 2.2, 2.2], rowH: 0.36, size: 12.5 });

    card(s, 8.35, 1.6, 4.45, 1.5, "Read the R2 column first",
      "It is the one metric that exposes a model doing no better than predicting the " +
      "average. Negative means worse than guessing.", { headSize: 13, size: 12 });

    s.addShape(pres.ShapeType.roundRect, {
      x: 8.35, y: 3.25, w: 4.45, h: 1.55, rectRadius: 0.06,
      fill: { color: "FBEFEF" }, line: { color: "FBEFEF" },
    });
    s.addText("Under the honest split", {
      x: 8.6, y: 3.42, w: 3.95, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: RED,
    });
    s.addText(
      "every model - including the fusion - is WORSE than simply guessing that patient's " +
      "average glucose.",
      { x: 8.6, y: 3.76, w: 3.95, h: 0.9, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: INK }
    );

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.25, w: 7.6, h: 1.85, rectRadius: 0.06,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText(
      "Same data. Same model. Same code.\nOnly the split changed.",
      { x: M + 0.3, y: 4.5, w: 7.0, h: 0.8, isTextBox: true, margin: 0,
        fontFace: HEAD, fontSize: 22, bold: true, color: PAPER }
    );
    s.addText(
      "This independently replicates the 2026 finding above - on a different signal (ECG), " +
      "a different dataset, and a different model class (fuzzy-integral fusion, not CNNs).",
      { x: M + 0.3, y: 5.35, w: 7.0, h: 0.6, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: "D6E6EA" }
    );
  }

  // ---- 7b. THE PARKES PICTURE --------------------------------------------
  {
    const s = contentSlide("What the failure looks like: predictions form a flat band, whatever the truth");
    s.addImage({ path: "figures/results/fig10_parkes_subject_aware.png",
                 x: M, y: 1.35, w: 4.85, h: 4.85 });
    bullets(s, [
      "This is the paper's Fig. 10 - the Parkes error grid - drawn on our subject-aware predictions.",
      "The horizontal axis is the true glucose; the vertical axis is what the model predicted.",
      "A good model would produce a diagonal cloud along the dotted line.",
      "Ours is a HORIZONTAL band: whether the patient was at 4 or at 20 mmol/L, the model predicts roughly 6-9.",
      "That is what 'no better than predicting the average' looks like - and it is invisible in the zone percentages, because a flat band still lands inside zones A and B.",
    ], 5.85, 1.5, 6.95, 4.0, 14);
    note(s, "30,830 predictions, Choquet fusion, subject-aware split.");
    s.addNotes("This is the single most convincing slide. Point at the horizontal band. A model that had learned anything would slope upward along the diagonal.");
  }

  // ---- 8. THE MASKING ----------------------------------------------------
  {
    const s = contentSlide("Finding 2: the clinical metric everyone reports cannot tell the difference");
    s.addText(
      "The Parkes error grid scores predictions by whether acting on them would harm the " +
      "patient. Zone A+B is the headline clinical number in this field. Under the " +
      "subject-aware split:",
      { x: M, y: 1.42, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 15, color: INK }
    );
    table(s, [
      ["Method", "R2", "Zone A", "Zone A+B"],
      ["Choquet fusion", "-0.223", "41.9%", "89.4%"],
      ["Random Forest", "-0.249", "40.4%", "88.2%"],
      ["Gradient Boosting", "-0.243", "40.4%", "88.5%"],
      ["No-skill baseline", "-0.074", "43.7%", "90.0%"],
    ], M, 2.15, 7.4, { colW: [2.6, 1.6, 1.6, 1.6], rowH: 0.36, size: 13 });

    s.addShape(pres.ShapeType.roundRect, {
      x: 8.15, y: 2.15, w: 4.65, h: 2.1, rectRadius: 0.06,
      fill: { color: "FBEFEF" }, line: { color: "FBEFEF" },
    });
    s.addText("The baseline wins on BOTH", {
      x: 8.4, y: 2.33, w: 4.15, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: RED,
    });
    s.addText(
      "A constant predictor - which explains zero variance by construction - has the best " +
      "R-squared AND the best clinical score.\n\nShown only the Parkes column, a reader " +
      "sees 88-90% across the board and concludes the method works.",
      { x: 8.4, y: 2.67, w: 4.15, h: 1.45, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12, color: INK }
    );

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.55, w: W - 2 * M, h: 1.45, rectRadius: 0.06,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText("Why this happens, and what to do about it", {
      x: M + 0.3, y: 4.74, w: 8, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: MINT,
    });
    s.addText(
      "Most glucose readings sit in a narrow band around normal, so predicting a constant " +
      "already lands the large majority of points in the acceptable zones. Zone metrics " +
      "cannot certify a model on their own - they must be reported next to a baseline " +
      "computed on the same folds.",
      { x: M + 0.3, y: 5.08, w: W - 2 * M - 0.6, h: 0.8, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 13, color: PAPER }
    );
  }

  // ---- 8b. THE MASKING, AS A PICTURE -------------------------------------
  {
    const s = contentSlide("The same seven models, two metrics, opposite verdicts");
    s.addImage({ path: "figures/results/fig_zone_vs_r2.png",
                 x: M, y: 1.45, w: 12.1, h: 3.9 });
    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 5.55, w: W - 2 * M, h: 1.15, rectRadius: 0.05,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText(
      "The red bar is a model that predicts a CONSTANT. On the left it has the LONGEST " +
      "bar - the best clinical score of anything tested. On the right it has the " +
      "SHORTEST - because it is the least-bad R-squared. One metric says it is the " +
      "winner; the other says nothing here works.",
      { x: M + 0.3, y: 5.75, w: W - 2 * M - 0.6, h: 0.8, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 13.5, color: PAPER }
    );
    s.addNotes("If you only have time for one point about evaluation, make it this one: never report a clinical zone score without the baseline beside it.");
  }

  // ---- 9. THE DEGENERACY -------------------------------------------------
  {
    const s = contentSlide("Finding 3: the fusion had degenerated into a minimum operator");
    s.addText(
      "If every model gets the SAME density, the fuzzy measure becomes symmetric - it " +
      "depends only on how many models are in a group, never which ones. The Choquet " +
      "integral then reduces to a fixed function of the sorted predictions:",
      { x: M, y: 1.4, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 14, color: INK }
    );
    formula(s, M, 2.05, 6.4, [
      "w_j = g * beta^(j-1),   beta = 1 + lambda*g",
      "",
      "j = 1 is the LARGEST prediction",
      "",
      "sum(g) < 1  =>  lambda > 0  =>  beta > 1",
      "so weight GROWS toward the smallest.",
    ], 12);

    table(s, [
      ["g", "w(largest)", "w(middle)", "w(smallest)", "becomes"],
      ["0.010", "0.010", "0.095", "0.895", "minimum"],
      ["0.100", "0.100", "0.254", "0.646", "rank-weighted"],
      ["0.333", "0.333", "0.333", "0.333", "arithmetic mean"],
    ], 7.15, 2.05, 5.55, { colW: [0.75, 1.1, 1.1, 1.2, 1.4], rowH: 0.32, size: 11 });

    s.addText("In our runs the densities sat at the 0.01 floor. So we checked the output against min():", {
      x: 7.15, y: 3.45, w: 5.65, h: 0.55, isTextBox: true,
      fontFace: BODY, fontSize: 12.5, color: INK,
    });
    stat(s, 7.15, 4.0, 2.7, "0.998", "correlation with min()", RED);
    stat(s, 10.05, 4.0, 2.7, "0.04", "mean gap to min()\n(mmol/L)", RED);

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.55, w: 6.4, h: 1.55, rectRadius: 0.06,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText(
      "The published method's distinguishing component was returning min(m1, m2, m3).",
      { x: M + 0.28, y: 4.75, w: 5.85, h: 0.6, isTextBox: true, margin: 0,
        fontFace: HEAD, fontSize: 16, bold: true, color: PAPER }
    );
    s.addText(
      "And it is not only a bug: under honest evaluation the models genuinely cannot " +
      "generalise, so the densities floor legitimately - the fusion silently turns into " +
      "min() exactly when you most need it to help.",
      { x: M + 0.28, y: 5.35, w: 5.85, h: 0.65, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11.5, color: "D6E6EA" }
    );
    note(s, "The symmetric-measure/OWA equivalence is standard theory (Grabisch; Marichal). New here: a saturating density estimator induces it by accident.");
  }

  // ---- 9b. THE DERIVATION ------------------------------------------------
  {
    const s = contentSlide("The derivation, so you can reproduce it on a board");
    s.addText("With all densities equal to g, the Sugeno measure of a group depends only on its SIZE:", {
      x: M, y: 1.4, w: W - 2 * M, h: 0.35, isTextBox: true,
      fontFace: BODY, fontSize: 14, color: INK,
    });
    formula(s, M, 1.85, 7.9, [
      "Sugeno recursion, applied j times:",
      "",
      "    g(A_j) = [ (1 + lambda*g)^j  -  1 ] / lambda",
      "",
      "The weight on the j-th largest prediction is the growth:",
      "",
      "    w_j = g(A_j) - g(A_j-1)",
      "        = [ beta^j - beta^(j-1) ] / lambda      (beta = 1+lambda*g)",
      "        = g * beta^(j-1)",
      "",
      "Check it sums to 1:",
      "",
      "    SUM_j w_j = g*(beta^N - 1)/(beta - 1)",
      "              = (beta^N - 1)/lambda  =  g(X)  =  1",
    ], 11.5);

    bullets(s, [
      "Step 1 is just the Sugeno rule g(A u B) = g(A)+g(B)+lambda*g(A)*g(B) applied repeatedly to identical densities.",
      "Step 2 is the definition of the Choquet weights.",
      "Step 3 uses the geometric series, and the last equality is the boundary condition g(X)=1.",
      "The conclusion: the weights depend only on RANK and on g - never on which model is which.",
    ], 8.75, 1.85, 4.05, 3.1, 12);

    s.addShape(pres.ShapeType.roundRect, {
      x: 8.75, y: 5.05, w: 4.05, h: 1.35, rectRadius: 0.06,
      fill: { color: "FBEFEF" }, line: { color: "FBEFEF" },
    });
    s.addText("Why beta > 1 matters", {
      x: 9.0, y: 5.22, w: 3.55, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12.5, bold: true, color: RED,
    });
    s.addText(
      "Weak models give sum(g) < 1, hence lambda > 0, hence beta > 1 - so w_j GROWS " +
      "with j, piling weight on the smallest prediction.",
      { x: 9.0, y: 5.54, w: 3.55, h: 0.75, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11.5, color: INK }
    );
  }

  // ---- 10. NON-DETERMINISM -----------------------------------------------
  {
    const s = contentSlide("Finding 4: a standard feature library returns different answers for identical input");
    s.addText(
      "One of the ten features is the correlation dimension, estimated as the slope of a " +
      "log-log plot. The library fits that slope with RANSAC - a method that tries RANDOM " +
      "subsets - and does not seed it.",
      { x: M, y: 1.42, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 15, color: INK }
    );
    table(s, [
      ["Slope fitting method", "Distinct values from 30 identical calls"],
      ["RANSAC (the library default)", "5"],
      ["Ordinary least squares", "1"],
    ], M, 2.15, 7.0, { colW: [3.4, 3.6], rowH: 0.38, size: 13 });

    stat(s, M, 3.4, 3.4, "72%", "of correlation-dimension\nvalues changed", RED);
    stat(s, M + 3.6, 3.4, 3.4, "177", "other features:\nbit-identical", TEAL);

    card(s, 7.55, 2.15, 5.25, 1.9, "Why the second number matters",
      "The 177 unchanged features are the control. They prove the differences came from " +
      "the random fit, not from anything else we changed.",
      { headSize: 13, size: 12 });
    card(s, 7.55, 4.2, 5.25, 1.4, "The fix",
      "One argument - fit the slope with least squares. Both methods agree on the typical " +
      "value; only one always returns it.", { headSize: 13, size: 12 });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.95, w: 7.0, h: 1.15, rectRadius: 0.05,
      fill: { color: "FBEFEF" }, line: { color: "FBEFEF" },
    });
    s.addText(
      "Any result computed from these features was irreproducible - nobody re-running the " +
      "pipeline, including us, would get the same numbers. Found only because we tested " +
      "whether identical input gives identical output.",
      { x: M + 0.28, y: 5.14, w: 6.45, h: 0.85, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: INK }
    );
  }

  // ---- 11. CONTRIBUTIONS -------------------------------------------------
  {
    const s = contentSlide("What this contributes, and what we cannot claim");
    const items = [
      ["1", "An open reproduction on open data",
       "All three stages rebuilt from the paper, run on PhysioCGM: 30,830 windows, 193 features, 10 patients."],
      ["2", "A degeneracy theorem with a runnable diagnostic",
       "When densities saturate, the Sugeno-lambda Choquet integral provably becomes a fixed order statistic. Verified at correlation 0.998."],
      ["3", "Evidence that the evaluation protocol dominates",
       "R-squared +0.149 to -0.223 on identical data, and a constant predictor beating every model on the clinical metric."],
      ["4", "A reproducibility failure in a standard library",
       "An unseeded random fit changing up to 72% of values between identical runs."],
    ];
    items.forEach(([n, t, d], i) => {
      const y = 1.45 + i * 0.95;
      s.addShape(pres.ShapeType.ellipse, {
        x: M, y: y + 0.03, w: 0.42, h: 0.42,
        fill: { color: INK }, line: { color: INK },
      });
      s.addText(n, { x: M, y: y + 0.09, w: 0.42, h: 0.3, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 13, bold: true, color: MINT, align: "center" });
      s.addText(t, { x: M + 0.62, y, w: 11.5, h: 0.3, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 14.5, bold: true, color: INK });
      s.addText(d, { x: M + 0.62, y: y + 0.32, w: 11.5, h: 0.55, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12, color: MUTED });
    });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 5.35, w: W - 2 * M, h: 1.35, rectRadius: 0.06,
      fill: { color: "FFF6E5" }, line: { color: "FFF6E5" },
    });
    s.addText("What we cannot claim", {
      x: M + 0.3, y: 5.52, w: 6, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: "8A5A00",
    });
    s.addText(
      "That the method never works. We show it does not work ON THIS DATASET UNDER HONEST " +
      "EVALUATION, and that its fusion component was inactive. Our morphological branch " +
      "differs from theirs, ten patients is small, and leave-one-subject-out was not " +
      "completed - so we do not report it.",
      { x: M + 0.3, y: 5.85, w: W - 2 * M - 0.6, h: 0.75, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: INK }
    );
  }

  // ---- 12. REFERENCES ----------------------------------------------------
  {
    const s = contentSlide("References");
    const refs = [
      "Li, J. et al. \"Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG Feature Fusion and Weight-Based Choquet Integral Multimodel Approach.\" IEEE Trans. Neural Networks and Learning Systems, 35(10), 2024.",
      "PhysioCGM: a multimodal physiological dataset for non-invasive blood glucose estimation. Scientific Data, 2025. figshare 28136294 (CC0).",
      "Reassessing the Feasibility of PPG-Based Non-Invasive Blood Glucose Level Estimation. arXiv:2608.01820, 2026.",
      "Parkes, J. L. et al. \"A New Consensus Error Grid to Evaluate the Clinical Significance of Inaccuracies in the Estimation of Blood Glucose.\" Diabetes Care, 23(8), 2000.",
      "Pfutzner, A. et al. \"Technical Aspects of the Parkes Error Grid.\" J. Diabetes Science and Technology, 7(5), 2013.",
      "Eckert, B. & Agardh, C.-D. \"Hypoglycaemia leads to an increased QT interval in normal men.\" Clinical Physiology, 18(6), 1998.",
      "Grabisch, M. \"Fuzzy integral in multicriteria decision making.\" Fuzzy Sets and Systems, 69(3), 1995.",
      "Marichal, J.-L. \"On Choquet and Sugeno integrals as aggregation functions.\" Fuzzy Measures and Integrals, 2000.",
      "Sugeno, M. Theory of fuzzy integrals and its applications. PhD thesis, Tokyo Institute of Technology, 1974.",
      "Hjorth, B. \"EEG analysis based on time domain properties.\" Electroencephalography and Clinical Neurophysiology, 29(3), 1970.",
    ];
    s.addText(
      refs.map((t, i) => ({ text: t, options: { bullet: false, breakLine: i !== refs.length - 1 } })),
      { x: M, y: 1.45, w: W - 2 * M, h: 4.6, isTextBox: true,
        fontFace: BODY, fontSize: 11.5, color: INK, paraSpaceAfter: 7 }
    );
    s.addText("Full technical write-up, including every derivation: WRITEUP.md in the project repository.", {
      x: M, y: 6.2, w: W - 2 * M, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 12.5, color: TEAL, bold: true,
    });
  }
};
