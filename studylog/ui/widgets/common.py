"""여러 화면에서 같이 쓰는 작은 위젯과 도우미."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Iterable

import customtkinter as ctk

from .. import theme as t


# --- 이벤트 도우미 ---

def _ctk_tree(widget) -> Iterable:
    """widget과 그 아래 CTk 위젯들. CTk 위젯 안쪽의 tk 위젯(캔버스 등)은 빼고 돌려준다.

    CTk 위젯의 bind()는 안쪽 tk 위젯에도 알아서 연결하므로, 안쪽까지 내려가면 두 번 연결된다.
    """
    yield widget
    for child in widget.winfo_children():
        if isinstance(child, ctk.CTkBaseClass):
            yield from _ctk_tree(child)


def bind_tree(widget, sequence: str, func: Callable, skip: Iterable = ()) -> None:
    """widget과 그 안의 모든 요소에 같은 이벤트를 연결한다(skip과 그 자식은 제외)."""
    skip = tuple(skip)
    for w in _ctk_tree(widget):
        if any(w is s or str(w).startswith(str(s) + ".") for s in skip):
            continue
        w.bind(sequence, func, add="+")


def pointer_inside(widget) -> bool:
    x, y = widget.winfo_pointerxy()
    under = widget.winfo_containing(x, y)
    return under is not None and (under is widget or str(under).startswith(str(widget) + "."))


def bind_hover(widget, on_enter: Callable[[], None], on_leave: Callable[[], None]) -> None:
    """카드 안 어느 요소 위에 있어도 '올라가 있음'으로 본다.

    자식 위젯으로 들어갈 때도 부모에서 <Leave>가 나므로, 그때 포인터가 실제로
    바깥에 있을 때만 on_leave를 부른다. 그래서 요소 사이를 움직여도 깜빡이지 않는다.
    """
    state = {"inside": False}

    def enter(_event=None):
        if not state["inside"]:
            state["inside"] = True
            on_enter()

    def leave(_event=None):
        if pointer_inside(widget):
            return
        if state["inside"]:
            state["inside"] = False
            on_leave()

    bind_tree(widget, "<Enter>", enter)
    bind_tree(widget, "<Leave>", leave)


def widget_scaling(widget) -> float:
    return ctk.ScalingTracker.get_widget_scaling(widget)


def elide(font: ctk.CTkFont, text: str, max_px: float) -> str:
    """max_px(배율 적용 전 px)에 들어가도록 뒤를 잘라 '…'을 붙인다."""
    if max_px <= 0 or font.measure(text) <= max_px:
        return text
    while text and font.measure(text + "…") > max_px:
        text = text[:-1]
    return text + "…"


# --- 위젯 ---

def label(master, text: str = "", size: int = 14, bold: bool = False,
          color: str = t.TEXT, **kwargs) -> ctk.CTkLabel:
    return ctk.CTkLabel(master, text=text, font=t.font(size, bold), text_color=color,
                        height=0, fg_color="transparent", **kwargs)


def card(master, **kwargs) -> ctk.CTkFrame:
    opts = dict(fg_color=t.SURFACE, border_width=1, border_color=t.BORDER, corner_radius=t.R_CARD)
    opts.update(kwargs)
    return ctk.CTkFrame(master, **opts)


def hline(master, color: str = t.BORDER) -> tk.Frame:
    # CTkFrame은 1px 높이를 제대로 그리지 못해 tk 기본 Frame을 쓴다
    return tk.Frame(master, height=1, bg=color, bd=0, highlightthickness=0)


def vline(master, color: str = t.BORDER) -> tk.Frame:
    return tk.Frame(master, width=1, bg=color, bd=0, highlightthickness=0)


class Badge(ctk.CTkFrame):
    """가운데 글자가 있는 정사각형/원(로고 S, 프로필 첫 글자, ! 아이콘).

    CTkLabel에 글자를 넣으면 모서리 반지름만큼 좌우 여백이 붙어 원이 타원이 되므로
    도형(Frame)과 글자(Label)를 따로 둔다.
    """

    def __init__(self, master, text: str, size: int, radius: int, bg: str, fg: str,
                 font_size: int, bold: bool = True):
        super().__init__(master, width=size, height=size, corner_radius=radius, fg_color=bg)
        self._label = label(self, text, font_size, bold=bold, color=fg)
        self._label.place(relx=0.5, rely=0.5, anchor="center")

    def set(self, text: str | None = None, bg: str | None = None, fg: str | None = None) -> None:
        if bg is not None:
            self.configure(fg_color=bg)
        if text is not None:
            self._label.configure(text=text)
        if fg is not None:
            self._label.configure(text_color=fg)


_BUTTON_STYLES = {
    "primary": dict(fg_color=t.PRIMARY, hover_color=t.PRIMARY_HOVER, text_color="#FFFFFF",
                    border_width=0, bold=True),
    "secondary": dict(fg_color=t.SURFACE, hover_color=t.GRAY_100, text_color=t.TEXT,
                      border_width=1, border_color=t.BORDER, bold=False),
    "danger": dict(fg_color=t.DANGER, hover_color=t.DANGER_HOVER, text_color="#FFFFFF",
                   border_width=0, bold=True),
    "ghost": dict(fg_color="transparent", hover_color=t.GRAY_100, text_color=t.MUTED,
                  border_width=0, bold=False),
}


class Button(ctk.CTkButton):
    """디자인의 버튼 종류(primary/secondary/danger/ghost). 비활성이면 회색 배경."""

    def __init__(self, master, text: str, kind: str = "primary", width: int = 100,
                 height: int = 44, size: int = 15, command: Callable | None = None, **kwargs):
        style = dict(_BUTTON_STYLES[kind])
        bold = style.pop("bold")
        self._enabled_colors = (style["fg_color"], style["hover_color"])
        super().__init__(master, text=text, width=width, height=height, corner_radius=t.R_CTRL,
                         font=t.font(size, bold), command=command,
                         text_color_disabled=t.DISABLED_TEXT, **style, **kwargs)

    def set_enabled(self, enabled: bool) -> None:
        if enabled:
            fg, hover = self._enabled_colors
            self.configure(state="normal", fg_color=fg, hover_color=hover)
        else:
            self.configure(state="disabled", fg_color=t.DISABLED_BG, hover_color=t.DISABLED_BG)

    @property
    def enabled(self) -> bool:
        return self.cget("state") == "normal"


class Dot(ctk.CTkFrame):
    """작은 동그라미(과목 색, 메뉴 표시)."""

    def __init__(self, master, color: str, size: int = 10, radius: int | None = None):
        super().__init__(master, width=size, height=size, fg_color=color,
                         corner_radius=size // 2 if radius is None else radius)

    def set_color(self, color: str) -> None:
        self.configure(fg_color=color)
