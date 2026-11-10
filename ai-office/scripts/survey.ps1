# 1단계: 설치 환경 자동 조사 (읽기 전용 — 아무것도 바꾸지 않습니다)
# 결과: <데이터 폴더>\reports\환경조사_<날짜>.md
param([switch]$Quiet)
. (Join-Path $PSScriptRoot 'common.ps1')
$ErrorActionPreference = 'Continue'

$lines = New-Object System.Collections.Generic.List[string]
function Add([string]$s) { $lines.Add($s) | Out-Null; if (-not $Quiet) { Write-Host $s } }
# 오래 걸리거나 응답 없이 기다리는 명령은 별도 작업으로 돌리고 제한 시간이 지나면 건너뛴다
function Invoke-Timed([scriptblock]$sb, [int]$sec, [object[]]$argList) {
  if ($argList -and $argList.Count) { $j = Start-Job -ScriptBlock $sb -ArgumentList $argList } else { $j = Start-Job -ScriptBlock $sb }
  $out = $null
  if (Wait-Job $j -Timeout $sec) { $out = Receive-Job $j 2>&1 | Out-String } else { Stop-Job $j }
  Remove-Job $j -Force
  return $out
}
function Ver([string]$cmd, [string[]]$a) {
  if (-not (Test-Cmd $cmd)) { return '없음' }
  try { $o = & $cmd @a 2>&1 | Select-Object -First 1; return ([string]$o).Trim() } catch { return '확인 실패' }
}

Add "# AI 사무실 환경 조사 ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))"
Add ''
Add '## 프로그램'
Add "- Windows: $((Get-CimInstance Win32_OperatingSystem).Caption) $((Get-CimInstance Win32_OperatingSystem).Version)"
Add "- Node.js: $(Ver 'node' @('--version'))  (AI 사무실 실행에 필요, 20 이상)"
Add "- Git: $(Ver 'git' @('--version'))"
Add "- Python(py): $(Ver 'py' @('-3', '--version'))"
$claude = Get-Command claude -ErrorAction SilentlyContinue
if ($claude) { Add "- Claude Code: $(Ver 'claude' @('--version')) — $($claude.Source)" } else { Add '- Claude Code: 찾지 못함' }
Add "- Docker: $(Ver 'docker' @('--version'))"
$ppt = $null
try { $ppt = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\POWERPNT.EXE' -ErrorAction Stop).'(default)' } catch { }
if ($ppt) { Add "- PowerPoint: 설치됨 ($ppt) — PPT 렌더가 가장 정확합니다" } else { Add '- PowerPoint: 찾지 못함 — LibreOffice 또는 근사 렌더 사용' }

Add ''
Add '## 기존 Claude 에이전트'
$slideSrc = 'C:\JY\slide-svg'
foreach ($p in @($slideSrc, 'C:\AI-OFFICE\agents\slide-svg')) {
  if (Test-Path $p) {
    $sk = @(Get-ChildItem (Join-Path $p '.claude\skills') -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.Name }) -join ', '
    $venv = Test-Path (Join-Path $p '.venv\Scripts\python.exe')
    $envf = Test-Path (Join-Path $p 'automation\cafe_inquiry\.env')
    Add "- $p : 스킬 [$sk] · 가상환경 $(if ($venv) {'있음'} else {'없음'}) · 교육문의 .env $(if ($envf) {'있음'} else {'없음'})"
  } else { Add "- $p : 없음" }
}
foreach ($p in @('C:\AI-OFFICE\agents\insight1-cardnews', 'C:\AI-OFFICE\insight1')) {
  if (Test-Path (Join-Path $p '.claude\skills\cardnews\SKILL.md')) { Add "- $p : /cardnews 스킬 있음" } elseif (Test-Path $p) { Add "- $p : 폴더는 있으나 /cardnews 스킬 없음" }
}
$ud = Join-Path $env:USERPROFILE '.claude'
foreach ($sub in @('skills', 'agents', 'commands')) {
  $names = @(Get-ChildItem (Join-Path $ud $sub) -ErrorAction SilentlyContinue | ForEach-Object { $_.Name }) -join ', '
  if ($names) { Add "- 사용자 $sub : $names" } else { Add "- 사용자 $sub : 없음" }
}
$sched = Join-Path $ud 'scheduled-tasks'
if (Test-Path $sched) {
  $t = @(Get-ChildItem $sched -ErrorAction SilentlyContinue | ForEach-Object { $_.Name }) -join ', '
  Add "- Claude 데스크톱 예약 작업: $t  ← 교육문의 예약 작업이 있으면 AI 사무실 'n8n 작업대기 처리'와 동시에 켜지 마세요"
}
if ($claude) {
  try {
    if (-not $Quiet) { Write-Host '  (Claude 연결 목록 확인 중 — 최대 25초)' }
    $mcp = Invoke-Timed { & claude mcp list 2>&1 } 25 @()
    if ($null -eq $mcp) { throw '시간 초과' }
    $names = @($mcp -split "`r?`n" | Where-Object { $_ -match '^\S+:' } | ForEach-Object { ($_ -split ':')[0] }) -join ', '
    Add "- Claude MCP 서버: $(if ($names) { $names } else { '없음 또는 확인 실패' })"
  } catch { Add '- Claude MCP 서버: 확인 실패' }
}

Add ''
Add '## n8n (Docker)'
$c = Get-N8nContainer
if ($c) {
  Add "- 컨테이너: $c"
  Add "- 이미지: $(& docker inspect -f '{{.Config.Image}}' $c 2>$null)"
  $nv = Invoke-Timed { param($name) & docker exec $name n8n --version 2>$null } 30 @($c)
  Add "- n8n 버전: $(if ($nv) { ($nv.Trim() -split "`r?`n")[-1] } else { '확인 못 함(시간 초과)' })"
  Add "- 포트: $((& docker port $c 2>$null) -join ', ')"
  Add "- 연결 폴더: $(& docker inspect -f '{{range .Mounts}}{{.Source}} -> {{.Destination}}; {{end}}' $c 2>$null)"
  try {
    if (-not $Quiet) { Write-Host '  (n8n 워크플로 목록 읽는 중 — 최대 60초)' }
    $wf = Invoke-Timed { param($name) & docker exec $name n8n list:workflow 2>$null } 60 @($c)
    if ($null -eq $wf) { Add '- 워크플로 목록: 시간 초과로 건너뜀' }
    else {
      Add '- 워크플로 목록(이름만 읽음, 바꾸지 않음):'
      foreach ($w in ($wf -split "`r?`n")) { if ($w -match '\|') { Add "  - $w" } }
    }
  } catch { Add '- 워크플로 목록: 읽기 실패' }
} else { Add '- n8n 컨테이너를 찾지 못했습니다(Docker Desktop 이 켜져 있는지 확인)' }
try { $h = Invoke-WebRequest -Uri 'http://localhost:5678/healthz' -UseBasicParsing -TimeoutSec 3; Add "- http://localhost:5678 응답: $($h.StatusCode)" } catch { Add '- http://localhost:5678 응답 없음' }

Add ''
Add '## C:\AI-OFFICE 폴더'
if (Test-Path 'C:\AI-OFFICE') { Get-ChildItem 'C:\AI-OFFICE' -Directory | ForEach-Object { Add "- $($_.Name)" } } else { Add '- 없음' }

$dir = Join-Path (Get-DataDir) 'reports'
$file = Join-Path $dir ("환경조사_" + (Get-Date -Format 'yyyyMMdd_HHmm') + '.md')
Write-TextFile $file (($lines -join "`r`n") + "`r`n")
Write-Host ''
Write-Ok "조사 결과 저장: $file"
