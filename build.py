import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [
        "os", 
        "sys", 
        "json", 
        "telnetlib", 
        "psutil", 
        "PyQt6",
        "logging",
        "logging.handlers",
        "threading",
        "winreg",
        "datetime"
    ],
    "includes": [
        "PyQt6.QtCore", 
        "PyQt6.QtGui", 
        "PyQt6.QtWidgets",
        "PyQt6.sip"
    ],
    "include_files": [
        ("vlc_history.json", "vlc_history.json"),
        ("tracker.ico", "tracker.ico"),
        ("tracker.png", "tracker.png"),
        ("trash.png", "trash.png")
    ],
    "excludes": ["tkinter", "test", "unittest"],
    "optimize": 2,
    "include_msvcr": True  # Moved outside of build_exe dict
}

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