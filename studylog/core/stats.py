"""공부 기록 집계. 모든 시간은 초 단위, 날짜는 기록을 시작한 날짜 기준."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

from .models import Session

STREAK_MIN_SECONDS = 60  # 하루에 1분 이상 기록이 있어야 연속일로 센다


def day_totals(sessions: Iterable[Session]) -> dict[date, int]:
    totals: dict[date, int] = defaultdict(int)
    for s in sessions:
        totals[s.day] += s.study_seconds
    return dict(totals)


def total_between(sessions: Iterable[Session], first: date, last: date) -> int:
    """first~last(둘 다 포함) 동안의 공부 시간."""
    return sum(s.study_seconds for s in sessions if first <= s.day <= last)


def week_start(d: date) -> date:
    """그 주의 월요일."""
    return d - timedelta(days=d.weekday())


def today_total(sessions: Iterable[Session], today: date) -> int:
    return total_between(sessions, today, today)


def week_total(sessions: Iterable[Session], today: date) -> int:
    """이번 주 월요일부터 오늘까지."""
    return total_between(sessions, week_start(today), today)


def subject_week_total(sessions: Iterable[Session], subject_id: str, today: date) -> int:
    return week_total((s for s in sessions if s.subject_id == subject_id), today)


def streak(sessions: Iterable[Session], today: date) -> int:
    """연속 공부일. 오늘 아직 기록이 없으면 어제까지 이어진 날 수를 보여 준다."""
    days = {d for d, sec in day_totals(sessions).items() if sec >= STREAK_MIN_SECONDS}
    d = today if today in days else today - timedelta(days=1)
    count = 0
    while d in days:
        count += 1
        d -= timedelta(days=1)
    return count


@dataclass(frozen=True)
class GoalProgress:
    goal_seconds: int
    done_seconds: int

    @property
    def has_goal(self) -> bool:
        return self.goal_seconds > 0

    @property
    def percent(self) -> int:
        """달성률(%). 목표를 넘으면 100보다 커질 수 있다."""
        if not self.has_goal:
            return 0
        return int(self.done_seconds * 100 // self.goal_seconds)

    @property
    def ratio(self) -> float:
        """진행 막대용 0~1."""
        return min(1.0, self.done_seconds / self.goal_seconds) if self.has_goal else 0.0

    @property
    def remaining_seconds(self) -> int:
        return max(0, self.goal_seconds - self.done_seconds)


def goal_progress(done_seconds: int, goal_minutes: int) -> GoalProgress:
    return GoalProgress(goal_minutes * 60, done_seconds)


def sessions_by_day(sessions: Iterable[Session]) -> list[tuple[date, list[Session], int]]:
    """기록 화면용: (날짜, 그날 기록들, 그날 합계). 최근 날짜가 먼저, 하루 안에서도 늦게 시작한 기록이 먼저."""
    groups: dict[date, list[Session]] = defaultdict(list)
    for s in sessions:
        groups[s.day].append(s)
    return [(d, sorted(groups[d], key=lambda s: s.start, reverse=True),
             sum(s.study_seconds for s in groups[d]))
            for d in sorted(groups, reverse=True)]
