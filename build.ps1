# Builds dist\Guitar-Chord-Guide.exe (single file, no console window).
# Run from the project folder:  powershell -ExecutionPolicy Bypass -File build.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Run($exe, [string[]]$arguments) {
    & $exe @arguments
    if ($LASTEXITCODE -ne 0) { throw "$exe failed with exit code $LASTEXITCODE" }
}

if (-not (Test-Path .venv\Scripts\python.exe)) {
    Run python @("-m", "venv", ".venv")
}
$py = ".\.venv\Scripts\python.exe"
Run $py @("-m", "pip", "install", "--quiet", "--upgrade", "pip", "pyinstaller")

Run $py @("-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
          "--name", "Guitar-Chord-Guide", "--paths", ".", "Guitar-Chord-Guide.pyw")

$exe = Join-Path $PSScriptRoot "dist\Guitar-Chord-Guide.exe"
if (-not (Test-Path $exe)) { throw "Build finished but $exe was not created" }
Write-Host "Built: $exe ($([math]::Round((Get-Item $exe).Length / 1MB, 1)) MB)"
