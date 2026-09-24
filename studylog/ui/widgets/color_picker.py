"""12색 원형 선택: 고른 색은 검은 링, 다른 과목이 쓰는 색은 흰 점."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ...core.colors import PALETTE
from .. import theme as t
from .common import Dot, bind_tree


class ColorPicker(ctk.CTkFrame):
    COLUMNS = 6

    def __init__(self, master, selected: str, used: list[str],
                 on_change: Callable[[str], None] | None = None):
        super().__init__(master, fg_color="transparent")
        self.selected = selected.upper()
        self._on_change = on_change
        used_set = {u.upper() for u in used}
        self._rings: dict[str, ctk.CTkFrame] = {}

        for i, color in enumerate(PALETTE):
            ring = ctk.CTkFrame(self, width=40, height=40, corner_radius=20, border_width=2,
                                fg_color=t.SURFACE, border_color=t.SURFACE)
            ring.grid(row=i // self.COLUMNS, column=i % self.COLUMNS,
                      padx=(0, 18 if i % self.COLUMNS < self.COLUMNS - 1 else 0), pady=(0, 10))
            swatch = ctk.CTkFrame(ring, width=30, height=30, corner_radius=15, fg_color=color)
            swatch.place(relx=0.5, rely=0.5, anchor="center")
            if color in used_set:
                Dot(swatch, "#FFFFFF", size=8).place(relx=0.5, rely=0.5, anchor="center")
            bind_tree(ring, "<Button-1>", lambda e, c=color: self.select(c))
            self._rings[color] = ring
        self._paint()

    def select(self, color: str) -> None:
        self.selected = color
        self._paint()
        if self._on_change:
            self._on_change(color)

    def _paint(self) -> None:
        for color, ring in self._rings.items():
            ring.configure(border_color=t.TEXT if color == self.selected else t.SURFACE)
