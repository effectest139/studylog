import random
from datetime import datetime

import pytest

from studylog.core import greeting as g
from studylog.core.stats import GoalProgress

NO_GOAL = GoalProgress(0, 0)
FIRSTS = g.Picks()                                # 모든 문구에서 첫째 후보
SECONDS = g.Picks({k: 1 for k in (*g.FIRST, *g.SECOND)})  # 모든 문구에서 둘째 후보
THU = datetime(2026, 10, 8)   # 목요일
FRI = datetime(2026, 10, 9)
SUN = datetime(2026, 10, 11)


def at(day: datetime, hour: int, minute: int = 0) -> datetime:
    return day.replace(hour=hour, minute=minute)


@pytest.mark.parametrize("hour, minute, slot", [
    (5, 0, g.MORNING), (10, 59, g.MORNING),
    (11, 0, g.AFTERNOON), (16, 59, g.AFTERNOON),
    (17, 0, g.EVENING), (21, 59, g.EVENING),
    (22, 0, g.NIGHT), (23, 59, g.NIGHT), (0, 0, g.NIGHT), (4, 59, g.NIGHT),
])
def test_time_slot_boundaries(hour, minute, slot):
    assert g.time_slot(at(THU, hour, minute).hour) == slot


@pytest.mark.parametrize("hour, first", [
    (7, "좋은 아침이에요, 민지님"), (13, "좋은 오후예요, 민지님"),
    (19, "좋은 저녁이에요, 민지님"), (23, "늦은 시간이네요, 민지님"),
])
def test_first_line_by_time(hour, first):
    assert g.lines("민지", at(THU, hour), 0, NO_GOAL, FIRSTS)[0] == first


def test_second_candidates():
    assert g.lines("민지", at(THU, 19), 0, NO_GOAL, SECONDS)[0] == "오늘 하루 어땠어요, 민지님?"
    assert g.lines("민지", at(THU, 7), 0, NO_GOAL, SECONDS)[1] == "가벼운 과목부터 시작해 봐요"


def test_weekday_greeting_only_on_friday_and_sunday():
    weekday = g.Picks(weekday=True)
    assert g.lines("민지", at(FRI, 19), 0, NO_GOAL, weekday)[0] == "즐거운 금요일이에요, 민지님"
    assert g.lines("민지", at(SUN, 7), 0, NO_GOAL, weekday)[0] == "여유로운 일요일이에요, 민지님"
    assert g.lines("민지", at(THU, 19), 0, NO_GOAL, weekday)[0] == "좋은 저녁이에요, 민지님"
    assert g.lines("민지", at(FRI, 19), 0, NO_GOAL, FIRSTS)[0] == "좋은 저녁이에요, 민지님"


def test_weekday_chance_is_about_one_in_three():
    rng = random.Random(1)
    share = sum(g.pick(rng).weekday for _ in range(3000)) / 3000
    assert 0.3 < share < 0.37


GOAL = 600 * 60  # 주간 목표 10시간


@pytest.mark.parametrize("hour, today, done, kind", [
    (3, 3600, GOAL, g.LATE_NIGHT),          # 새벽이 가장 먼저
    (1, 0, 0, g.LATE_NIGHT),
    (0, 0, 0, g.NOT_YET),                   # 0시는 새벽 문구가 아니다
    (5, 0, 0, g.NOT_YET),
    (20, 0, GOAL, g.GOAL_DONE),
    (20, 0, GOAL + 1, g.GOAL_DONE),
    (20, 0, int(GOAL * 0.95), g.GOAL_NEAR),
    (20, 3600, int(GOAL * 0.95) - 1, g.STUDIED),
    (20, 59, 0, g.NOT_YET),                 # 1분 미만은 공부 안 함
    (20, 60, 0, g.STUDIED),
])
def test_second_line_priority(hour, today, done, kind):
    assert g.second_kind(hour, today, GoalProgress(GOAL, done)) == kind


def test_no_goal_skips_goal_lines():
    assert g.second_kind(20, 0, NO_GOAL) == g.NOT_YET
    assert g.second_kind(20, 3600, GoalProgress(0, 10**6)) == g.STUDIED


def test_studied_line_shows_today_time():
    first, second = g.lines("민지", at(THU, 20), 5100, NO_GOAL, FIRSTS)
    assert second == "오늘 벌써 1시간 25분 공부했어요"
    assert g.lines("민지", at(THU, 20), 1500, NO_GOAL, SECONDS)[1] == "오늘도 25분 쌓았어요. 좋은 흐름이에요"


def test_picks_keep_text_fixed():
    picks = g.pick(random.Random(7))
    a = g.lines("민지", at(THU, 9), 0, NO_GOAL, picks)
    assert all(g.lines("민지", at(THU, 9), 0, NO_GOAL, picks) == a for _ in range(20))
