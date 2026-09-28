"""
deck/fill_nsut.py
=================
Fill the NSUT Mid-Term-Review template with this project's content.

WHY THE TEMPLATE IS EDITED RATHER THAN REBUILT
----------------------------------------------
The department's template carries its own branding as a picture pasted onto EVERY
slide, not on the layout or master. A slide created fresh from a layout therefore comes
out unbranded. So the deck is built by DUPLICATING an existing content slide (which
copies the picture with it) and then replacing the text - see deck/build_nsut.sh for
the duplication step.

The prescribed section order is fixed by the department and is not ours to change:

    1  Title                      10  Solution Methodology (2)
    2  Contents                   11  Results (1)
    3  Introduction               12  Results (2)
    4  Literature Survey (1)      13  Results (3)
    5  Gaps Identified            14  Results (4)
    6  Aims / Objectives          15  Future work
    7  Literature Survey (2)      16  Expected Outputs / Outcomes
    8  Problem Formulation        17  References
    9  Solution Methodology (1)   18  Thank You

Run:  python deck/fill_nsut.py
"""

from __future__ import annotations

import copy
import os

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches, Pt

DECK = "nsut_deck.pptx"
EQ = os.path.join("figures", "equations")
FIG = os.path.join("figures", "results")

INK = RGBColor(0x0B, 0x2F, 0x3A)
TEAL = RGBColor(0x1C, 0x72, 0x93)
RED = RGBColor(0xC6, 0x28, 0x28)
MUTED = RGBColor(0x5A, 0x6B, 0x72)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

STUDENT = "NAVTESH MAKEN"
ROLL = "<ROLL NO.>"          # fill in before submitting


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def title_of(slide):
    for sh in slide.shapes:
        if sh.name.startswith("Title"):
            return sh
    return None


def body_of(slide):
    for sh in slide.shapes:
        if sh.name.startswith("Content Placeholder"):
            return sh
    return None


def set_title(slide, text, size=28):
    sh = title_of(slide)
    if sh is None:
        return
    tf = sh.text_frame
    p = tf.paragraphs[0]
    # Assign to a RUN, not to text_frame.text: the latter drops the paragraph's
    # formatting and leaves an unstyled single run.
    for r in list(p.runs)[1:]:
        r._r.getparent().remove(r._r)
    run = p.runs[0] if p.runs else p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = True
    run.font.color.rgb = INK
    for extra in list(tf.paragraphs)[1:]:
        extra._p.getparent().remove(extra._p)


def set_body(slide, items, size=16, clear_only=False):
    """Replace the content placeholder's paragraphs with `items`.

    `items` may be strings, or (text, indent_level) tuples.
    """
    sh = body_of(slide)
    if sh is None:
        return None
    tf = sh.text_frame
    tf.word_wrap = True
    first = tf.paragraphs[0]
    for extra in list(tf.paragraphs)[1:]:
        extra._p.getparent().remove(extra._p)
    for r in list(first.runs):
        r._r.getparent().remove(r._r)
    if clear_only or not items:
        return sh

    for i, item in enumerate(items):
        text, lvl = item if isinstance(item, tuple) else (item, 0)
        p = first if i == 0 else tf.add_paragraph()
        p.level = lvl
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size - (1.5 if lvl else 0))
        run.font.color.rgb = INK if lvl == 0 else MUTED
        if text.endswith(":"):
            run.font.bold = True
    return sh


def shrink_body(slide, height_in, gap_in=0.16):
    """Shorten the body placeholder and RETURN the y-coordinate just below it.

    Callers must place tables and figures at the returned y. Hard-coding a y is how
    slides 7, 11 and 13 ended up with a table drawn on top of the intro line: the
    placeholder starts at 1.63in on every content slide of this template, so a table
    at y=1.85 overlaps any body text that wraps to a second line.
    """
    sh = body_of(slide)
    if sh is None:
        return 1.63 + height_in + gap_in
    sh.height = Inches(height_in)
    return sh.top / 914400 + height_in + gap_in


def add_equation(slide, name, left_in, top_in, width_in):
    """Place a rendered equation PNG, preserving its aspect ratio."""
    path = os.path.join(EQ, f"{name}.png")
    w, h = Image.open(path).size
    height_in = width_in * h / w
    return slide.shapes.add_picture(path, Inches(left_in), Inches(top_in),
                                    width=Inches(width_in), height=Inches(height_in))


def add_figure(slide, filename, left_in, top_in, max_w, max_h):
    """Place a result figure, fitted inside a box without distortion."""
    path = os.path.join(FIG, filename)
    w, h = Image.open(path).size
    scale = min(max_w / w, max_h / h)
    return slide.shapes.add_picture(path, Inches(left_in), Inches(top_in),
                                    width=Inches(w * scale), height=Inches(h * scale))


def add_table(slide, rows, left_in, top_in, width_in, height_in,
              col_w=None, size=11, highlight=None):
    """A table styled to match the deck. `highlight` is a row index to mark red."""
    n_r, n_c = len(rows), len(rows[0])
    # python-pptx sizes the table by col_w when it is given, IGNORING width_in. If the
    # two disagree the table renders at the col_w total and can run off the slide - and
    # because each cell is its own shape, a naive per-shape bounds check misses it.
    if col_w:
        total = sum(col_w)
        if abs(total - width_in) > 0.02:
            raise ValueError(f"table at x={left_in}: col_w sums to {total:.2f} "
                             f"but width_in={width_in}")
        if left_in + total > 13.33 - 0.5 + 0.02:
            raise ValueError(f"table at x={left_in} reaches {left_in + total:.2f}in, "
                             f"past the 12.83in margin")
    shape = slide.shapes.add_table(n_r, n_c, Inches(left_in), Inches(top_in),
                                   Inches(width_in), Inches(height_in))
    tbl = shape.table
    if col_w:
        for i, w in enumerate(col_w):
            tbl.columns[i].width = Inches(w)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            run = p.add_run()
            run.text = str(val)
            run.font.size = Pt(size)
            head = ri == 0
            hot = highlight is not None and ri == highlight
            run.font.bold = head or hot
            run.font.color.rgb = WHITE if head else (RED if hot else INK)
            cell.margin_left = Emu(45720)
            cell.margin_right = Emu(45720)
            cell.margin_top = Emu(18288)
            cell.margin_bottom = Emu(18288)
    return shape


def add_note(slide, text, top_in=6.55, size=10.5):
    box = slide.shapes.add_textbox(Inches(0.55), Inches(top_in),
                                   Inches(12.2), Inches(0.4))
    tf = box.text_frame
    tf.word_wrap = True
    run = tf.paragraphs[0].add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.italic = True
    run.font.color.rgb = MUTED
    return box


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ---------------------------------------------------------------------------
# the deck
# ---------------------------------------------------------------------------
def build():
    prs = Presentation(DECK)
    S = list(prs.slides)

    # ---- 1  TITLE -----------------------------------------------------------
    s = S[0]
    set_title(s, "Reproducing Choquet-Integral Multimodel Fusion for Noninvasive "
                 "Blood Glucose Estimation from ECG and PPG", size=26)
    for sh in s.shapes:
        if sh.has_table:
            t = sh.table
            t.cell(0, 0).text_frame.paragraphs[0].runs[0].text = ROLL
            t.cell(0, 1).text_frame.paragraphs[0].runs[0].text = STUDENT
            for r in range(1, len(t.rows)):
                for c in range(len(t.columns)):
                    cell = t.cell(r, c)
                    for p in cell.text_frame.paragraphs:
                        for run in p.runs:
                            run.text = ""
    notes(s, "30s. Name the paper and say plainly that this is a reproduction: we "
             "rebuilt a published method and tested whether its result survives on "
             "data the original authors never saw.")

    # ---- 2  CONTENTS --------------------------------------------------------
    s = S[1]
    set_title(s, "Contents")
    set_body(s, [
        "Introduction",
        "Literature Survey",
        "Gaps Identified",
        "Aims / Objectives of the Project",
        "Problem Formulation",
        "Solution Methodology",
        "Results",
        "Future Work",
        "Expected Outputs / Outcomes",
        "References",
    ], size=18)
    notes(s, "15s. Read the headings, do not elaborate.")

    # ---- 3  INTRODUCTION ----------------------------------------------------
    s = S[2]
    set_title(s, "Introduction")
    set_body(s, [
        "Blood glucose must stay within 3.9 - 10.0 mmol/L. Below 3.9 causes seizure "
        "and coma within minutes; above 10.0 damages nerves, eyes and kidneys over years.",
        "Every accurate measurement today breaks the skin: a finger-prick 4-10 times "
        "daily, or a CGM filament replaced every 10-14 days. ~590 million adults "
        "worldwide manage diabetes this way.",
        "Motivation: ECG and PPG can be recorded painlessly by a chest strap or a "
        "smartwatch. If glucose can be inferred from them, monitoring becomes "
        "non-invasive and effectively free.",
        "Established mechanism: hypoglycaemia triggers adrenaline, which drives "
        "potassium into cells; potassium governs cardiac repolarisation, so the ECG "
        "QT interval lengthens. Hyperglycaemia suppresses vagal tone and alters ST "
        "and T-wave morphology.",
        "Caveat carried through this work: the mechanism supports DETECTING a "
        "dysglycaemic event (classification), not reading the exact concentration "
        "(regression). Published classification reaches 84-94% accuracy; regression "
        "does not replicate.",
    ], size=15)
    notes(s, "90s. Three beats: what glucose is and why both directions are dangerous; "
             "measuring it today means breaking skin; there IS a real mechanism linking "
             "the heart to blood sugar. End on the caveat - it explains the whole result.")

    # ---- 4  LITERATURE SURVEY (1) ------------------------------------------
    s = S[3]
    set_title(s, "Literature Survey (1/2): the method under test")
    set_body(s, [
        "Li et al., IEEE Trans. Neural Networks and Learning Systems 35(10), 2024 - "
        "\"Spatiotemporal ECG and PPG Feature Fusion and Weight-Based Choquet Integral "
        "Multimodel Approach\" (SFF-WCIM).",
        "Reported performance on the authors' private cohort, and the methods they "
        "compare against:",
    ], size=15)
    shrink_body(s, 1.35)
    add_table(s, [
        ["Ref.", "Method", "RMSE (mmol/L)", "MARD (%)", "Zone A (%)", "Zone A+B (%)"],
        ["[21]", "CNN-RNN", "1.66", "14.93", "75.46", "99.35"],
        ["[48]", "ResNets", "1.63", "15.22", "75.18", "99.26"],
        ["[22]", "CDA", "1.99", "20.67", "60.88", "98.56"],
        ["[40]", "CNN-MFVW", "1.61", "14.71", "76.96", "98.94"],
        ["Paper", "SFF-WCIM (the method we reproduce)", "1.49", "13.42", "80.09", "99.49"],
    ], 0.75, 3.35, 11.9, 2.4, col_w=[0.85, 4.35, 1.85, 1.5, 1.6, 1.75],
       size=12, highlight=5)
    add_note(s, "Source: Li et al. 2024, Table V. 1.49 mmol/L approaches the accuracy of "
                "approved CGM devices, which is why the claim warranted independent checking.")
    notes(s, "75s. This is the paper's own comparison table. SFF-WCIM is the row we are "
             "reproducing. 1.49 approaches approved CGM accuracy - that is why it matters.")

    # ---- 5  GAPS IDENTIFIED -------------------------------------------------
    s = S[4]
    set_title(s, "Gaps Identified")
    set_body(s, [
        "No independent validation. The authors released code but not data - their "
        "recordings are private - so the result had never been tested on a cohort they "
        "did not choose.",
        "Evaluation protocol not controlled. Results are reported under a random "
        "window-level split, in which the same participant appears in both training and "
        "test data. Windows from one person are highly correlated, so a model can "
        "identify the person rather than learn about glucose.",
        "Clinical metrics reported without a reference point. Parkes Zone A+B is quoted "
        "as evidence of clinical readiness, but no no-skill baseline is reported "
        "alongside it, so the reader cannot tell how much of that score is the method.",
        "Fusion behaviour never audited. The Choquet integral's fuzzy densities are "
        "estimated from model performance, but the paper does not report them or verify "
        "that the fusion is still discriminating between models.",
        "Reproducibility of the feature pipeline unverified - no check that identical "
        "input produces identical features.",
    ], size=15)
    notes(s, "75s. Four gaps, each of which became one of our findings. Gap 2 is the "
             "most important: the split protocol.")

    # ---- 6  AIMS / OBJECTIVES ----------------------------------------------
    s = S[5]
    set_title(s, "Aims / Objectives of the Project")
    set_body(s, [
        "Aim: to determine whether the reported accuracy of SFF-WCIM survives "
        "independent reproduction on open data under leakage-controlled evaluation.",
        "Objectives:",
        ("Rebuild all three stages of the method from the published description.", 1),
        ("Run it on PhysioCGM - 10 Type-1 participants with simultaneous ECG, PPG and "
         "CGM, released CC0.", 1),
        ("Evaluate under three progressively stricter split protocols, reporting a "
         "no-skill baseline beside every result.", 1),
        ("Audit the fusion operator itself: recover the fuzzy densities and verify the "
         "integral is still discriminating between models.", 1),
        ("Verify that the feature pipeline is deterministic.", 1),
        "Scope and limitations: the paper's private dataset is unavailable, so this is a "
        "reproduction of the METHOD on different data, not a replication of the "
        "experiment. The spatial morphological branch is implemented with hand-crafted "
        "physiological features rather than a ResNet (no GPU available); this deviation "
        "is documented and its effect examined in the ablation.",
    ], size=14.5)
    notes(s, "75s. State the aim as a question - does the result survive? - then the five "
             "objectives. Be explicit that we could not use their data, and why that makes "
             "this a reproduction of the method rather than of the experiment.")

    # ---- 7  LITERATURE SURVEY (2) ------------------------------------------
    s = S[6]
    set_title(s, "Literature Survey (2/2): evaluation practice in this field")
    set_body(s, [
        "Recent work questions whether results in this area survive rigorous evaluation:",
    ], size=15)
    y = shrink_body(s, 0.55)
    add_table(s, [
        ["Study", "Finding relevant to this project"],
        ["Reassessing PPG-Based BGL Estimation,\narXiv:2608.01820 (2026)",
         "Re-tested five published PPG-glucose methods. Best model scored R2 = 0.60 under a\n"
         "random split and -0.08 under a participant-aware split - i.e. no better than the mean.\n"
         "Over 90% of predictions fell in Clarke Zone A+B INCLUDING the baseline."],
        ["Advances in ECG-Based Non-Invasive\nBlood Glucose Monitoring (review, 2026)",
         "Identifies record-level splitting as a field-wide source of data leakage yielding\n"
         "optimistic estimates; notes most studies use fewer than 30 subjects; concludes that\n"
         "current methods do not reach the 10-12% MARD of approved CGM devices."],
        ["Grabisch (1995); Marichal (2000)",
         "Aggregation theory: a Choquet integral taken with respect to a SYMMETRIC fuzzy measure\n"
         "reduces to an ordered weighted average (OWA). This is the theoretical basis of our\n"
         "degeneracy result, and is cited as prior work rather than claimed as novel."],
    ], 0.75, y, 11.9, 3.35, col_w=[3.5, 8.4], size=11)
    add_note(s, "The first two motivate our three-protocol design; the third bounds what we "
                "claim as new in Finding 3.")
    notes(s, "75s. The first row is the study we independently replicate - on ECG instead of "
             "PPG. The third row matters for honesty: the symmetric-measure result is known "
             "theory. Our contribution is showing it fires by accident in practice.")

    # ---- 8  PROBLEM FORMULATION --------------------------------------------
    s = S[7]
    set_title(s, "Problem Formulation")
    set_body(s, [
        "Given a 16 s window of ECG and PPG preceding a CGM reading, predict the glucose "
        "concentration y (mmol/L). Three regressors produce h1, h2, h3, to be combined "
        "into one estimate.",
        "A weighted average assigns importance to each model individually, so it cannot "
        "express that two models overlap. A fuzzy measure assigns importance to every "
        "SUBSET; the Sugeno lambda-measure generates all 2^N of them from one density per "
        "model:",
    ], size=14.5)
    shrink_body(s, 1.5)
    add_equation(s, "sugeno_union", 1.35, 3.0, 6.2)
    add_equation(s, "sugeno_lambda", 8.35, 2.85, 3.0)
    add_equation(s, "choquet", 1.35, 4.35, 8.2)
    add_note(s,
        "lambda is fixed by the boundary condition g(X) = 1.  Sum(g_i) = 1 gives lambda = 0 "
        "and the integral reduces to a weighted average;  > 1 gives lambda < 0, an overlap "
        "penalty;  < 1 gives lambda > 0, a synergy bonus.", top_in=6.2)
    notes(s, "2 min, the densest slide. Open with the analogy: three doctors, two trained "
             "together so averaging double-counts them, one far more experienced. A weighted "
             "average handles the second but not the first. THEN the equations. Sorting is "
             "what lets group importance enter - the weight depends on RANK.")

    # ---- 9  SOLUTION METHODOLOGY (1) ---------------------------------------
    s = S[8]
    set_title(s, "Solution Methodology (1/2): pipeline and dataset")
    set_body(s, [
        "Level 1 - acquisition and conditioning: 16 s windows (~20 cardiac cycles) "
        "preceding each CGM reading; Butterworth band-pass 0.5-40 Hz for ECG and "
        "0.5-8 Hz for PPG (64 Hz sampling limits the representable band to 32 Hz).",
        "Level 2 - feature extraction: db4 DWT to 7 levels gives 8 sub-signals per "
        "modality; 10 statistical features each (80 per modality, 160 total), plus 33 "
        "morphological features. Selection by UFS n RFE n L1.",
        "Level 3 - decision fusion: Random Forest, Gradient Boosting and Bagging, "
        "combined by the weight-based Choquet integral.",
    ], size=14.5)
    shrink_body(s, 2.3)
    add_table(s, [
        ["Signal", "Device", "Rate", "Role"],
        ["ECG", "Zephyr BioHarness (chest strap)", "250 Hz", "Electrical activity of the heart"],
        ["PPG (BVP)", "Empatica E4 (wristband)", "64 Hz", "Blood volume pulse, measured optically"],
        ["Glucose", "Dexcom CGM", "every 5 min", "Reference value to be predicted"],
    ], 0.75, 3.85, 7.4, 1.35, col_w=[1.25, 2.85, 1.2, 2.1], size=11.5)
    add_table(s, [
        ["Study population", ""],
        ["Participants", "10 (Type-1 diabetes)"],
        ["Paired ECG+PPG windows", "30,830"],
        ["Features per window", "193"],
        ["Glucose range", "2.2 - 21.5 mmol/L"],
        ["Mean / standard deviation", "7.17 / 2.519 mmol/L"],
    ], 8.55, 3.85, 4.1, 2.0, col_w=[2.5, 1.6], size=11, highlight=5)
    add_note(s, "PhysioCGM (Scientific Data, 2025; figshare 28136294, CC0) - the only open "
                "dataset carrying ECG and PPG against a CGM reference. The 2.519 mmol/L "
                "standard deviation is the error of a model that always predicts the mean: "
                "the no-skill baseline every result is measured against.", top_in=6.05)
    notes(s, "90s. Walk the three levels, then the two tables. SLOW DOWN on 2.519 - it is "
             "the standard deviation of glucose and therefore the RMSE of a model that "
             "learns nothing. Everything after this slide is judged against it.")

    # ---- 10  SOLUTION METHODOLOGY (2) --------------------------------------
    s = S[9]
    set_title(s, "Solution Methodology (2/2): feature extraction and selection")
    set_body(s, [
        "Temporal statistical features - 10 per sub-signal: kurtosis, skewness, Hjorth "
        "mobility and complexity, fractal dimension, correlation dimension, "
        "C0-complexity, power spectral entropy, Kolmogorov entropy, Shannon entropy.",
    ], size=14)
    shrink_body(s, 0.95)
    add_equation(s, "hjorth", 0.8, 2.05, 6.6)
    add_equation(s, "entropy", 7.9, 2.0, 4.6)
    set_body_note = slide_note = None
    box = s.shapes.add_textbox(Inches(0.75), Inches(2.95), Inches(11.9), Inches(0.75))
    tf = box.text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run()
    r.text = ("Spatial morphological features - measured directly rather than learned, "
              "because the mechanism is known: QT and corrected QT, ST level, T-wave "
              "amplitude and sharpness, QRS duration, and heart-rate variability.")
    r.font.size = Pt(14); r.font.color.rgb = INK
    add_equation(s, "qtc", 0.8, 3.75, 5.9)

    box2 = s.shapes.add_textbox(Inches(0.75), Inches(4.55), Inches(11.9), Inches(0.5))
    tf2 = box2.text_frame; tf2.word_wrap = True
    r2 = tf2.paragraphs[0].add_run()
    r2.text = ("Feature selection - a feature is retained only if all three criteria "
               "select it (paper eqs. 5 and 6), fitted on training data within each fold:")
    r2.font.size = Pt(14); r2.font.color.rgb = INK
    add_equation(s, "eq5_rfe", 0.8, 5.15, 6.5)
    add_equation(s, "eq6_lasso", 7.7, 5.2, 4.7)
    add_note(s, "193 features per window = 80 ECG temporal + 80 PPG temporal + 19 ECG "
                "morphological + 14 PPG morphological. Selection typically retains ~10. "
                "Validation: median QTc 0.405 s against a textbook normal of 0.35-0.44 s.",
             top_in=6.35)
    notes(s, "90s. Three groups: temporal statistical (the wavelet ones), morphological "
             "(measured directly, since we know QT is the mechanism), and selection. "
             "Equations 5 and 6 are the paper's own numbering so they can follow in the PDF. "
             "Mention that selection runs INSIDE each fold - selecting on the whole dataset "
             "leaks test information into the feature choice.")

    # ---- 11  RESULTS (1) ----------------------------------------------------
    s = S[10]
    set_title(s, "Results (1/4): performance under three split protocols")
    set_body(s, [
        "193 features, 30,830 windows, 10 participants. Every model is reported beside "
        "the no-skill baseline computed on the same folds.",
    ], size=14.5)
    y = shrink_body(s, 0.6)
    add_table(s, [
        ["Split protocol", "Method", "R2", "RMSE\n(mmol/L)", "MARD\n(%)", "Zone A\n(%)", "Zone A+B\n(%)"],
        ["1. Random window", "Choquet fusion", "+0.149", "2.324", "24.86", "52.87", "93.75"],
        ["   (paper's protocol)", "No-skill baseline", "-0.000", "2.520", "29.14", "45.34", "90.89"],
        ["2. Subject-aware", "Choquet fusion", "-0.223", "2.786", "31.50", "41.91", "89.39"],
        ["", "No-skill baseline", "-0.074", "2.610", "30.30", "43.74", "90.01"],
        ["3. Leave-one-subject-out", "Choquet fusion", "-0.097", "2.639", "28.86", "45.57", "91.25"],
        ["", "No-skill baseline", "-0.035", "2.564", "29.74", "44.14", "90.57"],
    ], 0.75, y, 11.9, 2.35, col_w=[2.85, 2.25, 1.15, 1.35, 1.2, 1.4, 1.7], size=11)
    add_equation(s, "metrics", 0.9, 4.95, 6.3)
    box = s.shapes.add_textbox(Inches(7.7), Inches(4.95), Inches(5.0), Inches(1.5))
    tf = box.text_frame; tf.word_wrap = True
    for txt, bold, col in (
        ("Read the R2 column first.", True, INK),
        ("R2 = 0 means exactly as good as predicting the mean; negative means worse. "
         "It is the only metric here that exposes a model that has learned nothing.", False, INK),
        ("Under both honest protocols every method - including the fusion - falls behind "
         "the baseline.", True, RED)):
        p = tf.paragraphs[0] if not tf.paragraphs[0].runs else tf.add_paragraph()
        r = p.add_run(); r.text = txt
        r.font.size = Pt(12); r.font.bold = bold; r.font.color.rgb = col
    notes(s, "2 min. Define R-squared FIRST. Then: +0.149 random, -0.223 subject-aware, "
             "-0.097 leave-one-out. Same data, same code, only the split changed. "
             "RAISE THE ORDERING YOURSELF - leave-one-out beats subject-aware because it "
             "trains on 9 of 10 rather than 4 of 5. Saying it first is far stronger than "
             "being caught on it.")

    # ---- 12  RESULTS (2) ----------------------------------------------------
    s = S[11]
    set_title(s, "Results (2/4): Parkes error grid and prediction trace")
    set_body(s, [], clear_only=True)
    add_figure(s, "fig10_parkes_subject_aware.png", 0.7, 1.35, 4.5, 4.6)
    add_figure(s, "fig09_timeseries_subject_aware_c2s04.png", 5.5, 1.5, 7.3, 3.1)
    box = s.shapes.add_textbox(Inches(5.5), Inches(4.5), Inches(7.3), Inches(2.0))
    tf = box.text_frame; tf.word_wrap = True
    for txt, bold, col in (
        ("A working model would produce a diagonal cloud along the dotted line.", False, INK),
        ("Ours is a horizontal band: whether the true value was 4 or 20 mmol/L, the "
         "prediction is approximately 6-9. That is what \"no better than the mean\" "
         "looks like when drawn.", True, INK),
        ("The same flat band scores 89.4% in Zones A+B - which is why the clinical "
         "metric cannot certify a model on its own.", False, RED)):
        p = tf.paragraphs[0] if not tf.paragraphs[0].runs else tf.add_paragraph()
        r = p.add_run(); r.text = txt
        r.font.size = Pt(12.5); r.font.bold = bold; r.font.color.rgb = col
        p.space_after = Pt(7)
    add_note(s, "Equivalent to Figs. 9 and 10 of the paper. Subject-aware split, Choquet "
                "fusion, 30,830 predictions.", top_in=6.6)
    notes(s, "90s. YOUR STRONGEST SLIDE. Trace the diagonal with your hand - that is what "
             "a working model looks like. Then trace the horizontal band. Then the sting: "
             "89.4% Zone A+B. PAUSE and let it land.")

    # ---- 13  RESULTS (3) ----------------------------------------------------
    s = S[12]
    set_title(s, "Results (3/4): ablation over feature sets")
    set_body(s, [
        "Every feature set evaluated under leave-one-subject-out, Choquet fusion:",
    ], size=14.5)
    y = shrink_body(s, 0.45)
    add_table(s, [
        ["Feature set", "Features", "R2", "RMSE (mmol/L)", "Zone A+B (%)"],
        ["No-skill baseline", "0", "-0.035", "2.564", "90.6"],
        ["Morphological (shape) only", "33", "-0.070", "2.606", "90.8"],
        ["PPG only", "94", "-0.075", "2.612", "90.6"],
        ["Fused (ECG + PPG)", "193", "-0.097", "2.639", "91.3"],
        ["Temporal (wavelet) only", "160", "-0.102", "2.645", "91.5"],
        ["ECG only", "99", "-0.106", "2.650", "91.5"],
    ], 0.75, y, 7.6, 2.5, col_w=[2.7, 1.05, 1.0, 1.5, 1.35], size=11.5, highlight=1)
    box = s.shapes.add_textbox(Inches(8.6), Inches(y), Inches(4.1), Inches(4.3))
    tf = box.text_frame; tf.word_wrap = True
    for head, body in (
        ("Every set is behind the baseline.",
         "The entire spread, best to worst, is 0.036 in R2 - and the baseline sits above "
         "all of it."),
        ("Fusing the two signals is worse than the better one alone.",
         "PPG alone (-0.075) beats the fused set (-0.097). The paper found the opposite. "
         "We do not read a 0.03 gap between two failing configurations as evidence."),
        ("Fewer features score better.",
         "33 features beat 193. When adding information makes a model worse, it is "
         "fitting noise."),
        ("And the clinical score runs backwards.",
         "The worst models by R2 carry the highest Zone A+B. Not weakly related - inverted.")):
        p = tf.paragraphs[0] if not tf.paragraphs[0].runs else tf.add_paragraph()
        r = p.add_run(); r.text = head
        r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = INK
        p2 = tf.add_paragraph()
        r2 = p2.add_run(); r2.text = body
        r2.font.size = Pt(11); r2.font.color.rgb = MUTED
        p2.space_after = Pt(8)
    add_note(s, "Equivalent to Tables III and IV of the paper. Feature counts in brackets "
                "in the first column.", top_in=6.5)
    notes(s, "75s. Four observations, in order. The last two are the interesting ones: "
             "fewer features do better (fitting noise), and the clinical score is INVERSELY "
             "related to R-squared.")

    # ---- 14  RESULTS (4) ----------------------------------------------------
    s = S[13]
    set_title(s, "Results (4/4): the fusion operator degenerates")
    set_body(s, [
        "Two anomalies in the output: the weighted average and the plain average agreed "
        "to three decimals (3.927 vs 3.927), and every fuzzy density sat at the 0.01 "
        "clipping floor. With equal densities the Sugeno measure becomes symmetric, and "
        "the Choquet integral reduces to a fixed order statistic:",
    ], size=14)
    shrink_body(s, 1.15)
    add_equation(s, "degeneracy", 0.85, 2.35, 5.6)
    add_equation(s, "degeneracy_limit", 0.85, 5.0, 5.9)
    add_table(s, [
        ["g", "lambda", "w (largest)", "w (middle)", "w (smallest)", "Reduces to"],
        ["0.010", "846.24", "0.010", "0.095", "0.895", "minimum operator"],
        ["0.100", "15.41", "0.100", "0.254", "0.646", "rank-weighted OWA"],
        ["0.333", "0.00", "0.333", "0.333", "0.333", "arithmetic mean"],
    ], 7.0, 2.35, 5.65, 1.1, col_w=[0.68, 0.87, 0.95, 0.9, 1.0, 1.25], size=10.5, highlight=1)
    box = s.shapes.add_textbox(Inches(7.0), Inches(3.75), Inches(5.65), Inches(2.6))
    tf = box.text_frame; tf.word_wrap = True
    for txt, bold, col, sz in (
        ("Verified against the saved predictions:", True, INK, 12),
        ("corr(Choquet output, min of the three models) = 0.998", False, RED, 12.5),
        ("mean |Choquet - min| = 0.04 mmol/L, against 0.27 to the mean", False, INK, 11.5),
        ("The method's distinguishing component was returning min(h1, h2, h3).", True, RED, 12.5),
        ("Not only a bug: under honest evaluation the base models genuinely cannot "
         "generalise, so the densities floor legitimately - the fusion degenerates "
         "exactly when it is most needed.", False, INK, 11)):
        p = tf.paragraphs[0] if not tf.paragraphs[0].runs else tf.add_paragraph()
        r = p.add_run(); r.text = txt
        r.font.size = Pt(sz); r.font.bold = bold; r.font.color.rgb = col
        p.space_after = Pt(6)
    add_note(s, "The symmetric-measure/OWA equivalence is established theory (Grabisch; "
                "Marichal). The contribution here is identifying it as a practical failure "
                "mode of performance-based density estimation, with a closed-form diagnostic.",
             top_in=6.6)
    notes(s, "2 min. Start with the two clues, then the derivation, then the table, then "
             "the empirical confirmation. DO NOT SKIP the last line - the degeneracy is a "
             "symptom as well as a bug, and it fires exactly when the models are weak.")

    # ---- 15  FUTURE WORK ----------------------------------------------------
    s = S[14]
    set_title(s, "Future work to be done")
    set_body(s, [
        "Reframe the task from regression to classification. The physiological mechanism "
        "supports detecting hypo- and hyperglycaemic events, not reading absolute "
        "concentration. Reported ECG classification reaches 84-94% accuracy.",
        "Evaluate personalisation. The gap between random and subject-aware splitting "
        "indicates the models rely on participant-specific structure; a short per-user "
        "calibration matches how CGM devices are actually deployed.",
        "Implement the spatial morphological branch as specified (ResNet) to isolate the "
        "effect of our substitution, given GPU access.",
        "Test the degeneracy diagnostic on other Choquet-fusion pipelines. The failure "
        "mode is not specific to glucose - it applies wherever fuzzy densities are "
        "estimated from model performance.",
        "Planned publication: a short reproducibility paper. Candidate venues - IEEE "
        "Journal of Biomedical and Health Informatics, or the ML Reproducibility "
        "Challenge.",
    ], size=15)
    notes(s, "60s. The first point is the most important and the most defensible: the "
             "biology supports classification, not regression.")

    # ---- 16  EXPECTED OUTPUTS ----------------------------------------------
    s = S[15]
    set_title(s, "Expected Outputs / Outcomes of the work")
    set_body(s, [
        "An open, reproducible implementation. All three stages, released publicly with "
        "the data pipeline, so the method can be tested by others: "
        "github.com/navtesh21/btp-project",
        "A degeneracy theorem with a runnable diagnostic. Closed form w_j = g x beta^(j-1); "
        "when densities saturate, the Choquet integral provably reduces to a fixed order "
        "statistic. Reusable by anyone employing fuzzy-integral fusion, in any domain.",
        "Evidence that evaluation protocol dominates model choice in this field, and that "
        "clinical zone metrics cannot certify a model without a baseline reported beside "
        "them.",
        "A reproducibility defect reported in a widely used nonlinear-features library: "
        "an unseeded random slope fit changes up to 72% of correlation-dimension values "
        "between identical runs.",
        "Methodological contribution: three guards that fail loudly rather than guess - "
        "timezone detection that refuses when ambiguous, feature selection with no "
        "whole-dataset variant, and a per-fold degeneracy report.",
    ], size=14.5)
    notes(s, "75s. Four outcomes plus the methodological one. Emphasise that the "
             "degeneracy result is reusable outside this problem entirely.")

    # ---- 17  REFERENCES -----------------------------------------------------
    s = S[16]
    set_title(s, "References")
    for sh in list(s.shapes):
        if sh.name.startswith("TextBox"):
            sh._element.getparent().remove(sh._element)
    set_body(s, [
        "[1] J. Li et al., \"Noninvasive blood glucose monitoring using spatiotemporal ECG "
        "and PPG feature fusion and weight-based Choquet integral multimodel approach,\" "
        "IEEE Trans. Neural Netw. Learn. Syst., vol. 35, no. 10, pp. 14493-14505, Oct. 2024.",
        "[2] \"PhysioCGM: a multimodal physiological dataset for non-invasive blood glucose "
        "estimation,\" Sci. Data, vol. 12, 2025. [Online]. Available: "
        "https://doi.org/10.6084/m9.figshare.28136294 (accessed Sep. 25, 2026).",
        "[3] \"Reassessing the feasibility of PPG-based non-invasive blood glucose level "
        "estimation,\" arXiv:2608.01820, 2026.",
        "[4] \"Advances in electrocardiogram-based non-invasive blood glucose monitoring "
        "technology,\" (review), 2026.",
        "[5] J. L. Parkes, S. L. Slatin, S. Pardo, and B. H. Ginsberg, \"A new consensus "
        "error grid to evaluate the clinical significance of inaccuracies in the estimation "
        "of blood glucose,\" Diabetes Care, vol. 23, no. 8, pp. 1143-1148, Aug. 2000.",
        "[6] A. Pfutzner, D. C. Klonoff, S. Pardo, and J. L. Parkes, \"Technical aspects of "
        "the Parkes error grid,\" J. Diabetes Sci. Technol., vol. 7, no. 5, pp. 1275-1281, 2013.",
        "[7] B. Eckert and C.-D. Agardh, \"Hypoglycaemia leads to an increased QT interval in "
        "normal men,\" Clin. Physiol., vol. 18, no. 6, pp. 570-575, Nov. 1998.",
        "[8] M. Grabisch, \"Fuzzy integral in multicriteria decision making,\" Fuzzy Sets Syst., "
        "vol. 69, no. 3, pp. 279-298, 1995.",
        "[9] J.-L. Marichal, \"On Choquet and Sugeno integrals as aggregation functions,\" in "
        "Fuzzy Measures and Integrals, Heidelberg, Germany: Physica-Verlag, 2000, pp. 247-272.",
        "[10] B. Hjorth, \"EEG analysis based on time domain properties,\" Electroencephalogr. "
        "Clin. Neurophysiol., vol. 29, no. 3, pp. 306-310, 1970.",
    ], size=11.5)
    notes(s, "15s. Do not read these aloud.")

    # ---- 18  THANK YOU ------------------------------------------------------
    s = S[17]
    set_title(s, "Thank You.")
    for sh in s.shapes:
        if sh.has_table:
            t = sh.table
            t.cell(0, 0).text_frame.paragraphs[0].runs[0].text = ROLL
            t.cell(0, 1).text_frame.paragraphs[0].runs[0].text = STUDENT
            for r in range(1, len(t.rows)):
                for c in range(len(t.columns)):
                    for p in t.cell(r, c).text_frame.paragraphs:
                        for run in p.runs:
                            run.text = ""
    notes(s, "Leave this up, or return to Results (4) for questions.")

    prs.save(DECK)
    print(f"filled {len(S)} slides -> {DECK}")


if __name__ == "__main__":
    build()
