# Silent PowerShell wrapper for TimeLapse - completely hidden execution
# This script runs completely silently in the background

# Execute the batch file silently
$batPath = Join-Path $PSScriptRoot "run_timelapse.bat"

# Start the process completely hidden
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "cmd.exe"
$processInfo.Arguments = "/c `"$batPath`""
$processInfo.UseShellExecute = $false
$processInfo.CreateNoWindow = $true
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden

$process = [System.Diagnostics.Process]::Start($processInfo)
$process.WaitForExit()

# Script completes silently - no output or windows