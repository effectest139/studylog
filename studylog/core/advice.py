"""학습 조언 카드(규칙 기반). 전체 기록에서 기록한 날이 3일 이상일 때만 만든다.

비교 문구는 같은 기간끼리: 이번 주 오늘까지 ↔ 지난주 같은 요일까지,
이번 달 오늘까지 ↔ 지난달 같은 날짜까지.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable

from . import fmt, stats
from .models import Session, Subject

MIN_RECORDED_DAYS = 3
MAX_CARDS = 3

# 카드 머리표 색(화면에서 tone으로 고른다)
PINK, TEAL, INDIGO, AMBER = "pink", "teal", "indigo", "amber"


@dataclass(frozen=True)
class Advice:
    tag: str
    tone: str
    title: str
    body: str


def _has_batchim(word: str) -> bool | None:
    """마지막 글자에 받침이 있으면 True. 한글이 아니면 None."""
    if not word:
        return None
    code = ord(word[-1]) - 0xAC00
    if 0 <= code < 11172:
        return code % 28 != 0
    return None


def josa(word: str, with_batchim: str, without: str) -> str:
    """josa('수학', '은', '는') → '수학은'. 한글이 아닌 글자로 끝나면 '은(는)'."""
    b = _has_batchim(word)
    if b is None:
        return f"{word}{with_batchim}({without})"
    return word + (with_batchim if b else without)


def ieyo(word: str) -> str:
    """'1시간' → '1시간이에요', '국어' → '국어예요'."""
    return josa(word, "이에요", "예요")


def build(period: str, sessions: list[Session], subjects: list[Subject], today: date) -> list[Advice]:
    """period: 'week' 또는 'month'. 조건이 안 되면 빈 목록."""
    if stats.recorded_days(sessions) < MIN_RECORDED_DAYS:
        return []
    rules: list[Callable[[], Advice | None]]
    if period == "week":
        rules = [lambda: _week_weak_subject(sessions, subjects, today),
                 lambda: _week_best_day(sessions, today),
                 lambda: _week_compare(sessions, today),
                 lambda: _steady(sessions, today, stats.week_start(today), "이번 주")]
    else:
        rules = [lambda: _month_best_week(sessions, today),
                 lambda: _month_weak_subject(sessions, subjects, today),
                 lambda: _month_compare(sessions, today),
                 lambda: _steady(sessions, today, today.replace(day=1), "이번 달")]
    cards = []
    for rule in rules:
        card = rule()
        if card is not None:
            cards.append(card)
        if len(cards) == MAX_CARDS:
            break
    return cards


def _subject_totals(sessions, subjects, first: date, last: date) -> list[tuple[Subject, int]]:
    totals: dict[str, int] = defaultdict(int)
    for s in sessions:
        if first <= s.day <= last:
            totals[s.subject_id] += s.study_seconds
    return [(sub, totals.get(sub.id, 0)) for sub in subjects]


# --- 주간 ---

def _week_weak_subject(sessions, subjects, today) -> Advice | None:
    if len(subjects) < 2:
        return None
    rows = _subject_totals(sessions, subjects, stats.week_start(today), today)
    sub, sec = min(rows, key=lambda r: r[1])
    name = sub.name
    title = f"이번 주 {name} 기록이 없어요" if sec == 0 else f"{name} 시간이 가장 적어요"
    status = "" if sec == 0 else f"이번 주 {josa(name, '은', '는')} {ieyo(fmt.duration(sec))}. "

    days_left = 7 - today.weekday()  # 오늘 포함 남은 날
    remaining = sub.weekly_goal_minutes * 60 - sec
    if sub.weekly_goal_minutes and remaining > 0:
        if days_left == 1:
            tip = f"오늘 {josa(fmt.duration(remaining), '을', '를')} 채우면 주간 목표에 닿아요."
        else:
            per_day = fmt.duration(math.ceil(remaining / days_left / 60) * 60)
            tip = f"하루 {per_day}씩 더하면 주간 목표에 닿을 수 있어요."
    elif sec == 0:
        tip = "짧게라도 시작해 보세요. 하루 15분이면 충분해요."
    else:
        tip = "하루 15분씩 더해 보세요."
    return Advice("부족한 과목", PINK, title, status + tip)


def _week_best_day(sessions, today) -> Advice | None:
    days = [(d, sec) for d, sec in stats.week_days(sessions, today) if d <= today and sec > 0]
    if not days:
        return None
    d, sec = max(days, key=lambda x: x[1])
    wd = fmt.WEEKDAYS[d.weekday()]
    when = "오늘" if d == today else f"{wd}요일에"
    return Advice("집중한 날", TEAL, f"{when} 가장 오래 공부했어요",
                  f"{'오늘' if d == today else wd + '요일'} {fmt.duration(sec)} 기록이 이번 주 최고예요. "
                  "그날처럼 꾸준히 이어가 보세요.")


def _week_compare(sessions, today) -> Advice | None:
    c = stats.compare_week(sessions, today)
    if c.current == 0 and c.previous == 0:
        return None
    upto = f"월~{fmt.WEEKDAYS[today.weekday()]}요일"
    return _compare_card(c, "지난주 비교", "지난주 같은 요일", f"지난주 {upto}", f"이번 주 {upto}")


# --- 월간 ---

def _month_best_week(sessions, today) -> Advice | None:
    weeks = [(i + 1, a, b, sec) for i, (a, b, sec) in enumerate(stats.month_weeks(sessions, today))
             if a <= today and sec > 0]
    if not weeks:
        return None
    n, a, b, sec = max(weeks, key=lambda w: w[3])
    time = fmt.duration(sec)
    return Advice("최고 기록", TEAL, f"{n}주차에 가장 많이 공부했어요",
                  f"{n}주차({a.month}/{a.day}–{b.day}) {josa(time, '이', '가')} 이번 달 최고예요. "
                  "그 주의 공부 습관을 다시 이어가 보세요.")


def _month_weak_subject(sessions, subjects, today) -> Advice | None:
    if len(subjects) < 2:
        return None
    rows = _subject_totals(sessions, subjects, today.replace(day=1), today)
    total = sum(sec for _, sec in rows)
    if total == 0:
        return None
    sub, sec = min(rows, key=lambda r: r[1])
    if sec == 0:
        return Advice("부족한 과목", PINK, f"이번 달 {sub.name} 기록이 없어요",
                      "주 2회 30분씩이라도 시작해 보세요.")
    pct = round(sec * 100 / total)
    return Advice("부족한 과목", PINK, f"{sub.name} 비율이 {pct}%예요",
                  f"이번 달 {josa(sub.name, '은', '는')} {ieyo(fmt.duration(sec))}. "
                  "주 2회 30분씩 더해 보세요.")


def _month_compare(sessions, today) -> Advice | None:
    c = stats.compare_month(sessions, today)
    if c.current == 0 and c.previous == 0:
        return None
    upto = c.previous_range[1].day
    return _compare_card(c, "지난달 비교", "지난달 같은 날짜", f"지난달 1~{upto}일",
                         f"이번 달 1~{today.day}일")


# --- 공통 ---

def _compare_card(c: stats.Comparison, tag: str, basis: str, prev_label: str, cur_label: str) -> Advice:
    prev, cur, diff = fmt.duration(c.previous), fmt.duration(c.current), fmt.duration(abs(c.diff))
    if c.diff > 0:
        return Advice(tag, TEAL, f"{basis}보다 {diff} 늘었어요",
                      f"{prev_label} {prev}, {cur_label} {ieyo(cur)}. 이 흐름을 이어가 보세요.")
    if c.diff < 0:
        per_day = math.ceil(-c.diff / 7 / 60)
        return Advice(tag, AMBER, f"{basis}보다 {diff} 줄었어요",
                      f"{prev_label} {prev}, {cur_label} {ieyo(cur)}. "
                      f"앞으로 일주일 동안 하루 {per_day}분씩 더 하면 따라잡을 수 있어요.")
    return Advice(tag, INDIGO, f"{basis}와 같은 속도예요",
                  f"{prev_label}와 {cur_label} 모두 {ieyo(cur)}. 조금만 더 해 보세요.")


def _steady(sessions, today, first: date, label: str) -> Advice:
    streak = stats.streak(sessions, today)
    if streak >= 2:
        return Advice("꾸준함", INDIGO, f"{streak}일 연속으로 공부하고 있어요",
                      "내일도 이어가면 연속 기록이 늘어나요.")
    days = len({s.day for s in sessions if first <= s.day <= today})
    total_days = (today - first).days + 1
    return Advice("꾸준함", INDIGO, f"{label} {days}일 공부했어요",
                  f"{total_days}일 중 {days}일 기록이 있어요. 공부하는 날을 조금씩 늘려 보세요.")
