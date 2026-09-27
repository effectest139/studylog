"""12색 원형 선택: 고른 색은 검은 링, 다른 과목이 쓰는 색은 흰 점."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ...core.colors import PALETTE
from .. import theme as t
from ..images import color_swatch


class ColorPicker(ctk.CTkFrame):
    COLUMNS = 6

    def __init__(self, master, selected: str, used: list[str],
                 on_change: Callable[[str], None] | None = None):
        super().__init__(master, fg_color="transparent")
        self.selected = selected.upper()
        self._on_change = on_change
        self._used = {u.upper() for u in used}
        self._cells: dict[str, ctk.CTkLabel] = {}

        for i, color in enumerate(PALETTE):
            cell = ctk.CTkLabel(self, text="", width=40, height=40, fg_color="transparent")
            cell.grid(row=i // self.COLUMNS, column=i % self.COLUMNS,
                      padx=(0, 18 if i % self.COLUMNS < self.COLUMNS - 1 else 0), pady=(0, 10))
            cell.bind("<Button-1>", lambda e, c=color: self.select(c))
            self._cells[color] = cell
        self._paint()

    def select(self, color: str) -> None:
        self.selected = color
        self._paint()
        if self._on_change:
            self._on_change(color)

    def _paint(self) -> None:
        for color, cell in self._cells.items():
            cell.configure(image=color_swatch(color, color == self.selected, color in self._used,
                                              bg=t.SURFACE))
