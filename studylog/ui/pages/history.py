"""기록(05): 날짜별 공부 기록과 날짜별 합계, 기록마다 삭제. 기록이 없으면 05-E 빈 화면."""

from __future__ import annotations

from datetime import date

import customtkinter as ctk

from ...core import fmt, stats
from ...core.models import Session
from .. import theme as t
from ..dialogs.confirm import ConfirmDialog
from ..widgets.common import Button, Dot, card, elide, hline, label
from .base import Page

DAYS_PER_LOAD = 14  # 처음엔 최근 14일만 그리고 '더 보기'로 늘린다(위젯이 많으면 느려짐)
SUBJECT_W = 80


class HistoryPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        self._box: ctk.CTkFrame | None = None
        self._scroll: ctk.CTkScrollableFrame | None = None
        self._days_shown = DAYS_PER_LOAD

    def refresh(self) -> None:
        """사이드바에서 들어올 때: 처음 14일부터 다시 보여 준다."""
        self._days_shown = DAYS_PER_LOAD
        self._render()

    def _render(self, keep_scroll: bool = False) -> None:
        pos = self._scroll_pos() if keep_scroll else 0.0
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

        today = date.today()
        for i, (day, items, total) in enumerate(shown):
            self._day(self._scroll, day, items, total, today, first=i == 0)
        if has_more:
            Button(self._scroll, "더 보기", kind="secondary", height=40, size=14,
                   command=self._load_more).pack(fill="x", padx=(0, 16), pady=(12, 12))

    def _day(self, master, day: date, items: list[Session], total: int, today: date, first: bool) -> None:
        box = ctk.CTkFrame(master, fg_color="transparent")
        box.pack(fill="x", padx=(0, 16), pady=(4 if first else 12, 12))
        head = ctk.CTkFrame(box, fg_color="transparent", height=40)
        head.pack(fill="x")
        head.pack_propagate(False)
        label(head, fmt.date_short(day, today), 15, bold=True).pack(side="left")
        # '합계 1시간 25분' — 숫자만 굵은 주색
        label(head, fmt.duration(total), 14, bold=True, color=t.PRIMARY).pack(side="right")
        label(head, "합계 ", 14, color=t.MUTED).pack(side="right")

        subjects = {s.id: s for s in self.app.store.subjects}
        for session in items:
            hline(box, t.DIVIDER).pack(fill="x")
            self._item(box, session, subjects[session.subject_id])

    def _item(self, master, session: Session, subject) -> None:
        row = ctk.CTkFrame(master, fg_color="transparent", height=44)
        row.pack(fill="x")
        row.pack_propagate(False)
        Dot(row, subject.color, size=10).pack(side="left", padx=(0, 12))
        name_font = t.font(15)
        name_box = ctk.CTkFrame(row, fg_color="transparent", width=SUBJECT_W, height=44)
        name_box.pack(side="left")
        name_box.pack_propagate(False)
        label(name_box, elide(name_font, subject.name, SUBJECT_W - 4), 15).pack(side="left")
        label(row, fmt.time_range(session.start, session.end), 14, color=t.MUTED).pack(
            side="left", padx=(12, 0))

        delete = ctk.CTkButton(row, text="삭제", width=44, height=28, corner_radius=6, border_width=0,
                               fg_color="transparent", hover_color=t.DANGER_SOFT, text_color=t.FAINT,
                               font=t.font(13), command=lambda: self._confirm_delete(session, subject))
        delete.pack(side="right", padx=(12, 0))
        delete.bind("<Enter>", lambda e: delete.configure(text_color=t.DANGER), add="+")
        delete.bind("<Leave>", lambda e: delete.configure(text_color=t.FAINT), add="+")
        label(row, fmt.duration(session.study_seconds), 15, bold=True).pack(side="right")

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
        if canvas is not None:
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
