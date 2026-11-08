param(
    [string]$WorkbenchPath = "",
    [string]$KnowledgePath = ""
)
$ErrorActionPreference = 'Stop'
$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($WorkbenchPath)) { $WorkbenchPath = Read-Host 'Путь к папке SERGDATA Workbench' }
if ([string]::IsNullOrWhiteSpace($KnowledgePath)) { $KnowledgePath = Read-Host 'Путь к папке AI-Knowledge' }
$WorkbenchPath = (Resolve-Path -LiteralPath $WorkbenchPath).Path
$KnowledgePath = (Resolve-Path -LiteralPath $KnowledgePath).Path
if (!(Test-Path -LiteralPath (Join-Path $WorkbenchPath 'main.py'))) { throw 'В выбранной папке Workbench не найден main.py' }
if (!(Test-Path -LiteralPath (Join-Path $WorkbenchPath 'static\app.js'))) { throw 'В Workbench не найдена static\app.js' }
if (!(Test-Path -LiteralPath (Join-Path $KnowledgePath 'kb.py'))) { throw 'В AI-Knowledge не найден kb.py' }
if (!(Test-Path -LiteralPath (Join-Path $KnowledgePath 'server.py'))) { throw 'В AI-Knowledge не найден server.py' }
$Confirm = Read-Host 'Убедись, что Workbench остановлен. Продолжить? (Y/N)'
if ($Confirm -notin @('Y','y','Д','д')) { Write-Host 'Установка отменена.'; exit 2 }
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupRoot = Join-Path $env:LOCALAPPDATA "SERGDATA\backups\Knowledge-Integration-$Stamp"
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
$Map = @(
    @{ Source = 'workbench\main.py'; Target = (Join-Path $WorkbenchPath 'main.py'); Backup = 'workbench\main.py' },
    @{ Source = 'workbench\static\app.js'; Target = (Join-Path $WorkbenchPath 'static\app.js'); Backup = 'workbench\static\app.js' },
    @{ Source = 'workbench\static\index.html'; Target = (Join-Path $WorkbenchPath 'static\index.html'); Backup = 'workbench\static\index.html' },
    @{ Source = 'workbench\static\style.css'; Target = (Join-Path $WorkbenchPath 'static\style.css'); Backup = 'workbench\static\style.css' },
    @{ Source = 'ai-knowledge\kb.py'; Target = (Join-Path $KnowledgePath 'kb.py'); Backup = 'ai-knowledge\kb.py' },
    @{ Source = 'ai-knowledge\server.py'; Target = (Join-Path $KnowledgePath 'server.py'); Backup = 'ai-knowledge\server.py' },
    @{ Source = 'ai-knowledge\update-knowledge.ps1'; Target = (Join-Path $KnowledgePath 'update-knowledge.ps1'); Backup = 'ai-knowledge\update-knowledge.ps1' }
)
$Manifest = @()
foreach ($Item in $Map) {
    $Source = Join-Path $PatchRoot $Item.Source
    if (!(Test-Path -LiteralPath $Source)) { throw "В архиве отсутствует файл: $($Item.Source)" }
    if (!(Test-Path -LiteralPath $Item.Target)) { throw "Не найден целевой файл: $($Item.Target)" }
    $BackupFile = Join-Path $BackupRoot $Item.Backup
    New-Item -ItemType Directory -Path (Split-Path -Parent $BackupFile) -Force | Out-Null
    Copy-Item -LiteralPath $Item.Target -Destination $BackupFile
    $Manifest += [pscustomobject]@{ target = $Item.Target; backup = $BackupFile; source = $Source; source_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Source).Hash }
}
$Manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $BackupRoot 'manifest.json') -Encoding UTF8
try {
    foreach ($Item in $Map) {
        Copy-Item -LiteralPath (Join-Path $PatchRoot $Item.Source) -Destination $Item.Target -Force
        $Expected = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $PatchRoot $Item.Source)).Hash
        $Actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Item.Target).Hash
        if ($Expected -ne $Actual) { throw "Проверка SHA256 не пройдена: $($Item.Target)" }
    }
    Write-Host "Установка завершена. Резервная копия: $BackupRoot" -ForegroundColor Green
    Write-Host 'База SQLite, .env, .workbench, Git-папки, SSH-ключи и профили не изменялись.'
} catch {
    Write-Host "Ошибка установки: $_. Выполняю автоматический откат." -ForegroundColor Red
    foreach ($Item in $Manifest) { if (Test-Path -LiteralPath $Item.backup) { Copy-Item -LiteralPath $Item.backup -Destination $Item.target -Force } }
    throw
}
