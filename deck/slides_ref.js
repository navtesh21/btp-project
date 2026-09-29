/* Slide content for the reference-style deck. See build_ref_style.js for the styling. */
const D = require("./build_ref_style");
const {
  pres, FONT, BLACK, GREY, W, H, M,
  section, subhead, card, body, takeaway, table, equation, figure, titleSlide,
} = D;

module.exports = function build() {

  // ---- 1  TITLE ----------------------------------------------------------
  titleSlide();

  // ---- 2  CONTENTS -------------------------------------------------------
  {
    const s = pres.addSlide();
    s.background = { color: "FFFFFF" };
    s.addText("Contents", {
      x: M, y: 0.42, w: W - 2 * M, h: 0.62, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 21, bold: true, color: BLACK, align: "center",
    });
    s.addShape(pres.ShapeType.line, { x: M, y: 1.12, w: W - 2 * M, h: 0.004,
      line: { color: BLACK, width: 1.1 } });
    const items = [
      ["1.", "Introduction — Background and Motivation"],
      ["2.", "Literature Survey — The Method Under Test"],
      ["3.", "Literature Survey — Evaluation Practice in the Field"],
      ["4.", "Research Gaps and Limitations Identified"],
      ["5.", "Aim and Objectives"],
      ["6.", "Problem Formulation — Fuzzy Measures and the Choquet Integral"],
      ["7.", "Methodology I — Pipeline, Signals and Dataset"],
      ["8.", "Methodology II — Feature Extraction and Selection"],
      ["9.", "Results I — Performance Under Three Split Protocols"],
      ["10.", "Results II — Parkes Error Grid and Prediction Trace"],
      ["11.", "Results III — Feature-Set Ablation"],
      ["12.", "Results IV — Degeneracy of the Fusion Operator"],
      ["13.", "Future Work and Expected Outcomes"],
      ["14.", "Conclusion and References"],
    ];
    items.forEach(([n, t], i) => {
      const col = i < 7 ? 0 : 1;
      const row = i % 7;
      const x = M + 0.4 + col * 6.1;
      const y = 1.72 + row * 0.55;
      s.addText(n, { x, y, w: 0.5, h: 0.42, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 13, color: BLACK, align: "right",
        valign: "middle" });
      s.addText(t, { x: x + 0.62, y, w: 5.2, h: 0.42, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 13, color: BLACK, valign: "middle" });
    });
    D.footer(s);
  }

  // ---- 3  INTRODUCTION ---------------------------------------------------
  {
    const s = section(1, "Introduction — Background and Motivation");
    card(s, M, 1.32, 6.0, 3.15, "The clinical problem", [
      "Blood glucose must remain within 3.9–10.0 mmol/L. Below 3.9 causes seizure and "
      + "coma within minutes; above 10.0 causes nerve, eye and kidney damage over years.",
      "Every accurate measurement available today breaks the skin: a finger-prick four "
      + "to ten times daily, or a continuous glucose monitor whose filament is replaced "
      + "every 10–14 days.",
      "Approximately 590 million adults worldwide manage diabetes in this way.",
    ]);
    card(s, 7.05, 1.32, 5.55, 3.15, "Why the heart carries the signal", [
      "Hypoglycaemia triggers adrenaline release, which drives potassium into cells. "
      + "Potassium governs cardiac repolarisation, so the ECG QT interval lengthens.",
      "Hyperglycaemia suppresses vagal tone and impairs coronary microcirculation, "
      + "altering ST level, T-wave morphology and heart-rate variability.",
      "Both signals can be acquired painlessly: ECG from a chest strap, PPG from a "
      + "wrist-worn device.",
    ]);
    card(s, M, 4.65, 11.85, 1.5, "The distinction that governs this work", [
      "The mechanism above supports DETECTING a dysglycaemic event. That is a "
      + "classification problem, and published ECG methods report 84–94% accuracy "
      + "on it. It does not "
      + "establish that the absolute concentration can be recovered from the waveform, "
      + "which is a regression problem. This project evaluates the regression claim.",
    ]);
    takeaway(s, "A painless, continuous, zero-consumable glucose monitor would remove a "
                + "lifelong burden — if the signal genuinely carries the information.");
  }

  // ---- 4  LITERATURE SURVEY I --------------------------------------------
  {
    const s = section(2, "Literature Survey — The Method Under Test");
    subhead(s, "Li et al., IEEE Trans. Neural Networks and Learning Systems 35(10), 2024 "
               + "— reported performance against prior methods");
    table(s, [
      ["Ref.", "Method", "RMSE (mmol/L)", "MARD (%)", "Zone A (%)", "Zone A+B (%)"],
      ["[2]", "CNN-RNN", "1.66", "14.93", "75.46", "99.35"],
      ["[3]", "ResNets", "1.63", "15.22", "75.18", "99.26"],
      ["[4]", "Convolutional denoising autoencoder", "1.99", "20.67", "60.88", "98.56"],
      ["[5]", "CNN with multisegment fusion", "1.61", "14.71", "76.96", "98.94"],
      ["[1]", "SFF-WCIM — the method reproduced here", "1.49", "13.42", "80.09", "99.49"],
    ], M, 1.72, 11.85, { colW: [0.8, 4.65, 1.75, 1.4, 1.5, 1.75], rowH: 0.36,
                         size: 11, boldRow: 5, align: "center", textCols: 2 });
    card(s, M, 4.15, 11.85, 1.65, "Why this claim required independent checking", [
      "1.49 mmol/L approaches the accuracy of approved continuous glucose monitors, "
      + "which report a MARD of 10–12%. The authors released their source code but not "
      + "their recordings, which are private. The result had therefore never been "
      + "evaluated on a cohort the authors did not themselves select.",
    ]);
    takeaway(s, "Survey takeaway: the reported accuracy is the strongest in its class, "
                + "and has never been independently verified.");
  }

  // ---- 5  LITERATURE SURVEY II -------------------------------------------
  {
    const s = section(3, "Literature Survey — Evaluation Practice in the Field");
    subhead(s, "Recent work questioning whether reported results survive rigorous evaluation");
    table(s, [
      ["Study", "Finding relevant to this project"],
      ["Reassessing PPG-Based Blood Glucose\nLevel Estimation, arXiv:2608.01820 (2026)",
       "Re-evaluated five published PPG-glucose methods. The best scored R² = 0.60 under a random\n"
       + "split and −0.08 under a participant-aware split, no better than predicting the mean.\n"
       + "Over 90% of predictions fell within Clarke Zone A+B, including the baseline."],
      ["Advances in ECG-Based Non-Invasive Blood\nGlucose Monitoring Technology (review, 2026)",
       "Identifies record-level splitting as a field-wide source of data leakage producing\n"
       + "optimistic estimates; notes that most studies use fewer than 30 subjects; concludes that\n"
       + "current methods do not reach the 10–12% MARD of approved devices."],
      ["Grabisch (1995); Marichal (2000)",
       "Aggregation theory: a Choquet integral taken with respect to a symmetric fuzzy measure\n"
       + "reduces to an ordered weighted average. This bounds what we claim as novel in Section 12."],
    ], M, 1.72, 11.85, { colW: [3.7, 8.15], rowH: 1.12, size: 11 });
    takeaway(s, "Survey takeaway: the first two studies motivate our three-protocol design; "
                + "the third establishes which part of our theoretical result is prior work.");
  }

  // ---- 6  RESEARCH GAPS --------------------------------------------------
  {
    const s = section(4, "Research Gaps and Limitations Identified");
    const gaps = [
      ["No independent validation",
       "Source code released, data withheld. The result has never been tested on a cohort "
       + "selected by anyone other than the authors."],
      ["Evaluation protocol not controlled",
       "Performance is reported under a random window-level split, in which the same "
       + "participant appears in both training and test sets. Windows from one individual "
       + "are strongly correlated, so a model may identify the participant rather than "
       + "learn the glucose relationship."],
      ["Clinical metrics reported without a reference point",
       "Parkes Zone A+B is presented as evidence of clinical readiness, with no no-skill "
       + "baseline reported alongside, so the reader cannot determine how much of that "
       + "score is attributable to the method."],
      ["Fusion behaviour never audited",
       "The fuzzy densities that parameterise the Choquet integral are estimated from model "
       + "performance, but are neither reported nor checked for degeneracy."],
      ["Reproducibility of the feature pipeline unverified",
       "No check that identical input produces identical features."],
    ];
    gaps.forEach(([h, t], i) => {
      const y = 1.35 + i * 0.94;
      s.addText(`${i + 1}.`, { x: M, y, w: 0.4, h: 0.3, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 12, bold: true, color: BLACK });
      s.addText(h, { x: M + 0.45, y, w: 11.4, h: 0.28, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 12.5, bold: true, color: BLACK });
      s.addText(t, { x: M + 0.45, y: y + 0.3, w: 11.4, h: 0.6, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 11, color: BLACK });
    });
    takeaway(s, "Each gap above corresponds directly to one of the findings reported in "
                + "Sections 9 to 12.", H - 1.0);
  }

  // ---- 7  AIM AND OBJECTIVES ---------------------------------------------
  {
    const s = section(5, "Aim and Objectives");
    card(s, M, 1.32, 11.85, 1.0, "", [
      "Aim: to determine whether the reported accuracy of the SFF-WCIM method survives "
      + "independent reproduction on open data under leakage-controlled evaluation.",
    ], 13);
    subhead(s, "Objectives", 2.5);
    const objs = [
      "Rebuild all three stages of the published method from its description.",
      "Evaluate on PhysioCGM: ten Type-1 participants with simultaneous ECG, PPG and CGM, "
      + "released into the public domain.",
      "Evaluate under three progressively stricter split protocols, reporting a no-skill "
      + "baseline computed on the same folds beside every result.",
      "Audit the fusion operator itself: recover the fuzzy densities and verify that the "
      + "integral still discriminates between the base models.",
      "Verify that the feature-extraction pipeline is deterministic.",
    ];
    objs.forEach((t, i) => {
      const y = 2.95 + i * 0.44;
      s.addText(`${i + 1}.`, { x: M + 0.3, y, w: 0.35, h: 0.4, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 12, color: BLACK, align: "right",
        valign: "middle" });
      s.addText(t, { x: M + 0.75, y, w: 11.0, h: 0.4, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 12, color: BLACK, valign: "middle" });
    });
    card(s, M, 5.25, 11.85, 1.45, "Scope and limitations", [
      "The authors' dataset is unavailable, so this reproduces the METHOD on different "
      + "data rather than replicating the experiment. The spatial morphological branch is "
      + "implemented with hand-crafted physiological features rather than a ResNet, as no "
      + "GPU was available; this deviation is documented and examined in the ablation.",
    ], 11);
  }

  // ---- 8  PROBLEM FORMULATION --------------------------------------------
  {
    const s = section(6, "Problem Formulation — Fuzzy Measures and the Choquet Integral");
    body(s, [
      "Given a 16 s window of ECG and PPG preceding a CGM reading, predict the glucose "
      + "concentration y. Three regressors produce estimates h₁, h₂, h₃, which must be "
      + "combined into a single value.",
      "A weighted average assigns importance to each model individually and therefore "
      + "cannot express that two models overlap. A fuzzy measure assigns importance to "
      + "every subset; the Sugeno λ-measure generates all 2ᴺ subset values from one "
      + "density per model:",
    ], M, 1.3, 11.85, 1.1, 12);
    equation(s, "sugeno_union", 1.55, 2.6, 5.9);
    equation(s, "sugeno_lambda", 8.6, 2.45, 2.9);
    equation(s, "choquet", 2.4, 3.90, 6.3);
    card(s, M, 5.35, 11.85, 1.15, "", [
      "λ is fixed by the boundary condition g(X) = 1.  Σgᵢ = 1 gives λ = 0, and the "
      + "integral reduces exactly to a weighted average.  Σgᵢ > 1 gives λ < 0, an overlap "
      + "penalty.  Σgᵢ < 1 gives λ > 0, a synergy bonus.  Sorting is what allows subset "
      + "importance to enter: the weight a prediction receives depends on its rank.",
    ], 11);
  }

  // ---- 9  METHODOLOGY I --------------------------------------------------
  {
    const s = section(7, "Methodology I — Pipeline, Signals and Dataset");
    body(s, [
      { text: "Level 1 — acquisition and conditioning.", bold: true },
      "16 s windows (approximately 20 cardiac cycles) preceding each CGM reading; "
      + "Butterworth band-pass 0.5–40 Hz for ECG and 0.5–8 Hz for PPG, the latter because "
      + "64 Hz sampling limits the representable band to 32 Hz.",
      { text: "Level 2 — feature extraction.", bold: true },
      "db4 DWT to 7 levels yields 8 sub-signals per modality; 10 statistical features each "
      + "(80 per modality, 160 in total), plus 33 morphological features. Selection by the "
      + "intersection of UFS, RFE and L1.",
      { text: "Level 3 — decision fusion.", bold: true },
      "Random Forest, Gradient Boosting and Bagging, combined by the weight-based Choquet "
      + "integral.",
    ], M, 1.3, 11.85, 2.3, 11.5);
    table(s, [
      ["Signal", "Device", "Rate", "Role"],
      ["ECG", "Zephyr BioHarness (chest strap)", "250 Hz", "Electrical activity of the heart"],
      ["PPG (BVP)", "Empatica E4 (wristband)", "64 Hz", "Blood volume pulse, optical"],
      ["Glucose", "Dexcom CGM", "5 min", "Reference value to be predicted"],
    ], M, 3.75, 7.15, { colW: [1.05, 2.55, 0.85, 2.7], rowH: 0.32, size: 10.5 });
    table(s, [
      ["Study population", "Value"],
      ["Participants", "10 (Type-1 diabetes)"],
      ["Paired ECG + PPG windows", "30,830"],
      ["Features per window", "193"],
      ["Glucose range", "2.2 – 21.5 mmol/L"],
      ["Mean / standard deviation", "7.17 / 2.519 mmol/L"],
    ], 8.25, 3.75, 4.35, { colW: [2.55, 1.8], rowH: 0.33, size: 10.5, boldRow: 5 });
    takeaway(s, "The 2.519 mmol/L standard deviation is the RMSE of a model that always "
                + "predicts the mean. That is the no-skill baseline against which every "
                + "result in this work is reported.");
  }

  // ---- 10  METHODOLOGY II ------------------------------------------------
  {
    const s = section(8, "Methodology II — Feature Extraction and Selection");
    body(s, [
      { text: "Temporal statistical features — 10 per sub-signal:", bold: true },
      "kurtosis, skewness, Hjorth mobility and complexity, fractal dimension, correlation "
      + "dimension, C0-complexity, power spectral entropy, Kolmogorov entropy, Shannon entropy.",
    ], M, 1.3, 11.85, 0.7, 11.5);
    equation(s, "hjorth", 0.95, 2.05, 6.1);
    equation(s, "entropy", 7.6, 2.02, 4.4);
    body(s, [
      { text: "Spatial morphological features — measured directly, not learned:", bold: true },
      "QT and corrected QT, ST level, T-wave amplitude and sharpness, QRS duration, and "
      + "heart-rate variability. Each is individually attributable to the mechanism in Section 1.",
    ], M, 2.95, 11.85, 0.7, 11.5);
    equation(s, "qtc", 0.95, 3.62, 5.0);
    body(s, [
      { text: "Feature selection — a feature is retained only if all three criteria "
              + "select it (paper eqs. 5 and 6), fitted within each training fold:", bold: true },
    ], M, 4.55, 11.85, 0.45, 11.5);
    equation(s, "eq5_rfe", 0.95, 5.1, 6.2);
    equation(s, "eq6_lasso", 7.6, 5.15, 4.4);
    takeaway(s, "193 features = 80 ECG temporal + 80 PPG temporal + 19 ECG and 14 PPG "
                + "morphological; selection typically retains ~10. Validation: median "
                + "QTc 0.405 s against a textbook normal of 0.35–0.44 s.", H - 0.95);
  }

  // ---- 11  RESULTS I -----------------------------------------------------
  {
    const s = section(9, "Results I — Performance Under Three Split Protocols");
    subhead(s, "Fused feature set (193 features), 30,830 windows, 10 participants. "
               + "Each method is reported beside the baseline computed on the same folds.");
    table(s, [
      ["Split protocol", "Method", "R²", "RMSE", "MARD (%)", "Zone A (%)", "Zone A+B (%)"],
      ["1. Random window", "Choquet fusion", "+0.149", "2.324", "24.86", "52.87", "93.75"],
      ["    (the paper's protocol)", "No-skill baseline", "−0.000", "2.520", "29.14", "45.34", "90.89"],
      ["2. Subject-aware", "Choquet fusion", "−0.223", "2.786", "31.50", "41.91", "89.39"],
      ["", "No-skill baseline", "−0.074", "2.610", "30.30", "43.74", "90.01"],
      ["3. Leave-one-subject-out", "Choquet fusion", "−0.097", "2.639", "28.86", "45.57", "91.25"],
      ["", "No-skill baseline", "−0.035", "2.564", "29.74", "44.14", "90.57"],
    ], M, 1.75, 11.85, { colW: [2.85, 2.2, 1.15, 1.15, 1.35, 1.5, 1.65],
                         rowH: 0.31, size: 10.5, align: "center", textCols: 2 });
    equation(s, "metrics", 1.0, 4.15, 5.6);
    card(s, 7.3, 4.1, 5.3, 1.75, "Reading the table", [
      "R² = 0 denotes performance identical to predicting the mean; negative values denote "
      + "worse. It is the only metric here that exposes a model which has learned nothing.",
      "Under both leakage-controlled protocols, every method falls behind the "
      + "baseline, the fusion included.",
    ], 11);
    takeaway(s, "Leave-one-subject-out is not worse than subject-aware because it trains on "
                + "9 of 10 participants rather than 4 of 5; the baseline shifts identically. "
                + "The claim is not monotonic degradation, but that both honest splits "
                + "place every method behind the baseline.", H - 1.0);
  }

  // ---- 12  RESULTS II ----------------------------------------------------
  {
    const s = section(10, "Results II — Parkes Error Grid and Prediction Trace");
    figure(s, "fig10_parkes_subject_aware.png", 0.85, 1.3, 4.35, 4.45);
    figure(s, "fig09_timeseries_subject_aware_c2s04.png", 5.5, 1.45, 7.2, 3.05);
    body(s, [
      "A model that had learned the glucose relationship would produce a diagonal cloud "
      + "along the identity line of the error grid, and a prediction trace that tracked "
      + "the reference.",
      "The observed result is a horizontal band: irrespective of whether the reference "
      + "value was 4 or 20 mmol/L, the prediction lies between approximately 6 and 9. "
      + "The trace on the right shows the same behaviour over seventeen days.",
      "That same flat band attains 89.4% in Parkes Zones A+B.",
    ], 5.5, 4.6, 7.2, 1.5, 11);
    takeaway(s, "Equivalent to Figs. 9 and 10 of the source paper. The clinical zone metric "
                + "cannot distinguish this from a working model.", H - 0.95);
  }

  // ---- 13  RESULTS III ---------------------------------------------------
  {
    const s = section(11, "Results III — Feature-Set Ablation");
    subhead(s, "Every feature set evaluated under leave-one-subject-out with Choquet fusion");
    table(s, [
      ["Feature set", "Features", "R²", "RMSE (mmol/L)", "Zone A+B (%)"],
      ["No-skill baseline", "0", "−0.035", "2.564", "90.6"],
      ["Morphological (shape) only", "33", "−0.070", "2.606", "90.8"],
      ["PPG only", "94", "−0.075", "2.612", "90.6"],
      ["Fused (ECG + PPG)", "193", "−0.097", "2.639", "91.3"],
      ["Temporal (wavelet) only", "160", "−0.102", "2.645", "91.5"],
      ["ECG only", "99", "−0.106", "2.650", "91.5"],
    ], M, 1.75, 7.3, { colW: [2.8, 1.05, 1.0, 1.35, 1.1], rowH: 0.31,
                       size: 10.5, boldRow: 1, align: "center" });
    const obs = [
      ["Every feature set falls behind the baseline.",
       "The entire spread, best to worst, is 0.036 in R², and the baseline lies above all of it."],
      ["Fusing the two signals is worse than the better one alone.",
       "PPG alone (−0.075) exceeds the fused set (−0.097). The source paper reports the "
       + "opposite ordering. A 0.03 gap between two failing configurations is not read as evidence."],
      ["Fewer features perform better.",
       "33 features exceed 193. When additional information degrades a model, the model is "
       + "fitting noise rather than signal."],
      ["The clinical score is inversely related to R².",
       "The configurations with the poorest R² carry the highest Zone A+B."],
    ];
    obs.forEach(([h, t], i) => {
      const y = 1.78 + i * 1.02;
      s.addText(h, { x: 8.4, y, w: 4.2, h: 0.5, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 11, bold: true, color: BLACK });
      s.addText(t, { x: 8.4, y: y + 0.32, w: 4.2, h: 0.68, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 10, color: BLACK });
    });
    takeaway(s, "Equivalent to Tables III and IV of the source paper.", H - 0.95);
  }

  // ---- 14  RESULTS IV ----------------------------------------------------
  {
    const s = section(12, "Results IV — Degeneracy of the Fusion Operator");
    body(s, [
      "Two anomalies appeared in the output: the weighted average and the plain average "
      + "agreed to three decimal places (3.927 against 3.927), and every fuzzy density "
      + "sat at the 0.01 clipping floor. With equal densities the Sugeno measure becomes "
      + "symmetric, and the Choquet integral reduces to a fixed order statistic:",
    ], M, 1.28, 11.85, 0.85, 11.5);
    equation(s, "degeneracy", 0.95, 2.2, 5.5);
    equation(s, "degeneracy_limit", 0.95, 4.75, 5.7);
    table(s, [
      ["g", "λ", "w (largest)", "w (middle)", "w (smallest)", "Reduces to"],
      ["0.010", "846.24", "0.010", "0.095", "0.895", "minimum"],
      ["0.100", "15.41", "0.100", "0.254", "0.646", "rank-weighted"],
      ["0.333", "0.00", "0.333", "0.333", "0.333", "arithmetic mean"],
    ], 6.95, 2.2, 5.6, { colW: [0.6, 0.85, 0.96, 0.96, 1.03, 1.2],
                         rowH: 0.3, size: 10, boldRow: 1, align: "center" });
    card(s, 6.95, 3.65, 5.65, 2.45, "Verification against the saved predictions", [
      "corr(Choquet output, minimum of the three models) = 0.998",
      "mean |Choquet − min| = 0.04 mmol/L, against 0.27 to the mean.",
      "The method's distinguishing component was returning min(h₁, h₂, h₃).",
      "This is not solely a defect. Under honest evaluation the base models genuinely "
      + "cannot generalise, so the densities floor legitimately. The fusion degenerates "
      + "precisely when it is most needed.",
    ], 10.5);
    takeaway(s, "The symmetric-measure/OWA equivalence is established theory. The "
                + "contribution here is its identification as a practical failure mode of "
                + "performance-based density estimation, with a closed-form diagnostic.",
             H - 0.9);
  }

  // ---- 15  FUTURE WORK ---------------------------------------------------
  {
    const s = section(13, "Future Work and Expected Outcomes");
    subhead(s, "Future work");
    const fut = [
      ["Reframe from regression to classification.",
       "The physiological mechanism supports detection of hypo- and hyperglycaemic events "
       + "rather than recovery of absolute concentration; published ECG classification "
       + "reports 84–94% accuracy."],
      ["Evaluate per-participant calibration.",
       "The gap between random and subject-aware splitting indicates reliance on "
       + "participant-specific structure, which matches how CGM devices are deployed."],
      ["Implement the ResNet morphological branch as specified,",
       "to isolate the effect of our substitution, given GPU access."],
      ["Apply the degeneracy diagnostic to other Choquet-fusion pipelines.",
       "The failure mode is not specific to glucose estimation."],
    ];
    fut.forEach(([h, t], i) => {
      const y = 1.75 + i * 0.66;
      s.addText(`${i + 1}.`, { x: M + 0.15, y, w: 0.35, h: 0.3, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 11.5, color: BLACK, align: "right",
        valign: "middle" });
      s.addText([{ text: h + " ", options: { bold: true } }, { text: t }], {
        x: M + 0.6, y, w: 11.2, h: 0.6, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 11.5, color: BLACK });
    });
    subhead(s, "Expected outputs and outcomes", 4.5);
    card(s, M, 4.9, 5.8, 1.55, "", [
      "• An open, reproducible implementation of all three stages.",
      "• A degeneracy theorem with a runnable diagnostic, reusable in any domain "
      + "employing fuzzy-integral fusion.",
    ], 10.5);
    card(s, 7.0, 4.9, 5.6, 1.55, "", [
      "• Evidence that evaluation protocol dominates model choice, and that clinical zone "
      + "metrics require a reported baseline.",
      "• A reproducibility defect reported in a widely used nonlinear-features library.",
    ], 10.5);
    takeaway(s, "A short reproducibility paper is planned. Candidate venues: IEEE Journal "
                + "of Biomedical and Health Informatics, or the ML Reproducibility Challenge.",
             H - 0.85);
  }

  // ---- 16  CONCLUSION AND REFERENCES -------------------------------------
  {
    const s = section(14, "Conclusion and References");
    card(s, M, 1.3, 11.85, 1.5, "Conclusion", [
      "The SFF-WCIM method was rebuilt in full and evaluated on 30,830 paired ECG and PPG "
      + "windows from ten participants. Under the source paper's own protocol it learns "
      + "(R² = +0.149). Under either leakage-controlled protocol every method, including "
      + "the fusion, performs worse than a model that predicts the population mean, while "
      + "still attaining 89–91% in the clinical acceptability zones. The fusion operator "
      + "was additionally found to have degenerated into a minimum operator.",
    ], 11.5);
    const refs = [
      "[1] J. Li et al., \"Noninvasive blood glucose monitoring using spatiotemporal ECG and PPG feature fusion and weight-based Choquet integral multimodel approach,\" IEEE Trans. Neural Netw. Learn. Syst., vol. 35, no. 10, pp. 14493–14505, Oct. 2024.",
      "[2] \"PhysioCGM: a multimodal physiological dataset for non-invasive blood glucose estimation,\" Sci. Data, vol. 12, 2025. [Online]. Available: https://doi.org/10.6084/m9.figshare.28136294 (accessed Sep. 25, 2026).",
      "[3] \"Reassessing the feasibility of PPG-based non-invasive blood glucose level estimation,\" arXiv:2608.01820, 2026.",
      "[4] \"Advances in electrocardiogram-based non-invasive blood glucose monitoring technology,\" review, 2026.",
      "[5] J. L. Parkes, S. L. Slatin, S. Pardo and B. H. Ginsberg, \"A new consensus error grid to evaluate the clinical significance of inaccuracies in the estimation of blood glucose,\" Diabetes Care, vol. 23, no. 8, pp. 1143–1148, Aug. 2000.",
      "[6] A. Pfützner, D. C. Klonoff, S. Pardo and J. L. Parkes, \"Technical aspects of the Parkes error grid,\" J. Diabetes Sci. Technol., vol. 7, no. 5, pp. 1275–1281, 2013.",
      "[7] B. Eckert and C.-D. Agardh, \"Hypoglycaemia leads to an increased QT interval in normal men,\" Clin. Physiol., vol. 18, no. 6, pp. 570–575, Nov. 1998.",
      "[8] M. Grabisch, \"Fuzzy integral in multicriteria decision making,\" Fuzzy Sets Syst., vol. 69, no. 3, pp. 279–298, 1995.",
      "[9] J.-L. Marichal, \"On Choquet and Sugeno integrals as aggregation functions,\" in Fuzzy Measures and Integrals, Heidelberg: Physica-Verlag, 2000, pp. 247–272.",
      "[10] B. Hjorth, \"EEG analysis based on time domain properties,\" Electroencephalogr. Clin. Neurophysiol., vol. 29, no. 3, pp. 306–310, 1970.",
    ];
    s.addText("References", {
      x: M, y: 2.95, w: W - 2 * M, h: 0.3, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 13, bold: true, color: BLACK, align: "center",
    });
    s.addText(
      refs.map((t, i) => ({ text: t, options: { breakLine: i !== refs.length - 1 } })),
      { x: M, y: 3.35, w: 11.85, h: 3.0, isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: 9, color: BLACK, paraSpaceAfter: 4 }
    );
  }
};
