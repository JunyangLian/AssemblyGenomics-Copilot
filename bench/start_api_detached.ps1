# Launch the same approved harness independently of the chat terminal.
# Credentials enter only hidden input and temporary inherited process environment.
$ErrorActionPreference = 'Stop'
$benchRoot = $PSScriptRoot
$benchRepoRoot = Split-Path -Parent $benchRoot
$benchKeyNames = @('DEEPSEEK_API_KEY', 'DASHSCOPE_API_KEY')
$benchOriginalKeys = @{}
$benchOriginalNoProxy = [Environment]::GetEnvironmentVariable('NO_PROXY', 'Process')
$benchWorker = $null
$benchStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
$benchOutputBase = Join-Path $benchRoot ('runs/api_worker_' + $benchStamp)
$benchPython = @(Get-Command python -CommandType Application)[0].Source
Push-Location -LiteralPath $benchRepoRoot
try {
    python -c "import sys; sys.path.insert(0,'bench'); from run_plan import verify; from model_adapter import approval; from pathlib import Path; approval(Path('bench'),verify()); print('Approved unchanged run plan verified')"
    if ($LASTEXITCODE -ne 0) { throw 'Approval/frozen verification failed' }
    $benchLock = Join-Path $benchRoot 'runs/API_ACTIVE.lock'
    $benchAbsentOwner = $null
    if (Test-Path -LiteralPath $benchLock) {
        $benchOldOwner = [int](Get-Content -LiteralPath $benchLock)
        try { $null = [System.Diagnostics.Process]::GetProcessById($benchOldOwner) }
        catch [System.ArgumentException] { $benchAbsentOwner = $benchOldOwner }
        if ($null -eq $benchAbsentOwner) { throw 'Existing queue process is present; leave its lock and requests untouched' }
        $benchRecovery = [ordered]@{
            timestamp_utc = [DateTime]::UtcNow.ToString('o')
            absent_previous_pid = $benchAbsentOwner
            plan_sha256 = (Get-Content -LiteralPath (Join-Path $benchRoot 'RUN_PLAN.sha256')).Trim()
            launcher_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
            reason = 'Previous lock owner is absent. Retain ledger and all responses; resume same plan. Reserved requests are never resent.'
            parameters_changed = $false
        }
        $benchRecoveryText = ($benchRecovery | ConvertTo-Json) -replace "`r`n", "`n"
        [IO.File]::WriteAllText((Join-Path $benchRoot 'PROCESS_RECOVERY.json'), $benchRecoveryText + "`n", [Text.UTF8Encoding]::new($false))
        Remove-Item -LiteralPath $benchLock
    }
    $benchDirectHosts = 'api.deepseek.com,dashscope.aliyuncs.com'
    if (-not [string]::IsNullOrEmpty($benchOriginalNoProxy)) { $benchDirectHosts = $benchOriginalNoProxy + ',' + $benchDirectHosts }
    [Environment]::SetEnvironmentVariable('NO_PROXY', $benchDirectHosts, 'Process')
    foreach ($benchKeyName in $benchKeyNames) {
        $benchOriginalKeys[$benchKeyName] = [Environment]::GetEnvironmentVariable($benchKeyName, 'Process')
        if ([string]::IsNullOrEmpty($benchOriginalKeys[$benchKeyName])) {
            $benchSecretInput = Read-Host -Prompt "Enter $benchKeyName (hidden)" -AsSecureString
            $benchSecretPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($benchSecretInput)
            try { [Environment]::SetEnvironmentVariable($benchKeyName, [Runtime.InteropServices.Marshal]::PtrToStringBSTR($benchSecretPointer), 'Process') }
            finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($benchSecretPointer); $benchSecretInput.Dispose() }
            if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($benchKeyName, 'Process'))) { throw "Missing $benchKeyName" }
        }
    }
    $benchWorker = Start-Process -FilePath $benchPython -ArgumentList @('-u', 'bench/resume_api.py') -WorkingDirectory $benchRepoRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput ($benchOutputBase + '.stdout.log') -RedirectStandardError ($benchOutputBase + '.stderr.log')
    $benchLockDeadline = [DateTime]::UtcNow.AddSeconds(30)
    while (-not (Test-Path -LiteralPath $benchLock)) {
        if ($benchWorker.HasExited) { throw 'API worker exited during startup; review its stderr log' }
        if ([DateTime]::UtcNow -gt $benchLockDeadline) { throw 'Worker has not acquired lock; leave process and ledger untouched' }
        Start-Sleep -Milliseconds 500
    }
} finally {
    [Environment]::SetEnvironmentVariable('NO_PROXY', $benchOriginalNoProxy, 'Process')
    foreach ($benchKeyName in $benchOriginalKeys.Keys) { [Environment]::SetEnvironmentVariable($benchKeyName, $benchOriginalKeys[$benchKeyName], 'Process') }
    Pop-Location
}
# The postprocessor inherits the restored environment and never needs credentials.
$benchFollower = Start-Process -FilePath $benchPython -ArgumentList @('-u', 'bench/finish_api.py') -WorkingDirectory $benchRepoRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput ($benchOutputBase + '.finish.stdout.log') -RedirectStandardError ($benchOutputBase + '.finish.stderr.log')
$benchLaunch = [ordered]@{
    timestamp_utc = [DateTime]::UtcNow.ToString('o')
    worker_pid = $benchWorker.Id
    finisher_pid = $benchFollower.Id
    plan_sha256 = (Get-Content -LiteralPath (Join-Path $benchRoot 'RUN_PLAN.sha256')).Trim()
    launcher_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    output_prefix = $benchOutputBase
    credentials = 'Temporary inherited process environment only; no key values or Authorization in this record'
    model_parameters_changed = $false
    existing_reservations_retained = $true
}
$benchLaunchText = ($benchLaunch | ConvertTo-Json) -replace "`r`n", "`n"
[IO.File]::WriteAllText((Join-Path $benchRoot 'PROCESS_LAUNCH.json'), $benchLaunchText + "`n", [Text.UTF8Encoding]::new($false))
Write-Output "Detached approved queue PID $($benchWorker.Id); finisher PID $($benchFollower.Id)"
