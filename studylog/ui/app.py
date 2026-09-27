"""메인 창: 첫 실행 화면과 메인 화면(사이드바 + 페이지)을 바꿔 가며 보여 준다."""

from __future__ import annotations

import customtkinter as ctk

from ..core.store import DataStore, ValidationError
from . import theme as t
from .dialogs.confirm import AlertDialog
from .pages.base import Page, PlaceholderPage
from .pages.home import HomePage
from .pages.onboarding import OnboardingScreen
from .pages.study import StudyPage
from .widgets.sidebar import Sidebar


class MainScreen(ctk.CTkFrame):
    """왼쪽 사이드바 + 오른쪽 페이지."""

    def __init__(self, master, app: App):
        super().__init__(master, fg_color=t.BG, corner_radius=0)
        self.app = app
        self.sidebar = Sidebar(self, app.store.name, self.show_page, app.open_profile)
        self.sidebar.pack(side="left", fill="y")
        self.content = ctk.CTkFrame(self, fg_color=t.BG, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)
        self.pages: dict[str, Page] = {}
        self.current: str | None = None
        self.locked = False
        self.study: StudyPage | None = None
        self.show_page("home")

    def _make_page(self, key: str) -> Page:
        if key == "home":
            return HomePage(self.content, self.app)
        titles = {"record": ("기록", 5), "analysis": ("분석", 6), "goal": ("목표", 7)}
        title, step = titles[key]
        return PlaceholderPage(self.content, self.app, title, step)

    def show_page(self, key: str) -> None:
        if self.locked:
            return
        if key not in self.pages:
            self.pages[key] = self._make_page(key)
        if self.current and self.current != key:
            self.pages[self.current].pack_forget()
        page = self.pages[key]
        page.pack(fill="both", expand=True)
        page.refresh()
        self.current = key
        self.sidebar.set_active(key)

    def set_locked(self, locked: bool) -> None:
        """공부 중에는 사이드바와 프로필 버튼을 잠근다."""
        self.locked = locked
        self.sidebar.set_locked(locked)
        if not locked:
            self.sidebar.set_active(self.current or "home")

    # --- 공부 ---

    def start_study(self, subject_id: str) -> None:
        if self.study is not None:
            return
        subject = self.app.store.get_subject(subject_id)
        if self.current:
            self.pages[self.current].pack_forget()
        self.study = StudyPage(self.content, self.app, subject, on_finish=self._end_study)
        self.study.pack(fill="both", expand=True)
        self.set_locked(True)

    def _end_study(self) -> None:
        if self.study is not None:
            self.study.destroy()
            self.study = None
        self.set_locked(False)
        self.current = None
        self.show_page("home")  # 방금 저장한 기록이 요약에 반영된다

    # --- 키 ---

    def on_enter_key(self) -> None:
        if self.study is not None:
            self.study.on_enter_key()

    def on_space_key(self) -> None:
        if self.study is not None:
            self.study.on_space_key()


class App(ctk.CTk):
    def __init__(self, store: DataStore):
        ctk.set_appearance_mode("light")
        super().__init__(fg_color=t.BG)
        t.init_fonts(self)
        self.store = store
        self.title("StudyLog")
        self._fit_scaling_to_screen()
        self.geometry(f"{t.WINDOW_W}x{t.WINDOW_H}")
        self.minsize(t.WINDOW_W, t.WINDOW_H)
        self._center_on_screen()

        self.screen: OnboardingScreen | MainScreen | None = None
        self.bind("<Return>", self._on_return)
        self.bind("<KP_Enter>", self._on_return)
        self.bind("<space>", self._on_space)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if store.is_onboarded:
            self.show_main()
        else:
            self.show_onboarding()

        if store.recovered_backup is not None:
            self.after(300, lambda: AlertDialog(
                self, "데이터 파일을 읽지 못했어요",
                "파일이 손상되어 새로 시작해요. 원래 파일은 아래 이름으로 보관했어요.\n"
                f"{store.recovered_backup.name}"))

    # --- 화면 전환 ---

    def _set_screen(self, screen) -> None:
        if self.screen is not None:
            self.screen.destroy()
        self.screen = screen
        screen.pack(fill="both", expand=True)

    def show_onboarding(self) -> None:
        self._set_screen(OnboardingScreen(self, self.store, on_done=self.show_main))

    def show_main(self) -> None:
        self._set_screen(MainScreen(self, self))

    def open_profile(self) -> None:
        """프로필 창은 7단계에서 만든다."""

    def open_goal_editor(self) -> None:
        """목표 수정창은 7단계에서 만든다. 지금은 목표 페이지로만 이동한다."""
        if isinstance(self.screen, MainScreen):
            self.screen.show_page("goal")

    def start_study(self, subject_id: str) -> None:
        """과목 카드를 누르면 공부를 시작한다."""
        if isinstance(self.screen, MainScreen):
            self.screen.start_study(subject_id)

    def run_safely(self, action, *args) -> bool:
        """데이터를 바꾸는 동작을 실행한다. 실패하면 알림창을 띄우고 False."""
        try:
            action(*args)
            return True
        except ValidationError as e:
            AlertDialog(self, "저장할 수 없어요", str(e))
        except OSError as e:
            AlertDialog(self, "저장하지 못했어요", f"데이터 파일을 쓸 수 없어요.\n{e}")
        return False

    # --- 키 ---

    def _on_return(self, _event=None):
        # 대화상자는 별도 창이라 이 바인딩이 불리지 않는다(대화상자가 따로 처리)
        if self.screen is not None:
            self.screen.on_enter_key()

    def _on_space(self, _event=None):
        # 공부 중일 때만 쓴다(처음 등록 화면의 입력칸에서는 그냥 띄어쓰기)
        if isinstance(self.screen, MainScreen):
            self.screen.on_space_key()

    def _on_close(self) -> None:
        """창의 X. 대화상자가 떠 있으면 무시하고, 공부 중이면 저장할지 묻는다."""
        grabbed = self.grab_current()
        if grabbed is not None and grabbed is not self:
            grabbed.focus_force()
            return
        if isinstance(self.screen, MainScreen) and self.screen.study is not None:
            self.screen.study.ask_quit(self.destroy)
            return
        self.destroy()

    # --- 창 크기 ---

    def _fit_scaling_to_screen(self) -> None:
        """Windows 배율 때문에 1100×700 창이 화면보다 커지면 전체를 조금 줄인다."""
        scale = ctk.ScalingTracker.get_window_scaling(self)
        room_w = self.winfo_screenwidth() - 40
        room_h = self.winfo_screenheight() - 100  # 작업 표시줄·제목 표시줄
        factor = min(1.0, room_w / (t.WINDOW_W * scale), room_h / (t.WINDOW_H * scale))
        if factor < 1.0:
            ctk.set_window_scaling(factor)
            ctk.set_widget_scaling(factor)

    def _center_on_screen(self) -> None:
        scale = ctk.ScalingTracker.get_window_scaling(self)
        w, h = t.WINDOW_W * scale, t.WINDOW_H * scale
        x = int((self.winfo_screenwidth() - w) / 2)
        y = int((self.winfo_screenheight() - h) / 2 - 20)
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
