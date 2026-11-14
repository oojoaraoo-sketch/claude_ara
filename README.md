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

## Phase 2: 숏폼 영상 (YouTube Shorts)

월간 리포트 글마다 약 30~45초 세로 영상(1080x1920)을 자동으로 만듭니다(하루 최대 2편).
Claude가 장면별 대본을 쓰되 블로그와 같은 플레이스홀더 규칙을 따르므로 영상 속 숫자도 원자료와 일치합니다.
설명란에는 블로그 글 링크가 들어가고, 업로드된 영상은 블로그 글 하단에 자동으로 임베드됩니다.

```
글(facts) → 대본(Claude, 자동 검수) → 음성(TTS) → 장면 이미지 6장 → ffmpeg 합성 → YouTube 업로드
```

**YouTube 연결 (사용자가 직접, 최초 1회)**
1. console.cloud.google.com → 새 프로젝트 → "YouTube Data API v3" 사용 설정.
2. OAuth 동의 화면 구성(외부, 앱 이름 입력, 테스트 사용자에 본인 계정 추가) → 게시 상태를 **프로덕션**으로 전환
   (테스트 상태로 두면 리프레시 토큰이 7일 후 만료됩니다).
3. 사용자 인증 정보 → OAuth 클라이언트 ID → 유형 **데스크톱 앱** → 클라이언트 ID/보안 비밀 복사.
4. 내 PC에서:
   ```powershell
   $env:YT_CLIENT_ID="..."; $env:YT_CLIENT_SECRET="..."
   .venv\Scripts\python.exe -m pipeline.youtube auth
   ```
   브라우저에서 채널 계정으로 로그인 → 출력되는 리프레시 토큰 복사.
5. GitHub Secrets에 `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` 저장.
6. **중요**: 감사(audit)를 받지 않은 API 프로젝트로 올린 영상은 YouTube가 강제로 **비공개**로 잠급니다.
   공개 업로드를 하려면 YouTube API 감사 신청 양식(YouTube API Services - Audit and Quota Extension Form)을 제출해야 합니다.
   승인 전까지는 영상이 비공개로 쌓이며, 승인 후 YouTube Studio에서 공개로 바꿀 수 있습니다.

YouTube 키가 없으면 영상은 업로드되지 않고 Actions 실행 화면의 Artifacts(`shorts-번호`)로 30일간 보관됩니다.

**음성(TTS)**: 기본값 `edge`는 무료지만 Microsoft의 비공식 경로라 언제든 막힐 수 있고 상업적 이용 조건이 불명확합니다.
수익화가 시작되면 Google Cloud Text-to-Speech(`tts_provider = "google"`, Secret `GOOGLE_TTS_API_KEY`)로 바꾸는 것을 권장합니다.

데모 영상 만들기: `.venv\Scripts\python.exe -m pipeline.run shorts --demo --tts edge` → `videos/` 폴더

## 다음 단계
- TikTok 업로드(Content Posting API — 앱 심사 전에는 비공개 게시만 가능), Instagram Reels(Graph API, 비즈니스 계정 필요)
- Phase 3: Search Console·YouTube Analytics 성과를 주간으로 읽어 주제·제목·프롬프트를 스스로 조정하는 개선 루프
