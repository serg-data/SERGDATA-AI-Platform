$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw 'Сначала запусти start.cmd для создания .venv и установки основных зависимостей.'
}
& $python -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Не удалось установить дополнительные инструменты.' }
& $python -m workbench.doctor
if ($LASTEXITCODE -ne 0) { throw 'Проверка окружения обнаружила отсутствующие обязательные зависимости.' }
