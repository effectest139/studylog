"""프로필창(10): 이름 수정 + 맨 아래 작은 빨간 글씨 '데이터 초기화'."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ...core.store import check_name
from .. import theme as t
from ..widgets.common import Badge, Button, bind_hover, hline, label
from ..widgets.name_entry import NameEntry
from .base import ModalDialog


class ProfileDialog(ModalDialog):
    """on_save(name): 저장을 누르면. on_reset(): '데이터 초기화'를 누르면(이 창을 닫은 뒤 불린다)."""

    def __init__(self, parent, name: str, on_save: Callable[[str], None], on_reset: Callable[[], None]):
        super().__init__(parent, "프로필", 400)
        self._on_save = on_save
        self._on_reset = on_reset

        top = ctk.CTkFrame(self.body, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=24)
        self._avatar = Badge(top, name[:1], 64, 32, t.PRIMARY, "#FFFFFF", 24)
        self._avatar.pack()
        self.name_entry = NameEntry(top, "이름", "1~10자 · 홈 인사말과 사이드바에 표시돼요", value=name,
                                    validator=check_name, on_change=self._changed)
        self.name_entry.pack(fill="x", pady=(20, 0))

        bar = ctk.CTkFrame(self.body, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(0, 20))
        self.default_button = Button(bar, "저장", width=100, command=self.on_confirm)
        self.default_button.pack(side="right")
        Button(bar, "취소", kind="secondary", width=100, command=self.close).pack(side="right", padx=(0, 10))

        hline(self.body).pack(fill="x")
        reset = label(self.body, "데이터 초기화", 13, color=t.DANGER, cursor="hand2")
        reset.pack(anchor="w", padx=24, pady=14)
        reset.bind("<Button-1>", lambda e: self._reset())
        bind_hover(reset, lambda: reset.configure(text_color=t.DANGER_HOVER, font=t.font(13, True)),
                   lambda: reset.configure(text_color=t.DANGER, font=t.font(13)))
        self._changed()
        self.show()

    def initial_focus(self):
        return self.name_entry

    def _changed(self) -> None:
        self._avatar.set(text=self.name_entry.value[:1])
        if self.default_button is not None:
            self.default_button.set_enabled(self.name_entry.valid)

    def on_confirm(self) -> None:
        if not self.name_entry.valid:
            return
        name = self.name_entry.value
        self.close()
        self._on_save(name)

    def _reset(self) -> None:
        self.close()
        self._on_reset()
