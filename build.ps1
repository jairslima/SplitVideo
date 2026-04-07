param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if ($Clean) {
    Remove-Item -Recurse -Force "$root\build" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$root\dist" -ErrorAction SilentlyContinue
}

pyinstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name SplitVideo `
    --add-data "tools;tools" `
    splitvideo.py
