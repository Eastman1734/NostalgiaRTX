# Third-party components

This software contains source code provided by NVIDIA Corporation.

This application uses the NVIDIA RTX Video SDK 1.1 (RTX Video Super Resolution). NVIDIA and RTX are trademarks and/or registered trademarks of NVIDIA Corporation in the United States and other countries. This is an independent application and is not sponsored or endorsed by NVIDIA.

Use of this application is governed by `EULA.md`.

The included NVIDIA `nvngx_vsr.dll` and NVIDIA object code linked into
`nostalgia_rtx.dll` are proprietary NVIDIA RTX Video SDK 1.1 components. They
remain subject to the NVIDIA RTX SDKs License and supplement, included as
`licenses/NVIDIA_RTX_Video_SDK_License.pdf`. They are incorporated into this
video-processing application and are not licensed as standalone SDK products.
SDK headers, SDK development libraries, samples, and documentation are not
redistributed with this application. Obtain the SDK from NVIDIA to rebuild.

Installed runtime components retain their own licenses:

- Python 3.12: Python Software Foundation license; `LICENSE.txt` in `.runtime`.
- PySide6/Qt for Python: LGPLv3/GPLv3/commercial, as applicable. The official
  wheels retain their license notices in `.runtime/Lib/site-packages`.
  Qt is dynamically linked and its DLLs remain replaceable. Corresponding
  upstream source: https://download.qt.io/official_releases/QtForPython/pyside6/6.8.3/
  and https://download.qt.io/official_releases/qt/6.8/6.8.3/ .
- Shiboken6: upstream Qt for Python license notices in its installed wheel.
- NumPy: BSD-3-Clause and bundled dependency notices in its installed wheel.
- Pillow: HPND and bundled dependency notices in its installed wheel.
- FFmpeg 7.1.1 essentials build by Gyan Doshi: GPLv3, with its COPYING/LICENSE
  files retained by the installer. Official build/source information:
  https://www.gyan.dev/ffmpeg/builds/ and https://ffmpeg.org/releases/ffmpeg-7.1.1.tar.xz .
- Microsoft runtime DLLs distributed in the official Python/Qt wheels retain
  their original redistribution terms and notices.

Original application source can be modified for your own use. Third-party
licenses are not replaced or overridden by the application's source terms.
