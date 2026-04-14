# Fix Crash Dump Configuration
# - Increase C: PageFile to 32GB (for Kernel dump)
# - Change CrashDumpEnabled: Small (3) -> Kernel (2)
# - Disable AutoReboot on BSOD (so you can see the error code)
# - Requires: Run as Administrator

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Fix Crash Dump Configuration" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- Check Admin ---
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] Must run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell, Run as Administrator, then run:" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File $PSCommandPath" -ForegroundColor Yellow
    exit 1
}

# --- 1. Fix PageFile on C: ---
Write-Host "[1/3] Configuring PageFile on C: ..." -ForegroundColor Yellow

$existing = Get-CimInstance -ClassName Win32_PageFileSetting | Where-Object { $_.Name -eq "C:\pagefile.sys" }
if ($existing) {
    Remove-CimInstance -InputObject $existing
    Write-Host "  Removed existing C: pagefile setting" -ForegroundColor Gray
}

$pfKey = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
Set-ItemProperty -Path $pfKey -Name "PagingFiles" -Value @(
    "C:\pagefile.sys 32768 32768",
    "E:\pagefile.sys 8096 8096"
)
Write-Host "  C: pagefile = 32768 MB (32 GB fixed)" -ForegroundColor Green
Write-Host "  E: pagefile = 8096 MB (8 GB, unchanged)" -ForegroundColor Green

# --- 2. Change CrashDumpEnabled to Kernel dump ---
Write-Host ""
Write-Host "[2/3] Configuring Crash Dump ..." -ForegroundColor Yellow

$crashKey = "HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl"

$currentDump = (Get-ItemProperty -Path $crashKey -Name "CrashDumpEnabled").CrashDumpEnabled
Set-ItemProperty -Path $crashKey -Name "CrashDumpEnabled" -Value 2
Write-Host "  CrashDumpEnabled: $currentDump -> 2 (Kernel memory dump)" -ForegroundColor Green

Write-Host "  DumpFile: C:\WINDOWS\MEMORY.DMP" -ForegroundColor Gray

Set-ItemProperty -Path $crashKey -Name "Overwrite" -Value 1
Write-Host "  Overwrite old dumps: Yes" -ForegroundColor Gray

# --- 3. Disable AutoReboot on BSOD ---
Write-Host ""
Write-Host "[3/3] Disabling AutoReboot on BSOD ..." -ForegroundColor Yellow

$currentAutoReboot = (Get-ItemProperty -Path $crashKey -Name "AutoReboot").AutoReboot
Set-ItemProperty -Path $crashKey -Name "AutoReboot" -Value 0
Write-Host "  AutoReboot: $currentAutoReboot -> 0 (OFF, you will see BSOD screen)" -ForegroundColor Green

# --- Summary ---
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  DONE! Configuration Summary:" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  C: PageFile     : 32 GB fixed" -ForegroundColor White
Write-Host "  E: PageFile     : 8 GB fixed (unchanged)" -ForegroundColor White
Write-Host "  Crash Dump Type : Kernel memory dump" -ForegroundColor White
Write-Host "  Dump Location   : C:\WINDOWS\MEMORY.DMP" -ForegroundColor White
Write-Host "  AutoReboot      : OFF (see BSOD code)" -ForegroundColor White
Write-Host ""
Write-Host "  REBOOT REQUIRED for changes to take effect." -ForegroundColor Yellow
Write-Host ""

$answer = Read-Host "Reboot now? (y/N)"
if ($answer -eq "y" -or $answer -eq "Y") {
    Write-Host "Rebooting in 5 seconds ..." -ForegroundColor Red
    Start-Sleep 5
    Restart-Computer -Force
} else {
    Write-Host "Okay, reboot manually when ready." -ForegroundColor Gray
}
