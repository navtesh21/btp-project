/* Part 3-4: what the signals are, the dataset, and Stage 1. Slides 10-19. */
const D = require("./build_deck");
const {
  pres, INK, TEAL, MINT, RED, PAPER, MUTED, LIGHT, HEAD, BODY, W, H, M,
  ecgTrace, sectionSlide, contentSlide, bullets, card, stat, formula, note, table,
} = D;

module.exports = function build() {

  sectionSlide("PART 3", "The signals and the data",
    "What an ECG and a PPG actually measure, and the dataset we used");

  // ---- WHAT IS AN ECG ----------------------------------------------------
  {
    const s = contentSlide("An ECG records the electrical pulse that makes each heartbeat");
    s.addText(
      "Every beat starts as an electrical wave sweeping through the heart muscle. " +
      "Electrodes on the skin pick up that wave. One beat has a standard shape, and each " +
      "part of it is named:",
      { x: M, y: 1.45, w: W - 2 * M, h: 0.6, isTextBox: true,
        fontFace: BODY, fontSize: 15, color: INK }
    );

    // One large beat, with labels derived from the waveform geometry itself.
    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 2.15, w: 7.2, h: 3.55, rectRadius: 0.06,
      fill: { color: "F4F9FA" }, line: { color: "F4F9FA" },
    });
    D.annotatedBeat(s, M + 0.75, 3.1, 5.7, 2.1, INK);

    bullets(s, [
      "Sampled 250 times per second, so fine detail is preserved.",
      "The QT interval - from the start of QRS to the end of T - is how long the heart takes to reset. This is the part glucose affects.",
      "The gap between beats (RR interval) varies naturally; how much it varies is 'heart rate variability'.",
      "Everything our features measure is some property of this shape, or of how it changes from beat to beat.",
    ], 7.65, 2.2, 5.15, 3.4, 13.5);
    note(s, "Waveform drawn schematically; real recordings are noisier and vary between people.");
  }

  // ---- WHAT IS A PPG -----------------------------------------------------
  {
    const s = contentSlide("A PPG shines light through the skin and watches the blood volume pulse");
    bullets(s, [
      "A small LED shines into the skin; a photodetector measures how much light comes back.",
      "With each heartbeat a pulse of blood arrives, absorbing more light. The reflected signal therefore rises and falls once per beat.",
      "This is exactly what the green flashing light on a smartwatch is doing.",
      "The SHAPE of each pulse - how fast it rises, how it decays, whether a secondary reflection is visible - depends on blood vessel tone and blood properties.",
    ], M, 1.5, 7.0, 3.0, 14.5);

    card(s, 7.55, 1.45, 5.25, 1.65, "Why include PPG at all?",
      "It measures something physically different from ECG: ECG is electrical activity, " +
      "PPG is blood volume and vessel behaviour. Two different views of the same body.",
      { headSize: 14, size: 12.5 });

    card(s, 7.55, 3.25, 5.25, 1.25, "In our data",
      "Sampled 64 times per second by an Empatica E4 wristband, recorded as 'BVP' " +
      "(blood volume pulse).", { headSize: 14, size: 12.5 });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.75, w: W - 2 * M, h: 1.2, rectRadius: 0.05,
      fill: { color: LIGHT }, line: { color: LIGHT },
    });
    s.addText(
      "The paper's central bet: ECG and PPG each carry a partial, noisy trace of glucose, " +
      "and combining them recovers more than either alone. Their own ablation supports " +
      "it - ECG alone 1.56, PPG alone 1.82, both together 1.49 mmol/L.",
      { x: M + 0.28, y: 4.95, w: W - 2 * M - 0.56, h: 0.85, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 13.5, color: INK }
    );
  }

  // ---- THE REFERENCE TRUTH ----------------------------------------------
  {
    const s = contentSlide("The CGM gives us the answer key: what the glucose actually was");
    bullets(s, [
      "A Dexcom continuous glucose monitor sits under the skin and reports a glucose value every 5 minutes.",
      "This is our 'ground truth' - the number the model is trying to predict.",
      "For each CGM reading we take the 16 seconds of ECG and PPG recorded immediately before it, and ask: can we predict this number from those 16 seconds?",
    ], M, 1.5, 7.2, 2.3, 15);

    s.addShape(pres.ShapeType.roundRect, {
      x: 7.9, y: 1.45, w: 4.9, h: 2.4, rectRadius: 0.06,
      fill: { color: "FFF6E5" }, line: { color: "FFF6E5" },
    });
    s.addText("A limitation worth stating", {
      x: 8.15, y: 1.62, w: 4.4, h: 0.32, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: "8A5A00",
    });
    s.addText(
      "CGMs read fluid between cells, not blood directly, so they lag real blood glucose " +
      "by roughly 5-15 minutes and carry their own error of about 9-10%. Our 'truth' is " +
      "itself an estimate.",
      { x: 8.15, y: 1.98, w: 4.4, h: 1.7, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: INK }
    );

    s.addText("One training example =", {
      x: M, y: 4.2, w: 3.2, h: 0.35, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 14, bold: true, color: INK,
    });
    const parts = [
      ["16 s of ECG", "4000 samples at 250 Hz"],
      ["16 s of PPG", "1024 samples at 64 Hz"],
      ["1 glucose value", "from the CGM, in mmol/L"],
    ];
    parts.forEach(([t, d], i) => {
      const x = M + i * 4.12;
      card(s, x, 4.65, 3.85, 1.1, t, d,
        { fill: i === 2 ? INK : LIGHT, headColor: i === 2 ? MINT : INK,
          color: i === 2 ? "D6E6EA" : INK, headSize: 14, size: 11.5 });
    });
    note(s, "16 seconds is about 20 heartbeats - the window length the paper specifies.");
  }

  // ---- THE DATASET -------------------------------------------------------
  {
    const s = contentSlide("PhysioCGM gives us both signals against a CGM reference, openly and for free");
    s.addText(
      "\"PhysioCGM: a multimodal physiological dataset for non-invasive blood glucose " +
      "estimation\", Scientific Data, 2025. Ten Type-1 diabetes participants, released " +
      "under CC0 (public domain).",
      { x: M, y: 1.42, w: W - 2 * M, h: 0.55, isTextBox: true,
        fontFace: BODY, fontSize: 13.5, color: INK }
    );
    table(s, [
      ["Signal", "Rate", "Device", "What it measures"],
      ["ECG", "250 Hz", "Zephyr BioHarness", "Heart's electrical activity (chest strap)"],
      ["PPG (BVP)", "64 Hz", "Empatica E4", "Blood volume pulse (wristband)"],
      ["EDA", "4 Hz", "Empatica E4", "Skin conductance - not used here"],
      ["Accelerometry", "100 Hz", "both", "Movement - not used here"],
      ["Glucose", "every 5 min", "Dexcom CGM", "The reference value to predict"],
    ], M, 2.1, 7.5, { colW: [1.5, 1.2, 2.1, 2.7], rowH: 0.36, size: 11.5 });

    card(s, 8.35, 2.1, 4.45, 1.5, "Why this dataset",
      "It is the only open dataset carrying ECG AND PPG against a CGM reference - " +
      "exactly the pair the paper needs.", { headSize: 13.5, size: 12 });
    card(s, 8.35, 3.75, 4.45, 1.55, "Our earlier attempt",
      "We first used D1NAMO, which has ECG only. Half the paper's design could not be " +
      "built. PhysioCGM removed that limit.", { headSize: 13.5, size: 12 });

    s.addText("Total data: 8.6 GB of raw recordings across 10 participants", {
      x: M, y: 4.55, w: 7.5, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 13.5, bold: true, color: TEAL,
    });
    note(s, "Data: figshare record 28136294. Code: github.com/PSI-TAMU/PhysioCGM.");
  }

  // ---- OUR DATASET IN NUMBERS -------------------------------------------
  {
    const s = contentSlide("After processing we have 30,830 examples - far more than any previous open attempt");
    stat(s, M, 1.5, 3.0, "30,830", "paired ECG+PPG windows", TEAL);
    stat(s, M + 3.15, 1.5, 3.0, "193", "features per window", TEAL);
    stat(s, M + 6.3, 1.5, 3.0, "10", "participants", TEAL);
    stat(s, M + 9.45, 1.5, 3.0, "2.2-21.5", "glucose range (mmol/L)", TEAL);

    table(s, [
      ["Participant", "Windows", "Participant", "Windows"],
      ["c1s01", "2,541", "c2s01", "3,423"],
      ["c1s02", "3,143", "c2s02", "2,917"],
      ["c1s03", "3,110", "c2s03", "2,654"],
      ["c1s04", "2,500", "c2s04", "3,754"],
      ["c1s05", "3,386", "c2s05", "3,641"],
    ], M, 3.35, 6.3, { colW: [1.8, 1.35, 1.8, 1.35], rowH: 0.3, size: 11.5 });

    card(s, 7.3, 3.35, 5.5, 1.35, "Feature breakdown",
      "80 ECG temporal + 80 PPG temporal (the paper's 160) plus 19 ECG and 14 PPG " +
      "morphological features = 193.", { headSize: 13.5, size: 12 });

    s.addShape(pres.ShapeType.roundRect, {
      x: 7.3, y: 4.85, w: 5.5, h: 1.35, rectRadius: 0.05,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText("The number that matters most", {
      x: 7.55, y: 5.0, w: 5.0, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12.5, bold: true, color: MINT,
    });
    s.addText(
      "Standard deviation of glucose = 2.519 mmol/L. A model that simply guesses the " +
      "average every time scores this. Nothing counts as learning unless it beats it.",
      { x: 7.55, y: 5.32, w: 5.0, h: 0.8, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12, color: "D6E6EA" }
    );
  }

  sectionSlide("PART 4", "Stage 1: turning recordings into examples",
    "Cleaning the signal, cutting it into windows - and two ways the clock can silently lie");

  // ---- FILTERING ---------------------------------------------------------
  {
    const s = contentSlide("Raw recordings carry noise that has nothing to do with the heart, so we filter first");
    s.addText("A raw ECG contains the heartbeat plus several contaminants:", {
      x: M, y: 1.45, w: W - 2 * M, h: 0.35, isTextBox: true,
      fontFace: BODY, fontSize: 15, color: INK,
    });
    const noises = [
      ["Below 0.5 Hz", "Baseline wander", "Slow drift from breathing and the electrode shifting on the skin"],
      ["0.5 - 40 Hz", "THE HEARTBEAT", "Everything clinically meaningful in the ECG lives here"],
      ["Above 40 Hz", "Muscle + mains noise", "Electrical interference and signal from other muscles"],
    ];
    noises.forEach(([band, name, desc], i) => {
      const y = 1.95 + i * 1.12;
      const keep = i === 1;
      s.addShape(pres.ShapeType.roundRect, {
        x: M, y, w: 7.4, h: 0.98, rectRadius: 0.05,
        fill: { color: keep ? INK : "F2F5F6" }, line: { color: keep ? INK : "F2F5F6" },
      });
      s.addText(band, {
        x: M + 0.22, y: y + 0.12, w: 1.6, h: 0.32, isTextBox: true, margin: 0,
        fontFace: "Courier New", fontSize: 12, bold: true, color: keep ? MINT : MUTED,
      });
      s.addText(name, {
        x: M + 1.9, y: y + 0.12, w: 2.4, h: 0.32, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 13, bold: true, color: keep ? PAPER : INK,
      });
      s.addText(desc, {
        x: M + 0.22, y: y + 0.5, w: 6.9, h: 0.36, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11.5, color: keep ? "D6E6EA" : MUTED,
      });
    });
    s.addText("So we keep only 0.5 - 40 Hz. This is the paper's Level-1 preprocessing.", {
      x: M, y: 5.35, w: 7.4, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 14, bold: true, color: INK,
    });

    card(s, 8.15, 1.95, 4.65, 1.6, "For PPG the band is different",
      "PPG is sampled at only 64 Hz, so the highest frequency it can represent is 32 Hz - " +
      "a 40 Hz limit is not even expressible.", { headSize: 13, size: 12 });
    card(s, 8.15, 3.7, 4.65, 1.6, "We use 0.5 - 8 Hz for PPG",
      "That keeps the pulse (about 1-2 Hz) and its first few harmonics, which is where " +
      "the pulse shape lives.", { headSize: 13, size: 12 });
  }

  // ---- HAZARD 1: CLOCKS --------------------------------------------------
  {
    const s = contentSlide("Hazard 1: the two recorders do not share a clock, and nothing warns you");
    bullets(s, [
      "The Zephyr chest strap writes local wall-clock time: \"08/06/2022 13:32:45\".",
      "The Empatica wristband writes a Unix timestamp, which is UTC.",
      "If you assume they agree, every PPG window gets paired with glucose from five hours away.",
      "Nothing crashes. Features compute. Models train. Results look normal - and are meaningless.",
    ], M, 1.5, 7.2, 2.3, 14.5);

    s.addShape(pres.ShapeType.roundRect, {
      x: 7.95, y: 1.45, w: 4.85, h: 2.3, rectRadius: 0.06,
      fill: { color: INK }, line: { color: INK },
    });
    s.addText("How we resolved it", {
      x: 8.2, y: 1.62, w: 4.35, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: MINT,
    });
    s.addText(
      "Both devices were started by hand at roughly the same moments. So we test every " +
      "candidate offset and keep the one under which the two sets of start times line up.",
      { x: 8.2, y: 1.96, w: 4.35, h: 1.1, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: "D6E6EA" }
    );
    s.addText("Result: UTC-5 matched 16 of 20 sessions.\nEvery other offset matched 0-2.", {
      x: 8.2, y: 3.02, w: 4.35, h: 0.6, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12, bold: true, color: MINT,
    });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 4.05, w: W - 2 * M, h: 1.9, rectRadius: 0.06,
      fill: { color: "FBEFEF" }, line: { color: "FBEFEF" },
    });
    s.addText("The general lesson", {
      x: M + 0.3, y: 4.25, w: 5, h: 0.32, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: RED,
    });
    s.addText(
      "When you combine two sensors, the alignment between them is an ASSUMPTION, not a " +
      "fact - and it is an assumption that fails silently. We wrote the detector to " +
      "REFUSE to proceed when the evidence is not decisive, rather than pick the best " +
      "guess. That refusal is what caught the next problem.",
      { x: M + 0.3, y: 4.6, w: W - 2 * M - 0.6, h: 1.15, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 14, color: INK }
    );
  }

  // ---- HAZARD 2: DST -----------------------------------------------------
  {
    const s = contentSlide("Hazard 2: one participant's recording crosses a daylight-saving change");
    s.addText(
      "Participant c2s04 was recorded 27 October to 17 November 2022. US clocks went " +
      "back an hour on 6 November - in the middle of their recording.",
      { x: M, y: 1.45, w: W - 2 * M, h: 0.5, isTextBox: true,
        fontFace: BODY, fontSize: 15, color: INK }
    );
    table(s, [
      ["Sessions", "Count", "Correct offset"],
      ["Before 6 November", "7", "UTC-5  (daylight time)"],
      ["On or after 6 November", "15", "UTC-6  (standard time)"],
    ], M, 2.05, 6.4, { colW: [2.6, 1.2, 2.6], rowH: 0.36, size: 12.5 });

    s.addText("No single fixed offset is correct for this participant.", {
      x: M, y: 3.35, w: 6.4, h: 0.4, isTextBox: true,
      fontFace: BODY, fontSize: 15, bold: true, color: RED,
    });

    card(s, 7.2, 2.05, 5.6, 1.7, "What our guard did",
      "The detector scored UTC-6 at 9 sessions and UTC-5 at 6 - no decisive winner - and " +
      "stopped the run rather than guessing. Picking the winner would have misaligned " +
      "7 sessions by an hour, silently.",
      { headSize: 13.5, size: 12, fill: "FBEFEF", headColor: RED });

    card(s, 7.2, 3.9, 5.6, 1.45, "The fix",
      "Convert through a real time zone (America/Chicago) instead of a fixed offset, so " +
      "the shift is a function of the instant and the transition applies automatically.",
      { headSize: 13.5, size: 12 });

    s.addShape(pres.ShapeType.roundRect, {
      x: M, y: 3.9, w: 6.4, h: 1.45, rectRadius: 0.05,
      fill: { color: LIGHT }, line: { color: LIGHT },
    });
    s.addText("Which participants were affected", {
      x: M + 0.25, y: 4.05, w: 5.9, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12.5, bold: true, color: INK,
    });
    s.addText(
      "Only c2s04 crosses a transition. The others are entirely inside one season, so " +
      "their already-processed data stayed valid - verified by re-extracting windows and " +
      "comparing: largest difference 7e-14, pure rounding noise.",
      { x: M + 0.25, y: 4.38, w: 5.9, h: 0.85, isTextBox: true, margin: 0,
        fontFace: BODY, fontSize: 11.5, color: INK }
    );
    note(s, "This is the kind of bug that never announces itself - the pipeline runs perfectly and the answers are wrong.");
  }
};
