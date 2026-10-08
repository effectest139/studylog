"""경고 확인창(09-D, 04-D, 10-R 모양)과 단순 알림창."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .. import theme as t
from ..widgets.common import Badge, Button, label
from .base import ModalDialog


class ConfirmDialog(ModalDialog):
    """[!] 제목 / 빨간 안내 상자 / (추가 줄) / [취소][위험 버튼]. 버튼은 가로로 반씩.

    되돌릴 수 없는 동작용이라 Enter로는 확인되지 않는다(위험 버튼은 마우스로만). Esc는 취소.
    type_to_confirm을 주면 그 낱말을 정확히 입력해야 위험 버튼이 켜진다(데이터 초기화).
    """

    confirm_on_enter = False

    def __init__(self, parent, title: str, message: str, confirm_text: str,
                 on_confirm: Callable[[], None], rows: list[tuple[str, str]] | None = None,
                 note: str | None = None, icon: bool = True, width: int = 400,
                 type_to_confirm: str | None = None):
        super().__init__(parent, title, width)
        self._callback = on_confirm
        self._word = type_to_confirm
        self._entry: ctk.CTkEntry | None = None
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
            label(box, note, 13, color=t.MUTED, justify="left").pack(anchor="w", pady=(16, 0))

        if type_to_confirm:
            self._typing_box(box, type_to_confirm)

        buttons = ctk.CTkFrame(box, fg_color="transparent")
        buttons.pack(fill="x", pady=(20, 0))
        buttons.grid_columnconfigure((0, 1), weight=1, uniform="b")
        Button(buttons, "취소", kind="secondary", height=48, command=self.close).grid(
            row=0, column=0, sticky="ew", padx=(0, 5))
        self.default_button = Button(buttons, confirm_text, kind="danger", height=48,
                                     command=self.on_confirm)
        self.default_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        if type_to_confirm:
            self.default_button.set_enabled(False)
        self.show()

    def _typing_box(self, box, word: str) -> None:
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", pady=(16, 0))
        label(row, "계속하려면 ", 14, color=t.TEXT_SUB).pack(side="left")
        label(row, word, 14, bold=True, color=t.DANGER).pack(side="left")
        label(row, "라고 입력해 주세요", 14, color=t.TEXT_SUB).pack(side="left")
        self._var = ctk.StringVar()
        self._entry = ctk.CTkEntry(box, textvariable=self._var, height=44, corner_radius=t.R_CTRL,
                                   border_width=1, border_color=t.BORDER_STRONG, fg_color=t.SURFACE,
                                   text_color=t.TEXT, font=t.font(15))
        self._entry.pack(fill="x", pady=(8, 0))
        self._entry.bind("<FocusIn>", lambda e: self._entry.configure(border_width=2, border_color=t.PRIMARY))
        self._entry.bind("<FocusOut>", lambda e: self._entry.configure(border_width=1,
                                                                        border_color=t.BORDER_STRONG))
        self._var.trace_add("write", lambda *_: self.default_button.set_enabled(self._typed_ok()))

    def _typed_ok(self) -> bool:
        return self._word is None or self._var.get().strip() == self._word

    def initial_focus(self):
        return self._entry if self._entry is not None else self

    def on_confirm(self) -> None:
        if not self._typed_ok():
            return
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
