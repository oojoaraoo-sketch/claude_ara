# Instagram 토큰을 GitHub Secrets에 등록한다. 값은 화면에 표시되지 않는다.
# 사용법: Meta 앱 대시보드에서 생성한 Instagram 액세스 토큰을 Ctrl+C 복사 → 이 스크립트 실행
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$repo = "oojoaraoo-sketch/claude_ara"
$root = Split-Path $PSScriptRoot -Parent

$tok = (Get-Clipboard -Raw)
if ($null -eq $tok) { $tok = "" }
$tok = $tok.Trim()
if ($tok.Length -lt 50 -or $tok -match "\s") {
    Write-Host "클립보드에 Instagram 토큰이 없습니다. 토큰을 Ctrl+C로 복사한 뒤 다시 실행하세요."
    exit 1
}

# 토큰 상태 파일 암호화 키 (새로 만들고 등록)
$key = & "$root\.venv\Scripts\python.exe" -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
$key | & $gh secret set IG_STATE_KEY --repo $repo
$tok | & $gh secret set IG_ACCESS_TOKEN --repo $repo
if ($LASTEXITCODE -eq 0) {
    Write-Host "등록 완료: IG_ACCESS_TOKEN (길이 $($tok.Length)자), IG_STATE_KEY"
    Set-Clipboard -Value " "   # 클립보드에서 토큰 지우기
}
