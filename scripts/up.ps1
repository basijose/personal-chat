$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root '..\backend'
$frontend = Join-Path $root '..\frontend'
$backendDb = Join-Path $backend 'personal_chat.db'

foreach ($port in 8000, 3000) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

if (Test-Path $backendDb) {
    Remove-Item -LiteralPath $backendDb -Force
}

$backendJob = Start-Job -Name 'personal-chat-backend' -ScriptBlock {
    param($backendPath)
    Set-Location $backendPath
    alembic upgrade head | Out-Host
    python -m scripts.seed | Out-Host
    uvicorn app.main:app --host 127.0.0.1 --port 8000
} -ArgumentList $backend

$frontendJob = Start-Job -Name 'personal-chat-frontend' -ScriptBlock {
    param($frontendPath)
    Set-Location $frontendPath
    npm run dev -- --hostname 127.0.0.1 --port 3000
} -ArgumentList $frontend

Write-Host 'Personal Chat local demo starting...'
Write-Host 'Backend:  http://127.0.0.1:8000'
Write-Host 'Frontend: http://127.0.0.1:3000'
Write-Host 'Press Ctrl+C to stop.'

while ($true) {
    foreach ($job in @($backendJob, $frontendJob)) {
        $output = Receive-Job -Job $job -Keep -ErrorAction SilentlyContinue
        foreach ($line in $output) {
            if ($line -ne $null -and $line.ToString().Length -gt 0) {
                Write-Host "[$($job.Name)] $line"
            }
        }
        if ($job.State -eq 'Failed') {
            throw "Job $($job.Name) failed."
        }
    }

    if ($backendJob.State -eq 'Completed' -or $frontendJob.State -eq 'Completed') {
        break
    }

    Start-Sleep -Seconds 1
}
