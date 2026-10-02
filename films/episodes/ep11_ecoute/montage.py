"""Épisode 11 — « Ton téléphone t'écoute ? » : montage selon la bible de style (films/montage_ia.py).

    python -m films.episodes.ep11_ecoute.montage output/ep11_ecoute.mp4
"""
import os
import sys

from films import hook as HK
from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1

HERE = os.path.dirname(os.path.abspath(__file__))

SEG = [("Une conversation entre amis.", 0.00, 1.41), ("Un produit mentionné.", 1.78, 2.72),
       ("Une heure plus tard,", 3.18, 4.03), ("la pub apparaît.", 4.29, 5.12), ("Hasard ?", 5.56, 6.05),
       ("Non.", 6.43, 6.74), ("Tu as raison de te poser la question.", 7.12, 8.68),
       ("Mais la vérité est plus dérangeante.", 9.03, 11.01),
       ("Ton téléphone n'enregistre pas tes conversations.", 11.39, 13.91), ("Il fait pire.", 14.33, 15.06),
       ("Il écoute en permanence.", 15.40, 17.21), ("Une petite puce,", 17.57, 18.48),
       ("séparée du reste,", 18.65, 19.63), ("qui ne dort jamais.", 19.94, 20.90),
       ("Elle garde les dernières secondes de son en mémoire,", 21.35, 23.72),
       ("et les efface aussitôt.", 24.02, 25.20), ("Encore et encore.", 25.56, 27.07),
       ("Elle attend deux mots.", 27.47, 28.32), ("« Dis Siri ».", 28.76, 29.36), ("« OK Google ».", 29.74, 30.45),
       ("Mais pour reconnaître deux mots…", 30.88, 32.28), ("elle doit entendre tous les autres.", 32.65, 34.28),
       ("Et le son ne sert pas qu'à ça.", 34.72, 36.16),
       ("Certaines publicités télé émettent des ultrasons.", 36.52, 39.08),
       ("Des sons que ton oreille ne perçoit pas.", 39.40, 41.16), ("Ton téléphone, lui,", 41.54, 42.78),
       ("les entend.", 43.09, 43.64), ("En 2017,", 44.06, 44.97),
       ("des chercheurs ont trouvé plus de 200 applications capables de les capter.", 45.25, 48.62),
       ("Pour savoir ce que tu regardes.", 49.26, 50.68), ("Et où tu es.", 51.01, 51.68),
       ("La même année,", 52.16, 52.79), ("le fabricant de télévisions Vizio a été condamné.", 53.08, 55.68),
       ("11 millions de téléviseurs.", 56.04, 57.71), ("Pendant des années,", 58.10, 59.04),
       ("ils ont enregistré ce que leurs propriétaires regardaient.", 59.32, 61.81),
       ("Seconde par seconde.", 62.12, 63.62), ("Sans le leur dire.", 63.91, 64.79),
       ("Google et Amazon ont déposé des brevets décrivant des assistants capables de repérer tes centres "
        "d'intérêt dans tes conversations.", 65.24, 71.66),
       ("Et même ton humeur.", 71.99, 73.12), ("Ces brevets sont publics.", 73.45, 74.69),
       ("Pourtant, en 2018,", 75.07, 76.66), ("des chercheurs ont testé plus de 17 000 applications.", 76.88, 79.59),
       ("Résultat :", 79.94, 80.54), ("aucune n'enregistrait tes conversations en secret.", 80.86, 83.29),
       ("Mais certaines faisaient autre chose.", 83.70, 85.44), ("Elles filmaient ton écran.", 85.80, 87.01),
       ("Parce que la vraie surveillance n'a pas besoin de ta voix.", 87.41, 90.10),
       ("Ta position GPS.", 90.51, 91.77), ("Les sites que tu visites.", 92.04, 93.20),
       ("Les achats de tes amis.", 93.49, 94.57), ("Le Wi-Fi auquel tu te connectes,", 94.91, 96.51),
       ("le même que celui de la personne qui t'a parlé du produit.", 96.75, 99.39),
       ("Tout est croisé.", 99.79, 100.53), ("Un algorithme calcule ce que tu vas vouloir…", 100.87, 103.17),
       ("avant que tu le saches.", 103.47, 104.59), ("La pub n'est pas une réaction.", 105.02, 106.54),
       ("C'est une prédiction.", 106.83, 107.87), ("Et le pire ?", 108.28, 108.88), ("Tu as signé.", 109.24, 109.92),
       ("Dans les conditions d'utilisation que personne ne lit.", 110.28, 112.90),
       ("À chaque application qui demande ton micro,", 113.28, 115.28), ("ta position,", 115.51, 116.24),
       ("tes contacts.", 116.47, 117.16), ("Tout ça est légal.", 117.47, 118.61), ("Tu l'as autorisé.", 118.94, 119.90),
       ("Ton téléphone ne t'écoute pas comme tu le penses.", 120.34, 122.48),
       ("Il fait beaucoup plus que ça.", 122.77, 124.14), ("Il te lit.", 124.52, 125.14),
       ("Il te comprend.", 125.48, 126.26), ("Il te prédit.", 126.60, 127.50),
       ("Et c'est toi qui l'as payé.", 127.87, 129.30)]

# (plan, début dans la voix d'origine, fin, départ dans le clip, vitesse) — début = premier mot du plan
SHOTS = [("01", 0.00, 3.10, 0.0, 1.0), ("02", 3.10, 6.90, 0.0, 1.0), ("03", 6.90, 11.20, 0.0, 1.0),
         ("04", 11.20, 15.30, 0.0, 1.0), ("05", 15.30, 21.20, 0.0, 1.0), ("06", 21.20, 27.40, 0.0, 1.0),
         ("07", 27.40, 30.80, 0.0, 1.0), ("08", 30.80, 34.60, 0.0, 1.0), ("09", 34.60, 41.40, 0.0, 1.0),
         ("10", 41.40, 43.90, 0.0, 1.0), ("11", 43.90, 51.80, 0.0, 1.0), ("12", 51.80, 57.90, 0.0, 1.0),
         ("13", 57.90, 65.00, 0.0, 1.0), ("14", 65.00, 74.90, 0.0, 1.0), ("15", 74.90, 83.50, 0.0, 1.0),
         ("16", 83.50, 87.30, 0.0, 1.0), ("17", 87.30, 90.40, 0.0, 1.0), ("18", 90.40, 94.80, 0.0, 1.0),
         ("19", 94.80, 100.70, 0.0, 1.0), ("20", 100.70, 104.90, 0.0, 1.0), ("21", 104.90, 108.10, 0.0, 1.0),
         ("22", 108.10, 112.90, 0.0, 1.0), ("23", 112.90, 120.10, 0.0, 1.0), ("24", 120.10, 124.40, 0.0, 1.0),
         ("25", 124.40, 129.30, 0.0, 1.0)]

FX = [(0.0, E1.swell(0.12), 1.0), (6.43, HK.sub_drop(0.35), 1.0), (9.03, E1.swell(0.1), 1.0),
      (53.08, HK.sub_drop(0.4), 1.0), (85.80, E1.swish(0.5, 0.08), 1.0), (105.02, E1.swell(0.1), 1.0),
      (109.24, HK.sub_drop(0.3), 1.0), (127.87, HK.sub_drop(0.3), 1.0)]


if __name__ == "__main__":
    MI.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep11_ecoute.mp4",
              os.path.join(HERE, "audio", "voix.mp3"), os.path.join(HERE, "clips"), SEG, SHOTS, FX)
