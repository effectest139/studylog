"""모든 대화상자의 바탕: 별도 창, 떠 있는 동안 뒤 창 조작 막기, Enter 확인 / Esc 닫기."""

from __future__ import annotations

import customtkinter as ctk

from .. import theme as t
from ..widgets.common import Button, Hover, hline


class ModalDialog(ctk.CTkToplevel):
    """사용법: 하위 클래스에서 self.body와 add_footer()로 내용을 만든 뒤 마지막에 self.show().

    - on_confirm(): Enter나 확인 버튼. 기본 확인 버튼이 비활성이면 Enter는 무시한다.
    - close(): Esc, 창의 X, 취소 버튼.
    """

    # 되돌릴 수 없는 동작(삭제·초기화)의 확인창은 False로 두어 마우스로만 확인하게 한다
    confirm_on_enter = True

    # 지금 떠 있는 대화상자들(대화상자 위에 대화상자가 뜰 수 있다)
    _open: list[ModalDialog] = []

    def __init__(self, parent, title: str, width: int):
        super().__init__(parent, fg_color=t.SURFACE)
        self.withdraw()  # 내용을 다 만들고 가운데로 옮긴 뒤 보인다(깜빡임 방지)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self._parent = parent
        self._width = width
        self.default_button: Button | None = None
        self._focus_job = None

        self.body = ctk.CTkFrame(self, fg_color="transparent", width=width)
        self.body.pack(fill="both", expand=True)
        # pack은 내용 폭을 따라가서 정한 폭보다 좁아질 수 있다: 폭을 잡아 주는 보이지 않는 틀
        ctk.CTkFrame(self.body, width=width, height=0, fg_color="transparent").pack()

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Return>", self._on_return)
        self.bind("<KP_Enter>", self._on_return)
        self.bind("<Escape>", lambda e: self.close())

    # --- 하위 클래스에서 쓰는 도우미 ---

    def add_footer(self, confirm_text: str, kind: str = "primary") -> Button:
        """디자인의 아래쪽 버튼 줄: 구분선 + 오른쪽 정렬 [취소][확인]."""
        hline(self.body).pack(fill="x")
        bar = ctk.CTkFrame(self.body, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=16)
        ok = Button(bar, confirm_text, kind=kind, width=100, command=self.on_confirm)
        ok.pack(side="right")
        Button(bar, "취소", kind="secondary", width=100, command=self.close).pack(side="right", padx=(0, 10))
        self.default_button = ok
        return ok

    def on_confirm(self) -> None:
        self.close()

    def initial_focus(self):
        """창이 뜬 뒤 포커스를 줄 위젯. 기본은 창 자신."""
        return self

    # --- 열기/닫기 ---

    def show(self) -> None:
        # 떠 있는 동안 뒤 창은 <Leave>를 못 받으니 호버를 먼저 모두 끈다
        ModalDialog._open.append(self)
        Hover.reset_all()
        self.update_idletasks()
        self._center_on_parent()
        self.deiconify()
        self.lift()
        try:
            self.wait_visibility()
            self.grab_set()  # 창이 보인 뒤에 잡아야 실패하지 않는다
        except Exception:
            pass
        self._focus_initial()
        # CTkToplevel이 뜬 직후 스스로 창 설정을 다시 하면서 포커스를 가져가는 경우가 있어 한 번 더 준다
        self._focus_job = self.after(250, self._focus_initial)

    def _focus_initial(self) -> None:
        if self.winfo_exists():
            self.focus_force()
            self.initial_focus().focus()

    def close(self) -> None:
        if self._focus_job:
            self.after_cancel(self._focus_job)
        try:
            self.grab_release()
        except Exception:
            pass
        parent = self._parent
        if self in ModalDialog._open:
            ModalDialog._open.remove(self)
        root = self._root()
        self.destroy()
        # 창이 완전히 사라진 뒤 실제 마우스 위치로 호버를 맞춘다.
        # 닫으면서 바로 다른 대화상자를 여는 경우(과목 수정 → 삭제 확인)는 그 대화상자가 닫힐 때 맞춘다.
        root.after_idle(ModalDialog._sync_hovers)
        # 대화상자 위에 뜬 대화상자였으면 뒤 대화상자가 다시 모달이 된다
        if isinstance(parent, ModalDialog) and parent.winfo_exists():
            parent.grab_set()
            parent.focus_force()
        elif parent.winfo_exists():
            parent.winfo_toplevel().focus_force()

    @staticmethod
    def _sync_hovers() -> None:
        ModalDialog._open = [d for d in ModalDialog._open if d.winfo_exists()]
        if not ModalDialog._open:
            Hover.sync_all()

    def _on_return(self, _event=None):
        if not self.confirm_on_enter:
            return "break"
        if self.default_button is not None and not self.default_button.enabled:
            return "break"
        self.on_confirm()
        return "break"

    def _center_on_parent(self) -> None:
        top = self._parent.winfo_toplevel()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        x = top.winfo_rootx() + (top.winfo_width() - w) // 2
        y = top.winfo_rooty() + (top.winfo_height() - h) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")  # 위치는 실제 픽셀(CTk가 배율을 곱하지 않음)
