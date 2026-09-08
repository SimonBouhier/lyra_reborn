param()
$ErrorActionPreference = 'Stop'
$repoP6 = Split-Path -Parent $PSScriptRoot
$pythonP6 = Join-Path $repoP6 '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonP6 -PathType Leaf)) { throw 'Python du dépôt introuvable.' }
$nodeP6 = (Get-Command node -ErrorAction Stop).Source
$runP6 = Join-Path $repoP6 ('data\runs\p6-verification\' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $runP6) { throw 'Le dossier de vérification doit être neuf.' }
$null = New-Item -ItemType Directory -Path $runP6
$tempP6 = Join-Path $runP6 'pytest-temp'
$oldLiveP6 = [Environment]::GetEnvironmentVariable('LYRA_LIVE', 'Process')
$testsP6 = @(
    'tests/test_p6_requests.py', 'tests/test_p6_requests_http.py',
    'tests/test_p6_journal_migration.py', 'tests/test_session_persistence.py',
    'tests/test_p6_http.py', 'tests/test_p6_concurrency.py', 'tests/test_p6_first_layers.py',
    'tests/test_p6_context.py', 'tests/test_p6_context_http.py',
    'tests/test_p6_chat_backend.py', 'tests/test_p6_dialogue_migration.py'
)
Push-Location -LiteralPath $repoP6
try {
    Remove-Item Env:LYRA_LIVE -ErrorAction SilentlyContinue
    & $pythonP6 -B -X utf8 -m pytest -q -p no:cacheprovider @testsP6 --basetemp $tempP6 --junitxml (Join-Path $runP6 'pytest.xml') --tb=short 2>&1 |
        Tee-Object -FilePath (Join-Path $runP6 'pytest.log')
    $pythonExitP6 = $LASTEXITCODE
    & $nodeP6 --test --test-reporter=tap tests/test_journal_client.cjs tests/test_p6_ui.cjs 2>&1 |
        Tee-Object -FilePath (Join-Path $runP6 'javascript.log')
    $nodeExitP6 = $LASTEXITCODE
    $pathsP6 = @('app/main.py', 'app/storage.py', 'app/session.py', 'app/journal.py',
        'app/requests.py', 'app/static/index.html', 'app/static/journal-client.js',
        'app/static/p6-ui.js', 'scripts/migrate_p6_journal.py', 'scripts/verifier_p6.ps1',
        'app/dialogue.py', 'app/dialogue_store.py', 'app/context.py', 'app/chat_backend.py',
        'app/static/dialogue-ui.js', 'scripts/migrate_p6_dialogue.py',
        'tests/test_journal_client.cjs', 'tests/test_p6_ui.cjs') + $testsP6
    $hashesP6 = foreach ($relativeP6 in $pathsP6) {
        [pscustomobject]@{ path = $relativeP6; sha256 = (Get-FileHash -LiteralPath (Join-Path $repoP6 $relativeP6) -Algorithm SHA256).Hash.ToLowerInvariant() }
    }
    $resultP6 = [ordered]@{
        completed_utc = [DateTime]::UtcNow.ToString('o')
        pytest_exit_code = $pythonExitP6
        javascript_exit_code = $nodeExitP6
        scope = 'P6 dialogue: scripted clients, temporary SQLite, Node simulated DOM. No live inference or user database migration.'
        files = @($hashesP6)
    }
    $resultP6 | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runP6 'verification.json') -Encoding UTF8
    Write-Output "Rapports : $runP6"
    if ($pythonExitP6 -ne 0 -or $nodeExitP6 -ne 0) { throw 'Au moins un contrôle P6 a échoué ; consulter les rapports.' }
} finally {
    if ($null -eq $oldLiveP6) { Remove-Item Env:LYRA_LIVE -ErrorAction SilentlyContinue }
    else { $env:LYRA_LIVE = $oldLiveP6 }
    Pop-Location
}
