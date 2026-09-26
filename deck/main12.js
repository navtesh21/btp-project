/* Build the 12-slide presentation. */
const path = require("path");
const D = require("./build_deck");
require("./slides12")();
const out = path.join(__dirname, "..", "BTP_presentation.pptx");
D.pres.writeFile({ fileName: out }).then(() => console.log("wrote " + out));
