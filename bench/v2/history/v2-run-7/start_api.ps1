[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$taskPriorNoProxy = $env:NO_PROXY
try {
    if ([string]::IsNullOrWhiteSpace($env:INTERN_DISCOVERY_API_KEY)) {
        $env:INTERN_DISCOVERY_API_KEY = [Environment]::GetEnvironmentVariable('INTERN_DISCOVERY_API_KEY', 'User')
    }
    if ([string]::IsNullOrWhiteSpace($env:INTERN_DISCOVERY_API_KEY)) {
        throw 'INTERN_DISCOVERY_API_KEY is not set in the local environment.'
    }
    # Only this authorized provider bypasses the failing local proxy. TLS verification stays on.
    $taskNoProxyHosts = @($taskPriorNoProxy -split ',' | Where-Object { $_ })
    $taskNoProxyHosts += 'discovery-api.intern-ai.org.cn'
    $env:NO_PROXY = ($taskNoProxyHosts | Select-Object -Unique) -join ','
    $taskRepo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    Push-Location -LiteralPath $taskRepo
    try {
        python bench/v2/run.py --mode api
        if ($LASTEXITCODE -ne 0) { throw 'API runner stopped; inspect sanitized logs and cumulative ledger before resuming.' }
    }
    finally { Pop-Location }
}
finally { $env:NO_PROXY = $taskPriorNoProxy }
