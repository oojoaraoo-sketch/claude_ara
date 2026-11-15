"""숏폼 장면 이미지(1080x1920)를 그리고 음성과 합쳐 mp4로 만든다."""
import subprocess
from pathlib import Path

from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

from .tts import FFMPEG

W, H = 1080, 1920
WHITE, MUTED, ACCENT, UP, DOWN = "#ffffff", "#cbd5e1", "#fbbf24", "#f87171", "#60a5fa"


def _font_path(bold: bool) -> str:
    for fam in ("Malgun Gothic", "NanumGothic", "Noto Sans CJK KR", "AppleGothic"):
        try:
            return font_manager.findfont(
                font_manager.FontProperties(family=fam, weight="bold" if bold else "normal"),
                fallback_to_default=False)
        except ValueError:
            continue
    raise RuntimeError("한글 폰트를 찾을 수 없습니다 (Linux: sudo apt-get install fonts-nanum)")


_FONTS: dict = {}


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _FONTS:
        path = _font_path(bold)
        # 맑은 고딕은 굵은체가 별도 파일
        if bold and path.lower().endswith("malgun.ttf"):
            alt = path[:-4] + "bd.ttf"
            if Path(alt).exists():
                path = alt
        _FONTS[key] = ImageFont.truetype(path, size)
    return _FONTS[key]


def _background() -> Image.Image:
    img = Image.new("RGB", (W, H))
    top, bottom = (15, 23, 42), (30, 58, 138)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


_BG = None


def _wrap(draw, text: str, f, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=f) <= width:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        cur = ""
        for ch in word:  # 한 단어가 너무 길면 글자 단위로 자름
            if draw.textlength(cur + ch, font=f) > width:
                lines.append(cur)
                cur = ""
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def _center(draw, y: int, text: str, f, fill=WHITE) -> int:
    for line in _wrap(draw, text, f, W - 140):
        w = draw.textlength(line, font=f)
        draw.text(((W - w) / 2, y), line, font=f, fill=fill)
        y += int(f.size * 1.25)
    return y


def _change_color(s: str) -> str:
    return UP if s.startswith("+") else DOWN if s.startswith("-") else MUTED


def scene_image(kind: str, headline: str, narration: str, facts: dict, site_title: str,
                site_url: str, chart_path: Path | None, out: Path) -> None:
    global _BG
    if _BG is None:
        _BG = _background()
    img = _BG.copy()
    d = ImageDraw.Draw(img)

    # 상단 브랜드
    tag = f"  {site_title}  "
    tw = d.textlength(tag, font=font(40))
    d.rounded_rectangle(((W - tw) / 2 - 10, 150, (W + tw) / 2 + 10, 215), radius=32, fill="#1d4ed8")
    _center(d, 158, tag.strip(), font(40))
    _center(d, 240, f"{facts['region']} · {facts['month']}", font(44, False), MUTED)
    y = _center(d, 380, headline, font(84))

    y += 60
    if kind == "hook":
        y = _center(d, y + 80, facts["region"], font(170), ACCENT)
        _center(d, y + 10, f"{facts['month']} 아파트 실거래", font(70))
    elif kind == "volume":
        y = _center(d, y + 60, facts["trade_count"], font(170), ACCENT)
        _center(d, y + 20, f"전월 대비 {facts['count_change']}", font(68), _change_color(facts["count_change"]))
    elif kind == "price":
        y = _center(d, y, facts["median_price"], font(120), ACCENT)
        y = _center(d, y + 5, f"전월 대비 {facts['median_change']}", font(60), _change_color(facts["median_change"]))
        if chart_path and chart_path.exists():
            ch = Image.open(chart_path).convert("RGB")
            y0 = y + 40
            ch.thumbnail((W - 100, min(640, 1330 - y0)))  # 하단 자막(약 1400px~)과 겹치지 않게
            x0 = (W - ch.width) // 2
            d.rounded_rectangle((x0 - 16, y0 - 16, x0 + ch.width + 16, y0 + ch.height + 16), radius=24, fill="white")
            img.paste(ch, (x0, y0))
    elif kind == "top_deal":
        y = _center(d, y + 40, facts["top_price"], font(124), ACCENT)
        y = _center(d, y + 20, facts["top_apt"], font(76))
        _center(d, y + 10, f"{facts['top_area']} · {facts['top_floor']} · {facts['top_date']}", font(52, False), MUTED)
    elif kind == "busy":
        y += 40
        for i in (1, 2, 3):
            if f"busy{i}_apt" in facts:
                y = _center(d, y, f"{i}. {facts[f'busy{i}_apt']}  {facts[f'busy{i}_count']}", font(66))
                y += 30
    elif kind == "outro":
        y = _center(d, y + 80, site_title, font(100), ACCENT)
        y = _center(d, y + 20, "단지별 실거래 표는 블로그에서", font(64))
        _center(d, y + 20, site_url.replace("https://", ""), font(50, False), MUTED)

    # 하단 자막 (쇼츠 UI에 가리지 않도록 아래쪽 여백 확보)
    lines = _wrap(d, narration, font(54), W - 160)
    box_h = len(lines) * 70 + 50
    top = 1500 - box_h // 2
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle((50, top, W - 50, top + box_h), radius=28, fill=(0, 0, 0, 150))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)
    yy = top + 25
    for line in lines:
        w = d.textlength(line, font=font(54))
        d.text(((W - w) / 2, yy), line, font=font(54), fill=WHITE)
        yy += 70
    img.save(out)


def segment(image: Path, audio: Path, seconds: float, out: Path) -> None:
    subprocess.run([
        FFMPEG, "-y", "-loglevel", "error",
        "-loop", "1", "-framerate", "30", "-i", str(image), "-i", str(audio),
        "-filter_complex", "[0:v]format=yuv420p[v];[1:a]apad,aresample=44100[a]",
        "-map", "[v]", "-map", "[a]", "-t", f"{seconds:.2f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-r", "30",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2", str(out),
    ], check=True)


def concat(segments: list[Path], out: Path) -> None:
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in segments), encoding="utf-8")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    lst.unlink()
