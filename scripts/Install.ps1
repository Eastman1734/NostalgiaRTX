#Requires -Version 5.1
[CmdletBinding()]
param([switch]$AcceptEula)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$cache = Join-Path $root '.downloads'
$lock = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'dependencies.json') -Raw -Encoding UTF8 | ConvertFrom-Json

function Get-Asset {
    param($Asset)
    $path = Join-Path $cache $Asset.name
    if ((Test-Path -LiteralPath $path) -and (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -eq $Asset.sha256) {
        return $path
    }
    $temporary = $path + '.part'
    Write-Host ('Downloading ' + $Asset.name + ' ...')
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $Asset.url -OutFile $temporary
        if ((Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash -ne $Asset.sha256) {
            throw ('SHA256 verification failed: ' + $Asset.name)
        }
        Move-Item -LiteralPath $temporary -Destination $path -Force
    }
    finally { Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue }
    return $path
}

function Expand-Package {
    param([string]$Archive, [string]$Destination, [string]$Working)
    $zip = Join-Path $Working ([Guid]::NewGuid().ToString() + '.zip')
    Copy-Item -LiteralPath $Archive -Destination $zip
    try { Expand-Archive -LiteralPath $zip -DestinationPath $Destination -Force }
    finally { Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue }
}

try {
    if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
        throw 'Nostalgia RTX requires Windows 10/11 x64 and an NVIDIA RTX GPU.'
    }
    $eulaMark = Join-Path $root '.eula-accepted-1.0'
    if (-not (Test-Path -LiteralPath $eulaMark)) {
        $eula = Join-Path $root 'EULA.md'
        if (-not (Test-Path -LiteralPath $eula)) { throw 'EULA.md is missing. Extract the complete archive.' }
        Write-Host ''
        Write-Host 'Nostalgia RTX includes proprietary NVIDIA RTX Video SDK components.'
        Write-Host ('Read the license agreement first: ' + $eula)
        Write-Host ''
        if (-not $AcceptEula) {
            $answer = Read-Host 'Type ACCEPT to accept the EULA and continue, or anything else to cancel'
            if ($answer.Trim().ToUpperInvariant() -ne 'ACCEPT') { throw 'EULA not accepted. Installation cancelled.' }
        }
        [IO.File]::WriteAllText($eulaMark, ('EULA 1.0 accepted ' + (Get-Date).ToString('s') + "`r`n"), [Text.Encoding]::ASCII)
    }
    $null = New-Item -ItemType Directory -Path $cache -Force
    $working = Join-Path $root ('.setup-' + [Guid]::NewGuid().ToString())
    $null = New-Item -ItemType Directory -Path $working
    Write-Host 'Installing portable application components. No system Python or CUDA Toolkit is required.'
    $runtime = Join-Path $root '.runtime'
    if (-not (Test-Path -LiteralPath (Join-Path $runtime 'installed-0.2.0'))) {
        $stage = Join-Path $working 'runtime'
        Expand-Package (Get-Asset $lock.python) $stage $working
        $site = Join-Path $stage 'Lib\site-packages'
        $null = New-Item -ItemType Directory -Path $site -Force
        foreach ($asset in $lock.files) {
            Expand-Package (Get-Asset $asset) $site $working
        }
        [IO.File]::WriteAllText((Join-Path $stage 'python312._pth'),
            "python312.zip`r`n.`r`nLib\site-packages`r`n..`r`nimport site`r`n", [Text.Encoding]::ASCII)
        $python = Join-Path $stage 'python.exe'
        & $python (Join-Path $PSScriptRoot 'check_runtime.py')
        if ($LASTEXITCODE -ne 0) { throw 'Python/Qt import check failed.' }
        $backup = $runtime + '.old'
        if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup -Recurse -Force }
        if (Test-Path -LiteralPath $runtime) { Move-Item -LiteralPath $runtime -Destination $backup }
        try { Move-Item -LiteralPath $stage -Destination $runtime }
        catch {
            if ((Test-Path -LiteralPath $backup) -and -not (Test-Path -LiteralPath $runtime)) {
                Move-Item -LiteralPath $backup -Destination $runtime
            }
            throw
        }
        if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup -Recurse -Force }
        $null = New-Item -ItemType File -Path (Join-Path $runtime 'installed-0.2.0')
    }
    # App-local redistributable CRT files included in the official Qt wheel.
    $bin = Join-Path $root 'bin'
    $qt = Join-Path $runtime 'Lib\site-packages\PySide6'
    foreach ($name in @('vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll', 'msvcp140_1.dll',
                         'msvcp140_2.dll', 'msvcp140_codecvt_ids.dll', 'concrt140.dll')) {
        Copy-Item -LiteralPath (Join-Path $qt $name) -Destination $bin -Force
    }
    if (-not (Test-Path -LiteralPath (Join-Path $bin 'ffmpeg.exe')) -or -not (Test-Path -LiteralPath (Join-Path $bin 'ffprobe.exe'))) {
        $ff = Join-Path $working 'ffmpeg'
        Expand-Package (Get-Asset $lock.ffmpeg) $ff $working
        foreach ($name in @('ffmpeg.exe', 'ffprobe.exe')) {
            $matches = @(Get-ChildItem -LiteralPath $ff -Recurse -File -Filter $name)
            if ($matches.Count -ne 1) { throw ('Cannot locate ' + $name) }
            Copy-Item -LiteralPath $matches[0].FullName -Destination $bin -Force
        }
        $licenseFolder = Join-Path $root 'licenses\ffmpeg'
        $null = New-Item -ItemType Directory -Path $licenseFolder -Force
        Get-ChildItem -LiteralPath $ff -Recurse -File | Where-Object { $_.Name -match '^(LICENSE|COPYING|README)' } |
            ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $licenseFolder -Force }
    }
    & (Join-Path $runtime 'python.exe') (Join-Path $PSScriptRoot 'check_bridge.py')
    if ($LASTEXITCODE -ne 0) { throw 'The RTX bridge could not be loaded. See the error above.' }
    Write-Host 'Ready. Open NostalgiaRTX.exe, then click the RTX/NVENC check and render a short preview.' -ForegroundColor Green
}
catch {
    Write-Error -Message $_.Exception.Message -ErrorAction Continue
    exit 1
}
finally {
    if ($null -ne (Get-Variable -Name working -ErrorAction SilentlyContinue) -and (Test-Path -LiteralPath $working)) {
        Remove-Item -LiteralPath $working -Recurse -Force -ErrorAction SilentlyContinue
    }
}
