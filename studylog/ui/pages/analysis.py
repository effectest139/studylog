"""분석(06 주간 / 06-M 월간 / 06-E 기록 없음): 막대 차트, 과목별 비율 도넛, 비교, 학습 조언."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Callable

import customtkinter as ctk

from ...core import advice, fmt, stats
from .. import charts
from .. import theme as t
from ..widgets.common import Dot, card, elide, label, widget_scaling
from .base import Page

LEGEND_MAX = 5          # 범례·도넛에 따로 보여 줄 과목 수. 나머지는 '기타'로 묶는다
OTHER_COLOR = "#9CA3AF"
# 디자인은 120이지만 주간 화면 오른쪽 카드가 좁아 범례 이름 자리를 위해 조금 줄인다
DONUT = 108
TAG_COLORS = {          # 조언 카드 머리표 (배경, 글자) — 디자인 06의 색
    advice.PINK: ("#FCE7F3", "#BE185D"),
    advice.TEAL: ("#CCFBF1", "#0F766E"),
    advice.INDIGO: ("#EEF2FF", "#4338CA"),
    advice.AMBER: ("#FEF3C7", "#B45309"),
}


class _Segmented(ctk.CTkFrame):
    """[주간][월간] 전환: 회색 바탕 위에 고른 쪽만 흰색."""

    def __init__(self, master, options: list[tuple[str, str]], selected: str,
                 on_change: Callable[[str], None]):
        super().__init__(master, fg_color=t.BORDER, corner_radius=t.R_CTRL)
        self._buttons = {}
        for i, (key, text) in enumerate(options):
            b = ctk.CTkButton(self, text=text, width=72, height=32, corner_radius=6, border_width=0,
                              command=lambda k=key: on_change(k))
            b.pack(side="left", padx=(4, 4 if i == len(options) - 1 else 0), pady=4)
            self._buttons[key] = b
        for key, b in self._buttons.items():
            on = key == selected
            b.configure(fg_color=t.SURFACE if on else t.BORDER,
                        hover_color=t.SURFACE if on else t.GRAY_100,
                        text_color=t.TEXT if on else t.MUTED, font=t.font(14, on))


class AnalysisPage(Page):
    def __init__(self, master, app):
        super().__init__(master, app)
        self.period = "week"
        self._box: ctk.CTkFrame | None = None

    def refresh(self) -> None:
        if self._box is not None:
            self._box.destroy()
        self._box = ctk.CTkFrame(self, fg_color="transparent")
        self._box.pack(fill="both", expand=True, padx=t.CONTENT_PAD, pady=t.CONTENT_PAD)

        today = date.today()
        sessions = self.app.store.sessions
        subjects = {s.id: s for s in self.app.store.subjects}
        week = self.period == "week"
        if week:
            first, last = stats.week_start(today), stats.week_start(today) + timedelta(days=6)
        else:
            first, last = today.replace(day=1), stats.month_last_day(today)

        self._header(fmt.date_range(first, last) if week else fmt.month_title(today))
        top = ctk.CTkFrame(self._box, fg_color="transparent")
        top.pack(fill="x", pady=(20, 0))
        # 디자인: 주간 1.35fr 1fr, 월간 1.2fr 1fr
        top.grid_columnconfigure(0, weight=135 if week else 120, uniform="top")
        top.grid_columnconfigure(1, weight=100, uniform="top")
        left, right = card(top), card(top)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        right.grid(row=0, column=1, sticky="nsew")

        if week:
            self._week_chart(left, sessions, today)
        else:
            self._month_chart(left, sessions, today)
        self._shares(right, stats.subject_shares(sessions, first, min(last, today)), subjects)

        label(self._box, "학습 조언", 15, bold=True).pack(anchor="w", pady=(20, 12))
        self._advice(sessions, today)

    def _set_period(self, period: str) -> None:
        if period != self.period:
            self.period = period
            self.refresh()

    # --- 머리글 ---

    def _header(self, range_text: str) -> None:
        row = ctk.CTkFrame(self._box, fg_color="transparent")
        row.pack(fill="x")
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left")
        label(left, "분석", 26, bold=True).pack(anchor="w")
        label(left, range_text, 14, color=t.MUTED).pack(anchor="w", pady=(6, 0))
        _Segmented(row, [("week", "주간"), ("month", "월간")], self.period, self._set_period).pack(
            side="right")

    # --- 막대 차트 ---

    def _chart_card_top(self, master, title: str, total: int, comparison: stats.Comparison,
                        basis: str) -> None:
        head = ctk.CTkFrame(master, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(20, 0))
        left = ctk.CTkFrame(head, fg_color="transparent")
        left.pack(side="left")
        label(left, title, 13, color=t.MUTED).pack(anchor="w")
        label(left, fmt.duration(total, empty="0시간 0분"), 26, bold=True,
              color=t.TEXT if total >= 60 else t.GHOST).pack(anchor="w", pady=(4, 0))

        c = comparison
        if c.current == 0 and c.previous == 0:
            return
        if c.diff > 0:
            text, color = f"{basis}보다 {fmt.duration(c.diff)} ↑", t.ACCENT
        elif c.diff < 0:
            text, color = f"{basis}보다 {fmt.duration(-c.diff)} ↓", t.WARN
        else:
            text, color = f"{basis}와 같아요", t.MUTED
        if abs(c.diff) < 60 and c.diff != 0:  # 1분 미만 차이는 같다고 본다
            text, color = f"{basis}와 같아요", t.MUTED
        label(head, text, 13, bold=True, color=color).pack(side="right", anchor="n", pady=(2, 0))

    def _week_chart(self, master, sessions, today: date) -> None:
        days = stats.week_days(sessions, today)
        total = sum(sec for d, sec in days if d <= today)
        self._chart_card_top(master, "총 공부 시간", total, stats.compare_week(sessions, today),
                             "지난주 같은 요일")
        values = [sec if d <= today else 0 for d, sec in days]
        fig = charts.bar_chart(
            values,
            labels=list(fmt.WEEKDAYS),
            colors=[t.ACCENT if d == today else t.PRIMARY for d, _ in days],
            value_labels=[fmt.duration_short(v) if v else "" for v in values],
            empty_text=None if any(values) else "요일별 공부 시간이 여기에 표시돼요",
            bar_width=0.42)
        self._place_chart(master, fig, height=210)

    def _month_chart(self, master, sessions, today: date) -> None:
        weeks = stats.month_weeks(sessions, today)
        total = sum(sec for _, _, sec in weeks)
        self._chart_card_top(master, "이번 달 총 공부 시간", total, stats.compare_month(sessions, today),
                             "지난달 같은 날짜")
        values = [sec if a <= today else 0 for a, _, sec in weeks]
        fig = charts.bar_chart(
            values,
            labels=[f"{i + 1}주" for i in range(len(weeks))],
            sub_labels=[f"{a.month}/{a.day}–{b.day}" for a, b, _ in weeks],
            colors=[t.ACCENT if a <= today <= b else t.PRIMARY for a, b, _ in weeks],
            value_labels=[fmt.duration_short(v) if v else ("예정" if a > today else "")
                          for v, (a, _, _) in zip(values, weeks)],
            empty_text=None if any(values) else "주차별 공부 시간이 여기에 표시돼요",
            bar_width=0.5)
        self._place_chart(master, fig, height=226)

    def _place_chart(self, master, fig, height: int) -> None:
        holder = ctk.CTkFrame(master, fg_color=t.SURFACE)
        holder.pack(fill="x", padx=16, pady=(4, 16))
        charts.embed(fig, holder, height).get_tk_widget().pack(fill="x")

    # --- 과목별 비율 ---

    def _shares(self, master, shares: list[tuple[str, int]], subjects) -> None:
        head = ctk.CTkFrame(master, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(20, 0))
        label(head, "과목별 비율", 15, bold=True).pack(side="left")
        body = ctk.CTkFrame(master, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(8, 20))

        rows = [(subjects[sid].name, subjects[sid].color, sec) for sid, sec in shares]
        if len(rows) > LEGEND_MAX:  # 색을 새로 만들지 않고 나머지는 '기타'로 묶는다
            rest = rows[LEGEND_MAX - 1:]
            rows = rows[:LEGEND_MAX - 1] + [(f"기타 {len(rest)}개", OTHER_COLOR, sum(r[2] for r in rest))]
        total = sum(r[2] for r in rows)

        donut_box = ctk.CTkFrame(body, fg_color=t.SURFACE, width=DONUT, height=DONUT)
        donut_box.pack(side="left", anchor="center")
        fig = charts.donut_chart([r[2] for r in rows], [r[1] for r in rows])
        widget = charts.embed(fig, donut_box, DONUT).get_tk_widget()
        widget.configure(width=round(DONUT * charts.widget_scaling(donut_box)))
        widget.pack()

        legend = ctk.CTkFrame(body, fg_color="transparent")
        legend.pack(side="left", fill="both", expand=True, padx=(14, 0))
        if not rows:
            label(legend, "과목별로 공부하면 비율을 보여 드려요", 14, color=t.MUTED,
                  wraplength=180, justify="left").pack(anchor="w", expand=True)
            return
        label(head, "시간 많은 순", 12, color=t.MUTED).pack(side="right")
        center = ctk.CTkFrame(legend, fg_color="transparent")
        center.pack(fill="x", expand=True)
        for name, color, sec in rows:
            row = ctk.CTkFrame(center, fg_color="transparent", height=30)
            row.pack(fill="x")
            row.pack_propagate(False)
            # pack은 먼저 넣은 것부터 자리를 차지한다: 비율·시간을 먼저 두고 이름은 남는 폭만 쓴다
            pct = ctk.CTkFrame(row, fg_color="transparent", width=36, height=30)
            pct.pack(side="right")
            pct.pack_propagate(False)
            label(pct, f"{round(sec * 100 / total)}%", 13, bold=True).pack(side="right")
            label(row, fmt.duration(sec), 12, color=t.MUTED).pack(side="right", padx=(6, 0))
            Dot(row, color, size=10, radius=3).pack(side="left", padx=(0, 8))
            name_box = ctk.CTkFrame(row, fg_color="transparent", width=1, height=30)
            name_box.pack(side="left", fill="x", expand=True)
            name_box.pack_propagate(False)
            name_label = label(name_box, name, 13)
            name_label.pack(side="left")
            name_box.bind("<Configure>", lambda e, lb=name_label, n=name: lb.configure(
                text=elide(t.font(13), n, e.width / widget_scaling(lb) - 2)))

    # --- 학습 조언 ---

    def _advice(self, sessions, today: date) -> None:
        cards = advice.build(self.period, sessions, self.app.store.subjects, today)
        if not cards:
            box = card(self._box)
            box.pack(fill="both", expand=True)
            center = ctk.CTkFrame(box, fg_color="transparent")
            center.place(relx=0.5, rely=0.5, anchor="center")
            days = stats.recorded_days(sessions)
            label(center, "아직 분석할 기록이 없어요" if days == 0 else f"기록한 날이 {days}일이에요",
                  16, bold=True).pack()
            label(center, "3일 이상 기록하면 맞춤 학습 조언을 알려 드려요", 14, color=t.MUTED).pack(pady=(8, 0))
            return

        grid = ctk.CTkFrame(self._box, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="advice")
        grid.grid_rowconfigure(0, weight=1)
        for i, a in enumerate(cards):
            box = card(grid)
            box.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 10, 0 if i == 2 else 10))
            inner = ctk.CTkFrame(box, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=20, pady=18)
            bg, fg = TAG_COLORS[a.tone]
            tag = ctk.CTkFrame(inner, fg_color=bg, corner_radius=12, height=24)
            tag.pack(anchor="w")
            label(tag, a.tag, 12, bold=True, color=fg).pack(padx=10, pady=3)
            label(inner, a.title, 15, bold=True, wraplength=230, justify="left").pack(anchor="w", pady=(8, 0))
            label(inner, a.body, 13, color=t.MUTED, wraplength=230, justify="left").pack(anchor="w", pady=(8, 0))
