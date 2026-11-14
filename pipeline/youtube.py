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
SCOPE = "https://www.googleapis.com/auth/youtube.upload"


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


def auth_flow():
    """설치형 앱 OAuth: 브라우저 로그인 → 리프레시 토큰 출력."""
    cid, secret = os.environ.get("YT_CLIENT_ID"), os.environ.get("YT_CLIENT_SECRET")
    if not (cid and secret):
        sys.exit("먼저 YT_CLIENT_ID, YT_CLIENT_SECRET 환경변수를 설정하세요.")
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
    r.raise_for_status()
    print("\nYT_REFRESH_TOKEN (GitHub Secrets에 저장, 다른 곳에 공유 금지):\n" + r.json()["refresh_token"])


if __name__ == "__main__":
    if sys.argv[1:] == ["auth"]:
        auth_flow()
    else:
        print(__doc__)
