# VLC Tracker

A system tray application that tracks your VLC media player progress and manages your watching history.

## Features

- Tracks current playing media in VLC
- Shows watch progress with color coding
- Maintains a history of watched files
- Renames files with progress or [WATCHED] tag
- Minimizes to system tray
- Delete files directly from history

## Requirements

- Python 3.8+
- VLC Media Player with telnet interface enabled

### Enable VLC Telnet Interface

1. Open VLC
2. Go to Tools -> Preferences
3. Show settings: All
4. Interface -> Main interfaces -> Check 'Telnet'
5. Interface -> Main interfaces -> Lua -> Configure password if desired

## Installation

1. Clone this repository:
```bash
git clone https://github.com/hyperdarkmoon/VLCWatcher.git
cd Tracker
```

2. Install required packages:
```bash
pip install PyQt6
pip install psutil
pip install cx_Freeze
```

## Building the Executable

To create a standalone executable:

```bash
python build.py build
```

The executable will be created in the `build` directory.

## Usage

1. Run the executable
2. Play media in VLC
3. The app will track your progress
4. Files will be renamed with timestamps or [WATCHED] when closed
5. Access history in the History tab
6. Right-click tray icon to show/quit

## Configuration

Edit these constants in `Tracker.py`:

- `VLC_TELNET_HOST`: VLC telnet host (default: "localhost")
- `VLC_TELNET_PORT`: VLC telnet port (default: 4212)
- `VLC_TELNET_PASSWORD`: VLC telnet password (if configured)

## Notes

- Files are considered "watched" when:
  - Within last 90 seconds of end
  - Or completed 95% of total length
- History colors:
  - Green: Watched
  - Yellow: Past halfway
  - Red: Before halfway