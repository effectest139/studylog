"""과목 카드(높이 88): 왼쪽 색 띠 + 과목 이름 + 오른쪽 위 ⋯ 버튼."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ...core import colors
from .. import theme as t
from .common import HoverGroup, bind_hover, bind_tree, elide, label, widget_scaling

CARD_H = 88
CARD_MIN_W = 150
_NAME_X = 30        # 이름 시작 위치
_NAME_RIGHT = 12    # 이름 오른쪽 여백(⋯ 버튼은 위쪽, '시작하기'는 아래쪽이라 이름과 겹치지 않음)


class SubjectCard(ctk.CTkFrame):
    """두 가지 모양이 있다.

    - on_click 없음(처음 등록 화면 00-2): ⋯ 버튼이 항상 보인다.
    - on_click 있음(홈 01-H): 카드를 누르면 공부 시작. 마우스를 올렸을 때만 연한 배경,
      2px 과목색 테두리, '시작하기 →', ⋯ 버튼이 보인다.
    """

    def __init__(self, master, name: str, color: str,
                 on_menu: Callable[[], None] | None = None,
                 on_click: Callable[[], None] | None = None,
                 hover_group: HoverGroup | None = None):
        super().__init__(master, width=CARD_MIN_W, height=CARD_H, fg_color=t.SURFACE, border_width=1,
                         border_color=t.BORDER, corner_radius=t.R_CARD)
        self._full_name = name
        self._color = color
        self._tint = colors.tint(color)
        self._dark = colors.dark(color)
        self._name_font = t.font(16, bold=True)
        self._hoverable = on_click is not None

        # 둥근 모서리 밖으로 삐져나오지 않게 띠를 안쪽에 둥근 막대로 둔다(계획 5번)
        self._stripe = ctk.CTkFrame(self, width=6, height=CARD_H - 28, corner_radius=3, fg_color=color)
        self._stripe.place(x=12, rely=0.5, anchor="w")

        self._name = label(self, name, 16, bold=True)
        self._name.place(x=_NAME_X, rely=0.5, anchor="w")

        self._menu = None
        if on_menu:
            self._menu = ctk.CTkButton(self, text="⋯", width=26, height=26, corner_radius=6,
                                       font=t.font(13, True), command=on_menu)
        self._start = label(self, "시작하기 →", 12, bold=True, color=self._dark) if self._hoverable else None

        if self._hoverable:
            bind_tree(self, "<Button-1>", lambda e: on_click(), skip=[self._menu] if self._menu else [])
            bind_hover(self, lambda: self._paint(True), lambda: self._paint(False), hover_group)
        self._paint(False)
        self.bind("<Configure>", self._fit_name)

    def _paint(self, hover: bool) -> None:
        if not self._hoverable:
            # 처음 등록 화면: 항상 같은 모양
            if self._menu:
                self._menu.configure(fg_color=t.GRAY_100, hover_color=t.BORDER, text_color=t.MUTED,
                                     border_width=0)
                self._menu.place(relx=1.0, x=-8, y=8, anchor="ne")
            return

        if hover:
            self.configure(fg_color=self._tint, border_width=2, border_color=self._color)
            self._start.place(relx=1.0, rely=1.0, x=-11, y=-9, anchor="se")
            if self._menu:
                self._menu.configure(fg_color=t.SURFACE, hover_color=self._tint, text_color=self._dark,
                                     border_width=1, border_color=self._color)
                self._menu.place(relx=1.0, x=-7, y=7, anchor="ne")
        else:
            self.configure(fg_color=t.SURFACE, border_width=1, border_color=t.BORDER)
            self._start.place_forget()
            if self._menu:
                self._menu.place_forget()

    def _fit_name(self, event) -> None:
        avail = event.width / widget_scaling(self) - _NAME_X - _NAME_RIGHT
        self._name.configure(text=elide(self._name_font, self._full_name, avail))


class AddSlot(ctk.CTkFrame):
    """'+ 과목 추가' 칸."""

    def __init__(self, master, on_click: Callable[[], None], height: int = CARD_H,
                 hover_group: HoverGroup | None = None):
        super().__init__(master, width=CARD_MIN_W, height=height, fg_color=t.BG, border_width=1,
                         border_color=t.BORDER_STRONG, corner_radius=t.R_CARD)
        self._text = label(self, "+ 과목 추가", 15, color=t.FAINT)
        self._text.place(relx=0.5, rely=0.5, anchor="center")
        bind_tree(self, "<Button-1>", lambda e: on_click())
        bind_hover(self, lambda: self._paint(True), lambda: self._paint(False), hover_group)

    def _paint(self, hover: bool) -> None:
        self.configure(fg_color=t.GRAY_100 if hover else t.BG)
        self._text.configure(text_color=t.MUTED if hover else t.FAINT)
