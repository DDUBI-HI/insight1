# AI 사무실 PowerShell 공통 도구 (Windows PowerShell 5.1 호환)
$ErrorActionPreference = 'Stop'
$Script:AppRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Script:ConfigFile = Join-Path $Script:AppRoot 'config.json'
$Script:Utf8Bom = New-Object System.Text.UTF8Encoding $true
$Script:Utf8 = New-Object System.Text.UTF8Encoding $false

function Write-Step([string]$msg) { Write-Host ''; Write-Host "▶ $msg" -ForegroundColor Cyan }
function Write-Ok([string]$msg) { Write-Host "  [완료] $msg" -ForegroundColor Green }
function Write-Warn2([string]$msg) { Write-Host "  [주의] $msg" -ForegroundColor Yellow }
function Write-Bad([string]$msg) { Write-Host "  [실패] $msg" -ForegroundColor Red }

function Ask-YesNo([string]$question, [bool]$default = $true) {
  if ($Script:AssumeYes) { return $default }
  $hint = '[Y/n]'; if (-not $default) { $hint = '[y/N]' }
  while ($true) {
    $a = Read-Host "  $question $hint"
    if ([string]::IsNullOrWhiteSpace($a)) { return $default }
    if ($a -match '^(y|yes|ㅛ|예|네)$') { return $true }
    if ($a -match '^(n|no|ㅜ|아니오|아니요)$') { return $false }
  }
}

function Test-Cmd([string]$name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }

function Get-Config {
  $file = $Script:ConfigFile
  if (-not (Test-Path $file)) { $file = Join-Path $Script:AppRoot 'config.example.json' }
  $raw = [System.IO.File]::ReadAllText($file, $Script:Utf8)
  return ($raw | ConvertFrom-Json)
}

function Get-DataDir {
  $c = Get-Config
  if ($env:AI_OFFICE_DATA) { return $env:AI_OFFICE_DATA }
  return [string]$c.dataDir
}

function Get-Port {
  $c = Get-Config
  if ($env:AI_OFFICE_PORT) { return [int]$env:AI_OFFICE_PORT }
  return [int]$c.port
}

function Test-Health([int]$port) {
  try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:$port/api/health" -TimeoutSec 3
    return ($r.ok -eq $true -and $r.app -eq 'ai-office')
  } catch { return $false }
}

function Write-TextFile([string]$path, [string]$text) {
  $dir = Split-Path $path -Parent
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::WriteAllText($path, $text, $Script:Utf8)
}

function Get-N8nContainer {
  if (-not (Test-Cmd 'docker')) { return $null }
  try {
    $lines = & docker ps --format '{{.Names}}|{{.Image}}' 2>$null
    foreach ($l in $lines) {
      $p = $l -split '\|'
      if ($p.Length -ge 2 -and ($p[1] -match 'n8n' -or $p[0] -match 'n8n')) { return $p[0] }
    }
  } catch { }
  return $null
}

function New-Shortcut([string]$lnk, [string]$target, [string]$arguments, [string]$workDir, [string]$desc) {
  $sh = New-Object -ComObject WScript.Shell
  $s = $sh.CreateShortcut($lnk)
  $s.TargetPath = $target
  $s.Arguments = $arguments
  $s.WorkingDirectory = $workDir
  $s.Description = $desc
  $s.Save()
}
