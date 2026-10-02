// Compose des personnages complets (corps + tête + visage + barbe/accessoire) via le composant Effigy.
const fs = require("fs"), path = require("path");
const React = require("react"), { renderToStaticMarkup } = require("react-dom/server");
const { Effigy } = require("@opeepsfun/open-peeps");
const P = { outlineColor: "#1B1B2F", skinColor: "#E8B48A", hairColor: "#2B1D16", topColor: "#4A7BD0", pantsColor: "#2E3A59",
  shoesColor: "#1B1B2F", jacketColor: "#C9603A", coatColor: "#EDE6D6", beardColor: "#2B1D16" };
const skins = ["#F4CFA8", "#E8B48A", "#C68B5E", "#8D5A3B", "#5E3A26"];
const tops = ["#4A7BD0", "#C9603A", "#3E9E7A", "#7A5BA6", "#D9A441", "#E2E8F0"];
const list = JSON.parse(process.argv[2]);
fs.mkdirSync("persos", { recursive: true });
list.forEach((c, i) => {
  const o = Object.assign({}, P, { skinColor: skins[i % 5], topColor: tops[i % 6], hairColor: i % 3 ? "#2B1D16" : "#8A5A2B" });
  const el = React.createElement(Effigy, {
    body: { type: c[0], options: o }, head: { type: c[1], options: o }, face: { type: c[2], options: o },
    beard: c[3] ? { type: c[3], options: o } : undefined, accessory: c[4] ? { type: c[4], options: o } : undefined });
  fs.writeFileSync(`persos/p${String(i).padStart(2, "0")}.svg`, renderToStaticMarkup(el));
});
console.log(list.length);
