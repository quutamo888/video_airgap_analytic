$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User') + ';' + (Join-Path $env:USERPROFILE ".dotnet\tools")

# 1. Check wix tool
$wix = Get-Command wix -ErrorAction SilentlyContinue
if (-not $wix) {
    Write-Host "[INFO] WiX tool not found in PATH. Checking dotnet tool..."
    $dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
    if ($dotnet) {
        Write-Host "[INFO] Installing wix as global dotnet tool..."
        dotnet tool install --global wix --version 5.0.2
        $env:Path = (Join-Path $env:USERPROFILE ".dotnet\tools") + ';' + $env:Path
        $wix = Get-Command wix -ErrorAction SilentlyContinue
    }
}

if (-not $wix) {
    Write-Host "[INFO] Installing WiX Toolset via winget..."
    winget install --id WiX.Toolset -e --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
    $wix = Get-Command wix -ErrorAction SilentlyContinue
}

# 2. Ensure dist\VideoDeadAirCutter exists
$distFolder = Join-Path $repoRoot "dist\VideoDeadAirCutter"
if (-not (Test-Path (Join-Path $distFolder "VideoDeadAirCutter.exe"))) {
    Write-Host "[INFO] Building PyInstaller distribution first..."
    uv run python build_exe.py
}

# 3. Add WixToolset.UI.wixext matching WiX version 5
Write-Host "[INFO] Ensuring WixToolset.UI.wixext (v5) is installed..."
wix extension add -g WixToolset.UI.wixext/5.0.2

# 4. Compile MSI
$msiOutput = Join-Path $repoRoot "dist\VideoDeadAirCutter_Setup.msi"
$wxsFile = Join-Path $repoRoot "installer\Package.wxs"

Write-Host "[INFO] Building MSI installer using WiX..."
wix build -ext WixToolset.UI.wixext/5.0.2 -o $msiOutput $wxsFile

if (Test-Path $msiOutput) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "[SUCCESS] MSI Installer built successfully!" -ForegroundColor Green
    Write-Host "Output: $msiOutput" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to generate MSI installer." -ForegroundColor Red
    exit 1
}
