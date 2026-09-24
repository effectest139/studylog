"""과목 카드(높이 88): 왼쪽 색 띠 + 과목 이름 + 오른쪽 위 ⋯ 버튼."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .. import theme as t
from .common import bind_hover, bind_tree, elide, label, widget_scaling

CARD_H = 88
CARD_MIN_W = 150
_NAME_X = 30        # 이름 시작 위치
_MENU_SPACE = 40    # 오른쪽 ⋯ 버튼 자리


class SubjectCard(ctk.CTkFrame):
    """on_menu: ⋯ 버튼을 누르면. on_click: 카드를 누르면(홈에서 공부 시작, 3단계)."""

    def __init__(self, master, name: str, color: str,
                 on_menu: Callable[[], None] | None = None,
                 on_click: Callable[[], None] | None = None):
        super().__init__(master, width=CARD_MIN_W, height=CARD_H, fg_color=t.SURFACE, border_width=1,
                         border_color=t.BORDER, corner_radius=t.R_CARD)
        self._full_name = name
        self._name_font = t.font(16, bold=True)

        # 둥근 모서리 밖으로 삐져나오지 않게 띠를 안쪽에 둥근 막대로 둔다(계획 5번)
        self._stripe = ctk.CTkFrame(self, width=6, height=CARD_H - 28, corner_radius=3, fg_color=color)
        self._stripe.place(x=12, rely=0.5, anchor="w")

        self._name = label(self, name, 16, bold=True)
        self._name.place(x=_NAME_X, rely=0.5, anchor="w")

        self._menu = None
        if on_menu:
            self._menu = ctk.CTkButton(
                self, text="⋯", width=26, height=26, corner_radius=6, border_width=0,
                fg_color=t.GRAY_100, hover_color=t.BORDER, text_color=t.MUTED,
                font=t.font(13, True), command=on_menu)
            self._menu.place(relx=1.0, x=-8, y=8, anchor="ne")

        if on_click:
            bind_tree(self, "<Button-1>", lambda e: on_click(), skip=[self._menu] if self._menu else [])
            bind_hover(self, self._hover_on, self._hover_off)

        self.bind("<Configure>", self._fit_name)

    def _fit_name(self, event) -> None:
        avail = event.width / widget_scaling(self) - _NAME_X - _MENU_SPACE
        self._name.configure(text=elide(self._name_font, self._full_name, avail))

    # 홈 카드의 호버 모양은 3단계에서 채운다
    def _hover_on(self) -> None:
        pass

    def _hover_off(self) -> None:
        pass


class AddSlot(ctk.CTkFrame):
    """'+ 과목 추가' 칸."""

    def __init__(self, master, on_click: Callable[[], None], height: int = CARD_H):
        super().__init__(master, width=CARD_MIN_W, height=height, fg_color=t.BG, border_width=1,
                         border_color=t.BORDER_STRONG, corner_radius=t.R_CARD)
        self._text = label(self, "+ 과목 추가", 15, color=t.FAINT)
        self._text.place(relx=0.5, rely=0.5, anchor="center")
        bind_tree(self, "<Button-1>", lambda e: on_click())
        bind_hover(self, lambda: self._paint(True), lambda: self._paint(False))

    def _paint(self, hover: bool) -> None:
        self.configure(fg_color=t.GRAY_100 if hover else t.BG)
        self._text.configure(text_color=t.MUTED if hover else t.FAINT)
