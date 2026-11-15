"""Instagram 릴스 게시 (Instagram API with Instagram Login, 본인 계정 = Standard Access).

필요한 GitHub Secrets
  IG_ACCESS_TOKEN : Meta 앱 대시보드에서 생성한 장기 토큰 (최초 1회만 사용)
  IG_STATE_KEY    : 토큰 상태 파일 암호화 키 (scripts/setup_instagram.ps1 이 만들어 등록)

장기 토큰은 60일 뒤 만료되고, 갱신하면 새 토큰이 나온다. 새 토큰은 공개 저장소에 그대로 둘 수 없으므로
IG_STATE_KEY 로 암호화해 data/ig_state.enc 에 저장한다.
영상은 GitHub Pages(public/media/)에 먼저 배포된 뒤 그 URL로 게시한다 (Instagram이 URL에서 가져감).
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests

from .config import DATA_DIR

GRAPH = "https://graph.instagram.com"
STATE = DATA_DIR / "ig_state.enc"
REFRESH_AFTER = timedelta(days=3)  # 갱신은 발급 24시간 이후 가능, 60일 안에 해야 함


class InstagramError(RuntimeError):
    pass


def configured() -> bool:
    return bool(os.environ.get("IG_STATE_KEY")) and (STATE.exists() or bool(os.environ.get("IG_ACCESS_TOKEN")))


def _fernet():
    from cryptography.fernet import Fernet
    return Fernet(os.environ["IG_STATE_KEY"].encode())


def _load() -> dict:
    if STATE.exists():
        return json.loads(_fernet().decrypt(STATE.read_bytes()))
    return {"token": os.environ["IG_ACCESS_TOKEN"], "refreshed_at": "2000-01-01T00:00:00+00:00"}


def _save(state: dict):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_bytes(_fernet().encrypt(json.dumps(state).encode()))


def _err(r) -> str:
    try:
        e = r.json().get("error", {})
        return f"HTTP {r.status_code} {e.get('type', '')} {e.get('code', '')}: {e.get('message', '')[:200]}"
    except ValueError:
        return f"HTTP {r.status_code}"


def token() -> str:
    """유효한 토큰을 반환하고, 오래됐으면 갱신해 암호화 저장한다."""
    state = _load()
    last = datetime.fromisoformat(state["refreshed_at"])
    if datetime.now(timezone.utc) - last > REFRESH_AFTER:
        r = requests.get(f"{GRAPH}/refresh_access_token", timeout=30,
                         params={"grant_type": "ig_refresh_token", "access_token": state["token"]})
        if r.status_code == 200:
            state = {"token": r.json()["access_token"],
                     "refreshed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
            _save(state)
        elif not STATE.exists():
            # 막 발급한 토큰(24시간 이내)은 갱신이 거절될 수 있음 → 그대로 저장하고 다음에 갱신
            state["refreshed_at"] = (datetime.now(timezone.utc) - REFRESH_AFTER + timedelta(days=1)).isoformat()
            _save(state)
        else:
            raise InstagramError(f"토큰 갱신 실패 ({_err(r)}). 토큰을 다시 발급해 IG_ACCESS_TOKEN을 갱신하고 data/ig_state.enc를 지우세요.")
    return state["token"]


def publish_reel(video_url: str, caption: str, wait_seconds: int = 600) -> str:
    tok = token()
    me = requests.get(f"{GRAPH}/me", params={"fields": "user_id,username", "access_token": tok}, timeout=30)
    if me.status_code != 200:
        raise InstagramError(f"계정 조회 실패: {_err(me)}")
    ig_id = me.json()["user_id"]

    c = requests.post(f"{GRAPH}/{ig_id}/media", timeout=60, data={
        "media_type": "REELS", "video_url": video_url, "caption": caption[:2200],
        "share_to_feed": "true", "access_token": tok})
    if c.status_code != 200:
        raise InstagramError(f"컨테이너 생성 실패: {_err(c)}")
    cid = c.json()["id"]

    deadline = time.time() + wait_seconds
    while True:
        s = requests.get(f"{GRAPH}/{cid}", params={"fields": "status_code,status", "access_token": tok}, timeout=30)
        code = s.json().get("status_code") if s.status_code == 200 else None
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise InstagramError(f"영상 처리 실패: {s.json().get('status', code)}")
        if time.time() > deadline:
            raise InstagramError("영상 처리 시간 초과")
        time.sleep(30)

    p = requests.post(f"{GRAPH}/{ig_id}/media_publish", timeout=60,
                      data={"creation_id": cid, "access_token": tok})
    if p.status_code != 200:
        raise InstagramError(f"게시 실패: {_err(p)}")
    return p.json()["id"]


def caption_for(video: dict, post_url: str) -> str:
    title = video["title"].replace(" #Shorts", "").strip()
    tags = " ".join("#" + t.replace(" ", "") for t in json.loads(video["tags"]))
    return (f"{title}\n\n국토교통부 실거래가 공개 자료로 정리했습니다. "
            f"단지별 상세 표는 프로필 링크의 블로그에서 확인하세요.\n{post_url}\n\n"
            f"※ 투자 권유가 아닌 통계 정리입니다.\n\n{tags} #실거래가 #부동산 #아파트")
