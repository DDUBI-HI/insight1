# 연결 시험: ① 이 PC → AI 사무실  ② n8n(Docker) → AI 사무실  ③ 이 PC → n8n
. (Join-Path $PSScriptRoot 'common.ps1')
$ErrorActionPreference = 'Continue'
$port = Get-Port
Write-Step '① 이 PC → AI 사무실'
if (Test-Health $port) { Write-Ok "http://127.0.0.1:$port 응답 정상" } else { Write-Bad 'AI 사무실이 꺼져 있습니다 — START-AI-OFFICE.bat 을 먼저 실행하세요'; exit 1 }

Write-Step '② n8n(Docker) → AI 사무실'
$c = Get-N8nContainer
if (-not $c) { Write-Bad 'n8n 컨테이너를 찾지 못했습니다(Docker Desktop 확인)' }
else {
  $js = "fetch('http://host.docker.internal:$port/api/health').then(r=>r.text()).then(t=>console.log(t)).catch(e=>console.log('ERR '+e.message))"
  $out = & docker exec $c node -e $js 2>&1 | Out-String
  if ($out -match '"app":"ai-office"') { Write-Ok "n8n 컨테이너($c)에서 접속 성공 — n8n 의 주소는 http://host.docker.internal:$port 를 쓰면 됩니다" }
  else {
    Write-Bad "n8n 컨테이너에서 접속 실패: $($out.Trim())"
    Write-Host '   해결: config.json 의 "bindHost" 를 "0.0.0.0" 으로 바꾸고 AI 사무실을 다시 켠 뒤 다시 시험하세요.'
    Write-Host '         (그러면 같은 네트워크의 다른 PC 도 접속을 시도할 수 있습니다. 토큰 없이는 작업을 못 시키지만,'
    Write-Host '          Windows 방화벽에서 이 포트를 "개인 네트워크"만 허용으로 두세요.)'
  }
}

Write-Step '③ 이 PC → n8n'
try { $h = Invoke-WebRequest -Uri 'http://localhost:5678/healthz' -UseBasicParsing -TimeoutSec 3; Write-Ok "n8n 응답 $($h.StatusCode)" } catch { Write-Bad 'http://localhost:5678 응답 없음' }
