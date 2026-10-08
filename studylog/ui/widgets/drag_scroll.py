"""스크롤 영역의 빈 곳을 누른 채로 끌어서 스크롤하기(마우스 휠과 함께 쓴다). 여러 화면에서 쓰는 공통 부품.

사용법:
    drag = DragScroll(scrollable_frame, area=카드, ignore=...)   # CTkScrollableFrame
    ... 안에 위젯을 다 넣은 뒤 ...
    drag.attach()                                     # 내용을 다시 그렸으면 다시 부른다

- area(기본: 스크롤 영역 자체) 안 어디서든 끌 수 있다. 목록을 감싼 카드를 주면 카드 여백에서도 된다.
- DRAG_START_PX 이상 움직여야 끌기로 본다. 그 전에는 평소처럼 클릭이다.
- 입력칸·버튼·스크롤바에서 시작한 누름은 끌기로 쓰지 않는다(글자 선택·버튼 누름이 우선).
- ignore(event)가 True인 누름도 끌기로 쓰지 않는다(기록의 '삭제'처럼 화면마다 다른 곳).
- 누를 수 있는 카드(make_clickable)는 손을 뗄 때 실행되고, 끌었으면 실행되지 않는다.
"""

from __future__ import annotations

import itertools
import tkinter as tk
from typing import Callable

import customtkinter as ctk

from .common import DRAG_START_PX, widget_scaling

# 여기서 시작한 누름은 끌기로 쓰지 않는다(CTk 위젯은 안쪽의 tk 위젯까지 포함)
INTERACTIVE = (ctk.CTkEntry, ctk.CTkTextbox, ctk.CTkButton, ctk.CTkScrollbar, ctk.CTkSlider,
               ctk.CTkCheckBox, ctk.CTkSwitch, ctk.CTkOptionMenu, ctk.CTkComboBox,
               tk.Entry, tk.Text, tk.Button, tk.Scrollbar)

_ids = itertools.count(1)


class DragScroll:
    def __init__(self, scrollable: ctk.CTkScrollableFrame, area=None,
                 ignore: Callable[[tk.Event], bool] | None = None):
        self._frame = scrollable
        self._canvas = scrollable._parent_canvas  # CTkScrollableFrame 안의 실제 스크롤 캔버스
        self._area = area if area is not None else scrollable._parent_frame
        self._ignore = ignore
        self._start: tuple[int, float] | None = None  # (누른 화면 y, 그때의 맨 위 위치 0~1)
        self.dragging = False
        # 위젯마다 bind하지 않고 이름표(bindtag) 하나에 한 번만 연결한다:
        # attach()를 여러 번 불러도 겹치지 않고, 위젯이 없어지면 함께 정리된다
        self._tag = f"DragScroll{next(_ids)}"
        root = scrollable._root()
        root.bind_class(self._tag, "<ButtonPress-1>", self._press)
        root.bind_class(self._tag, "<B1-Motion>", self._motion)
        root.bind_class(self._tag, "<ButtonRelease-1>", self._release)

    def attach(self) -> None:
        """area 안의 모든 위젯(나중에 넣은 것 포함)에 끌기를 연결한다."""
        for widget in self._tree(self._area):
            tags = widget.bindtags()
            if self._tag not in tags:
                widget.bindtags((self._tag, *tags))

    @staticmethod
    def _tree(widget):
        """widget과 그 아래 모든 위젯.

        CTkFrame.winfo_children()는 자기 바탕을 그리는 캔버스를 빼고 돌려줘서, 그걸 쓰면
        틀의 빈 바탕(글자·막대 사이)에서 끌기가 안 됐다. 그래서 tkinter 원래 것으로 모두 읽는다.
        """
        yield widget
        for child in tk.Misc.winfo_children(widget):
            yield from DragScroll._tree(child)

    # --- 판단 ---

    def _interactive(self, widget) -> bool:
        """widget이나 그 위(area 안쪽까지)가 입력칸·버튼·스크롤바 등인가."""
        w = widget
        while w is not None and w is not self._area:
            if isinstance(w, INTERACTIVE):
                return True
            w = w.master
        return False

    def _can_start(self, event) -> bool:
        if self._interactive(event.widget):
            return False
        return not (self._ignore and self._ignore(event))

    # --- 이벤트 ---

    def _press(self, event) -> None:
        self.dragging = False
        self._start = (event.y_root, self._canvas.yview()[0]) if self._can_start(event) else None

    def _motion(self, event) -> None:
        if self._start is None:
            return
        y0, top = self._start
        dy = event.y_root - y0
        if not self.dragging:
            if abs(dy) < DRAG_START_PX * widget_scaling(self._frame):
                return
            self.dragging = True
            self._canvas.configure(cursor="fleur")
        height = self._frame.winfo_height()  # 스크롤되는 내용 전체 높이
        if height > 0:
            self._canvas.yview_moveto(top - dy / height)

    def _release(self, _event) -> None:
        if self.dragging:
            self._canvas.configure(cursor="")
        self._start = None
