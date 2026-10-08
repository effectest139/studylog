"""기록(05): 날짜별 공부 기록과 날짜별 합계, 기록마다 삭제. 기록이 없으면 05-E 빈 화면."""

from __future__ import annotations

import tkinter as tk
from datetime import date
from typing import Callable

import customtkinter as ctk

from ...core import fmt, stats
from ...core.models import Session
from .. import images
from .. import theme as t
from ..dialogs.confirm import ConfirmDialog
from ..widgets.common import Button, card, elide, label, widget_scaling
from ..widgets.drag_scroll import DRAG_START_PX, DragScroll
from .base import Page

DAYS_PER_LOAD = 14  # 처음엔 최근 14일만 그리고 '더 보기'로 늘린다(위젯이 많으면 느려짐)
SUBJECT_W = 80

HEAD_H = 40
ROW_H = 44


class DayBlock(tk.Canvas):
    """날짜 하나(머리줄 + 기록 줄들)를 캔버스 하나에 그린다.

    줄마다 CTk 위젯(프레임·라벨·점·버튼)을 만들면 14일치에 위젯이 500개 가까이 되고,
    위젯 하나하나가 따로 그려져 기록 화면을 여는 데 1.7초쯤 걸렸다. 캔버스의 글자·도형은 가벼워서 빠르다.
    캔버스는 배율을 자동으로 곱하지 않으므로 크기·글꼴은 _px()로 바꿔 쓴다.
    """

    def __init__(self, master, scale: float, day: date, items: list[Session], total: int,
                 today: date, subjects: dict, on_delete):
        self._scale = scale
        px = self._px
        super().__init__(master, height=px(HEAD_H + len(items) * (ROW_H + 1)), bg=t.SURFACE,
                         bd=0, highlightthickness=0)
        self._actions: dict[str, Callable[[], None]] = {}  # '삭제' 태그 → 실행할 일
        self._right: list[tuple[int, int, str]] = []  # (항목, 오른쪽 끝에서 떨어진 거리, 'x'|'line')
        self._hover_tag: str | None = None
        self._pressed: tuple[str, int, int] | None = None  # 누른 '삭제'의 (태그, 화면 x, y)

        mid = px(HEAD_H) / 2
        self._text(0, mid, fmt.date_short(day, today), 15, bold=True)
        # '합계 1시간 25분' — 숫자만 굵은 주색
        amount = self._text(0, mid, fmt.duration(total), 14, bold=True, color=t.PRIMARY, right=0)
        self._text(0, mid, "합계 ", 14, color=t.MUTED, right=self._width_of(amount))

        y = px(HEAD_H)
        for i, session in enumerate(items):
            line = self.create_line(0, y, 0, y, fill=t.DIVIDER)
            self._right.append((line, 0, "line"))
            self._row(y + 1, session, subjects[session.subject_id], f"del{i}", on_delete)
            y += px(ROW_H + 1)
        self.bind("<Configure>", self._place_right)
        self.bind("<B1-Motion>", self._cancel_if_moved, add="+")
        self.bind("<ButtonRelease-1>", self._release, add="+")

    def _px(self, value: float) -> int:
        return round(value * self._scale)

    def _text(self, x: float, y: float, text: str, size: int, bold: bool = False, color: str = t.TEXT,
              right: int | None = None, tags: str = "") -> int:
        """right를 주면 오른쪽 끝에서 right만큼 떨어진 곳에 오른쪽 정렬로 놓는다."""
        item = self.create_text(x, y, text=text, fill=color, anchor="e" if right is not None else "w",
                                font=t.font(size, bold).create_scaled_tuple(self._scale), tags=tags)
        if right is not None:
            self._right.append((item, right, "x"))
        return item

    def _width_of(self, item: int) -> int:
        x1, _, x2, _ = self.bbox(item)
        return x2 - x1

    def _row(self, top: int, session: Session, subject, tag: str, on_delete) -> None:
        px = self._px
        mid = top + px(ROW_H) / 2
        self.create_image(px(5), mid, image=images.dot_photo(subject.color, px(10)))
        name = elide(t.font(15), subject.name, SUBJECT_W - 4)
        self._text(px(22), mid, name, 15)
        self._text(px(22 + SUBJECT_W + 12), mid, fmt.time_range(session.start, session.end), 14,
                   color=t.MUTED)

        # '삭제': 올리면 빨간 글자 + 연한 빨강 배경
        del_w, del_h = px(44), px(28)
        bg = self.create_rectangle(0, mid - del_h / 2, 0, mid + del_h / 2, fill=t.SURFACE, outline="",
                                   tags=(tag, tag + "bg"))
        self._right.append((bg, del_w, "rect"))
        word = self._text(0, mid, "삭제", 13, color=t.FAINT, right=del_w // 2, tags=tag)
        self.itemconfigure(word, anchor="center", tags=(tag, tag + "fg"))
        self._text(0, mid, fmt.duration(session.study_seconds), 15, bold=True, right=del_w + px(12))

        self.tag_bind(tag, "<Enter>", lambda e: self._set_hover(tag))
        self.tag_bind(tag, "<Leave>", lambda e: self._set_hover(None))
        # 손을 뗄 때 실행한다: 누른 채 밖으로 나가거나 조금 이상 움직였으면 취소
        self.tag_bind(tag, "<ButtonPress-1>", lambda e: setattr(self, "_pressed", (tag, e.x_root, e.y_root)))
        self._actions[tag] = lambda: on_delete(session, subject)

    def on_delete_button(self) -> bool:
        """마우스가 지금 '삭제' 위에 있나(끌기 스크롤을 시작하지 않는다)."""
        return self._hover_tag is not None

    def _cancel_if_moved(self, event) -> None:
        if self._pressed:
            _, x, y = self._pressed
            if max(abs(event.x_root - x), abs(event.y_root - y)) >= DRAG_START_PX * self._scale:
                self._pressed = None

    def _release(self, _event) -> None:
        pressed, self._pressed = self._pressed, None
        if pressed and pressed[0] == self._hover_tag:
            self._set_hover(None)
            self._actions[pressed[0]]()

    def _set_hover(self, tag: str | None) -> None:
        if self._hover_tag and self.winfo_exists():
            self.itemconfigure(self._hover_tag + "bg", fill=t.SURFACE)
            self.itemconfigure(self._hover_tag + "fg", fill=t.FAINT)
        self._hover_tag = tag
        if tag:
            self.itemconfigure(tag + "bg", fill=t.DANGER_SOFT)
            self.itemconfigure(tag + "fg", fill=t.DANGER)
        self.configure(cursor="hand2" if tag else "")

    def _place_right(self, event) -> None:
        """폭이 정해지거나 바뀌면 오른쪽 정렬 항목을 옮긴다."""
        w = event.width
        for item, offset, kind in self._right:
            coords = self.coords(item)
            if kind == "line":
                self.coords(item, 0, coords[1], w, coords[3])
            elif kind == "rect":
                self.coords(item, w - offset, coords[1], w, coords[3])
            else:
                self.coords(item, w - offset, coords[1])


class HistoryPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        self._box: ctk.CTkFrame | None = None
        self._scroll: ctk.CTkScrollableFrame | None = None
        self._days_shown = DAYS_PER_LOAD
        self._drawn_for: tuple | None = None  # 지금 화면을 그린 기준(데이터 변경 번호, 오늘 날짜)

    def _state(self) -> tuple:
        # 날짜가 바뀌면 '· 오늘' 표시가 달라지므로 오늘 날짜도 기준에 넣는다
        return self.app.store.revision, date.today()

    def refresh(self) -> None:
        """사이드바에서 들어올 때: 처음 14일부터 다시 보여 준다.

        기록이 그대로이고 '더 보기'도 누르지 않았으면 만들어 둔 화면을 맨 위로 올려 다시 쓴다.
        """
        if (self._box is not None and self._drawn_for == self._state()
                and self._days_shown == DAYS_PER_LOAD):
            self._set_scroll_pos(0.0)
            return
        self._days_shown = DAYS_PER_LOAD
        self._render()

    def _render(self, keep_scroll: bool = False) -> None:
        pos = self._scroll_pos() if keep_scroll else 0.0
        self._drawn_for = self._state()
        if self._box is not None:
            self._box.destroy()
        self._box = ctk.CTkFrame(self, fg_color="transparent")
        self._box.pack(fill="both", expand=True, padx=t.CONTENT_PAD, pady=t.CONTENT_PAD)

        groups = stats.sessions_by_day(self.app.store.sessions)
        shown = groups[:self._days_shown]
        self._header(self._box, shown)
        if not groups:
            self._empty(self._box)
            return
        self._list(self._box, shown, has_more=len(groups) > len(shown))
        if keep_scroll:
            self.after_idle(lambda: self._set_scroll_pos(pos))

    # --- 머리글 ---

    def _header(self, master, shown) -> None:
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x")
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left")
        label(left, "기록", 26, bold=True).pack(anchor="w")
        label(left, "날짜별 공부 기록", 14, color=t.MUTED).pack(anchor="w", pady=(6, 0))
        if shown:
            total = sum(day_total for _, _, day_total in shown)
            label(row, f"최근 {len(shown)}일 · {fmt.duration(total)}", 14, color=t.MUTED).pack(
                side="right", anchor="s")

    # --- 목록 ---

    def _list(self, master, shown, has_more: bool) -> None:
        box = card(master)
        box.pack(fill="both", expand=True, pady=(24, 0))
        self._scroll = ctk.CTkScrollableFrame(box, fg_color=t.SURFACE, corner_radius=0,
                                              scrollbar_button_color=t.BORDER,
                                              scrollbar_button_hover_color=t.BORDER_STRONG)
        self._scroll.pack(fill="both", expand=True, padx=(24, 8), pady=8)
        # 빈 곳을 누른 채 끌어도 스크롤된다. '삭제' 위에서 시작한 끌기는 무시(실수로 삭제되지 않게)
        drag = DragScroll(self._scroll, can_start=lambda e: not (
            isinstance(e.widget, DayBlock) and e.widget.on_delete_button()))
        drag.attach(self._scroll)
        drag.attach(self._scroll._parent_canvas)

        today = date.today()
        scale = widget_scaling(self)
        subjects = {s.id: s for s in self.app.store.subjects}
        for i, (day, items, total) in enumerate(shown):
            block = DayBlock(self._scroll, scale, day, items, total, today, subjects, self._confirm_delete)
            # 캔버스(tk 위젯)는 pack 여백에도 배율이 곱해지지 않는다
            block.pack(fill="x", padx=(0, round(16 * scale)),
                       pady=(round((4 if i == 0 else 12) * scale), round(12 * scale)))
            drag.attach(block)
        if has_more:
            Button(self._scroll, "더 보기", kind="secondary", height=40, size=14,
                   command=self._load_more).pack(fill="x", padx=(0, 16), pady=(12, 12))

    def _load_more(self) -> None:
        self._days_shown += DAYS_PER_LOAD
        self._render(keep_scroll=True)

    # --- 삭제 ---

    def _confirm_delete(self, session: Session, subject) -> None:
        when = f"{fmt.date_short(session.day)} {fmt.time_range(session.start, session.end)}"
        ConfirmDialog(self, "이 기록을 삭제할까요?",
                      f"{subject.name} · {fmt.duration(session.study_seconds)} ({when})\n"
                      "삭제하면 되돌릴 수 없어요",
                      "삭제", lambda: self._delete(session.id))

    def _delete(self, session_id: str) -> None:
        if self.app.run_safely(self.app.store.delete_session, session_id):
            self._render(keep_scroll=True)

    # --- 스크롤 위치 유지(삭제·더 보기 뒤 맨 위로 튀지 않게) ---

    def _scroll_pos(self) -> float:
        canvas = getattr(self._scroll, "_parent_canvas", None)
        return canvas.yview()[0] if canvas is not None and self._scroll.winfo_exists() else 0.0

    def _set_scroll_pos(self, pos: float) -> None:
        canvas = getattr(self._scroll, "_parent_canvas", None)
        if canvas is not None and self._scroll.winfo_exists():
            canvas.yview_moveto(pos)

    # --- 05-E 빈 화면 ---

    def _empty(self, master) -> None:
        box = card(master)
        box.pack(fill="both", expand=True, pady=(24, 0))
        center = ctk.CTkFrame(box, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")
        icon = ctk.CTkFrame(center, width=72, height=72, corner_radius=36, fg_color=t.PRIMARY_SOFT)
        icon.pack()
        ctk.CTkFrame(icon, width=28, height=32, corner_radius=4, border_width=3,
                     border_color="#A5B4FC", fg_color=t.PRIMARY_SOFT).place(relx=0.5, rely=0.5, anchor="center")
        label(center, "아직 공부 기록이 없어요", 20, bold=True).pack(pady=(16, 0))
        label(center, "홈에서 과목 카드를 누르면 공부가 시작돼요", 14, color=t.MUTED).pack(pady=(16, 0))
        Button(center, "홈으로 가기", width=160, height=52, size=16,
               command=lambda: self.app.screen.show_page("home")).pack(pady=(24, 0))
