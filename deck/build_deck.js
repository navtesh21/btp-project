/*
 * build_deck.js
 * =============
 * Builds the BTP presentation: a from-scratch explanation of noninvasive blood glucose
 * estimation, the Choquet-integral fusion method, and what our reproduction found.
 *
 * Audience assumption: no background in ML, signal processing, or the underlying maths.
 * Every concept is introduced before it is used.
 *
 * Run:  node deck/build_deck.js
 */

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------------------
// Design system
// ---------------------------------------------------------------------------
// Palette chosen for the topic: the deep navy/teal of clinical monitors, with a
// bright mint that reads like a live ECG trace on a dark screen. The red is
// reserved for the three failure findings and never used decoratively.
const INK = "0B2F3A";        // deep teal-navy: dark backgrounds, headings on light
const TEAL = "1C7293";       // supporting mid-teal
const MINT = "00C2A8";       // accent: the "signal" colour
const RED = "C62828";        // reserved: failures / warnings only
const PAPER = "FFFFFF";
const MUTED = "5A6B72";
const LIGHT = "EAF2F4";      // tinted card background

const HEAD = "Cambria";      // safe-list serif for headings
const BODY = "Calibri";      // safe-list sans for body

const W = 13.333, H = 7.5;
const M = 0.6;               // page margin

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Navtesh Maken";
pres.title = "Noninvasive Blood Glucose Estimation";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// One normalised heartbeat: [fraction across, fraction down]. y grows DOWNWARD, so a
// smaller y is a taller upward deflection. Named fiducials are indices into this list,
// so labels can be positioned from the same geometry the line is drawn from rather
// than from guessed coordinates.
const BEAT = [
  [0.00, 0.50], [0.08, 0.50], [0.12, 0.40], [0.16, 0.50], [0.22, 0.50],
  [0.26, 0.56], [0.30, 0.10], [0.34, 0.70], [0.38, 0.50], [0.46, 0.50],
  [0.54, 0.32], [0.62, 0.50], [0.75, 0.50], [1.00, 0.50],
];
const FIDUCIAL = { P: 2, R: 6, T: 10 };

/** An ECG-like polyline, used as the deck's repeated visual motif. */
function ecgTrace(slide, x, y, w, h, color, thickness) {
  const beat = BEAT;
  const pts = [];
  const reps = 2;
  for (let r = 0; r < reps; r++) {
    beat.forEach(([bx, by]) => pts.push([(r + bx) / reps, by]));
  }
  for (let i = 0; i < pts.length - 1; i++) {
    const [x1, y1] = pts[i], [x2, y2] = pts[i + 1];
    const ax = x + Math.min(x1, x2) * w;
    const ay = y + Math.min(y1, y2) * h;
    const aw = Math.abs(x2 - x1) * w;
    const ah = Math.abs(y2 - y1) * h;
    // A shape's width and height must be NON-NEGATIVE. Writing a negative extent
    // produces a file every validator accepts and PowerPoint refuses to open at all
    // ("the file is corrupted and unreadable") -- so an upward segment is drawn as a
    // positive-height box with flipV, not as a negative height.
    slide.addShape(pres.ShapeType.line, {
      x: ax, y: ay, w: aw, h: Math.max(ah, 0.004),
      flipV: y2 < y1,
      line: { color: color, width: thickness || 2 },
    });
  }
}

/**
 * One large, labelled heartbeat. Label positions are DERIVED from the same BEAT array
 * the line is drawn from, so they cannot drift out of register with the waveform the
 * way hand-placed coordinates do.
 */
function annotatedBeat(slide, x, y, w, h, color) {
  // Draw a single beat across the full width.
  for (let i = 0; i < BEAT.length - 1; i++) {
    const [x1, y1] = BEAT[i], [x2, y2] = BEAT[i + 1];
    slide.addShape(pres.ShapeType.line, {
      x: x + Math.min(x1, x2) * w, y: y + Math.min(y1, y2) * h,
      w: Math.abs(x2 - x1) * w, h: Math.max(Math.abs(y2 - y1) * h, 0.004),
      flipV: y2 < y1,
      line: { color: color || INK, width: 3 },
    });
  }
  const labels = [
    ["P", "atria contract", FIDUCIAL.P, -0.62],
    ["QRS", "ventricles fire", FIDUCIAL.R, -0.66],
    ["T", "ventricles reset", FIDUCIAL.T, -0.62],
  ];
  labels.forEach(([name, desc, idx, dy]) => {
    const [bx, by] = BEAT[idx];
    const px = x + bx * w;
    const py = y + by * h + dy;          // sit above the fiducial point
    slide.addText(name, {
      x: px - 0.7, y: py, w: 1.4, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 15, bold: true, color: MINT, align: "center",
    });
    slide.addText(desc, {
      x: px - 1.0, y: py + 0.29, w: 2.0, h: 0.28, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 10, color: MUTED, align: "center",
    });
  });
}

/** Dark section-divider slide. */
function sectionSlide(part, title, subtitle) {
  const s = pres.addSlide();
  s.background = { color: INK };
  s.addText(part, {
    x: M, y: 2.35, w: W - 2 * M, h: 0.4, isTextBox: true,
    fontFace: BODY, fontSize: 16, color: MINT, charSpacing: 3, bold: true,
  });
  s.addText(title, {
    x: M, y: 2.8, w: W - 2 * M, h: 1.2, isTextBox: true,
    fontFace: HEAD, fontSize: 40, color: PAPER, bold: true,
  });
  if (subtitle) {
    s.addText(subtitle, {
      x: M, y: 4.05, w: W - 2 * M - 3.0, h: 0.9, isTextBox: true,
      fontFace: BODY, fontSize: 16, color: "AEC6CC",
    });
  }
  ecgTrace(s, W - 4.4, 5.55, 3.8, 0.85, MINT, 2);
  return s;
}

/** Standard light content slide with an action title. */
function contentSlide(title) {
  const s = pres.addSlide();
  s.background = { color: PAPER };
  s.addText(title, {
    x: M, y: 0.42, w: W - 2 * M, h: 0.95, isTextBox: true,
    fontFace: HEAD, fontSize: 27, color: INK, bold: true, valign: "top",
  });
  return s;
}

/** Bulleted body text block. */
function bullets(slide, items, x, y, w, h, size) {
  slide.addText(
    items.map((t, i) => ({
      text: t,
      options: { bullet: true, breakLine: i !== items.length - 1 },
    })),
    {
      x, y, w, h, isTextBox: true, fontFace: BODY,
      fontSize: size || 15, color: INK, paraSpaceAfter: 9, valign: "top",
    }
  );
}

/** Tinted card with an optional heading. */
function card(slide, x, y, w, h, heading, text, opts) {
  opts = opts || {};
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: opts.fill || LIGHT }, line: { color: opts.fill || LIGHT },
  });
  if (heading) {
    slide.addText(heading, {
      x: x + 0.22, y: y + 0.16, w: w - 0.44, h: 0.38, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: opts.headSize || 14, bold: true,
      color: opts.headColor || INK,
    });
  }
  if (text) {
    slide.addText(text, {
      x: x + 0.22, y: y + (heading ? 0.58 : 0.2), w: w - 0.44,
      h: h - (heading ? 0.75 : 0.4), isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: opts.size || 12.5,
      color: opts.color || INK, valign: "top",
    });
  }
}

/** Big number callout. */
function stat(slide, x, y, w, value, label, color) {
  slide.addText(value, {
    x, y, w, h: 0.95, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 42, bold: true, color: color || TEAL, align: "center",
  });
  slide.addText(label, {
    x, y: y + 0.92, w, h: 0.6, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 11.5, color: MUTED, align: "center",
  });
}

/**
 * A formula shown in monospace on a dark panel. Returns the panel height so callers
 * can place the next element below it.
 *
 * Height is computed FROM THE FONT SIZE. A fixed per-line constant (the earlier bug)
 * over-sizes small text, leaving dead space, and under-sizes large text, pushing the
 * panel off the slide - both of which happened.
 */
function formula(slide, x, y, w, lines, size) {
  const fs = size || 14;
  // Rendered line height runs a little above the nominal point size times the line
  // spacing, so size the panel with 1.45 while the text itself is set at 1.30. The
  // difference is deliberate slack: with none, the final line of a long block sits
  // just below the panel edge.
  const lineH = (fs / 72) * 1.45;
  const h = 0.45 + lines.length * lineH;
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.05,
    fill: { color: INK }, line: { color: INK },
  });
  slide.addText(lines.join("\n"), {
    x: x + 0.25, y: y + 0.16, w: w - 0.5, h: h - 0.32, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: fs, color: MINT, valign: "top",
    lineSpacingMultiple: 1.30,
  });
  return h;
}

/** Small source/footnote line. */
function note(slide, text, y) {
  slide.addText(text, {
    x: M, y: y || H - 0.62, w: W - 2 * M, h: 0.35, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 10.5, color: MUTED, italic: true,
  });
}

/** Simple table. rows[0] is the header. */
function table(slide, rows, x, y, w, opts) {
  opts = opts || {};
  // pptxgenjs sizes a table by colW when it is supplied, IGNORING w. If the two
  // disagree the table silently renders at the colW width and can run off the slide -
  // and because each cell is its own shape, a naive bounds check does not catch it.
  // So the two must agree, and the total must fit inside the page margins.
  if (opts.colW) {
    const sum = opts.colW.reduce((a, b) => a + b, 0);
    if (Math.abs(sum - w) > 0.02) {
      throw new Error(`table at x=${x}: colW sums to ${sum.toFixed(2)} but w=${w}`);
    }
    if (x + sum > W - M + 0.02) {
      throw new Error(`table at x=${x} runs to ${(x + sum).toFixed(2)}, past the ${(W - M).toFixed(2)} margin`);
    }
  }
  slide.addTable(
    rows.map((r, ri) =>
      r.map((c) => ({
        text: String(c),
        options: {
          fontFace: BODY, fontSize: opts.size || 12,
          bold: ri === 0, color: ri === 0 ? PAPER : INK,
          fill: { color: ri === 0 ? INK : (ri % 2 ? PAPER : LIGHT) },
          align: opts.align || "left", valign: "middle",
        },
      }))
    ),
    {
      x, y, w, colW: opts.colW, rowH: opts.rowH || 0.32,
      border: { type: "solid", color: "D5E2E6", pt: 0.5 },
    }
  );
}

module.exports = {
  pres, pptxgen, INK, TEAL, MINT, RED, PAPER, MUTED, LIGHT, HEAD, BODY, W, H, M,
  ecgTrace, annotatedBeat, sectionSlide, contentSlide, bullets, card, stat, formula, note, table,
};
