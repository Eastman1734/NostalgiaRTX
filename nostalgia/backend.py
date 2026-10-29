from __future__ import annotations
import ctypes as C
import os
from pathlib import Path
import numpy as np


class RTXVideo:
    """Call the actual NGX VSR bridge. No silent resize or CPU fallback."""
    def __init__(self, width: int, height: int, scale: int, quality: int, gpu: int, root: Path, cache: Path):
        if os.name != "nt":
            raise RuntimeError("RTX Video SDK работает только в этой Windows-сборке")
        folder = root / "bin"
        self._directory = os.add_dll_directory(str(folder))
        try:
            self.lib = C.CDLL(str(folder / "nostalgia_rtx.dll"))
        except OSError as error:
            self._directory.close()
            raise RuntimeError("Не удалось загрузить движок RTX Video. Запустите установку или проверьте bin/nostalgia_rtx.dll.") from error
        lib = self.lib
        lib.nr_abi_version.restype = C.c_uint
        if lib.nr_abi_version() != 1:
            raise RuntimeError("Версия интерфейса движка не совпадает с приложением")
        lib.nr_error.restype = C.c_char_p
        lib.nr_create.argtypes = [C.c_uint]*5 + [C.c_wchar_p]
        lib.nr_create.restype = C.c_void_p
        lib.nr_destroy.argtypes = [C.c_void_p]
        lib.nr_process.argtypes = [C.c_void_p, C.c_void_p, C.c_ulonglong, C.c_void_p, C.c_ulonglong]
        lib.nr_process.restype = C.c_int
        cache.mkdir(parents=True, exist_ok=True)
        self.handle = lib.nr_create(width, height, scale, quality, gpu, str(cache))
        if not self.handle:
            message = self.error()
            self._directory.close()
            raise RuntimeError(message)
        self.shape = (height, width, 4)
        self.output = np.empty((height*scale, width*scale, 4), dtype=np.uint8)

    def error(self):
        return self.lib.nr_error().decode("utf-8", "replace") or "Ошибка NVIDIA RTX Video SDK"

    def process(self, bgra: np.ndarray) -> np.ndarray:
        if bgra.shape != self.shape or bgra.dtype != np.uint8 or not bgra.flags.c_contiguous:
            raise ValueError("Ожидался непрерывный кадр BGRA uint8")
        if not self.lib.nr_process(self.handle, bgra.ctypes.data, bgra.nbytes,
                                  self.output.ctypes.data, self.output.nbytes):
            raise RuntimeError(self.error())
        return self.output

    def close(self):
        if getattr(self, "handle", None):
            self.lib.nr_destroy(self.handle)
            self.handle = None
        if getattr(self, "_directory", None):
            self._directory.close()
            self._directory = None
