<#
  Windows PC(GPU 없음, Python 3.12, ffmpeg) 로컬 환경 세팅.
  사용:  PowerShell 에서  .\scripts\setup_windows.ps1            # 기본 설치
         .\scripts\setup_windows.ps1 -SkipDemucs               # Demucs(torch) 설치 생략
         .\scripts\setup_windows.ps1 -RunTests                 # 설치 후 테스트 실행

  TODO(미검증): 이 스크립트는 Linux 클라우드에서 작성되어 Windows 에서 실행해 보지 못했습니다.
  오류가 나면 메시지를 확인하고 해당 줄만 수동으로 실행해 보세요.
  (실행 정책 오류 시:  Set-ExecutionPolicy -Scope Process Bypass)
#>
param(
    [switch]$SkipDemucs,
    [switch]$SkipMediaPipe,
    [switch]$RunTests,
    [string]$VenvDir = ".venv"
)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Fail($m) { Write-Host "오류: $m" -ForegroundColor Red; exit 1 }

Step "1/6 필수 도구 확인 (Python 3.12, ffmpeg)"
$pyExe = $null; $pyArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $pyExe = "py"; $pyArgs = @("-3.12") }
}
if (-not $pyExe -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $v = & python --version 2>&1
    if ($v -match "3\.1[0-3]") { $pyExe = "python" }
}
if (-not $pyExe) { Fail "Python 3.12 를 찾지 못했습니다. https://www.python.org/downloads/ 에서 설치하세요 (Add to PATH 체크)." }
foreach ($t in @("ffmpeg", "ffprobe")) {
    if (-not (Get-Command $t -ErrorAction SilentlyContinue)) {
        Fail "$t 를 찾지 못했습니다. 설치:  winget install Gyan.FFmpeg  (설치 후 새 PowerShell 창을 여세요)"
    }
}
& ffmpeg -version | Select-Object -First 1

Step "2/6 가상환경 만들기 ($VenvDir)"
if (-not (Test-Path $VenvDir)) { & $pyExe @pyArgs -m venv $VenvDir }
$vpy = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $vpy)) { Fail "가상환경 생성에 실패했습니다." }
& $vpy -m pip install --upgrade pip

Step "3/6 파이프라인 설치 (numpy, scipy, opencv, pyyaml, pytest)"
& $vpy -m pip install -e ".[dev]"

if (-not $SkipMediaPipe) {
    Step "4/6 mediapipe 설치 (얼굴 랜드마크: 각도/눈 감김/입 위치). 실패해도 OpenCV Haar 로 대체 동작합니다."
    & $vpy -m pip install mediapipe
    if ($LASTEXITCODE -ne 0) { Write-Host "mediapipe 설치 실패 -> scan 단계는 Haar(정면 얼굴만, 각도/눈 감김 판정 없음)로 동작합니다." -ForegroundColor Yellow }
} else { Step "4/6 mediapipe 건너뜀" }

if (-not $SkipDemucs) {
    Step "5/6 Demucs 설치 (CPU 전용 torch, 용량 큼). 보컬 분리는 CPU 로 수 분~수십 분 걸릴 수 있습니다."
    & $vpy -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    # torchaudio 최신 버전에서 Demucs 저장 오류가 나면 torch/torchaudio 를 2.8 이하로 맞추세요 (TODO: 버전 확인 필요)
    & $vpy -m pip install demucs
} else { Step "5/6 Demucs 건너뜀 (separate 단계에서 --backend passthrough 로 시험만 가능)" }

Step "6/6 동작 확인"
& $vpy -m lipsync models
if ($RunTests) { & $vpy -m pytest -q }

Write-Host @"

설치 완료. 사용 예 (PowerShell):
  $VenvDir\Scripts\Activate.ps1
  python -m lipsync prepare "D:\영상\컷 1.mp4" "D:\음원\노래.wav" --name 노래1
  python -m lipsync separate 노래1 --device cpu
  python -m lipsync analyze 노래1
  python -m lipsync scan 노래1            # cuts_report.csv 확인 (경고 컷 / 워터마크 경고)
  python -m lipsync segments 노래1
  python -m lipsync pack 노래1 --kind upload     # -> work\노래1\gpu_upload.zip 을 외부 GPU 로
  (GPU 에서 lipsync 후) python -m lipsync unpack 노래1 gpu_result.zip
  python -m lipsync review 노래1          # 후보 비교/선택
  python -m lipsync finalize 노래1

CodeFormer / Real-ESRGAN / RIFE 는 별도 설치가 필요합니다 (README 참고). GPU 없이도 CPU 로 느리게 동작할 수 있습니다.
"@
