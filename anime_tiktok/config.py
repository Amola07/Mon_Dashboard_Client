"""Chargement de config.yaml et surcharges en ligne de commande."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class Config(dict):
    """Dictionnaire de configuration avec accès pratique aux chemins."""

    def __init__(self, data: dict, base_dir: Path):
        super().__init__(data)
        self.base_dir = base_dir

    def path(self, key: str) -> Path:
        p = Path(self["paths"][key])
        return p if p.is_absolute() else self.base_dir / p

    def tool(self, key: str) -> Path:
        p = Path(self["tools"][key])
        return p if p.is_absolute() else self.path("tools") / p

    def style(self, name: str) -> dict:
        styles = self["styles"]
        if name not in styles:
            raise SystemExit(f"Style inconnu : {name!r}. Styles disponibles : {', '.join(styles)}")
        return styles[name]

    @property
    def work(self) -> Path:
        return self.path("work")

    @property
    def tmp(self) -> Path:
        return self.path("tmp") if "tmp" in self["paths"] else self.work / "tmp"


def _parse_value(raw: str) -> Any:
    return yaml.safe_load(raw)


def load_config(path: str | Path, overrides: list[str] | None = None) -> Config:
    path = Path(path).resolve()
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for item in overrides or []:
        if "=" not in item:
            raise SystemExit(f"Surcharge invalide {item!r} : format attendu cle.sous_cle=valeur")
        key, raw = item.split("=", 1)
        node = data
        parts = key.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = _parse_value(raw)
    return Config(data, path.parent)
