# 데모 모드 — 진짜 Claude 를 쓰지 않고(사용량 0) 화면과 업무 흐름만 시험합니다. 이 창을 닫으면 꺼집니다.
. (Join-Path $PSScriptRoot 'common.ps1')
if (-not (Test-Cmd 'node')) { Write-Bad 'Node.js 가 없습니다. SETUP-AI-OFFICE.bat 을 먼저 실행하세요.'; exit 1 }
$env:AI_OFFICE_DATA = 'C:\AI-OFFICE\office-data-demo'
Write-Step '데모 모드로 켭니다 (http://127.0.0.1:8766/) — 데이터는 C:\AI-OFFICE\office-data-demo 에 따로 쌓입니다'
Start-Job -ScriptBlock { Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:8766/'; Start-Process 'http://127.0.0.1:8766/control.html' } | Out-Null
& node (Join-Path $Script:AppRoot 'bridge\server.mjs') --demo --port 8766
