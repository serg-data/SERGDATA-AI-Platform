param(
    [Parameter(Mandatory = $true)]
    [string]$Root
)
$ErrorActionPreference = 'Stop'
$files = @(
    @{ Relative = 'workbench\agent.py'; Expected = '6e0d59d3bf94e112b4d0d1bbc73db870f2a4b0584349ca327e660df80b5b8c36'; NewHash = 'fea660aa8f32c41384856c26c5fec9fb667e108937cd82aaf4052131e2368c4f' },
    @{ Relative = 'workbench\tool_call_adapter.py'; Expected = '824faed016fc7061f585483bc8fb817128087e67e1a893c8b6c924aaafed72a2'; NewHash = '824faed016fc7061f585483bc8fb817128087e67e1a893c8b6c924aaafed72a2' }
)
$targets = @()
foreach ($item in $files) {
    $target = Join-Path $Root $item.Relative
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "SAFE STOP: target not found: $target. No files changed." }
    $actual = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $item.Expected) {
        throw "SAFE STOP: $($item.Relative) hash mismatch. Expected $($item.Expected), got $actual. No files changed. Do not force installation; provide current files for a compatible rebuild."
    }
    $source = Join-Path $PSScriptRoot $item.Relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Patch source missing: $source" }
    $targets += [pscustomobject]@{ Target = $target; Source = $source; NewHash = $item.NewHash }
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backups = @()
foreach ($item in $targets) {
    $backup = "$($item.Target).bak-$stamp"
    Copy-Item -LiteralPath $item.Target -Destination $backup
    $backups += [pscustomobject]@{ Target = $item.Target; Backup = $backup }
}
try {
    foreach ($item in $targets) {
        Copy-Item -LiteralPath $item.Source -Destination $item.Target -Force
        $actual = (Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $item.NewHash) { throw "Post-copy hash mismatch for $($item.Target): $actual" }
    }
    Write-Host "Installed both compatible files. Backups:" -ForegroundColor Green
    $backups | ForEach-Object { Write-Host "  $($_.Backup)" }
} catch {
    foreach ($backup in $backups) {
        if (Test-Path -LiteralPath $backup.Backup) {
            Copy-Item -LiteralPath $backup.Backup -Destination $backup.Target -Force
        }
    }
    throw "Install failed; both original files were restored. $($_.Exception.Message)"
}
