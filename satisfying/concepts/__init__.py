"""Un module par concept. Chaque module expose TITLE et render(ctx) -> durée en secondes."""
from importlib import import_module

NAMES = ["grow", "escape", "pendulum", "spiro", "multiply", "sand", "ocean", "aurora"]


def load(name):
    if name not in NAMES:
        raise SystemExit(f"Concept inconnu : {name}. Disponibles : {', '.join(NAMES)}")
    return import_module(f"{__name__}.{name}")
