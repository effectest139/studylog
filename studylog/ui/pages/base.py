"""메인 화면 오른쪽 콘텐츠 영역의 페이지 바탕."""

from __future__ import annotations

import customtkinter as ctk

from .. import theme as t
from ..widgets.common import label


class Page(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=t.BG, corner_radius=0)
        self.app = app

    def refresh(self) -> None:
        """페이지가 보일 때마다 불린다. 데이터를 다시 읽어 그린다."""


class PlaceholderPage(Page):
    """아직 만들지 않은 페이지(다음 단계에서 바뀐다)."""

    def __init__(self, master, app, title: str, step: int):
        super().__init__(master, app)
        box = ctk.CTkFrame(self, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=t.CONTENT_PAD, pady=t.CONTENT_PAD)
        label(box, title, 26, bold=True).pack(anchor="w")
        label(box, f"{step}단계에서 만들 화면이에요", 14, color=t.MUTED).pack(anchor="w", pady=(6, 0))
