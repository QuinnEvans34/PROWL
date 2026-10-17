# PROWL machine inventory for Windows. READ-ONLY: collects hardware/software facts, changes nothing.
# Usage: paste into a PowerShell window, or: powershell -ExecutionPolicy Bypass -File machine_inventory.ps1
# Output: Desktop\prowl-machine-inventory.md (also copied to the clipboard).
$ErrorActionPreference = 'SilentlyContinue'
$out = Join-Path ([Environment]::GetFolderPath('Desktop')) 'prowl-machine-inventory.md'
$L = New-Object System.Collections.Generic.List[string]
function W($s) { [void]$L.Add($s) }
function Section($label, [scriptblock]$sb) {
  W "### $label"; W '```'
  try { $r = (& $sb 2>&1 | Out-String) } catch { $r = "ERROR: $($_.Exception.Message)" }
  if (-not $r -or -not $r.Trim()) { $r = '(none / not found)' }
  W $r.TrimEnd(); W '```'; W ''
}
W "# Machine inventory: $env:COMPUTERNAME"
W "Generated $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz') by scripts/diagnostics/machine_inventory.ps1 (read-only)."
W ''
Section 'Operating system' { Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture | Format-List }
Section 'Computer' { Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model, @{n='RAM_GB';e={[math]::Round($_.TotalPhysicalMemory/1GB,1)}} | Format-List }
Section 'CPU' { Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | Format-List }
Section 'Memory modules' { Get-CimInstance Win32_PhysicalMemory | Select-Object @{n='GB';e={[math]::Round($_.Capacity/1GB)}}, Speed, Manufacturer | Format-Table -AutoSize }
Section 'Graphics adapters' { Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, VideoProcessor | Format-List }
Section 'nvidia-smi summary' { nvidia-smi --query-gpu=name,memory.total,driver_version,power.limit,pcie.link.gen.max --format=csv }
Section 'nvidia-smi full' { nvidia-smi }
Section 'CUDA toolkit (nvcc)' { nvcc --version }
Section 'Volumes' { Get-Volume | Where-Object DriveLetter | Select-Object DriveLetter, FileSystemLabel, FileSystem, @{n='SizeGB';e={[math]::Round($_.Size/1GB)}}, @{n='FreeGB';e={[math]::Round($_.SizeRemaining/1GB)}} | Format-Table -AutoSize }
Section 'Physical disks' { Get-PhysicalDisk | Select-Object FriendlyName, MediaType, BusType, @{n='SizeGB';e={[math]::Round($_.Size/1GB)}} | Format-Table -AutoSize }
Section 'Power plan and battery' { powercfg /getactivescheme; Get-CimInstance Win32_Battery | Select-Object Name, EstimatedChargeRemaining, BatteryStatus | Format-List }
Section 'Sleep/hibernate timeouts (AC)' { powercfg /query SCHEME_CURRENT SUB_SLEEP | Select-String -Pattern 'Power Setting GUID|Current AC Power Setting Index' }
Section 'Network adapters (up)' { Get-NetAdapter | Where-Object Status -eq 'Up' | Select-Object Name, InterfaceDescription, LinkSpeed | Format-Table -AutoSize }
Section 'Long paths enabled' { (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem').LongPathsEnabled }
Section 'git' { git --version }
Section 'Python launcher interpreters (py -0p)' { py -0p }
Section 'python on PATH' { where.exe python }
Section 'conda environments' { conda env list }
Section 'WSL' { wsl --status; wsl -l -v }
$probe = @'
import sys
print("exe:", sys.executable); print("python:", sys.version.split()[0])
try:
    import torch
    print("torch:", torch.__version__, "| built for CUDA:", torch.version.cuda, "| cuda available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        p = torch.cuda.get_device_properties(0)
        print("gpu0:", p.name, "|", round(p.total_memory / 2**30, 1), "GiB | capability", f"{p.major}.{p.minor}")
        print("bf16 supported:", torch.cuda.is_bf16_supported())
except Exception as e:
    print("torch: not importable ->", e)
for m in ("monai", "nibabel", "mlflow", "numpy", "pandas"):
    try:
        mod = __import__(m); print(f"{m}:", getattr(mod, "__version__", "?"))
    except Exception as e:
        print(f"{m}: not importable")
'@
$tmp = Join-Path $env:TEMP 'prowl_probe.py'; Set-Content -Path $tmp -Value $probe -Encoding ASCII
$exes = @()
$exes += (where.exe python) | Where-Object { $_ -and ($_ -notmatch 'WindowsApps') }
$exes += (py -0p) | ForEach-Object { ($_ -split '\s+')[-1] } | Where-Object { $_ -and (Test-Path $_) }
$exes += Get-ChildItem -Path $env:USERPROFILE -Filter python.exe -Recurse -Depth 5 -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\(\.venv[^\\]*|venv[^\\]*|envs\\[^\\]+)\\' } | ForEach-Object FullName
foreach ($exe in ($exes | Sort-Object -Unique)) { Section "Python packages: $exe" { & $exe $tmp } }
Section 'Possible PROWL checkouts (search under user profile)' { Get-ChildItem -Path $env:USERPROFILE -Directory -Recurse -Depth 5 -Filter 'PROWL*' -ErrorAction SilentlyContinue | ForEach-Object FullName }
$text = $L -join "`r`n"
Set-Content -Path $out -Value $text -Encoding UTF8
try { Set-Clipboard -Value $text } catch {}
Write-Host "Wrote $out (also copied to clipboard). Paste it to Claude or attach the file."
