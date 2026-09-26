/*
 * deck/main.js — assemble and write the presentation.
 *
 * Results slides are filled from results/summary_*.csv when those exist, so the deck
 * can be rebuilt at any time and simply gains its numbers once the evaluation lands.
 */
const fs = require("fs");
const path = require("path");
const D = require("./build_deck");

const ROOT = path.join(__dirname, "..");
const RESULTS = path.join(ROOT, "results");

/** Read a summary CSV into rows of objects, or null if absent. */
function readSummary(tag) {
  const p = path.join(RESULTS, `summary_${tag}.csv`);
  if (!fs.existsSync(p)) return null;
  const lines = fs.readFileSync(p, "utf8").trim().split(/\r?\n/);
  const head = lines[0].split(",");
  return lines.slice(1).map((l) => {
    const cells = l.split(",");
    return Object.fromEntries(head.map((h, i) => [h, cells[i]]));
  });
}

const fmt = (v, d) => (v === undefined || v === "" ? "-" : Number(v).toFixed(d));

/** Build the headline table: Choquet + controls under the three protocols. */
function headlineTable() {
  const protocols = [
    ["random_window", "1. Random window"],
    ["subject_aware", "2. Subject-aware"],
    ["loso", "3. Leave-one-subject-out"],
  ];
  const rows = [["Split protocol", "R2", "RMSE", "MARD", "Zone A+B", "Verdict"]];
  let any = false;
  for (const [tag, label] of protocols) {
    const s = readSummary(`fused_${tag}`);
    if (!s) { rows.push([label, "-", "-", "-", "-", "not yet run"]); continue; }
    any = true;
    const ch = s.find((r) => r.Method === "Choquet");
    const bl = s.find((r) => r.Method === "NoSkillBaseline");
    const r2 = Number(ch.R2), r2b = Number(bl ? bl.R2 : 0);
    rows.push([
      label, fmt(ch.R2, 3), fmt(ch.RMSE, 3), fmt(ch.MARD, 1) + "%",
      fmt(ch["Zone A+B"] !== undefined ? ch["Zone A+B"] : ch["ZoneA+B"], 1) + "%",
      r2 > r2b + 0.02 ? "beats the baseline" : "no better than guessing",
    ]);
    rows.push([
      "    (no-skill baseline)", fmt(bl.R2, 3), fmt(bl.RMSE, 3), fmt(bl.MARD, 1) + "%",
      fmt(bl["Zone A+B"] !== undefined ? bl["Zone A+B"] : bl["ZoneA+B"], 1) + "%", "",
    ]);
  }
  return any ? rows : null;
}

// ---------------------------------------------------------------------------
require("./part1_problem")();
require("./part2_data")();
require("./part3_math")();

const headline = headlineTable();
require("./part4_results")({
  headline,
  headlineNote: headline
    ? "Each model row is paired with the no-skill baseline computed on the same folds. " +
      "Read the R-squared column first: it is the one that exposes a model performing no " +
      "better than predicting the average."
    : "",
});

const out = path.join(ROOT, "BTP_presentation.pptx");
D.pres.writeFile({ fileName: out }).then(() => {
  console.log("wrote " + out);
  console.log(headline ? "results table: FILLED" : "results table: placeholder (evaluation still running)");
});
