# Updates scheduled task "\Murphy\TimeLapse解... (name matched by content below)
# from powershell.exe (console flash) to pythonw.exe direct (fully windowless).
# Requires admin: double-click update_task.bat to self-elevate.
# NOTE: keep this file pure ASCII - PowerShell 5.1 reads BOM-less files as ANSI.
$ErrorActionPreference = "Stop"

$service = New-Object -ComObject Schedule.Service
$service.Connect()
$folder = $service.GetFolder("\Murphy")

$found = $null
foreach ($t in $folder.GetTasks(1)) {
    if ($t.Xml -like "*run_timelapse*" -or $t.Xml -like "*capture_once*") { $found = $t; break }
}
if (-not $found) { Write-Host "ERROR: task not found under \Murphy\"; pause; exit 1 }
Write-Host ("Found task: " + $found.Name)

$def = $found.Definition
Write-Host ("  old action: " + $def.Actions.Item(1).Path + " " + $def.Actions.Item(1).Arguments)

$def.Actions.Clear()
$action = $def.Actions.Create(0)   # TASK_ACTION_EXEC
$action.Path = "D:\DevEnv\miniconda3\envs\dev\pythonw.exe"
$action.Arguments = '"D:\DevProj\TickTock-Timelapse\TickTock-Desk\capture_once.py"'
$action.WorkingDirectory = "D:\DevProj\TickTock-Timelapse\TickTock-Desk"

# 4 = TASK_UPDATE;  3 = TASK_LOGON_INTERACTIVE_TOKEN (no password needed)
$folder.RegisterTaskDefinition($found.Name, $def, 4, $null, $null, 3) | Out-Null

$verify = $folder.GetTask($found.Name).Definition.Actions
Write-Host ("  new action: " + $verify.Item(1).Path + " " + $verify.Item(1).Arguments)
Write-Host ""
Write-Host "Done. Next unlock will run fully windowless. You may delete this script."
Write-Host ""
pause
