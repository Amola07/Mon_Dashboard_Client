"""Test de bout en bout sur de faux épisodes, avec les backends CPU (ffmpeg + Lanczos).

    python tests/test_pipeline.py        (ou : pytest tests/)
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from make_fixtures import OP_SECONDS, main as make_fixtures  # noqa: E402

from anime_tiktok.montage import detect_beats  # noqa: E402

SETS = [
    "analysis.op_ed_min_seconds=30", "selection.min_seconds=4", "selection.max_seconds=10",
    "selection.clips_total=3", "selection.max_per_episode=1", "render.width=180", "render.height=320",
    "render.fps=48", "render.encoder=libx264", "styles.hype.video_seconds=8",
]


def _cli(workdir: Path, *args: str) -> None:
    sets = [x for s in SETS for x in ("--set", s)]
    subprocess.run([sys.executable, "-m", "anime_tiktok", *args, "--config", str(workdir / "config.yaml"), *sets],
                   cwd=ROOT, check=True)


def _probe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-print_format", "json", "-show_streams",
                          str(path)], capture_output=True, text=True, check=True).stdout
    return {s["codec_type"]: s for s in json.loads(out)["streams"]}


def test_pipeline() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        make_fixtures(work)
        (work / "config.yaml").write_text((ROOT / "config.yaml").read_text(encoding="utf-8"), encoding="utf-8")

        _cli(work, "analyze")
        meta = json.loads((work / "work/analysis/episode_02.json").read_text())
        (s, e), = meta["excluded"]
        assert s < 2 and abs(e - OP_SECONDS) < 3, f"opening mal détecté : {meta['excluded']}"

        _cli(work, "select")
        with open(work / "work/selection/clips.csv", encoding="utf-8") as f:
            clips = list(csv.DictReader(f))
        assert len(clips) == 3
        assert all(float(c["start"]) > OP_SECONDS for c in clips), "un extrait tombe dans l'opening"

        _cli(work, "make", "--style", "brut")
        (brut_dir,) = (work / "output").glob("*_brut")
        videos = sorted(brut_dir.glob("*.mp4"))
        assert len(videos) == 3 and len(list(brut_dir.glob("*.txt"))) == 3
        streams = _probe(videos[0])
        v = streams["video"]
        assert (v["width"], v["height"], v["r_frame_rate"]) == (180, 320, "48/1")
        assert "audio" in streams
        clip = next(c for c in clips if c["id"] == videos[0].stem)
        hook = 1.5 if float(clip["duration"]) > 1.5 * 3 else 0  # pas d'accroche sur un extrait très court
        expected = (float(clip["duration"]) + hook) * 48
        assert abs(int(v["nb_read_frames"]) - expected) <= 3

        _cli(work, "make", "--style", "hype")
        (hype_video,) = (work / "output").glob("*_hype/*.mp4")
        assert abs(float(_probe(hype_video)["video"]["duration"]) - 8) < 1

        _cli(work, "make", "--style", "cinematique")
        assert len(list((work / "output").glob("*_cinematique/*.mp4"))) == 3

        tempo, beats = detect_beats(work / "input/music/beat120.mp3")
        assert abs(tempo - 120) < 1, tempo
        assert abs((beats[-1] - beats[0]) / (len(beats) - 1) - 0.5) < 0.005
    print("OK : analyse, sélection, rendu et 3 styles de montage")


if __name__ == "__main__":
    test_pipeline()
