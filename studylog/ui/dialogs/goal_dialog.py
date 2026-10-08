"""목표 수정창(07-D): 주간 전체 목표와 과목별 주간 목표를 시·분으로 입력한다."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ...core import fmt
from ...core.store import DataStore
from .. import theme as t
from ..widgets.common import Dot, hline, label
from ..widgets.drag_scroll import DragScroll
from .base import ModalDialog

MAX_HOURS = 168          # 일주일
ROW_H = 52
SCROLL_AFTER = 6         # 과목이 이보다 많으면 과목 목록만 스크롤


class _NumberBox(ctk.CTkEntry):
    """숫자만 들어가는 작은 입력칸. 비우면 0으로 본다."""

    def __init__(self, master, value: int, max_value: int, digits: int, width: int, height: int,
                 size: int, bold: bool, on_change: Callable[[], None]):
        self.var = ctk.StringVar(value=str(value))
        super().__init__(master, textvariable=self.var, width=width, height=height,
                         corner_radius=t.R_CTRL, border_width=1, border_color=t.BORDER_STRONG,
                         fg_color=t.SURFACE, text_color=t.TEXT, font=t.font(size, bold), justify="right")
        self._max = max_value
        self._digits = digits
        self._on_change = on_change
        self._focused = False
        self.var.trace_add("write", self._changed)
        self.bind("<FocusIn>", self._focus_in)
        self.bind("<FocusOut>", lambda e: self._set_focus(False))

    @property
    def value(self) -> int | None:
        """올바르지 않으면 None."""
        text = self.var.get()
        if text == "":
            return 0
        n = int(text)
        return n if 0 <= n <= self._max else None

    def _changed(self, *_):
        text = self.var.get()
        cleaned = "".join(ch for ch in text if ch.isdigit())[:self._digits]
        if cleaned != text:
            self.var.set(cleaned)  # 다시 _changed가 불린다
            return
        self._paint()
        self._on_change()

    def _focus_in(self, _event=None):
        self._set_focus(True)
        self.after_idle(lambda: self.select_range(0, "end"))  # 들어가면 전체 선택: 바로 고쳐 쓰기 쉽게

    def _set_focus(self, focused: bool) -> None:
        self._focused = focused
        self._paint()

    def _paint(self) -> None:
        if self.value is None:
            self.configure(border_width=2, border_color=t.DANGER)
        else:
            self.configure(border_width=2 if self._focused else 1,
                           border_color=t.PRIMARY if self._focused else t.BORDER_STRONG)


class _TimeInput(ctk.CTkFrame):
    """[ 12 ] 시간 [ 0 ] 분."""

    def __init__(self, master, minutes: int, on_change: Callable[[], None], big: bool = False):
        super().__init__(master, fg_color="transparent")
        h, m = divmod(minutes, 60)
        height, size = (44, 17) if big else (38, 15)
        unit_color = t.TEXT if big else t.MUTED
        self.hours = _NumberBox(self, h, MAX_HOURS, 3, 64, height, size, big, on_change)
        self.hours.pack(side="left")
        unit = ctk.CTkFrame(self, fg_color="transparent", width=34, height=height)
        unit.pack(side="left")
        unit.pack_propagate(False)
        label(unit, "시간", 14, color=unit_color).pack(side="left", padx=(6, 0))
        self.minutes = _NumberBox(self, m, 59, 2, 56, height, size, big, on_change)
        self.minutes.pack(side="left")
        label(self, "분", 14, color=unit_color).pack(side="left", padx=(6, 0))

    @property
    def total(self) -> int | None:
        h, m = self.hours.value, self.minutes.value
        if h is None or m is None:
            return None
        total = h * 60 + m
        return total if total <= MAX_HOURS * 60 else None


class GoalDialog(ModalDialog):
    def __init__(self, parent, store: DataStore, on_saved: Callable[[], None]):
        super().__init__(parent, "목표 수정", 500)
        self.store = store
        self._on_saved = on_saved

        form = ctk.CTkFrame(self.body, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=20)

        weekly = ctk.CTkFrame(form, fg_color="transparent")
        weekly.pack(fill="x")
        label(weekly, "주간 전체 목표", 15, bold=True).pack(side="left")
        self.weekly = _TimeInput(weekly, store.weekly_goal_minutes, self._update, big=True)
        self.weekly.pack(side="right")

        head = ctk.CTkFrame(form, fg_color="transparent")
        head.pack(fill="x", pady=(18, 0))
        label(head, "과목별 목표", 14, bold=True).pack(side="left", anchor="s")
        self._sum = label(head, "", 13, bold=True)
        self._sum.pack(side="right", anchor="s")
        hline(form).pack(fill="x", pady=(6, 0))

        subjects = store.subjects
        if len(subjects) > SCROLL_AFTER:
            rows_box = ctk.CTkScrollableFrame(form, fg_color=t.SURFACE, corner_radius=0,
                                              height=ROW_H * SCROLL_AFTER,
                                              scrollbar_button_color=t.BORDER,
                                              scrollbar_button_hover_color=t.BORDER_STRONG)
        else:
            rows_box = ctk.CTkFrame(form, fg_color="transparent")
        rows_box.pack(fill="x")
        self.inputs: dict[str, _TimeInput] = {}
        for s in subjects:
            row = ctk.CTkFrame(rows_box, fg_color="transparent", height=ROW_H)
            row.pack(fill="x")
            row.pack_propagate(False)
            Dot(row, s.color, size=10).pack(side="left", padx=(0, 10))
            label(row, s.name, 15).pack(side="left")
            self.inputs[s.id] = _TimeInput(row, s.weekly_goal_minutes, self._update)
            self.inputs[s.id].pack(side="right", padx=(0, 8 if len(subjects) > SCROLL_AFTER else 0))
            hline(rows_box, t.DIVIDER).pack(fill="x")
        if not subjects:
            label(rows_box, "과목이 없어요. 홈에서 과목을 추가해 주세요", 13, color=t.MUTED).pack(
                anchor="w", pady=12)
        if isinstance(rows_box, ctk.CTkScrollableFrame):
            # 시·분 입력칸(CTkEntry)에서 시작한 끌기는 DragScroll이 무시한다(글자 입력·선택이 우선)
            DragScroll(rows_box).attach()

        label(form, "분은 0~59 · 과목별 합계가 전체보다 커도 저장할 수 있어요", 12,
              color=t.MUTED).pack(anchor="w", pady=(12, 0))

        self.add_footer("저장")
        self._update()
        self.show()

    def initial_focus(self):
        return self.weekly.hours

    def _values(self) -> tuple[int | None, dict[str, int | None]]:
        return self.weekly.total, {sid: box.total for sid, box in self.inputs.items()}

    def _update(self) -> None:
        weekly, per_subject = self._values()
        valid = weekly is not None and all(v is not None for v in per_subject.values())
        if self.default_button is not None:
            self.default_button.set_enabled(valid)
        if not self.inputs:
            self._sum.configure(text="")
            return
        total = sum(v or 0 for v in per_subject.values())  # 분 단위
        text = f"합계 {fmt.duration(total * 60, empty='0분')}"
        if weekly is None:
            color = t.MUTED
        elif total == weekly:
            text, color = text + " · 전체와 같아요", "#0F766E"
        elif total > weekly:
            text, color = text + f" · 전체보다 {fmt.duration((total - weekly) * 60)} 많아요", t.WARN
        else:
            text, color = text + f" · 전체보다 {fmt.duration((weekly - total) * 60)} 적어요", t.MUTED
        self._sum.configure(text=text, text_color=color)

    def on_confirm(self) -> None:
        weekly, per_subject = self._values()
        if weekly is None or any(v is None for v in per_subject.values()):
            return
        self.close()
        if self._parent.winfo_toplevel().run_safely(self.store.set_goals, weekly, per_subject):
            self._on_saved()
