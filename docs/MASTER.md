# 실거래가 리포트 — 마스터 문서

> 이 문서는 프로젝트의 **변하지 않는 기준**(목표·원칙·구조·계정·운영 방법)을 담는다.
> 진행 상황과 할 일은 [STATUS.md](STATUS.md)에 적는다. 구조나 계정·원칙이 바뀌면 이 문서를 같은 커밋에서 고친다.

## 1. 목표
- 국토교통부 아파트 매매 실거래가 공개 데이터로 서울 25개 구의 콘텐츠를 **사람 개입 없이** 매일 만들고, 올리고, 관리하고, 개선한다.
- 수익: 블로그 광고(애드센스, 글이 쌓인 뒤 신청), YouTube·Instagram·TikTok 채널 성장.

## 2. 운영 원칙 (사용자 지시)
| 원칙 | 내용 |
|---|---|
| 무료 | 유료 결제가 필요한 수단은 쓰지 않는다 (API 종량 과금, 유료 TTS, 도메인 구입 없음). Claude는 구독 토큰으로 호출 |
| 모델 | 기본 모델은 Opus (`claude-opus-5-5`) |
| 개인정보 | 개인 연락처·본명·구글 이메일이 들어간 아이디는 공개되면 안 된다. 계정 아이디는 그대로 두되, URL·설명 등 공개되는 곳에는 넣지 않는다 |
| 품질 | 완전 자동화이므로 품질은 Claude가 직접 보고 검토한다 (자동 검사 + Claude 2차 검수 + 정기 직접 검토) |
| 언어 | 사용자에게 하는 설명·보고는 한국어 |
| 문서 | 변경이 있을 때마다 MASTER.md / STATUS.md / 현황 아티팩트를 갱신한다 |
| 브라우저 | 웹 설정 작업은 필요하면 크롬(Claude in Chrome)을 직접 조작한다. 비밀번호·인증 코드·토큰 값은 Claude가 입력하거나 보지 않는다 |

## 3. 전체 구조
```
매일 06:00 KST  GitHub Actions (daily-pipeline)
  run       : 테스트 → 수집(data.go.kr) → 글 생성(Claude CLI) → 규칙 검사 → Claude 2차 검수 → 사이트 빌드
              → 숏츠 생성(Pillow+ffmpeg+TTS) → YouTube 업로드 → DB 커밋
  deploy    : GitHub Pages 배포 (public/, media/*.mp4 포함)
  instagram : 방금 배포된 mp4 URL로 릴스 게시 (Graph API, 시스템 사용자 토큰)
  report    : 오류가 있으면 실패 표시 → GitHub 이메일 알림
매일 08:10 KST  이 PC의 Claude 예약 작업 "틱톡 숏츠 자동 업로드"
  scripts/tiktok_prepare.py 로 대기열 준비 → 크롬(Claude in Chrome)으로 TikTok Studio 업로드 (하루 최대 2편)
```
- DB: `data/pipeline.db` (SQLite, 저장소에 커밋). 테이블: trades, posts, videos, social_posts, runs, rejections 등
- 실행 요약: `data/last_run.json` (비밀값 자동 제거)

## 4. 코드 지도
| 파일 | 역할 |
|---|---|
| `config.toml` | 모든 설정 (사이트 주소, 수집 기간, 모델, 숏츠·YouTube·Instagram 옵션, 킬 스위치) |
| `pipeline/collect.py` | 실거래 API 수집. 오류 메시지에 URL·키를 남기지 않음 |
| `pipeline/analyze.py` | 구·월별 facts 계산 (median_ppp=3.3㎡당, top_apt_umd=최고가 단지 동, top_umd=거래 최다 동) |
| `pipeline/write.py` | Claude CLI 호출, 글쓰기 지침(facts 정의), 2차 검수 프롬프트 |
| `pipeline/qa.py` | 규칙 검사(근거 없는 숫자·금지어·마커), 플레이스홀더 채우기와 조사 자동 교정 |
| `pipeline/generate.py` | 글 계획·생성. 지적을 피드백으로 최대 3회 작성 |
| `pipeline/shorts.py`, `render.py`, `tts.py` | 숏츠 대본·장면 렌더·음성(edge → gTTS) |
| `pipeline/youtube.py` | YouTube Data API 업로드 (공개) |
| `pipeline/instagram.py` | 릴스 게시 (시스템 사용자 토큰=graph.facebook.com / IG 토큰=graph.instagram.com) |
| `pipeline/site.py` | 정적 사이트 빌드, sitemap, media 복사 |
| `pipeline/run.py` | 명령 진입점 (`all`, `instagram` 등), 비밀값 마스킹 |
| `scripts/tiktok_prepare.py` | TikTok 업로드 대기열/기록 (`--done <slug>`) |
| `scripts/set_data_key.ps1`, `setup_instagram.ps1` | 클립보드의 비밀값을 화면에 표시하지 않고 GitHub Secrets에 등록 |
| `tests/test_pipeline.py` | 단위·통합 테스트 (실패하면 발행 안 함) |

## 5. 계정·서비스
> 이 저장소는 공개다. 계정 아이디·내부 ID는 로컬 전용 `private/ACCOUNTS.md`(git 제외)에만 적고, 비밀값은 어디에도 적지 않는다.

| 서비스 | 식별 정보 | 비고 |
|---|---|---|
| GitHub | 조직 `silgeorae-report`, 저장소 `silgeorae-report/silgeorae-report.github.io` (공개) | 개인 계정은 조직 비공개 멤버 |
| 블로그 | https://silgeorae-report.github.io/ | GitHub Pages (Actions 배포) |
| 공공데이터포털 | 아파트 매매 실거래가 상세 (Dev 엔드포인트) | Secret `DATA_GO_KR_KEY` (재발급본) |
| Claude | 구독 토큰 | Secret `CLAUDE_CODE_OAUTH_TOKEN` |
| YouTube | 채널 "실거래가 리포트" (Google Cloud OAuth 앱, 프로덕션 게시) | Secrets `YT_CLIENT_ID/SECRET/REFRESH_TOKEN`. 채널 휴대폰 인증 완료 |
| Instagram | 크리에이터 계정 | Meta 비즈니스 포트폴리오 "실거래가 리포트", 앱(개발 모드), 시스템 사용자, 만료 없는 토큰. Secrets `IG_ACCESS_TOKEN`, `IG_USER_ID` |
| TikTok | 표시 이름 "실거래가 리포트" | API 미사용 (미심사 앱은 비공개만 가능) → 크롬 예약 작업으로 업로드 |
| 저장소 변수 | `SITE_BASE_URL=https://silgeorae-report.github.io` | `PIPELINE_ENABLED=false` 로 두면 전체 중단 |

## 6. 운영 방법
- 수동 실행: GitHub → Actions → daily-pipeline → Run workflow (또는 `gh workflow run daily-pipeline --repo silgeorae-report/silgeorae-report.github.io`)
- 긴급 중단: 저장소 변수 `PIPELINE_ENABLED=false` 또는 `config.toml`의 `[safety] enabled=false`
- 로컬 테스트: `.venv\Scripts\python.exe -m unittest discover -s tests`
- 비밀값 교체: 값을 Ctrl+C → `scripts\set_data_key.ps1` 또는 `scripts\setup_instagram.ps1 -IgUserId <ID>`
- 품질 검토(Claude): 실행 후 `data/last_run.json`의 published/rejected 확인, 새 글 본문 직접 읽기, 알려진 오류 패턴(㎡당·재건축·학군·소재지) 검색
- 커밋 규칙: `-c user.name=pipeline-setup -c user.email=pipeline-setup@users.noreply.github.com`, 데이터 커밋은 봇이 함

## 7. 하지 않기로 한 것
- TikTok Content Posting API: 미심사 앱은 비공개 게시만 가능하고 "자기 계정 업로드 도구"는 심사에서 거절되는 유형
- 유료 도메인·유료 TTS·Claude API 종량 과금
