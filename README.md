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

## 비용 원칙: 유료 결제 수단 없음

| 구성 요소 | 사용하는 것 | 비용 |
|---|---|---|
| 글·대본 작성(Claude) | Claude Code CLI + 기존 Claude 구독 토큰 (`claude setup-token`) | 추가 결제 없음 (구독 사용 한도 안에서 동작, API 종량 과금 안 씀) |
| 데이터 | 공공데이터포털 API | 무료 |
| 실행 | GitHub Actions (public 저장소) | 무료 |
| 호스팅 | GitHub Pages (`<아이디>.github.io`) | 무료 (도메인 구입 안 함) |
| 음성 | edge-tts → 실패 시 gTTS | 무료 |
| 영상 업로드 | YouTube Data API | 무료 (결제 계정 등록 불필요) |

Anthropic API 키(`ANTHROPIC_API_KEY`)는 쓰지 않으며, 실수로 환경에 있더라도 코드가 Claude CLI에 넘기지 않아 종량 과금이 발생하지 않습니다.
구독 사용 한도에 걸리면 그날 생성은 멈추고 다음 실행에서 이어서 진행합니다.

## 설치해야 할 것 (한 번만)

1. **공공데이터포털 키**: data.go.kr 가입 → "국토교통부_아파트 매매 실거래가 상세 자료" 활용신청 → 마이페이지의 **일반 인증키(Decoding)** 복사.
2. **Claude 구독 토큰**: Claude Code가 설치된 PC 터미널에서 `claude setup-token` 실행 → 브라우저 로그인 → 출력된 토큰 복사(약 1년 유효).
   Claude Code를 따로 설치하지 않았다면 `npm install -g @anthropic-ai/claude-code` (Node.js 필요, 무료).
3. **GitHub 저장소**: github.com에서 새 **public** 저장소 생성 후 이 폴더를 push (private이면 Pages가 유료 요금제 필요).
   - Settings → Secrets and variables → Actions
     - Secrets: `CLAUDE_CODE_OAUTH_TOKEN`, `DATA_GO_KR_KEY`
     - Variables: `SITE_BASE_URL` = `https://<아이디>.github.io/<저장소>`
   - Settings → Pages → Source: **GitHub Actions**
4. Actions 탭 → daily-pipeline → **Run workflow** 로 첫 실행. 첫 실행은 13개월치를 수집합니다.
5. 글이 20~30편 이상 쌓이면 Google Search Console 등록(사이트맵: `/sitemap.xml`, 무료), 이후 AdSense 신청(무료). 승인되면 `config.toml`의 `adsense_client`에 값을 넣습니다.
   (`github.io` 하위 경로 사이트는 AdSense 승인이 어려울 수 있습니다. 그 경우에도 YouTube 수익화와 블로그 트래픽은 그대로 쌓입니다.)

## 로컬 실행

```powershell
.venv\Scripts\python.exe -m pipeline.run all --demo     # 키 없이 가상 데이터로 전체 시험
.venv\Scripts\python.exe -m unittest discover -s tests  # 테스트
.venv\Scripts\python.exe -m http.server 8000 --directory public   # 결과 보기
```

실데이터로 로컬 실행하려면 Claude Code에 로그인된 상태(또는 `CLAUDE_CODE_OAUTH_TOKEN`)에서 `DATA_GO_KR_KEY`를 설정하고 `--demo` 없이 실행합니다.
`claude`가 PATH에 없으면 `CLAUDE_BIN`에 실행 파일 경로를 넣습니다.

## 운영
- **멈추기**: 저장소 Variables에 `PIPELINE_ENABLED=false` (워크플로 전체 중단) 또는 `config.toml`의 `safety.enabled=false` (생성만 중단, 수집·빌드는 계속).
- **상태 확인**: Actions 실행 화면의 Summary, 또는 `data/last_run.json` (발행/반려 목록, Claude 호출 수).
- **구독 한도 조절**: `config.toml`의 `max_new_posts_per_run`, `model`, `effort`, `llm_review`.

## Phase 2: 숏폼 영상 (YouTube Shorts)

월간 리포트 글마다 약 30~45초 세로 영상(1080x1920)을 자동으로 만듭니다(하루 최대 2편).
Claude가 장면별 대본을 쓰되 블로그와 같은 플레이스홀더 규칙을 따르므로 영상 속 숫자도 원자료와 일치합니다.
설명란에는 블로그 글 링크가 들어가고, 업로드된 영상은 블로그 글 하단에 자동으로 임베드됩니다.

```
글(facts) → 대본(Claude, 자동 검수) → 음성(TTS) → 장면 이미지 6장 → ffmpeg 합성 → YouTube 업로드
```

**YouTube 연결 (사용자가 직접, 최초 1회)**
1. console.cloud.google.com → 새 프로젝트 → "YouTube Data API v3" 사용 설정. (결제 계정 연결은 필요 없습니다. 무료 체험·결제 등록 안내가 나오면 건너뛰세요.)
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
6. 감사(audit)는 필요 없습니다. 2026-11-02 YouTube Data API 정책 변경으로 미검증 프로젝트의 업로드도 공개 게시가 가능합니다
   (그 전에는 비공개로 잠겼음). 기본 할당량(하루 10,000 단위 ≈ 업로드 6편)을 넘길 때만 할당량 증설 신청이 필요합니다.

YouTube 키가 없으면 영상은 업로드되지 않고 Actions 실행 화면의 Artifacts(`shorts-번호`)로 30일간 보관됩니다.

**음성(TTS)**: 기본값 `auto`는 edge-tts(Microsoft 음성)를 쓰고, 막히면 gTTS(Google 번역 음성)로 자동 전환합니다. 둘 다 무료지만
공식 상용 API가 아닌 비공식 경로라 언제든 막힐 수 있고 상업적 이용 조건이 명확하지 않습니다. 둘 다 실패하면 그날 영상만 건너뜁니다.

데모 영상 만들기: `.venv\Scripts\python.exe -m pipeline.run shorts --demo --tts auto` → `videos/` 폴더

## 다음 단계
- TikTok 업로드(Content Posting API — 앱 심사 전에는 비공개 게시만 가능), Instagram Reels(Graph API, 비즈니스 계정 필요)
- Phase 3: Search Console·YouTube Analytics 성과를 주간으로 읽어 주제·제목·프롬프트를 스스로 조정하는 개선 루프
