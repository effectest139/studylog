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


# --- 분석 화면 ---

def week_days(sessions: Iterable[Session], today: date) -> list[tuple[date, int]]:
    """이번 주 월~일 7일의 (날짜, 공부 시간). 오늘 이후 날은 0."""
    totals = day_totals(sessions)
    monday = week_start(today)
    return [(monday + timedelta(days=i), totals.get(monday + timedelta(days=i), 0)) for i in range(7)]


def month_last_day(d: date) -> date:
    nxt = date(d.year + d.month // 12, d.month % 12 + 1, 1)
    return nxt - timedelta(days=1)


def month_weeks(sessions: Iterable[Session], today: date) -> list[tuple[date, date, int]]:
    """이번 달을 1~7일, 8~14일 … 7일씩 나눈 주차별 (첫날, 끝날, 공부 시간)."""
    sessions = list(sessions)
    first = today.replace(day=1)
    last = month_last_day(today)
    weeks = []
    start = first
    while start <= last:
        end = min(start + timedelta(days=6), last)
        weeks.append((start, end, total_between(sessions, start, end)))
        start = end + timedelta(days=1)
    return weeks


@dataclass(frozen=True)
class Comparison:
    """같은 기간끼리 비교: 이번 기간(오늘까지) ↔ 지난 기간(같은 요일·날짜까지)."""
    current: int
    previous: int
    current_range: tuple[date, date]
    previous_range: tuple[date, date]

    @property
    def diff(self) -> int:
        return self.current - self.previous


def compare_week(sessions: Iterable[Session], today: date) -> Comparison:
    sessions = list(sessions)
    monday = week_start(today)
    prev_monday = monday - timedelta(days=7)
    prev_same = today - timedelta(days=7)
    return Comparison(total_between(sessions, monday, today),
                      total_between(sessions, prev_monday, prev_same),
                      (monday, today), (prev_monday, prev_same))


def compare_month(sessions: Iterable[Session], today: date) -> Comparison:
    """지난달에 같은 날짜가 없으면(예: 3/31 ↔ 2월) 지난달 말일까지."""
    sessions = list(sessions)
    first = today.replace(day=1)
    prev_last_day = first - timedelta(days=1)
    prev_first = prev_last_day.replace(day=1)
    prev_same = prev_first.replace(day=min(today.day, prev_last_day.day))
    return Comparison(total_between(sessions, first, today),
                      total_between(sessions, prev_first, prev_same),
                      (first, today), (prev_first, prev_same))


def subject_shares(sessions: Iterable[Session], first: date, last: date) -> list[tuple[str, int]]:
    """기간 안의 과목별 (subject_id, 공부 시간). 시간이 많은 순, 0인 과목은 뺀다."""
    totals: dict[str, int] = defaultdict(int)
    for s in sessions:
        if first <= s.day <= last:
            totals[s.subject_id] += s.study_seconds
    return sorted(((sid, sec) for sid, sec in totals.items() if sec > 0), key=lambda x: -x[1])


def recorded_days(sessions: Iterable[Session]) -> int:
    """기록이 있는 날짜 수(전체 기록 기준). 학습 조언은 3일 이상일 때만 보여 준다."""
    return len({s.day for s in sessions})
