# step2_port_scan.ps1
$inputFile = "alive_ips.txt"
$outputFile = "ip_port.txt"
$portRange = "-p-"   

if (-not (Get-Command nmap -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: nmap not installed or not in PATH." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $inputFile)) {
    Write-Host "ERROR: $inputFile not found. Run step1 first." -ForegroundColor Red
    exit 1
}

if (Test-Path $outputFile) { Remove-Item $outputFile }

Get-Content $inputFile | ForEach-Object {
    $ip = $_.Trim()
    Write-Host "Scanning $ip ..." -ForegroundColor Yellow
    $nmapOut = nmap $portRange --open -oG - $ip 2>$null | Select-String "Ports:"
    if ($nmapOut) {
        $portsLine = $nmapOut.ToString()
        if ($portsLine -match "Ports: (.*)") {
            $portsData = $Matches[1]
            $openPorts = $portsData -split ',' | ForEach-Object {
                if ($_ -match '(\d+)/open') { $matches[1] }
            }
            foreach ($port in $openPorts) {
                "${ip}:${port}" | Out-File -FilePath $outputFile -Append -Encoding ascii
                Write-Host "  Found open port: $port" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "  No open ports found." -ForegroundColor DarkGray
    }
}
Write-Host "Done. IP:port list saved to $outputFile"