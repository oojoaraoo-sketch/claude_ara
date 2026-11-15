# 클립보드에 복사한 공공데이터포털 인증키(Decoding)를 GitHub Secret DATA_GO_KR_KEY로 등록한다.
# 키는 화면에 표시되지 않는다.  사용법: 키를 Ctrl+C 복사 → .\scripts\set_data_key.ps1
$key = (Get-Clipboard -Raw)
if ($null -eq $key) { $key = "" }
$key = $key.Trim()
if ($key.Length -lt 20 -or $key -match "\s") {
    Write-Host "클립보드에 인증키가 없습니다. 인증키(Decoding)를 Ctrl+C로 복사한 뒤 다시 실행하세요."
    exit 1
}
$key | & "C:\Program Files\GitHub CLI\gh.exe" secret set DATA_GO_KR_KEY --repo oojoaraoo-sketch/claude_ara
if ($LASTEXITCODE -eq 0) { Write-Host "등록 완료 (길이 $($key.Length)자, 앞 4자리 $($key.Substring(0,4))…)" }
