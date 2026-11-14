import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from datetime import datetime  # noqa: E402

_KR_FONTS = ["Malgun Gothic", "NanumGothic", "NanumBarunGothic", "Noto Sans CJK KR", "AppleGothic"]


def _setup_font():
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in _KR_FONTS:
        if name in available:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


_setup_font()

INK, MUTED, ACCENT, ACCENT2 = "#1f2933", "#7b8794", "#2563eb", "#f59e0b"


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9)
    ax.grid(axis="y", color="#e4e7eb", linewidth=0.8)
    ax.set_axisbelow(True)


def gu_trend(trend: list[tuple[str, int, float]], title: str, path, figsize=(8, 4.2)) -> None:
    labels = [f"{ym[2:4]}.{ym[4:]}" for ym, _, _ in trend]
    counts = [n for _, n, _ in trend]
    meds = [m / 10000 for _, _, m in trend]
    fig, ax = plt.subplots(figsize=figsize, dpi=110)
    _style(ax)
    ax.bar(labels, counts, color="#bfdbfe", label="거래 건수")
    ax.set_ylabel("거래 건수", color=INK)
    ax2 = ax.twinx()
    ax2.plot(labels, meds, color=ACCENT, marker="o", linewidth=2, label="중위 거래가(억원)")
    ax2.set_ylabel("중위 거래가 (억원)", color=ACCENT)
    ax2.spines["top"].set_visible(False)
    ax2.tick_params(colors=ACCENT, labelsize=9)
    ax.set_title(title, color=INK, fontsize=12, loc="left")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False, fontsize=9)
    fig.text(0.99, 0.01, "자료: 국토교통부 실거래가 공개시스템", ha="right", fontsize=7, color=MUTED)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def complex_scatter(points: list[tuple[str, int, int]], title: str, path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=110)
    _style(ax)
    by_area: dict[int, list] = {}
    for d, p, a in points:
        by_area.setdefault(a, []).append((datetime.strptime(d, "%Y-%m-%d"), p / 10000))
    palette = [ACCENT, ACCENT2, "#10b981", "#ef4444", "#8b5cf6", "#0ea5e9", "#84cc16"]
    for i, (a, pts) in enumerate(sorted(by_area.items(), key=lambda kv: -len(kv[1]))[:7]):
        xs, ys = zip(*pts)
        ax.scatter(xs, ys, s=28, color=palette[i], label=f"{a}㎡", alpha=0.85)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%y.%m"))
    ax.set_ylabel("거래금액 (억원)", color=INK)
    ax.set_title(title, color=INK, fontsize=12, loc="left")
    ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper left")
    fig.text(0.99, 0.01, "자료: 국토교통부 실거래가 공개시스템", ha="right", fontsize=7, color=MUTED)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
