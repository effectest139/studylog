"""공부 화면: 03 공부 중 / 03-P 일시정지 / 04 공부 완료 / 04-D 저장 안 함 확인.

이 화면이 떠 있는 동안 사이드바와 프로필 버튼은 잠겨 있다(MainScreen이 처리).
"""

from __future__ import annotations

import time
from typing import Callable

import customtkinter as ctk

from ...core import colors, fmt
from ...core.models import Subject
from ...core.store import MIN_SESSION_SECONDS
from ...core.timer import FINISHED, RUNNING, StudyTimer
from .. import theme as t
from ..dialogs.base import ModalDialog
from ..dialogs.confirm import ConfirmDialog
from ..widgets.common import Badge, Button, Dot, card, hline, label

TICK_MS = 200
ACCENT_HOVER = "#0D9488"
SPACE_REPEAT_S = 0.3  # Space를 누르고 있을 때 반복 입력으로 계속 바뀌지 않게


class StudyPage(ctk.CTkFrame):
    def __init__(self, master, app, subject: Subject, on_finish: Callable[[], None]):
        super().__init__(master, fg_color=t.BG, corner_radius=0)
        self.app = app
        self.subject = subject
        self._on_finish = on_finish
        self.timer = StudyTimer()
        self._tick_job = None
        self._last_space = 0.0
        self._save_button: Button | None = None

        self.timer.start()
        self._build_timer_view()
        self._tick()

    # --- 03 / 03-P 타이머 ---

    def _build_timer_view(self) -> None:
        self._view = card(self)
        self._view.pack(fill="both", expand=True, padx=t.CONTENT_PAD, pady=t.CONTENT_PAD)
        center = ctk.CTkFrame(self._view, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")
        center.grid_columnconfigure(0, weight=1)

        # 과목 배지 + 상태
        top = ctk.CTkFrame(center, fg_color="transparent")
        top.grid(row=0, column=0, pady=(0, 32))
        pill = ctk.CTkFrame(top, height=36, corner_radius=t.R_CTRL, fg_color=self.subject.color)
        pill.pack(side="left")
        label(pill, self.subject.name, 16, bold=True,
              color=colors.on_color(self.subject.color)).pack(padx=16, pady=7)
        self._status_dot = Dot(top, t.ACCENT, size=10)
        self._status_dot.pack(side="left", padx=(12, 8))
        self._status = label(top, "", 15, bold=True)
        self._status.pack(side="left")

        # 01:12:45 + 시/분/초
        clock_box = ctk.CTkFrame(center, fg_color="transparent")
        clock_box.grid(row=1, column=0)
        self._clock = ctk.CTkLabel(clock_box, text=fmt.clock(0), font=t.timer_font(104),
                                   text_color=t.TEXT, height=0)
        self._clock.pack()
        units = ctk.CTkFrame(clock_box, fg_color="transparent", height=24)
        units.pack(fill="x", pady=(8, 0))
        # Consolas는 글자 폭이 같아서 'HH:MM:SS' 8칸 중 1·4·7번째 칸 중심이 시·분·초 가운데
        for text, relx in (("시", 1 / 8), ("분", 4 / 8), ("초", 7 / 8)):
            label(units, text, 14, color=t.MUTED).place(relx=relx, rely=0.5, anchor="center")

        # 시작 시각 / 일시정지 안내 (같은 자리를 번갈아 쓴다)
        self._started = label(center, f"시작 시각 {fmt.time_of_day(self.timer.started_at)}", 14,
                              color=t.MUTED)
        self._paused_note = ctk.CTkLabel(center, text="일시정지 중에는 시간이 기록되지 않아요",
                                         fg_color=t.GRAY_100, corner_radius=t.R_CTRL, height=0,
                                         text_color=t.MUTED, font=t.font(14))

        # 버튼 + Space 안내
        actions = ctk.CTkFrame(center, fg_color="transparent")
        actions.grid(row=3, column=0, pady=(32, 0))
        buttons = ctk.CTkFrame(actions, fg_color="transparent")
        buttons.pack()
        Button(buttons, "종료", kind="secondary", width=180, height=56, size=17, bold=True,
               command=self.stop).pack(side="left", padx=(0, 16))
        self._toggle_btn = Button(buttons, "일시정지", width=180, height=56, size=17,
                                  command=self.toggle)
        self._toggle_btn.pack(side="left")
        hint = ctk.CTkFrame(actions, fg_color="transparent")
        hint.pack(pady=(14, 0))
        key = ctk.CTkFrame(hint, height=22, corner_radius=4, border_width=1,
                           border_color=t.BORDER_STRONG, fg_color="transparent")
        key.pack(side="left")
        label(key, "Space", 12, color=t.MUTED).pack(padx=8, pady=2)
        self._hint = label(hint, "", 13, color=t.MUTED)
        self._hint.pack(side="left", padx=(6, 0))

        self._paint_timer_view()

    def _paint_timer_view(self) -> None:
        running = self.timer.state == RUNNING
        self._status.configure(text="공부 중" if running else "일시정지됨",
                               text_color=t.ACCENT if running else t.MUTED)
        self._status_dot.configure(fg_color=t.ACCENT if running else t.MUTED,
                                   corner_radius=5 if running else 2)  # 일시정지는 네모
        self._clock.configure(text_color=t.TEXT if running else t.FAINT)
        if running:
            self._paused_note.grid_remove()
            self._started.grid(row=2, column=0, pady=(32, 0))
            self._toggle_btn.configure(text="일시정지", fg_color=t.PRIMARY, hover_color=t.PRIMARY_HOVER)
            self._hint.configure(text="로 일시정지")
        else:
            self._started.grid_remove()
            self._paused_note.grid(row=2, column=0, pady=(32, 0), ipadx=16, ipady=10)
            self._toggle_btn.configure(text="재개", fg_color=t.ACCENT, hover_color=ACCENT_HOVER)
            self._hint.configure(text="로 재개")
        self._update_clock()

    def _update_clock(self) -> None:
        self._clock.configure(text=fmt.clock(self.timer.elapsed))

    def _tick(self) -> None:
        if self.timer.state == RUNNING:
            self._update_clock()
        self._tick_job = self.after(TICK_MS, self._tick)

    def toggle(self) -> None:
        if not self.timer.active:
            return
        self.timer.toggle()
        self._paint_timer_view()

    def stop(self) -> None:
        if not self.timer.active:
            return
        self.timer.stop()
        self._view.destroy()
        self._build_done_view()

    # --- 04 공부 완료 ---

    def _build_done_view(self) -> None:
        elapsed = self.timer.elapsed
        savable = elapsed >= MIN_SESSION_SECONDS
        self._view = ctk.CTkFrame(self, fg_color="transparent")
        self._view.pack(fill="both", expand=True, padx=t.CONTENT_PAD, pady=t.CONTENT_PAD)
        box = card(self._view)
        box.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(padx=40, pady=40)
        ctk.CTkFrame(inner, width=400, height=0, fg_color="transparent").pack()  # 카드 폭 480

        Badge(inner, "✓", 64, 32, t.ACCENT, "#FFFFFF", 30).pack()
        label(inner, "공부 완료!", 26, bold=True).pack(pady=(24, 0))
        label(inner, "수고했어요. 오늘 기록을 저장할까요?" if savable else "1분 미만은 저장되지 않아요",
              14, color=t.MUTED).pack(pady=(6, 0))

        info = ctk.CTkFrame(inner, fg_color=t.BG, corner_radius=t.R_CTRL)
        info.pack(fill="x", pady=(24, 0))
        rows = ctk.CTkFrame(info, fg_color="transparent")
        rows.pack(fill="x", padx=20, pady=8)
        self._info_row(rows, "과목", self._subject_value)
        hline(rows).pack(fill="x")
        self._info_row(rows, "공부한 시간", lambda m: label(
            m, fmt.duration_hms(elapsed), 18, bold=True, color=t.PRIMARY))
        hline(rows).pack(fill="x")
        self._info_row(rows, "시간", lambda m: label(
            m, fmt.time_range(self.timer.started_at, self.timer.ended_at), 15))

        self._save_button = Button(inner, "기록 저장", height=52, size=16, command=self.save)
        self._save_button.pack(fill="x", pady=(24, 0))
        self._save_button.set_enabled(savable)
        Button(inner, "저장하지 않고 닫기" if savable else "닫기", kind="ghost", height=40, size=14,
               command=self.discard).pack(fill="x", pady=(10, 0))

    def _info_row(self, master, key: str, make_value) -> None:
        row = ctk.CTkFrame(master, fg_color="transparent", height=48)
        row.pack(fill="x")
        row.pack_propagate(False)
        label(row, key, 14, color=t.MUTED).pack(side="left")
        make_value(row).pack(side="right")

    def _subject_value(self, master) -> ctk.CTkFrame:
        box = ctk.CTkFrame(master, fg_color="transparent")
        Dot(box, self.subject.color, size=10).pack(side="left", padx=(0, 8))
        label(box, self.subject.name, 15, bold=True).pack(side="left")
        return box

    def save(self) -> None:
        if self.timer.state != FINISHED or not self._save_button or not self._save_button.enabled:
            return
        if self._store_session():
            self._finish()

    def discard(self) -> None:
        if self.timer.elapsed < MIN_SESSION_SECONDS:
            self._finish()
            return
        ConfirmDialog(self, "기록을 저장하지 않을까요?",
                      f"이번 기록이 사라져요 ({self.subject.name} {fmt.duration_hms(self.timer.elapsed)})",
                      "저장 안 함", self._finish, icon=False)

    # --- 공통 ---

    def _store_session(self) -> bool:
        return self.app.run_safely(self.app.store.add_session, self.subject.id,
                                   self.timer.started_at, self.timer.ended_at, self.timer.elapsed)

    def _finish(self) -> None:
        self._on_finish()

    def destroy(self) -> None:
        if self._tick_job is not None:
            self.after_cancel(self._tick_job)
            self._tick_job = None
        super().destroy()

    # --- 키 (App → MainScreen이 넘겨준다) ---

    def on_space_key(self) -> None:
        now = time.monotonic()
        if now - self._last_space < SPACE_REPEAT_S:
            return
        self._last_space = now
        self.toggle()

    def on_enter_key(self) -> None:
        if self.timer.state == FINISHED:
            self.save()

    # --- 창 닫기 ---

    def ask_quit(self, quit_app: Callable[[], None]) -> None:
        """공부 중(또는 완료 화면)에 창을 닫으려 할 때 저장 여부를 묻는다."""
        QuitDialog(self, quit_app)


class QuitDialog(ModalDialog):
    """[취소] [저장 안 하고 종료] [저장하고 종료]. 1분 미만이면 [취소] [종료]."""

    def __init__(self, page: StudyPage, quit_app: Callable[[], None]):
        super().__init__(page, "StudyLog 종료", 440)
        self._page = page
        self._quit_app = quit_app
        timer = page.timer
        elapsed = timer.elapsed
        self._savable = elapsed >= MIN_SESSION_SECONDS

        box = ctk.CTkFrame(self.body, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=28, pady=28)
        label(box, "공부 기록을 저장하고 끝낼까요?" if self._savable else "앱을 끝낼까요?",
              20, bold=True).pack(anchor="w")
        msg = ("창을 닫기 전에 이번 기록을 저장할 수 있어요" if self._savable
               else "1분 미만이라 이번 기록은 저장되지 않아요")
        label(box, msg, 14, color=t.MUTED).pack(anchor="w", pady=(12, 0))
        what = ctk.CTkFrame(box, fg_color="transparent")
        what.pack(anchor="w", pady=(8, 0))
        Dot(what, page.subject.color, size=10).pack(side="left", padx=(0, 8))
        label(what, f"{page.subject.name} · {fmt.duration_hms(elapsed)}", 15, bold=True).pack(side="left")

        buttons = ctk.CTkFrame(box, fg_color="transparent")
        buttons.pack(fill="x", pady=(24, 0))
        if self._savable:
            self.default_button = Button(buttons, "저장하고 종료", width=130, command=self.on_confirm)
            self.default_button.pack(side="right")
            Button(buttons, "저장 안 하고 종료", kind="secondary", width=140,
                   command=self._quit_without_saving).pack(side="right", padx=(0, 10))
        else:
            self.default_button = Button(buttons, "종료", width=100, command=self.on_confirm)
            self.default_button.pack(side="right")
        Button(buttons, "취소", kind="secondary", width=80, command=self.close).pack(
            side="right", padx=(0, 10))
        self.show()

    def on_confirm(self) -> None:
        if not self._savable:
            self._quit_without_saving()
            return
        self._page.timer.stop()  # 완료 화면이었다면 이미 멈춰 있어 아무 일도 없다
        self.close()
        if self._page._store_session():
            self._quit_app()

    def _quit_without_saving(self) -> None:
        self.close()
        self._quit_app()
