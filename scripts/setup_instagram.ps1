# Instagram 시스템 사용자 토큰을 GitHub Secrets에 등록한다. 토큰 값은 화면에 표시되지 않는다.
# 사용법: 비즈니스 설정 > 시스템 사용자 > 토큰 생성 → 토큰을 Ctrl+C 복사 → 이 스크립트 실행
#   .\scripts\setup_instagram.ps1 -IgUserId 1784xxxxxxxxxxxx
param([Parameter(Mandatory = $true)][string]$IgUserId)
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$repo = "silgeorae-report/silgeorae-report.github.io"

$tok = (Get-Clipboard -Raw)
if ($null -eq $tok) { $tok = "" }
$tok = $tok.Trim()
if ($tok.Length -lt 50 -or $tok -match "\s") {
    Write-Host "클립보드에 토큰이 없습니다. 토큰을 Ctrl+C로 복사한 뒤 다시 실행하세요."
    exit 1
}

# 토큰이 이 Instagram 계정에 게시할 수 있는지 확인 (토큰은 출력하지 않음)
try {
    $me = Invoke-RestMethod -Uri "https://graph.facebook.com/$IgUserId" -Method Get -Body @{ fields = "username"; access_token = $tok }
    Write-Host "확인됨: Instagram 계정 @$($me.username)"
} catch {
    Write-Host "토큰 확인 실패: 시스템 사용자에게 Instagram 계정 권한과 instagram_content_publish 권한이 있는지 확인하세요."
    exit 1
}

& $gh secret set IG_ACCESS_TOKEN --repo $repo --body $tok   # 파이프는 인코딩·줄바꿈이 섞일 수 있음
& $gh secret set IG_USER_ID --repo $repo --body $IgUserId
if ($LASTEXITCODE -eq 0) {
    Write-Host "등록 완료: IG_ACCESS_TOKEN (길이 $($tok.Length)자), IG_USER_ID"
    Set-Clipboard -Value " "   # 클립보드에서 토큰 지우기
}
