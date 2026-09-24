"""과목 추가(09-A) / 수정(09-E) 창."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ...core.colors import next_unused
from ...core.store import check_subject_name
from .. import theme as t
from ..widgets.color_picker import ColorPicker
from ..widgets.common import Button, hline, label
from ..widgets.name_entry import NameEntry
from .base import ModalDialog


class SubjectDialog(ModalDialog):
    """other_names / other_colors: 수정 중인 과목을 뺀 나머지 과목의 이름과 색.

    on_submit(name, color)은 저장 버튼이 눌리면 불린다.
    on_delete가 있으면(수정 모드) 아래에 '과목 삭제' 버튼이 생긴다. 이 창을 닫은 뒤 불린다.
    """

    def __init__(self, parent, other_names: list[str], other_colors: list[str],
                 on_submit: Callable[[str, str], None],
                 name: str = "", color: str | None = None,
                 on_delete: Callable[[], None] | None = None):
        editing = on_delete is not None
        super().__init__(parent, "과목 수정" if editing else "과목 추가", 440)
        self._on_submit = on_submit
        self._on_delete = on_delete

        form = ctk.CTkFrame(self.body, fg_color="transparent")
        form.pack(fill="x", padx=24, pady=20)

        self.name_entry = NameEntry(
            form, "과목 이름", "1~10자", value=name,
            validator=lambda n: check_subject_name(n, other_names),
            on_change=self._update_button)
        self.name_entry.pack(fill="x")

        head = ctk.CTkFrame(form, fg_color="transparent")
        head.pack(fill="x", pady=(18, 8))
        label(head, "색", 14, bold=True).pack(side="left")
        label(head, "흰 점: 다른 과목이 쓰는 색" if editing else "흰 점: 이미 쓰는 색",
              12, color=t.MUTED).pack(side="right")
        self.picker = ColorPicker(form, color or next_unused(other_colors), other_colors)
        self.picker.pack(anchor="w")

        self.add_footer("저장" if editing else "추가")
        if editing:
            hline(self.body).pack(fill="x")
            Button(self.body, "과목 삭제", kind="danger", command=self._delete).pack(
                fill="x", padx=24, pady=16)
        self._update_button()
        self.show()

    def initial_focus(self):
        return self.name_entry

    def _update_button(self) -> None:
        if self.default_button is not None:
            self.default_button.set_enabled(self.name_entry.valid)

    def on_confirm(self) -> None:
        if not self.name_entry.valid:
            return
        name, color = self.name_entry.value, self.picker.selected
        self.close()
        self._on_submit(name, color)

    def _delete(self) -> None:
        self.close()
        self._on_delete()
