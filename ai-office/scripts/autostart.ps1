# PC 를 켜고 로그인하면 AI 사무실이 저절로 켜지게(시작프로그램 바로가기). -Remove 로 끕니다. 관리자 권한 필요 없음.
param([switch]$Remove)
. (Join-Path $PSScriptRoot 'common.ps1')
$startup = [Environment]::GetFolderPath('Startup')
$lnk = Join-Path $startup 'AI 사무실 자동 시작.lnk'
if ($Remove) {
  if (Test-Path $lnk) { Remove-Item $lnk -Force; Write-Ok '자동 시작을 껐습니다' } else { Write-Warn2 '자동 시작이 이미 꺼져 있습니다' }
  exit 0
}
$ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$arg = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$(Join-Path $PSScriptRoot 'start.ps1')`" -NoBrowser"
New-Shortcut $lnk $ps $arg $Script:AppRoot 'AI 사무실 자동 시작'
Write-Ok "자동 시작을 켰습니다: $lnk"
