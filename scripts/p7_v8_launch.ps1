param(
    [ValidateSet('lifecycle-smoke', 'q0')]
    [string]$Phase,
    [string]$LifecycleOutput,
    [double]$LifecycleDelay = 3.0,
    [int]$Timeout = 600
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot '.venv\Scripts\python.exe'
$runner = Join-Path $PSScriptRoot 'p7_v8.py'
$runRoot = Join-Path $repoRoot 'data\runs'

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Python environment not found: $pythonExe"
}
New-Item -ItemType Directory -Path $runRoot -Force | Out-Null

$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$logStem = Join-Path $runRoot "p7_v8_${Phase}_launcher_$stamp"
$stdoutLog = "$logStem.stdout.log"
$stderrLog = "$logStem.stderr.log"

$runnerArgs = @(
    $runner,
    $Phase,
    '--timeout', [string]$Timeout,
    '--output-root', $runRoot,
    '--stdout-log', $stdoutLog,
    '--stderr-log', $stderrLog
)
if ($Phase -eq 'lifecycle-smoke') {
    if ([string]::IsNullOrWhiteSpace($LifecycleOutput)) {
        throw 'LifecycleOutput is required for lifecycle-smoke'
    }
    $runnerArgs += @('--lifecycle-output', $LifecycleOutput, '--lifecycle-delay', [string]$LifecycleDelay)
}

function ConvertTo-QuotedArgument([string]$Value) {
    return '"' + $Value.Replace('"', '\"') + '"'
}

$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $pythonExe
$startInfo.WorkingDirectory = $repoRoot
$startInfo.UseShellExecute = $true
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.Arguments = ($runnerArgs | ForEach-Object { ConvertTo-QuotedArgument $_ }) -join ' '

$process = [System.Diagnostics.Process]::Start($startInfo)
if ($null -eq $process) {
    throw 'Detached process did not start'
}

[pscustomobject]@{
    phase = $Phase
    pid = $process.Id
    stdout = $stdoutLog
    stderr = $stderrLog
    lifecycle_output = $LifecycleOutput
    controller_returned_at_utc = (Get-Date).ToUniversalTime().ToString('o')
} | ConvertTo-Json -Compress
