"""Lecture d'un script de présentation narrée.

Format (une ou plusieurs phrases par ligne) :

    [enigme] Il le ramène 18 ans plus tôt. À l'époque où il était encore un enfant...
    [tendu] Cette fois, ce n'est pas un accident qu'il doit empêcher. {visuel: neige, salle de classe}
    [posé] Cet anime, c'est Erased.

- [émotion] : ton de la voix (et ambiance des plans) jusqu'à la prochaine balise ;
- {visuel: …} : description des plans voulus pour la phrase (optionnelle, aide le choix des plans) ;
- {titre: …} ou « Cet anime, c'est X » : affiche le nom de l'animé en grand à ce moment-là.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Réglages de voix par émotion : vitesse de lecture, silence après la phrase (s),
# et ambiance visuelle recherchée (-1 calme/lumineux … +1 sombre/agité).
EMOTIONS = {
    "neutre": {"speed": 1.00, "pause": 0.40, "mood": 0.0},
    "enigme": {"speed": 0.90, "pause": 0.65, "mood": 0.4},
    "mystere": {"speed": 0.90, "pause": 0.65, "mood": 0.4},
    "tendu": {"speed": 1.07, "pause": 0.30, "mood": 0.8},
    "anxieux": {"speed": 1.05, "pause": 0.35, "mood": 0.7},
    "inquiet": {"speed": 0.95, "pause": 0.50, "mood": 0.6},
    "triste": {"speed": 0.88, "pause": 0.70, "mood": 0.2},
    "determine": {"speed": 1.02, "pause": 0.35, "mood": 0.3},
    "pose": {"speed": 0.92, "pause": 0.70, "mood": -0.5},
    "calme": {"speed": 0.92, "pause": 0.70, "mood": -0.6},
    "enthousiasme": {"speed": 1.10, "pause": 0.30, "mood": -0.2},
    "joyeux": {"speed": 1.08, "pause": 0.30, "mood": -0.6},
    "epique": {"speed": 1.00, "pause": 0.40, "mood": 0.9},
}

_TAG = re.compile(r"\[([^\]]+)\]")
_HINT = re.compile(r"\{\s*(visuel|titre)\s*:\s*([^}]*)\}", re.IGNORECASE)
_TITLE_SENTENCE = re.compile(r"(?:cet|cette|l')\s*anim[eé]\s*,?\s*c'est\s+(.+?)[.!?…]*$", re.IGNORECASE)
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+(?=\S)")


def normalize_emotion(tag: str) -> str:
    """« Déterminé », « enthousiaste », « ENIGME » -> clé connue (sinon « neutre »)."""
    t = unicodedata.normalize("NFKD", tag.strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    if t in EMOTIONS:
        return t
    for key in EMOTIONS:  # enthousiaste -> enthousiasme, mysterieux -> mystere…
        if t[:5] == key[:5]:
            return key
    return "neutre"


@dataclass
class Sentence:
    text: str                 # texte lu par la voix
    emotion: str = "neutre"
    visual: str = ""          # indication de plans {visuel: …}
    title: str = ""           # nom de l'animé à afficher (phrase-titre)
    hints: list[str] = field(default_factory=list)

    @property
    def speed(self) -> float:
        return EMOTIONS[self.emotion]["speed"]

    @property
    def pause(self) -> float:
        return EMOTIONS[self.emotion]["pause"]

    @property
    def mood(self) -> float:
        return EMOTIONS[self.emotion]["mood"]


def parse_script(text: str) -> list[Sentence]:
    """Découpe le script en phrases, chacune avec son émotion et ses indications."""
    sentences: list[Sentence] = []
    emotion = "neutre"
    # On découpe sur les balises d'émotion en gardant leur position.
    pos = 0
    chunks: list[tuple[str, str]] = []
    for m in _TAG.finditer(text):
        if m.start() > pos:
            chunks.append((emotion, text[pos:m.start()]))
        emotion = normalize_emotion(m.group(1))
        pos = m.end()
    chunks.append((emotion, text[pos:]))

    for emo, chunk in chunks:
        chunk = " ".join(chunk.split())
        if not chunk:
            continue
        for part in _SENTENCE_END.split(chunk):
            visual, title = "", ""
            for kind, value in _HINT.findall(part):
                if kind.lower() == "visuel":
                    visual = value.strip()
                else:
                    title = value.strip()
            spoken = " ".join(_HINT.sub("", part).split())
            if not spoken:
                # indication seule : elle s'applique à la phrase précédente
                if sentences:
                    sentences[-1].visual = sentences[-1].visual or visual
                    sentences[-1].title = sentences[-1].title or title
                continue
            if not title and (m := _TITLE_SENTENCE.search(spoken)):
                title = m.group(1).strip()
            sentences.append(Sentence(text=spoken, emotion=emo, visual=visual, title=title))
    return sentences


def estimated_seconds(sentences: list[Sentence], words_per_second: float = 2.6) -> float:
    """Durée approximative une fois lu (utile pour viser plus d'une minute)."""
    total = 0.0
    for s in sentences:
        total += len(s.text.split()) / (words_per_second * s.speed) + s.pause
    return total
