import sys
from cx_Freeze import setup, Executable
build_exe_options = {"packages": ["os"], "includes": ["pyvisa","pandas","eel","random","json","datetime","pytz","numpy","string","secrets","math", "numpy", "scipy.special", "scipy.optimize", "scipy.optimize"]}
base = None
if sys.platform == "win32":
    base = "Win32GUI"
setup( name = "test",
version = "0.1",
description = "application",
options = {"build_exe": build_exe_options},
executables = [Executable("build_v1.py", base=base)])