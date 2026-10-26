$ErrorActionPreference = 'Stop'
$configured = 0
Write-Host 'AX Stage 1 - secure API key setup'
Write-Host 'Input is masked. Keys are stored in Windows USER environment variables.'
Write-Host 'Do not paste keys into chat, command arguments, files, or screenshots.'
Write-Host 'Press Enter without a value to retain an existing setting or skip.'
foreach ($name in @('OPENAI_API_KEY', 'GEMINI_API_KEY', 'ANTHROPIC_API_KEY')) {
    $secureValue = Read-Host "$name (masked)" -AsSecureString
    if ($secureValue.Length -eq 0) {
        Write-Host "$name unchanged"
        continue
    }
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
    try {
        $plainValue = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer).Trim()
        if ($plainValue -match '\s' -or $plainValue.Length -lt 15) {
            throw "Invalid format for $name. No value was printed. Run setup again."
        }
        [Environment]::SetEnvironmentVariable($name, $plainValue, 'User')
        [Environment]::SetEnvironmentVariable($name, $plainValue, 'Process')
        $configured += 1
        Write-Host "$name configured (value hidden)"
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
        $plainValue = $null
        $secureValue.Dispose()
    }
}
Write-Host "Setup complete: $configured setting(s) updated. No API calls were made."
Read-Host 'Press Enter to close' | Out-Null
