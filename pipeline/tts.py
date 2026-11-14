"""문장 → 음성(mp3). 공급자는 config [shorts].tts_provider 로 선택."""
import asyncio
import base64
import os
import re
import subprocess

import imageio_ffmpeg
import requests

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


class TTSError(RuntimeError):
    pass


def duration(path) -> float:
    """ffmpeg 출력에서 길이(초)를 읽는다."""
    proc = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", proc.stderr)
    if not m:
        raise TTSError(f"길이를 읽을 수 없음: {path}")
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def _edge(text: str, voice: str, path):
    import edge_tts

    async def go():
        await edge_tts.Communicate(text, voice, rate="+8%").save(str(path))
    asyncio.run(go())


def _google(text: str, voice: str, path):
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        raise TTSError("GOOGLE_TTS_API_KEY 환경변수가 없습니다.")
    r = requests.post(
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        params={"key": key}, timeout=60,
        json={"input": {"text": text},
              "voice": {"languageCode": "ko-KR", "name": voice},
              "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.08}},
    )
    if r.status_code != 200:
        raise TTSError(f"Google TTS 오류 {r.status_code}: {r.text[:200]}")
    with open(path, "wb") as f:
        f.write(base64.b64decode(r.json()["audioContent"]))


def _silent(text: str, voice: str, path):
    secs = max(2.0, len(text) / 7)  # 한국어 낭독 속도 근사
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=24000:cl=mono", "-t", f"{secs:.2f}", "-q:a", "9", str(path)], check=True)


PROVIDERS = {"edge": _edge, "google": _google, "silent": _silent}


def speak(text: str, path, provider: str, voice: str) -> float:
    try:
        PROVIDERS[provider](text, voice, path)
    except KeyError:
        raise TTSError(f"알 수 없는 TTS 공급자: {provider}")
    return duration(path)
