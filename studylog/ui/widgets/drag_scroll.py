"""스크롤 영역의 빈 곳을 누른 채로 끌어서 스크롤하기(마우스 휠과 함께 쓴다)."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .common import widget_scaling

DRAG_START_PX = 6  # 이만큼(배율 적용 전 px) 움직여야 끌기로 본다. 그 전에는 클릭


class DragScroll:
    """attach()한 위젯 위에서 시작한 끌기로 scrollable을 위아래로 움직인다.

    can_start(event)가 False면 그 누름에서는 끌기를 시작하지 않는다(삭제 버튼 위 등).
    """

    def __init__(self, scrollable: ctk.CTkScrollableFrame,
                 can_start: Callable[[object], bool] = lambda e: True):
        self._frame = scrollable
        self._canvas = scrollable._parent_canvas  # CTkScrollableFrame 안의 실제 스크롤 캔버스
        self._can_start = can_start
        self._start: tuple[int, float] | None = None  # (누른 화면 y, 그때의 맨 위 위치 0~1)
        self.dragging = False

    def attach(self, widget) -> None:
        widget.bind("<ButtonPress-1>", self._press, add="+")
        widget.bind("<B1-Motion>", self._motion, add="+")
        widget.bind("<ButtonRelease-1>", self._release, add="+")

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
