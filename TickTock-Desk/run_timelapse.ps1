# Transitional shim: the Windows scheduled task still points to this file.
# After running update_task.bat (switches the task to pythonw directly,
# fully windowless), this file can be deleted.
# NOTE: Start-Process is required for GUI executables; "&" would let the
# parent exit immediately and take pythonw down with it.
$script = Join-Path $PSScriptRoot "capture_once.py"
Start-Process -FilePath "D:\DevEnv\miniconda3\envs\dev\pythonw.exe" -ArgumentList ('"' + $script + '"') -WorkingDirectory $PSScriptRoot -Wait
