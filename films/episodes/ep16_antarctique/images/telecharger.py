"""Retélécharge les images Wikimedia Commons (miniatures, les originaux sont limités en débit). Les images NASA
viennent de images-api.nasa.gov/asset/<id> ; Clinton : miniatures 500px-seek=20 et seek=60 de la vidéo (voir CREDITS.md)."""
import os
ICI = os.path.dirname(os.path.abspath(__file__))
import json, urllib.request, urllib.parse, time, urllib.error, re, subprocess
UA = {"User-Agent": "MonDashboardClient/1.0 (https://github.com/amola07/mon_dashboard_client; educational)"}
FILES = {
 "01_bulles": "CSIRO ScienceImage 518 Air Bubbles Trapped in Ice.jpg",
 "02_antarctique": "Antarctica 6400px from Blue Marble.jpg",
 "03_couches": "GISP2 1855m ice core layers.png",
 "04_lame": "Ice thin-section awi.jpg",
 "05_bulles2": "CSIRO ScienceImage 521 Bubbles in Ice.jpg",
 "06_forage": "Ice-core drill hg.jpg",
 "07_camp": "Antarctica WAIS Divide Field Camp 10.jpg",
 "08_carotte": "Epica-dml end hg.jpg",
 "09_stock": "The EastGRIP ice core in core buffer.jpg",
 "10_foret": "Tree fern understorey in Whirinaki Forest.jpg",
 "10b_foret": "A temperate Rainforest (52295290076).jpg",
 "11_dino": "Cryolophosaurus skeletal mount.jpg",
 "12_courant": "Antarctic Circumpolar Current.jpg",
 "13_glace": "A view of Antarctica’s ice sheet and mountains.jpeg",
 "14_glacebleue": "Blue ice (30724543322).jpg",
 "15_meteorite": "Miller Range, Antarctica - Meteorite (2).jpg",
 "16_clinton": "Pres. Clinton's Remarks on the Possible Discovery of Life on Mars.webm",
}
def get(url, raw=False):
    for k in range(6):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60)
            return r.read() if raw else json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(20 * (k + 1))
credits = []
import os
for key, f in FILES.items():
    if any(x.startswith(key + ".") for x in os.listdir(ICI)): continue
    time.sleep(2)
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "titles": "File:" + f,
        "prop": "imageinfo", "iiprop": "url|size|extmetadata", "format": "json"})
    d = get(u)
    p = list(d["query"]["pages"].values())[0]
    if "imageinfo" not in p:
        print("MISSING", key, f, flush=True); continue
    ii = p["imageinfo"][0]; md = ii["extmetadata"]
    url = ii["url"].split("?")[0]
    name = url.rsplit("/", 1)[1]
    ext = name.rsplit(".", 1)[1].lower()
    data = None
    if ext != "webm":
        base = url.replace("/commons/", "/commons/thumb/", 1)
        for wpx in (1920, 1280, 960):
            if wpx >= ii["width"]: continue
            cand = f"{base}/{wpx}px-{name}" + (".jpg" if ext in ("tif", "tiff") else "")
            try:
                data = urllib.request.urlopen(urllib.request.Request(cand, headers=UA), timeout=60).read()
                ext = "jpg" if ext in ("tif", "tiff") else ext
                print("  thumb", wpx, flush=True); break
            except Exception as e:
                print("  ", wpx, e, flush=True)
    if data is None:
        try: data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception as e: print("FAIL", key, e, flush=True); continue
    open(f"{ICI}/{key}.{ext}", "wb").write(data)
    lic = md.get("LicenseShortName", {}).get("value", "?")
    art = re.sub("<[^>]+>", "", md.get("Artist", {}).get("value", "?")).strip().replace("\n", " ")
    open(f"{ICI}/CREDITS_commons.md", "a").write(f"- {key} : « {f} » — {art} — {lic} — {ii['descriptionurl']}\n")
    print(key, len(data), lic, flush=True)
