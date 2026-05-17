#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

Write-Host ">> Claude Code Status Line - Windows Setup"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Resolve-Path (Join-Path $ScriptDir '..\..')
$SrcPs1    = Join-Path $RepoRoot 'scripts\win\statusline.ps1'
$SrcCmd    = Join-Path $RepoRoot 'scripts\win\statusline.cmd'
$DestDir   = Join-Path $env:USERPROFILE '.claude'
$DestCmd   = Join-Path $DestDir 'statusline.cmd'
$Settings  = Join-Path $DestDir 'settings.json'

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "'git' is required but not installed. See https://git-scm.com/download/win"
    exit 1
}
foreach ($f in @($SrcPs1, $SrcCmd)) {
    if (-not (Test-Path $f)) { Write-Error "Source file not found: $f"; exit 1 }
}

New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
Copy-Item $SrcPs1 (Join-Path $DestDir 'statusline.ps1') -Force
Copy-Item $SrcCmd $DestCmd -Force
Write-Host "   installed: $DestCmd"

$statusLine = [ordered]@{ type = 'command'; command = $DestCmd }

if (Test-Path $Settings) {
    Copy-Item $Settings "$Settings.bak.$(Get-Date -UFormat %s)" -Force
    $json = Get-Content $Settings -Raw | ConvertFrom-Json
    if ($null -eq $json) { $json = [pscustomobject]@{} }
    if ($json.PSObject.Properties.Name -contains 'statusLine') {
        $json.statusLine = $statusLine
    } else {
        $json | Add-Member -NotePropertyName statusLine -NotePropertyValue $statusLine
    }
} else {
    $json = [pscustomobject]@{ statusLine = $statusLine }
}

($json | ConvertTo-Json -Depth 20) | Set-Content -Path $Settings -Encoding UTF8
Write-Host "   updated:   $Settings"

Write-Host ">> Done. Restart Claude Code to load the status line."
