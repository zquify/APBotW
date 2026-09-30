
$ErrorActionPreference = "Stop"

$ProjectDir = "C:\Projects\BotWArchipelago"
$ArchivePath = Join-Path $ProjectDir "botw.apworld"
$ZipPath = Join-Path $ProjectDir "botw.zip"
$CustomWorldsDir = "C:\ProgramData\Archipelago\custom_worlds"
$InstalledPath = Join-Path $CustomWorldsDir "botw.apworld"

$StageRoot = Join-Path $env:TEMP "BotW_APWorld_Build"
$PackageDir = Join-Path $StageRoot "botw"

try {
    Write-Host ""
    Write-Host "=== BotW Archipelago World Updater ===" -ForegroundColor Cyan
    Write-Host ""

    # Verify the Manual repository files.
    $RequiredFiles = @(
        "__init__.py",
        "Game.py",
        "Data.py",
        "Items.py",
        "Locations.py",
        "Regions.py",
        "Rules.py",
        "data\game.json"
    )

    foreach ($File in $RequiredFiles) {
        if (-not (Test-Path (Join-Path $ProjectDir $File))) {
            throw "Required repository file not found: $ProjectDir\$File"
        }
    }

    # Create a clean staging directory.
    Remove-Item $StageRoot -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $PackageDir -Force |
        Out-Null

    # Copy the repository into one package directory.
    # Exclude Git metadata, editor settings, caches, and old archives.
    & robocopy $ProjectDir $PackageDir /E `
        /XD ".git" ".vscode" "__pycache__" `
        /XF "*.apworld" "*.zip" "update_apworld.ps1" `
        /NFL /NDL /NJH /NJS /NP

    $RobocopyExitCode = $LASTEXITCODE
    if ($RobocopyExitCode -ge 8) {
        throw "Failed to stage repository files. Robocopy exit code: $RobocopyExitCode"
    }

    if (-not (Test-Path (Join-Path $PackageDir "__init__.py"))) {
        throw "Staged package is missing __init__.py."
    }

    # Ensure the custom worlds directory exists.
    if (-not (Test-Path $CustomWorldsDir)) {
        New-Item -ItemType Directory -Path $CustomWorldsDir -Force |
            Out-Null
    }

    Remove-Item $ArchivePath, $ZipPath -Force -ErrorAction SilentlyContinue

    # Archive the botw directory itself, preserving the botw/ prefix.
    Compress-Archive -Path $PackageDir -DestinationPath $ZipPath -Force
    Move-Item $ZipPath $ArchivePath -Force

    # Verify the APWorld archive structure.
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $Zip = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)

    try {
        $Entries = @(
            $Zip.Entries | ForEach-Object {
                $_.FullName.Replace("\", "/")
            }
        )

        if ($Entries -notcontains "botw/__init__.py") {
            throw "Archive is missing botw/__init__.py."
        }

        if ($Entries -notcontains "botw/Game.py") {
            throw "Archive is missing botw/Game.py."
        }

        if ($Entries -notcontains "botw/data/game.json") {
            throw "Archive is missing botw/data/game.json."
        }

        $TopLevelEntries = @(
            $Entries |
                Where-Object { $_ -and $_ -notmatch "^botw/" }
        )

        if ($TopLevelEntries.Count -gt 0) {
            throw "Unexpected files outside the botw directory: $($TopLevelEntries -join ', ')"
        }
    }
    finally {
        $Zip.Dispose()
    }

    # Install the verified archive.
    Copy-Item $ArchivePath $InstalledPath -Force

    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "Built:     $ArchivePath"
    Write-Host "Installed: $InstalledPath"
    Write-Host "Archive contains one top-level botw/ directory."
    Write-Host ""
    Write-Host "Restart Archipelago before testing changes."
}
catch {
    Write-Host ""
    Write-Host "UPDATE FAILED:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
finally {
    Remove-Item $StageRoot -Recurse -Force -ErrorAction SilentlyContinue
}