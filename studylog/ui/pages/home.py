"""홈(01): 인사말·연속일 / 오늘·이번 주·주간 목표 / 과목 카드와 과목 관리."""

from __future__ import annotations

from datetime import date, datetime

import customtkinter as ctk

from ...core import fmt, greeting, stats
from ...core.colors import next_unused
from ...core.models import Subject
from ...core.store import MAX_SUBJECTS
from .. import theme as t
from ..dialogs.confirm import ConfirmDialog
from ..dialogs.subject_dialog import SubjectDialog
from ..widgets.common import (Dot, HoverGroup, bind_hover, bind_tree, card, label, make_clickable,
                             widget_scaling)
from ..widgets.subject_card import AddSlot, SubjectCard
from .base import Page

COLUMNS = 5


class HomePage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        self._box: ctk.CTkFrame | None = None

    @property
    def store(self):
        return self.app.store

    def refresh(self) -> None:
        # 요소가 몇 개 안 돼서 매번 새로 그린다(날짜가 바뀐 경우도 자연스럽게 반영)
        if self._box is not None:
            self._box.destroy()
        self._box = ctk.CTkFrame(self, fg_color="transparent")
        self._box.pack(fill="both", expand=True, padx=t.CONTENT_PAD, pady=t.CONTENT_PAD)
        now = datetime.now()
        today = now.date()
        sessions = self.store.sessions
        self._header(self._box, now, sessions)
        self._summary(self._box, today, sessions)
        self._subjects(self._box)

    # --- 인사말(두 줄) + 날짜 + 연속일 ---

    def _header(self, master, now: datetime, sessions) -> None:
        today = now.date()
        streak = stats.streak(sessions, today)
        today_sec = stats.today_total(sessions, today)
        goal = stats.goal_progress(stats.week_total(sessions, today), self.store.weekly_goal_minutes)
        first, second = greeting.lines(self.store.name, now, today_sec, goal, self.app.greeting_picks)

        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x")
        # 배지를 먼저 놓아야 이름이 길 때 배지가 눌리지 않고 인사말이 줄을 바꾼다
        on = streak > 0
        pill = ctk.CTkFrame(row, height=36, corner_radius=18, fg_color=t.ACCENT if on else t.GRAY_100)
        pill.pack(side="right", anchor="n", padx=(24, 0))
        Dot(pill, "#FFFFFF" if on else t.GHOST, size=8).pack(side="left", padx=(16, 8), pady=14)
        label(pill, f"연속 {streak}일 공부 중" if on else "연속 0일", 14, bold=True,
              color="#FFFFFF" if on else t.MUTED).pack(side="left", padx=(0, 16))

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", anchor="n", fill="x", expand=True)
        title = label(left, first, 26, bold=True, justify="left")
        title.pack(anchor="w")
        status = label(left, second, 18, color=t.TEXT_SUB, justify="left")
        status.pack(anchor="w", pady=(6, 0))
        label(left, fmt.date_long(today), 13, color=t.MUTED).pack(anchor="w", pady=(8, 0))
        _wrap_to_width(left, title, status)

    # --- 요약 3칸 ---

    def _summary(self, master, today: date, sessions) -> None:
        grid = ctk.CTkFrame(master, fg_color="transparent")
        grid.pack(fill="x", pady=(24, 0))
        for col, weight in enumerate((2, 2, 3)):  # 디자인 1fr 1fr 1.5fr
            grid.grid_columnconfigure(col, weight=weight, uniform="summary")

        today_sec = stats.today_total(sessions, today)
        week_sec = stats.week_total(sessions, today)
        for col, (title, sec) in enumerate((("오늘 공부 시간", today_sec), ("이번 주 합계", week_sec))):
            box = card(grid)
            box.grid(row=0, column=col, sticky="nsew", padx=(0, 16))
            label(box, title, 14, color=t.MUTED).pack(anchor="w", padx=20, pady=(20, 0))
            label(box, fmt.duration(sec, empty="0시간 0분"), 28, bold=True,
                  color=t.TEXT if sec >= 60 else t.GHOST).pack(anchor="w", padx=20, pady=(6, 20))

        goal = card(grid)
        goal.grid(row=0, column=2, sticky="nsew")
        self._goal_card(goal, stats.goal_progress(week_sec, self.store.weekly_goal_minutes))

    def _goal_card(self, box, g: stats.GoalProgress) -> None:
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        label(top, "주간 목표", 14, color=t.MUTED).pack(side="left", anchor="s")
        link = None

        if not g.has_goal:
            link = label(top, "목표를 설정해 보세요 →", 14, bold=True, color=t.PRIMARY, cursor="hand2")
            link.pack(side="right", anchor="s")
            link.bind("<Button-1>", lambda e: self.app.open_goal_editor())
            bind_hover(link, lambda: link.configure(text_color=t.PRIMARY_HOVER),
                       lambda: link.configure(text_color=t.PRIMARY))
            sub = "주간 목표를 정하면 진행률이 보여요"
        else:
            # '72% · 8시간 40분 / 12시간' — 한 줄에 여러 스타일이라 라벨을 나눈다
            right = ctk.CTkFrame(top, fg_color="transparent")
            right.pack(side="right", anchor="s")
            label(right, f"{g.percent}%", 18, bold=True,
                  color=t.PRIMARY if g.done_seconds else t.TEXT).pack(side="left", anchor="s")
            done = fmt.duration(g.done_seconds, empty="0시간")
            label(right, f" · {done} / {fmt.duration(g.goal_seconds)}", 13, color=t.MUTED).pack(
                side="left", anchor="s", pady=(0, 2))
            if g.done_seconds == 0:
                sub = "첫 기록을 남기면 진행률이 채워져요"
            elif g.remaining_seconds:
                sub = f"목표까지 {fmt.duration(g.remaining_seconds)} 남았어요"
            else:
                sub = "이번 주 목표를 달성했어요!"

        bar = ctk.CTkProgressBar(inner, height=12, corner_radius=6, border_width=0,
                                 fg_color=t.PRIMARY_SOFT, progress_color=t.PRIMARY)
        bar.pack(fill="x", pady=(10, 10))
        bar.set(g.ratio)
        if g.ratio == 0:
            # 0이어도 막대 끝에 점이 남지 않게 채움색을 배경색과 같게 한다
            bar.configure(progress_color=t.PRIMARY_SOFT)
        label(inner, sub, 12, color=t.MUTED).pack(anchor="w")

        # 칸 어디를 눌러도 목표 페이지로(목표 페이지 배너와 같은 식의 호버: 바탕이 한 단계 진해짐).
        # '목표를 설정해 보세요 →'는 따로 목표 수정창을 연다
        make_clickable(box, lambda: self.app.screen.show_page("goal"),
                       lambda: box.configure(fg_color=t.GRAY_100),
                       lambda: box.configure(fg_color=t.SURFACE),
                       skip=[link] if link is not None else [])

    # --- 과목 ---

    def _subjects(self, master) -> None:
        subjects = self.store.subjects
        n = len(subjects)
        head = ctk.CTkFrame(master, fg_color="transparent")
        head.pack(fill="x", pady=(24, 12))
        label(head, "과목", 18, bold=True).pack(side="left", anchor="s")
        count = f"{n}/{MAX_SUBJECTS} · 최대 {MAX_SUBJECTS}개" if n >= MAX_SUBJECTS else f"{n}/{MAX_SUBJECTS}"
        label(head, count, 13, color=t.MUTED).pack(side="left", anchor="s", padx=(8, 0), pady=(0, 2))

        if not subjects:
            self._empty_subjects(master)
            return
        label(head, "카드를 누르면 바로 공부가 시작돼요", 13, color=t.MUTED).pack(
            side="right", anchor="s", pady=(0, 2))

        grid = ctk.CTkFrame(master, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure(tuple(range(COLUMNS)), weight=1, uniform="subject")
        group = HoverGroup()  # 카드와 '과목 추가' 칸 중 호버는 하나만
        cells = [SubjectCard(grid, s.name, s.color,
                             on_menu=lambda s=s: self._edit(s),
                             on_click=lambda s=s: self.app.start_study(s.id),
                             hover_group=group)
                 for s in subjects]
        if n < MAX_SUBJECTS:
            cells.append(AddSlot(grid, self._add, hover_group=group))
        for i, cell in enumerate(cells):
            col = i % COLUMNS
            cell.grid(row=i // COLUMNS, column=col, sticky="ew", pady=(0, 16),
                      padx=(0 if col == 0 else 8, 0 if col == COLUMNS - 1 else 8))

    def _empty_subjects(self, master) -> None:
        """01-E: 과목이 하나도 없으면 남은 공간 전체가 '과목 추가' 칸."""
        box = ctk.CTkFrame(master, fg_color=t.BG, border_width=1, border_color=t.BORDER_STRONG,
                           corner_radius=t.R_CARD)
        box.pack(fill="both", expand=True)
        center = ctk.CTkFrame(box, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")
        plus = ctk.CTkFrame(center, width=56, height=56, corner_radius=28, border_width=1,
                            border_color=t.BORDER_STRONG, fg_color=t.SURFACE)
        plus.pack()
        label(plus, "+", 30, color=t.FAINT).place(relx=0.5, rely=0.5, anchor="center")
        title = label(center, "과목 추가", 17, bold=True, color=t.MUTED)
        title.pack(pady=(10, 0))
        label(center, "과목을 추가하면 카드를 눌러 바로 공부를 시작할 수 있어요", 13,
              color=t.FAINT).pack(pady=(10, 0))
        bind_tree(box, "<Button-1>", lambda e: self._add())
        bind_hover(box, lambda: box.configure(fg_color=t.GRAY_100), lambda: box.configure(fg_color=t.BG))

    # --- 과목 관리 ---

    def _add(self) -> None:
        if not self.store.can_add_subject():
            return
        used = self.store.used_colors()
        SubjectDialog(self, [s.name for s in self.store.subjects], used,
                      lambda name, color: self._save(self.store.add_subject, name, color),
                      color=next_unused(used))

    def _edit(self, subject: Subject) -> None:
        others = [s for s in self.store.subjects if s.id != subject.id]
        SubjectDialog(self, [s.name for s in others], [s.color for s in others],
                      lambda name, color: self._save(self.store.update_subject, subject.id, name, color),
                      name=subject.name, color=subject.color,
                      on_delete=lambda: self._confirm_delete(subject))

    def _confirm_delete(self, subject: Subject) -> None:
        n = self.store.count_sessions(subject.id)
        message = (f"이 과목의 기록 {n}개도 함께 삭제되며 되돌릴 수 없어요" if n
                   else "이 과목의 기록은 0개예요. 삭제하면 되돌릴 수 없어요")
        ConfirmDialog(self, f"'{subject.name}' 과목을 삭제할까요?", message, "삭제",
                      lambda: self._save(self.store.delete_subject, subject.id))

    def _save(self, action, *args) -> None:
        if self.app.run_safely(action, *args):
            self.refresh()


def _wrap_to_width(box, *labels) -> None:
    """이름이 길면(최대 20자) 인사말을 자르지 않고 box 폭에 맞춰 줄을 바꾼다."""
    def fit(_event=None):
        width = box.winfo_width() / widget_scaling(box)
        if width > 100:
            for lb in labels:
                lb.configure(wraplength=width)
    box.bind("<Configure>", fit, add="+")
