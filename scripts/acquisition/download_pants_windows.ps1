<#
Windows PanTS acquisition (archive download only, no extraction, never deletes).
Windows counterpart of download_pants.py (which is macOS/APFS-only).

- Downloads the pinned PanTS inventory (docs/capstone/data/acquisition-2026-09-19.json) to the external
  drive with volume label QUINN, under <drive>:\PROWL\sources\pants\acquisition-<rev12>\
- Resumable: partials are kept as <name>.part; re-running continues where it stopped.
- Verifies size and the publisher SHA-256 (labels have none -> local SHA-256 is recorded).
- Keeps the PC awake while running. Logs JSONL to the acquisition folder.

Usage: double-click download_pants_windows.bat, or
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\acquisition\download_pants_windows.ps1
#>
param(
  [string]$DriveLabel = 'QUINN',
  [string]$Inventory  = (Join-Path $PSScriptRoot '..\..\docs\capstone\data\acquisition-2026-09-19.json'),
  [long]$ReserveBytes = 25GB
)
$ErrorActionPreference = 'Stop'

# --- keep the machine awake (system, not display) while this process runs ---
Add-Type -Namespace Prowl -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
[void][Prowl.Power]::SetThreadExecutionState([uint32]2147483649)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED

function Fmt([double]$b) { '{0:N1} GB' -f ($b / 1e9) }

# --- locate the QUINN drive ---
$vol = @(Get-Volume | Where-Object { $_.FileSystemLabel -eq $DriveLabel -and $_.DriveLetter })
if ($vol.Count -ne 1) { throw "Expected exactly one mounted volume labelled '$DriveLabel'; found $($vol.Count). Plug in the drive and retry." }
$vol = $vol[0]
$root = "$($vol.DriveLetter):\"
Write-Host "Drive $DriveLabel = $root  fs=$($vol.FileSystem)  size=$(Fmt $vol.Size)  free=$(Fmt $vol.SizeRemaining)"

# --- inventory ---
$inv = Get-Content -Raw -Path $Inventory | ConvertFrom-Json
$rev = $inv.pants.huggingface_revision
if ($rev -notmatch '^[a-f0-9]{40}$') { throw 'Inventory does not pin an immutable Hugging Face revision' }
$files  = @($inv.pants.files)
$labels = [pscustomobject]@{ name = 'PanTSMini_Label.tar.gz'; bytes = [long]$inv.pants.labels.bytes; sha256 = $null; url = $inv.pants.labels.url; etag = $inv.pants.labels.etag; kind = 'labels' }
$queue  = @($files[0], $labels) + $files[1..($files.Count - 1)]   # metadata, labels, train shards, test shard

$dest = Join-Path $root ("PROWL\sources\pants\acquisition-" + $rev.Substring(0, 12))
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$log = Join-Path $dest ("attempt-" + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + "-windows.jsonl")
function Record($evt, $fields = @{}) {
  $o = [ordered]@{ at = (Get-Date).ToUniversalTime().ToString('o'); event = $evt }
  foreach ($k in $fields.Keys) { $o[$k] = $fields[$k] }
  $line = ($o | ConvertTo-Json -Compress)
  Add-Content -Path $log -Value $line -Encoding utf8
  Write-Host $line
}

# --- capacity check for what is still missing ---
$remaining = 0L
foreach ($it in $queue) {
  $final = Join-Path $dest $it.name; $part = "$final.part"
  if (Test-Path $final) { continue }
  $have = if (Test-Path $part) { (Get-Item $part).Length } else { 0 }
  $remaining += ([long]$it.bytes - $have)
}
Record 'attempt_started' @{ host = $env:COMPUTERNAME; drive = $root; filesystem = $vol.FileSystem; free_bytes = $vol.SizeRemaining; remaining_bytes = $remaining; files = $queue.Count; revision = $rev; extraction = $false }
if ($remaining + $ReserveBytes -gt $vol.SizeRemaining) { Record 'refused_capacity'; throw "Not enough free space: need $(Fmt ($remaining + $ReserveBytes)) incl. reserve, have $(Fmt $vol.SizeRemaining)" }
if ($vol.FileSystem -eq 'FAT32') { throw 'FAT32 cannot hold files > 4 GB; reformat the drive as exFAT or NTFS.' }

$curl = "$env:WINDIR\System32\curl.exe"
$i = 0
foreach ($it in $queue) {
  $i++
  $name = $it.name; $bytes = [long]$it.bytes
  if ((Split-Path $name -Leaf) -ne $name) { throw "Unsafe inventory filename: $name" }
  $final = Join-Path $dest $name; $part = "$final.part"; $side = "$final.sha256"
  if ((Test-Path $final) -and (Test-Path $side) -and ((Get-Item $final).Length -eq $bytes)) { Record 'verified_existing' @{ name = $name }; continue }

  if (-not (Test-Path $final)) {
    for ($try = 1; $try -le 6; $try++) {
      $have = if (Test-Path $part) { (Get-Item $part).Length } else { 0 }
      if ($have -gt $bytes) { throw "Oversize partial for $name; inspect manually" }
      if ($have -eq $bytes) { break }
      Write-Host ""
      Write-Host "[$i/$($queue.Count)] $name  $(Fmt $have) / $(Fmt $bytes)  (attempt $try)"
      Record 'starting' @{ name = $name; resume_bytes = $have; expected_bytes = $bytes; attempt = $try }
      $cargs = @('-L', '--fail', '--retry', '5', '--retry-delay', '15', '--retry-all-errors', '--connect-timeout', '60',
                '-A', 'PROWL-research-acquisition/1.0', '-C', '-', '-o', $part)
      if ($it.etag) { $cargs += @('-H', "If-Match: $($it.etag)") }
      $cargs += $it.url
      & $curl @cargs
      $code = $LASTEXITCODE
      if ($code -eq 0) { break }
      Record 'network_attempt_failed' @{ name = $name; curl_exit = $code; attempt = $try }
      Start-Sleep -Seconds ([math]::Min(300, 15 * [math]::Pow(2, $try)))
    }
    $have = if (Test-Path $part) { (Get-Item $part).Length } else { 0 }
    if ($have -ne $bytes) { Record 'attempt_stopped' @{ name = $name; bytes = $have; expected_bytes = $bytes }; throw "Incomplete transfer for $name ($(Fmt $have) of $(Fmt $bytes)). Re-run to resume." }
    $verify = $part
  } else { $verify = $final }

  Write-Host "Verifying SHA-256 of $name ..."
  $actual = (Get-FileHash -Algorithm SHA256 -Path $verify).Hash.ToLower()
  if ($it.sha256 -and $actual -ne $it.sha256) { Record 'sha256_mismatch' @{ name = $name; actual = $actual; expected = $it.sha256 }; throw "SHA-256 mismatch for $name; file retained for investigation" }
  if ($verify -eq $part) { Rename-Item -Path $part -NewName $name }
  Set-Content -Path $side -Value "$actual  $name" -Encoding ascii
  Record 'verified_download' @{ name = $name; bytes = $bytes; sha256 = $actual; publisher_sha256_available = [bool]$it.sha256 }
}
Record 'archive_queue_complete' @{ source_ready = $false; next_step = 'extraction (separate step)' }
Write-Host ""
Write-Host "All $($queue.Count) PanTS files downloaded and verified in $dest"
[void][Prowl.Power]::SetThreadExecutionState([uint32]2147483648)
