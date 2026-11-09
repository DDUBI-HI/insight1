# AI 사무실 켜기 — 이미 켜져 있으면 화면만 엽니다.
param([switch]$NoBrowser)
. (Join-Path $PSScriptRoot 'common.ps1')

if (-not (Test-Cmd 'node')) { Write-Bad 'Node.js 가 없습니다. SETUP-AI-OFFICE.bat 을 먼저 실행하세요.'; exit 1 }
$port = Get-Port
if (-not (Test-Health $port)) {
  $logDir = Join-Path (Get-DataDir) 'logs'
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  $server = Join-Path $Script:AppRoot 'bridge\server.mjs'
  Start-Process -FilePath 'node' -ArgumentList "`"$server`"" -WorkingDirectory $Script:AppRoot -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $logDir 'bridge.log') -RedirectStandardError (Join-Path $logDir 'bridge-error.log')
  $ok = $false
  for ($i = 0; $i -lt 20; $i++) { Start-Sleep -Milliseconds 500; if (Test-Health $port) { $ok = $true; break } }
  if (-not $ok) { Write-Bad "AI 사무실을 켜지 못했습니다. 기록: $logDir\bridge-error.log"; exit 1 }
  Write-Ok "AI 사무실을 켰습니다 (http://127.0.0.1:$port/)"
} else { Write-Ok 'AI 사무실이 이미 켜져 있습니다' }
if (-not $NoBrowser) {
  Start-Process "http://127.0.0.1:$port/"
  Start-Process "http://127.0.0.1:$port/control.html"
}
