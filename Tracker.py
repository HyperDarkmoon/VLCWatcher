import sys
import json
import os
import telnetlib
import psutil
import threading
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QThread, QMetaObject, Qt, pyqtSlot
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                           QListWidget, QTabWidget, QHBoxLayout, QPushButton,
                           QListWidgetItem, QMessageBox, QSystemTrayIcon, QMenu)
from PyQt6.QtGui import QIcon

import os.path
ICON_FILE = "tracker.ico"
TRAY_ICON_FILE = "tracker.png"  # 16x16 or 32x32 PNG recommended for tray

HISTORY_FILE = "vlc_history.json"
VLC_TELNET_HOST = "localhost"
VLC_TELNET_PORT = 4212
VLC_TELNET_PASSWORD = ""  # Set this if needed, else leave empty

def rename_media_file(original_path, is_watched, timestamp=None):
    """Helper function to rename the media file"""
    try:
        # Remove file:/// prefix if present
        if original_path.startswith("file:///"):
            original_path = original_path[8:]  # Remove "file:///"
        
        # Convert path separators to system format
        original_path = os.path.normpath(original_path)
        
        directory = os.path.dirname(original_path)
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        
        # Remove any existing [WATCHED] or [MM:SS] prefix
        if name.startswith('['):
            name = name[name.find(']') + 1:].strip()
        
        # Create new filename
        prefix = '[WATCHED]' if is_watched else f'[{timestamp}]'
        new_filename = f"{prefix} {name}{ext}"
        new_path = os.path.join(directory, new_filename)
        
        
        # Rename the file
        if os.path.exists(original_path):
            os.rename(original_path, new_path)
            return new_path
        else:
            return original_path
            
    except Exception as e:
        return original_path

def format_time(seconds):
    """Convert seconds into a MM:SS string."""
    minutes = seconds // 60
    sec = seconds % 60
    return f"{minutes}:{sec:02d}"

def format_time_filename(seconds):
    """Convert seconds into a MM-SS string safe for filenames."""
    minutes = seconds // 60
    sec = seconds % 60
    return f"{minutes:02d}-{sec:02d}"

def is_vlc_running():
    """Check if VLC process is running."""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and "vlc" in proc.info['name'].lower():
            return True
    return False

def get_vlc_status_telnet(host=VLC_TELNET_HOST, port=VLC_TELNET_PORT, password=VLC_TELNET_PASSWORD):
    """
    Connect to VLC's telnet interface, send commands and parse the output.
    Returns a dictionary with 'file', 'time', 'length', and 'state'
    if media is loaded; otherwise, returns None.
    """
    try:
        tn = telnetlib.Telnet(host, port, timeout=3)
        
        # Read until we see a prompt; handle password if needed
        prompt = tn.read_until(b"Password: ", timeout=1)
        if b"Password:" in prompt:
            tn.write((password + "\n").encode('utf-8'))
        
        # Send 'status' command to fetch state and file info
        tn.write(b"status\n")
        status_result = tn.read_until(b">", timeout=2)
        
        # Decode status output and parse lines
        lines = status_result.decode('utf-8', errors='ignore').splitlines()
        
        file_name = None
        state = None
        for line in lines:
            if line.startswith("( state "):
                state = line[len("( state "):].rstrip(" )").strip()
            elif line.startswith("( new input: "):
                file_name = line[len("( new input: "):].rstrip(" )").strip()
            elif line.startswith("input: "):
                file_name = line[len("input: "):].strip()
        
        # Get current playback time
        tn.write(b"get_time\n")
        time_result = tn.read_until(b">", timeout=2)
        
        # Get total length
        tn.write(b"get_length\n")
        length_result = tn.read_until(b">", timeout=2)
        
        tn.close()
        
        try:
            time_line = time_result.decode('utf-8', errors='ignore').strip().splitlines()[0]
            current_time = int(time_line)
            
            length_line = length_result.decode('utf-8', errors='ignore').strip().splitlines()[0]
            total_length = int(length_line)
        except Exception as e:
            current_time = 0
            total_length = 0
        
        # If state is playing or paused and file info is present, return status.
        if state in ("playing", "paused") and file_name:
            return {
                "file": file_name,
                "time": current_time,
                "length": total_length,
                "state": state
            }
        else:
            return None
    except Exception as e:
        return None

class VLCStatusWorker(QObject):
    status_ready = pyqtSignal(dict)
    vlc_not_running = pyqtSignal()

    @pyqtSlot()  # Add this decorator to mark it as a slot
    def check_status(self):
        if not is_vlc_running():
            self.vlc_not_running.emit()
            return
        
        status = get_vlc_status_telnet()
        if status:
            self.status_ready.emit(status)
        else:
            self.status_ready.emit({})

class VLCTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VLC Tracker")
        self.setGeometry(100, 100, 800, 500)

        if os.path.exists(ICON_FILE):
            self.setWindowIcon(QIcon(ICON_FILE))

        # Initialize status tracking variables
        self.current_file = None
        self.current_time = 0
        self.current_state = None
        self.vlc_running = False
        
        # Create worker and move to thread properly
        self.worker = VLCStatusWorker()
        self.worker_thread = QThread()  # Create the thread first
        self.worker.moveToThread(self.worker_thread)  # Move worker to thread
        
        # Connect signals
        self.worker.status_ready.connect(self.on_status_ready, Qt.ConnectionType.QueuedConnection)
        self.worker.vlc_not_running.connect(self.on_vlc_not_running, Qt.ConnectionType.QueuedConnection)
        
        # Start the thread
        self.worker_thread.start()
        
        # Setup UI
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        # Now Playing Tab
        self.now_playing_tab = QWidget()
        np_layout = QVBoxLayout()
        self.now_playing_label = QLabel("No video playing.")
        np_layout.addWidget(self.now_playing_label)
        self.now_playing_tab.setLayout(np_layout)
        
        # History Tab
        self.history_tab = QWidget()
        history_layout = QVBoxLayout()
        self.history_list = QListWidget()
        history_layout.addWidget(self.history_list)
        self.history_tab.setLayout(history_layout)
        
        self.tabs.addTab(self.now_playing_tab, "Now Playing")
        self.tabs.addTab(self.history_tab, "History")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # Create system tray
        self.create_tray_icon()
        
        # Setup timer for status checks
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start_status_check)
        self.timer.start(2000)
        
        self.load_history()

    def start_status_check(self):
        # Use QMetaObject.invokeMethod for thread-safe invocation
        QMetaObject.invokeMethod(self.worker, "check_status", Qt.ConnectionType.QueuedConnection)

    def on_status_ready(self, status):
        self.vlc_running = True
        self.current_file = status["file"]
        self.current_time = status["time"]
        self.current_state = status["state"]
        self.last_total_length = status["length"]
        display_file = os.path.basename(self.current_file) if self.current_file else "Unknown"
        state_str = "Paused" if self.current_state == "paused" else "Playing"
        self.now_playing_label.setText(
            f"{state_str}: {display_file} - {format_time(self.current_time)}"
        )

    def on_vlc_not_running(self):
   
        if self.vlc_running and self.current_file and self.current_time > 0:
            is_watched = False
            if hasattr(self, 'last_total_length') and self.last_total_length > 0:
                time_remaining = self.last_total_length - self.current_time
                is_watched = (time_remaining <= 90 or 
                            (self.current_time / self.last_total_length) > 0.95)
            
            new_path = rename_media_file(
                self.current_file, 
                is_watched, 
                format_time_filename(self.current_time)
            )
            
            self.add_to_history(new_path, format_time(self.current_time), is_watched)
            self.current_file = None
            self.current_time = 0
            self.current_state = None
        
        self.vlc_running = False
        self.now_playing_label.setText("No video playing.")

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_file = TRAY_ICON_FILE if os.path.exists(TRAY_ICON_FILE) else ICON_FILE
        self.tray_icon.setIcon(QIcon(icon_file))

        # Create tray menu
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show()
            self.raise_()
            self.activateWindow()
        
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "VLC Tracker",
            "Application minimized to tray",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
        
    def quit_application(self):
        self.tray_icon.hide()
        QApplication.quit()

    def update_status(self):
    # Check if VLC is running before attempting connection
        if not is_vlc_running():
            if self.vlc_running and self.current_file and self.current_time > 0:
                # Calculate if video was watched based on last known values
                is_watched = False
                if hasattr(self, 'last_total_length') and self.last_total_length > 0:
                    time_remaining = self.last_total_length - self.current_time
                    # Consider it watched if within 90 seconds of the end OR 95% complete
                    is_watched = (time_remaining <= 90 or 
                                (self.current_time / self.last_total_length) > 0.95)
                
                # Rename the actual file
                new_path = rename_media_file(
                    self.current_file, 
                    is_watched, 
                    format_time_filename(self.current_time)
                )
                
                self.add_to_history(new_path, format_time(self.current_time), is_watched)
                self.current_file = None
                self.current_time = 0
                self.current_state = None
            self.vlc_running = False
            self.now_playing_label.setText("No video playing.")
            return
        
        # Fetch status via telnet
        status = get_vlc_status_telnet()
        if status:
            self.vlc_running = True
            self.current_file = status["file"]
            self.current_time = status["time"]
            self.current_state = status["state"]
            self.last_total_length = status["length"]  # Store length for later use
            display_file = os.path.basename(self.current_file) if self.current_file else "Unknown"
            state_str = "Paused" if self.current_state == "paused" else "Playing"
            self.now_playing_label.setText(
                f"{state_str}: {display_file} - {format_time(self.current_time)}"
            )
        
    def load_history(self):
        self.history_list.clear()
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
                for entry in history:
                    # Create widget for the entry
                    item_widget = QWidget()
                    layout = QHBoxLayout()
                    
                    # Create label for file info
                    label = QLabel(f"{os.path.basename(entry['file'])} - {entry['timestamp']}")
                    label.setStyleSheet("color: black;")
                    layout.addWidget(label)
                    
                    # Create delete button
                    delete_btn = QPushButton()
                    delete_btn.setFixedSize(24, 24)
                    delete_btn.setIcon(QIcon("trash.png"))
                    delete_btn.setToolTip("Delete from history")
                    delete_btn.setProperty("file_path", entry['file'])
                    delete_btn.clicked.connect(self.delete_history_entry)
                    layout.addWidget(delete_btn)
                    layout.addStretch()
                    
                    item_widget.setLayout(layout)
                    
                    # Set background color based on status
                    if entry.get('watched', False):
                        item_widget.setStyleSheet("QWidget { background-color: #90EE90; } QLabel { color: black; }")  # Green
                    else:
                        timestamp = entry['timestamp']
                        if timestamp != "[WATCHED]":
                            try:
                                minutes, seconds = map(int, timestamp.split(':'))
                                current_time = minutes * 60 + seconds
                                total_length = entry.get('length', 0)
                                
                                if total_length > 0:
                                    progress = current_time / total_length
                                    if progress > 0.5:
                                        item_widget.setStyleSheet("QWidget { background-color: #FFD700; } QLabel { color: black; }")  # Yellow
                                    else:
                                        item_widget.setStyleSheet("QWidget { background-color: #FFB6C1; } QLabel { color: black; }")  # Light red
                                else:
                                    item_widget.setStyleSheet("QWidget { background-color: #FFB6C1; } QLabel { color: black; }")  # Light red
                            except:
                                item_widget.setStyleSheet("QWidget { background-color: #FFB6C1; } QLabel { color: black; }")  # Light red
                        else:
                            item_widget.setStyleSheet("QWidget { background-color: #90EE90; } QLabel { color: black; }")  # Green
                    
                    # Create and add list widget item
                    item = QListWidgetItem()
                    item.setSizeHint(item_widget.sizeHint())
                    self.history_list.addItem(item)
                    self.history_list.setItemWidget(item, item_widget)
                    
        except (FileNotFoundError, json.JSONDecodeError):
            with open(HISTORY_FILE, "w") as f:
                json.dump([], f)
    
    def delete_history_entry(self):
        # Get the sender button
        button = self.sender()
        file_path = button.property("file_path")
        
        try:
            # Show confirmation dialog
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("Delete File")
            msg.setInformativeText(f"Do you want to delete this file?\n{os.path.basename(file_path)}")
            msg.setWindowTitle("Confirm Deletion")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                # Delete the actual file if it exists
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Could not delete file:\n{str(e)}")
                        return
                
                # Remove from history
                with open(HISTORY_FILE, "r") as f:
                    history = json.load(f)
                
                # Remove the entry with matching file path
                history = [entry for entry in history if entry['file'] != file_path]
                
                with open(HISTORY_FILE, "w") as f:
                    json.dump(history, f, indent=4)
                    
                # Refresh the history display
                self.load_history()
                
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def add_to_history(self, file, timestamp, is_watched=False):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []
        
        # Look for existing entry with the same base filename (ignoring timestamps)
        file_found = False
        base_name = os.path.basename(file)
        if base_name.startswith('['):
            base_name = base_name[base_name.find(']') + 1:].strip()
        
        for entry in history:
            entry_base = os.path.basename(entry['file'])
            if entry_base.startswith('['):
                entry_base = entry_base[entry_base.find(']') + 1:].strip()
                
            if entry_base == base_name:
                entry['file'] = file  # Update with new path
                entry['timestamp'] = "[WATCHED]" if is_watched else timestamp
                entry['watched'] = is_watched
                file_found = True
                break
        
        if not file_found:
            history.append({
                "file": file,
                "timestamp": "[WATCHED]" if is_watched else timestamp,
                "watched": is_watched,
                "length": self.last_total_length if hasattr(self, 'last_total_length') else 0
            })
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
        self.load_history()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tracker = VLCTracker()
    tracker.show()
    sys.exit(app.exec())
