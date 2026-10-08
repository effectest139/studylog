"""목표(07): 주간 목표 달성률 배너 + 과목별 목표 막대."""

from __future__ import annotations

import math
from datetime import date

import customtkinter as ctk

from ...core import fmt, stats
from .. import theme as t
from ..widgets.common import Button, Dot, card, label, make_clickable
from ..widgets.drag_scroll import DragScroll
from .base import Page

BANNER_SOFT = "#C7D2FE"   # 배너 위 연한 글자
BANNER_TRACK = "#6366F1"  # 배너 진행 막대 바탕


def _bar(master, ratio: float, color: str, track: str, height: int) -> ctk.CTkProgressBar:
    bar = ctk.CTkProgressBar(master, height=height, corner_radius=height // 2, border_width=0,
                             fg_color=track, progress_color=color if ratio > 0 else track)
    bar.set(ratio)  # 0이면 채움색을 바탕색과 같게 해 끝에 점이 남지 않게 한다
    return bar


class GoalsPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        self._box: ctk.CTkFrame | None = None

    def refresh(self) -> None:
        if self._box is not None:
            self._box.destroy()
        self._box = ctk.CTkFrame(self, fg_color="transparent")
        self._box.pack(fill="both", expand=True, padx=t.CONTENT_PAD, pady=t.CONTENT_PAD)
        today = date.today()
        store = self.app.store
        sessions = store.sessions

        head = ctk.CTkFrame(self._box, fg_color="transparent")
        head.pack(fill="x")
        left = ctk.CTkFrame(head, fg_color="transparent")
        left.pack(side="left")
        label(left, "목표", 26, bold=True).pack(anchor="w")
        label(left, "이번 주 목표와 달성률", 14, color=t.MUTED).pack(anchor="w", pady=(6, 0))
        Button(head, "목표 수정", kind="secondary", width=110, command=self.app.open_goal_editor).pack(
            side="right", anchor="s")

        g = stats.goal_progress(stats.week_total(sessions, today), store.weekly_goal_minutes)
        self._banner(g, today)
        self._subjects(sessions, today)

    # --- 주간 목표 배너 ---

    def _banner(self, g: stats.GoalProgress, today: date) -> None:
        banner = ctk.CTkFrame(self._box, fg_color=t.PRIMARY, corner_radius=t.R_CARD)
        banner.pack(fill="x", pady=(24, 0))
        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(fill="x", padx=32, pady=28)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left")
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="left", fill="x", expand=True, padx=(32, 0))

        if not g.has_goal:
            label(left, "주간 목표", 14, color=BANNER_SOFT).pack(anchor="w")
            label(left, "–", 56, bold=True, color="#FFFFFF").pack(anchor="w")
            label(right, "아직 주간 목표가 없어요", 17, bold=True, color="#FFFFFF").pack(anchor="w")
            label(right, "'목표 수정'에서 이번 주에 공부할 시간을 정해 보세요", 13,
                  color=BANNER_SOFT).pack(anchor="w", pady=(8, 0))
            self._clickable(banner)
            return

        label(left, f"주간 목표 {fmt.duration(g.goal_seconds)}", 14, color=BANNER_SOFT).pack(anchor="w")
        label(left, f"{g.percent}%", 56, bold=True, color="#FFFFFF").pack(anchor="w")

        row = ctk.CTkFrame(right, fg_color="transparent")
        row.pack(fill="x")
        done = ctk.CTkFrame(row, fg_color="transparent")
        done.pack(side="left")
        label(done, fmt.duration(g.done_seconds, empty="0분"), 15, bold=True, color="#FFFFFF").pack(side="left")
        label(done, " 달성", 15, color="#FFFFFF").pack(side="left")
        label(row, f"{fmt.duration(g.remaining_seconds)} 남음" if g.remaining_seconds else "달성 완료",
              15, color=BANNER_SOFT).pack(side="right")
        _bar(right, g.ratio, "#FFFFFF", BANNER_TRACK, 16).pack(fill="x", pady=(12, 12))

        if g.remaining_seconds:
            days_left = 7 - today.weekday()  # 오늘 포함
            per_day = fmt.duration(math.ceil(g.remaining_seconds / days_left / 60) * 60)
            tip = (f"오늘 {per_day} 공부하면 이번 주 목표를 채울 수 있어요" if days_left == 1
                   else f"하루 {per_day}씩 공부하면 이번 주 목표를 채울 수 있어요")
        else:
            tip = "이번 주 목표를 달성했어요! 잘하고 있어요"
        label(right, tip, 13, color=BANNER_SOFT).pack(anchor="w")
        self._clickable(banner)

    def _clickable(self, banner) -> None:
        """배너 어디를 눌러도 목표 수정창. 올리면 조금 진한 보라."""
        make_clickable(banner, self.app.open_goal_editor,
                       lambda: banner.configure(fg_color=t.PRIMARY_HOVER),
                       lambda: banner.configure(fg_color=t.PRIMARY))

    # --- 과목별 목표 ---

    def _subjects(self, sessions, today: date) -> None:
        box = card(self._box)
        box.pack(fill="both", expand=True, pady=(24, 0))
        label(box, "과목별 목표", 16, bold=True).pack(anchor="w", padx=28, pady=(24, 6))
        subjects = self.app.store.subjects
        if not subjects:
            label(box, "과목이 없어요. 홈에서 과목을 추가해 주세요", 14, color=t.MUTED).pack(
                anchor="w", padx=28, pady=(6, 24))
            return

        rows_box = ctk.CTkScrollableFrame(box, fg_color=t.SURFACE, corner_radius=0,
                                          scrollbar_button_color=t.BORDER,
                                          scrollbar_button_hover_color=t.BORDER_STRONG)
        rows_box.pack(fill="both", expand=True, padx=(28, 12), pady=(0, 16))
        for s in subjects:
            done = stats.subject_week_total(sessions, s.id, today)
            g = stats.goal_progress(done, s.weekly_goal_minutes)
            row = ctk.CTkFrame(rows_box, fg_color="transparent")
            row.pack(fill="x", padx=(0, 16), pady=(8, 8))
            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x")
            Dot(top, s.color, size=10).pack(side="left", padx=(0, 10))
            label(top, s.name, 15, bold=True).pack(side="left")
            pct = ctk.CTkFrame(top, fg_color="transparent", width=48, height=22)
            pct.pack(side="right")
            pct.pack_propagate(False)
            if g.has_goal:
                label(pct, f"{g.percent}%", 15, bold=True).pack(side="right")
                detail = f"{fmt.duration(done, empty='0분')} / {fmt.duration(g.goal_seconds)}"
            else:
                label(pct, "–", 15, bold=True, color=t.FAINT).pack(side="right")
                detail = f"목표 없음 · 이번 주 {fmt.duration(done, empty='0분')}"
            label(top, detail, 14, color=t.MUTED).pack(side="right")
            _bar(row, g.ratio, s.color, t.GRAY_100, 10).pack(fill="x", pady=(10, 0))
        DragScroll(rows_box, area=box).attach()  # 과목이 많으면 카드 안 빈 곳을 끌어서도 스크롤
