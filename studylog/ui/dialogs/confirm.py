"""경고 확인창(09-D, 04-D, 10-R 모양)과 단순 알림창."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .. import theme as t
from ..widgets.common import Badge, Button, label
from .base import ModalDialog


class ConfirmDialog(ModalDialog):
    """[!] 제목 / 빨간 안내 상자 / (추가 줄) / [취소][위험 버튼]. 버튼은 가로로 반씩."""

    def __init__(self, parent, title: str, message: str, confirm_text: str,
                 on_confirm: Callable[[], None], rows: list[tuple[str, str]] | None = None,
                 note: str | None = None, icon: bool = True, width: int = 400):
        super().__init__(parent, title, width)
        self._callback = on_confirm
        box = ctk.CTkFrame(self.body, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=28, pady=28)

        if icon:
            Badge(box, "!", 48, 24, t.DANGER_ICON_BG, t.DANGER, 24).pack(anchor="w", pady=(0, 16))
        label(box, title, 20, bold=True, wraplength=width - 56, justify="left").pack(anchor="w")
        ctk.CTkLabel(box, text=message, fg_color=t.DANGER_SOFT, text_color=t.DANGER_TEXT,
                     corner_radius=t.R_CTRL, font=t.font(14), anchor="w", justify="left",
                     wraplength=width - 56 - 28, height=0).pack(fill="x", pady=(16, 0), ipadx=14, ipady=12)

        for key, value in rows or []:
            row = ctk.CTkFrame(box, fg_color="transparent")
            row.pack(fill="x", pady=(8, 0))
            label(row, key, 14, color=t.MUTED).pack(side="left")
            label(row, value, 14, bold=True).pack(side="right")
        if note:
            label(box, note, 13, color=t.MUTED).pack(anchor="w", pady=(16, 0))

        buttons = ctk.CTkFrame(box, fg_color="transparent")
        buttons.pack(fill="x", pady=(20, 0))
        buttons.grid_columnconfigure((0, 1), weight=1, uniform="b")
        Button(buttons, "취소", kind="secondary", height=48, command=self.close).grid(
            row=0, column=0, sticky="ew", padx=(0, 5))
        self.default_button = Button(buttons, confirm_text, kind="danger", height=48,
                                     command=self.on_confirm)
        self.default_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.show()

    def on_confirm(self) -> None:
        self.close()
        self._callback()


class AlertDialog(ModalDialog):
    """제목 + 본문 + [확인] 하나."""

    def __init__(self, parent, title: str, message: str, width: int = 400):
        super().__init__(parent, title, width)
        box = ctk.CTkFrame(self.body, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=28, pady=28)
        label(box, title, 20, bold=True).pack(anchor="w")
        label(box, message, 14, color=t.MUTED, wraplength=width - 56, justify="left").pack(
            anchor="w", pady=(12, 0))
        self.default_button = Button(box, "확인", height=48, command=self.close)
        self.default_button.pack(fill="x", pady=(20, 0))
        self.show()

    def on_confirm(self) -> None:
        self.close()
