import ctypes
import os
from pathlib import Path

folder = Path(__file__).resolve().parents[1] / "bin"
directory = os.add_dll_directory(str(folder))
library = ctypes.CDLL(str(folder / "nostalgia_rtx.dll"))
library.nr_abi_version.restype = ctypes.c_uint
if library.nr_abi_version() != 1:
    raise RuntimeError("RTX bridge ABI mismatch")
print("RTX bridge: loaded")
