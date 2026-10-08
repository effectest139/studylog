"""Pillow로 그리는 작은 도형 이미지.

CTk의 원형 테두리는 작은 크기에서 끊겨 보여서, 크게 그린 뒤 줄여 가장자리를 부드럽게 한다.
"""

from __future__ import annotations

from functools import lru_cache

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

_SUPER = 8   # 이 배율로 크게 그린 뒤
_KEEP = 3    # 이 배율까지만 줄여 둔다(Windows 배율 확대에도 선명하게)


@lru_cache(maxsize=None)
def color_swatch(color: str, selected: bool, used: bool, size: int = 40, inner: int = 30,
                 ring: int = 2, ring_color: str = "#111827", bg: str = "#FFFFFF") -> ctk.CTkImage:
    """색 선택 원: (선택 링) + 색 원 + (이미 쓰는 색이면 가운데 흰 점)."""
    s = _SUPER
    big = size * s
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if selected:
        draw.ellipse((0, 0, big - 1, big - 1), fill=ring_color)
        draw.ellipse((ring * s, ring * s, big - 1 - ring * s, big - 1 - ring * s), fill=bg)
    margin = (size - inner) / 2 * s
    draw.ellipse((margin, margin, big - 1 - margin, big - 1 - margin), fill=color)
    if used:
        r, c = 4 * s, big / 2
        draw.ellipse((c - r, c - r, c + r, c + r), fill="#FFFFFF")
    small = img.resize((size * _KEEP, size * _KEEP), Image.LANCZOS)
    return ctk.CTkImage(light_image=small, dark_image=small, size=(size, size))


@lru_cache(maxsize=None)
def dot_photo(color: str, px: int) -> ImageTk.PhotoImage:
    """tk.Label에 넣는 색 점(px는 배율을 적용한 실제 픽셀). 기록 목록처럼 많이 쓰는 곳용."""
    big = px * _SUPER
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, big - 1, big - 1), fill=color)
    return ImageTk.PhotoImage(img.resize((px, px), Image.LANCZOS))
