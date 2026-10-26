param([switch]$ValidateHttp)

$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $axPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $axPython)) {
        throw 'The project .venv is missing. Follow data/v2_5/research/README.md.'
    }
    $env:PYTHONPATH = 'src;.'
    $env:PYTHONIOENCODING = 'utf-8'
    & $axPython -m scripts.run_v25_dev_baselines
    if ($LASTEXITCODE -ne 0) { throw 'Dev baseline execution failed.' }
    if ($ValidateHttp) {
        & $axPython -m scripts.validate_v25_research --base-url http://127.0.0.1:8766
    } else {
        & $axPython -m scripts.validate_v25_research
    }
    if ($LASTEXITCODE -ne 0) { throw 'Research input validation failed.' }
} finally {
    Pop-Location
}
