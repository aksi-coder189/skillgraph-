$ErrorActionPreference = 'Stop'
$backend = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $backend 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'SkillGraph Python environment is missing.' }
$listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $listener) {
    $script = Join-Path $backend 'start_backend.py'
    Start-Process -FilePath $python -ArgumentList @($script) -WorkingDirectory $backend -WindowStyle Hidden
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        $listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($listener) { break }
    }
}
if (-not $listener) { throw 'SkillGraph API did not start. Check XAMPP MySQL and the backend.' }
