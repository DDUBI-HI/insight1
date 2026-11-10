# 기존 시스템 백업 (원본은 읽기만 합니다)
#  - C:\JY\slide-svg (PPT 디자인 에이전트 + 교육문의 자동화) — .venv·.git 제외
#  - 사용자 Claude 설정 중 skills·agents·commands·settings.json·CLAUDE.md (로그인 정보 파일은 복사하지 않음)
#  - n8n 워크플로 전체(내보내기 — 자격증명은 내보내지 않음)
param([string]$SlideSvg = 'C:\JY\slide-svg')
. (Join-Path $PSScriptRoot 'common.ps1')
$ErrorActionPreference = 'Continue'

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$dest = Join-Path (Join-Path (Get-DataDir) 'backups') $stamp
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Write-Step "백업 폴더: $dest"

if (Test-Path $SlideSvg) {
  Write-Host '  slide-svg 복사 중(몇 분 걸릴 수 있습니다)…'
  & robocopy $SlideSvg (Join-Path $dest 'slide-svg') /E /XD .venv .git node_modules __pycache__ /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -lt 8) { Write-Ok 'slide-svg 백업 완료' } else { Write-Bad "slide-svg 백업 실패(robocopy $LASTEXITCODE)" }
} else { Write-Warn2 "$SlideSvg 가 없어 건너뜀" }

$ud = Join-Path $env:USERPROFILE '.claude'
$cd = Join-Path $dest 'claude-user'
New-Item -ItemType Directory -Force -Path $cd | Out-Null
foreach ($sub in @('skills', 'agents', 'commands')) {
  $p = Join-Path $ud $sub
  if (Test-Path $p) { & robocopy $p (Join-Path $cd $sub) /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null }
}
foreach ($f in @('settings.json', 'CLAUDE.md')) { $p = Join-Path $ud $f; if (Test-Path $p) { Copy-Item $p (Join-Path $cd $f) } }
Write-Ok '사용자 Claude 설정 백업 완료(.credentials.json 등 로그인 정보는 제외)'

$c = Get-N8nContainer
if ($c) {
  $tmp = '/tmp/ai-office-workflows-backup.json'
  & docker exec $c n8n export:workflow --all --pretty --output=$tmp 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) {
    & docker cp "${c}:$tmp" (Join-Path $dest 'n8n-workflows.json') | Out-Null
    & docker exec $c rm -f $tmp 2>$null | Out-Null
    Write-Ok 'n8n 워크플로 내보내기 완료(n8n-workflows.json, 자격증명 제외)'
  } else { Write-Bad 'n8n 워크플로 내보내기 실패 — n8n 화면에서 직접 내려받아 두세요' }
} else { Write-Warn2 'n8n 컨테이너를 찾지 못해 n8n 백업을 건너뜀' }

$readme = @"
AI 사무실 설치 전 백업 ($stamp)
- slide-svg\       : $SlideSvg 사본(.venv·.git 제외)
- claude-user\     : $ud 의 skills·agents·commands·settings.json·CLAUDE.md
- n8n-workflows.json : n8n 워크플로 전체(자격증명 제외). 되돌릴 때는 n8n 화면 → Import from File
이 폴더의 파일은 AI 사무실이 고치거나 지우지 않습니다.
"@
Write-TextFile (Join-Path $dest '백업_안내.txt') $readme
Write-Ok "백업 끝: $dest"
