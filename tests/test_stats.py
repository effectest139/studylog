from datetime import date, datetime, timedelta

from studylog.core import stats
from studylog.core.models import Session

TODAY = date(2026, 9, 23)  # 수요일


def sess(day: date, minutes: float, subject: str = "s1", hour: int = 19) -> Session:
    start = datetime(day.year, day.month, day.day, hour)
    sec = int(minutes * 60)
    return Session(f"r{day}{hour}{subject}", subject, start, start + timedelta(seconds=sec), sec)


def ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def test_today_and_week_total():
    sessions = [
        sess(TODAY, 60), sess(TODAY, 25, hour=21),
        sess(ago(2), 30),   # 월요일: 이번 주
        sess(ago(3), 100),  # 지난주 일요일: 제외
    ]
    assert stats.today_total(sessions, TODAY) == 85 * 60
    assert stats.week_start(TODAY) == date(2026, 9, 21)
    assert stats.week_total(sessions, TODAY) == 115 * 60


def test_session_past_midnight_counts_on_start_day():
    s = sess(ago(1), 90, hour=23)
    assert stats.today_total([s], TODAY) == 0
    assert stats.today_total([s], ago(1)) == 90 * 60


def test_subject_week_total():
    sessions = [sess(TODAY, 30, "a"), sess(TODAY, 40, "b", hour=10), sess(ago(1), 20, "a")]
    assert stats.subject_week_total(sessions, "a", TODAY) == 50 * 60


def test_streak_including_today():
    sessions = [sess(TODAY, 10), sess(ago(1), 10), sess(ago(2), 10), sess(ago(4), 10)]
    assert stats.streak(sessions, TODAY) == 3


def test_streak_keeps_yesterday_when_today_empty():
    sessions = [sess(ago(1), 10), sess(ago(2), 10)]
    assert stats.streak(sessions, TODAY) == 2


def test_streak_broken():
    assert stats.streak([sess(ago(2), 10)], TODAY) == 0
    assert stats.streak([], TODAY) == 0


def test_streak_needs_one_minute_per_day():
    # 같은 날 30초 두 번 = 1분이면 인정, 59초면 불인정
    sessions = [sess(TODAY, 0.5), sess(TODAY, 0.5, hour=20), sess(ago(1), 59 / 60)]
    assert stats.streak(sessions, TODAY) == 1


def test_goal_progress():
    g = stats.goal_progress(520 * 60, 720)
    assert g.percent == 72
    assert g.remaining_seconds == 200 * 60
    assert 0.72 < g.ratio < 0.73

    over = stats.goal_progress(800 * 60, 720)
    assert over.percent == 111 and over.ratio == 1.0 and over.remaining_seconds == 0

    none = stats.goal_progress(100, 0)
    assert not none.has_goal and none.percent == 0 and none.ratio == 0
