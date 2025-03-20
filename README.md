# VLC Tracker

A system tray application that tracks your VLC media player progress and manages your watching history.

## Features

- Tracks current playing media in VLC
- Shows watch progress with color coding:
  - Green: Watched
  - Yellow: Past halfway point
  - Red: Before halfway point
- Maintains a history of watched files
- Renames files with progress or [WATCHED] tag
- Minimizes to system tray
- Delete files directly from history
- Automatic crash logging and debugging

## Requirements

- Python 3.8+
- VLC Media Player with telnet interface enabled
- Required Python packages:
  ```bash
  pip install PyQt6
  pip install psutil
  pip install cx_Freeze
  pip install appdirs
  ```

## Building from Source

1. Ensure all required files are present:
   - `tracker.ico` - Application icon
   - `tracker.png` - Tray icon (16x16 or 32x32)
   - `trash.png` - Delete button icon

2. Build the executable:
   ```bash
   python build.py build
   ```

3. The executable will be created in `build/exe.win-amd64-3.10/` directory

## VLC Configuration

1. Open VLC Media Player
2. Go to Tools > Preferences
3. Show settings: All
4. Interface > Main interfaces > Check 'Telnet'
5. Interface > Main interfaces > Lua:
   - Set telnet password if desired (default: none)
   - Default port is 4212

## Application Data

- All application data is stored in: `%APPDATA%\VLCTracker\`
- Files stored:
  - `vlctracker.log` - Log files with rotation (max 4MB total)
  - `vlc_history.json` - Watch history

## Debug Logs

- Logs are stored in `%APPDATA%\VLCTracker\vlctracker.log`
- Log files rotate after reaching 1MB
- Keeps last 3 backup files
- Only errors and warnings are logged by default
- Full debug logs are captured during crashes

## Startup Configuration

- Can be configured to run on Windows startup
- Settings are accessible from the Settings tab
- Startup configuration only works with the compiled .exe version

## Notes 
- Files are considered "watched" when:
  - Within last 90 seconds of end
  - Or completed 95% of total length
- History colors:
  - Green: Watched
  - Yellow: Past halfway
  - Red: Before halfway