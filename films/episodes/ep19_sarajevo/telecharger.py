"""Retélécharge les archives Wikimedia de l épisode 19 dans images/ (miniatures : les originaux sont limités en débit)."""
import os
ICI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
import json, urllib.request, urllib.parse, time, urllib.error, re, subprocess
UA = {"User-Agent": "MonDashboardClient/1.0 (https://github.com/amola07/mon_dashboard_client; educational)"}
FILES = {
 "a01_depart": "Franz Ferdinand & Sophie Leave Sarajevo Guildhall.jpg",
 "a02_voiture": "Franz Ferdinand & Sophie Leave Sarajevo Guildhall in a Car.jpg",
 "a03_rues": "Franz Ferdinand & Sophie in Sarajevo Streets.jpg",
 "a04_arrivee": "Archduke Franz Ferdinand in Sarajevo, June 1914 Q91848.jpg",
 "a05_illustration": "DC-1914-27-d-Sarajevo-cropped.jpg",
 "a06_epicerie": "1908-10-07 - Moritz Schiller's Delicatessen.jpg",
 "a07_miljacka": "1914 Miljacka Sarajevo.png",
 "a08_sarajevo": "Sarajevo c. 1914.jpg",
 "a09_princip": "Gavrilo Princip, cell, headshot, bw (cropped).jpg",
 "a10_princip_proces": "Gavrilo Princip, outside court.jpg",
 "a11_chaos": "Ferdinand Behr arrested in Sarajevo 1914.jpg",
 "a12_moment": "The Assassination of Archduke Franz Ferdinand, June 1914 Q79761.jpg",
 "a13_voiture_avant": "Gräf & Stift automobile of Archduke Franz Ferdinand of Austria-0486.jpg",
 "a14_voiture_cote": "Gräf & Stift automobile of Archduke Franz Ferdinand of Austria-0491.jpg",
 "a15_voiture_3": "Gräf & Stift automobile of Archduke Franz Ferdinand of Austria-0496.jpg",
 "a16_tranchee": "Breastwork trench at Armentieres 1916.jpg",
 "a17_front": "The British Army on the Western Front, 1914-1918 Q706.jpg",
 "a18_armistice_train": "Armisticetrain.jpg",
 "a19_carte": "Map Europe alliances 1914-fr.svg",
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
        for wpx in (1920, 1280, 960, 500):
            if wpx >= ii["width"]: continue
            cand = f"{base}/{wpx}px-{name}" + (".jpg" if ext in ("tif", "tiff") else ".png" if ext == "svg" else "")
            try:
                data = urllib.request.urlopen(urllib.request.Request(cand, headers=UA), timeout=60).read()
                ext = "jpg" if ext in ("tif", "tiff") else "png" if ext == "svg" else ext
                print("  thumb", wpx, flush=True); break
            except Exception as e:
                print("  ", wpx, e, flush=True)
    if data is None:
        try: data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception as e: print("FAIL", key, e, flush=True); continue
    open(f"{ICI}/{key}.{ext}", "wb").write(data)
    lic = md.get("LicenseShortName", {}).get("value", "?")
    art = re.sub("<[^>]+>", "", md.get("Artist", {}).get("value", "?")).strip().replace("\n", " ")
    open(f"{ICI}/CREDITS_telechargement.md", "a").write(f"- {key} : « {f} » — {art} — {lic} — {ii['descriptionurl']}\n")
    print(key, len(data), lic, flush=True)
