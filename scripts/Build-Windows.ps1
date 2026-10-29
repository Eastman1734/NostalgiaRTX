# Run from a Visual Studio x64 Native Tools command prompt.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Sdk)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) { throw 'Open x64 Native Tools Command Prompt for Visual Studio first.' }
$include = Join-Path $Sdk 'include'
$library = Join-Path $Sdk 'lib\Windows\x64\nvsdk_ngx_d.lib'
if (-not (Test-Path -LiteralPath $library)) { throw 'Select the root of NVIDIA RTX Video SDK 1.1.0.' }
Push-Location $root
try {
    & cl.exe /nologo /O2 /MD /EHsc /std:c++17 /LD /D_WIN32_WINNT=0x0A00 /I $include native\rtx_bridge.cpp $library `
        /link /OUT:bin\nostalgia_rtx.dll d3d11.lib dxgi.lib dxguid.lib user32.lib shell32.lib advapi32.lib
    if ($LASTEXITCODE -ne 0) { throw 'RTX bridge build failed.' }
    & cl.exe /nologo /O2 /MT native\launcher.c /link /SUBSYSTEM:WINDOWS /OUT:NostalgiaRTX.exe user32.lib shell32.lib
    if ($LASTEXITCODE -ne 0) { throw 'Launcher build failed.' }
    Copy-Item -LiteralPath (Join-Path $Sdk 'bin\Windows\x64\rel\nvngx_vsr.dll') -Destination bin -Force
    Copy-Item -LiteralPath (Join-Path $Sdk 'NVIDIA_RTX_Video_SDK_License.pdf') -Destination licenses -Force
    Write-Host 'Windows binaries rebuilt successfully.'
}
finally { Pop-Location }
