param([switch]$Desktop, [string]$PythonPath)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $PythonPath) {
    $PythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $PythonPath)) { $PythonPath = (Get-Command python).Source }
}
$PythonPath = (Resolve-Path -LiteralPath $PythonPath).Path
$outputDirectory = Join-Path $projectRoot 'dist/desktop'
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
$launcherSource = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'PrototypeLauncher.cs') -Raw
$launcherSource = $launcherSource.Replace('__APPLICATION_ROOT__', $projectRoot.Replace('"', '""')).Replace('__PYTHON_PATH__', $PythonPath.Replace('"', '""'))
$sourcePath = Join-Path $outputDirectory 'PrototypeLauncher.generated.cs'
[IO.File]::WriteAllText($sourcePath, $launcherSource, [Text.UTF8Encoding]::new($true))
$compilerPath = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
$outputPath = Join-Path $outputDirectory 'AX나침반.exe'
& $compilerPath /nologo /target:winexe /reference:System.Windows.Forms.dll "/out:$outputPath" $sourcePath
if ($LASTEXITCODE -ne 0) { throw 'Launcher compilation failed.' }
Write-Output "Built: $outputPath"
if ($Desktop) {
    $desktopDirectory = [Environment]::GetFolderPath('Desktop')
    $destination = Join-Path $desktopDirectory 'AX나침반.exe'
    if (Test-Path -LiteralPath $destination) {
        $existingHash = (Get-FileHash -LiteralPath $destination).Hash
        $newHash = (Get-FileHash -LiteralPath $outputPath).Hash
        if ($existingHash -ne $newHash) { throw 'A different AX나침반.exe already exists. Preserve it and choose a new name.' }
    } else { Copy-Item -LiteralPath $outputPath -Destination $destination }
    Write-Output "Installed: $destination"
}
