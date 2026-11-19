# 토큰을 클립보드에 복사합니다(화면에는 보이지 않습니다). n8n 자격증명에 붙여 넣을 때 씁니다.
#   COPY-TOKEN.bat        → n8n 이 AI 사무실을 부를 때 쓰는 토큰 (Header Auth: X-Office-Token)
#   COPY-TOKEN.bat n8n    → AI 사무실이 n8n 알림 웹훅을 부를 때 쓰는 비밀값 (Header Auth: X-Office-Secret)
param([string]$Which = 'bridge')
. (Join-Path $PSScriptRoot 'common.ps1')
$name = 'bridge-token.txt'; if ($Which -eq 'n8n') { $name = 'n8n-webhook-secret.txt' }
$file = Join-Path (Get-DataDir) "secret\$name"
if (-not (Test-Path $file)) { Write-Bad '토큰 파일이 없습니다. AI 사무실을 한 번 켜면 만들어집니다(START-AI-OFFICE.bat).'; exit 1 }
([System.IO.File]::ReadAllText($file)).Trim() | Set-Clipboard
Write-Ok "클립보드에 복사했습니다($name). n8n 자격증명 Value 칸에 Ctrl+V 로 붙여 넣으세요."
