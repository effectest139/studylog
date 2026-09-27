from datetime import datetime, timedelta

import pytest

from studylog.core.timer import FINISHED, IDLE, PAUSED, RUNNING, StudyTimer


class FakeClock:
    """monotonic 시계와 실제 시각을 같이 움직이는 가짜 시계."""

    def __init__(self):
        self.t = 1000.0
        self.base = datetime(2026, 9, 23, 19, 30, 0)

    def advance(self, seconds: float) -> None:
        self.t += seconds

    def mono(self) -> float:
        return self.t

    def wall(self) -> datetime:
        return self.base + timedelta(seconds=self.t - 1000.0)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def timer(clock):
    return StudyTimer(clock=clock.mono, wall=clock.wall)


def test_counts_while_running(timer, clock):
    assert timer.state == IDLE and timer.elapsed == 0
    timer.start()
    clock.advance(65.7)
    assert timer.state == RUNNING
    assert timer.elapsed == 65


def test_pause_is_not_counted(timer, clock):
    timer.start()
    clock.advance(600)
    timer.pause()
    clock.advance(300)          # 일시정지 5분
    assert timer.state == PAUSED and timer.elapsed == 600
    timer.resume()
    clock.advance(120)
    assert timer.elapsed == 720


def test_toggle(timer, clock):
    timer.start()
    timer.toggle()
    assert timer.state == PAUSED
    timer.toggle()
    assert timer.state == RUNNING


def test_stop_records_times(timer, clock):
    timer.start()
    clock.advance(3000)
    timer.pause()
    clock.advance(500)
    timer.resume()
    clock.advance(1365)
    timer.stop()
    assert timer.state == FINISHED
    assert timer.elapsed == 4365
    assert timer.started_at == datetime(2026, 9, 23, 19, 30, 0)
    assert timer.ended_at == datetime(2026, 9, 23, 20, 51, 5)
    # 종료 뒤에는 시간이 더 흐르지 않는다
    clock.advance(100)
    assert timer.elapsed == 4365


def test_stop_while_paused(timer, clock):
    timer.start()
    clock.advance(90)
    timer.pause()
    clock.advance(1000)
    timer.stop()
    assert timer.elapsed == 90


def test_cannot_start_twice(timer):
    timer.start()
    with pytest.raises(RuntimeError):
        timer.start()
