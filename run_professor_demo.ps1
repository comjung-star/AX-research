param([int]$Port = 8766)
$ErrorActionPreference = 'Stop'
$pythonPath = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    $pythonPath = Join-Path (Split-Path $PSScriptRoot) 'AX-prototype/.venv/Scripts/python.exe'
}
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = 'python' }
& $pythonPath (Join-Path $PSScriptRoot 'professor_demo.py') --port $Port
