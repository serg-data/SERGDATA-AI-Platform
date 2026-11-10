param(
    [string]$BasePath = $PSScriptRoot,
    [string]$PythonPath = "",
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"

# Безопасное обновление базы знаний.
# Не используем git reset --hard и git clean.
$Base = (Resolve-Path -LiteralPath $BasePath).Path
$Code = Join-Path $Base "code"
$BackupRoot = Join-Path $Base "backups"
if (![string]::IsNullOrWhiteSpace($PythonPath)) {
    $Python = $PythonPath
} else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) { $Python = $PythonCommand.Source } else { $Python = "python" }
}
$Indexer = Join-Path $Base "kb.py"
$RepoList = Join-Path $Base "repositories.json"
$Log = Join-Path $Base "update-knowledge.log"
$TimeTag = Get-Date -Format "yyyyMMdd-HHmmss"

Set-Location $Base
Start-Transcript -Path $Log -Append

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string[]]$GitArgs,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )

    & git -C $WorkingDirectory @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (git exit code $LASTEXITCODE)"
    }
}

function Test-RepoHealthy {
    param([string]$Path, [string]$Name)

    if (!(Test-Path -LiteralPath (Join-Path $Path ".git"))) {
        return $false
    }

    & git -C $Path rev-parse --verify HEAD *> $null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    $Tracked = @(& git -C $Path ls-files)
    if ($LASTEXITCODE -ne 0 -or $Tracked.Count -eq 0) {
        return $false
    }

    if ($Name -eq "systemd") {
        return (
            (Test-Path -LiteralPath (Join-Path $Path "README")) -and
            (Test-Path -LiteralPath (Join-Path $Path "meson.build"))
        )
    }

    foreach ($RelativePath in $Tracked) {
        if ([string]::IsNullOrWhiteSpace($RelativePath)) {
            continue
        }

        if (Test-Path -LiteralPath (Join-Path $Path $RelativePath)) {
            return $true
        }
    }

    return $false
}

function Rebuild-SystemdSafely {
    param([string]$Path, [string]$Url)

    $Parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    $Stage = Join-Path $Parent ("systemd-stage-" + $TimeTag)
    $Backup = Join-Path $BackupRoot ("systemd-before-swap-" + $TimeTag)

    if (Test-Path -LiteralPath $Stage) {
        throw "Временная папка уже существует: $Stage"
    }

    Write-Host "systemd: создаю временный checkout." -ForegroundColor Yellow

    Invoke-Git -WorkingDirectory $Base `
        -GitArgs @("clone", "--depth", "1", "--no-checkout", $Url, $Stage) `
        -FailureMessage "Не удалось создать временный clone systemd"

    Invoke-Git -WorkingDirectory $Stage `
        -GitArgs @("sparse-checkout", "init", "--no-cone") `
        -FailureMessage "Не удалось включить sparse checkout"

    # Исключаем Windows-несовместимые тестовые файлы.
    $Patterns = @("/*", "!/test/", "!/test/**")

    Invoke-Git -WorkingDirectory $Stage `
        -GitArgs (@("sparse-checkout", "set", "--no-cone") + $Patterns) `
        -FailureMessage "Не удалось задать sparse patterns"

    Invoke-Git -WorkingDirectory $Stage `
        -GitArgs @("-c", "core.protectNTFS=false", "checkout") `
        -FailureMessage "Checkout systemd завершился ошибкой"

    if (!(Test-RepoHealthy -Path $Stage -Name "systemd")) {
        throw "Временный systemd не прошёл проверку. Исходная папка не изменена: $Stage"
    }

    $StageStatus = @(& git -C $Stage status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $StageStatus.Count -gt 0) {
        throw "Временный systemd не прошёл проверку чистоты."
    }

    if (Test-Path -LiteralPath $Path) {
        Move-Item -LiteralPath $Path -Destination $Backup

        try {
            Move-Item -LiteralPath $Stage -Destination $Path
        }
        catch {
            if (!(Test-Path -LiteralPath $Path) -and
                (Test-Path -LiteralPath $Backup)) {
                Move-Item -LiteralPath $Backup -Destination $Path
            }
            throw
        }

        Write-Host "Резервная копия systemd: $Backup" -ForegroundColor Yellow
    }
    else {
        Move-Item -LiteralPath $Stage -Destination $Path
    }

    if (!(Test-RepoHealthy -Path $Path -Name "systemd")) {
        throw "После замены systemd не прошёл проверку. Резервная копия: $Backup"
    }

    Write-Host "systemd: проверка пройдена." -ForegroundColor Green
}


function Test-ManPagesSparseCheckout {
    param([string]$Path)

    $Enabled = & git -C $Path config --bool core.sparseCheckout 2>$null
    if ($LASTEXITCODE -ne 0 -or "$Enabled".Trim() -ne "true") {
        return $false
    }

    $Patterns = @(& git -C $Path sparse-checkout list 2>$null)
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    $Required = @(
        "!/man2/_Exit.2",
        "!/man2/_exit.2",
        "!/man3/NAN.3",
        "!/man3/nan.3"
    )

    foreach ($Pattern in $Required) {
        if ($Patterns -notcontains $Pattern) {
            return $false
        }
    }

    return $true
}

function Rebuild-ManPagesSafely {
    param([string]$Path, [string]$Url)

    $Parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    $Stage = Join-Path $Parent ("man-pages-stage-" + $TimeTag)
    $Backup = Join-Path $BackupRoot ("man-pages-before-sparse-" + $TimeTag)

    if (Test-Path -LiteralPath $Stage) {
        throw "Временная папка уже существует: $Stage"
    }

    Write-Host "man-pages: создаю свежую копию с исключением четырёх конфликтующих путей Windows." -ForegroundColor Yellow

    Invoke-Git -WorkingDirectory $Base `
        -GitArgs @("clone", "--depth", "1", "--no-checkout", $Url, $Stage) `
        -FailureMessage "Не удалось создать временный clone man-pages"

    Invoke-Git -WorkingDirectory $Stage `
        -GitArgs @("sparse-checkout", "init", "--no-cone") `
        -FailureMessage "Не удалось включить sparse checkout для man-pages"

    # Включаем всё содержимое, кроме четырёх путей, которые различаются
    # только регистром и конфликтуют на типичной файловой системе Windows.
    $Patterns = @(
        "/*",
        "!/man2/_Exit.2",
        "!/man2/_exit.2",
        "!/man3/NAN.3",
        "!/man3/nan.3"
    )

    Invoke-Git -WorkingDirectory $Stage `
        -GitArgs (@("sparse-checkout", "set", "--no-cone") + $Patterns) `
        -FailureMessage "Не удалось задать исключения sparse checkout для man-pages"

    Invoke-Git -WorkingDirectory $Stage `
        -GitArgs @("checkout") `
        -FailureMessage "Checkout man-pages завершился ошибкой"

    if (!(Test-RepoHealthy -Path $Stage -Name "man-pages")) {
        throw "Временный man-pages не прошёл проверку. Исходная папка не изменена: $Stage"
    }

    foreach ($RelativePath in @("man2/_Exit.2", "man2/_exit.2", "man3/NAN.3", "man3/nan.3")) {
        if (Test-Path -LiteralPath (Join-Path $Stage $RelativePath)) {
            throw "Конфликтующий файл неожиданно присутствует в рабочей копии: $RelativePath"
        }
    }

    $StageStatus = @(& git -C $Stage status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $StageStatus.Count -gt 0) {
        throw "Временный man-pages не прошёл проверку чистоты."
    }

    if (Test-Path -LiteralPath $Path) {
        Move-Item -LiteralPath $Path -Destination $Backup

        try {
            Move-Item -LiteralPath $Stage -Destination $Path
        }
        catch {
            if (!(Test-Path -LiteralPath $Path) -and
                (Test-Path -LiteralPath $Backup)) {
                Move-Item -LiteralPath $Backup -Destination $Path
            }
            throw
        }

        Write-Host "Резервная копия man-pages: $Backup" -ForegroundColor Yellow
    }
    else {
        Move-Item -LiteralPath $Stage -Destination $Path
    }

    if (!(Test-RepoHealthy -Path $Path -Name "man-pages")) {
        throw "После замены man-pages не прошёл проверку. Резервная копия: $Backup"
    }

    Write-Host "man-pages: рабочая копия настроена; четыре конфликтующих пути исключены, остальные файлы доступны для обновления." -ForegroundColor Green
}

function Update-Repo {
    param([string]$Name, [string]$Url)

    if ([string]::IsNullOrWhiteSpace($Name) -or
        $Name -notmatch '^[a-zA-Z0-9._-]+$' -or
        $Name -eq "." -or $Name -eq "..") {
        throw "Недопустимое имя репозитория: $Name"
    }

    if ($Url -notmatch '^https://github\.com/[^/]+/[^/]+(?:\.git)?/?$') {
        throw "Недопустимый URL GitHub для ${Name}: $Url"
    }

    $Path = Join-Path $Code $Name

    Write-Host "`n========== $Name ==========" -ForegroundColor Cyan

    if ($Name -eq "man-pages" -and (Test-Path -LiteralPath $Path)) {
        if (!(Test-ManPagesSparseCheckout -Path $Path)) {
            Rebuild-ManPagesSafely -Path $Path -Url $Url
            return
        }
    }

    if ($Name -eq "systemd" -and (Test-Path -LiteralPath $Path)) {
        if (!(Test-RepoHealthy -Path $Path -Name $Name)) {
            Rebuild-SystemdSafely -Path $Path -Url $Url
            return
        }

        $Status = @(& git -C $Path status --porcelain)
        if ($LASTEXITCODE -ne 0) {
            throw "Не удалось проверить состояние systemd."
        }

        if ($Status.Count -gt 0) {
            Write-Host "systemd изменён локально. Создаю проверенную замену." -ForegroundColor Yellow
            Rebuild-SystemdSafely -Path $Path -Url $Url
            return
        }
    }

    if (Test-Path -LiteralPath (Join-Path $Path ".git")) {
        if (!(Test-RepoHealthy -Path $Path -Name $Name)) {
            throw "${Name}: репозиторий повреждён или неполон. Папка сохранена: $Path"
        }

        $Status = @(& git -C $Path status --porcelain)
        if ($LASTEXITCODE -ne 0) {
            throw "Не удалось проверить локальные изменения в $Name."
        }

        # Отслеживаемые изменения не сбрасываем и не перезаписываем.
        $TrackedChanges = @(
            $Status | Where-Object {
                $_.Length -ge 2 -and $_.Substring(0, 2) -ne "??"
            }
        )

        if ($TrackedChanges.Count -gt 0) {
            $Details = $TrackedChanges -join "`n"
            throw "${Name}: найдены локальные изменения. Обновление пропущено:`n$Details"
        }

        if ($Status.Count -gt 0) {
            Write-Host "$Name`: оставляю неотслеживаемые файлы без изменений." -ForegroundColor Yellow
            $Status | ForEach-Object { Write-Host "  $_" }
        }

        Invoke-Git -WorkingDirectory $Path `
            -GitArgs @("pull", "--ff-only") `
            -FailureMessage "Не удалось обновить $Name"
    }
    elseif (Test-Path -LiteralPath $Path) {
        throw "Папка $Path существует, но не является Git-репозиторием. Она сохранена."
    }
    else {
        $Stage = Join-Path $Code ($Name + "-stage-" + $TimeTag)

        if (Test-Path -LiteralPath $Stage) {
            throw "Временная папка уже существует: $Stage"
        }

        Invoke-Git -WorkingDirectory $Base `
            -GitArgs @("clone", "--depth", "1", $Url, $Stage) `
            -FailureMessage "Не удалось скачать $Name"

        if (!(Test-RepoHealthy -Path $Stage -Name $Name)) {
            throw "Первичная копия $Name не прошла проверку. Она сохранена в $Stage"
        }

        $StageStatus = @(& git -C $Stage status --porcelain)
        if ($LASTEXITCODE -ne 0 -or $StageStatus.Count -gt 0) {
            throw "Первичная копия $Name не прошла проверку чистоты."
        }

        Move-Item -LiteralPath $Stage -Destination $Path
    }

    if (!(Test-RepoHealthy -Path $Path -Name $Name)) {
        throw "${Name}: после обновления не пройдена проверка полноты."
    }

    Write-Host "${Name}: проверка пройдена" -ForegroundColor Green
}

$ExitCode = 0

try {
    if (!(Test-Path -LiteralPath $Python)) {
        $PythonCommand = Get-Command $Python -ErrorAction SilentlyContinue
        if ($PythonCommand) { $Python = $PythonCommand.Source }
        else { throw "Не найден Python: $Python" }
    }

    if (!(Test-Path -LiteralPath $Indexer)) {
        throw "Не найден индексатор: $Indexer"
    }

    if (!(Test-Path -LiteralPath $Code)) {
        throw "Не найдена папка: $Code"
    }

    # New recovery copies live outside code, so they are not indexed as source.
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

    if (!(Test-Path -LiteralPath $RepoList)) {
        throw "Не найден список репозиториев: $RepoList"
    }

    if (!(Get-Command git -ErrorAction SilentlyContinue)) {
        throw "Git не найден. Проверь установку и PATH."
    }

    $Config = Get-Content -LiteralPath $RepoList -Raw | ConvertFrom-Json

    if ($null -eq $Config.repositories -or $Config.repositories.Count -eq 0) {
        throw "В repositories.json нет репозиториев."
    }

    # Проверяем список целиком до начала обновления.
    $Names = @{}

    foreach ($Repo in $Config.repositories) {
        if ($null -eq $Repo.name -or $null -eq $Repo.url) {
            throw "У каждой записи должны быть поля name и url."
        }

        $Key = ([string]$Repo.name).ToLowerInvariant()

        if ($Names.ContainsKey($Key)) {
            throw "Повторяется имя репозитория: $($Repo.name)"
        }

        $Names[$Key] = $true
    }

    # Ошибка одного репозитория не мешает обработать остальные.
    # Локальные изменения отслеживаемых файлов остаются нетронутыми.
    $RepoFailures = @()

    foreach ($Repo in $Config.repositories) {
        try {
            Update-Repo -Name ([string]$Repo.name) -Url ([string]$Repo.url)
        }
        catch {
            $Message = "$($Repo.name): $($_.Exception.Message)"
            $RepoFailures += $Message

            Write-Host "`nПРОПУСК РЕПОЗИТОРИЯ: $Message" -ForegroundColor Yellow
            Write-Host "Перехожу к следующему репозиторию." -ForegroundColor Yellow
        }
    }

    # Индексация выполняется после обработки всех репозиториев.
    Write-Host "`n========== ПЕРЕИНДЕКСАЦИЯ ==========" -ForegroundColor Cyan

    & $Python $Indexer index

    if ($LASTEXITCODE -ne 0) {
        throw "Индексатор завершился с ошибкой."
    }

    if ($RepoFailures.Count -gt 0) {
        $ExitCode = 2

        Write-Host "`nОБНОВЛЕНИЕ ЗАВЕРШЕНО ЧАСТИЧНО." -ForegroundColor Yellow
        Write-Host "Индексация выполнена, но некоторые репозитории пропущены:" -ForegroundColor Yellow

        $RepoFailures | ForEach-Object {
            Write-Host " - $_" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "`nОБНОВЛЕНИЕ И ИНДЕКСАЦИЯ ЗАВЕРШЕНЫ." -ForegroundColor Green
    }
}
catch {
    $ExitCode = 1
    Write-Host "`nОШИБКА: $_" -ForegroundColor Red
}
finally {
    Stop-Transcript
    Write-Host "`nПодробный журнал: $Log"
    if (!$NoPause) { Read-Host "Нажми Enter для завершения" }
}

exit $ExitCode
