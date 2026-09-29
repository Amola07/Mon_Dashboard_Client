"""Illustrations clés d'anime (Kaggle, GPU) + cartes de profondeur, puis animation « motion comic ».

Modèle d'image : Animagine XL 4.0 (licence CreativeML Open RAIL++-M, usage commercial autorisé).
Profondeur : Depth Anything V2 (petit modèle).

    python -m films.anime.keyart <dossier de sortie> [nombre d'images par invite]
"""
import sys
from pathlib import Path

QUALITY = "masterpiece, high score, great score, absurdres"
NEGATIVE = ("lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, fewer digits, cropped, "
            "worst quality, low quality, low score, bad score, average score, signature, watermark, username, blurry")
PROMPTS = {
    "falaise": "1girl, solo, standing on a cliff edge at night, from behind, looking up at a vast starry sky, milky way, "
               "nebula, holding a small glowing blue star lantern, long dark blue hair blowing in the wind, red scarf, "
               "cape, wide shot, cinematic lighting, mysterious, cosmic",
    "toits": "1boy, solo, sitting on a rooftop of a sleeping town at night, shooting stars, purple nebula sky, "
             "glowing blue particles floating, wind, hood, looking up, wide shot, cinematic lighting, mysterious, cosmic",
    "cosmos": "1girl, solo, floating in space among glowing constellations, closed eyes, peaceful, long white hair floating, "
              "ethereal blue light, stars, galaxy, cosmic, dreamy, full body, cinematic lighting",
}


def main(out, per_prompt=2):
    import torch
    from diffusers import StableDiffusionXLPipeline
    from transformers import pipeline

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    pipe = StableDiffusionXLPipeline.from_pretrained("cagliostrolab/animagine-xl-4.0", torch_dtype=torch.float16,
                                                     use_safetensors=True).to("cuda")
    pipe.enable_vae_slicing()
    images = []
    for name, prompt in PROMPTS.items():
        for k in range(per_prompt):
            g = torch.Generator("cuda").manual_seed(1000 + k)
            img = pipe(f"{prompt}, {QUALITY}", negative_prompt=NEGATIVE, width=832, height=1216,
                       num_inference_steps=28, guidance_scale=5.0, generator=g).images[0]
            path = out / f"{name}_{k}.png"
            img.save(path)
            images.append(path)
            print("illustration :", path, flush=True)
    del pipe
    torch.cuda.empty_cache()
    depth = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device=0)
    from PIL import Image
    for path in images:
        d = depth(Image.open(path))["depth"]
        dpath = path.with_name(path.stem + "_profondeur.png")
        d.save(dpath)
        print("profondeur :", dpath, flush=True)
    from .motion import render
    for path in images:
        video = path.with_suffix(".mp4")
        render(str(path), str(path.with_name(path.stem + "_profondeur.png")), str(video), 8.0)
        print("animation :", video, flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "output/anime", int(sys.argv[2]) if len(sys.argv) > 2 else 2)
