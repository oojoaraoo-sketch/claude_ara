"""DB의 거래 데이터를 글에 쓸 '사실(facts)'과 표·차트 데이터로 가공한다.

글에 들어가는 모든 숫자는 여기서 계산된다. Claude는 숫자를 직접 쓰지 않고
{{키}} 플레이스홀더만 쓰며, 발행 직전에 이 값으로 치환된다 (수치 환각 차단).
"""
import hashlib
import statistics
from collections import Counter, defaultdict

PYEONG = 3.305785


def won(manwon: float | int) -> str:
    """만원 단위 정수 → '8억 2,500만원'."""
    v = int(round(manwon))
    eok, man = divmod(v, 10000)
    if eok and man:
        return f"{eok}억 {man:,}만원"
    if eok:
        return f"{eok}억원"
    return f"{man:,}만원"


def pct(new: float, old: float) -> str:
    if not old:
        return "비교 불가"
    p = (new - old) / old * 100
    return f"{p:+.1f}%"


def ym_label(ym: str) -> str:
    return f"{ym[:4]}년 {int(ym[4:])}월"


def prev_ym(ym: str, n: int = 1) -> str:
    y, m = int(ym[:4]), int(ym[4:])
    for _ in range(n):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return f"{y:04d}{m:02d}"


def _valid(conn, where: str, params: tuple):
    return conn.execute(
        f"SELECT * FROM trades WHERE canceled = 0 AND {where}", params
    ).fetchall()


def complex_key(row) -> str:
    return row["apt_seq"] or f"{row['apt_name']}|{row['jibun']}"


def complex_slug(sgg_cd: str, key: str) -> str:
    return f"apt-{sgg_cd}-{hashlib.sha1(key.encode()).hexdigest()[:10]}"


# ---------------------------------------------------------------- 구별 월간 리포트

def gu_monthly(conn, sgg_cd: str, gu_name: str, ym: str, as_of: str) -> dict | None:
    rows = _valid(conn, "sgg_cd = ? AND deal_ym = ?", (sgg_cd, ym))
    if not rows:
        return None
    prev = _valid(conn, "sgg_cd = ? AND deal_ym = ?", (sgg_cd, prev_ym(ym)))
    yoy = _valid(conn, "sgg_cd = ? AND deal_ym = ?", (sgg_cd, prev_ym(ym, 12)))

    prices = [r["price"] for r in rows]
    ppp = [r["price"] / (r["area"] / PYEONG) for r in rows]
    med = statistics.median(prices)
    top = max(rows, key=lambda r: r["price"])
    umd = Counter(r["umd"] for r in rows).most_common(1)[0]
    by_complex = Counter((r["apt_name"]) for r in rows).most_common(3)
    small = sum(1 for r in rows if r["area"] < 60) / len(rows) * 100

    # 데이터 수집 기간 내 단지·면적 기준 최고가 경신 건수
    highs = 0
    for r in rows:
        prior = conn.execute(
            """SELECT MAX(price) FROM trades WHERE canceled = 0 AND sgg_cd = ? AND apt_name = ?
               AND ABS(area - ?) < 1 AND deal_date < ?""",
            (sgg_cd, r["apt_name"], r["area"], f"{ym[:4]}-{ym[4:]}-01"),
        ).fetchone()[0]
        if prior and r["price"] > prior:
            highs += 1
    since = conn.execute("SELECT MIN(deal_ym) FROM trades WHERE sgg_cd = ?", (sgg_cd,)).fetchone()[0]

    facts = {
        "region": gu_name,
        "month": ym_label(ym),
        "prev_month": ym_label(prev_ym(ym)),
        "as_of": as_of,
        "trade_count": f"{len(rows):,}건",
        "prev_count": f"{len(prev):,}건" if prev else "자료 없음",
        "count_change": pct(len(rows), len(prev)) if prev else "비교 불가",
        "median_price": won(med),
        "median_change": pct(med, statistics.median([r["price"] for r in prev])) if prev else "비교 불가",
        "median_ppp": won(statistics.median(ppp)),
        "yoy_count": f"{len(yoy):,}건" if yoy else "자료 없음",
        "yoy_median_change": pct(med, statistics.median([r["price"] for r in yoy])) if yoy else "비교 불가",
        "top_apt": top["apt_name"],
        "top_area": f"{top['area']:.2f}㎡",
        "top_floor": f"{top['floor']}층" if top["floor"] is not None else "층 정보 없음",
        "top_price": won(top["price"]),
        "top_date": top["deal_date"],
        "top_apt_umd": top["umd"],
        "top_umd": umd[0],
        "top_umd_count": f"{umd[1]:,}건",
        "small_share": f"{small:.1f}%",
        "new_high_count": f"{highs:,}건",
        "high_since": ym_label(since) if since else "수집 시작",
    }
    for i, (name, cnt) in enumerate(by_complex, 1):
        facts[f"busy{i}_apt"] = name
        facts[f"busy{i}_count"] = f"{cnt:,}건"

    top10 = sorted(rows, key=lambda r: -r["price"])[:10]
    table = "| 순위 | 단지 | 법정동 | 전용면적 | 층 | 거래금액 | 계약일 |\n|---|---|---|---|---|---|---|\n"
    table += "\n".join(
        f"| {i} | {r['apt_name']} | {r['umd']} | {r['area']:.2f}㎡ | {r['floor']} | {won(r['price'])} | {r['deal_date']} |"
        for i, r in enumerate(top10, 1)
    )

    series = conn.execute(
        """SELECT deal_ym, COUNT(*) AS n, GROUP_CONCAT(price) AS ps FROM trades
           WHERE canceled = 0 AND sgg_cd = ? AND deal_ym <= ? GROUP BY deal_ym ORDER BY deal_ym""",
        (sgg_cd, ym),
    ).fetchall()
    trend = [(s["deal_ym"], s["n"], statistics.median(int(p) for p in s["ps"].split(",")))
             for s in series][-13:]

    return {"facts": facts, "tables": {"top10": table}, "trend": trend, "trade_count": len(rows)}


# ---------------------------------------------------------------- 단지 페이지

def list_complexes(conn, sgg_cd: str, min_trades: int, since_ym: str) -> list[dict]:
    rows = _valid(conn, "sgg_cd = ?", (sgg_cd,))
    groups = defaultdict(list)
    for r in rows:
        groups[complex_key(r)].append(r)
    out = []
    for key, rs in groups.items():
        if len(rs) >= min_trades and max(r["deal_ym"] for r in rs) >= since_ym:
            out.append({"key": key, "count": len(rs), "name": rs[0]["apt_name"]})
    return sorted(out, key=lambda c: -c["count"])


def complex_page(conn, sgg_cd: str, gu_name: str, key: str, as_of: str) -> dict | None:
    if "|" in key:
        name, jibun = key.split("|", 1)
        rows = _valid(conn, "sgg_cd = ? AND apt_seq IS NULL AND apt_name = ? AND jibun = ?",
                      (sgg_cd, name, jibun))
    else:
        rows = _valid(conn, "sgg_cd = ? AND apt_seq = ?", (sgg_cd, key))
    if not rows:
        return None
    rows = sorted(rows, key=lambda r: r["deal_date"])
    latest = rows[-1]
    areas = defaultdict(list)
    for r in rows:
        areas[round(r["area"])].append(r)
    main_area, main_rows = max(areas.items(), key=lambda kv: len(kv[1]))
    main_prices = [r["price"] for r in main_rows]
    hi = max(rows, key=lambda r: r["price"])

    facts = {
        "region": gu_name,
        "apt": latest["apt_name"],
        "umd": latest["umd"],
        "build_year": f"{latest['build_year']}년" if latest["build_year"] else "정보 없음",
        "as_of": as_of,
        "trade_count": f"{len(rows):,}건",
        "period_start": rows[0]["deal_date"],
        "period_end": latest["deal_date"],
        "area_types": f"{len(areas)}개",
        "main_area": f"{main_area}㎡",
        "main_count": f"{len(main_rows):,}건",
        "main_median": won(statistics.median(main_prices)),
        "main_max": won(max(main_prices)),
        "main_min": won(min(main_prices)),
        "main_latest": won(main_rows[-1]["price"]),
        "main_latest_date": main_rows[-1]["deal_date"],
        "latest_price": won(latest["price"]),
        "latest_area": f"{latest['area']:.2f}㎡",
        "latest_date": latest["deal_date"],
        "high_price": won(hi["price"]),
        "high_area": f"{hi['area']:.2f}㎡",
        "high_date": hi["deal_date"],
    }
    if len(main_rows) >= 2:
        facts["main_first"] = won(main_rows[0]["price"])
        facts["main_first_date"] = main_rows[0]["deal_date"]
        facts["main_change"] = pct(main_rows[-1]["price"], main_rows[0]["price"])

    area_table = "| 전용면적 | 거래 건수 | 최저 | 중위 | 최고 | 최근 거래 |\n|---|---|---|---|---|---|\n"
    area_table += "\n".join(
        f"| {a}㎡ | {len(rs)}건 | {won(min(r['price'] for r in rs))} | "
        f"{won(statistics.median(r['price'] for r in rs))} | {won(max(r['price'] for r in rs))} | "
        f"{won(rs[-1]['price'])} ({rs[-1]['deal_date']}) |"
        for a, rs in sorted(areas.items())
    )
    recent = "| 계약일 | 전용면적 | 층 | 거래금액 |\n|---|---|---|---|\n"
    recent += "\n".join(
        f"| {r['deal_date']} | {r['area']:.2f}㎡ | {r['floor']} | {won(r['price'])} |"
        for r in reversed(rows[-15:])
    )
    points = [(r["deal_date"], r["price"], round(r["area"])) for r in rows]
    return {"facts": facts, "tables": {"areas": area_table, "recent": recent},
            "points": points, "trade_count": len(rows)}
