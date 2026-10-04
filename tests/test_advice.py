from datetime import date

from studylog.core import advice
from studylog.core.models import Subject

from test_stats import TODAY, ago, sess  # 수요일 2026-09-23 기준 도우미

MATH = Subject("a", "수학", "#0EA5E9")
KOR = Subject("b", "국어", "#EC4899")
ENG = Subject("c", "영어", "#F59E0B", weekly_goal_minutes=120)


def test_needs_three_recorded_days():
    two_days = [sess(TODAY, 30, "a"), sess(ago(1), 30, "a"), sess(ago(1), 30, "b", hour=8)]
    assert advice.build("week", two_days, [MATH, KOR], TODAY) == []
    three = two_days + [sess(ago(20), 10, "a")]  # 3일째가 이번 주 밖이어도 전체 기준으로 센다
    assert advice.build("week", three, [MATH, KOR], TODAY) != []


def test_week_cards():
    sessions = [sess(TODAY, 30, "a"), sess(ago(1), 90, "a"), sess(ago(2), 20, "b"),
                sess(ago(7), 30, "a"), sess(ago(8), 10, "a")]  # 지난주 월~수 40분
    cards = advice.build("week", sessions, [MATH, KOR], TODAY)
    assert [c.tag for c in cards] == ["부족한 과목", "집중한 날", "지난주 비교"]
    assert cards[0].title == "국어 시간이 가장 적어요"
    assert "이번 주 국어는 20분이에요" in cards[0].body
    assert cards[1].title == "화요일에 가장 오래 공부했어요"
    # 이번 주 월~수 140분 ↔ 지난주 월~수 40분
    assert cards[2].title == "지난주 같은 요일보다 1시간 40분 늘었어요"
    assert "지난주 월~수요일 40분" in cards[2].body


def test_week_weak_subject_with_goal():
    sessions = [sess(TODAY, 100, "a"), sess(ago(1), 30, "c"), sess(ago(2), 50, "a")]
    cards = advice.build("week", sessions, [MATH, ENG], TODAY)
    # 영어 목표 120분 중 30분 → 남은 90분 / 오늘 포함 5일 = 하루 18분
    assert "하루 18분씩 더하면 주간 목표" in cards[0].body


def test_month_compare_down():
    sessions = [sess(date(2026, 9, 2), 30, "a"), sess(date(2026, 9, 10), 30, "b"),
                sess(date(2026, 8, 5), 200, "a"), sess(date(2026, 8, 30), 999, "a")]
    cards = advice.build("month", sessions, [MATH, KOR], TODAY)
    compare = next(c for c in cards if c.tag == "지난달 비교")
    assert compare.tone == advice.AMBER
    assert compare.title == "지난달 같은 날짜보다 2시간 20분 줄었어요"  # 8/30 기록은 비교에서 빠짐
    assert "지난달 1~23일 3시간 20분" in compare.body


def test_josa():
    assert advice.josa("수학", "은", "는") == "수학은"
    assert advice.josa("국어", "은", "는") == "국어는"
    assert advice.josa("Python", "은", "는") == "Python은(는)"
    assert advice.ieyo("1시간") == "1시간이에요"


def test_weak_subject_without_records():
    sessions = [sess(TODAY, 30, "a"), sess(ago(1), 30, "a"), sess(ago(2), 30, "a")]
    week = advice.build("week", sessions, [MATH, ENG], TODAY)[0]
    assert week.title == "이번 주 영어 기록이 없어요"
    assert week.body == "하루 24분씩 더하면 주간 목표에 닿을 수 있어요."  # 120분 / 5일
    sunday = date(2026, 9, 27)
    last_day = advice.build("week", [sess(sunday, 30, "a"), sess(ago(1), 30, "a"), sess(ago(2), 30, "a")],
                            [MATH, ENG], sunday)[0]
    assert last_day.body == "오늘 2시간을 채우면 주간 목표에 닿아요."
    month = next(c for c in advice.build("month", sessions, [MATH, KOR], TODAY) if c.tag == "부족한 과목")
    assert month.title == "이번 달 국어 기록이 없어요"
