# Nostalgia RTX 0.2.2 — Windows x64

**English** · [Русский](README-RU.md)

Video upscaling with **NVIDIA RTX Video SDK 1.1 / RTX Video Super Resolution**, with a windowed interface and MP4 export through NVENC.

![Main window](docs/screenshots/main.png)

This is an experimental build. Start with the built-in hardware check and a short preview.

## Repository contents and downloads

This repository contains the source code. **The ready-to-run build is in [Releases](../../releases):** download `NostalgiaRTX-Windows-*.zip`, extract it and run `INSTALL.cmd`. The compiled files (`NostalgiaRTX.exe`, `bin/nostalgia_rtx.dll`) and `nvngx_vsr.dll` contain proprietary NVIDIA components, so they are distributed only inside the release archive, under the terms of the [EULA](EULA.md).

## First run

If version 0.2 or 0.2.1 is already installed, close the application and extract the new archive over the `NostalgiaRTX` folder, replacing files. The `.runtime` and `.downloads` folders are kept; you do not need to run `INSTALL.cmd` again. The version (0.2.2) is shown in the window title.

In 0.2.2 the result check shows expected and actual dimensions, FPS and frame count. A small rounding of the average FPS by the container is accepted only when the frame count and duration match; a real frame-rate change or missing frames is still an error. If the check fails, the finished MP4 is kept next to the result with an `_unverified_` mark, and the raw FFprobe data is saved as `input-probe.json` and `output-probe.json` in the session folder. Such an MP4 is not considered a confirmed result.

1. Extract the archive completely, for example to `C:\Apps\NostalgiaRTX`. Do not run the program from inside the ZIP and do not move the EXE away from its folder.
2. Open `INSTALL.cmd`. You will be asked to accept the EULA. The installer then downloads about **185 MB**: a local Python, Qt, NumPy, Pillow and FFmpeg. All downloads are pinned by version and SHA256 and are installed into the application folder. A system Python, Visual Studio, CUDA Toolkit or TensorRT is not needed to run the program. Internet access is required for the first installation, and about 2 GB of free space is needed.
3. After installation, run `NostalgiaRTX.exe`. Use `START.cmd` to see errors in a console.

The program does not modify the system Python and does not require administrator rights. The folder must be writable. After the dependencies are installed, video is processed locally; the application does not upload your source video to any server.

Requirements: Windows 10/11 x64, an NVIDIA GeForce RTX GPU and a compatible, up-to-date driver. SDK 1.1 supports RTX 50. The built-in check tells you whether VSR and NVENC are available on your PC.

## How to process a video

1. Click **"Проверить RTX и NVENC"** (Check RTX and NVENC): it runs a real VSR conversion of a test frame and a trial encode.
2. Choose a video or drag it into the window. Set a new MP4 name.
3. For the first try keep **×2, quality 3, H.264, CQ 18, RTX #0**. Colour is preserved; a black-and-white result is a separate option.
4. Set the start of the fragment in seconds and click **"Пробный фрагмент"** (Preview fragment). By default 3 seconds with audio are saved. The name contains `_preview_` and a random suffix.
5. Compare the first frame with the slider, then open the preview MP4: a still frame does not show flicker or errors in motion.
6. Click **"Увеличить видео"** (Upscale video) to process the video from the chosen mark to the end.

For 1920×1080, ×2 gives 3840×2160 (4K) and ×4 gives 7680×4320 (8K). For an output with a side longer than 4096 pixels the application selects H.265 automatically; you can change the codec manually. Before VSR is loaded, encoding is tested on one black frame at the **real output resolution**, with the selected codec and CQ. If the encoder refuses, VSR does not start and the message explains why. The RTX/NVENC check button also uses the output resolution of the selected video. The result is limited to 8192 pixels per side; NVENC capabilities additionally depend on the GPU and codec.

VSR quality: 1 — Low, 2 — Medium, 3 — High, 4 — Ultra. These are real SDK levels; non-AI scaling is never substituted silently. If VSR is unavailable, the operation fails with an error.

CQ controls compression loss: a lower number usually gives a larger file. For audio, AAC 192 kbit/s and copying the source tracks are available. If the source audio codec is incompatible with MP4, use AAC.

The interface language is currently Russian.

## Limitations of the first version

- Progressive SDR with square pixels is supported. The internal path is 8-bit BGRA/RGBA and the export is 8-bit YUV 4:2:0 BT.709. HDR and anamorphic/interlaced video are rejected. 10-bit support in the SDK itself does not mean it is available in this version of the program.
- Rotation by 90°, 180° and 270° is normalised by the decoder. For other angles, prepare the source first.
- FPS is stored as a fraction, for example `24000/1001`. Variable frame rate is converted to a constant average rate; there is no frame interpolation.
- All audio tracks are carried over; subtitles and chapters are not.
- The comparison shows the first processed frame of the chosen fragment. The original is enlarged with Lanczos to the same displayed size.
- Whole frames pass through VSR on the GPU. There is a copy through RAM between FFmpeg and the SDK; decoding and encoding do not form a fully GPU-resident pipeline.
- Progress and remaining time are approximate. Resuming after an interruption is not implemented.
- On cancel, child processes are stopped. If a worker does not respond for 8 seconds, the application tries to force-terminate its process tree. After such a stop, a `.nostalgia-render-*` folder may remain next to the result; you can delete it after closing the application.
- Names of finished files are never overwritten. Only a result whose dimensions, FPS, duration and audio presence were verified receives the final name. The source file is not modified.

Logs and comparison frames: `%LOCALAPPDATA%\NostalgiaRTX\sessions`. Click **"Открыть папку журнала"** (Open log folder) to open the folder of the current session. On an error, send `session.log` and, if present, `input-probe.json` and `output-probe.json`. If the interface does not open, see `startup.log` next to the EXE and run `START.cmd`.

## What was verified

- The Windows PE x64 EXE/DLL were compiled successfully; the module is linked with the real SDK 1.1 library.
- The interface was started and visually checked on Linux with Qt offscreen, including a small window size.
- Automated tests cover the FFmpeg stream, audio, fractional FPS, colour channel order, cancellation, overwrite protection, geometry and interface events.
- In the pipeline tests the GPU is replaced by a test backend.
- On the author's Windows PC with an NVIDIA RTX GPU, the PowerShell installer and a render with result verification completed successfully. Other hardware, drivers and long films have not been tested.

## Source and rebuilding

`nostalgia/gui.py` — interface; `pipeline.py` — video and audio; `backend.py` — DLL calls; `native/rtx_bridge.cpp` — Direct3D 11 / NGX VSR; `native/launcher.c` — launcher EXE.

To rebuild you need Visual Studio C++ x64 Build Tools and a separately obtained SDK 1.1. From an **x64 Native Tools Command Prompt**:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\Build-Windows.ps1 -Sdk "D:\SDK\RTX_Video_SDK_v1.1.0"
```

Runtime installation does not rebuild the program. The full SDK, its headers and developer tools are not included in the release archive or in this repository. After building, run `INSTALL.cmd` to download Python, Qt, NumPy, Pillow and FFmpeg.

Official sources:

- RTX Video: https://developer.nvidia.com/rtx-video-sdk/getting-started
- SDK 1.1: https://catalog.ngc.nvidia.com/orgs/nvidia/multimedia/models/dlpp/1.5/file-browser
- Python: https://www.python.org/downloads/windows/
- Qt for Python: https://doc.qt.io/qtforpython-6/
- FFmpeg build: https://github.com/GyanD/codexffmpeg/releases/tag/7.1.1

## License and notices

The original source code of this project is licensed under the [Apache License 2.0](LICENSE) (see also [NOTICE](NOTICE)). This license applies only to the author's original code. It does **not** cover the NVIDIA components (`nvngx_vsr.dll`, NVIDIA object code linked into `nostalgia_rtx.dll`, and any material provided by NVIDIA) or other third-party components, which keep their own licenses. The compiled release archive contains NVIDIA components and is governed by the [EULA](EULA.md) (bilingual; acceptance is required during installation and on first launch).

Component terms and attribution are in `licenses` and [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md). The application uses NVIDIA RTX Video SDK 1.1. NVIDIA and RTX are trademarks of NVIDIA Corporation. This is an independent application, not an NVIDIA or Topaz product, and is not endorsed by them.

Frame in the screenshot: a scene from a feature film, shown only to illustrate the program's interface.
