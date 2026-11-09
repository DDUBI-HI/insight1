# AI 사무실 설치 (처음 한 번). 단계마다 물어보고, 기존 파일은 지우거나 덮어쓰지 않습니다.
#   1) 환경 조사  2) Node.js 확인  3) 기존 시스템 백업  4) 에이전트 작업용 복사본 만들기
#   5) 설정 파일 만들기  6) AI 사무실 켜기  7) 바로가기·자동 시작  8) 연결 시험
param([switch]$Yes, [string]$SlideSvg = 'C:\JY\slide-svg')
. (Join-Path $PSScriptRoot 'common.ps1')
$Script:AssumeYes = [bool]$Yes
$ErrorActionPreference = 'Continue'
$agents = 'C:\AI-OFFICE\agents'
$slideCopy = Join-Path $agents 'slide-svg'
$cardCopy = Join-Path $agents 'insight1-cardnews'

Write-Host ''
Write-Host '==============================================' -ForegroundColor Cyan
Write-Host '   인싸이트러닝 AI 사무실 설치' -ForegroundColor Cyan
Write-Host '   기존 n8n 워크플로·Claude 에이전트는 바꾸지 않습니다' -ForegroundColor Cyan
Write-Host '==============================================' -ForegroundColor Cyan

Write-Step '1/8 설치 환경 조사(읽기 전용)'
& (Join-Path $PSScriptRoot 'survey.ps1') -Quiet

Write-Step '2/8 Node.js 확인'
$nodeOk = $false
if (Test-Cmd 'node') {
  $v = (& node --version).Trim()
  $major = [int](($v -replace '^v', '') -split '\.')[0]
  if ($major -ge 20) { Write-Ok "Node.js $v"; $nodeOk = $true } else { Write-Warn2 "Node.js $v — 20 이상이 필요합니다" }
}
if (-not $nodeOk) {
  if ((Test-Cmd 'winget') -and (Ask-YesNo 'Node.js LTS 를 설치할까요? (무료, winget 사용)' $true)) {
    & winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
    Write-Warn2 '설치가 끝나면 이 창을 닫고 SETUP-AI-OFFICE.bat 을 다시 실행하세요(새 창에서 node 가 보입니다).'
    exit 0
  }
  Write-Bad 'Node.js 가 없으면 AI 사무실을 켤 수 없습니다. https://nodejs.org 에서 LTS 를 설치한 뒤 다시 실행하세요.'
  exit 1
}

Write-Step '3/8 기존 시스템 백업'
if (Ask-YesNo "slide-svg·사용자 Claude 설정·n8n 워크플로를 백업할까요? (권장)" $true) { & (Join-Path $PSScriptRoot 'backup.ps1') -SlideSvg $SlideSvg }
else { Write-Warn2 '백업을 건너뛰었습니다' }

Write-Step '4/8 에이전트 작업용 복사본(원본은 그대로 두고 복사본에서 일합니다)'
New-Item -ItemType Directory -Force -Path $agents | Out-Null
if (Test-Path $slideCopy) { Write-Ok "PPT 에이전트 복사본이 이미 있습니다: $slideCopy (그대로 사용)" }
elseif (-not (Test-Path $SlideSvg)) { Write-Bad "원본 $SlideSvg 를 찾지 못했습니다. 경로를 확인한 뒤 SETUP-AI-OFFICE.bat 을 다시 실행하세요." }
elseif (Ask-YesNo "PPT 디자인 에이전트($SlideSvg)를 $slideCopy 로 복사할까요? (가상환경 포함, 몇 분)" $true) {
  & robocopy $SlideSvg $slideCopy /E /XD .git __pycache__ /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -lt 8) { Write-Ok "복사 완료: $slideCopy" } else { Write-Bad "복사 실패(robocopy $LASTEXITCODE)" }
}
$py = Join-Path $slideCopy '.venv\Scripts\python.exe'
if (Test-Path $py) {
  $chk = & $py -c "import pptx; print('ok')" 2>&1 | Out-String
  if ($chk -match 'ok') { Write-Ok '복사본 Python 가상환경 동작 확인' } else { Write-Warn2 "복사본 가상환경 확인 실패: $($chk.Trim())" }
} elseif (Test-Path $slideCopy) { Write-Warn2 '복사본에 .venv 가 없습니다 — 원본 slide-svg 의 가상환경을 먼저 만들어야 합니다' }
if ((Test-Path $slideCopy) -and -not (Test-Path (Join-Path $slideCopy 'automation\cafe_inquiry\.env'))) {
  Write-Warn2 '교육문의 자동화 설정(automation\cafe_inquiry\.env)이 없습니다 — "인사쟁이 작업대기 처리"는 이 파일이 있어야 동작합니다'
}

if (Test-Path (Join-Path $cardCopy '.claude\skills\cardnews\SKILL.md')) { Write-Ok "카드뉴스 에이전트 복사본이 이미 있습니다: $cardCopy" }
elseif (Test-Path $cardCopy) { Write-Warn2 "$cardCopy 폴더가 있지만 카드뉴스 스킬이 없습니다 — 그대로 둡니다(직접 확인 필요)" }
elseif (-not (Test-Cmd 'git')) { Write-Warn2 'Git 이 없어 카드뉴스 에이전트를 받지 못했습니다(winget install Git.Git 후 다시 실행)' }
elseif (Ask-YesNo "카드뉴스 에이전트(GitHub DDUBI-HI/insight1)를 $cardCopy 로 받을까요?" $true) {
  & git clone https://github.com/DDUBI-HI/insight1.git $cardCopy
  if ($LASTEXITCODE -eq 0) { Write-Ok "받기 완료: $cardCopy" } else { Write-Bad '받기 실패 — 인터넷 연결을 확인하세요' }
}

Write-Step '5/8 설정 파일(config.json)'
if (Test-Path $Script:ConfigFile) { Write-Ok '이미 있습니다 — 그대로 둡니다' }
else {
  $raw = [System.IO.File]::ReadAllText((Join-Path $Script:AppRoot 'config.example.json'), $Script:Utf8)
  $cl = Get-Command claude -ErrorAction SilentlyContinue
  if ($cl) {
    $esc = $cl.Source -replace '\\', '\\'
    $raw = $raw -replace '"claudePath": "claude"', ('"claudePath": "' + $esc + '"')
  }
  Write-TextFile $Script:ConfigFile $raw
  Write-Ok "만들었습니다: $($Script:ConfigFile)"
}

Write-Step '6/8 AI 사무실 켜기'
& (Join-Path $PSScriptRoot 'start.ps1') -NoBrowser

Write-Step '7/8 바로가기·자동 시작'
$desk = [Environment]::GetFolderPath('Desktop')
if (Ask-YesNo '바탕 화면에 "AI 사무실 열기" 바로가기를 만들까요?' $true) {
  New-Shortcut (Join-Path $desk 'AI 사무실 열기.lnk') (Join-Path $Script:AppRoot 'START-AI-OFFICE.bat') '' $Script:AppRoot 'AI 사무실 켜고 열기'
  Write-Ok '바탕 화면 바로가기를 만들었습니다'
}
if (Ask-YesNo 'PC 를 켜면 AI 사무실이 저절로 켜지게 할까요? (나중에 끌 수 있음)' $true) { & (Join-Path $PSScriptRoot 'autostart.ps1') }

Write-Step '8/8 연결 시험'
& (Join-Path $PSScriptRoot 'test-connection.ps1')

Write-Host ''
Write-Host '설치가 끝났습니다. 남은 일(사람이 해야 하는 것):' -ForegroundColor Cyan
Write-Host '  1. n8n 화면에서 ai-office\n8n 폴더의 워크플로 5개를 Import (기존 워크플로는 그대로)'
Write-Host '  2. COPY-TOKEN.bat 으로 토큰을 복사해 n8n 자격증명 "AI-OFFICE 브리지 토큰"에 붙여 넣기'
Write-Host '  3. 사용 설명서: ai-office\docs\사용설명서.md'
Start-Process "http://127.0.0.1:$(Get-Port)/"
Start-Process "http://127.0.0.1:$(Get-Port)/control.html"
