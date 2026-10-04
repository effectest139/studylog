"""matplotlib 차트를 창에 넣는 도우미: 막대(요일별·주차별)와 도넛(과목별 비율)."""

from __future__ import annotations

import matplotlib
from matplotlib import font_manager
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from . import theme as t
from .widgets.common import widget_scaling

# dpi 72면 matplotlib의 글자 크기(pt)가 디자인 px와 같아진다(Windows 배율은 matplotlib가 곱해 줌)
DPI = 72
_fonts_ready = False


def setup_fonts() -> None:
    """한글이 깨지지 않게 맑은 고딕을 쓴다. 없으면 기본 글꼴."""
    global _fonts_ready
    if _fonts_ready:
        return
    names = {f.name for f in font_manager.fontManager.ttflist}
    matplotlib.rcParams["font.family"] = ["Malgun Gothic"] if "Malgun Gothic" in names else ["sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    _fonts_ready = True


def embed(fig: Figure, master, height: int) -> FigureCanvasTkAgg:
    """Figure를 tk 위젯으로 넣는다. 폭은 부모를 따라 늘고 높이는 height(디자인 px)."""
    canvas = FigureCanvasTkAgg(fig, master=master)
    widget = canvas.get_tk_widget()
    widget.configure(height=round(height * widget_scaling(master)), highlightthickness=0,
                     bd=0, bg=t.SURFACE)
    canvas.draw_idle()
    return canvas


def new_figure() -> Figure:
    setup_fonts()
    return Figure(dpi=DPI, facecolor=t.SURFACE)


def bar_chart(values: list[int], labels: list[str], colors: list[str], value_labels: list[str],
              sub_labels: list[str] | None = None, empty_text: str | None = None,
              bar_width: float = 0.42) -> Figure:
    """values가 0인 막대는 연한 회색의 낮은 막대(자리 표시)로 그린다.

    value_labels의 빈 문자열은 글자를 쓰지 않는다.
    """
    fig = new_figure()
    bottom = 0.26 if sub_labels else 0.16
    ax = fig.add_axes((0.02, bottom, 0.96, 0.98 - bottom))
    ax.set_facecolor(t.SURFACE)

    top = max(values) if any(values) else 1
    ymax = top * 1.22
    stub = ymax * 0.025
    xs = range(len(values))
    heights = [v if v > 0 else stub for v in values]
    fills = [c if v > 0 else t.BORDER for v, c in zip(values, colors)]
    ax.bar(xs, heights, width=bar_width, color=fills, edgecolor=t.SURFACE, linewidth=0)

    for x, h, text in zip(xs, heights, value_labels):
        if text:
            ax.text(x, h + ymax * 0.025, text, ha="center", va="bottom", fontsize=11, color=t.MUTED)

    ax.set_ylim(0, ymax)
    ax.set_xlim(-0.6, len(values) - 0.4)
    ax.set_yticks([])
    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels, fontsize=13, color=t.TEXT_SUB if sub_labels else t.MUTED)
    ax.tick_params(axis="x", length=0, pad=8)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(t.BORDER)

    if sub_labels:
        trans = ax.get_xaxis_transform()  # x는 데이터, y는 축 비율
        for x, text in zip(xs, sub_labels):
            ax.text(x, -0.2, text, transform=trans, ha="center", va="top", fontsize=11, color=t.MUTED)
    if empty_text:
        ax.text(0.5, 0.5, empty_text, transform=ax.transAxes, ha="center", va="center",
                fontsize=14, color=t.MUTED)
    return fig


def donut_chart(values: list[int], colors: list[str]) -> Figure:
    """12시 방향에서 시계 방향으로. 값이 없으면 회색 고리."""
    fig = new_figure()
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_facecolor(t.SURFACE)
    if not any(values):
        values, colors = [1], [t.BORDER]
    ring = dict(width=0.38, edgecolor=t.SURFACE, linewidth=2 if len(values) > 1 else 0)
    ax.pie(values, colors=colors, startangle=90, counterclock=False, wedgeprops=ring)
    ax.set_aspect("equal")
    return fig
