# AI 사무실 끄기 (진행 중인 작업이 있으면 중단됩니다)
. (Join-Path $PSScriptRoot 'common.ps1')
$pidFile = Join-Path (Get-DataDir) 'run\bridge.pid'
if (-not (Test-Path $pidFile)) { Write-Warn2 '켜져 있지 않습니다'; exit 0 }
$info = [System.IO.File]::ReadAllText($pidFile) | ConvertFrom-Json
$p = Get-Process -Id $info.pid -ErrorAction SilentlyContinue
if ($p -and $p.ProcessName -eq 'node') { Stop-Process -Id $info.pid -Force; Write-Ok 'AI 사무실을 껐습니다' } else { Write-Warn2 '이미 꺼져 있습니다' }
Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
