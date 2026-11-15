# 클립보드에 복사한 값을 GitHub Secret으로 등록한다. 값은 화면에 표시되지 않는다.
# 사용법: 값을 Ctrl+C 복사 → .\scripts\set_secret.ps1 -Name PEXELS_API_KEY
param([Parameter(Mandatory = $true)][string]$Name)
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$repo = "silgeorae-report/silgeorae-report.github.io"
$val = (Get-Clipboard -Raw)
if ($null -eq $val) { $val = "" }
$val = $val.Trim()
if ($val.Length -lt 16 -or $val -match "\s") {
    Write-Host "클립보드에 키가 없습니다. 키를 Ctrl+C로 복사한 뒤 다시 실행하세요."
    exit 1
}
& $gh secret set $Name --repo $repo --body $val
if ($LASTEXITCODE -eq 0) {
    Write-Host "등록 완료: $Name (길이 $($val.Length)자)"
    Set-Clipboard -Value " "
}
