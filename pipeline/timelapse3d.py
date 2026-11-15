"""서울 25개 구 3D 타임랩스: 구별 평당 중위가를 3D 막대 지도로 세우고 월 순서대로 재생한다.

  python -m pipeline.timelapse3d --out out/seoul_3d.mp4 [--end 202609] [--months 12]

- 숫자 규칙: 화면의 모든 수치는 seoul_facts()가 DB에서 계산한 값(won() 문자열)만 쓴다.
- 신고 기한(계약 후 30일)이 끝나지 않은 달은 빼도록 기본 끝 달은 '이번 달 - 2개월'.
- 지도는 실제 경계가 아니라 구의 대략적 위치를 칸으로 배치한 도식(타일 지도)이다.
- 3D는 외부 라이브러리 없이 회전 + 등각 투영을 직접 계산해 Pillow로 그린다 (2배로 그린 뒤 축소해 계단 현상 제거).
"""
import argparse
import math
import statistics
import subprocess
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw

from .analyze import PYEONG, prev_ym, won
from .motion import FPS, THEMES, ease, _gradient
from .regions import SEOUL
from .render import W, H, font
from .tts import FFMPEG

# 구 이름 → (열, 행) 도식 배치 (북쪽이 위, 한강 이북 0~3행, 이남 3~5행)
TILES = {
    "은평구": (1, 0), "강북구": (3, 0), "도봉구": (4, 0), "노원구": (5, 0),
    "서대문구": (1, 1), "종로구": (2, 1), "성북구": (3, 1), "동대문구": (4, 1), "중랑구": (5, 1),
    "강서구": (0, 2), "마포구": (1, 2), "중구": (2, 2), "성동구": (3, 2), "광진구": (4, 2), "강동구": (5, 2),
    "양천구": (0, 3), "영등포구": (1, 3), "용산구": (2, 3),
    "구로구": (0, 4), "동작구": (1, 4), "서초구": (2, 4), "강남구": (3, 4), "송파구": (4, 4),
    "금천구": (0, 5), "관악구": (1, 5),
}
MIN_TRADES = 10        # 구·월 거래가 이보다 적으면 그 달 값은 비워 둔다 (중위가 신뢰도)
SOURCE = "자료: 국토교통부 아파트 매매 실거래가 · 계약월 기준 · 해제 거래 제외"


def default_end(today: date | None = None) -> str:
    today = today or date.today()
    return prev_ym(f"{today.year:04d}{today.month:02d}", 2)


def seoul_facts(conn, end_ym: str, months: int = 12) -> dict:
    """월별·구별 평당 중위가(만원)와 화면용 문자열. 모든 화면 수치의 유일한 출처."""
    yms = [end_ym]
    for _ in range(months - 1):
        yms.insert(0, prev_ym(yms[0]))
    vals: dict[str, dict[str, float]] = {}
    counts: dict[str, int] = {}
    for ym in yms:
        vals[ym] = {}
        n_total = 0
        for cd, (gu, _) in SEOUL.items():
            rows = conn.execute("SELECT price, area FROM trades WHERE canceled = 0 AND sgg_cd = ? AND deal_ym = ?",
                                (cd, ym)).fetchall()
            n_total += len(rows)
            if len(rows) >= MIN_TRADES:
                vals[ym][gu] = statistics.median(r["price"] / (r["area"] / PYEONG) for r in rows)
        counts[ym] = n_total
    yms = [ym for ym in yms if vals[ym]]
    if len(yms) < 2:
        raise ValueError("타임랩스에 쓸 달이 2개 미만입니다")
    last = vals[yms[-1]]
    rank = sorted(last.items(), key=lambda kv: -kv[1])
    facts = {
        "start_month": _ym(yms[0]), "end_month": _ym(yms[-1]),
        "top1_gu": rank[0][0], "top1_ppp": won(rank[0][1]),
        "low1_gu": rank[-1][0], "low1_ppp": won(rank[-1][1]),
        "trade_total": f"{sum(counts[ym] for ym in yms):,}건",
    }
    return {"months": yms, "values": vals, "counts": counts, "facts": facts}


def _ym(ym: str) -> str:
    return f"{ym[:4]}년 {int(ym[4:])}월"


# ---------------------------------------------------------------- 3D 투영

def project(x: float, y: float, z: float, angle: float, scale: float, cx: float, cy: float):
    """지도 좌표(x 동쪽, y 남쪽, z 위)를 회전 후 등각 투영한 화면 좌표와 깊이(클수록 앞)."""
    ca, sa = math.cos(angle), math.sin(angle)
    xr, yr = x * ca - y * sa, x * sa + y * ca
    sx = cx + (xr - yr) * scale * 0.866
    sy = cy + (xr + yr) * scale * 0.5 - z * scale
    return sx, sy, xr + yr


def _shade(rgb, k: float):
    return tuple(max(0, min(255, int(c * k))) for c in rgb)


def _hex(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _color(p: float, lo_rgb, hi_rgb):
    return tuple(int(lo_rgb[i] + (hi_rgb[i] - lo_rgb[i]) * p) for i in range(3))


def _hull(points):
    """볼록 껍질 (반시계)."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _inside(pt, hull) -> bool:
    n = len(hull)
    if n < 3:
        return False
    sign = None
    for i in range(n):
        a, b = hull[i], hull[(i + 1) % n]
        c = (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0])
        if c != 0:
            if sign is None:
                sign = c > 0
            elif (c > 0) != sign:
                return False
    return True


class Timelapse:
    HOLD_START, PER_MONTH, HOLD_END = 1.6, 1.5, 3.4

    def __init__(self, data: dict, theme: str = "midnight", site_title: str = "실거래가 리포트"):
        self.d, self.th = data, THEMES[theme]
        self.site_title = site_title
        self.months = data["months"]
        allv = [v for ym in self.months for v in data["values"][ym].values()]
        self.vmax = max(allv)
        self.vmin = min(allv)
        self.seconds = self.HOLD_START + self.PER_MONTH * (len(self.months) - 1) + self.HOLD_END
        self.grad = _gradient(self.th)
        self.lo_rgb, self.hi_rgb = _hex(self.th["bar"]), _hex(self.th["accent"])
        cols = [c for c, _ in TILES.values()]
        rows = [r for _, r in TILES.values()]
        self.mid = ((max(cols) + 1) / 2, (max(rows) + 1) / 2)

    def values_at(self, t: float) -> tuple[dict, int, float]:
        """시각 t의 구별 값(앞뒤 달 사이 보간), 현재 달 index, 전환 진행률."""
        u = (t - self.HOLD_START) / self.PER_MONTH
        i = max(0, min(len(self.months) - 1, int(math.floor(u)) if u > 0 else 0))
        frac = 0.0 if u <= 0 or i >= len(self.months) - 1 else ease((u - i) / 0.7)
        a = self.d["values"][self.months[i]]
        b = self.d["values"][self.months[min(i + 1, len(self.months) - 1)]]
        out = {}
        for gu in TILES:
            va, vb = a.get(gu), b.get(gu)
            if va is None and vb is None:
                continue
            va = vb if va is None else va
            vb = va if vb is None else vb
            out[gu] = va + (vb - va) * frac
        shown = i + 1 if frac > 0.5 else i
        return out, min(shown, len(self.months) - 1), frac

    # ------------------------------------------------------------ 그리기

    def _scene3d(self, vals: dict, angle: float, grow: float, highlight: set) -> Image.Image:
        S = 2                              # 2배로 그리고 축소
        sw, sh = W * S, 980 * S
        img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        scale, cx, cy = 106 * S, sw / 2, sh * 0.60
        mx, my = self.mid
        gap = 0.13
        boxes = []
        for gu, (c, r) in TILES.items():
            x0, y0 = c - mx + gap, r - my + gap
            x1, y1 = c + 1 - mx - gap, r + 1 - my - gap
            v = vals.get(gu)
            p = 0.0 if v is None else (v - self.vmin) / ((self.vmax - self.vmin) or 1)
            hgt = 0.0 if v is None else (0.35 + 4.2 * (v / self.vmax) ** 1.6) * grow
            depth = project((x0 + x1) / 2, (y0 + y1) / 2, 0, angle, 1, 0, 0)[2]
            boxes.append((depth, gu, x0, y0, x1, y1, hgt, p, v is None))
        # 바닥판
        floor = [project(x, y, 0, angle, scale, cx, cy)[:2] for x, y in
                 ((-mx - 0.25, -my - 0.25), (mx + 0.25, -my - 0.25), (mx + 0.25, my + 0.25), (-mx - 0.25, my + 0.25))]
        d.polygon(floor, fill=(*_hex(self.th["grid"]), 70))
        labels, hulls = [], []
        for depth, gu, x0, y0, x1, y1, hgt, p, empty in sorted(boxes):
            base = (90, 100, 115) if empty else _color(p, self.lo_rgb, self.hi_rgb)
            corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            bot = [project(x, y, 0, angle, scale, cx, cy) for x, y in corners]
            top = [project(x, y, hgt, angle, scale, cx, cy) for x, y in corners]
            # 옆면 4개: 앞쪽(깊이 큰) 면이 나중에 그려지게
            sides = []
            for k in range(4):
                j = (k + 1) % 4
                dep = (bot[k][2] + bot[j][2]) / 2
                poly = [bot[k][:2], bot[j][:2], top[j][:2], top[k][:2]]
                light = 0.62 if k % 2 == 0 else 0.80
                sides.append((dep, poly, light))
            for dep, poly, light in sorted(sides):
                d.polygon(poly, fill=(*_shade(base, light), 255))
            outline = (*_shade(base, 1.25), 255) if gu in highlight else None
            d.polygon([q[:2] for q in top], fill=(*_shade(base, 1.08), 255), outline=outline,
                      width=5 if outline else 0)
            tx = sum(q[0] for q in top) / 4
            ty = sum(q[1] for q in top) / 4
            labels.append((gu in highlight, depth, gu, tx, ty))
            hulls.append((depth, _hull([q[:2] for q in bot + top])))
        # 이름표: 상위 3개 구 먼저(크게), 나머지는 앞쪽부터. 이미 놓인 이름표와 겹치면 생략
        placed = []
        for hi, my_depth, gu, tx, ty in sorted(labels, key=lambda l: (not l[0], -l[1])):
            box = self._label_box(d, gu, tx, ty, (42 if hi else 30) * S, hi)
            if any(box[0] < o[2] and o[0] < box[2] and box[1] < o[3] and o[1] < box[3] for o in placed):
                continue
            # 더 앞에 있는 막대에 가려지는 이름표는 그 막대 이름으로 오해되므로 생략
            pts = [(box[0], ty), (tx, ty), (box[2], ty)]
            if any(dep > my_depth + 1e-9 and any(_inside(pt, h) for pt in pts) for dep, h in hulls):
                continue
            placed.append(box)
            self._label(d, gu, tx, ty, (42 if hi else 30) * S, hi, S)
        return img.resize((W, 980), Image.LANCZOS)

    @staticmethod
    def _label_box(d, gu, tx, ty, size, bold):
        name = gu[:-1] if len(gu) > 2 else gu
        f = font(size, bold)
        tw = d.textlength(name, font=f)
        pad = size * 0.15
        return (tx - tw / 2 - pad, ty - f.size * 0.6 - pad, tx + tw / 2 + pad, ty + f.size * 0.7 + pad)

    @staticmethod
    def _label(d, gu, tx, ty, size, bold, S):
        name = gu[:-1] if len(gu) > 2 else gu      # '구'는 빼고 짧게
        f = font(size, bold)
        tw = d.textlength(name, font=f)
        d.text((tx - tw / 2 + 2 * S, ty - f.size * 0.6 + 2 * S), name, font=f, fill=(0, 0, 0, 170))
        d.text((tx - tw / 2, ty - f.size * 0.6), name, font=f, fill=(255, 255, 255, 255))

    def frame(self, t: float) -> Image.Image:
        th, facts = self.th, self.d["facts"]
        fr = self.grad.copy()
        d = ImageDraw.Draw(fr)
        # 머리글
        tag = self.site_title
        tw = d.textlength(tag, font=font(40)) + 60
        d.rounded_rectangle(((W - tw) / 2, 150, (W + tw) / 2, 215), radius=32, fill=th["chip"])
        d.text(((W - d.textlength(tag, font=font(40))) / 2, 158), tag, font=font(40), fill="#ffffff")
        title = "서울 25개 구 평당 중위가"
        d.text(((W - d.textlength(title, font=font(72))) / 2, 250), title, font=font(72), fill=th["text"])
        sub = f"{facts['start_month']} ~ {facts['end_month']}"
        d.text(((W - d.textlength(sub, font=font(40, False))) / 2, 345), sub, font=font(40, False), fill=th["muted"])

        vals, idx, _ = self.values_at(t)
        ym = self.months[idx]
        month = _ym(ym)
        d.text(((W - d.textlength(month, font=font(96))) / 2, 410), month, font=font(96), fill=th["accent"])

        angle = math.radians(-24 - 18 * (t / self.seconds))           # 북쪽이 대략 위, 천천히 도는 카메라
        grow = 0.35 + 0.65 * ease(t / 1.2)                        # 첫 프레임(표지)도 비어 보이지 않게
        cur = self.d["values"][ym]
        top3 = [g for g, _ in sorted(cur.items(), key=lambda kv: -kv[1])[:3]]
        scene = self._scene3d(vals, angle, grow, set(top3))
        fr.paste(scene, (0, 470), scene)

        # 아래 순위 (현재 달의 DB 값 그대로)
        y = 1440
        d.text((110, y), "이번 달 상위 3개 구 (3.3㎡당)", font=font(40, False), fill=th["muted"])
        for k, gu in enumerate(top3):
            yy = y + 62 + k * 74
            d.text((110, yy), f"{k + 1}", font=font(54), fill=th["accent"])
            d.text((180, yy), gu, font=font(54), fill=th["text"])
            v = won(cur[gu])
            d.text((W - 110 - d.textlength(v, font=font(54)), yy), v, font=font(54), fill=th["text"])
        # 범례 막대
        ly = 1385
        for i in range(300):
            c = _color(i / 299, self.lo_rgb, self.hi_rgb)
            d.line([(390 + i, ly), (390 + i, ly + 16)], fill=c)
        d.text((390 - 12 - d.textlength("낮음", font=font(28, False)), ly - 8), "낮음", font=font(28, False),
               fill=th["muted"])
        d.text((702, ly - 8), "높음", font=font(28, False), fill=th["muted"])
        d.text((60, H - 150), SOURCE, font=font(26, False), fill=th["muted"])
        d.text((60, H - 112), "지도는 구 위치를 칸으로 단순화한 도식", font=font(26, False), fill=th["muted"])
        d.rectangle((0, 0, int(W * min(1.0, t / self.seconds)), 10), fill=th["accent"])
        return fr


def render(conn, out: Path, end_ym: str | None = None, months: int = 12, theme: str = "midnight",
           site_title: str = "실거래가 리포트") -> dict:
    data = seoul_facts(conn, end_ym or default_end(), months)
    tl = Timelapse(data, theme, site_title)
    n = round(tl.seconds * FPS)
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([
        FFMPEG, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-map", "0:v", "-map", "1:a", "-t", f"{n / FPS:.3f}", "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(out),
    ], stdin=subprocess.PIPE)
    try:
        for i in range(n):
            proc.stdin.write(tl.frame(i / FPS).tobytes())
        proc.stdin.close()
    except BrokenPipeError:
        pass
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg 인코딩 실패")
    return {"path": str(out), "seconds": round(n / FPS, 2), "facts": data["facts"], "months": data["months"]}


def main():
    from . import db
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/seoul_3d.mp4")
    ap.add_argument("--end", default=None)
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--theme", default="midnight", choices=sorted(THEMES))
    ap.add_argument("--frames", default="", help="이 초(쉼표 구분)의 프레임을 PNG로 저장하고 끝냄")
    a = ap.parse_args()
    conn = db.connect()
    if a.frames:
        tl = Timelapse(seoul_facts(conn, a.end or default_end(), a.months), a.theme)
        for s in a.frames.split(","):
            p = Path(a.out).with_name(f"frame_{float(s):05.1f}.png")
            p.parent.mkdir(parents=True, exist_ok=True)
            tl.frame(float(s)).save(p)
            print(p)
        return
    print(render(conn, Path(a.out), a.end, a.months, a.theme))


if __name__ == "__main__":
    main()
