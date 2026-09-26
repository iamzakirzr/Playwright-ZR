"""Vision-LLM visual comparison (opt-in).

Pixel diffs answer "did anything change?". A vision model can answer "does the
change *matter*?": for example, a moved button versus a slightly different
font weight. It's slower and non-deterministic, so it supplements the pixel
comparator rather than replacing it. It needs a vision model in Ollama, e.g.
``ollama pull qwen2.5vl:3b``.

Measured with qwen2.5vl:3b: sending the two screenshots as separate images, it
called an obviously changed page "same". A single **side-by-side composite**
(baseline left, new right) gave the right verdict for both changed and
identical pages. Its written ``differences`` still contained hallucinations
(it described the separator bar as a background change), so treat the verdict
as advisory and the prose as a hint, never as a gate.
"""

from __future__ import annotations

import base64
import io
import json
from dataclasses import dataclass

import httpx
from PIL import Image

PROMPT = (
    "The image shows two versions of the same web component side by side: LEFT is the approved baseline, "
    "RIGHT is the new version (separated by a black bar). Compare them carefully: element positions, spacing, "
    'colours and text. Reply with JSON only: {"same": true|false, "differences": ["..."]}'
)
SEPARATOR_PX = 20


def side_by_side(left_png: bytes, right_png: bytes) -> bytes:
    """One PNG with ``left`` and ``right`` next to each other, split by a black bar."""
    left, right = Image.open(io.BytesIO(left_png)), Image.open(io.BytesIO(right_png))
    canvas = Image.new("RGB", (left.width + right.width + SEPARATOR_PX, max(left.height, right.height)), "black")
    canvas.paste(left, (0, 0))
    canvas.paste(right, (left.width + SEPARATOR_PX, 0))
    out = io.BytesIO()
    canvas.save(out, "PNG")
    return out.getvalue()


@dataclass(frozen=True)
class VisionVerdict:
    """The vision model's judgement."""

    same: bool
    differences: list[str]


class VisionJudge:
    """Asks an Ollama vision model to compare two screenshots.

    Args:
        ollama_host: Ollama base URL.
        model: A vision-capable model name.
    """

    def __init__(self, ollama_host: str, model: str) -> None:
        """Store connection settings."""
        self.ollama_host = ollama_host.rstrip("/")
        self.model = model

    def compare(self, baseline_png: bytes, actual_png: bytes) -> VisionVerdict:
        """Return whether the model sees the two screenshots as visually the same (one side-by-side image)."""
        composite = base64.b64encode(side_by_side(baseline_png, actual_png)).decode()
        response = httpx.post(
            f"{self.ollama_host}/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
                "messages": [
                    {
                        "role": "user",
                        "content": PROMPT,
                        "images": [composite],
                    }
                ],
            },
            timeout=600,
        )
        response.raise_for_status()
        data = json.loads(response.json()["message"]["content"])
        return VisionVerdict(same=bool(data.get("same")), differences=list(data.get("differences", [])))
