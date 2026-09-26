/* Part 1-2: the problem, and the paper we set out to reproduce. Slides 1-9. */
const D = require("./build_deck");
const {
  pres, INK, TEAL, MINT, RED, PAPER, MUTED, LIGHT, HEAD, BODY, W, H, M,
  ecgTrace, sectionSlide, contentSlide, bullets, card, stat, formula, note, table,
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
      "estimation from ECG and PPG signals",
      { x: M, y: 3.3, w: W - 2 * M - 2.2, h: 1.0, isTextBox: true,
        fontFace: BODY, fontSize: 17, color: "AEC6CC" }
    );
    s.addText("B.Tech Final Year Project", {
      x: M, y: 4.55, w: 6, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 13, color: MINT, bold: true, charSpacing: 2,
    });
    s.addText("Navtesh Maken", {
      x: M, y: 5.0, w: 6, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 15, color: PAPER,
    });
    ecgTrace(s, M, 6.0, W - 2 * M, 1.0, MINT, 2.5);
    s.addNotes(
      "This project asks whether a signal we can already measure without pain - the " +
      "electrical activity of the heart - carries enough information to estimate blood " +
      "glucose. We reproduce a 2024 IEEE paper, and report what we found."
    );
  }

  // ---- 2. WHAT IS BLOOD GLUCOSE -----------------------------------------
  {
    const s = contentSlide("Blood glucose is the sugar your body runs on, and it must stay in a narrow band");
    bullets(s, [
      "Glucose is the fuel every cell uses. It arrives from food and is carried in the blood.",
      "Insulin is the hormone that moves glucose out of the blood and into cells.",
      "In Type 1 diabetes the body makes almost no insulin, so glucose stays in the blood and builds up.",
      "Both directions are dangerous: too low starves the brain within minutes; too high damages nerves, eyes, kidneys and blood vessels over years.",
    ], M, 1.55, 6.6, 3.1, 15);

    card(s, 7.55, 1.5, 5.2, 4.5, "The safe range (mmol/L)",
      "", { fill: LIGHT });
    const bands = [
      ["Below 3.9", "HYPOGLYCAEMIA - confusion, seizure, coma", RED],
      ["3.9 - 10.0", "Normal range - the target", "1B7F5E"],
      ["Above 10.0", "HYPERGLYCAEMIA - long-term organ damage", "B26A00"],
    ];
    bands.forEach(([range, meaning, col], i) => {
      const y = 2.15 + i * 1.22;
      s.addShape(pres.ShapeType.roundRect, {
        x: 7.8, y, w: 4.7, h: 1.02, rectRadius: 0.05,
        fill: { color: PAPER }, line: { color: col, width: 1.5 },
      });
      s.addText(range, {
        x: 7.98, y: y + 0.11, w: 1.65, h: 0.36, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 15, bold: true, color: col,
      });
      s.addText(meaning, {
        x: 7.98, y: y + 0.48, w: 4.35, h: 0.48, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11, color: INK,
      });
    });
    note(s, "Thresholds follow the American Diabetes Association standard-of-care definitions.");
    s.addNotes("Start here: the audience may not know what glucose is or why its level matters.");
  }

  // ---- 3. HOW IT IS MEASURED TODAY --------------------------------------
  {
    const s = contentSlide("Measuring it today means breaking the skin, several times a day, for life");
    const methods = [
      ["Finger-prick test", "A lancet draws a drop of blood onto a test strip.",
       "Painful. 4-10 times per day. People skip tests, so dangerous swings go unseen."],
      ["Continuous glucose monitor (CGM)", "A filament sits under the skin and reads glucose every 5 minutes.",
       "Far better, but still invasive. The sensor is replaced every 10-14 days and is expensive."],
    ];
    methods.forEach(([t, how, problem], i) => {
      const x = M + i * 6.25;
      card(s, x, 1.6, 5.85, 2.35, t, how, { headSize: 16, size: 13 });
      s.addShape(pres.ShapeType.roundRect, {
        x, y: 4.12, w: 5.85, h: 1.55, rectRadius: 0.05,
        fill: { color: "FBEFEF" }, line: { color: "FBEFEF" },
      });
      s.addText("The problem", {
        x: x + 0.22, y: 4.28, w: 5.4, h: 0.3, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12, bold: true, color: RED,
      });
      s.addText(problem, {
        x: x + 0.22, y: 4.6, w: 5.4, h: 0.9, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: INK,
      });
    });
    s.addText(
      "Roughly 590 million adults live with diabetes worldwide. Every one of them " +
      "manages it by repeatedly breaking their own skin.",
      { x: M, y: 6.0, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 14, color: INK, italic: true }
    );
    note(s, "Prevalence: International Diabetes Federation, Diabetes Atlas (11th ed., 2025).");
  }

  // ---- 4. THE IDEA -------------------------------------------------------
  {
    const s = contentSlide("So the goal is to read glucose from a signal we can already measure painlessly");
    s.addText(
      "If a sensor you already wear - a chest strap, a smartwatch - carried enough " +
      "information about glucose, monitoring would cost nothing extra and hurt no one.",
      { x: M, y: 1.5, w: W - 2 * M, h: 0.7, isTextBox: true,
        fontFace: BODY, fontSize: 16, color: INK }
    );
    const chain = [
      ["Wearable sensor", "ECG from a chest strap,\nPPG from a wrist device"],
      ["Signal processing", "Clean the waveform,\nmeasure its properties"],
      ["Machine learning", "Map those properties\nto a glucose value"],
      ["Glucose estimate", "A number, in mmol/L,\nwith no needle"],
    ];
    chain.forEach(([t, d], i) => {
      const x = M + i * 3.14;
      const isLast = i === chain.length - 1;
      card(s, x, 2.5, 2.85, 1.95, t, d,
        { fill: isLast ? INK : LIGHT, headColor: isLast ? MINT : INK,
          color: isLast ? PAPER : INK, headSize: 13.5, size: 11.5 });
      if (!isLast) {
        s.addText(">", {
          x: x + 2.86, y: 3.25, w: 0.28, h: 0.4, isTextBox: true, margin: 0,
          fontFace: BODY, fontSize: 20, bold: true, color: TEAL, align: "center",
        });
      }
    });
    s.addText("But this only works if the signal genuinely carries the information. That is the question this project tests.", {
      x: M, y: 4.85, w: W - 2 * M, h: 0.5, isTextBox: true,
      fontFace: BODY, fontSize: 15, color: INK, bold: true,
    });
    ecgTrace(s, M, 5.6, W - 2 * M, 0.9, "C9DCE1", 2);
  }

  // ---- 5. THE PHYSIOLOGY -------------------------------------------------
  {
    const s = contentSlide("There is a real biological reason the heart should react to blood sugar");
    s.addText("Why would an ECG know anything about glucose? Two established mechanisms:", {
      x: M, y: 1.45, w: W - 2 * M, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 15, color: INK,
    });

    card(s, M, 2.0, 5.95, 2.15, "When glucose is LOW (hypoglycaemia)",
      "The body releases adrenaline. Adrenaline activates beta-2 receptors, which drive " +
      "potassium INTO cells, lowering blood potassium. Potassium controls how heart " +
      "muscle cells reset after each beat, so this stretches the recovery phase.",
      { headSize: 14, size: 12.5 });
    s.addText("Visible as: a longer QT interval, flattened T waves", {
      x: M + 0.22, y: 4.28, w: 5.5, h: 0.35, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12, bold: true, color: TEAL,
    });

    card(s, 6.95, 2.0, 5.85, 2.15, "When glucose is HIGH (hyperglycaemia)",
      "Sustained high glucose suppresses vagal (calming) nerve activity and impairs the " +
      "smallest coronary blood vessels, so the heart's electrical recovery and its " +
      "beat-to-beat timing both change.",
      { headSize: 14, size: 12.5 });
    s.addText("Visible as: QT prolongation, ST depression, reduced heart-rate variability", {
      x: 7.17, y: 4.28, w: 5.45, h: 0.35, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12, bold: true, color: TEAL,
    });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.75, w: W - 2 * M, h: 1.25, rectRadius: 0.05,
      fill: { color: "FFF6E5" }, line: { color: "FFF6E5" },
    });
    s.addText("Important caveat, and it shapes everything that follows", {
      x: M + 0.25, y: 4.9, w: W - 2 * M - 0.5, h: 0.32, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: "8A5A00",
    });
    s.addText(
      "These mechanisms explain DETECTING an event - a dangerous low or high. They do " +
      "not promise that the exact glucose number can be read off the waveform. " +
      "Detection is a classification problem; reading the number is a regression " +
      "problem, and it is much harder.",
      { x: M + 0.25, y: 5.24, w: W - 2 * M - 0.5, h: 0.7, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: INK }
    );
    note(s, "Mechanisms: Eckert & Agardh, Clin Physiol 1998; review of ECG-based glucose monitoring, 2026.");
  }

  // ---- 6. SECTION: THE PAPER --------------------------------------------
  sectionSlide("PART 2", "The paper we set out to reproduce",
    "A 2024 IEEE method that reports near-clinical accuracy by fusing two signals and three models");

  // ---- 7. THE PAPER'S CLAIM ---------------------------------------------
  {
    const s = contentSlide("Li et al. report 1.49 mmol/L error by fusing ECG and PPG through a Choquet integral");
    s.addText(
      "\"Noninvasive Blood Glucose Monitoring Using Spatiotemporal ECG and PPG Feature " +
      "Fusion and Weight-Based Choquet Integral Multimodel Approach\"",
      { x: M, y: 1.45, w: W - 2 * M, h: 0.62, isTextBox: true,
        fontFace: BODY, fontSize: 14.5, color: INK, italic: true }
    );
    s.addText("IEEE Transactions on Neural Networks and Learning Systems, vol. 35, no. 10, 2024", {
      x: M, y: 2.05, w: W - 2 * M, h: 0.3, isTextBox: true,
      fontFace: BODY, fontSize: 12, color: MUTED,
    });

    stat(s, M, 2.7, 3.0, "1.49", "RMSE (mmol/L)\ntypical error size", TEAL);
    stat(s, M + 3.15, 2.7, 3.0, "13.42%", "MARD\nrelative error", TEAL);
    stat(s, M + 6.3, 2.7, 3.0, "80.1%", "Parkes Zone A\nclinically harmless", TEAL);
    stat(s, M + 9.45, 2.7, 3.0, "99.5%", "Zone A+B\nclinically acceptable", TEAL);

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.55, w: W - 2 * M, h: 1.45, rectRadius: 0.05,
      fill: { color: LIGHT }, line: { color: LIGHT },
    });
    s.addText("Why this paper is worth reproducing", {
      x: M + 0.25, y: 4.72, w: W - 2 * M - 0.5, h: 0.32, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13.5, bold: true, color: INK,
    });
    s.addText(
      "1.49 mmol/L approaches the accuracy of approved CGM devices. If it holds, it is a " +
      "major result. The authors published their code but not their data - the recordings " +
      "are private - so the claim has never been independently checked on public data. " +
      "That is exactly what a reproduction is for.",
      { x: M + 0.25, y: 5.06, w: W - 2 * M - 0.5, h: 0.8, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 13, color: INK }
    );
  }

  // ---- 8. THE THREE STAGES ----------------------------------------------
  {
    const s = contentSlide("Their method has three stages, and we implement all three");
    const stages = [
      ["STAGE 1", "Collect and clean",
       "Record ECG and PPG. Filter out drift and noise. Cut the signal into short windows, each paired with one glucose reading."],
      ["STAGE 2", "Describe the signal",
       "Turn each window into numbers: statistical 'temporal' features from a wavelet transform, plus 'morphological' features describing waveform shape."],
      ["STAGE 3", "Predict and fuse",
       "Three machine-learning models each predict a glucose value. A Choquet integral combines their three answers into one."],
    ];
    stages.forEach(([tag, title, body], i) => {
      const x = M + i * 4.12;
      s.addShape(pres.ShapeType.roundRect, {
        x, y: 1.6, w: 3.85, h: 3.3, rectRadius: 0.06,
        fill: { color: i === 2 ? INK : LIGHT }, line: { color: i === 2 ? INK : LIGHT },
      });
      s.addText(tag, {
        x: x + 0.25, y: 1.78, w: 3.4, h: 0.3, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11.5, bold: true, charSpacing: 2,
        color: i === 2 ? MINT : TEAL,
      });
      s.addText(title, {
        x: x + 0.25, y: 2.12, w: 3.4, h: 0.45, isTextBox: true, margin: 0,
        fontFace: HEAD, fontSize: 19, bold: true, color: i === 2 ? PAPER : INK,
      });
      s.addText(body, {
        x: x + 0.25, y: 2.68, w: 3.4, h: 2.0, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: i === 2 ? "D6E6EA" : INK,
      });
    });
    s.addText(
      "Stage 3 is where the paper's novelty sits - and, as we will show, where it quietly breaks.",
      { x: M, y: 5.15, w: W - 2 * M, h: 0.45, isTextBox: true,
        fontFace: BODY, fontSize: 15, bold: true, color: INK }
    );
    ecgTrace(s, M, 5.85, W - 2 * M, 0.8, "C9DCE1", 2);
    note(s, "Structure follows Fig. 1 of Li et al., IEEE TNNLS 2024.");
  }

  // ---- 9. WHAT REPRODUCTION MEANS ---------------------------------------
  {
    const s = contentSlide("Reproducing a result means rebuilding it from the paper and testing it on data the authors never saw");
    bullets(s, [
      "We rebuilt every stage from the paper's description, in our own code, from scratch.",
      "We ran it on PhysioCGM: a public dataset of 10 Type-1 diabetes patients with simultaneous ECG, PPG and CGM.",
      "We graded it exactly as the paper does - RMSE, MARD and the Parkes error grid - and then applied stricter tests the paper did not.",
    ], M, 1.5, 7.1, 2.2, 15);

    card(s, 8.15, 1.45, 4.6, 2.35, "Why it matters",
      "A method that only works on its authors' own recordings is not yet a method. " +
      "Independent reproduction on open data is how a claim becomes knowledge.",
      { headSize: 14, size: 12.5 });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.05, w: W - 2 * M, h: 1.95, rectRadius: 0.06,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText("What we actually found", {
      x: M + 0.3, y: 4.25, w: 5, h: 0.35, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: MINT, charSpacing: 1.5,
    });
    s.addText(
      "Four separate ways this pipeline can produce confident, plausible, completely " +
      "wrong numbers - while appearing to work perfectly. Three of them we found by " +
      "checking things nobody normally checks.",
      { x: M + 0.3, y: 4.66, w: W - 2 * M - 0.6, h: 1.1, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 15, color: PAPER }
    );
  }
};
