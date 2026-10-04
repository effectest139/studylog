"""메인 화면 오른쪽 콘텐츠 영역의 페이지 바탕."""

from __future__ import annotations

import customtkinter as ctk

from .. import theme as t


class Page(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=t.BG, corner_radius=0)
        self.app = app

    def refresh(self) -> None:
        """페이지가 보일 때마다 불린다. 데이터를 다시 읽어 그린다."""

