param(
    [switch]$n
)

# Get Git username
$gitUser = git config --global --get user.name
if (-not $gitUser) { $gitUser = "UnknownUser" }

# Get hostname
$serverName = $env:COMPUTERNAME

# Get current datetime
$shortTime = Get-Date -Format "yyyy-MM-dd HH:mm"

Write-Host "Running git status..."
git status

Write-Host "Running git add..."
git add .

# Check if there are changes to commit
$hasChanges = git diff-index --quiet HEAD --
if ($LASTEXITCODE -eq 0) {
    Write-Host "No changes to commit."
    exit 0
}

Write-Host "Running git commit..."

# Build commit message
$subject = "[Auto] $gitUser@$serverName | $shortTime"

if ($n) {
    # -n mode: skip description
    Write-Host "Committing with subject only (-n mode)..."
    git commit -m $subject
} else {
    # Interactive mode: ask for description
    $description = Read-Host "Enter description (press Enter to skip)"
    
    if ([string]::IsNullOrEmpty($description)) {
        Write-Host "Committing with subject only..."
        git commit -m $subject
    } else {
        Write-Host "Committing with description..."
        git commit -m $subject -m $description
    }
}

Write-Host "Running git push..."
git push
