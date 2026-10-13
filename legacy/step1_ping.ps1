# step1_ping.ps1 - Ping IPs and avoid reprocessing duplicates
# Input: ips.txt (one IPv4 per line)
# Output: alive_ips.txt (IPs that responded to ping)
# Log: processed_ips.txt (keeps track of all tested IPs)

$inputFile = "ips.txt"
$aliveFile = "alive_ips.txt"
$processedFile = "processed_ips.txt"   # Log file for all tested IPs
$pingTimeout = 1000                     # milliseconds

# Load list of already processed IPs (if file exists)
if (Test-Path $processedFile) {
    $processed = Get-Content $processedFile | Where-Object { $_ -match '^(\d{1,3}\.){3}\d{1,3}$' }
} else {
    $processed = @()
}

# Read all IPs from input, remove duplicates, keep only valid IPv4 format
$allIps = Get-Content $inputFile | Where-Object { $_ -match '^(\d{1,3}\.){3}\d{1,3}$' } | Sort-Object -Unique

# Filter out IPs that have already been processed
$newIps = $allIps | Where-Object { $_ -notin $processed }

if ($newIps.Count -eq 0) {
    Write-Host "No new IPs to test." -ForegroundColor Yellow
    exit 0
}

Write-Host "Number of new IPs: $($newIps.Count)" -ForegroundColor Cyan

# Clear previous alive_ips.txt (optional – use -Append if you want to keep older results)
if (Test-Path $aliveFile) { Remove-Item $aliveFile }

$newAlive = @()
foreach ($ip in $newIps) {
    Write-Host "Pinging $ip ... " -NoNewline
    $ping = Test-Connection -ComputerName $ip -Count 1 -Quiet -ErrorAction SilentlyContinue
    if ($ping) {
        Write-Host "OK" -ForegroundColor Green
        $ip | Out-File -FilePath $aliveFile -Append
        $newAlive += $ip
    } else {
        Write-Host "FAILED" -ForegroundColor Red
    }
}

# Append newly tested IPs (even those that failed) to the processed log
$newIps | Out-File -FilePath $processedFile -Append -Encoding ascii

Write-Host "`nSummary:"
Write-Host "  New IPs tested: $($newIps.Count)"
Write-Host "  Alive IPs (ping OK): $($newAlive.Count)"
Write-Host "  Saved to $aliveFile"