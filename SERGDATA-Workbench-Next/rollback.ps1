param([string]$BackupPath = "")
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($BackupPath)) { $BackupPath = Read-Host 'Путь к папке резервной копии Knowledge-Integration' }
$BackupPath = (Resolve-Path -LiteralPath $BackupPath).Path
$ManifestPath = Join-Path $BackupPath 'manifest.json'
if (!(Test-Path -LiteralPath $ManifestPath)) { throw 'manifest.json не найден в резервной копии' }
$Items = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$Confirm = Read-Host 'Workbench должен быть остановлен. Выполнить откат? (Y/N)'
if ($Confirm -notin @('Y','y','Д','д')) { Write-Host 'Откат отменён.'; exit 2 }
foreach ($Item in $Items) {
    if (!(Test-Path -LiteralPath $Item.backup)) { throw "Резервный файл отсутствует: $($Item.backup)" }
    Copy-Item -LiteralPath $Item.backup -Destination $Item.target -Force
}
Write-Host 'Откат файлов завершён. База знаний и пользовательские данные не затрагивались.' -ForegroundColor Green
