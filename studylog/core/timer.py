"""공부 타이머: 일시정지한 시간을 뺀 실제 공부 시간(초)을 잰다."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

IDLE, RUNNING, PAUSED, FINISHED = "idle", "running", "paused", "finished"


class StudyTimer:
    """idle → running ⇄ paused → finished.

    경과 시간은 monotonic 시계로 잰다(PC 시계를 바꿔도 흔들리지 않음).
    시작·종료 시각은 기록에 남길 실제 시각(wall)으로 따로 저장한다.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic,
                 wall: Callable[[], datetime] = datetime.now):
        self._clock = clock
        self._wall = wall
        self.state = IDLE
        self.started_at: datetime | None = None
        self.ended_at: datetime | None = None
        self._banked = 0.0            # 지난 구간들에서 쌓인 공부 시간
        self._run_since: float | None = None

    @property
    def elapsed(self) -> int:
        """지금까지의 실제 공부 시간(초)."""
        total = self._banked
        if self.state == RUNNING and self._run_since is not None:
            total += self._clock() - self._run_since
        return int(total)

    @property
    def active(self) -> bool:
        """공부 중이거나 일시정지 중."""
        return self.state in (RUNNING, PAUSED)

    def start(self) -> None:
        if self.state != IDLE:
            raise RuntimeError(f"start: {self.state}")
        self.started_at = self._wall().replace(microsecond=0)
        self._run_since = self._clock()
        self.state = RUNNING

    def pause(self) -> None:
        if self.state != RUNNING:
            return
        self._banked += self._clock() - self._run_since
        self._run_since = None
        self.state = PAUSED

    def resume(self) -> None:
        if self.state != PAUSED:
            return
        self._run_since = self._clock()
        self.state = RUNNING

    def toggle(self) -> None:
        """Space 키: 공부 중이면 일시정지, 일시정지면 재개."""
        if self.state == RUNNING:
            self.pause()
        elif self.state == PAUSED:
            self.resume()

    def stop(self) -> None:
        if not self.active:
            return
        self.pause()
        self.ended_at = self.now()
        self.state = FINISHED

    def now(self) -> datetime:
        return self._wall().replace(microsecond=0)
