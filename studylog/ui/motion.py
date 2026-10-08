"""짧은 화면 모션(0.3~0.5초)을 after()로 돌리는 도우미."""

from __future__ import annotations

import time
from typing import Callable

FRAME_SECONDS = 1 / 60
# Windows에서 Tk의 after(2~15)는 다음 15.6ms 눈금까지 기다린다. 그래서 프레임 작업이 몇 ms만 걸려도
# after(15)는 31ms 뒤가 되어 초당 30프레임으로 떨어진다. after(1)은 거의 정확하므로
# 1ms마다 시각만 확인하다가 다음 프레임 시각이 되면 그린다(확인 자체는 매우 가볍다).
# 0.3~0.5초 동안만 이렇게 돈다.
POLL_MS = 1


def ease_out_cubic(p: float) -> float:
    return 1 - (1 - p) ** 3


class Tween:
    """duration초 동안 on_frame(진행도 0→1, 이징 적용)을 부른다. 마지막 프레임은 항상 1.0.

    after는 위젯이 아니라 루트 창에 건다: 위젯이 먼저 없어지면(화면 전환) 예약된 호출이
    '없는 명령' 오류를 내기 때문이다. 대신 프레임마다 위젯이 살아 있는지 확인한다.
    """

    def __init__(self, widget, duration: float, on_frame: Callable[[float], None],
                 ease: Callable[[float], float] = ease_out_cubic):
        self._widget = widget
        self._root = widget._root()
        self._duration = duration
        self._on_frame = on_frame
        self._ease = ease
        self._job = None
        self._t0 = 0.0
        self._next = 0.0  # 다음 프레임을 그릴 시각

    @property
    def running(self) -> bool:
        return self._job is not None

    def start(self) -> None:
        self.cancel()
        # 첫 프레임(0)을 그리고 밀려 있던 화면 작업을 끝낸 뒤부터 시간을 잰다.
        # 화면에 막 들어왔을 때는 이 작업이 0.2초쯤 걸려, 먼저 재기 시작하면 모션 앞부분이 건너뛰어진다
        self._on_frame(0.0)
        self._root.update_idletasks()
        self._t0 = time.perf_counter()
        self._next = self._t0 + FRAME_SECONDS
        self._job = self._root.after(POLL_MS, self._step)

    def cancel(self) -> None:
        if self._job is not None:
            try:
                self._root.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _step(self) -> None:
        self._job = None
        try:
            if not self._widget.winfo_exists():
                return
        except Exception:
            return
        now = time.perf_counter()
        if now < self._next:
            self._job = self._root.after(POLL_MS, self._step)
            return
        self._next = max(self._next + FRAME_SECONDS, now)  # 밀렸으면 따라잡으려 몰아 그리지 않는다
        p = min(1.0, (now - self._t0) / self._duration)
        self._on_frame(self._ease(p) if p < 1 else 1.0)
        # 1ms마다 타이머가 돌면 Tk는 '할 일 없을 때' 하는 화면 다시 그리기를 계속 미룬다.
        # 그러면 모션 내내 화면이 멈춰 있다가 끝에서 한 번에 바뀌므로 프레임마다 직접 마무리한다
        self._root.update_idletasks()
        if p < 1:
            self._job = self._root.after(POLL_MS, self._step)
