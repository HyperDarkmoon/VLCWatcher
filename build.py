import sys
from cx_Freeze import setup, Executable

build_exe_options = {
   "packages": [
        "os", "sys", "json", "telnetlib", "psutil", "PyQt6",
        "logging", "threading", "winreg", "datetime"
    ],
    "includes": [
        "PyQt6.QtCore", 
        "PyQt6.QtGui", 
        "PyQt6.QtWidgets",
        "PyQt6.sip"  # Required for PyQt6 signals
    ],
    "include_files": [
        "vlc_history.json",
        "tracker.ico",
        "tracker.png",
        "trash.png"
    ],
    "excludes": ["tkinter", "test", "unittest"],  # Reduce executable size
    "optimize": 2  # Enable optimization
}

# Remove the constants section as it's causing the error
# If you need constants, they should be defined as strings:
# "constants": ["PRODUCTION=True"]

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="VLC Watcher",
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