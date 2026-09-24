"""1~10자 이름 입력칸: 제목 + 입력칸 + 안내/오류 문구 + 글자 수."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ...core.store import NAME_MAX_LEN
from .. import theme as t
from .common import label


class NameEntry(ctk.CTkFrame):
    """validator(text)는 오류 문구나 None을 돌려준다. 빈 칸일 때는 오류를 빨갛게 보이지 않는다."""

    def __init__(self, master, title: str, hint: str, value: str = "",
                 validator: Callable[[str], str | None] | None = None,
                 on_change: Callable[[], None] | None = None,
                 height: int = 44, size: int = 15, show_count: bool = False):
        super().__init__(master, fg_color="transparent")
        self._validator = validator
        self._on_change = on_change
        self._hint = hint
        self._show_count = show_count
        self._focused = False

        label(self, title, 14, bold=True).pack(anchor="w")

        self.var = ctk.StringVar(value=value[:NAME_MAX_LEN])
        self.entry = ctk.CTkEntry(
            self, textvariable=self.var, height=height, corner_radius=t.R_CTRL,
            border_width=1, border_color=t.BORDER_STRONG, fg_color=t.SURFACE,
            text_color=t.TEXT, font=t.font(size))
        self.entry.pack(fill="x", pady=(8, 8))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x")
        self._msg = label(bottom, hint, 12, color=t.MUTED)
        self._msg.pack(side="left")
        self._count = label(bottom, "", 12, color=t.MUTED)
        if show_count:
            self._count.pack(side="right")

        self.entry.bind("<FocusIn>", lambda e: self._set_focus(True))
        self.entry.bind("<FocusOut>", lambda e: self._set_focus(False))
        self.var.trace_add("write", self._changed)
        self._refresh()

    @property
    def value(self) -> str:
        return self.var.get().strip()

    @property
    def error(self) -> str | None:
        if not self.value:
            return "empty"
        return self._validator(self.var.get()) if self._validator else None

    @property
    def valid(self) -> bool:
        return self.error is None

    def focus(self) -> None:
        self.entry.focus_set()
        self.entry.icursor("end")

    def _set_focus(self, focused: bool) -> None:
        self._focused = focused
        self._refresh()

    def _changed(self, *_):
        text = self.var.get()
        if len(text) > NAME_MAX_LEN:
            self.var.set(text[:NAME_MAX_LEN])  # 다시 _changed가 불린다
            return
        self._refresh()
        if self._on_change:
            self._on_change()

    def _refresh(self) -> None:
        err = self.error
        shown = err if err and err != "empty" else None
        if shown:
            self.entry.configure(border_width=2, border_color=t.DANGER)
            self._msg.configure(text=shown, text_color=t.DANGER, font=t.font(12, True))
        else:
            self.entry.configure(border_width=2 if self._focused else 1,
                                 border_color=t.PRIMARY if self._focused else t.BORDER_STRONG)
            self._msg.configure(text=self._hint, text_color=t.MUTED, font=t.font(12))
        if self._show_count:
            self._count.configure(text=f"{len(self.var.get())}/{NAME_MAX_LEN}")
