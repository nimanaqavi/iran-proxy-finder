$ips = Get-Content .\ips.txt
$outFile = ".\alive_with_loss.txt"
# پاک کردن فایل خروجی اگر از قبل وجود داشته باشد
if (Test-Path $outFile) { Clear-Content $outFile }

foreach ($ip in $ips) {
    Write-Host "Checking $ip ..."
    $pingResult = ping -n 4 $ip
    # پیدا کردن خط حاوی "Lost = "
    $lostLine = $pingResult | Select-String "Lost = "
    if ($lostLine) {
        # استخراج عدد درصد (مثل 0%، 25%، ...)
        $lossPercent = [regex]::Match($lostLine, '(\d+)%').Groups[1].Value
        if ([int]$lossPercent -lt 100) {
            "$ip - $lossPercent%" | Out-File -FilePath $outFile -Append
        }
    }
}
Write-Host "Done! Results saved to $outFile"