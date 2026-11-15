"""국토교통부 아파트 매매 실거래가 수집기 (공공데이터포털)."""
import hashlib
import os
import time
import xml.etree.ElementTree as ET
from datetime import date

import requests

# 2024년 개편 후 영문 태그 / 개편 전 한글 태그 모두 지원
FIELD_ALIASES = {
    "apt_name": ["aptNm", "아파트"],
    "price": ["dealAmount", "거래금액"],
    "area": ["excluUseAr", "전용면적"],
    "floor": ["floor", "층"],
    "build_year": ["buildYear", "건축년도"],
    "year": ["dealYear", "년"],
    "month": ["dealMonth", "월"],
    "day": ["dealDay", "일"],
    "umd": ["umdNm", "법정동"],
    "jibun": ["jibun", "지번"],
    "apt_seq": ["aptSeq"],
    "cdeal": ["cdealType", "해제여부"],
    "dealing_type": ["dealingGbn", "거래유형"],
}


class CollectError(RuntimeError):
    pass


def _get(item: ET.Element, key: str) -> str:
    for tag in FIELD_ALIASES[key]:
        el = item.find(tag)
        if el is not None and el.text is not None:
            return el.text.strip()
    return ""


def _int(s: str, default=None):
    try:
        return int(s.replace(",", "").strip())
    except (ValueError, AttributeError):
        return default


def parse_items(xml_text: str, sgg_cd: str) -> tuple[list[dict], int]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise CollectError(f"XML 파싱 실패: {xml_text[:200]!r}") from e

    # 게이트웨이 오류 (인증키 오류 등)
    auth_err = root.find(".//returnAuthMsg")
    if auth_err is not None:
        raise CollectError(f"API 인증 오류: {auth_err.text}")
    code = (root.findtext(".//resultCode") or "").strip()
    if code not in ("000", "00", ""):
        raise CollectError(f"API 오류 {code}: {root.findtext('.//resultMsg')}")

    total = _int(root.findtext(".//totalCount") or "0", 0)
    rows = []
    for item in root.iter("item"):
        y, m, d = _int(_get(item, "year")), _int(_get(item, "month")), _int(_get(item, "day"))
        price = _int(_get(item, "price"))
        area = _get(item, "area")
        name = _get(item, "apt_name")
        if not (y and m and d and price and area and name):
            continue
        row = {
            "sgg_cd": sgg_cd,
            "umd": _get(item, "umd"),
            "apt_seq": _get(item, "apt_seq") or None,
            "apt_name": name,
            "jibun": _get(item, "jibun"),
            "area": round(float(area), 2),
            "floor": _int(_get(item, "floor")),
            "build_year": _int(_get(item, "build_year")),
            "deal_date": f"{y:04d}-{m:02d}-{d:02d}",
            "deal_ym": f"{y:04d}{m:02d}",
            "price": price,
            "canceled": 1 if _get(item, "cdeal").upper() == "O" else 0,
            "dealing_type": _get(item, "dealing_type"),
        }
        key = "|".join(str(row[k]) for k in
                       ("sgg_cd", "apt_name", "jibun", "area", "floor", "deal_date", "price"))
        row["id"] = hashlib.sha1(key.encode()).hexdigest()[:20]
        rows.append(row)
    return rows, total


def fetch_month(endpoint: str, sgg_cd: str, ym: str, api_key: str | None = None,
                session: requests.Session | None = None) -> list[dict]:
    api_key = api_key or os.environ.get("DATA_GO_KR_KEY")
    if not api_key:
        raise CollectError("DATA_GO_KR_KEY 환경변수가 없습니다.")
    s = session or requests.Session()
    rows, page, per = [], 1, 1000
    while True:
        params = {"serviceKey": api_key, "LAWD_CD": sgg_cd, "DEAL_YMD": ym,
                  "pageNo": page, "numOfRows": per}
        for attempt in range(3):
            # 예외 메시지에는 키가 포함된 URL이 들어가므로 절대 그대로 내보내지 않는다
            try:
                resp = s.get(endpoint, params=params, timeout=30)
            except requests.RequestException as e:
                if attempt == 2:
                    raise CollectError(f"네트워크 오류: {type(e).__name__}") from None
                time.sleep(2 ** attempt)
                continue
            if resp.status_code in (401, 403):
                raise CollectError(f"인증 실패 HTTP {resp.status_code}: {resp.text[:120]!r}")
            if resp.status_code == 200:
                break
            if attempt == 2:
                raise CollectError(f"HTTP {resp.status_code}")
            time.sleep(2 ** attempt)
        batch, total = parse_items(resp.text, sgg_cd)
        rows.extend(batch)
        if page * per >= total or not batch:
            return rows
        page += 1


def recent_months(n: int, today: date | None = None) -> list[str]:
    today = today or date.today()
    y, m = today.year, today.month
    out = []
    for _ in range(n):
        out.append(f"{y:04d}{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return out
