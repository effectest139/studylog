"""첫 실행 화면: 00-1 이름 입력 → 00-2 과목 등록. '시작하기'를 누를 때 한 번에 저장한다."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ...core.colors import next_unused
from ...core.store import MAX_SUBJECTS, DataStore, ValidationError, check_name
from .. import theme as t
from ..dialogs.confirm import AlertDialog
from ..dialogs.subject_dialog import SubjectDialog
from ..widgets.common import Badge, Button, card, label
from ..widgets.name_entry import NameEntry
from ..widgets.subject_card import AddSlot, SubjectCard


def _progress(master, step: int) -> ctk.CTkFrame:
    """두 칸짜리 진행 막대 + '1/2'."""
    row = ctk.CTkFrame(master, fg_color="transparent")
    bars = ctk.CTkFrame(row, fg_color="transparent")
    bars.pack(side="left", fill="x", expand=True)
    bars.grid_columnconfigure((0, 1), weight=1, uniform="p")
    for i in range(2):
        ctk.CTkFrame(bars, height=6, corner_radius=3,
                     fg_color=t.PRIMARY if i < step else t.BORDER).grid(
            row=0, column=i, sticky="ew", padx=(0, 6) if i == 0 else 0)
    label(row, f"{step}/2", 14, bold=True, color=t.PRIMARY).pack(side="left", padx=(12, 0))
    return row


def _heading(master, title: str, subtitle: str) -> ctk.CTkFrame:
    box = ctk.CTkFrame(master, fg_color="transparent")
    label(box, title, 24, bold=True).pack(anchor="w")
    label(box, subtitle, 14, color=t.MUTED).pack(anchor="w", pady=(8, 0))
    return box


class OnboardingScreen(ctk.CTkFrame):
    def __init__(self, master, store: DataStore, on_done: Callable[[], None]):
        super().__init__(master, fg_color=t.BG, corner_radius=0)
        self.store = store
        self._on_done = on_done
        self.name = ""
        self.subjects: list[tuple[str, str]] = []  # 아직 저장 전 (이름, 색)
        self._step_frame: ctk.CTkFrame | None = None
        self.show_name_step()

    # --- 공통 ---

    def _swap(self, frame: ctk.CTkFrame) -> None:
        if self._step_frame is not None:
            self._step_frame.destroy()
        self._step_frame = frame
        frame.place(relx=0.5, rely=0.5, anchor="center")

    def on_enter_key(self) -> None:
        """App이 메인 창의 Enter를 넘겨준다."""
        self._enter_action()

    # --- 00-1 이름 ---

    def show_name_step(self) -> None:
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        logo = ctk.CTkFrame(wrap, fg_color="transparent")
        logo.pack(pady=(0, 32))
        Badge(logo, "S", 36, 8, t.PRIMARY, "#FFFFFF", 18).pack(side="left")
        label(logo, "StudyLog", 22, bold=True).pack(side="left", padx=(10, 0))

        box = card(wrap, width=520)
        box.pack()
        inner = ctk.CTkFrame(box, fg_color="transparent", width=440)
        inner.pack(padx=40, pady=40)
        _progress(inner, 1).pack(fill="x")
        _heading(inner, "반가워요! 이름을 알려 주세요", "홈 인사말과 프로필에 표시돼요").pack(
            fill="x", pady=(28, 0))
        self._name_entry = NameEntry(inner, "이름", "1~10자", value=self.name,
                                     validator=check_name, on_change=self._update_next,
                                     height=48, size=16, show_count=True)
        self._name_entry.pack(fill="x", pady=(28, 0))
        # 입력칸 폭을 고정하려고 440px짜리 빈 틀을 하나 둔다(pack은 내용 폭을 따라가므로)
        ctk.CTkFrame(inner, width=440, height=0, fg_color="transparent").pack()
        self._next = Button(inner, "다음", height=52, size=16, command=self._go_subjects)
        self._next.pack(fill="x", pady=(28, 0))

        self._swap(wrap)
        self._enter_action = self._go_subjects
        self._update_next()
        self.after(50, self._name_entry.focus)

    def _update_next(self) -> None:
        self._next.set_enabled(self._name_entry.valid)

    def _go_subjects(self) -> None:
        if not self._name_entry.valid:
            return
        self.name = self._name_entry.value
        self.show_subject_step()

    # --- 00-2 과목 ---

    def show_subject_step(self) -> None:
        box = card(self, width=940)
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(padx=40, pady=40)
        _progress(inner, 2).pack(fill="x")
        _heading(inner, "공부할 과목을 등록해 주세요",
                 f"최대 {MAX_SUBJECTS}개 · 나중에 홈에서 추가하거나 바꿀 수 있어요").pack(
            fill="x", pady=(28, 0))

        self._grid = ctk.CTkFrame(inner, fg_color="transparent")
        self._grid.pack(fill="x", pady=(28, 0))
        self._grid.grid_columnconfigure(tuple(range(5)), weight=1, uniform="c")
        # 카드 칸 폭을 디자인(860 = 940 - 여백 80)에 맞추는 보이지 않는 틀
        ctk.CTkFrame(inner, width=860, height=0, fg_color="transparent").pack()

        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(fill="x", pady=(28, 0))
        Button(actions, "이전", kind="secondary", width=120, height=52, size=16,
               command=self._back_to_name).pack(side="left", anchor="s")
        right = ctk.CTkFrame(actions, fg_color="transparent")
        right.pack(side="right")
        self._start = Button(right, "시작하기", width=200, height=52, size=16, command=self._finish)
        self._start.pack(anchor="e")
        self._start_hint = label(right, "과목을 1개 이상 추가해 주세요", 13, color=t.MUTED)

        self._swap(box)
        self._enter_action = self._finish
        self._render_subjects()

    def _render_subjects(self) -> None:
        for w in self._grid.winfo_children():
            w.destroy()
        cells = [SubjectCard(self._grid, name, color, on_menu=lambda i=i: self._edit(i))
                 for i, (name, color) in enumerate(self.subjects)]
        if len(self.subjects) < MAX_SUBJECTS:
            cells.append(AddSlot(self._grid, self._add))
        for i, cell in enumerate(cells):
            cell.grid(row=i // 5, column=i % 5, sticky="ew",
                      padx=(0 if i % 5 == 0 else 8, 0 if i % 5 == 4 else 8), pady=(0, 16))

        has_any = bool(self.subjects)
        self._start.set_enabled(has_any)
        if has_any:
            self._start_hint.pack_forget()
        else:
            self._start_hint.pack(anchor="e", pady=(8, 0))

    def _names(self, skip: int | None = None) -> list[str]:
        return [n for i, (n, _) in enumerate(self.subjects) if i != skip]

    def _colors(self, skip: int | None = None) -> list[str]:
        return [c for i, (_, c) in enumerate(self.subjects) if i != skip]

    def _add(self) -> None:
        def submit(name: str, color: str) -> None:
            self.subjects.append((name, color))
            self._render_subjects()
        SubjectDialog(self, self._names(), self._colors(), submit,
                      color=next_unused(self._colors()))

    def _edit(self, index: int) -> None:
        name, color = self.subjects[index]

        def submit(new_name: str, new_color: str) -> None:
            self.subjects[index] = (new_name, new_color)
            self._render_subjects()

        def delete() -> None:
            # 아직 저장 전이고 기록도 없으므로 확인 없이 목록에서 뺀다
            del self.subjects[index]
            self._render_subjects()

        SubjectDialog(self, self._names(index), self._colors(index), submit,
                      name=name, color=color, on_delete=delete)

    def _back_to_name(self) -> None:
        self.show_name_step()

    def _finish(self) -> None:
        if not self.subjects:
            return
        try:
            self.store.complete_onboarding(self.name, self.subjects)
        except ValidationError as e:
            AlertDialog(self, "시작할 수 없어요", str(e))
            return
        except OSError as e:
            AlertDialog(self, "저장하지 못했어요", f"데이터 파일을 쓸 수 없어요.\n{e}")
            return
        self._on_done()
