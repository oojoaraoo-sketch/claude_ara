"""TikTok 업로드 대기열 준비 (이 PC에서 예약 작업이 실행).

1) git pull 로 최신 DB를 받고
2) 최근 N일 영상 중 아직 TikTok에 올리지 않았고 GitHub Pages에 파일이 있는 것을 골라
3) tiktok_upload/ 에 mp4를 내려받고 queue.json 에 캡션과 함께 적는다.

올린 뒤에는  python scripts/tiktok_prepare.py --done <slug>  로 기록한다 (tiktok_upload/posted.json).
"""
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tiktok_upload"
POSTED = OUT / "posted.json"
BASE = "https://silgeorae-report.github.io"
MAX_PER_DAY = 2
DAYS_BACK = 3


def caption(title: str, tags: list[str]) -> str:
    title = title.replace("#Shorts", "").strip()
    hashtags = " ".join("#" + t.replace(" ", "") for t in tags[:5])
    return (f"{title} — 국토교통부 공개 자료로 만든 통계 정리이며 투자 권유가 아닙니다. "
            f"단지별 표는 프로필의 블로그에서 확인하세요. {hashtags} #실거래가")


def load_posted() -> dict:
    return json.loads(POSTED.read_text(encoding="utf-8")) if POSTED.exists() else {}


def main():
    OUT.mkdir(exist_ok=True)
    posted = load_posted()
    if len(sys.argv) == 3 and sys.argv[1] == "--done":
        posted[sys.argv[2]] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        POSTED.write_text(json.dumps(posted, ensure_ascii=False, indent=1), encoding="utf-8")
        (OUT / f"{sys.argv[2]}.mp4").unlink(missing_ok=True)
        print("기록 완료:", sys.argv[2])
        return

    subprocess.run(["git", "-C", str(ROOT), "pull", "-q", "--rebase", "--autostash"], check=False)
    conn = sqlite3.connect(ROOT / "data" / "pipeline.db")
    conn.row_factory = sqlite3.Row
    since = (datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")
    rows = conn.execute("SELECT slug, title, tags FROM videos WHERE created_at >= ? ORDER BY created_at DESC",
                        (since,)).fetchall()
    queue = []
    for r in rows:
        if len(queue) >= MAX_PER_DAY:
            break
        if r["slug"] in posted:
            continue
        url = f"{BASE}/media/{r['slug']}.mp4"
        resp = requests.get(url, timeout=60)
        if resp.status_code != 200 or not resp.headers.get("content-type", "").startswith("video"):
            continue
        path = OUT / f"{r['slug']}.mp4"
        path.write_bytes(resp.content)
        queue.append({"slug": r["slug"], "file": str(path),
                      "caption": caption(r["title"], json.loads(r["tags"] or "[]"))})
    (OUT / "queue.json").write_text(json.dumps(queue, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(queue, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
