"""Fabrique la migration SQL qui dépose l'UE oscilloscope dans ExaMaster (à coller dans l'éditeur SQL de Supabase).

    python -m films.cours_examaster.generer_migration
    → films/cours_examaster/046_cours_animation_oscilloscope.sql
"""
import os
import subprocess

from films.cours_examaster.importer import ICI, charger, images_citees

DEPOT = "Amola07/Mon_Dashboard_Client"


def dollar(texte, tag):
    if f"${tag}$" in texte:
        raise SystemExit(f"le texte contient ${tag}$")
    return f"${tag}${texte}${tag}$"


def main():
    ue = charger()
    images_citees(ue)
    # Adresse figée sur le commit qui contient les illustrations (le dépôt est public).
    sha = subprocess.run(["git", "log", "-1", "--format=%H", "--", os.path.join(ICI, "illustrations")],
                         capture_output=True, text=True, check=True).stdout.strip()
    base = f"https://raw.githubusercontent.com/{DEPOT}/{sha}/films/cours_examaster/illustrations/"
    l = []
    w = l.append
    w("-- ════════════════════════════════════════════════════════════════════════════")
    w(f"-- 046 — UE « {ue['nom']} »")
    w("-- ════════════════════════════════════════════════════════════════════════════")
    w("--")
    nb = sum(len(c['cours']) for c in ue['chapitres'])
    w(f"-- Dépose une UE complète : {len(ue['chapitres'])} chapitres, {nb} cours publiés, au nom d'un enseignant.")
    w("-- À coller tel quel dans Supabase → SQL Editor → Run. Sans risque à relancer : si l'UE existe déjà")
    w("-- chez ce compte, rien n'est écrit. Sans compte ni formation (base vierge), rien n'est écrit non plus.")
    w("--")
    w("-- Réglages (début du bloc) :")
    w("--   v_email : le compte qui publie ; NULL = le super administrateur ;")
    w("--   v_code  : le code de la formation ; NULL = celle où ce compte publie déjà le plus d'UE ;")
    w("--   v_prix  : en F CFA, 0 = gratuite.")
    w("--")
    w("-- Généré par films/cours_examaster/generer_migration.py (dépôt Mon_Dashboard_Client) ;")
    w("-- les illustrations sont servies depuis ce dépôt public, figées sur un commit.")
    w("")
    w("DO $depot$")
    w("DECLARE")
    w("  v_email TEXT    := NULL;")
    w("  v_code  TEXT    := NULL;")
    w(f"  v_prix  INTEGER := {int(ue.get('prix', 0))};")
    w("")
    w(f"  v_nom   TEXT := {dollar(ue['nom'], 'n')};")
    w(f"  v_img   TEXT := '{base}';")
    w("  v_prof  UUID;")
    w("  v_prog  UUID;")
    w("  v_ue    UUID;")
    w("  v_ch    UUID;")
    w("BEGIN")
    w("  IF v_email IS NOT NULL THEN")
    w("    SELECT id INTO v_prof FROM auth.users WHERE lower(email) = lower(v_email);")
    w("  ELSE")
    w("    SELECT user_id INTO v_prof FROM public.admin_users")
    w("     WHERE role = 'superadmin' ORDER BY granted_at LIMIT 1;")
    w("  END IF;")
    w("  IF v_prof IS NULL THEN")
    w("    RAISE NOTICE 'UE oscilloscope : aucun compte enseignant trouvé, rien n''est écrit.';")
    w("    RETURN;")
    w("  END IF;")
    w("")
    w("  IF v_code IS NOT NULL THEN")
    w("    SELECT id INTO v_prog FROM public.programmes WHERE code = v_code;")
    w("  ELSE")
    w("    SELECT programme_id INTO v_prog FROM public.ues WHERE professeur = v_prof")
    w("     GROUP BY programme_id ORDER BY count(*) DESC LIMIT 1;")
    w("    IF v_prog IS NULL THEN")
    w("      SELECT id INTO v_prog FROM public.programmes ORDER BY cree_le LIMIT 1;")
    w("    END IF;")
    w("  END IF;")
    w("  IF v_prog IS NULL THEN")
    w("    RAISE NOTICE 'UE oscilloscope : aucune formation trouvée, rien n''est écrit.';")
    w("    RETURN;")
    w("  END IF;")
    w("")
    w("  IF EXISTS (SELECT 1 FROM public.ues")
    w("              WHERE programme_id = v_prog AND professeur = v_prof AND nom = v_nom) THEN")
    w("    RAISE NOTICE 'UE oscilloscope : déjà présente chez ce compte, rien n''est écrit.';")
    w("    RETURN;")
    w("  END IF;")
    w("")
    w("  INSERT INTO public.ues (programme_id, nom, professeur, description, ordre)")
    w(f"  VALUES (v_prog, v_nom, v_prof, {dollar(ue['description'], 'd')},")
    w("          (SELECT count(*) FROM public.ues WHERE programme_id = v_prog)::SMALLINT)")
    w("  RETURNING id INTO v_ue;")
    w("  INSERT INTO public.prix_ue (ue_id, professeur, prix) VALUES (v_ue, v_prof, v_prix);")
    for i, ch in enumerate(ue["chapitres"]):
        w("")
        w(f"  -- ── {ch['nom']} " + "─" * max(4, 70 - len(ch['nom'])))
        w("  INSERT INTO public.unites (programme_id, ue_id, nom, ordre)")
        w(f"  VALUES (v_prog, v_ue, {dollar(ch['nom'], 'n')}, {i}) RETURNING id INTO v_ch;")
        for j, (titre, apercu, contenu) in enumerate(ch["cours"]):
            w("")
            w("  INSERT INTO public.supports (unite_id, professeur, titre, apercu, contenu, published, ordre)")
            w(f"  VALUES (v_ch, v_prof, {dollar(titre, 't')},")
            w(f"    {dollar(apercu, 'a') if apercu else 'NULL'},")
            w(f"    replace({dollar(contenu, 'c')}, '](illustrations/', '](' || v_img),")
            w(f"    true, {j});")
    w("")
    w(f"  RAISE NOTICE 'UE oscilloscope déposée : {len(ue['chapitres'])} chapitres, {nb} cours (UE %).', v_ue;")
    w("END")
    w("$depot$;")
    sortie = os.path.join(ICI, "046_cours_animation_oscilloscope.sql")
    with open(sortie, "w", encoding="utf-8") as f:
        f.write("\n".join(l) + "\n")
    print("écrit :", sortie)


if __name__ == "__main__":
    main()
