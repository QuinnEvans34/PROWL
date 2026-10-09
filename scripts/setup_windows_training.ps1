# Run after installing Python 3.12 from python.org. Uses a separate Windows environment.
[CmdletBinding()]
param([string]$Python312 = '')
$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoPath
$venvPath = Join-Path $repoPath '.venv-prowl-windows'
$trainingPython = Join-Path $venvPath 'Scripts/python.exe'
if (-not $Python312 -and (Test-Path -LiteralPath $trainingPython)) {
    $Python312 = $trainingPython
}
if (-not $Python312) {
    $Python312 = & py -3.12 -c 'import sys; print(sys.executable)'
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12 first: https://www.python.org/downloads/release/python-31210/' }
}
& $Python312 -c 'import sys; assert sys.version_info[:2] == (3, 12), "Python 3.12 required"'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 verification failed' }
if (-not (Test-Path -LiteralPath $venvPath)) {
    & $Python312 -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed' }
}
& $trainingPython -c 'import sys; assert sys.version_info[:2] == (3, 12) and sys.prefix != sys.base_prefix'
if ($LASTEXITCODE -ne 0) { throw 'Existing Windows environment is incompatible; preserve it and choose a new directory' }
& $trainingPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip setup failed' }
& $trainingPython -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
if ($LASTEXITCODE -ne 0) { throw 'CUDA PyTorch installation failed' }
& $trainingPython -m pip install -r requirements/windows-training.in
if ($LASTEXITCODE -ne 0) { throw 'Project dependency installation failed' }
& $trainingPython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency consistency check failed' }
& $trainingPython scripts/diagnostics/check_windows_training.py
if ($LASTEXITCODE -ne 0) { throw 'Environment check failed; read the readiness report' }
Write-Host 'Environment available. Dataset provisioning and full-trainer CUDA/Windows qualification still precede training.'
