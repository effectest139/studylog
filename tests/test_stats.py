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


def test_sessions_by_day():
    sessions = [sess(ago(1), 40), sess(TODAY, 13, hour=17), sess(TODAY, 72, hour=19), sess(ago(3), 20)]
    groups = stats.sessions_by_day(sessions)
    assert [d for d, _, _ in groups] == [TODAY, ago(1), ago(3)]
    day, items, total = groups[0]
    assert [s.start.hour for s in items] == [19, 17]
    assert total == 85 * 60
    assert stats.sessions_by_day([]) == []


def test_week_days():
    days = stats.week_days([sess(TODAY, 30), sess(ago(2), 10)], TODAY)
    assert [d for d, _ in days][0] == date(2026, 9, 21) and len(days) == 7
    assert [sec // 60 for _, sec in days] == [10, 0, 30, 0, 0, 0, 0]


def test_month_weeks_are_seven_day_chunks():
    weeks = stats.month_weeks([sess(date(2026, 9, 8), 60), sess(date(2026, 9, 30), 20)], TODAY)
    assert [(a.day, b.day) for a, b, _ in weeks] == [(1, 7), (8, 14), (15, 21), (22, 28), (29, 30)]
    assert [sec // 60 for _, _, sec in weeks] == [0, 60, 0, 0, 20]
    feb = stats.month_weeks([], date(2026, 2, 10))
    assert [(a.day, b.day) for a, b, _ in feb] == [(1, 7), (8, 14), (15, 21), (22, 28)]


def test_compare_week_same_weekday():
    # 오늘은 수요일: 이번 주 월~수 ↔ 지난주 월~수 (지난주 목요일 기록은 빼야 함)
    sessions = [sess(TODAY, 60), sess(ago(1), 30),
                sess(ago(7), 20), sess(ago(9), 10), sess(ago(6), 999)]
    c = stats.compare_week(sessions, TODAY)
    assert (c.current // 60, c.previous // 60, c.diff // 60) == (90, 30, 60)
    assert c.previous_range == (date(2026, 9, 14), date(2026, 9, 16))


def test_compare_month_same_date():
    sessions = [sess(date(2026, 9, 3), 40), sess(date(2026, 8, 23), 50), sess(date(2026, 8, 24), 999)]
    c = stats.compare_month(sessions, TODAY)
    assert (c.current // 60, c.previous // 60) == (40, 50)
    # 3월 31일 ↔ 2월은 말일(28일)까지
    c2 = stats.compare_month([], date(2026, 3, 31))
    assert c2.previous_range == (date(2026, 2, 1), date(2026, 2, 28))
    # 1월 ↔ 지난해 12월
    assert stats.compare_month([], date(2026, 1, 5)).previous_range == (date(2025, 12, 1), date(2025, 12, 5))


def test_subject_shares_and_recorded_days():
    sessions = [sess(TODAY, 10, "a"), sess(TODAY, 50, "b", hour=8), sess(ago(1), 30, "a"), sess(ago(10), 99, "c")]
    assert stats.subject_shares(sessions, ago(1), TODAY) == [("b", 3000), ("a", 2400)]
    assert stats.recorded_days(sessions) == 3
