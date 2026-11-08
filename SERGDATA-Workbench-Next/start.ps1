#requires -Version 5.1
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

# Keep console output predictable when launched from start.cmd.
try {
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
} catch {
    # Encoding setup is best-effort; it must not prevent startup.
}

$bootstrapPython = $null
$bootstrapArgs = @()

$pythonLauncher = Get-Command 'py.exe' -ErrorAction SilentlyContinue
if ($pythonLauncher) {
    & $pythonLauncher.Source -3.12 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"
    if ($LASTEXITCODE -eq 0) {
        $bootstrapPython = $pythonLauncher.Source
        $bootstrapArgs = @('-3.12')
    }
}

if (-not $bootstrapPython) {
    $pythonCommand = Get-Command 'python.exe' -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        & $pythonCommand.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"
        if ($LASTEXITCODE -eq 0) {
            $bootstrapPython = $pythonCommand.Source
            $bootstrapArgs = @()
        }
    }
}

if (-not $bootstrapPython) {
    throw 'Требуется Python 3.12 или новее. Установи Python и повтори запуск.'
}

$venvPath = Join-Path $PSScriptRoot '.venv'
if (-not (Test-Path -LiteralPath $venvPath)) {
    & $bootstrapPython @bootstrapArgs -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        throw 'Не удалось создать виртуальное окружение .venv.'
    }
}

$python = Join-Path $venvPath 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'В .venv не найден Python. Проверь виртуальное окружение; пользовательские данные не затронуты.'
}

& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw 'Не удалось обновить pip. Проверь подключение к интернету.'
}

& $python -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) {
    throw 'Не удалось установить основные зависимости Workbench.'
}

& $python -m workbench.doctor
if ($LASTEXITCODE -ne 0) {
    throw 'Проверка окружения обнаружила проблему. Исправь её и повтори запуск.'
}

$envFile = Join-Path $PSScriptRoot '.env'
$envExample = Join-Path $PSScriptRoot '.env.example'
if (-not (Test-Path -LiteralPath $envFile) -and (Test-Path -LiteralPath $envExample)) {
    Copy-Item -LiteralPath $envExample -Destination $envFile
    Write-Host 'Создан файл .env из шаблона. Проверь настройки Knowledge MCP и PROJECT_ROOT.' -ForegroundColor Yellow
    Start-Process -FilePath 'notepad.exe' -ArgumentList ('"' + $envFile + '"') -Wait
}

& $python (Join-Path $PSScriptRoot 'main.py')
$applicationExitCode = $LASTEXITCODE
if ($applicationExitCode -ne 0) {
    throw "Workbench завершился с кодом $applicationExitCode."
}

exit 0
