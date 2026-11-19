# Claude 자동화용 장기 토큰 설정 — AI 사무실이 로그인 만료로 멈추지 않게 한다(Pro 구독으로 사용, 추가 비용 없음)
#  1) 이 창에서 claude setup-token 이 실행되면 브라우저에서 로그인·허락
#  2) 화면에 나온 토큰(sk-ant-… 로 시작하는 긴 글자)을 복사해 아래 질문에 붙여 넣기(화면에 보이지 않음)
#  토큰은 C:\AI-OFFICE\office-data\secret\claude-oauth-token.txt 에만 저장된다. 지우면 일반 로그인으로 돌아간다.
. (Join-Path $PSScriptRoot 'common.ps1')
$ErrorActionPreference = 'Continue'
if (-not (Test-Cmd 'claude')) { Write-Bad 'claude 를 찾지 못했습니다'; exit 1 }
Write-Step '1/2 claude setup-token 실행 — 브라우저에서 로그인·허락한 뒤, 이 창에 나온 토큰을 복사하세요'
& claude setup-token
Write-Step '2/2 토큰 붙여 넣기 (마우스 오른쪽 클릭 또는 Ctrl+V 후 Enter — 화면에는 보이지 않습니다)'
$sec = Read-Host '토큰' -AsSecureString
$b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
try { $t = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b).Trim() } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
if ($t -notmatch '^[A-Za-z0-9._\-]{20,}$') { Write-Bad '토큰 모양이 아닙니다. 다시 실행해 주세요.'; exit 1 }
$file = Join-Path (Get-DataDir) 'secret\claude-oauth-token.txt'
Write-TextFile $file ($t + "`n")
Write-Ok "저장했습니다(내용은 표시하지 않음): $file"
Write-Host '  AI 사무실 다음 작업부터 이 토큰을 씁니다. 다시 켤 필요는 없습니다.'
