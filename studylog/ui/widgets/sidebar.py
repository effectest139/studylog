"""사이드바: 로고, 메뉴 4개, 아래쪽 프로필 버튼. 공부 중에는 잠근다."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .. import theme as t
from .common import Badge, Dot, bind_hover, bind_tree, elide, label, vline

MENU = (("home", "홈"), ("record", "기록"), ("analysis", "분석"), ("goal", "목표"))


class _MenuItem(ctk.CTkFrame):
    def __init__(self, master, text: str, on_click: Callable[[], None]):
        super().__init__(master, height=44, corner_radius=t.R_CTRL, fg_color=t.SURFACE)
        self.pack_propagate(False)
        self.active = False
        self.locked = False
        self._hover = False
        self._dot = Dot(self, t.GHOST, size=8)
        self._dot.pack(side="left", padx=(16, 12))
        self._text = label(self, text, 15)
        self._text.pack(side="left")
        bind_tree(self, "<Button-1>", lambda e: None if self.locked else on_click())
        bind_hover(self, lambda: self._set_hover(True), lambda: self._set_hover(False))

    def _set_hover(self, hover: bool) -> None:
        self._hover = hover
        self.paint()

    def paint(self) -> None:
        if self.locked:
            bg, fg, dot, bold = t.SURFACE, t.GHOST, t.BORDER, False
        elif self.active:
            bg, fg, dot, bold = t.PRIMARY, "#FFFFFF", "#FFFFFF", True
        else:
            bg = t.GRAY_100 if self._hover else t.SURFACE
            fg, dot, bold = t.MUTED, t.GHOST, False
        self.configure(fg_color=bg)
        self._dot.set_color(dot)
        self._text.configure(text_color=fg, font=t.font(15, bold))


class _ProfileButton(ctk.CTkFrame):
    NAME_MAX_PX = 78  # 이름이 길면 '…'으로 줄인다

    def __init__(self, master, name: str, on_click: Callable[[], None]):
        super().__init__(master, height=56, corner_radius=t.R_CTRL, border_width=1,
                         border_color=t.BORDER, fg_color=t.SURFACE)
        self.pack_propagate(False)
        self.locked = False
        self._hover = False
        self._avatar = Badge(self, "", 32, 16, t.PRIMARY, "#FFFFFF", 14)
        self._avatar.pack(side="left", padx=(12, 10))
        self._name = label(self, "", 15, bold=True)
        self._name.pack(side="left")
        self._settings = label(self, "설정", 12, color=t.MUTED)
        self._settings.pack(side="right", padx=(0, 12))
        self.set_name(name)
        bind_tree(self, "<Button-1>", lambda e: None if self.locked else on_click())
        bind_hover(self, lambda: self._set_hover(True), lambda: self._set_hover(False))

    def set_name(self, name: str) -> None:
        self._avatar.set(text=name[:1])
        self._name.configure(text=elide(t.font(15, True), name, self.NAME_MAX_PX))

    def _set_hover(self, hover: bool) -> None:
        self._hover = hover
        self.paint()

    def paint(self) -> None:
        if self.locked:
            self.configure(fg_color=t.BG, border_color=t.GRAY_100)
            self._avatar.set(bg=t.BORDER, fg=t.FAINT)
            self._name.configure(text_color=t.GHOST)
            self._settings.configure(text_color=t.BG)  # 잠기면 '설정' 글자를 감춘다
        else:
            self.configure(fg_color=t.GRAY_100 if self._hover else t.SURFACE, border_color=t.BORDER)
            self._avatar.set(bg=t.PRIMARY, fg="#FFFFFF")
            self._name.configure(text_color=t.TEXT)
            self._settings.configure(text_color=t.MUTED)


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, user_name: str, on_navigate: Callable[[str], None],
                 on_profile: Callable[[], None]):
        super().__init__(master, width=t.SIDEBAR_W, corner_radius=0, fg_color=t.SURFACE)
        self.pack_propagate(False)
        # 오른쪽 1px 테두리
        vline(self).pack(side="right", fill="y")
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=24)

        logo = ctk.CTkFrame(inner, fg_color="transparent")
        logo.pack(fill="x", padx=8, pady=(0, 24))
        Badge(logo, "S", 32, 8, t.PRIMARY, "#FFFFFF", 16).pack(side="left")
        label(logo, "StudyLog", 18, bold=True).pack(side="left", padx=(10, 0))

        self._items: dict[str, _MenuItem] = {}
        for key, text in MENU:
            item = _MenuItem(inner, text, lambda k=key: on_navigate(k))
            item.pack(fill="x", pady=(0, 8))
            self._items[key] = item

        self._profile = _ProfileButton(inner, user_name, on_profile)
        self._profile.pack(side="bottom", fill="x")
        self.set_active("home")

    def set_active(self, key: str) -> None:
        for k, item in self._items.items():
            item.active = k == key
            item.paint()

    def set_locked(self, locked: bool) -> None:
        """공부 중에는 메뉴와 프로필 버튼을 누를 수 없게 한다."""
        for item in (*self._items.values(), self._profile):
            item.locked = locked
            item.paint()

    def set_user_name(self, name: str) -> None:
        self._profile.set_name(name)
