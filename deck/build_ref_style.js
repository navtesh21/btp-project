/*
 * deck/build_ref_style.js
 * =======================
 * Builds the Mid-Term-Review deck in the style of the reference submission
 * (Three_Phase_Multifunctional_Converter, supplied by the user).
 *
 * That reference establishes a specific and consistent visual vocabulary, extracted
 * from the PDF rather than guessed at:
 *
 *   - Times New Roman throughout, regular and bold. No second typeface.
 *   - Monochrome: black text on white, with light grey card fills. Colour appears only
 *     inside data figures, where it carries meaning.
 *   - Numbered section titles ("2. Literature Survey") in bold ~21pt, with a thin
 *     horizontal rule beneath spanning the text column.
 *   - Rounded rectangle cards, pale grey fill, thin grey border, holding a bold centred
 *     heading over left-aligned body text.
 *   - A bold centred "takeaway" line beneath the content.
 *   - A footer: small run-in title on the left, page number on the right.
 *
 * Run:  node deck/build_ref_style.js
 */

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------------------
// style constants, lifted from the reference
// ---------------------------------------------------------------------------
const FONT = "Times New Roman";
const BLACK = "000000";
const CARD_FILL = "F5F5F5";
const CARD_LINE = "BFBFBF";
const HEAD_FILL = "EBEBEB";
const RULE = "000000";
const GREY = "444444";

const W = 13.333, H = 7.5;
const M = 0.75;                        // page margin
const RUN_TITLE = "Mid Term Review | Noninvasive Blood Glucose Estimation from ECG and PPG";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Vednash Singhal, Navtesh Maken, Aditya Agarwaal, Tushar Sharma";
pres.title = "Noninvasive Blood Glucose Estimation from ECG and PPG";

let pageNo = 0;

// ---------------------------------------------------------------------------
// primitives
// ---------------------------------------------------------------------------

/** Footer: run-in title left, page number right. On every slide but the title. */
function footer(slide) {
  pageNo += 1;
  slide.addText(RUN_TITLE, {
    x: M, y: H - 0.52, w: 9.0, h: 0.28, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 8, color: GREY,
  });
  slide.addText(String(pageNo), {
    x: W - M - 0.9, y: H - 0.52, w: 0.9, h: 0.28, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 8, color: GREY, align: "right",
  });
}

/** A numbered section slide: bold title, rule beneath, footer. */
function section(number, title) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText(`${number}. ${title}`, {
    x: M, y: 0.42, w: W - 2 * M, h: 0.62, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 21, bold: true, color: BLACK, valign: "middle",
  });
  // The rule under the title is the reference's strongest structural signal.
  s.addShape(pres.ShapeType.line, {
    x: M, y: 1.12, w: W - 2 * M, h: 0.004,
    line: { color: RULE, width: 1.1 },
  });
  footer(s);
  return s;
}

/** Centred bold sub-heading directly under the rule. */
function subhead(slide, text, y) {
  slide.addText(text, {
    x: M, y: y === undefined ? 1.24 : y, w: W - 2 * M, h: 0.34,
    isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 13, bold: true, color: BLACK, align: "center",
  });
}

/** A pale rounded card with a bold centred heading and left-aligned paragraphs. */
function card(slide, x, y, w, h, heading, paras, size) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.22,
    fill: { color: CARD_FILL }, line: { color: CARD_LINE, width: 0.75 },
    shadow: { type: "outer", color: "888888", blur: 5, offset: 2, angle: 45, opacity: 0.35 },
  });
  if (heading) {
    slide.addText(heading, {
      x: x + 0.2, y: y + 0.16, w: w - 0.4, h: 0.32, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 14, bold: true, color: BLACK, align: "center",
    });
  }
  if (paras && paras.length) {
    slide.addText(
      paras.map((t, i) => ({
        text: t,
        options: { breakLine: i !== paras.length - 1, bullet: false },
      })),
      {
        x: x + 0.28, y: y + (heading ? 0.62 : 0.22), w: w - 0.56,
        h: h - (heading ? 0.8 : 0.42), isTextBox: true, margin: 0,
        fontFace: FONT, fontSize: size || 12, color: BLACK,
        paraSpaceAfter: 7, valign: "top",
      }
    );
  }
}

/** Plain left-aligned body paragraphs, no card. */
function body(slide, paras, x, y, w, h, size) {
  slide.addText(
    paras.map((t, i) => ({
      text: typeof t === "string" ? t : t.text,
      options: {
        breakLine: i !== paras.length - 1,
        bullet: false,
        bold: typeof t === "object" && t.bold,
      },
    })),
    {
      x, y, w, h, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: size || 12, color: BLACK,
      paraSpaceAfter: 8, valign: "top",
    }
  );
}

/** Bold centred takeaway line, the reference's closing device on most slides. */
function takeaway(slide, text, y) {
  slide.addText(text, {
    x: M, y: y === undefined ? H - 1.15 : y, w: W - 2 * M, h: 0.5,
    isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 11.5, bold: true, color: BLACK, align: "center",
  });
}

/**
 * Table in the reference's style: pale bold header, no interior vertical rules,
 * generous row height, left-aligned body cells.
 *
 * colW must sum to w - pptxgenjs sizes by colW and ignores w when both are given,
 * which silently pushes wide tables off the slide.
 */
function table(slide, rows, x, y, w, opts) {
  opts = opts || {};
  if (opts.colW) {
    const sum = opts.colW.reduce((a, b) => a + b, 0);
    if (Math.abs(sum - w) > 0.02) {
      throw new Error(`table at x=${x}: colW sums to ${sum.toFixed(2)}, w=${w}`);
    }
    if (x + sum > W - M + 0.02) {
      throw new Error(`table at x=${x} reaches ${(x + sum).toFixed(2)}in, past ${W - M}`);
    }
  }
  const size = opts.size || 10.5;
  slide.addTable(
    rows.map((r, ri) =>
      r.map((c, ci) => ({
        text: String(c),
        options: {
          fontFace: FONT, fontSize: size,
          bold: ri === 0 || (opts.boldRow !== undefined && ri === opts.boldRow),
          color: BLACK,
          fill: { color: ri === 0 ? HEAD_FILL : "FFFFFF" },
          align: ri === 0 ? "center"
            : (ci < (opts.textCols === undefined ? 1 : opts.textCols)
               ? "left" : (opts.align || "left")),
          valign: "middle",
        },
      }))
    ),
    {
      x, y, w, colW: opts.colW,
      rowH: [opts.headH || Math.min(opts.rowH || 0.3, 0.38)]
        .concat(rows.slice(1).map(() => opts.rowH || 0.3)),
      border: [
        { type: "solid", color: "FFFFFF", pt: 0 },      // top
        { type: "solid", color: "FFFFFF", pt: 0 },      // right
        { type: "solid", color: "D9D9D9", pt: 0.5 },    // bottom: light row rules only
        { type: "solid", color: "FFFFFF", pt: 0 },      // left
      ],
    }
  );
}

/** An equation PNG, aspect preserved. */
function equation(slide, name, x, y, w) {
  const p = path.join("figures", "equations", `${name}.png`);
  const dim = pngSize(p);
  slide.addImage({ path: p, x, y, w, h: w * dim.h / dim.w });
}

/** A result figure fitted inside a box. */
function figure(slide, file, x, y, maxW, maxH) {
  const p = path.join("figures", "results", file);
  const d = pngSize(p);
  const s = Math.min(maxW / d.w, maxH / d.h);
  slide.addImage({ path: p, x, y, w: d.w * s, h: d.h * s });
}

/** Minimal PNG header reader - avoids depending on an image library. */
function pngSize(file) {
  const buf = fs.readFileSync(file);
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}

module.exports = {
  pres, pptxgen, FONT, BLACK, CARD_FILL, CARD_LINE, HEAD_FILL, GREY, W, H, M,
  section, subhead, card, body, takeaway, table, equation, figure, footer, pngSize,
  titleSlide,
};

// ---------------------------------------------------------------------------
// title slide (kept here because it does not use section())
// ---------------------------------------------------------------------------
function titleSlide() {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };

  s.addText("MID TERM REVIEW", {
    x: M, y: 1.15, w: W - 2 * M, h: 0.3, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 12, bold: true, color: BLACK,
    align: "center", charSpacing: 1,
  });

  s.addText("Reproducing Choquet-Integral Multimodel Fusion for\n"
            + "Noninvasive Blood Glucose Estimation", {
    x: M, y: 1.75, w: W - 2 * M, h: 1.15, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 30, bold: true, color: BLACK,
    align: "center", lineSpacingMultiple: 1.1,
  });

  s.addText("An independent reproduction on open ECG and PPG data, "
            + "under leakage-controlled evaluation", {
    x: M, y: 3.0, w: W - 2 * M, h: 0.4, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 15, color: BLACK, align: "center",
  });

  const team = [
    ["Vednash Singhal", "2023UIC3633"],
    ["Navtesh Maken", "2023UIC3641"],
    ["Aditya Agarwaal", "2023UIC4138"],
    ["Tushar Sharma", "2023UIC3600"],
  ];
  team.forEach(([name, roll], i) => {
    s.addText(`${name}    ${roll}`, {
      x: M, y: 3.72 + i * 0.3, w: W - 2 * M, h: 0.28, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 14, color: BLACK, align: "center",
    });
  });

  s.addText("Under the supervision of", {
    x: M, y: 5.12, w: W - 2 * M, h: 0.26, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 11, color: GREY, align: "center",
  });
  s.addText("Mrs. Asha Rani", {
    x: M, y: 5.38, w: W - 2 * M, h: 0.3, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 14, bold: true, color: BLACK, align: "center",
  });

  s.addText("Department of Instrumentation and Control Engineering\n"
            + "Netaji Subhas University of Technology, New Delhi", {
    x: M, y: 5.88, w: W - 2 * M, h: 0.6, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 12, color: BLACK, align: "center",
  });

  s.addText("EEEEC23  B. Tech Project - II", {
    x: M, y: 6.52, w: W - 2 * M, h: 0.3, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 11, color: GREY, align: "center",
  });

  pageNo = 1;   // the title page counts as page 1; footers start from 2
  return s;
}
