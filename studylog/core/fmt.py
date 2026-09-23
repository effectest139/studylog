"""화면에 보여 줄 한국어 시간·날짜 형식."""

from __future__ import annotations

from datetime import date, datetime

WEEKDAYS = "월화수목금토일"


def duration(seconds: int, empty: str = "0분") -> str:
    """'1시간 25분', '1시간', '13분'. 초는 버린다."""
    h, m = divmod(max(0, int(seconds)) // 60, 60)
    if h and m:
        return f"{h}시간 {m}분"
    if h:
        return f"{h}시간"
    if m:
        return f"{m}분"
    return empty


def duration_hms(seconds: int) -> str:
    """'1시간 12분 45초' (공부 완료 화면)."""
    seconds = max(0, int(seconds))
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    parts = []
    if h:
        parts.append(f"{h}시간")
    if h or m:
        parts.append(f"{m}분")
    parts.append(f"{s}초")
    return " ".join(parts)


def duration_short(seconds: int) -> str:
    """차트 막대 위 값: '1h 30m', '2h', '45m'."""
    h, m = divmod(max(0, int(seconds)) // 60, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def clock(seconds: int) -> str:
    """타이머 숫자 '01:12:45'."""
    seconds = max(0, int(seconds))
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def time_of_day(dt: datetime) -> str:
    """'오후 7:30', '오전 12:05'."""
    ampm = "오전" if dt.hour < 12 else "오후"
    h = dt.hour % 12 or 12
    return f"{ampm} {h}:{dt.minute:02d}"


def time_range(start: datetime, end: datetime) -> str:
    return f"{time_of_day(start)} – {time_of_day(end)}"


def date_long(d: date) -> str:
    """'2026년 9월 23일 수요일' (홈 인사말 아래)."""
    return f"{d.year}년 {d.month}월 {d.day}일 {WEEKDAYS[d.weekday()]}요일"


def date_short(d: date, today: date | None = None) -> str:
    """'9월 23일 (수)', 오늘이면 뒤에 ' · 오늘'."""
    text = f"{d.month}월 {d.day}일 ({WEEKDAYS[d.weekday()]})"
    if today is not None and d == today:
        text += " · 오늘"
    return text


def date_range(a: date, b: date) -> str:
    """'9월 21일 – 9월 27일'."""
    return f"{a.month}월 {a.day}일 – {b.month}월 {b.day}일"


def month_title(d: date) -> str:
    return f"{d.year}년 {d.month}월"
