"""matplotlib 차트를 창에 넣는 도우미: 막대(요일별·주차별)와 도넛(과목별 비율)."""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib
from matplotlib import font_manager
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from . import theme as t
from .motion import Tween
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
    # 따로 그리지 않는다: 창에 배치되어 크기가 정해지면(<Configure>) matplotlib가 알아서 그린다.
    # 배치 전에 그리면 크기가 달라 버려지는 그리기(막대 차트 50ms)가 한 번 더 생긴다
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
    bars = ax.bar(xs, heights, width=bar_width, color=fills, edgecolor=t.SURFACE, linewidth=0)

    value_texts = []
    gap = ymax * 0.025
    for x, h, text in zip(xs, heights, value_labels):
        if text:
            value_texts.append((ax.text(x, h + gap, text, ha="center", va="bottom", fontsize=11,
                                        color=t.MUTED), h))

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
    fig.studylog_bars = _BarParts(list(bars), heights, value_texts, gap)
    return fig


def donut_chart(values: list[int], colors: list[str]) -> Figure:
    """12시 방향에서 시계 방향으로. 값이 없으면 회색 고리."""
    fig = new_figure()
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_facecolor(t.SURFACE)
    if not any(values):
        values, colors = [1], [t.BORDER]
    ring = dict(width=0.38, edgecolor=t.SURFACE, linewidth=2 if len(values) > 1 else 0)
    wedges, _ = ax.pie(values, colors=colors, startangle=90, counterclock=False, wedgeprops=ring)
    ax.set_aspect("equal")
    fig.studylog_wedges = [(w, w.theta1, w.theta2) for w in wedges]
    return fig


# --- 모션: 막대가 아래에서 위로 자라고, 도넛이 12시부터 시계 방향으로 채워진다 ---

MOTION_SECONDS = 0.45


@dataclass
class _BarParts:
    bars: list            # Rectangle
    heights: list[float]  # 다 자랐을 때 높이
    texts: list           # (값 글자, 그 막대 높이)
    gap: float            # 막대 끝과 값 글자 사이


class BarGrowth:
    """막대 차트 모션.

    막대 차트를 통째로 다시 그리면 한 프레임에 50ms쯤 걸려 버벅인다.
    그래서 막대가 없는 상태(축·글자만)를 한 번 그려 배경으로 저장해 두고,
    프레임마다 배경을 덮고 막대와 값 글자만 그려 붙인다(블리팅, 프레임당 3~4ms).
    """

    def __init__(self, canvas: FigureCanvasTkAgg):
        self.canvas = canvas
        self.parts: _BarParts = canvas.figure.studylog_bars
        self._background = None
        self._waiting = False  # 배경을 저장할 다음 그리기를 기다리는 중
        self._then = None      # 모션을 시작할 때 같이 부를 것(도넛을 막대와 같이 시작)
        self._tween = Tween(canvas.get_tk_widget(), MOTION_SECONDS, self._frame)
        canvas.mpl_connect("draw_event", self._on_draw)
        canvas.mpl_connect("resize_event", self._on_resize)
        self._apply(0.0)  # 처음 그려질 때부터 막대가 없게(다 자란 막대가 한 번 비치지 않게)

    def play(self, then=None) -> None:
        """then: 막대가 실제로 자라기 시작할 때 같이 부를 함수.

        처음에는 화면 배치가 끝나고 차트가 제 크기로 그려진 뒤에야 시작할 수 있다.
        화면을 만드는 동안 시작하면 앞부분 프레임이 밀려 끊겨 보인다.
        """
        self._tween.cancel()
        self._apply(0.0)
        self._then = then
        if self._background is not None:
            self._start()
        else:
            self._waiting = True
            if self.canvas.get_tk_widget().winfo_width() > 1:
                self.canvas.draw_idle()  # 이미 배치된 뒤(창 크기가 바뀐 뒤 다시 재생)
            # 아직 배치 전이면 배치되며 matplotlib가 그릴 때(_on_draw) 시작한다

    def _start(self) -> None:
        then, self._then = self._then, None
        self._tween.start()
        if then is not None:
            then()

    def _apply(self, p: float) -> None:
        for bar, h in zip(self.parts.bars, self.parts.heights):
            bar.set_height(h * p)
        for text, h in self.parts.texts:
            text.set_y(h * p + self.parts.gap)
            text.set_alpha(p)

    def _sized(self) -> bool:
        """그림 크기가 창 위젯 크기와 같아졌나(창에 배치되기 전의 첫 그리기는 크기가 다르다)."""
        widget = self.canvas.get_tk_widget()
        return self.canvas.get_width_height(physical=True) == (widget.winfo_width(), widget.winfo_height())

    def _on_draw(self, _event) -> None:
        if self._waiting and self._sized():
            self._waiting = False
            self._background = self.canvas.copy_from_bbox(self.canvas.figure.bbox)
            self.canvas.get_tk_widget().after_idle(self._start)

    def _on_resize(self, _event) -> None:
        # 창 크기가 바뀌면 저장한 배경이 맞지 않는다.
        # 아직 시작 전이면 그대로 기다리고(다음 그리기에서 배경 저장), 자라는 중이면 다 자란 모습으로 끝낸다
        self._background = None
        if self._tween.running:
            self._tween.cancel()
            self._apply(1.0)

    def _frame(self, p: float) -> None:
        if self._background is None:
            return
        self._apply(p)
        ax = self.canvas.figure.axes[0]
        self.canvas.restore_region(self._background)
        for bar in self.parts.bars:
            ax.draw_artist(bar)
        for text, _ in self.parts.texts:
            ax.draw_artist(text)
        self.canvas.blit(self.canvas.figure.bbox)


class DonutFill:
    """도넛 모션. 도넛은 작아서 통째로 다시 그려도 프레임당 3ms쯤이라 블리팅 없이 그린다."""

    def __init__(self, canvas: FigureCanvasTkAgg):
        self.canvas = canvas
        self.wedges = canvas.figure.studylog_wedges
        self._tween = Tween(canvas.get_tk_widget(), MOTION_SECONDS, self._frame)
        self._apply(0.0)

    def play(self) -> None:
        self._tween.start()

    def _apply(self, p: float) -> None:
        # 조각은 12시(90°)부터 시계 방향으로 이어져 있다: 90°-360°×p 아래쪽은 아직 안 보인다
        edge = 90 - 360 * p
        for wedge, theta1, theta2 in self.wedges:
            start = max(theta1, edge)
            wedge.set_visible(start < theta2)
            wedge.set_theta1(min(start, theta2))

    def _frame(self, p: float) -> None:
        self._apply(p)
        self.canvas.draw()
