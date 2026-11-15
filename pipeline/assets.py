"""공개 자료(사진) 수급: 위키미디어 공용에서 조건에 맞는 사진만 골라 쓰고 출처를 기록한다.

원칙
  - 허용 라이선스만: CC0 / 퍼블릭 도메인 / CC BY (출처 표시만 요구) / 공공누리 1유형.
    동일조건변경허락(SA)·비영리(NC)·변경금지(ND)는 영상에 합성할 수 없으므로 제외.
  - 지도·로고·문서·인물 사진은 제목과 설명으로 걸러 내고, 최종 선택은 Claude가 후보 설명을 읽고 한다.
  - 쓴 자료는 assets 테이블에 URL·작가·라이선스를 남기고 영상 설명과 화면에 출처를 적는다.
  - 내려받기에 실패하면 그림 없이(그라데이션 배경) 진행한다. 영상 제작을 막지 않는다.
무료 영상 소스(Pexels, Pixabay)는 API 키 가입이 필요해 아직 연결하지 않았다. PROVIDERS에 추가하면 된다.
"""
import html
import json
import re
from pathlib import Path

import requests

from . import db

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "SilgeoraeReportBot/1.0 (https://silgeorae-report.github.io/)"}
BAD_WORDS = re.compile(r"map|지도|logo|로고|symbol|emblem|flag|seal|diagram|chart|station sign|노선도|"
                       r"portrait|초상|인물|mayor|구청장|의원|document|문서|poster|포스터|icon|svg", re.I)

ROMAN = {"종로구": "Jongno-gu", "중구": "Jung-gu", "용산구": "Yongsan-gu", "성동구": "Seongdong-gu",
         "광진구": "Gwangjin-gu", "동대문구": "Dongdaemun-gu", "중랑구": "Jungnang-gu", "성북구": "Seongbuk-gu",
         "강북구": "Gangbuk-gu", "도봉구": "Dobong-gu", "노원구": "Nowon-gu", "은평구": "Eunpyeong-gu",
         "서대문구": "Seodaemun-gu", "마포구": "Mapo-gu", "양천구": "Yangcheon-gu", "강서구": "Gangseo-gu",
         "구로구": "Guro-gu", "금천구": "Geumcheon-gu", "영등포구": "Yeongdeungpo-gu", "동작구": "Dongjak-gu",
         "관악구": "Gwanak-gu", "서초구": "Seocho-gu", "강남구": "Gangnam-gu", "송파구": "Songpa-gu",
         "강동구": "Gangdong-gu"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
    key TEXT PRIMARY KEY,            -- 예: region:강남구
    file_url TEXT,
    page_url TEXT,
    license TEXT,
    artist TEXT,
    title TEXT,
    status TEXT NOT NULL,            -- ok | none (쓸 만한 자료 없음)
    fetched_at TEXT NOT NULL
);
"""

PICK_SCHEMA = {"type": "object", "properties": {"index": {"type": "integer"}, "reason": {"type": "string"}},
               "required": ["index", "reason"], "additionalProperties": False}


def license_ok(short: str) -> bool:
    s = (short or "").strip().lower().replace("-", " ")
    if s in ("cc0", "public domain", "pd") or s.startswith("cc0") or "public domain" in s:
        return True
    if s.startswith("kogl type 1"):
        return True
    return s.startswith("cc by ") and not any(x in s.split() for x in ("sa", "nc", "nd"))


def _clean(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()[:120]


def search(query: str, limit: int = 30) -> list[dict]:
    r = requests.get(API, headers=UA, timeout=30, params={
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": limit,
        "gsrsearch": f"{query} filetype:bitmap", "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1600})
    r.raise_for_status()
    out = []
    for page in (r.json().get("query", {}).get("pages", {}) or {}).values():
        ii = (page.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "")
        title = page.get("title", "")
        desc = _clean(meta.get("ImageDescription", {}).get("value", ""))
        if ii.get("mime") != "image/jpeg" or not license_ok(lic):
            continue
        if ii.get("width", 0) < 1400 or ii.get("width", 0) < ii.get("height", 0):   # 가로 풍경 사진만
            continue
        if BAD_WORDS.search(title) or BAD_WORDS.search(desc):
            continue
        out.append({"title": title, "desc": desc, "license": lic,
                    "artist": _clean(meta.get("Artist", {}).get("value", "")) or "Wikimedia Commons",
                    "file_url": ii.get("thumburl") or ii.get("url"), "page_url": ii.get("descriptionurl", "")})
    return out


def _pick(writer, region: str, cands: list[dict]) -> int:
    """Claude가 후보의 제목·설명을 읽고 배경으로 쓸 사진을 고른다. 마땅치 않으면 -1."""
    listing = "\n".join(f"{i}. {c['title']} — {c['desc']}" for i, c in enumerate(cands))
    system = ("서울 아파트 실거래 영상의 배경 사진을 고릅니다. 후보의 파일 제목과 설명만 보고 판단하세요. "
              f"'{region}'의 거리·스카이라인·아파트 단지·한강 등 풍경으로 보이는 것 하나의 번호를 고르세요. "
              "특정 인물이 주제인 사진, 행사·시위·사고 사진, 실내, 음식, 지도, 간판·문서, 다른 지역 사진은 안 됩니다. "
              "적당한 것이 없으면 index 를 -1 로 답하세요.")
    try:
        res = writer._call(system, listing, PICK_SCHEMA, "low", 500)
        i = int(res.get("index", -1))
        return i if 0 <= i < len(cands) else -1
    except Exception:
        return -1


def region_photo(conn, writer, region: str, out_dir: Path) -> tuple[Path | None, str | None, str | None]:
    """(사진 파일, 화면용 출처 한 줄, 설명란용 출처) 를 돌려준다. 없으면 (None, None, None)."""
    conn.executescript(SCHEMA)
    key = f"region:{region}"
    row = conn.execute("SELECT * FROM assets WHERE key = ?", (key,)).fetchone()
    if row is None:
        if not hasattr(writer, "_call"):     # 시험용 작성기: 외부 검색을 하지 않는다
            return None, None, None
        chosen = None
        try:
            cands, seen = [], set()
            roman = ROMAN.get(region, region)
            for q in (f"{roman} Seoul", f"{roman} Seoul apartments", f"{region} 서울"):
                for c in search(q):
                    if c["page_url"] not in seen:
                        seen.add(c["page_url"])
                        cands.append(c)
                if len(cands) >= 10:
                    break
            if cands and hasattr(writer, "_call"):
                i = _pick(writer, region, cands[:12])
                chosen = cands[i] if i >= 0 else None
        except Exception:
            return None, None, None      # 네트워크 문제는 기록하지 않고 다음에 다시 시도
        c = chosen or {}
        conn.execute("INSERT OR REPLACE INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (key, c.get("file_url"), c.get("page_url"), c.get("license"), c.get("artist"),
                      c.get("title"), "ok" if chosen else "none", db.now_iso()))
        conn.commit()
        row = conn.execute("SELECT * FROM assets WHERE key = ?", (key,)).fetchone()
    if row["status"] != "ok":
        return None, None, None
    try:
        r = requests.get(row["file_url"], headers=UA, timeout=60)
        r.raise_for_status()
        path = out_dir / "photo.jpg"
        path.write_bytes(r.content)
    except Exception:
        return None, None, None
    short = f"사진: {row['artist']} / {row['license']}"
    full = f"배경 사진: {row['artist']}, {row['license']}, Wikimedia Commons ({row['page_url']})"
    return path, short, full


def credits(conn) -> list[dict]:
    conn.executescript(SCHEMA)
    return [dict(r) for r in conn.execute("SELECT * FROM assets WHERE status = 'ok' ORDER BY key")]


if __name__ == "__main__":   # 수동 점검: python -m pipeline.assets 강남구
    import sys
    print(json.dumps(search(sys.argv[1] + " 서울")[:8], ensure_ascii=False, indent=1))
