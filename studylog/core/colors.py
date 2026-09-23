"""과목 색 팔레트와 호버 색 계산 (디자인 01-H 규칙)."""

from __future__ import annotations

PALETTE = (
    "#4F46E5", "#0EA5E9", "#F59E0B", "#EC4899", "#14B8A6", "#8B5CF6",
    "#22C55E", "#F97316", "#84CC16", "#06B6D4", "#EF4444", "#64748B",
)
TEXT_DARK = "#111827"


def _rgb(c: str) -> list[int]:
    return [int(c[i:i + 2], 16) for i in (1, 3, 5)]


def _hex(rgb) -> str:
    # 디자인(JS Math.round)과 같게 반올림한다. 파이썬 round()는 0.5를 짝수로 보내서 다름
    return "#" + "".join(f"{int(x + 0.5):02X}" for x in rgb)


def _luminance(c: str) -> float:
    v = [x / 255 for x in _rgb(c)]
    v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def contrast_ratio(a: str, b: str) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def tint(c: str) -> str:
    """호버 배경: 과목 색 10% + 흰색 90%."""
    return _hex(x * 0.1 + 255 * 0.9 for x in _rgb(c))


def dark(c: str) -> str:
    """'시작하기 →' 글자색: tint 배경과 대비 4.5:1 이상이 될 때까지 과목 색을 어둡게 한 색."""
    bg = tint(c)
    for i in range(3, 18):  # 15%부터 85%까지 5%씩
        k = i * 0.05
        d = _hex(x * (1 - k) for x in _rgb(c))
        if contrast_ratio(d, bg) >= 4.5:
            return d
    return TEXT_DARK


def next_unused(used: list[str] | tuple[str, ...]) -> str:
    """아직 안 쓴 첫 번째 색. 다 썼으면 순서대로 다시 쓴다."""
    used_set = {u.upper() for u in used}
    for c in PALETTE:
        if c not in used_set:
            return c
    return PALETTE[len(used) % len(PALETTE)]
