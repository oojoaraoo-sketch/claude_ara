# 처음 설정하기 (쉬운 안내서)

모두 무료입니다. 결제 수단을 등록하라는 화면이 나오면 건너뛰세요.
총 4단계, 30~40분 정도 걸립니다. **비밀번호·키는 직접 입력**해 주세요 (Claude는 보안상 대신 입력하지 않습니다).

---

## 1단계. 공공데이터포털 인증키 받기 (약 10분)

실거래 데이터를 가져오는 열쇠입니다.

1. https://www.data.go.kr 접속 → 오른쪽 위 **회원가입** → 일반회원(개인)으로 가입합니다.
2. 로그인 후 위쪽 검색창에 `아파트 매매 실거래가 상세` 입력 → 검색.
3. 결과 중 **"국토교통부_아파트 매매 실거래가 상세 자료"** (오픈 API 탭)를 누릅니다.
4. 파란 **활용신청** 버튼 → 활용목적에 `웹 사이트 개발`, 내용에 `실거래가 통계 블로그` 정도로 적고 → 약관 동의 → **활용신청**.
   개발계정은 보통 바로 자동 승인됩니다.
5. 오른쪽 위 **마이페이지** → **데이터 활용** → **Open API** → **활용신청 현황** → 방금 신청한 항목 클릭.
6. **일반 인증키 (Decoding)** 칸의 긴 글자를 복사해 메모장에 잠시 붙여 둡니다.
   - 승인 직후 1시간 정도는 키가 아직 안 먹을 수 있습니다. 정상입니다.

## 2단계. Claude 구독 토큰 만들기 (약 3분)

파이프라인이 매일 새벽 사용자의 Claude 구독으로 글을 쓰게 하는 출입증입니다. (API 키가 아니므로 추가 요금 없음)

1. Claude가 열어 드린 터미널 탭에서(또는 직접 PowerShell을 열고) 아래를 실행합니다:
   ```powershell
   & (Get-ChildItem "$env:APPDATA\Claude\claude-code" -Recurse -Filter claude.exe | Select-Object -Last 1).FullName setup-token
   ```
2. 브라우저가 열리면 평소 쓰는 Claude 계정으로 로그인 → **승인**.
3. 터미널에 `sk-ant-oat...` 로 시작하는 긴 토큰이 나옵니다. 복사해서 메모장에 붙여 둡니다.
   - 이 토큰은 비밀번호와 같습니다. 다른 사람에게 보내거나 채팅에 붙여넣지 마세요.

## 3단계. GitHub에 올리기 (약 10분)

GitHub가 매일 새벽 6시에 파이프라인을 대신 돌려 주고, 블로그도 무료로 호스팅해 줍니다.

1. https://github.com 가입(무료, Free 플랜). 개인 아이디가 블로그 주소에 드러나지 않도록 저장소는 무료 조직
   `silgeorae-report` 아래 `silgeorae-report.github.io` 이름으로 둡니다 → 블로그 주소 `https://silgeorae-report.github.io/`.
2. Claude에게 "GitHub 가입했어"라고 알려 주세요. Claude가 GitHub CLI를 설치하고 저장소 만들기·코드 올리기를 진행합니다.
   - 중간에 `gh auth login` 화면이 나오면 브라우저에서 GitHub 로그인 → 화면의 8자리 코드 입력 → 승인만 해 주시면 됩니다.

   (직접 하고 싶다면: 오른쪽 위 **+** → **New repository** → 이름 `claude_ara`, **Public** 선택 → Create. 이후 Claude에게 주소를 알려 주세요.)

## 4단계. 비밀값 등록하기 (약 5분)

저장소 페이지에서:

1. 위쪽 **Settings** → 왼쪽 **Secrets and variables** → **Actions**.
2. **Secrets** 탭 → **New repository secret** 버튼을 눌러 아래 두 개를 하나씩 추가:

   | Name (정확히 이대로) | Secret (값) |
   |---|---|
   | `DATA_GO_KR_KEY` | 1단계에서 복사한 인증키 |
   | `CLAUDE_CODE_OAUTH_TOKEN` | 2단계에서 복사한 토큰 |

3. **Variables** 탭 → **New repository variable**:

   | Name | Value |
   |---|---|
   | `SITE_BASE_URL` | `https://silgeorae-report.github.io` |

4. 왼쪽 메뉴 **Pages** → **Source**를 **GitHub Actions** 로 선택.
5. 위쪽 **Actions** 탭 → (처음이면 "I understand… enable" 버튼) → 왼쪽 **daily-pipeline** → 오른쪽 **Run workflow** → 초록 버튼.
6. 10~30분 뒤 초록 체크가 뜨면 `https://silgeorae-report.github.io` 에서 블로그를 확인합니다.
   빨간 X가 뜨면 GitHub가 이메일을 보내고, Claude에게 "Actions 실패했어"라고 알려 주시면 원인을 찾아 고칩니다.

이후로는 매일 새벽 6시에 자동으로 돌아갑니다.

---

## (나중에) YouTube 연결

블로그가 잘 돌아가는 걸 확인한 뒤 진행하면 됩니다. README.md의 "YouTube 연결" 절을 따르거나 Claude에게 "유튜브 연결하자"라고 말해 주세요.

## 멈추고 싶을 때
저장소 **Settings → Secrets and variables → Actions → Variables** 에 `PIPELINE_ENABLED` = `false` 를 추가하면 전부 멈춥니다.
