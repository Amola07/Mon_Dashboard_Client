// Exporte chaque élément Open Peeps (composants React) en fichier SVG autonome.
const fs = require("fs"), path = require("path");
const React = require("react"), { renderToStaticMarkup } = require("react-dom/server");
const root = path.join(__dirname, "node_modules/@opeepsfun/open-peeps/build");
const out = path.join(__dirname, "svg");
let n = 0;
function walk(dir, rel) {
  for (const f of fs.readdirSync(dir)) {
    const p = path.join(dir, f);
    if (fs.statSync(p).isDirectory()) { if (f !== "types") walk(p, path.join(rel, f)); continue; }
    if (!f.endsWith(".js") || f === "index.js" || f === "Effigy.js") continue;
    const mod = require(p);
    const name = f.replace(".js", "");
    const comp = mod.default || mod[name];
    const cfg = mod[name + "Config"];
    if (!comp || !cfg) continue;
    const props = { outlineColor: "#1B1B2F", skinColor: "#E8B48A", hairColor: "#2B1D16", beardColor: "#2B1D16",
      topColor: "#4A7BD0", pantsColor: "#2E3A59", shoesColor: "#1B1B2F", jacketColor: "#C9603A", coatColor: "#EDE6D6",
      blazerColor: "#2E3A59", capColor: "#C9603A", beanieColor: "#C9603A", clipColor: "#F2C14E", hijabColor: "#7A5BA6",
      turbanColor: "#E8D9B5", pocketColor: "#F2C14E", paperColor: "#FFFFFF", cupColor: "#FFFFFF", computerColor: "#9AA5B8",
      frameColor: "#1B1B2F", prothesisColor: "#9AA5B8", knifeColor: "#9AA5B8", wheelchairColor: "#9AA5B8",
      bikeFrameColor: "#C9603A", bikeIronColor: "#9AA5B8" };
    const inner = renderToStaticMarkup(React.createElement(comp, props));
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${cfg.width}" height="${cfg.height}" viewBox="${cfg.viewBox}">${inner}</svg>`;
    fs.mkdirSync(path.join(out, rel), { recursive: true });
    fs.writeFileSync(path.join(out, rel, name + ".svg"), svg);
    n++;
  }
}
walk(root, "");
console.log(n, "SVG");
