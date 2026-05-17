#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

Write-Host ">> Claude Code Status Line - Windows Uninstall"

$DestDir  = Join-Path $env:USERPROFILE '.claude'
$DestPs1  = Join-Path $DestDir 'statusline.ps1'
$DestCmd  = Join-Path $DestDir 'statusline.cmd'
$Settings = Join-Path $DestDir 'settings.json'

foreach ($f in @($DestPs1, $DestCmd)) {
    if (Test-Path $f) {
        Remove-Item $f -Force
        Write-Host "   removed: $f"
    } else {
        Write-Host "   skipped: $f (not found)"
    }
}

if (Test-Path $Settings) {
    Copy-Item $Settings "$Settings.bak.$(Get-Date -UFormat %s)" -Force
    $json = Get-Content $Settings -Raw | ConvertFrom-Json
    if ($null -ne $json -and $json.PSObject.Properties.Name -contains 'statusLine') {
        $json.PSObject.Properties.Remove('statusLine')
    }
    ($json | ConvertTo-Json -Depth 20) | Set-Content -Path $Settings -Encoding UTF8
    Write-Host "   updated: $Settings (statusLine removed)"
} else {
    Write-Host "   skipped: $Settings (not found)"
}

Write-Host ">> Done. Restart Claude Code."
