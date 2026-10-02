"""Épisode 13 — « Pourquoi on bâille quand quelqu'un d'autre bâille ? » : montage selon la bible de style (films/montage_ia.py).

    python -m films.episodes.ep13_baillement.montage output/ep13_baillement.mp4
"""
import os
import sys

from films import hook as HK
from films import montage_ia as MI
from films.episodes.ep01_triangle import ep01 as E1

HERE = os.path.dirname(os.path.abspath(__file__))

SEG = [("Pourquoi on bâille quand quelqu'un d'autre bâille ?", 0.00, 2.35),
       ("Il suffit de voir quelqu'un bâiller.", 3.25, 4.92), ("Ou de l'entendre.", 5.43, 6.20),
       ("Chez environ la moitié des adultes,", 6.69, 8.46), ("le réflexe se déclenche en quelques minutes.", 8.79, 11.10),
       ("En 1986,", 11.70, 13.15), ("le neuroscientifique Robert Provine pousse l'expérience plus loin.", 13.40, 16.91),
       ("Il demande à des volontaires de simplement lire un texte sur le bâillement.", 17.46, 20.95),
       ("Ils bâillent.", 21.44, 21.93), ("La simple idée suffit.", 22.38, 23.51),
       ("Mais cette contagion obéit à des règles précises.", 24.08, 26.63),
       ("Elle se transmet d'abord entre membres d'une même famille.", 27.14, 29.83), ("Puis entre amis.", 30.27, 31.22),
       ("Beaucoup moins entre inconnus.", 31.60, 32.84), ("Plus le lien est fort,", 33.32, 34.41),
       ("plus le bâillement se propage.", 34.72, 36.14),
       ("Le fœtus bâille dès la 11e semaine de grossesse.", 36.81, 39.68), ("Pourtant,", 40.09, 40.47),
       ("l'enfant ne devient sensible à la contagion que vers 4 ou 5 ans.", 40.76, 44.04),
       ("L'âge précis où il commence à percevoir les émotions des autres.", 44.47, 47.80),
       ("Le phénomène dépasse l'espèce humaine.", 48.36, 50.36),
       ("Les chimpanzés se transmettent le bâillement, même face à une vidéo.", 50.79, 54.04),
       ("Et en 2008,", 54.46, 55.38),
       ("des chercheurs observent que 21 chiens sur 29 bâillent en voyant un humain bâiller.", 55.64, 60.59),
       ("En 2015,", 61.21, 62.06),
       ("une équipe de l'université Baylor mesure la personnalité de 135 étudiants,", 62.29, 66.81),
       ("puis leur présente des visages qui bâillent.", 67.08, 68.90),
       ("Ceux qui présentent les traits les plus froids et insensibles,", 69.31, 72.05),
       ("proches de la psychopathie,", 72.30, 73.48), ("sont aussi ceux qui bâillent le moins.", 73.75, 75.33),
       ("Reste une question.", 76.02, 77.16), ("À quoi sert le bâillement ?", 77.57, 78.85),
       ("Pendant des siècles, on a pensé qu'il apportait de l'oxygène au cerveau.", 79.31, 82.58),
       ("L'hypothèse est réfutée en 1987 :", 83.03, 85.53),
       ("respirer de l'oxygène pur ne modifie pas la fréquence des bâillements.", 85.86, 89.41),
       ("L'hypothèse actuelle est thermique.", 89.97, 91.91), ("Le bâillement refroidirait le cerveau.", 92.27, 94.26),
       ("Une large inspiration d'air frais,", 94.78, 96.47), ("l'étirement de la mâchoire,", 96.76, 98.17),
       ("un afflux de sang vers le crâne.", 98.44, 100.00),
       ("Une poche de froid posée sur le front suffit à réduire nettement la contagion.", 100.43, 104.59),
       ("Et chez les mammifères,", 105.05, 106.09), ("plus le cerveau est volumineux,", 106.36, 107.83),
       ("plus le bâillement est long.", 108.10, 109.16),
       ("Le mécanisme de la contagion, lui, reste inexpliqué.", 109.80, 112.98),
       ("Pourquoi le cerveau d'un individu réagit-il au bâillement d'un autre…", 113.44, 116.95),
       ("comme s'il était le sien ?", 117.38, 118.47)]

# (plan, début dans la voix d'origine, fin, départ dans le clip, vitesse) — début = premier mot du plan
SHOTS = [("01", 0.00, 3.10, 0.0, 1.0),
         ("02", 3.10, 6.40, 0.0, 1.0),
         ("03", 6.40, 11.50, 0.0, 1.0),
         ("04", 11.50, 17.30, 0.0, 1.0),
         ("05", 17.30, 21.30, 0.0, 1.0),
         ("06", 21.30, 24.00, 0.0, 1.0),
         ("07", 24.00, 26.90, 0.0, 1.0),
         ("08", 26.90, 30.10, 0.0, 1.0),
         ("09", 30.10, 33.10, 0.0, 1.0),
         ("10", 33.10, 36.60, 0.0, 1.0),
         ("11", 36.60, 40.00, 0.0, 1.0),
         ("12", 40.00, 44.30, 0.0, 1.0),
         ("13", 44.30, 48.20, 0.0, 1.0),
         ("14", 48.20, 50.70, 0.0, 1.0),
         ("15", 50.70, 54.40, 0.0, 1.0),
         ("16", 54.40, 57.60, 0.0, 1.0),
         ("17", 57.60, 61.10, 0.0, 1.0),
         ("18", 61.10, 67.00, 0.0, 1.0),
         ("19", 67.00, 69.20, 0.0, 1.0),
         ("20", 69.20, 72.20, 0.0, 1.0),
         ("21", 72.20, 76.00, 0.0, 1.0),
         ("22", 76.00, 79.20, 0.0, 1.0),
         ("23", 79.20, 83.00, 0.0, 1.0),
         ("24", 83.00, 85.80, 0.0, 1.0),
         ("25", 85.80, 89.80, 0.0, 1.0),
         ("26", 89.80, 94.70, 0.0, 1.0),
         ("27", 94.70, 98.30, 0.0, 1.0),
         ("28", 98.30, 100.40, 0.0, 1.0),
         ("29", 100.40, 105.00, 0.0, 1.0),
         ("30", 105.00, 109.70, 0.0, 1.0),
         ("31", 109.70, 113.30, 0.0, 1.0),
         ("32", 113.30, 118.75, 0.0, 1.0)]

FX = [(0.0, E1.swell(0.12), 1.0), (21.44, HK.sub_drop(0.3), 1.0), (24.08, E1.swell(0.1), 1.0),
      (36.81, E1.swell(0.1), 1.0), (48.36, E1.swell(0.1), 1.0), (61.21, E1.swell(0.1), 1.0),
      (73.75, HK.sub_drop(0.3), 1.0), (76.02, E1.swell(0.1), 1.0), (85.86, HK.sub_drop(0.3), 1.0),
      (89.97, E1.swell(0.1), 1.0), (109.80, HK.sub_drop(0.35), 1.0), (117.38, HK.sub_drop(0.4), 1.0)]


if __name__ == "__main__":
    MI.render(sys.argv[1] if len(sys.argv) > 1 else "output/ep13_baillement.mp4",
              os.path.join(HERE, "audio", "voix.mp3"), os.path.join(HERE, "clips"), SEG, SHOTS, FX)
