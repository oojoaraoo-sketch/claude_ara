# 실거래가 리포트 — 무인 콘텐츠 파이프라인 (Phase 1: 블로그)

국토교통부 아파트 실거래 공개 데이터를 매일 수집하고, Claude가 해설 글을 써서,
자동 검수를 통과한 글만 정적 사이트로 발행합니다. GitHub Actions가 매일 06:00(KST)에 실행하므로 PC를 켜 둘 필요가 없습니다.

```
수집(collect.py) → 분석(analyze.py) → 작성(write.py, Claude) → 검수(qa.py + Claude 2차) → 저장(db.py) → 사이트(site.py) → GitHub Pages
```

## 핵심 설계
- **수치 환각 차단**: 모든 숫자는 코드가 계산합니다. Claude는 `{{trade_count}}` 같은 플레이스홀더만 쓰고, 발행 직전에 실제 값으로 바뀝니다. 본문에 근거 없는 숫자를 직접 쓰면 자동 반려됩니다.
- **자동 검수**: 분량, 소제목, 표·차트 위치, 금지 표현(투자 권유 등), 제목·설명 길이를 검사하고 Claude가 한 번 더 편집 검수합니다. 반려되면 이유를 알려 주고 1회 재작성하며, 그래도 실패하면 버리고 기록합니다(`rejections` 테이블).
- **자동 유지보수**: 신고가 늦게 들어와 거래 건수가 15% 이상 늘면 글을 다시 써서 갱신합니다(`revision` 증가, 최종 갱신일 표시).
- **안전장치**: 하루 생성 상한(`max_new_posts_per_run`), 연속 실패 시 중단, 킬 스위치, 실패 시 GitHub 이메일 알림.

## 설치해야 할 것 (한 번만)

1. **공공데이터포털 키**: data.go.kr 가입 → "국토교통부_아파트 매매 실거래가 상세 자료" 활용신청 → 마이페이지의 **일반 인증키(Decoding)** 복사.
2. **Anthropic API 키**: console.anthropic.com → API Keys. 결제 수단 등록과 월 사용 한도 설정을 권장합니다.
3. **GitHub 저장소**: github.com에서 새 저장소(public 권장 — 무료 Pages) 생성 후 이 폴더를 push.
   - Settings → Secrets and variables → Actions
     - Secrets: `ANTHROPIC_API_KEY`, `DATA_GO_KR_KEY`
     - Variables: `SITE_BASE_URL` (예: `https://<아이디>.github.io/<저장소>` 또는 연결한 도메인)
   - Settings → Pages → Source: **GitHub Actions**
4. Actions 탭 → daily-pipeline → **Run workflow** 로 첫 실행. 첫 실행은 13개월치를 수집합니다.
5. (선택) 도메인 구입 후 Pages에 연결하고 `SITE_BASE_URL`을 도메인으로 변경.
6. 글이 20~30편 이상 쌓이면 Google Search Console 등록(사이트맵: `/sitemap.xml`), 이후 AdSense 신청. 승인되면 `config.toml`의 `adsense_client`에 값을 넣습니다.

## 로컬 실행

```powershell
.venv\Scripts\python.exe -m pipeline.run all --demo     # 키 없이 가상 데이터로 전체 시험
.venv\Scripts\python.exe -m unittest discover -s tests  # 테스트
.venv\Scripts\python.exe -m http.server 8000 --directory public   # 결과 보기
```

실데이터로 로컬 실행하려면 환경변수 `ANTHROPIC_API_KEY`, `DATA_GO_KR_KEY`를 설정하고 `--demo` 없이 실행합니다.

## 운영
- **멈추기**: 저장소 Variables에 `PIPELINE_ENABLED=false` (워크플로 전체 중단) 또는 `config.toml`의 `safety.enabled=false` (생성만 중단, 수집·빌드는 계속).
- **상태 확인**: Actions 실행 화면의 Summary, 또는 `data/last_run.json` (발행/반려 목록, 토큰 사용량).
- **비용 조절**: `config.toml`의 `max_new_posts_per_run`, `model`, `effort`, `llm_review`.

## 다음 단계
- Phase 2: 같은 데이터로 숏폼 영상 자동 생성(차트 애니메이션 + TTS) → YouTube/TikTok 업로드(각 플랫폼 앱 심사 필요)
- Phase 3: Search Console·YouTube Analytics 성과를 주간으로 읽어 주제·제목·프롬프트를 스스로 조정하는 개선 루프, 인스타그램 연동
