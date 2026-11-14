"""무엇을 쓸지 정하고(plan), 쓰고, 검수하고, 저장한다(produce)."""
from datetime import date

from . import analyze, db, qa
from .regions import get_group


def gu_slug(group_slug: str, gu_slug_: str, ym: str) -> str:
    return f"{group_slug}-{gu_slug_}-{ym[:4]}-{ym[4:]}"


def plan(conn, cfg, today: date) -> list[dict]:
    gname, gslug, regions = get_group(cfg["collect"]["regions"])
    g = cfg["generate"]
    cur = f"{today.year:04d}{today.month:02d}"
    jobs = []

    def status(slug: str, count: int) -> int | None:
        """None=건너뜀, 0=신규, 1=갱신."""
        post = db.get_post(conn, slug)
        if post is None:
            rejected = conn.execute("SELECT COUNT(*) FROM rejections WHERE slug = ?", (slug,)).fetchone()[0]
            return None if rejected >= 3 else 0
        if count >= post["trade_count"] * (1 + g["regenerate_growth"]):
            return 1
        return None

    # 1) 구별 월간 리포트: 지난달, 지지난달 (이번 달은 신고가 덜 들어와 제외)
    for ym in (analyze.prev_ym(cur, 1), analyze.prev_ym(cur, 2)):
        for sgg, (name, slug_) in regions.items():
            n = conn.execute("SELECT COUNT(*) FROM trades WHERE canceled=0 AND sgg_cd=? AND deal_ym=?",
                             (sgg, ym)).fetchone()[0]
            if n < 10:
                continue
            slug = gu_slug(gslug, slug_, ym)
            st = status(slug, n)
            if st is not None:
                jobs.append({"kind": "gu_monthly", "slug": slug, "sgg": sgg, "gu": name, "ym": ym,
                             "count": n, "rank": (st * 2, ym != analyze.prev_ym(cur, 1), -n)})

    # 2) 단지 페이지: 최근 3개월 내 거래가 있고 거래가 충분한 단지
    since = analyze.prev_ym(cur, 3)
    for sgg, (name, _) in regions.items():
        for c in analyze.list_complexes(conn, sgg, g["min_trades_for_complex"], since):
            slug = analyze.complex_slug(sgg, c["key"])
            st = status(slug, c["count"])
            if st is not None:
                jobs.append({"kind": "complex", "slug": slug, "sgg": sgg, "gu": name, "key": c["key"],
                             "count": c["count"], "rank": (st * 2 + 1, False, -c["count"])})

    jobs.sort(key=lambda j: j["rank"])
    return jobs[: g["max_new_posts_per_run"]]


def build_material(conn, job: dict, as_of: str) -> dict | None:
    if job["kind"] == "gu_monthly":
        m = analyze.gu_monthly(conn, job["sgg"], job["gu"], job["ym"], as_of)
        if m:
            m["chart"] = {"type": "gu_trend", "sgg": job["sgg"], "gu": job["gu"], "ym": job["ym"]}
            m["chart_alt"] = f"{job['gu']} 월별 아파트 거래량과 중위 거래가 추이"
    else:
        m = analyze.complex_page(conn, job["sgg"], job["gu"], job["key"], as_of)
        if m:
            m["chart"] = {"type": "complex", "sgg": job["sgg"], "gu": job["gu"], "key": job["key"]}
            m["chart_alt"] = f"{m['facts']['apt']} 거래 시점별 실거래가 분포"
    return m


def produce(conn, cfg, writer, job: dict, as_of: str) -> tuple[bool, list[str]]:
    """글 한 편 생성. (성공 여부, 문제 목록) 반환. 한 번은 피드백을 주고 재작성한다."""
    m = build_material(conn, job, as_of)
    if m is None:
        return False, ["데이터 없음"]
    facts = m["facts"]
    feedback = None
    for _ in range(2):
        draft = writer.write(job["kind"], facts, feedback)
        problems = qa.check(job["kind"], draft, facts, cfg)
        if not problems:
            final = qa.render(draft, facts, m["tables"], f"/charts/{job['slug']}.png", m["chart_alt"])
            if cfg["generate"]["llm_review"]:
                verdict = writer.review(final["body_md"], facts)
                if not verdict["approved"]:
                    problems = ["2차 검수: " + i for i in verdict["issues"]] or ["2차 검수 반려"]
        if not problems:
            db.save_post(conn, {
                "slug": job["slug"], "kind": job["kind"], "region_code": job["sgg"],
                "title": final["title"], "description": final["description"],
                "body_md": final["body_md"], "tags": final["tags"], "facts": facts,
                "trade_count": m["trade_count"], "charts": [m["chart"]],
            })
            return True, []
        feedback = problems
    db.log_rejection(conn, job["slug"], problems)
    return False, problems
