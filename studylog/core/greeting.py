"""홈 인사말 두 줄: 첫째 줄은 시간대(가끔 요일) 인사, 둘째 줄은 진행 상황 한마디.

문구 후보 중 무엇을 쓸지는 앱을 켤 때 pick()으로 한 번 정해 두고(Picks),
화면을 다시 그릴 때는 같은 Picks로 lines()를 불러 문구가 바뀌지 않게 한다.
시간대와 '오늘 ○시간 ○분' 같은 값은 그때그때 계산한다.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime

from . import fmt
from .stats import GoalProgress

MORNING, AFTERNOON, EVENING, NIGHT = "morning", "afternoon", "evening", "night"

# {name}은 사용자 이름
FIRST = {
    MORNING: ("좋은 아침이에요, {name}님", "상쾌한 아침이네요, {name}님"),          # 05~11시
    AFTERNOON: ("좋은 오후예요, {name}님", "오후도 힘내요, {name}님"),              # 11~17시
    EVENING: ("좋은 저녁이에요, {name}님", "오늘 하루 어땠어요, {name}님?"),        # 17~22시
    NIGHT: ("늦은 시간이네요, {name}님", "밤늦게까지 수고 많아요, {name}님"),       # 22~05시
}
WEEKDAY_FIRST = {  # date.weekday(): 금 4, 일 6
    4: "즐거운 금요일이에요, {name}님",
    6: "여유로운 일요일이에요, {name}님",
}
WEEKDAY_CHANCE = 1 / 3  # 금·일요일에 요일 인사를 쓸 확률

# 둘째 줄: 위에서부터 먼저 맞는 조건 하나. {time}은 오늘 공부한 시간
LATE_NIGHT = "late_night"   # 새벽 1~5시
GOAL_DONE = "goal_done"     # 주간 목표 달성
GOAL_NEAR = "goal_near"     # 주간 목표 95% 이상
NOT_YET = "not_yet"         # 오늘 아직 공부 안 함
STUDIED = "studied"         # 오늘 공부함
SECOND = {
    LATE_NIGHT: ("오늘은 여기까지 하고 푹 쉬어요", "내일을 위해 잠도 챙겨요"),
    GOAL_DONE: ("이번 주 목표 달성! 정말 잘했어요", "목표를 채웠어요. 오늘은 가볍게 가도 좋아요"),
    GOAL_NEAR: ("목표까지 거의 다 왔어요. 조금만 더 힘내요!", "한 번만 더 하면 목표 달성이에요"),
    NOT_YET: ("오늘 첫 공부를 시작해 볼까요?", "가벼운 과목부터 시작해 봐요"),
    STUDIED: ("오늘 벌써 {time} 공부했어요", "오늘도 {time} 쌓았어요. 좋은 흐름이에요"),
}
GOAL_NEAR_RATIO = 0.95


@dataclass(frozen=True)
class Picks:
    """앱을 켤 때 고른 문구 번호들. 키는 FIRST/SECOND의 키."""
    variants: dict[str, int] = field(default_factory=dict)
    weekday: bool = False  # 금·일요일이면 시간대 인사 대신 요일 인사

    def text(self, options: dict[str, tuple[str, ...]], key: str) -> str:
        choices = options[key]
        return choices[self.variants.get(key, 0) % len(choices)]


def pick(rng: random.Random | None = None) -> Picks:
    rng = rng or random.Random()
    variants = {key: rng.randrange(len(opts)) for key, opts in (*FIRST.items(), *SECOND.items())}
    return Picks(variants, weekday=rng.random() < WEEKDAY_CHANCE)


def time_slot(hour: int) -> str:
    """05~11시 아침, 11~17시 오후, 17~22시 저녁, 22~05시 밤(앞 시각 포함, 뒤 시각 미포함)."""
    if 5 <= hour < 11:
        return MORNING
    if 11 <= hour < 17:
        return AFTERNOON
    if 17 <= hour < 22:
        return EVENING
    return NIGHT


def second_kind(hour: int, today_seconds: int, goal: GoalProgress) -> str:
    """둘째 줄 조건. 주간 목표가 없으면 목표 조건(달성·95%)은 건너뛴다."""
    if 1 <= hour < 5:
        return LATE_NIGHT
    if goal.has_goal:
        if goal.done_seconds >= goal.goal_seconds:
            return GOAL_DONE
        if goal.done_seconds >= goal.goal_seconds * GOAL_NEAR_RATIO:
            return GOAL_NEAR
    # 1분 미만 기록은 저장되지 않으므로 '1분 미만'은 공부하지 않은 것과 같다
    return STUDIED if today_seconds >= 60 else NOT_YET


def lines(name: str, now: datetime, today_seconds: int, goal: GoalProgress, picks: Picks) -> tuple[str, str]:
    """(첫째 줄, 둘째 줄)."""
    weekday = now.weekday()
    if picks.weekday and weekday in WEEKDAY_FIRST:
        first = WEEKDAY_FIRST[weekday]
    else:
        first = picks.text(FIRST, time_slot(now.hour))
    second = picks.text(SECOND, second_kind(now.hour, today_seconds, goal))
    return first.format(name=name), second.format(time=fmt.duration(today_seconds))
