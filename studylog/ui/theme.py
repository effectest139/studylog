"""디자인(StudyLog v3)의 색·크기·글꼴 상수."""

from __future__ import annotations

import tkinter.font as tkfont

import customtkinter as ctk

# --- 색 ---
BG = "#F9FAFB"            # 창 배경
SURFACE = "#FFFFFF"       # 카드·사이드바·대화상자
BORDER = "#E5E7EB"
BORDER_STRONG = "#D1D5DB"
DIVIDER = "#F3F4F6"
GRAY_100 = "#F3F4F6"

TEXT = "#111827"
TEXT_SUB = "#374151"
MUTED = "#6B7280"
FAINT = "#9CA3AF"
GHOST = "#D1D5DB"         # 빈 값(0시간 0분), 잠긴 메뉴 글자

PRIMARY = "#4F46E5"
PRIMARY_HOVER = "#4338CA"
PRIMARY_SOFT = "#EEF2FF"
ACCENT = "#14B8A6"        # 청록: 연속일, 오늘, 증가, 재개
WARN = "#D97706"          # 감소

DANGER = "#DC2626"
DANGER_HOVER = "#B91C1C"
DANGER_SOFT = "#FEF2F2"
DANGER_TEXT = "#B91C1C"
DANGER_ICON_BG = "#FEE2E2"

DISABLED_BG = "#E5E7EB"
DISABLED_TEXT = "#9CA3AF"

# --- 크기 ---
WINDOW_W, WINDOW_H = 1100, 700
SIDEBAR_W = 200
CONTENT_PAD = 40
R_CARD = 12
R_CTRL = 8                # 버튼·입력칸·대화상자

# --- 글꼴 ---
# 한국어 Windows에서는 Tk가 "맑은 고딕"이라는 이름만 알고, 영어 Windows에서는 "Malgun Gothic"만 안다
_FONT_CANDIDATES = ("맑은 고딕", "Malgun Gothic")
FONT_FAMILY = "Malgun Gothic"
TIMER_FAMILY = "Consolas"

_font_cache: dict[tuple, ctk.CTkFont] = {}


def init_fonts(root) -> None:
    """Tk 창을 만든 직후 한 번 부른다(글꼴 목록은 창이 있어야 읽을 수 있음)."""
    global FONT_FAMILY
    families = set(tkfont.families(root))
    FONT_FAMILY = next((f for f in _FONT_CANDIDATES if f in families), "TkDefaultFont")
    # 글꼴을 따로 주지 않은 위젯도 맑은 고딕을 쓰게 한다
    ctk.ThemeManager.theme["CTkFont"]["family"] = FONT_FAMILY


def font(size: int, bold: bool = False) -> ctk.CTkFont:
    """맑은 고딕 글꼴. size는 디자인의 px 값 그대로."""
    return _cached(FONT_FAMILY, size, bold)


def timer_font(size: int, bold: bool = True) -> ctk.CTkFont:
    return _cached(TIMER_FAMILY, size, bold)


def _cached(family: str, size: int, bold: bool) -> ctk.CTkFont:
    key = (family, size, bold)
    if key not in _font_cache:
        _font_cache[key] = ctk.CTkFont(family=family, size=size,
                                       weight="bold" if bold else "normal")
    return _font_cache[key]
