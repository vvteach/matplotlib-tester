# РЕШЕНИЕ
user_pgm = """
import matplotlib.pyplot as plt

k = int(input())
b = int(input())
x = [i for i in range(-10, 11)]
y = [i*k + b for i in range(-10, 11)]

plt.plot(x,y)
plt.show()
"""

# НАСТРОЙКИ
options = """
PRINT_LINES = 1
"""

##########################################################

#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
matplotlib_tester.py — перехватчик matplotlib (без настоящего matplotlib)

Идея:
- matplotlib НЕ импортируется и НЕ используется.
- Подсовываем пользователю "фейковый" модуль matplotlib.pyplot,
  который перехватывает plot/bar/pie/hist/title/xlabel/ylabel/legend/xticks/subplots/gca и т.п.
- Результат — только текстовый вывод print_ax(...).

ENV-флаги (0/1):
  PRINT_LINES
  PRINT_BARS
  PRINT_PIES
  PRINT_PIE_LABELS
  PRINT_XTICKS
  PRINT_TITLE
  PRINT_AXIS
  PRINT_LABELS

Опционально для проверки labels в pie:
  PIE_LABELS="A,B,C"
"""

import os
import sys
import types
import math
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


# ===== ENV helpers =====
def env_flag(name: str, default: str = "0") -> bool:
    v = os.environ.get(name, default).strip().lower()
    return v not in ("0", "false", "no", "")


def env_list(name: str, default: str = "") -> List[str]:
    raw = os.environ.get(name, default)
    if raw is None:
        return []
    s = str(raw).strip()
    if not s:
        return []
    s = s.replace(";", ",").replace(" ", ",")
    return [p for p in (x.strip() for x in s.split(",")) if p]


def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        return list(x)
    try:
        return list(x)
    except Exception:
        return [x]


def _round2(v: Any) -> Any:
    try:
        r = round(float(v), 2)
        return 0.0 if r == 0.0 else r
    except Exception:
        return v


# =========================
# Models
# =========================
@dataclass
class LineModel:
    xs: List[float]
    ys: List[float]
    label: str = "_nolegend_"
    marker: Optional[str] = None
    markersize: Optional[float] = None
    linestyle: Optional[str] = None


@dataclass
class RectModel:
    x: float
    y: float
    w: float
    h: float


@dataclass
class PieWedgeModel:
    theta1: float
    theta2: float
    center: Tuple[float, float] = (0.0, 0.0)
    r: float = 1.0


@dataclass
class PieLabelModel:
    text: str
    pos: Tuple[float, float]


@dataclass
class PieModel:
    values: List[float]
    labels: List[str]
    wedges: List[PieWedgeModel] = field(default_factory=list)
    label_texts: List[PieLabelModel] = field(default_factory=list)


@dataclass
class PlotState:
    lines: List[LineModel] = field(default_factory=list)
    rects: List[RectModel] = field(default_factory=list)
    pies: List[PieModel] = field(default_factory=list)

    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    xtick_labels: List[str] = field(default_factory=list)

    _current_axes: Any = None


STATE = PlotState()


# =========================
# Fake matplotlib.pyplot API
# =========================
class _FakeFigure:
    def __init__(self):
        self.axes = []

    def add_axes(self, ax: Any) -> None:
        self.axes.append(ax)


class _FakeAxes:
    def plot(self, *args, **kwargs):
        return _pyplot_plot(*args, **kwargs)

    def bar(self, *args, **kwargs):
        return _pyplot_bar(*args, **kwargs)

    def pie(self, *args, **kwargs):
        return _pyplot_pie(*args, **kwargs)

    def hist(self, *args, **kwargs):
        return _pyplot_hist(*args, **kwargs)

    def set_title(self, s: str):
        STATE.title = str(s)

    def set_xlabel(self, s: str):
        STATE.xlabel = str(s)

    def set_ylabel(self, s: str):
        STATE.ylabel = str(s)

    def legend(self, *args, **kwargs):
        return None

    def set_xticklabels(self, labels):
        STATE.xtick_labels = [str(x) for x in _as_list(labels)]

    # чтобы ax.scatter / ax.fill / ax.imshow и т.п. не ломали тестер
    def __getattr__(self, name):
        def _dummy(*args, **kwargs):
            return None
        return _dummy


def _ensure_axes() -> _FakeAxes:
    if STATE._current_axes is None:
        STATE._current_axes = _FakeAxes()
    return STATE._current_axes


def subplots(*args, **kwargs):
    fig = _FakeFigure()
    ax = _FakeAxes()
    fig.add_axes(ax)
    STATE._current_axes = ax
    return fig, ax


def gca():
    return _ensure_axes()


def gcf():
    return _FakeFigure()


def show(*args, **kwargs):
    return None


def savefig(*args, **kwargs):
    return None


def title(s: str):
    STATE.title = str(s)


def xlabel(s: str):
    STATE.xlabel = str(s)


def ylabel(s: str):
    STATE.ylabel = str(s)


def legend(*args, **kwargs):
    return None


def xticks(ticks=None, labels=None, *args, **kwargs):
    if labels is not None:
        STATE.xtick_labels = [str(x) for x in _as_list(labels)]
    return None


def _pyplot_plot(*args, **kwargs):
    label = kwargs.get("label", "_nolegend_")
    marker = kwargs.get("marker", None)
    markersize = kwargs.get("markersize", None)
    linestyle = kwargs.get("linestyle", None)

    if len(args) == 1:
        ys = _as_list(args[0])
        xs = list(range(len(ys)))
    elif len(args) >= 2:
        xs = _as_list(args[0])
        ys = _as_list(args[1])
    else:
        xs, ys = [], []

    m = min(len(xs), len(ys))
    xs = xs[:m]
    ys = ys[:m]

    STATE.lines.append(
        LineModel(
            xs=[float(x) for x in xs],
            ys=[float(y) for y in ys],
            label=str(label),
            marker=None if marker is None else str(marker),
            markersize=None if markersize is None else float(markersize),
            linestyle=None if linestyle is None else str(linestyle),
        )
    )
    return None


def _pyplot_bar(x, height=None, width=0.8, *args, **kwargs):
    xs = _as_list(x)
    hs = _as_list(height)

    if xs and all(isinstance(v, str) for v in xs):
        STATE.xtick_labels = [str(v) for v in xs]
        xs_num = list(range(len(xs)))
    else:
        xs_num = [float(v) for v in xs]

    m = min(len(xs_num), len(hs))
    xs_num = xs_num[:m]
    hs = hs[:m]

    w = float(width) if width is not None else 0.8
    for xc, h in zip(xs_num, hs):
        left = float(xc) - w / 2.0
        hh = float(h)
        STATE.rects.append(RectModel(x=left, y=0.0, w=w, h=hh))
    return None


def _pyplot_hist(x, bins=10, *args, **kwargs):
    """
    Поддерживаем базовые варианты:
      hist(data)
      hist(data, bins=5)
      hist(data, bins=[0, 1, 3, 10])

    Результат сохраняем как прямоугольники в STATE.rects,
    чтобы print_ax(bars=True) их печатал.
    """
    data = [float(v) for v in _as_list(x)]
    if not data:
        return None

    if isinstance(bins, int):
        if bins <= 0:
            return None

        mn = min(data)
        mx = max(data)

        if mn == mx:
            left = mn - 0.5
            right = mx + 0.5
            step = (right - left) / bins
            edges = [left + i * step for i in range(bins + 1)]
        else:
            step = (mx - mn) / bins
            edges = [mn + i * step for i in range(bins + 1)]
    else:
        edges = [float(v) for v in _as_list(bins)]
        if len(edges) < 2:
            return None
        bins = len(edges) - 1

    counts = [0] * bins

    for v in data:
        placed = False
        for i in range(bins):
            left = edges[i]
            right = edges[i + 1]

            if i == bins - 1:
                if left <= v <= right:
                    counts[i] += 1
                    placed = True
                    break
            else:
                if left <= v < right:
                    counts[i] += 1
                    placed = True
                    break

        if not placed and v == edges[-1]:
            counts[-1] += 1

    for i in range(bins):
        left = edges[i]
        right = edges[i + 1]
        width = right - left
        height = counts[i]
        STATE.rects.append(RectModel(x=left, y=0.0, w=width, h=float(height)))

    return counts, edges, None


def _pyplot_pie(x, *args, **kwargs):
    vals = [float(v) for v in _as_list(x)]
    labels = [str(t) for t in _as_list(kwargs.get("labels", []))]

    total = sum(vals) if vals else 0.0

    startangle = float(kwargs.get("startangle", 0.0))
    counterclock = bool(kwargs.get("counterclock", True))
    labeldistance = float(kwargs.get("labeldistance", 1.1))

    if total != 0:
        angles = [v / total * 360.0 for v in vals]
    else:
        angles = [0.0 for _ in vals]

    wedges: List[PieWedgeModel] = []
    theta = startangle

    for ang in angles:
        if counterclock:
            t1 = theta
            t2 = theta + ang
            theta = t2
        else:
            t1 = theta
            t2 = theta - ang
            theta = t2
            if t2 < t1:
                t1, t2 = t2, t1

        wedges.append(PieWedgeModel(theta1=t1, theta2=t2))

    label_texts: List[PieLabelModel] = []
    for i, w in enumerate(wedges):
        txt = labels[i] if i < len(labels) else ""
        mid = (w.theta1 + w.theta2) / 2.0
        rad = math.radians(mid)
        px = labeldistance * math.cos(rad)
        py = labeldistance * math.sin(rad)
        label_texts.append(PieLabelModel(text=txt, pos=(px, py)))

    STATE.pies.append(PieModel(values=vals, labels=labels, wedges=wedges, label_texts=label_texts))
    return None


# =========================
# Text output inspector
# =========================
def print_ax(lines=False, bars=False, pies=False,
             pie_labels=False,
             xticks=False,
             title=False, axis_labels=False, plot_labes=False):

    if lines:
        print('На холсте найдено линий: {}.'.format(len(STATE.lines)))
        for i, ln in enumerate(STATE.lines, start=1):
            print('*' * 12 + str(i).center(7) + '*' * 12)
            for j, (x, y) in enumerate(zip(ln.xs, ln.ys)):
                print('Л.{},т.{:03}: ({:+7.2f},{:+7.2f})'.format(i, j, _round2(x), _round2(y)))

    if bars:
        if STATE.rects:
            print('На холсте найдено прямоугольников (bar/rect): {}.'.format(len(STATE.rects)))
            for i, r in enumerate(STATE.rects, start=1):
                print('*' * 12 + str(i).center(7) + '*' * 12)
                print('B.{}, x={:+7.2f}, y={:+7.2f}, w={:+7.2f}, h={:+7.2f}'
                      .format(i, _round2(r.x), _round2(r.y), _round2(r.w), _round2(r.h)))
        else:
            print('Прямоугольников (bar/rect) не найдено.')

    if pies:
        if STATE.pies:
            pie = STATE.pies[-1]
            wedges = pie.wedges
            print('На холсте найдено секторов pie (Wedge): {}.'.format(len(wedges)))
            for i, w in enumerate(wedges, start=1):
                print('*' * 12 + str(i).center(7) + '*' * 12)
                print('P.{}, center=({:+7.2f},{:+7.2f}), r={:+7.2f}, theta1={:+7.2f}, theta2={:+7.2f}'
                      .format(i, w.center[0], w.center[1], w.r, _round2(w.theta1), _round2(w.theta2)))
        else:
            print('Секторов pie (Wedge) не найдено.')

    if pie_labels:
        if STATE.pies and STATE.pies[-1].label_texts:
            print('===== PIE LABELS =====')
            for i, t in enumerate(STATE.pies[-1].label_texts, start=1):
                x, y = t.pos
                print('PL.{:02}: pos=({:+7.2f},{:+7.2f}) text={}'.format(
                    i, _round2(x), _round2(y), repr(t.text)
                ))

            required = env_list("PIE_LABELS", "")
            if required:
                texts = [t.text for t in STATE.pies[-1].label_texts]
                missing = [lbl for lbl in required if lbl not in texts]
                if missing:
                    print('❌ PIE_LABELS: отсутствуют подписи:', ', '.join(repr(x) for x in missing))
                else:
                    print('✅ PIE_LABELS: все подписи найдены.')
        else:
            print('PIE LABELS не найдены.')

    if xticks:
        if STATE.xtick_labels:
            print('Подписи по оси X (xtick labels): {}'.format(len(STATE.xtick_labels)))
            for i, t in enumerate(STATE.xtick_labels, start=1):
                print('X.{:02}: {}'.format(i, repr(t)))
        else:
            print('Подписей по оси X нет.')

    if title:
        print('Заголовок:', STATE.title)

    if axis_labels:
        print('Подпись оси x:', STATE.xlabel)
        print('Подпись оси y:', STATE.ylabel)

    if plot_labes:
        for i, ln in enumerate(STATE.lines, start=1):
            print('Подписи линии {}: {}'.format(i, repr(ln.label)))


# =========================
# Module injection for user code
# =========================
def _install_fake_matplotlib() -> None:
    """
    Делает так, чтобы:
      import matplotlib.pyplot as plt
    импортировал наш фейковый pyplot.

    Плюс: любые неизвестные команды matplotlib/pyplot/patches игнорируются.
    """
    matplotlib_mod = types.ModuleType("matplotlib")
    pyplot_mod = types.ModuleType("matplotlib.pyplot")
    patches_mod = types.ModuleType("matplotlib.patches")

    pyplot_mod.subplots = subplots
    pyplot_mod.gca = gca
    pyplot_mod.gcf = gcf
    pyplot_mod.show = show
    pyplot_mod.savefig = savefig
    pyplot_mod.plot = _pyplot_plot
    pyplot_mod.bar = _pyplot_bar
    pyplot_mod.pie = _pyplot_pie
    pyplot_mod.hist = _pyplot_hist
    pyplot_mod.title = title
    pyplot_mod.xlabel = xlabel
    pyplot_mod.ylabel = ylabel
    pyplot_mod.legend = legend
    pyplot_mod.xticks = xticks

    class Rectangle:
        pass

    class Wedge:
        pass

    patches_mod.Rectangle = Rectangle
    patches_mod.Wedge = Wedge

    def _dummy(*args, **kwargs):
        return None

    def _module_getattr(name):
        return _dummy

    pyplot_mod.__getattr__ = _module_getattr
    patches_mod.__getattr__ = _module_getattr
    matplotlib_mod.__getattr__ = _module_getattr

    matplotlib_mod.pyplot = pyplot_mod
    matplotlib_mod.patches = patches_mod

    sys.modules["matplotlib"] = matplotlib_mod
    sys.modules["matplotlib.pyplot"] = pyplot_mod
    sys.modules["matplotlib.patches"] = patches_mod


if __name__ == "__main__":
    PRINT_LINES = env_flag("PRINT_LINES")
    PRINT_BARS = env_flag("PRINT_BARS")
    PRINT_PIES = env_flag("PRINT_PIES")
    PRINT_PIE_LABELS = env_flag("PRINT_PIE_LABELS")
    PRINT_XTICKS = env_flag("PRINT_XTICKS")
    PRINT_TITLE = env_flag("PRINT_TITLE")
    PRINT_AXIS = env_flag("PRINT_AXIS")
    PRINT_LABELS = env_flag("PRINT_LABELS")

    user_pgm = sys.argv[1]

    with open(user_pgm, "r", encoding="utf-8") as f:
        code_lines = f.read().splitlines()

    for i in range(len(code_lines) - 1, -1, -1):
        line = code_lines[i]
        if ".show()" in line:
            code_lines.pop(i)
        elif "exec" in line:
            code_lines.pop(i)

    _install_fake_matplotlib()

    sys.modules["matplotlib_tester"] = sys.modules[__name__]

    code_lines.append(
        f'print_ax({PRINT_LINES}, {PRINT_BARS}, {PRINT_PIES}, '
        f'{PRINT_PIE_LABELS}, {PRINT_XTICKS}, {PRINT_TITLE}, '
        f'{PRINT_AXIS}, {PRINT_LABELS})'
    )

    code = "\n".join(code_lines)
    exec(compile(code, user_pgm, "exec"), globals())