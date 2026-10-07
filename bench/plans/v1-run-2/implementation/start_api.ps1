# Credentials are entered interactively, then passed only through process environment.
# Run from a local PowerShell terminal. No keys, .env files or registry writes.
$ErrorActionPreference = 'Stop'
$benchRepoRoot = Split-Path -Parent $PSScriptRoot
$benchKeyNames = @('DEEPSEEK_API_KEY', 'DASHSCOPE_API_KEY')
$benchOriginalKeys = @{}
$benchOriginalNoProxy = [Environment]::GetEnvironmentVariable('NO_PROXY', 'Process')
Push-Location -LiteralPath $benchRepoRoot
try {
    # Check approval and frozen identity before requesting credentials.
    python -c "import sys; sys.path.insert(0,'bench'); from run_plan import verify; from model_adapter import approval; from pathlib import Path; approval(Path('bench'),verify()); print('Approved run plan verified')"
    if ($LASTEXITCODE -ne 0) { throw 'Approval/frozen verification failed; no API calls made' }
    # Verified TLS connection failed through the local proxy, succeeded directly.
    # Affect only the two approved provider domains and restore this process value on exit.
    $benchDirectHosts = 'api.deepseek.com,dashscope.aliyuncs.com'
    if (-not [string]::IsNullOrEmpty($benchOriginalNoProxy)) { $benchDirectHosts = $benchOriginalNoProxy + ',' + $benchDirectHosts }
    [Environment]::SetEnvironmentVariable('NO_PROXY', $benchDirectHosts, 'Process')
    foreach ($benchKeyName in $benchKeyNames) {
        $benchOriginalKeys[$benchKeyName] = [Environment]::GetEnvironmentVariable($benchKeyName, 'Process')
        if ([string]::IsNullOrEmpty($benchOriginalKeys[$benchKeyName])) {
            $benchSecretInput = Read-Host -Prompt "Enter $benchKeyName (hidden)" -AsSecureString
            $benchSecretPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($benchSecretInput)
            try {
                [Environment]::SetEnvironmentVariable($benchKeyName, [Runtime.InteropServices.Marshal]::PtrToStringBSTR($benchSecretPointer), 'Process')
            } finally {
                [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($benchSecretPointer)
                $benchSecretInput.Dispose()
            }
            if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($benchKeyName, 'Process'))) {
                throw "Missing $benchKeyName; no API calls made"
            }
        }
    }
    Write-Output 'Starting approved B/C run: at most 576 requests and CNY 270 reserved allowance.'
    python bench/run.py --mode api
    if ($LASTEXITCODE -ne 0) { throw 'Run stopped; preserve bench/runs logs and ledger before attempting another run' }
} finally {
    [Environment]::SetEnvironmentVariable('NO_PROXY', $benchOriginalNoProxy, 'Process')
    foreach ($benchKeyName in $benchOriginalKeys.Keys) {
        [Environment]::SetEnvironmentVariable($benchKeyName, $benchOriginalKeys[$benchKeyName], 'Process')
    }
    Pop-Location
}
