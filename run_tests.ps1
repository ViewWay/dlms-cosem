# PowerShell test runner for dlms-cosem
$ErrorActionPreference = "Continue"

$ProjectDir = "D:\Users\HongLinHe\Projects\dlms-cosem"
$OutputFile = Join-Path $ProjectDir "test_results.txt"

# Change to project directory
Set-Location $ProjectDir

# Clear previous output
if (Test-Path $OutputFile) {
    Remove-Item $OutputFile
}

# Run pytest
Write-Host "Running pytest..." -ForegroundColor Green
$Output = & python -m pytest tests/test_china_gb.py tests/test_sml.py tests/test_protocol_frames.py tests/test_util_modules.py tests/test_hls_connection_live.py -v --tb=short 2>&1

# Save output
$Output | Out-File -FilePath $OutputFile -Encoding UTF8

# Display output
Write-Host "Test Results:" -ForegroundColor Yellow
Get-Content $OutputFile

Write-Host ""
Write-Host "Results saved to: $OutputFile" -ForegroundColor Cyan
