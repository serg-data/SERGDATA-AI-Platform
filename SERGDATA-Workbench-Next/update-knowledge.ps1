param(
    [string]$BasePath = 'F:\AI-Knowledge',
    [string]$PythonPath = 'C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe',
    [string]$RepositoryName = '',
    [switch]$DeepRepair,
    [switch]$DeepRepairAll,
    [switch]$NoPause
)

# Compatible with Windows PowerShell 5.1. Native stderr is redirected to a file,
# never allowed to become a terminating PowerShell ErrorRecord.
$ErrorActionPreference = 'Stop'
$Base = [IO.Path]::GetFullPath($BasePath)
$Code = Join-Path $Base 'code'
$ArchiveRoot = Join-Path $Base 'archive'
$StageRoot = Join-Path $ArchiveRoot 'staging'
$BackupRoot = Join-Path $Base 'backups'
$Python = $PythonPath
$Indexer = Join-Path $Base 'kb.py'
$GitSync = Join-Path $Base 'git_incremental.py'
$PendingManifest = Join-Path $Base 'index\pending-git-changes.json'
$RepoList = Join-Path $Base 'repositories.json'
$Log = Join-Path $Base 'update-knowledge.log'
$TimeTag = Get-Date -Format 'yyyyMMdd-HHmmss-fff'

if ($DeepRepair -and $DeepRepairAll) { throw 'Используй только один режим: -DeepRepair или -DeepRepairAll.' }
if ($DeepRepair -and [string]::IsNullOrWhiteSpace($RepositoryName)) { throw 'Для -DeepRepair обязательно укажи -RepositoryName.' }

Set-Location $Base
Start-Transcript -Path $Log -Append

function Invoke-Native {
    param(
        [Parameter(Mandatory=$true)][string]$Program,
        [Parameter(Mandatory=$true)][string[]]$Arguments,
        [string]$WorkingDirectory = $Base
    )
    $stderrFile = Join-Path $env:TEMP ('ai-kb-native-' + [guid]::NewGuid().ToString('N') + '.stderr')
    $stdout = @()
    $stderr = @()
    $code = -1
    $oldPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        Push-Location $WorkingDirectory
        try {
            # In Windows PowerShell 5.1, native stderr can be promoted to an
            # ErrorRecord. Redirect stream 2 to disk to avoid that conversion.
            $stdout = @(& $Program @Arguments 2> $stderrFile)
            $code = $LASTEXITCODE
        }
        finally { Pop-Location }
        if (Test-Path -LiteralPath $stderrFile) {
            $stderr = @(Get-Content -LiteralPath $stderrFile -ErrorAction SilentlyContinue)
        }
    }
    finally {
        $ErrorActionPreference = $oldPreference
        Remove-Item -LiteralPath $stderrFile -Force -ErrorAction SilentlyContinue
    }
    [pscustomobject]@{ ExitCode = [int]$code; StdOut = @($stdout); StdErr = @($stderr) }
}

function Invoke-Git {
    param([string]$WorkingDirectory, [string[]]$GitArgs, [string]$FailureMessage)
    $r = Invoke-Native -Program 'git' -Arguments (@('-C', $WorkingDirectory) + $GitArgs) -WorkingDirectory $Base
    foreach ($line in $r.StdOut) { Write-Host ([string]$line) }
    foreach ($line in $r.StdErr) { Write-Host ([string]$line) }
    if ($r.ExitCode -ne 0) {
        $detail = (@($r.StdErr) + @($r.StdOut) | Where-Object { $_ }) -join ' | '
        throw "$FailureMessage (git exit code $($r.ExitCode)). $detail"
    }
    return ,$r.StdOut
}

function Get-GitText {
    param([string]$WorkingDirectory, [string[]]$GitArgs)
    $r = Invoke-Native -Program 'git' -Arguments (@('-C', $WorkingDirectory) + $GitArgs) -WorkingDirectory $Base
    if ($r.ExitCode -ne 0) { return $null }
    return (@($r.StdOut) -join "`n").Trim()
}

function Test-RepoHealthy {
    param([string]$Path, [string]$Name)
    if (!(Test-Path -LiteralPath $Path -PathType Container)) { return $false }
    $gitDir = Join-Path $Path '.git'
    if (!(Test-Path -LiteralPath $gitDir)) { return $false }
    if (!(Get-GitText $Path @('rev-parse','--verify','HEAD'))) { return $false }
    $trackedText = Get-GitText $Path @('ls-files')
    if ([string]::IsNullOrWhiteSpace($trackedText)) { return $false }

    # Repositories may contain paths that Windows cannot represent (for example
    # colon-containing fuzz-test artifacts). Such a path must not abort the
    # health check for the entire repository. Require at least one materialized
    # tracked file, while Git object integrity is checked independently below.
    $materialized = $false
    foreach ($relative in ($trackedText -split "`n")) {
        if ([string]::IsNullOrWhiteSpace($relative)) { continue }
        try {
            $candidate = Join-Path $Path $relative.TrimEnd("`r")
            if (Test-Path -LiteralPath $candidate -PathType Leaf -ErrorAction Stop) {
                $materialized = $true
                break
            }
        }
        catch [System.ArgumentException] { continue }
        catch [System.Management.Automation.ItemNotFoundException] { continue }
        catch [System.IO.PathTooLongException] { continue }
        catch { continue }
    }
    if (!$materialized) { return $false }
    $fsck = Invoke-Native -Program 'git' -Arguments @('-C',$Path,'fsck','--connectivity-only','--no-reflogs') -WorkingDirectory $Base
    if ($fsck.ExitCode -ne 0) { return $false }
    return $true
}

function Get-WindowsInvalidGitPaths {
    param([string]$Path)

    # Git output may arrive from Windows PowerShell 5.1 as either one string
    # containing several lines or as an array of line strings. Normalize both
    # shapes before inspecting paths; otherwise a multi-line string can be
    # treated as one path and the scan incorrectly reports zero matches.
    $tree = Invoke-Native -Program 'git' -Arguments @('-C',$Path,'ls-tree','-r','--name-only','HEAD') -WorkingDirectory $Base
    if ($tree.ExitCode -ne 0) {
        $detail = (@($tree.StdErr) + @($tree.StdOut)) -join ' | '
        throw "Не удалось получить список путей HEAD для Windows-проверки. $detail"
    }

    $treeLines = New-Object System.Collections.Generic.List[string]
    foreach ($entry in @($tree.StdOut)) {
        if ($null -eq $entry) { continue }
        if ($entry -is [System.Array]) {
            $entryValues = $entry
        }
        else {
            $entryValues = @([string]$entry)
        }
        foreach ($entryValue in $entryValues) {
            foreach ($line in ([string]$entryValue -split '\r?\n')) {
                $normalized = ([string]$line).TrimEnd("`r")
                if (-not [string]::IsNullOrWhiteSpace($normalized)) {
                    $treeLines.Add($normalized)
                }
            }
        }
    }

    $invalid = New-Object System.Collections.Generic.List[string]
    $invalidChars = [char[]]@('<','>',':','"','/','\','|','?','*')
    foreach ($relative in $treeLines) {
        $bad = $false
        foreach ($component in ($relative -split '/')) {
            if ($component.IndexOfAny($invalidChars) -ge 0 -or
                $component -match '[\x00-\x1f]' -or
                $component.EndsWith('.') -or $component.EndsWith(' ') -or
                $component -match '^(?i:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)' -or
                $component.Length -gt 255) {
                $bad = $true
                break
            }
        }
        if ($bad) { $invalid.Add($relative) }
    }

    Write-Host "Windows path scan: checked $($treeLines.Count) tracked paths; incompatible: $($invalid.Count)" -ForegroundColor Cyan
    foreach ($path in $invalid) {
        Write-Host "Windows-incompatible tracked path: $path" -ForegroundColor Yellow
    }
    return ,@($invalid.ToArray())
}

function ConvertTo-SparsePatternLiteral {
    param([string]$Path)
    # Sparse-checkout --no-cone patterns use gitignore escaping.
    return ($Path -replace '([\\*?\[\]])','\$1')
}

function Set-RepoCheckout {
    param([string]$Path, [string]$Name)

    # Proactively discover Windows-invalid tracked paths. A plain checkout is
    # not sufficient: Git for Windows can silently leave these paths deleted
    # while returning exit code 0, which made the staging tree appear dirty.
    $invalidPaths = @(Get-WindowsInvalidGitPaths -Path $Path)
    $patterns = @('/*')
    foreach ($badPath in $invalidPaths) {
        $patterns += '!/' + (ConvertTo-SparsePatternLiteral -Path $badPath)
    }

    if ($invalidPaths.Count -gt 0) {
        Invoke-Git $Path @('sparse-checkout','init','--no-cone') "$Name`: cannot initialize sparse checkout" | Out-Null
        Invoke-Git $Path (@('sparse-checkout','set','--no-cone') + $patterns) "$Name`: cannot apply Windows-safe sparse patterns" | Out-Null
        $sparseEnabled = Get-GitText $Path @('config','--bool','core.sparseCheckout')
        if ($sparseEnabled -ne 'true') {
            throw "$Name`: Git не включил core.sparseCheckout после настройки; staging не будет установлен."
        }
        Write-Host "$Name`: заранее исключено Windows-несовместимых путей: $($invalidPaths.Count)" -ForegroundColor Yellow
        foreach ($badPath in $invalidPaths) {
            Write-Host "  Исключён из checkout: $badPath" -ForegroundColor Yellow
        }
    }

    $checkout = Invoke-Native -Program 'git' -Arguments @('-C',$Path,'-c','core.protectNTFS=false','checkout') -WorkingDirectory $Base
    foreach ($line in $checkout.StdOut) { Write-Host ([string]$line) }
    foreach ($line in $checkout.StdErr) { Write-Host ([string]$line) }
    if ($checkout.ExitCode -ne 0) {
        $diagnostic = (@($checkout.StdErr) + @($checkout.StdOut)) -join "`n"
        throw "$Name`: checkout failed after proactive Windows-path filtering. $diagnostic"
    }

    # Do not trust checkout's exit code alone. Confirm that Git sees no missing
    # tracked files after applying the sparse rules.
    $status = Get-GitText $Path @('status','--porcelain=v1','--untracked-files=all')
    if ($null -eq $status -or $status.Length -gt 0) {
        throw "$Name`: staging остаётся грязным после Windows-safe checkout. $status"
    }
    Write-Host "$Name`: checkout completed; excluded Windows-incompatible paths: $($invalidPaths.Count)" -ForegroundColor Green
}

function Rebuild-RepositorySafely {
    param([string]$Name, [string]$Url)
    if ($Name -notmatch '^[A-Za-z0-9._-]+$' -or $Name -in @('.','..')) { throw "Недопустимое имя репозитория: $Name" }
    if ($Url -notmatch '^https://github\.com/[^/]+/[^/]+(?:\.git)?/?$') { throw "Недопустимый URL репозитория: $Url" }

    $target = Join-Path $Code $Name
    $stage = Join-Path $StageRoot ($Name + '-stage-' + $TimeTag)
    $backup = Join-Path $BackupRoot ($Name + '-before-deep-repair-' + $TimeTag)
    New-Item -ItemType Directory -Path $StageRoot,$BackupRoot -Force | Out-Null
    if (Test-Path -LiteralPath $stage) { throw "Staging уже существует: $stage" }

    Write-Host "`n========== DEEP REPAIR: $Name ==========" -ForegroundColor Cyan
    Write-Host "Временная копия: $stage" -ForegroundColor Yellow
    Invoke-Git $Base @('clone','--depth','1','--no-checkout',$Url,$stage) "$Name`: clone failed" | Out-Null
    if (!(Test-Path -LiteralPath (Join-Path $stage '.git'))) { throw "$Name`: после clone отсутствует .git. Исходная папка не затронута; staging сохранён: $stage" }
    $origin = Get-GitText $stage @('remote','get-url','origin')
    $normalizeUrl = { param($value) ([string]$value).Trim().TrimEnd('/').Replace('.git','') }
    if (!$origin -or (& $normalizeUrl $origin) -ne (& $normalizeUrl $Url)) {
        throw "$Name`: origin staging-клона не совпадает с URL из repositories.json. Исходная папка не затронута; staging сохранён: $stage"
    }
    Set-RepoCheckout $stage $Name

    if (!(Test-RepoHealthy $stage $Name)) { throw "$Name`: staging не прошёл проверку полноты/целостности. Исходная папка не затронута: $stage" }
    $stageStatus = Get-GitText $stage @('status','--porcelain','--untracked-files=all')
    if ($null -eq $stageStatus -or $stageStatus.Length -gt 0) { throw "$Name`: staging не чистый. Исходная папка не затронута: $stage" }

    # Verify the fetched commit against the advertised default-branch HEAD.
    $remote = Invoke-Native -Program 'git' -Arguments @('ls-remote',$Url,'HEAD') -WorkingDirectory $Base
    if ($remote.ExitCode -ne 0) { throw "$Name`: не удалось запросить upstream HEAD. Старая папка не затронута. $(@($remote.StdErr) -join ' ')" }
    $remoteLine = @($remote.StdOut | Where-Object { $_ -match '^[0-9a-fA-F]{40}\s+HEAD$' }) | Select-Object -First 1
    if (!$remoteLine) { throw "$Name`: upstream не вернул HEAD. Старая папка не затронута." }
    $expected = ($remoteLine -split '\s+')[0].ToLowerInvariant()
    $actual = (Get-GitText $stage @('rev-parse','HEAD')).ToLowerInvariant()
    if ($actual -ne $expected) { throw "$Name`: HEAD клона $actual не совпал с upstream $expected. Старая папка не затронута." }

    $oldMoved = $false
    $newInstalled = $false
    $failedInstall = Join-Path $StageRoot ($Name + '-failed-install-' + $TimeTag)
    try {
        if (Test-Path -LiteralPath $target) {
            Move-Item -LiteralPath $target -Destination $backup -ErrorAction Stop
            $oldMoved = $true
            Write-Host "Старая рабочая копия сохранена: $backup" -ForegroundColor Yellow
        }
        Move-Item -LiteralPath $stage -Destination $target -ErrorAction Stop
        $newInstalled = $true
        if (!(Test-RepoHealthy $target $Name)) { throw 'Установленная копия не прошла проверку целостности.' }
        $finalHead = Get-GitText $target @('rev-parse','HEAD')
        $finalStatus = Get-GitText $target @('status','--porcelain','--untracked-files=all')
        $finalOrigin = Get-GitText $target @('remote','get-url','origin')
        if ($finalHead -ne $expected -or $null -eq $finalStatus -or $finalStatus.Length -gt 0 -or !$finalOrigin -or (& $normalizeUrl $finalOrigin) -ne (& $normalizeUrl $Url)) {
            throw 'Проверка установленной копии не пройдена (HEAD/status/origin).'
        }
        Write-Host "$Name`: восстановлен успешно. HEAD=$finalHead" -ForegroundColor Green
        if ($oldMoved) { Write-Host "Резервная копия: $backup" -ForegroundColor Green }
    }
    catch {
        $reason = $_.Exception.Message
        try {
            # Never move an existing target unless this function had already moved
            # the original aside and successfully installed the staging clone.
            # In particular, a failed first Move-Item must leave the original path
            # completely untouched.
            if ($newInstalled -and (Test-Path -LiteralPath $target)) {
                if (Test-Path -LiteralPath $failedInstall) {
                    $failedInstall = Join-Path $StageRoot ($Name + '-failed-install-' + [guid]::NewGuid().ToString('N'))
                }
                Move-Item -LiteralPath $target -Destination $failedInstall -ErrorAction Stop
                $newInstalled = $false
            }
            if ($oldMoved -and (Test-Path -LiteralPath $backup)) {
                if (Test-Path -LiteralPath $target) {
                    throw "Нельзя вернуть резерв: целевой путь уже занят '$target'. Резерв сохранён в '$backup'."
                }
                Move-Item -LiteralPath $backup -Destination $target -ErrorAction Stop
                $oldMoved = $false
                Write-Host "Откат выполнен: старая папка возвращена в $target" -ForegroundColor Yellow
            }
        }
        catch {
            throw "$Name`: КРИТИЧЕСКАЯ ОШИБКА ОТКАТА. Старая копия/резерв находится в '$backup'. Ошибка отката: $($_.Exception.Message). Первичная ошибка: $reason"
        }
        throw "$Name`: установка отменена; выполнен откат. Причина: $reason. Неудачная установка (если была): $failedInstall"
    }
}

function Update-RepoNormally {
    param([string]$Name, [string]$Url)
    $path = Join-Path $Code $Name
    Write-Host "`n========== $Name ==========" -ForegroundColor Cyan
    if (Test-Path -LiteralPath $path) {
        if (!(Test-RepoHealthy $path $Name)) { throw "$Name`: рабочая копия повреждена/неполна. Используй -DeepRepair -RepositoryName $Name." }
        $status = Get-GitText $path @('status','--porcelain','--untracked-files=all')
        if ($null -eq $status) { throw "$Name`: не удалось получить git status." }
        if ($status.Length -gt 0) { throw "$Name`: есть локальные изменения. Рабочая копия сохранена; для полной замены используй -DeepRepair -RepositoryName $Name." }
    }
    elseif (Test-Path -LiteralPath $path) { throw "$Name`: путь существует, но это не каталог репозитория." }

    $r = Invoke-Native -Program $Python -Arguments @($GitSync,'--base',$Base,'--name',$Name,'--url',$Url,'--manifest',$PendingManifest) -WorkingDirectory $Base
    foreach ($line in $r.StdOut) { Write-Host ([string]$line) }
    foreach ($line in $r.StdErr) { Write-Host ([string]$line) }
    if ($r.ExitCode -ne 0) { throw "$Name`: git_incremental завершился с кодом $($r.ExitCode)." }
    if (!(Test-RepoHealthy $path $Name)) { throw "$Name`: после обновления не пройдена проверка полноты." }
    Write-Host "$Name`: проверка пройдена" -ForegroundColor Green
}

$exitCode = 0
try {
    foreach ($required in @($Code,$RepoList)) { if (!(Test-Path -LiteralPath $required)) { throw "Не найден обязательный путь: $required" } }
    if (!(Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git не найден в PATH.' }
    if (!$DeepRepair -and !$DeepRepairAll) {
        foreach ($required in @($Python,$Indexer,$GitSync)) { if (!(Test-Path -LiteralPath $required)) { throw "Не найден обязательный путь: $required" } }
    }
    New-Item -ItemType Directory -Path $ArchiveRoot,$StageRoot,$BackupRoot -Force | Out-Null
    $config = Get-Content -LiteralPath $RepoList -Raw | ConvertFrom-Json
    $repos = @($config.repositories)
    if (!$repos.Count) { throw 'repositories.json не содержит репозиториев.' }
    $seen = @{}
    foreach ($repo in $repos) {
        $name = [string]$repo.name; $url = [string]$repo.url
        if ($name -notmatch '^[A-Za-z0-9._-]+$' -or $name -in @('.','..')) { throw "Недопустимое имя в repositories.json: $name" }
        if ($url -notmatch '^https://github\.com/[^/]+/[^/]+(?:\.git)?/?$') { throw "Недопустимый URL в repositories.json: $url" }
        $key = $name.ToLowerInvariant(); if ($seen.ContainsKey($key)) { throw "Дублируется репозиторий: $name" }; $seen[$key] = $true
    }
    if ($DeepRepair -and !($seen.ContainsKey($RepositoryName.ToLowerInvariant()))) { throw "Репозиторий '$RepositoryName' не найден в repositories.json." }

    $failures = @()
    foreach ($repo in $repos) {
        $name = [string]$repo.name; $url = [string]$repo.url
        if ($DeepRepair -and $name -ne $RepositoryName) { continue }
        try {
            if ($DeepRepair -or $DeepRepairAll) { Rebuild-RepositorySafely -Name $name -Url $url }
            else { Update-RepoNormally -Name $name -Url $url }
        }
        catch {
            $msg = "$name`: $($_.Exception.Message)"
            $failures += $msg
            Write-Host "ПРОПУСК РЕПОЗИТОРИЯ: $msg" -ForegroundColor Yellow
        }
    }

    if ($DeepRepair -or $DeepRepairAll) {
        Write-Host 'Глубокое восстановление: индексация намеренно не запускалась. Сначала проверь Git Doctor и файлы.' -ForegroundColor Yellow
    }
    else {
        $releaseSync = Join-Path $Base 'release_sync.py'
        if (Test-Path -LiteralPath $releaseSync) {
            $r = Invoke-Native -Program $Python -Arguments @($releaseSync,'--manifest',$PendingManifest) -WorkingDirectory $Base
            foreach ($line in $r.StdOut) { Write-Host ([string]$line) }; foreach ($line in $r.StdErr) { Write-Host ([string]$line) }
            if ($r.ExitCode -ne 0) { Write-Host 'Release Notes sync failed; continuing with recorded Git changes.' -ForegroundColor Yellow }
        }
        if (Test-Path -LiteralPath $PendingManifest) {
            $r = Invoke-Native -Program $Python -Arguments @($Indexer,'index','--no-release-sync','--paths-file',$PendingManifest) -WorkingDirectory $Base
            foreach ($line in $r.StdOut) { Write-Host ([string]$line) }; foreach ($line in $r.StdErr) { Write-Host ([string]$line) }
            if ($r.ExitCode -ne 0) { throw "Точечная индексация не прошла; манифест сохранён: $PendingManifest" }
            Remove-Item -LiteralPath $PendingManifest -Force
        }
    }
    if ($failures.Count -gt 0) { $exitCode = 2; Write-Host 'ОПЕРАЦИЯ ЗАВЕРШЕНА ЧАСТИЧНО:' -ForegroundColor Yellow; $failures | ForEach-Object { Write-Host " - $_" } }
    elseif ($DeepRepair -or $DeepRepairAll) { Write-Host 'ГЛУБОКОЕ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО.' -ForegroundColor Green }
    else { Write-Host 'ОБНОВЛЕНИЕ И ИНДЕКСАЦИЯ ЗАВЕРШЕНЫ.' -ForegroundColor Green }
}
catch { $exitCode = 1; Write-Host "ОШИБКА: $($_.Exception.Message)" -ForegroundColor Red }
finally {
    Stop-Transcript
    Write-Host "Подробный журнал: $Log"
    if (!$NoPause) { Read-Host 'Нажми Enter для завершения' }
}
exit $exitCode
