# ============================================================
# Cleanup AMD Radeon Software (leftover from old GPU)
# KEEP: AMD Chipset drivers (needed for Ryzen 9 3900X)
# REMOVE: AMD Software, DVR, Settings, RadeonSettings
# ============================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Remove AMD Radeon Software" -ForegroundColor Cyan
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

# --- 1. Kill AMD processes ---
Write-Host "[1/4] Killing AMD processes ..." -ForegroundColor Yellow
$procs = Get-Process | Where-Object { $_.Name -match "Radeon|AMD.*Settings|AMD.*CNext|RadeonSettings" }
if ($procs) {
    $procs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  Killed: $($procs.Name -join ', ')" -ForegroundColor Green
} else {
    Write-Host "  No AMD processes running" -ForegroundColor Gray
}

# --- 2. Run AMD express uninstall ---
Write-Host ""
Write-Host "[2/4] Running AMD Software uninstaller ..." -ForegroundColor Yellow
$radeonInstaller = "C:\Program Files\AMD\CIM\Bin64\RadeonInstaller.exe"
if (Test-Path $radeonInstaller) {
    Write-Host "  Running RadeonInstaller /EXPRESS_UNINSTALL (this takes a few minutes) ..." -ForegroundColor Gray
    Start-Process -FilePath $radeonInstaller -ArgumentList "/EXPRESS_UNINSTALL","/IGNORE_UPGRADE","/ON_REBOOT_MESSAGE:NO" -Wait -ErrorAction SilentlyContinue
    Write-Host "  Done" -ForegroundColor Green
} else {
    Write-Host "  RadeonInstaller not found, skipping" -ForegroundColor Gray
}

# --- 3. Remove leftover AMD Radeon folders ---
Write-Host ""
Write-Host "[3/4] Cleaning leftover AMD Radeon folders ..." -ForegroundColor Yellow
$foldersToRemove = @(
    "C:\Program Files\AMD\CNext"
    "C:\Program Files\AMD\CIM"
    "C:\Program Files\AMD\DVR"
    "C:\Program Files (x86)\AMD\RadeonSettings"
    "C:\Users\Admin\AppData\Local\AMD\CNext"
    "C:\Users\Admin\AppData\Roaming\AMD\CNext"
    "C:\Users\Admin\AppData\Local\AMD\DVR"
)

foreach ($folder in $foldersToRemove) {
    if (Test-Path $folder) {
        Remove-Item -Path $folder -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Removed: $folder" -ForegroundColor Green
    }
}

# Remove RadeonSettings.exe specifically if still there
$rsExe = "C:\Program Files\AMD\CNext\CNext\RadeonSettings.exe"
if (Test-Path $rsExe) {
    Remove-Item $rsExe -Force -ErrorAction SilentlyContinue
    Write-Host "  Removed: RadeonSettings.exe" -ForegroundColor Green
}

# Clean AMD temp folders
$amdTemp = "C:\AMD"
if (Test-Path $amdTemp) {
    Remove-Item $amdTemp -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  Removed: C:\AMD (temp installer files)" -ForegroundColor Green
}

# --- 4. Remove AMD DVR64 and AMD Settings via MSI ---
Write-Host ""
Write-Host "[4/4] Removing AMD DVR and Settings via MSI ..." -ForegroundColor Yellow

$msiToRemove = @(
    # AMD DVR64 entries
    "{90180409-6000-11D3-8CFE-0150048383C9}",  # AMD DVR64
    # AMD Problem Report Wizard
    "{DDF320BF-158F-0D83-5F26-8B2B7E604E3A}"
)

foreach ($guid in $msiToRemove) {
    $result = Start-Process msiexec.exe -ArgumentList "/x","$guid","/qn","REBOOT=ReallySuppress" -Wait -PassThru -ErrorAction SilentlyContinue
    if ($result -and $result.ExitCode -eq 0) {
        Write-Host "  Removed MSI: $guid" -ForegroundColor Green
    }
}

# --- Verify ---
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  DONE! Verification:" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green

Write-Host ""
Write-Host "Remaining AMD programs:" -ForegroundColor Cyan
$remaining = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*","HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -match "AMD|Radeon" } | Select-Object DisplayName, DisplayVersion

if ($remaining) {
    $remaining | Format-Table -AutoSize -Wrap
    Write-Host ""
    Write-Host "  (Chipset/PCI/PSP/SMBus/GPIO drivers are KEPT - needed for AMD Ryzen CPU)" -ForegroundColor Yellow
} else {
    Write-Host "  None" -ForegroundColor Gray
}

Write-Host ""
Write-Host "RadeonSettings.exe exists:" -ForegroundColor Cyan
if (Test-Path "C:\Program Files\AMD\CNext\CNext\RadeonSettings.exe") {
    Write-Host "  YES - still there, may need manual removal after reboot" -ForegroundColor Red
} else {
    Write-Host "  NO - cleaned!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Reboot recommended to complete cleanup." -ForegroundColor Yellow
Write-Host ""
$answer = Read-Host "Reboot now? (y/N)"
if ($answer -eq "y" -or $answer -eq "Y") {
    Write-Host "Rebooting in 5 seconds ..." -ForegroundColor Red
    Start-Sleep 5
    Restart-Computer -Force
} else {
    Write-Host "Okay, reboot manually when ready." -ForegroundColor Gray
}
