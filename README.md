# Nostalgia RTX

Увеличение видео через NVIDIA RTX Video Super Resolution (RTX Video SDK 1.1) с оконным интерфейсом и экспортом MP4 через NVENC. Windows 10/11 x64, видеокарта NVIDIA GeForce RTX.

Подробное описание, ограничения и инструкция: [README-RU.md](README-RU.md).

## Состав репозитория

Репозиторий содержит только исходный код. **Готовая к запуску сборка — в разделе [Releases](../../releases)**: скачайте `NostalgiaRTX-Windows-*.zip`, распакуйте и запустите `INSTALL.cmd`. Скомпилированные файлы (`NostalgiaRTX.exe`, `bin/nostalgia_rtx.dll`) и `nvngx_vsr.dll` содержат проприетарные компоненты NVIDIA, поэтому распространяются только в составе релиза на условиях [EULA](EULA.md).

## Сборка

1. Получите NVIDIA RTX Video SDK 1.1 на сайте NVIDIA и примите его лицензию.
2. В x64 Native Tools Command Prompt for Visual Studio выполните:
   `powershell -File scripts\Build-Windows.ps1 -Sdk <путь к SDK>`
3. Запустите `INSTALL.cmd` для загрузки Python, Qt, NumPy, Pillow и FFmpeg.

Условия использования: [EULA.md](EULA.md). Сторонние лицензии: [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
