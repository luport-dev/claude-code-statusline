#!/usr/bin/env pwsh
$ErrorActionPreference = 'SilentlyContinue'

$raw = [Console]::In.ReadToEnd()
try { $d = $raw | ConvertFrom-Json } catch { Write-Host "?"; exit 0 }

$cwd      = if ($d.cwd) { $d.cwd } else { "" }
$worktree = if ($d.worktree.name) { $d.worktree.name } else { "" }

$branch = ""
if ($cwd -and (Test-Path $cwd)) {
    Push-Location $cwd
    $branch = (git branch --show-current 2>$null)
    Pop-Location
}

$e = [char]27
$reset = "$e[0m"
$dim   = "$e[2m"
$sep   = " $dim|$reset "

function Color-Threshold($v, $warn, $crit) {
    if ($null -eq $v) { $v = 0 }
    if ($v -ge $crit) { return "$e[31m" }
    elseif ($v -ge $warn) { return "$e[33m" }
    else { return "$e[32m" }
}

function Model-Color($m) {
    $ml = "$m".ToLower()
    if ($ml -match "opus")   { return "$e[38;2;255;215;0m" }
    if ($ml -match "sonnet") { return "$e[38;2;100;180;255m" }
    if ($ml -match "haiku")  { return "$e[38;5;255m" }
    return "$e[37m"
}

function Effort-Color($lvl) {
    switch ($lvl) {
        "xhigh"  { return "$e[31m" }
        "high"   { return "$e[38;5;208m" }
        "medium" { return "$e[33m" }
        default  { return "$e[32m" }
    }
}

function Thinking-Color($on) {
    if ($on) { return "$e[38;2;80;220;200m" }
    else     { return "$e[2;37m" }
}

function Lbl($label, $color) { return "$color${label}:$reset" }

$modelName = $d.model.display_name
$mc = Model-Color $modelName
$isHaiku = "$modelName".ToLower() -match "haiku"

$dimGray = "$e[2;37m"

$effort = if ($d.effort.level) { $d.effort.level } else { "low" }
$ec     = Effort-Color $effort
$effortDisplay = if ($isHaiku) { "$dimGray`n/a$reset" } else { "$ec$effort$reset" }
$effortLabel   = if ($isHaiku) { "$dimGray`effort:$reset" } else { (Lbl "effort" $ec) }

$settingsPath = Join-Path $HOME ".claude/settings.json"
$thinkingOn = $false
if (Test-Path $settingsPath) {
    try {
        $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
        $thinkingOn = $settings.alwaysThinkingEnabled -eq $true
    } catch {}
}
$thinkingDisplay = if ($thinkingOn) {
    "$(Thinking-Color $true)thinking:on${reset}"
} else {
    "${dimGray}thinking:off${reset}"
}

$ctx  = if ($null -ne $d.context_window.used_percentage)        { $d.context_window.used_percentage } else { 0 }
$five = if ($null -ne $d.rate_limits.five_hour.used_percentage) { $d.rate_limits.five_hour.used_percentage } else { 0 }
$seven= if ($null -ne $d.rate_limits.seven_day.used_percentage) { $d.rate_limits.seven_day.used_percentage } else { 0 }

$ctxC   = Color-Threshold $ctx  70 90
$fiveC  = Color-Threshold $five 70 90
$sevenC = Color-Threshold $seven 50 80

$line1 = ($mc + $modelName + $reset) + $sep +
         $effortLabel + $effortDisplay + $sep +
         $thinkingDisplay + $sep +
         (Lbl "ctx" $ctxC)   + $ctxC   + $ctx   + "%" + $reset + $sep +
         (Lbl "5h"  $fiveC)  + $fiveC  + $five  + "%" + $reset + $sep +
         (Lbl "7d"  $sevenC) + $sevenC + $seven + "%" + $reset

$dirLbl   = "$e[38;5;130m"
$dirVal   = "$e[38;5;172m"
$cwdShown = if ($cwd) { $cwd } else { "?" }
$brShown  = if ($branch)   { $branch }   else { "-" }
$wtShown  = if ($worktree) { $worktree } else { "-" }

$line2 = "${dirLbl}dir:${reset}${dirVal}${cwdShown}${reset}" + $sep +
         "${dirLbl}branch:${reset}${dirVal}${brShown}${reset}" + $sep +
         "${dirLbl}worktree:${reset}${dirVal}${wtShown}${reset}"

Write-Host "$line1`n$line2"
