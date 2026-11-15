"""YouTube Data API v3 업로드 (재개 가능 업로드).

필요 환경변수: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
리프레시 토큰 발급(최초 1회, 내 PC에서):
    .venv\\Scripts\\python.exe -m pipeline.youtube auth
"""
import json
import os
import secrets
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
ANALYTICS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
# 업로드 + 내 채널 통계 읽기 + 분석(시청 지속률). 읽기 권한은 성과 학습(learn.py)에 쓴다.
SCOPE = " ".join([
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
])


class YouTubeError(RuntimeError):
    pass


def configured() -> bool:
    return all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))


def access_token() -> str:
    r = requests.post(TOKEN_URL, timeout=30, data={
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    })
    if r.status_code != 200:
        raise YouTubeError(f"토큰 갱신 실패 {r.status_code}: {r.text[:300]}")
    return r.json()["access_token"]


def upload(path, title: str, description: str, tags: list[str], privacy: str, category_id: str) -> str:
    token = access_token()
    meta = {
        "snippet": {"title": title[:100], "description": description[:4900], "tags": tags,
                    "categoryId": category_id, "defaultLanguage": "ko", "defaultAudioLanguage": "ko"},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    size = os.path.getsize(path)
    init = requests.post(
        UPLOAD_URL, params={"uploadType": "resumable", "part": "snippet,status"}, timeout=60,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
        data=json.dumps(meta),
    )
    if init.status_code != 200:
        raise YouTubeError(f"업로드 시작 실패 {init.status_code}: {init.text[:300]}")
    with open(path, "rb") as f:
        r = requests.put(init.headers["Location"], data=f, timeout=600,
                         headers={"Authorization": f"Bearer {token}", "Content-Type": "video/mp4"})
    if r.status_code not in (200, 201):
        raise YouTubeError(f"업로드 실패 {r.status_code}: {r.text[:300]}")
    return r.json()["id"]


def analytics(video_ids: list[str], start: str, end: str) -> dict:
    """영상별 시청 지표. {video_id: {views, avg_view_pct, avg_view_sec, likes, shares, subs}}
    분석 권한이 없는 토큰이면 YouTubeError."""
    token = access_token()
    out = {}
    for i in range(0, len(video_ids), 200):
        ids = video_ids[i:i + 200]
        r = requests.get(ANALYTICS_URL, timeout=60, headers={"Authorization": f"Bearer {token}"}, params={
            "ids": "channel==MINE", "startDate": start, "endDate": end, "dimensions": "video",
            "metrics": "views,averageViewPercentage,averageViewDuration,likes,shares,subscribersGained",
            "filters": "video==" + ",".join(ids), "maxResults": 200})
        if r.status_code != 200:
            raise YouTubeError(f"분석 조회 실패 {r.status_code}: {r.text[:200]}")
        for row in r.json().get("rows", []) or []:
            vid, views, pct, sec, likes, shares, subs = row
            out[vid] = {"views": int(views), "avg_view_pct": float(pct), "avg_view_sec": float(sec),
                        "likes": int(likes), "shares": int(shares), "subs": int(subs)}
    return out


def _client_from_json() -> tuple[str, str, str]:
    """다운로드 폴더의 최신 client_secret_*.json 에서 클라이언트 정보를 읽는다."""
    from pathlib import Path
    files = sorted(Path.home().joinpath("Downloads").glob("client_secret_*.json"),
                   key=lambda p: p.stat().st_mtime)
    if not files:
        sys.exit("다운로드 폴더에 client_secret_*.json 파일이 없습니다. Google Cloud에서 JSON을 다운로드하세요.")
    data = json.loads(files[-1].read_text(encoding="utf-8"))
    info = data.get("installed") or data.get("web") or {}
    return info["client_id"], info["client_secret"], str(files[-1])


def _gh_secret(repo: str, name: str, value: str):
    import subprocess
    gh = r"C:\Program Files\GitHub CLI\gh.exe" if os.name == "nt" else "gh"
    subprocess.run([gh, "secret", "set", name, "--repo", repo], input=value, text=True, check=True,
                   capture_output=True)


def auth_flow(repo: str | None = None):
    """설치형 앱 OAuth: 브라우저 로그인 → 리프레시 토큰.

    repo 를 주면 세 값을 GitHub Secrets에 바로 등록하고 화면에는 출력하지 않는다.
    """
    cid, secret = os.environ.get("YT_CLIENT_ID"), os.environ.get("YT_CLIENT_SECRET")
    src = "환경변수"
    if not (cid and secret):
        cid, secret, src = _client_from_json()
    print(f"OAuth 클라이언트 정보: {src}")
    port, state = 8765, secrets.token_urlsafe(16)
    redirect = f"http://127.0.0.1:{port}/"
    result = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state:
                result["code"] = q.get("code", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("인증 완료. 이 창을 닫고 터미널로 돌아가세요.".encode())

        def log_message(self, *a):
            pass

    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent", "state": state})
    print("브라우저에서 업로드할 채널의 구글 계정으로 로그인하세요:\n" + url)
    webbrowser.open(url)
    srv = HTTPServer(("127.0.0.1", port), Handler)
    while "code" not in result:
        srv.handle_request()
    r = requests.post(TOKEN_URL, timeout=30, data={
        "code": result["code"], "client_id": cid, "client_secret": secret,
        "redirect_uri": redirect, "grant_type": "authorization_code"})
    if r.status_code != 200:
        sys.exit(f"토큰 발급 실패 HTTP {r.status_code}")
    refresh = r.json().get("refresh_token")
    if not refresh:
        sys.exit("리프레시 토큰이 오지 않았습니다. 다시 실행하세요.")
    if repo:
        for name, val in (("YT_CLIENT_ID", cid), ("YT_CLIENT_SECRET", secret), ("YT_REFRESH_TOKEN", refresh)):
            _gh_secret(repo, name, val)
            print(f"✓ GitHub Secret 등록: {name}")
        print("완료. 다운로드한 client_secret JSON 파일은 지워도 됩니다.")
    else:
        print("\nYT_REFRESH_TOKEN (GitHub Secrets에 저장, 다른 곳에 공유 금지):\n" + refresh)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["auth"]:
        auth_flow(args[2] if len(args) >= 3 and args[1] == "--to-github" else None)
    else:
        print(__doc__)
