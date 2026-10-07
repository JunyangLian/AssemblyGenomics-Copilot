# Run locally. The key is entered privately, never a command argument or file.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskSecureKey = Read-Host 'INTERN_DISCOVERY_API_KEY (hidden input)' -AsSecureString
$taskKeyPointer = [IntPtr]::Zero
$taskPlainKey = $null
try {
    $taskKeyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($taskSecureKey)
    $taskPlainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($taskKeyPointer)
    if ([string]::IsNullOrWhiteSpace($taskPlainKey)) {
        throw 'Key cannot be empty.'
    }
    [Environment]::SetEnvironmentVariable('INTERN_DISCOVERY_API_KEY', $taskPlainKey, 'User')
    $env:INTERN_DISCOVERY_API_KEY = $taskPlainKey
    Write-Output 'INTERN_DISCOVERY_API_KEY is set in the local user environment. No API call was made.'
}
finally {
    if ($taskKeyPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($taskKeyPointer)
    }
    $taskPlainKey = $null
    $taskSecureKey.Dispose()
}
