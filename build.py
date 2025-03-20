import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["os", "sys", "json", "telnetlib", "psutil", "PyQt6", "logging"],
    "includes": ["PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets"],
    "include_files": [
        "vlc_history.json",
        "tracker.ico",
        "tracker.png",
        "trash.png"
    ]
}

# Remove the constants section as it's causing the error
# If you need constants, they should be defined as strings:
# "constants": ["PRODUCTION=True"]

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="VLC Tracker",
    version="1.0",
    description="VLC Media Player Progress Tracker",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "Tracker.py",
            base=base,
            icon="tracker.ico",
            target_name="VLCWatcher.exe"
        )
    ]
)