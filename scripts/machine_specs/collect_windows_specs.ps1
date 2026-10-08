# Collects hardware/software specs of this Windows machine for ML training planning.
# Usage (from repo root):
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\machine_specs\collect_windows_specs.ps1
# Writes: scripts\machine_specs\windows_laptop_specs.raw.json
$ErrorActionPreference = 'SilentlyContinue'
$out = Join-Path $PSScriptRoot 'windows_laptop_specs.raw.json'

function Run($exe, $argList) {
  try { $r = & $exe @argList 2>&1 | Out-String; if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0 -and -not $r) { return $null }; return $r.Trim() } catch { return $null }
}

$cs   = Get-CimInstance Win32_ComputerSystem
$bios = Get-CimInstance Win32_BIOS
$os   = Get-CimInstance Win32_OperatingSystem
$cpu  = Get-CimInstance Win32_Processor
$mem  = Get-CimInstance Win32_PhysicalMemory
$arr  = Get-CimInstance Win32_PhysicalMemoryArray
$gpu  = Get-CimInstance Win32_VideoController
$bat  = Get-CimInstance Win32_Battery
$cv   = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'

# Accurate VRAM via registry (Win32_VideoController.AdapterRAM caps at 4 GB)
$gpuReg = @()
Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}' -ErrorAction SilentlyContinue | ForEach-Object {
  $p = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
  if ($p.DriverDesc) { $gpuReg += [ordered]@{ name = $p.DriverDesc; vram_bytes = $p.'HardwareInformation.qwMemorySize'; driver = $p.DriverVersion } }
}

$nvsmi = (Get-Command nvidia-smi -ErrorAction SilentlyContinue).Source
if (-not $nvsmi -and (Test-Path "$env:WINDIR\System32\nvidia-smi.exe")) { $nvsmi = "$env:WINDIR\System32\nvidia-smi.exe" }
$nv = $null; $nvFull = $null
if ($nvsmi) {
  $nv = Run $nvsmi @('--query-gpu=name,memory.total,driver_version,compute_cap,pcie.link.gen.max,pcie.link.width.max,power.limit,power.max_limit,clocks.max.sm','--format=csv')
  $nvFull = Run $nvsmi @()
}

$pyCmds = [ordered]@{}
foreach ($c in @('python','python3','py')) { $g = Get-Command $c -ErrorAction SilentlyContinue; if ($g) { $pyCmds[$c] = [ordered]@{ path = $g.Source; version = (Run $c @('--version')) } } }
$pyList = $null; if (Get-Command py -ErrorAction SilentlyContinue) { $pyList = Run 'py' @('-0p') }

$torchProbe = @'
import json, sys
d = {"python": sys.version, "executable": sys.executable}
try:
    import torch
    d["torch"] = torch.__version__
    d["torch_cuda_build"] = torch.version.cuda
    d["cuda_available"] = torch.cuda.is_available()
    if torch.cuda.is_available():
        p = torch.cuda.get_device_properties(0)
        d["cuda_device"] = p.name; d["cuda_total_mem_gb"] = round(p.total_memory/1024**3, 2)
        d["cudnn"] = torch.backends.cudnn.version(); d["bf16_supported"] = torch.cuda.is_bf16_supported()
except Exception as e:
    d["torch_error"] = repr(e)
for m in ("monai", "numpy", "nibabel", "SimpleITK", "mlflow"):
    try:
        mod = __import__(m); d[m] = getattr(mod, "__version__", "installed")
    except Exception:
        d[m] = None
print(json.dumps(d))
'@
$torchInfo = $null
$pyExe = if ($pyCmds.Contains('python')) { 'python' } elseif ($pyCmds.Contains('py')) { 'py' } else { $null }
if ($pyExe) { $tmp = Join-Path $env:TEMP 'prowl_torch_probe.py'; Set-Content -Path $tmp -Value $torchProbe -Encoding ascii; $torchInfo = Run $pyExe @($tmp); Remove-Item $tmp -ErrorAction SilentlyContinue }

$wsl = $null; if (Get-Command wsl -ErrorAction SilentlyContinue) { $wsl = ((Run 'wsl' @('-l','-v')) -replace "`0",'') }

$specs = [ordered]@{
  collected_at   = (Get-Date).ToString('o')
  hostname       = $env:COMPUTERNAME
  system         = [ordered]@{ manufacturer = $cs.Manufacturer; model = $cs.Model; system_type = $cs.SystemType; bios = $bios.SMBIOSBIOSVersion; serial_hidden = $true }
  os             = [ordered]@{ caption = $os.Caption; version = $os.Version; build = $os.BuildNumber; display_version = $cv.DisplayVersion; ubr = $cv.UBR; arch = $os.OSArchitecture }
  cpu            = @($cpu | ForEach-Object { [ordered]@{ name = $_.Name.Trim(); cores = $_.NumberOfCores; logical_processors = $_.NumberOfLogicalProcessors; max_clock_mhz = $_.MaxClockSpeed; l2_kb = $_.L2CacheSize; l3_kb = $_.L3CacheSize; virtualization_fw = $_.VirtualizationFirmwareEnabled } })
  memory         = [ordered]@{
    total_bytes  = $cs.TotalPhysicalMemory
    slots        = ($arr | Measure-Object -Property MemoryDevices -Sum).Sum
    max_capacity_kb = ($arr | Measure-Object -Property MaxCapacityEx -Sum).Sum
    modules      = @($mem | ForEach-Object { [ordered]@{ slot = $_.DeviceLocator; capacity_bytes = $_.Capacity; speed_mts = $_.Speed; configured_speed_mts = $_.ConfiguredClockSpeed; manufacturer = $_.Manufacturer; part = ($_.PartNumber -as [string]).Trim(); smbios_type = $_.SMBIOSMemoryType; form_factor = $_.FormFactor } })
  }
  gpu_wmi        = @($gpu | ForEach-Object { [ordered]@{ name = $_.Name; driver = $_.DriverVersion; adapter_ram_bytes_capped = $_.AdapterRAM; resolution = "$($_.CurrentHorizontalResolution)x$($_.CurrentVerticalResolution)"; refresh = $_.CurrentRefreshRate } })
  gpu_registry   = $gpuReg
  nvidia_smi_csv = $nv
  nvidia_smi_full= $nvFull
  physical_disks = @(Get-PhysicalDisk | ForEach-Object { [ordered]@{ name = $_.FriendlyName; media = "$($_.MediaType)"; bus = "$($_.BusType)"; size_bytes = $_.Size; health = "$($_.HealthStatus)" } })
  volumes        = @(Get-Volume | Where-Object DriveLetter | ForEach-Object { [ordered]@{ letter = "$($_.DriveLetter)"; label = $_.FileSystemLabel; fs = $_.FileSystem; type = "$($_.DriveType)"; size_bytes = $_.Size; free_bytes = $_.SizeRemaining } })
  battery        = @($bat | ForEach-Object { [ordered]@{ name = $_.Name; status = $_.BatteryStatus; charge_pct = $_.EstimatedChargeRemaining } })
  power_plan     = (Run 'powercfg' @('/getactivescheme'))
  python_cmds    = $pyCmds
  py_launcher    = $pyList
  python_ml_probe= $torchInfo
  nvcc           = (Run 'nvcc' @('--version'))
  cuda_path_env  = $env:CUDA_PATH
  conda          = (Run 'conda' @('--version'))
  git            = (Run 'git' @('--version'))
  docker         = (Run 'docker' @('--version'))
  wsl            = $wsl
}
$specs | ConvertTo-Json -Depth 6 | Out-File -FilePath $out -Encoding utf8
Write-Host "Wrote $out"
