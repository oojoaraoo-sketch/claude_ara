"""공공데이터포털 키가 이 PC(한국 IP)에서 동작하는지 확인한다. 키는 화면에 표시되지 않는다.

사용법: 인증키(Decoding)를 Ctrl+C로 복사한 뒤
    .venv\\Scripts\\python.exe scripts\\check_key.py
"""
import subprocess

import requests

URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"

key = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                     capture_output=True, text=True, encoding="utf-8").stdout.strip()
if len(key) < 20 or " " in key or "\n" in key:
    raise SystemExit("클립보드에 인증키가 없습니다. 공공데이터포털에서 일반 인증키(Decoding)를 Ctrl+C로 복사한 뒤 다시 실행하세요.")
print(f"클립보드에서 키를 읽었습니다 (길이 {len(key)}자, 앞 4자리 {key[:4]}…)")

r = requests.get(URL, params={"serviceKey": key, "LAWD_CD": "11110", "DEAL_YMD": "202610",
                              "pageNo": 1, "numOfRows": 1}, timeout=30)
body = r.text.replace(key, "***")
print(f"\nHTTP {r.status_code}")
print(body[:300])
if r.status_code == 200 and "<item>" in body:
    print("\n결과: 정상 — 이 PC에서는 키가 동작합니다.")
elif r.status_code == 200:
    print("\n결과: 응답은 왔지만 데이터가 없음 — 위 메시지를 Claude에게 알려 주세요.")
else:
    print("\n결과: 실패 — 키가 아직 활성화되지 않았거나 신청한 API가 다를 수 있습니다.")
