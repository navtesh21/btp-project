/* Entry point: node deck/make_ref_deck.js  (run from the repo root) */
const D = require("./build_ref_style");
const build = require("./slides_ref");

build();

const out = "deck/btp_midterm_review.pptx";
D.pres.writeFile({ fileName: out }).then(() => {
  console.log("wrote " + out);
}).catch((e) => {
  console.error(e);
  process.exit(1);
});
