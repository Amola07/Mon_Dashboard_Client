"""Remplace le paquet `clip` d'OpenAI par le CLIP de Hugging Face (mêmes poids ViT-B/32)."""
import os
import torch
from transformers import CLIPModel, CLIPTokenizer

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "clip_hf")
_tok = CLIPTokenizer.from_pretrained(_DIR)


class _Texte(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.m = CLIPModel.from_pretrained(_DIR)

    def encode_text(self, ids):
        return self.m.text_projection(self.m.text_model(input_ids=ids).pooler_output)


def load(name, device="cpu", jit=False):
    return _Texte().to(device), None


def tokenize(texts, truncate=True):
    if isinstance(texts, str):
        texts = [texts]
    return _tok(texts, padding="max_length", max_length=77, truncation=True, return_tensors="pt")["input_ids"]


class model:
    @staticmethod
    def convert_weights(m):
        return m
