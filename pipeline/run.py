"""파이프라인 진입점.

    python -m pipeline.run all            # 수집 → 생성 → 사이트 빌드 (매일 자동 실행되는 것)
    python -m pipeline.run collect
    python -m pipeline.run generate
    python -m pipeline.run build
    python -m pipeline.run all --demo     # API 키 없이 가상 데이터 + 가짜 작성기로 전체 시험
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from . import collect, db, generate, site
from .config import DATA_DIR, DB_PATH, load_config
from .regions import get_group

KST = timezone(timedelta(hours=9))


def log(msg: str):
    print(f"[{datetime.now(KST):%H:%M:%S}] {msg}", flush=True)


def do_collect(conn, cfg, summary, demo=False):
    _, _, regions = get_group(cfg["collect"]["regions"])
    if demo:
        from .demo import make_trades
        new = db.upsert_trades(conn, make_trades(list(regions)[:3]))
        summary["collected_new"] = new
        log(f"[demo] 가상 거래 {new}건 적재")
        return
    c = cfg["collect"]
    n_months = c["backfill_months"] if db.count_trades(conn) == 0 else c["months_back"]
    months = collect.recent_months(n_months, datetime.now(KST).date())
    new, errors = 0, []
    for sgg, (name, _) in regions.items():
        for ym in months:
            try:
                new += db.upsert_trades(conn, collect.fetch_month(c["endpoint"], sgg, ym))
            except Exception as e:  # 한 지역 실패가 전체를 멈추지 않게
                errors.append(f"{name} {ym}: {e}")
                if isinstance(e, collect.CollectError) and "인증" in str(e):
                    raise
    summary["collected_new"] = new
    summary["collect_errors"] = errors
    log(f"수집 완료: 신규 {new}건, 오류 {len(errors)}건")
    if errors and len(errors) == len(regions) * len(months):
        raise RuntimeError("모든 수집 요청이 실패했습니다: " + errors[0])


def do_generate(conn, cfg, summary, fake=False):
    if not cfg["safety"]["enabled"]:
        log("safety.enabled=false → 생성 건너뜀 (킬 스위치)")
        summary["generate"] = "disabled"
        return
    from .write import ClaudeWriter, FakeWriter
    writer = FakeWriter() if fake else ClaudeWriter(cfg["generate"]["model"], cfg["generate"]["effort"])
    now = datetime.now(KST)
    jobs = generate.plan(conn, cfg, now.date())
    log(f"작업 {len(jobs)}건 계획됨")
    ok, failed, streak = [], [], 0
    for job in jobs:
        try:
            success, problems = generate.produce(conn, cfg, writer, job, now.strftime("%Y-%m-%d"))
        except Exception as e:
            success, problems = False, [f"{type(e).__name__}: {e}"]
        if success:
            ok.append(job["slug"])
            streak = 0
            log(f"  발행 {job['slug']}")
        else:
            failed.append({"slug": job["slug"], "problems": problems[:5]})
            streak += 1
            log(f"  반려 {job['slug']}: {problems[:3]}")
            if streak >= cfg["safety"]["max_consecutive_failures"]:
                log("연속 실패 한도 도달 → 이번 실행 생성 중단")
                break
    summary.update(published=ok, rejected=failed, usage=writer.usage)
    if jobs and not ok:
        raise RuntimeError(f"계획된 {len(jobs)}건 중 발행 0건 — 확인 필요")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["collect", "generate", "build", "all"])
    ap.add_argument("--demo", action="store_true", help="가상 데이터 + 가짜 작성기 (별도 DB 사용)")
    ap.add_argument("--fake-writer", action="store_true", help="Claude 대신 가짜 작성기")
    args = ap.parse_args(argv)

    cfg = load_config()
    db_path = DATA_DIR / "demo.db" if args.demo else DB_PATH
    conn = db.connect(db_path)
    run_id = db.start_run(conn)
    summary = {"command": args.command, "demo": args.demo, "errors": []}

    def stage(name, fn):
        # 한 단계가 실패해도 다음 단계(특히 사이트 빌드)는 계속 진행
        try:
            fn()
        except Exception as e:
            summary["errors"].append(f"{name}: {type(e).__name__}: {e}")
            log(f"오류[{name}]: {e}")

    def build():
        summary["site_posts"] = site.build(conn, cfg)
        log(f"사이트 빌드 완료: 글 {summary['site_posts']}편 → public/")

    if args.command in ("collect", "all"):
        stage("collect", lambda: do_collect(conn, cfg, summary, demo=args.demo))
    if args.command in ("generate", "all"):
        stage("generate", lambda: do_generate(conn, cfg, summary, fake=args.demo or args.fake_writer))
    if args.command in ("build", "all"):
        stage("build", build)

    status = "error" if summary["errors"] else "ok"
    db.finish_run(conn, run_id, status, summary)
    if not args.demo:
        (DATA_DIR / "last_run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                                encoding="utf-8")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
