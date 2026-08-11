"""Backend Application Package Initialization."""

import os
import sys

# Windows DLL directory fix for PyTorch dynamic libraries (c10.dll)
if sys.platform == "win32":
    try:
        torch_lib = os.path.join(sys.prefix, "Lib", "site-packages", "torch", "lib")
        if os.path.exists(torch_lib):
            os.add_dll_directory(torch_lib)
    except Exception:
        pass
