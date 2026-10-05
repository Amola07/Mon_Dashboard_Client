"""Dépose l'UE « Animation en code : le style oscilloscope » dans ExaMaster, au nom d'un enseignant.

Crée, dans une formation existante : l'UE (avec sa description et son prix), ses 7 chapitres et ses 14 cours,
publiés. Les illustrations sont envoyées dans le stockage « examaster-images » et leurs adresses remplacées dans
les cours. Rien n'est écrit si l'UE existe déjà chez cet enseignant.

À lancer depuis la racine du projet, avec la clé SERVICE de Supabase (jamais dans un fichier versionné) :

    export SUPABASE_URL="https://cwbsabgmlbufsgdwmcjz.supabase.co"
    export SUPABASE_SERVICE_ROLE_KEY="…"          # Supabase → Project Settings → API → service_role
    python -m films.cours_examaster.importer --essai                         # vérifie sans rien écrire
    python -m films.cours_examaster.importer --formations                    # liste les formations (codes)
    python -m films.cours_examaster.importer --email moi@exemple.com --formation CODE

Options : --prix 2000 (sinon le prix de ue.json, 0 = gratuit) ; --brouillon (cours déposés non publiés).
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
BUCKET = "examaster-images"
DOSSIER_IMAGES = "cours/animation-oscilloscope"


# ------------------------------------------------------------------------------------------------ contenu
def lire_cours(nom):
    texte = open(os.path.join(ICI, "cours", nom), encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", texte, re.S)
    if not m:
        sys.exit(f"{nom} : en-tête --- titre / apercu --- manquant")
    meta = dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M))
    contenu = m.group(2).strip()
    if not meta.get("titre") or not contenu:
        sys.exit(f"{nom} : titre ou contenu vide")
    if len(meta["titre"]) > 160 or len(meta.get("apercu", "")) > 2000:
        sys.exit(f"{nom} : titre (160) ou aperçu (2000) trop long")
    return meta["titre"], meta.get("apercu") or None, contenu


def charger():
    ue = json.load(open(os.path.join(ICI, "ue.json"), encoding="utf-8"))
    if len(ue["description"]) > 2000:
        sys.exit("description de l'UE trop longue (2000 caractères au plus)")
    for ch in ue["chapitres"]:
        ch["cours"] = [lire_cours(n) for n in ch["cours"]]
    return ue


def images_citees(ue):
    noms = set()
    for ch in ue["chapitres"]:
        for _, _, contenu in ch["cours"]:
            noms.update(re.findall(r"\]\(illustrations/([\w.-]+)\)", contenu))
    for n in noms:
        if not os.path.exists(os.path.join(ICI, "illustrations", n)):
            sys.exit(f"illustration manquante : {n}")
    return sorted(noms)


# ------------------------------------------------------------------------------------------------ Supabase
class Supabase:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        self.cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not self.url or not self.cle:
            sys.exit("Il faut SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY dans l'environnement.")

    def requete(self, methode, chemin, corps=None, entetes=None, brut=None):
        h = {"apikey": self.cle, "Authorization": f"Bearer {self.cle}"}
        h.update(entetes or {})
        data = brut
        if corps is not None:
            data = json.dumps(corps).encode()
            h["Content-Type"] = "application/json"
        req = urllib.request.Request(self.url + chemin, data=data, method=methode, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                txt = r.read().decode()
                return json.loads(txt) if txt else None
        except urllib.error.HTTPError as err:
            sys.exit(f"{methode} {chemin} → {err.code} : {err.read().decode()[:400]}")

    def lire(self, table, filtre):
        return self.requete("GET", f"/rest/v1/{table}?{filtre}")

    def inserer(self, table, ligne):
        rep = self.requete("POST", f"/rest/v1/{table}", ligne, {"Prefer": "return=representation"})
        return rep[0]

    def utilisateur(self, email):
        page = 1
        while True:
            rep = self.requete("GET", f"/auth/v1/admin/users?page={page}&per_page=200")
            users = rep.get("users", rep) if isinstance(rep, dict) else rep
            for u in users:
                if (u.get("email") or "").lower() == email.lower():
                    return u["id"]
            if len(users) < 200:
                return None
            page += 1

    def envoyer_image(self, nom):
        chemin = f"{DOSSIER_IMAGES}/{nom}"
        donnees = open(os.path.join(ICI, "illustrations", nom), "rb").read()
        self.requete("POST", f"/storage/v1/object/{BUCKET}/{chemin}", brut=donnees,
                     entetes={"Content-Type": "image/jpeg", "x-upsert": "true"})
        return f"{self.url}/storage/v1/object/public/{BUCKET}/{chemin}"


# ------------------------------------------------------------------------------------------------ dépôt
def main():
    ap = argparse.ArgumentParser(description="Dépose l'UE oscilloscope dans ExaMaster.")
    ap.add_argument("--email", help="compte de l'enseignant qui publie l'UE")
    ap.add_argument("--formation", help="code de la formation (programmes.code)")
    ap.add_argument("--prix", type=int, help="prix de l'UE en F CFA (0 = gratuite)")
    ap.add_argument("--brouillon", action="store_true", help="déposer les cours sans les publier")
    ap.add_argument("--essai", action="store_true", help="vérifier le contenu sans rien écrire")
    ap.add_argument("--formations", action="store_true", help="lister les formations existantes")
    a = ap.parse_args()

    ue = charger()
    images = images_citees(ue)
    nb = sum(len(ch["cours"]) for ch in ue["chapitres"])
    print(f"UE « {ue['nom']} » : {len(ue['chapitres'])} chapitres, {nb} cours, {len(images)} illustrations.")
    if a.essai:
        for ch in ue["chapitres"]:
            print(" ", ch["nom"])
            for titre, _, contenu in ch["cours"]:
                print(f"    - {titre} ({len(contenu)} caractères)")
        print("Contenu valide. Rien n'a été écrit.")
        return

    sb = Supabase()
    if a.formations:
        for p in sb.lire("programmes", "select=code,nom,etablissement&order=nom"):
            print(f"  {p['code']:<16} {p['nom']}  ({p.get('etablissement') or '—'})")
        return
    if not a.email or not a.formation:
        sys.exit("Indique --email (l'enseignant) et --formation (le code). --formations liste les codes.")

    prof = sb.utilisateur(a.email)
    if not prof:
        sys.exit(f"Aucun compte avec l'adresse {a.email}.")
    if not sb.lire("admin_users", f"select=role&user_id=eq.{prof}"):
        sys.exit(f"{a.email} n'est ni enseignant ni administrateur : il ne peut pas publier d'UE.")
    prog = sb.lire("programmes", "select=id,nom&code=eq." + urllib.parse.quote(a.formation))
    if not prog:
        sys.exit(f"Aucune formation avec le code {a.formation}. --formations liste les codes.")
    prog = prog[0]
    deja = sb.lire("ues", f"select=id&programme_id=eq.{prog['id']}&professeur=eq.{prof}"
                          f"&nom=eq.{urllib.parse.quote(ue['nom'])}")
    if deja:
        sys.exit(f"Cette UE existe déjà dans « {prog['nom']} » pour ce compte (id {deja[0]['id']}). Rien n'a été écrit.")

    adresses = {n: sb.envoyer_image(n) for n in images}
    print(f"{len(adresses)} illustrations envoyées.")

    rang = len(sb.lire("ues", f"select=id&programme_id=eq.{prog['id']}"))
    u = sb.inserer("ues", {"programme_id": prog["id"], "nom": ue["nom"], "professeur": prof,
                           "description": ue["description"], "ordre": rang})
    prix = a.prix if a.prix is not None else ue.get("prix", 0)
    sb.inserer("prix_ue", {"ue_id": u["id"], "professeur": prof, "prix": prix})
    for i, ch in enumerate(ue["chapitres"]):
        unite = sb.inserer("unites", {"programme_id": prog["id"], "ue_id": u["id"], "nom": ch["nom"], "ordre": i})
        for j, (titre, apercu, contenu) in enumerate(ch["cours"]):
            for n, url in adresses.items():
                contenu = contenu.replace(f"](illustrations/{n})", f"]({url})")
            sb.inserer("supports", {"unite_id": unite["id"], "professeur": prof, "titre": titre, "apercu": apercu,
                                    "contenu": contenu, "published": not a.brouillon, "ordre": j})
        print(f"  {ch['nom']} : {len(ch['cours'])} cours")
    etat = "en brouillon" if a.brouillon else "publiée"
    print(f"UE {etat} dans « {prog['nom']} » (id {u['id']}), prix : {prix} F.")


if __name__ == "__main__":
    main()
