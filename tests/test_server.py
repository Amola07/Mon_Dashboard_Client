"""Test du serveur de contrôle (API utilisée par l'application mobile), sur de faux épisodes.

    python tests/test_server.py        (ou : pytest tests/)
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from fastapi.testclient import TestClient  # noqa: E402

from make_fixtures import main as make_fixtures  # noqa: E402

from anime_tiktok.server import Notifier, create_app  # noqa: E402

SETS = [
    "analysis.op_ed_min_seconds=30", "selection.min_seconds=4", "selection.max_seconds=10",
    "selection.max_per_episode=1", "render.width=180", "render.height=320", "render.encoder=libx264",
]


def _wait(client: TestClient, headers: dict, timeout: float = 300) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout:
        job = client.get("/api/jobs/current", headers=headers).json()
        if job["status"] != "running":
            return job
        time.sleep(0.5)
    raise TimeoutError("tâche trop longue")


def test_server() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        make_fixtures(work)
        shutil.copy(ROOT / "config.yaml", work / "config.yaml")
        app = create_app(work / "config.yaml", SETS, "secret", Notifier(None))
        client = TestClient(app)
        h = {"Authorization": "Bearer secret"}

        assert client.get("/api/ping").status_code == 200
        assert client.get("/api/status").status_code == 401
        assert client.get("/api/status", headers={"Authorization": "Bearer faux"}).status_code == 401

        st = client.get("/api/status", headers=h).json()
        assert st["episodes"] == 3 and st["analyzed"] == 0 and "hype" in st["styles"]

        r = client.put("/api/settings", headers=h, json={"render.fps": 48, "selection.clips_total": 2,
                                                         "delivery.anime": "Test Anime"})
        assert r.status_code == 200 and r.json()["render.fps"] == 48
        assert client.put("/api/settings", headers=h, json={"paths.work": "/"}).status_code == 400

        job = client.post("/api/jobs", headers=h, json={"command": "analyze"}).json()
        assert client.post("/api/jobs", headers=h, json={"command": "select"}).status_code == 409
        job = _wait(client, h)
        assert job["status"] == "done" and job["progress"] == 1.0, job

        eps = client.get("/api/episodes", headers=h).json()
        assert all(e["analyzed"] and e["excluded"] for e in eps)

        client.post("/api/jobs", headers=h, json={"command": "select"})
        assert _wait(client, h)["status"] == "done"
        clips = client.get("/api/clips", headers=h).json()
        assert len(clips) == 2 and all(c["keep"] for c in clips)
        cid = clips[0]["id"]
        assert client.get(f"/api/clips/{cid}/thumb", headers=h).headers["content-type"] == "image/jpeg"
        assert client.get(f"/api/clips/{cid}/preview?token=secret").status_code == 200
        assert client.put("/api/clips/keep", headers=h, json={"keep": {clips[1]["id"]: False}}).json()["kept"] == 1

        client.post("/api/jobs", headers=h, json={"command": "make", "style": "brut"})
        job = _wait(client, h)
        assert job["status"] == "done", job["log"][-5:]
        outs = client.get("/api/outputs", headers=h).json()
        assert len(outs) == 1 and outs[0]["style"] == "brut" and len(outs[0]["videos"]) == 1
        video = outs[0]["videos"][0]
        assert "Test Anime" in video["caption"] and "#48fps" in video["caption"]
        url = f"/api/outputs/{outs[0]['folder']}/{video['name']}"
        part = client.get(url, headers={**h, "Range": "bytes=0-99"})
        assert part.status_code == 206 and len(part.content) == 100
        assert client.get(f"/api/outputs/{outs[0]['folder']}/..%2F..%2Fconfig.yaml", headers=h).status_code == 404

        r = client.post("/api/upload/music", headers=h, files={"file": ("son.mp3", b"ID3fake", "audio/mpeg")})
        assert r.status_code == 200
        assert {m["name"] for m in client.get("/api/music", headers=h).json()} == {"beat120.mp3", "son.mp3"}
        bad = client.post("/api/upload/music", headers=h, files={"file": ("x.exe", b"MZ", "application/octet-stream")})
        assert bad.status_code == 400

        # Présentation narrée : préparation (voix + plans), changement d'un plan, rendu
        script = "[enigme] Il le ramène 18 ans plus tôt. [posé] Cet anime, c'est Erased."
        r = client.post("/api/presentations", headers=h, json={"script": script, "name": "Erased test"})
        assert r.status_code == 200 and r.json()["name"] == "erased-test", r.text
        job = _wait(client, h)
        assert job["status"] == "done", job["log"][-5:]
        assert [p["name"] for p in client.get("/api/presentations", headers=h).json()] == ["erased-test"]
        plan = client.get("/api/presentations/erased-test", headers=h).json()
        assert plan["title"] == "Erased" and len(plan["sentences"]) == 2 and plan["slots"]
        assert client.put("/api/presentations/erased-test/slots/0", headers=h, json={"choice": 1}).json()["choice"] == 1
        assert client.put("/api/presentations/erased-test/slots/0", headers=h, json={"choice": 99}).status_code == 400
        assert client.get("/api/presentations/erased-test/thumbs/0/1", headers=h).status_code == 200
        assert client.get("/api/presentations/erased-test/voice?token=secret").status_code == 200
        assert client.get("/api/presentations/..%2F..%2Fconfig.yaml", headers=h).status_code == 404
        client.post("/api/presentations/erased-test/render", headers=h)
        job = _wait(client, h)
        assert job["status"] == "done", job["log"][-5:]
        pres = [o for o in client.get("/api/outputs", headers=h).json() if o["style"] == "presentation"]
        assert pres and pres[0]["videos"][0]["name"] == "erased-test.mp4"
        assert client.delete("/api/presentations/erased-test", headers=h).status_code == 200

        assert client.delete(f"/api/outputs/{outs[0]['folder']}", headers=h).status_code == 200
        assert all(o["style"] == "presentation" for o in client.get("/api/outputs", headers=h).json())
    print("OK : serveur de contrôle")


if __name__ == "__main__":
    test_server()
