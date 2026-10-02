"""Épisode 12 — « Ce que cache encore la Grande Pyramide » : montage selon la bible de style (films/montage_ia.py).

    python -m films.episodes.ep12_pyramide.montage output/ep12_pyramide.mp4
"""
import os
import sys

from films import hook as HK
from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1

HERE = os.path.dirname(os.path.abspath(__file__))

SEG = [("En 2017,", 0.00, 1.08),
       ("des physiciens ont envoyé des particules venues de l'espace à travers la Grande Pyramide.", 1.32, 5.71),
       ("Et ils ont vu quelque chose qui ne devrait pas être là.", 6.24, 8.85), ("Un vide.", 9.42, 9.95),
       ("Long d'au moins trente mètres.", 10.46, 12.01), ("Au cœur de la pyramide.", 12.46, 13.75),
       ("Personne ne l'a jamais ouvert.", 14.26, 15.73), ("Personne ne sait ce qu'il contient.", 16.11, 17.67),
       ("Tu crois qu'on connaît tout de la Grande Pyramide ?", 18.21, 20.08), ("Elle a 4 500 ans.", 20.49, 22.00),
       ("Et elle n'a pas fini de nous surprendre.", 22.40, 24.07), ("Première énigme.", 24.74, 25.56),
       ("2,3 millions de blocs.", 25.97, 27.70), ("20 ans de chantier.", 27.95, 29.06),
       ("Ça fait un bloc posé toutes les deux minutes.", 29.47, 31.76), ("Jour et nuit ?", 32.12, 32.61),
       ("Personne n'a jamais retrouvé comment ils montaient les derniers,", 33.05, 35.60),
       ("à plus de 100 mètres de haut.", 35.90, 37.27), ("Deuxième énigme.", 37.88, 38.76),
       ("Au cœur de la pyramide,", 39.19, 40.41), ("la chambre du roi.", 40.68, 41.69),
       ("Son plafond est fait de poutres de granit.", 42.11, 44.21), ("Jusqu'à 80 tonnes chacune.", 44.52, 46.25),
       ("Venues d'une carrière à 800 kilomètres.", 46.60, 48.97), ("Et hissées à 40 mètres du sol.", 49.34, 51.40),
       ("Sans poulie.", 51.77, 52.37), ("Sans roue.", 52.70, 53.15), ("Troisième énigme.", 53.78, 54.66),
       ("Dans cette chambre,", 55.08, 55.89), ("un sarcophage.", 56.20, 57.06), ("Vide.", 57.40, 57.82),
       ("Sans couvercle.", 58.13, 58.92), ("Et trop large pour passer par les couloirs.", 59.27, 61.13),
       ("Il a été posé là pendant la construction…", 61.56, 63.44), ("puis tout a été bâti autour.", 63.83, 65.49),
       ("Le corps du pharaon ?", 65.90, 66.69), ("Jamais retrouvé.", 67.10, 67.95),
       ("Quatrième énigme.", 68.59, 69.51), ("Deux conduits minuscules partent d'une autre chambre.", 69.91, 72.65),
       ("20 centimètres de large.", 72.95, 74.26), ("En 1993, un robot s'y glisse.", 74.68, 77.38),
       ("Au bout de 60 mètres,", 77.74, 78.93), ("il tombe sur une petite porte de pierre.", 79.16, 81.11),
       ("Avec deux poignées de cuivre.", 81.49, 82.97), ("En 2002,", 83.41, 84.08), ("on perce la porte.", 84.36, 85.41),
       ("Derrière…", 85.78, 86.35), ("une deuxième porte.", 86.75, 87.81), ("Cinquième énigme.", 88.37, 89.30),
       ("En 2023,", 89.72, 90.64), ("une caméra est glissée dans une fissure de la façade nord.", 90.92, 93.77),
       ("Elle révèle un couloir caché.", 94.15, 95.58), ("9 mètres.", 95.93, 96.66), ("Vide.", 96.99, 97.43),
       ("Scellé depuis 4 500 ans.", 97.75, 99.67), ("Il ne mène nulle part.", 100.08, 101.18),
       ("Ou pas encore.", 101.56, 102.70),
       ("Et ce grand vide de 30 mètres, juste au-dessus de la galerie principale ?", 103.29, 106.74),
       ("Les scientifiques savent où il est.", 107.14, 108.48), ("Ils connaissent sa taille.", 108.84, 109.87),
       ("Mais aucune caméra,", 110.22, 111.34), ("aucun robot,", 111.58, 112.30),
       ("aucun être humain n'y est jamais entré.", 112.52, 114.40), ("Une chambre.", 114.86, 115.46),
       ("Fermée depuis l'époque des pharaons.", 115.75, 117.47),
       ("Au cœur du monument le plus étudié de la planète.", 117.84, 120.61),
       ("Qu'est-ce qu'ils ont voulu cacher…", 121.03, 122.43),
       ("là où personne ne devait jamais regarder ?", 122.76, 124.98)]

# (plan, début dans la voix d'origine, fin, départ dans le clip, vitesse) — début = premier mot du plan
SHOTS = [("01", 0.00, 6.10, 0.0, 1.0),
           ("02", 6.10, 9.30, 0.0, 1.0),
           ("03", 9.30, 14.10, 0.0, 1.0),
           ("04", 14.10, 18.10, 0.0, 1.0),
           ("05", 18.10, 24.60, 0.0, 1.0),
           ("06", 24.60, 29.30, 0.0, 1.0),
           ("07", 29.30, 32.90, 0.0, 1.0),
           ("08", 32.90, 37.70, 0.0, 1.0),
           ("09", 37.70, 42.00, 0.0, 1.0),
           ("10", 42.00, 46.40, 0.0, 1.0),
           ("11", 46.40, 49.20, 0.0, 1.0),
           ("12", 49.20, 53.60, 0.0, 1.0),
           ("13", 53.60, 57.30, 0.0, 1.0),
           ("14", 57.30, 61.40, 0.0, 1.0),
           ("15", 61.40, 65.70, 0.0, 1.0),
           ("16", 65.70, 68.40, 0.0, 1.0),
           ("17", 68.40, 74.50, 0.0, 1.0),
           ("18", 74.50, 79.00, 0.0, 1.0),
           ("19", 79.00, 83.20, 0.0, 1.0),
           ("20", 83.20, 88.20, 0.0, 1.0),
           ("21", 88.20, 94.00, 0.0, 1.0),
           ("22", 94.00, 99.90, 0.0, 1.0),
           ("23", 99.90, 103.10, 0.0, 1.0),
           ("24", 103.10, 108.70, 0.0, 1.0),
           ("25", 108.70, 114.70, 0.0, 1.0),
           ("26", 114.70, 120.80, 0.0, 1.0),
           ("27", 120.80, 125.23, 0.0, 1.0)]

FX = [(0.0, E1.swell(0.12), 1.0), (9.42, HK.sub_drop(0.35), 1.0), (24.74, E1.swell(0.1), 1.0),
      (37.88, E1.swell(0.1), 1.0), (53.78, E1.swell(0.1), 1.0), (67.10, HK.sub_drop(0.3), 1.0),
      (68.59, E1.swell(0.1), 1.0), (86.75, HK.sub_drop(0.35), 1.0), (88.37, E1.swell(0.1), 1.0),
      (112.52, HK.sub_drop(0.3), 1.0), (122.76, HK.sub_drop(0.4), 1.0)]


if __name__ == "__main__":
    MI.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep12_pyramide.mp4",
              os.path.join(HERE, "audio", "voix.mp3"), os.path.join(HERE, "clips"), SEG, SHOTS, FX)
