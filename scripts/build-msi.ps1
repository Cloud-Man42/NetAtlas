$ErrorActionPreference = "Stop"

function Assert-LastExitCode {
    param(
        [string]$Step
    )

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE."
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $repoRoot "frontend"
$backendRoot = Join-Path $repoRoot "backend"
$installerRoot = Join-Path $repoRoot "installer"
$buildRoot = Join-Path $repoRoot "build"
$outputRoot = Join-Path $buildRoot "dist"
$installerDataRoot = Join-Path $buildRoot "installer-data"
$venvRoot = Join-Path $backendRoot ".venv"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"
$logoSource = Join-Path $frontendRoot "assets\netatlas logo.png"
$logoTargetDir = Join-Path $frontendRoot "dist\assets"
$emptyDatabase = Join-Path $installerDataRoot "netatlas.db"
$msiPath = Join-Path $outputRoot "NetAtlas-0.2.0.msi"

New-Item -ItemType Directory -Force -Path $buildRoot, $outputRoot, $installerDataRoot | Out-Null

if (-not (Test-Path $venvPython)) {
    py -3 -m venv $venvRoot
    Assert-LastExitCode "Creating Python virtual environment"
}

Push-Location $backendRoot
& $venvPython -m pip install --upgrade pip
Assert-LastExitCode "Upgrading pip"
& $venvPython -m pip install -e ".[dev]" pyinstaller
Assert-LastExitCode "Installing backend dependencies"
Pop-Location

Push-Location $frontendRoot
npm install
Assert-LastExitCode "Installing frontend dependencies"
npm run build
Assert-LastExitCode "Building frontend"
Pop-Location

if (Test-Path $logoSource) {
    New-Item -ItemType Directory -Force -Path $logoTargetDir | Out-Null
    Copy-Item $logoSource (Join-Path $logoTargetDir "netatlas logo.png") -Force
}
else {
    Write-Warning "frontend\assets\netatlas logo.png was not found. NetAtlas will use the built-in fallback mark until the file is added."
}

if (Test-Path (Join-Path $backendRoot "dist\NetAtlas")) {
    Remove-Item -Recurse -Force (Join-Path $backendRoot "dist\NetAtlas")
}

if (Test-Path (Join-Path $backendRoot "build\NetAtlas")) {
    Remove-Item -Recurse -Force (Join-Path $backendRoot "build\NetAtlas")
}

Push-Location $backendRoot
& $venvPython -m PyInstaller "NetAtlas.spec" --noconfirm
Assert-LastExitCode "Building NetAtlas executable"
Pop-Location

$packagedFrontendRoot = Join-Path $backendRoot "dist\NetAtlas\frontend"
if (Test-Path $packagedFrontendRoot) {
    Remove-Item -Recurse -Force $packagedFrontendRoot
}
Copy-Item -Recurse -Force (Join-Path $frontendRoot "dist") $packagedFrontendRoot

if (Test-Path $emptyDatabase) {
    Remove-Item -Force $emptyDatabase
}
New-Item -ItemType File -Path $emptyDatabase | Out-Null

if (Get-Command wix -ErrorAction SilentlyContinue) {
    dotnet tool update --global wix | Out-Null
    Assert-LastExitCode "Updating WiX CLI"
}
else {
    dotnet tool install --global wix | Out-Null
    Assert-LastExitCode "Installing WiX CLI"
}

$wixCli = (Get-Command wix -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
if (-not $wixCli) {
    $fallbackWix = Join-Path $env:USERPROFILE ".dotnet\tools\wix.exe"
    if (Test-Path $fallbackWix) {
        $wixCli = $fallbackWix
    }
    else {
        throw "WiX CLI was installed but could not be resolved on PATH."
    }
}

& $wixCli extension add WixToolset.UI.wixext | Out-Null
Assert-LastExitCode "Adding WiX UI extension"
& $wixCli extension add WixToolset.Util.wixext | Out-Null
Assert-LastExitCode "Adding WiX Util extension"

if (Test-Path $msiPath) {
    Remove-Item -Force $msiPath
}

& $wixCli build (Join-Path $installerRoot "NetAtlas.wxs") -ext WixToolset.UI.wixext -ext WixToolset.Util.wixext -bindpath "app=$(Join-Path $backendRoot 'dist\NetAtlas')" -bindpath "db=$installerDataRoot" -bindpath "installer=$installerRoot" -o $msiPath
Assert-LastExitCode "Building MSI"

Write-Host ""
Write-Host "MSI created at: $msiPath"
