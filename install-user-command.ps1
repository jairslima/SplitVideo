param(
    [string]$CommandName = "splitvideo"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$userBin = Join-Path $env:USERPROFILE "bin"
New-Item -ItemType Directory -Force -Path $userBin | Out-Null

$exePath = Join-Path $root "dist\SplitVideo\SplitVideo.exe"
$scriptPath = Join-Path $root "splitvideo.py"
$runnerPath = Join-Path $userBin "$CommandName.cmd"

if (Test-Path -LiteralPath $exePath) {
    $targetLine = "`"$exePath`" %*"
}
else {
    $pythonExe = (Get-Command python -ErrorAction Stop).Source
    $targetLine = "`"$pythonExe`" `"$scriptPath`" %*"
}

@"
@echo off
$targetLine
"@ | Set-Content -LiteralPath $runnerPath -Encoding ASCII

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$segments = @()
if ($userPath) {
    $segments = $userPath.Split(';', [System.StringSplitOptions]::RemoveEmptyEntries)
}
if ($segments -notcontains $userBin) {
    $newPath = if ($userPath) { "$userPath;$userBin" } else { $userBin }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
}

Write-Host "Comando instalado em: $runnerPath"
Write-Host "Abra um novo terminal e use: $CommandName"
