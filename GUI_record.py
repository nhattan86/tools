import sys
import os
import time
import datetime
import subprocess
import tempfile
import shutil  # For file copying

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QComboBox, QSpinBox, QCheckBox, QFileDialog, QMessageBox,
    QGroupBox, QSlider, QMenu, QAction, QDialog, QTabWidget, QLineEdit,
    QFormLayout, QRadioButton, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QColor, QImage, QPalette

# Screen recording libraries
import numpy as np
import cv2
import pyautogui
import sounddevice as sd
from scipy.io.wavfile import write as write_audio


class RecordingThread(QThread):
    """Thread to handle screen recording without blocking the GUI"""
    timer_updated = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    recording_complete = pyqtSignal(str)
    frame_captured = pyqtSignal(QPixmap)

    def __init__(self, record_full_screen=True, region=None,
                 record_system_audio=False, record_microphone=False,
                 frame_rate=30, quality=75, output_format="mp4",
                 output_file=None, parent=None):
        super().__init__(parent)

        # Recording parameters
        self.record_full_screen = record_full_screen
        self.region = region  # (x1, y1, x2, y2) tuple
        self.record_system_audio = record_system_audio
        self.record_microphone = record_microphone
        self.frame_rate = frame_rate
        self.quality = quality
        self.output_format = output_format
        self.output_file = output_file

        # State variables
        self.is_recording = False
        self.is_paused = False
        self.elapsed_time = 0

        # Data storage
        self.audio_data = []

        # Create temporary directory for intermediate files
        self.temp_dir = tempfile.mkdtemp()

    def run(self):
        """Main thread execution - starts recording process"""
        try:
            self.is_recording = True
            self.record_screen()
        except Exception as e:
            self.error_occurred.emit(f"Recording error: {str(e)}")

    def record_screen(self):
        """Main recording function that captures screen and optionally audio"""
        # Determine recording region
        if self.record_full_screen:
            screen_size = pyautogui.size()
            self.region = (0, 0, screen_size.width, screen_size.height)
        else:
            if not self.region:
                self.error_occurred.emit("No recording region specified")
                return

        # Calculate dimensions
        width = self.region[2] - self.region[0]
        height = self.region[3] - self.region[1]

        # Generate output filename if not provided
        if self.output_file is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file = f"screen_recording_{timestamp}.{self.output_format}"

        # Setup video writer
        temp_video_file = os.path.join(self.temp_dir, "temp_video.avi")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video_writer = cv2.VideoWriter(temp_video_file, fourcc, self.frame_rate, (width, height))

        # Setup audio recording if needed
        audio_sample_rate = 44100  # Standard audio sample rate
        if self.record_microphone:
            try:
                audio_stream = sd.InputStream(samplerate=audio_sample_rate, channels=2) # Stereo channels
                audio_stream.start()
            except Exception as e:
                self.error_occurred.emit(f"Could not initialize microphone: {str(e)}")
                self.record_microphone = False

        # Setup timer for elapsed time updates
        timer = QTimer()
        timer.setInterval(1000)  # Update every second
        timer.timeout.connect(self.update_timer)
        timer.start()

        # Recording loop timing setup
        start_time = time.time()
        frame_interval = 1.0 / self.frame_rate
        next_frame_time = start_time

        # Main recording loop
        while self.is_recording:
            current_time = time.time()

            if not self.is_paused and current_time >= next_frame_time:
                try:
                    # Capture screen
                    screenshot = pyautogui.screenshot(region=self.region)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                    # Save to video
                    video_writer.write(frame)

                    # Emit frame for preview (downsized version)
                    preview_frame = cv2.resize(frame, (320, 240))
                    preview_frame = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
                    h, w, c = preview_frame.shape
                    qimg = QPixmap.fromImage(QImage(preview_frame.data, w, h, w * c, QImage.Format_RGB888))
                    self.frame_captured.emit(qimg)

                    # Capture audio if needed
                    if self.record_microphone and not self.is_paused:
                        audio_data, overflowed = audio_stream.read(audio_sample_rate // self.frame_rate)
                        if overflowed:
                            print("Audio buffer overflowed") # Optional: Handle overflow more robustly
                        self.audio_data.append(audio_data)

                    next_frame_time += frame_interval
                except Exception as e:
                    self.error_occurred.emit(f"Frame capture error: {str(e)}")
                    break

            # Sleep to avoid high CPU usage
            time.sleep(0.001)

        # Clean up resources
        timer.stop()
        video_writer.release()

        if self.record_microphone:
            audio_stream.stop()
            audio_stream.close()

            # Save audio to file if we have any data
            if self.audio_data:
                try:
                    temp_audio_file = os.path.join(self.temp_dir, "temp_audio.wav")
                    audio_data_combined = np.concatenate(self.audio_data)
                    write_audio(temp_audio_file, audio_sample_rate, audio_data_combined)

                    # Merge audio and video
                    self.merge_audio_video(temp_video_file, temp_audio_file, self.output_file)
                except Exception as e:
                    self.error_occurred.emit(f"Audio processing error: {str(e)}")
                    # Fallback to just the video
                    os.rename(temp_video_file, self.output_file)
            else:
                # Just rename the video file if no audio
                os.rename(temp_video_file, self.output_file)
        else:
            # Just rename the video file if no audio recording was requested
            os.rename(temp_video_file, self.output_file)

        # Signal that recording is complete
        self.recording_complete.emit(self.output_file)

    def merge_audio_video(self, video_file, audio_file, output_file):
        """Merge audio and video files using ffmpeg"""
        try:
            # Use ffmpeg to merge audio and video
            cmd = [
                "ffmpeg", "-i", video_file, "-i", audio_file,
                "-c:v", "copy", "-c:a", "aac", "-strict", "experimental", # Using AAC for audio, adjust as needed
                output_file
            ]
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
            self.error_occurred.emit("FFmpeg not found. Please ensure FFmpeg is installed and in your PATH.")
            # Fallback to just video, or handle differently
            os.rename(video_file, output_file + ".noaudio.mp4") # Save video even if audio merge fails, with a different extension
        except subprocess.CalledProcessError as e:
            self.error_occurred.emit(f"Error merging audio and video with FFmpeg: {str(e)}")
            # Fallback to just the video
            os.rename(video_file, output_file + ".noaudio.mp4")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error during audio/video merge: {str(e)}")
            os.rename(video_file, output_file + ".noaudio.mp4")


    def update_timer(self):
        """Update the elapsed time counter and emit signal"""
        if not self.is_paused:
            self.elapsed_time += 1
            self.timer_updated.emit(self.elapsed_time)

    def pause(self):
        """Pause the recording"""
        self.is_paused = True

    def resume(self):
        """Resume a paused recording"""
        self.is_paused = False

    def stop(self):
        """Stop the recording"""
        self.is_recording = False
        self.is_paused = False # Ensure paused state is also reset when stopped


class RegionSelectorDialog(QDialog):
    """Dialog for selecting a screen region to record"""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint)
        self.setWindowTitle("Select Region")
        self.setWindowOpacity(0.7) # Increased opacity for better visibility
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(50, 100, 255, 150); /* Semi-transparent blue overlay */
            }
            QLabel {
                background-color: transparent;
                color: white;
                font-size: 20px;
            }
        """)

        # Enable mouse tracking for drawing selection rectangle
        self.setMouseTracking(True)

        # Selection state variables
        self.selected_region = None
        self.start_pos = None
        self.current_pos = None
        self.is_selecting = False

        # Cover the entire screen
        screen_size = QApplication.desktop().screenGeometry()
        self.setGeometry(0, 0, screen_size.width(), screen_size.height())

        # Instructions label
        self.label = QLabel("Click and drag to select a region. Press ESC to cancel.", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(0, 50, screen_size.width(), 50)

    def mousePressEvent(self, event):
        """Handle mouse press to start selection"""
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.current_pos = event.pos()
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse movement to update selection rectangle"""
        if self.is_selecting:
            self.current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to finalize selection"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            if self.start_pos and self.current_pos:
                x1 = min(self.start_pos.x(), self.current_pos.x())
                y1 = min(self.start_pos.y(), self.current_pos.y())
                x2 = max(self.start_pos.x(), self.current_pos.x())
                y2 = max(self.start_pos.y(), self.current_pos.y())

                # Ensure minimum size for the selection
                if x2 - x1 > 10 and y2 - y1 > 10:
                    self.selected_region = (x1, y1, x2, y2)
                    self.accept()

    def paintEvent(self, event):
        """Draw the selection rectangle"""
        super().paintEvent(event)
        if self.is_selecting and self.start_pos and self.current_pos:
            painter = QPainter(self)
            painter.setPen(QColor(200, 200, 255, 200)) # Light blue border with some transparency
            painter.setBrush(QColor(200, 200, 255, 50)) # Light blue fill with more transparency

            x1 = min(self.start_pos.x(), self.current_pos.x())
            y1 = min(self.start_pos.y(), self.current_pos.y())
            width = abs(self.current_pos.x() - self.start_pos.x())
            height = abs(self.current_pos.y() - self.start_pos.y())

            painter.drawRect(x1, y1, width, height)

    def keyPressEvent(self, event):
        """Handle escape key to cancel selection"""
        if event.key() == Qt.Key_Escape:
            self.reject()


class SettingsDialog(QDialog):
    """Dialog for application settings"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 350) # Slightly taller to accommodate hotkeys labels
        self.setStyleSheet("""
            QDialog {
                background-color: #e0f7fa; /* Light blue background */
            }
            QLabel {
                color: #004d40; /* Dark teal text color */
            }
            QLineEdit, QComboBox, QSpinBox, QSlider {
                background-color: white;
                border: 1px solid #b2ebf2;
                selection-background-color: #80deea;
            }
            QPushButton {
                background-color: #00bcd4; /* Cyan button color */
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #26c6da; /* Slightly darker cyan on hover */
            }
            QTabWidget::pane { /* The tab widget frame */
                border-top: 2px solid #80deea;
            }

            QTabWidget::tab-bar {
                left: 5px; /* move to the right by 5px */
            }

            QTabBar::tab {
                background: #b2ebf2; /* Light cyan tab background */
                border: 1px solid #80deea;
                border-bottom-color: #80deea; /* same as pane color */
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 8ex;
                padding: 2px 10px;
                color: #004d40;
            }

            QTabBar::tab:selected, QTabBar::tab:hover {
                background: #e0f7fa; /* Lighter background for selected/hovered tab */
            }

            QTabBar::tab:selected {
                border-color: #80deea;
                border-bottom-color: transparent; /* make current tab to overlap with the pane */
            }

            QTabBar::tab:!selected {
                margin-top: 2px; /* make non-selected tabs look smaller */
            }
        """)


        self.layout = QVBoxLayout()

        # Tab widget for different settings categories
        self.tabs = QTabWidget()

        # General Settings Tab
        self.general_tab = QWidget()
        general_layout = QFormLayout()

        # Save path setting
        self.default_save_path = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_save_path)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.default_save_path)
        path_layout.addWidget(self.browse_button)

        general_layout.addRow("Default Save Location:", path_layout)

        # Default format setting
        self.default_format = QComboBox()
        self.default_format.addItems(["mp4", "avi", "mov", "wmv"])
        general_layout.addRow("Default Format:", self.default_format)

        self.general_tab.setLayout(general_layout)

        # Hotkeys Tab (Placeholder - actual hotkey implementation is more complex)
        self.hotkeys_tab = QWidget()
        hotkeys_layout = QFormLayout()

        # Hotkey settings - These are just display and placeholders for a real hotkey system
        self.start_hotkey_label = QLabel("Ctrl+Shift+R (Example)") # Just labels showing example hotkeys
        self.pause_hotkey_label = QLabel("Ctrl+Shift+P (Example)")
        self.stop_hotkey_label = QLabel("Ctrl+Shift+S (Example)")

        hotkeys_layout.addRow("Start Recording:", self.start_hotkey_label)
        hotkeys_layout.addRow("Pause/Resume:", self.pause_hotkey_label)
        hotkeys_layout.addRow("Stop Recording:", self.stop_hotkey_label)

        self.hotkeys_tab.setLayout(hotkeys_layout)

        # Add tabs to tab widget
        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.hotkeys_tab, "Hotkeys")

        self.layout.addWidget(self.tabs)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)

        # Load initial settings
        self.load_settings()

    def browse_save_path(self):
        """Open file dialog to select default save location"""
        directory = QFileDialog.getExistingDirectory(self, "Select Default Save Location")
        if directory:
            self.default_save_path.setText(directory)

    def load_settings(self):
        """Load settings from storage (placeholder implementation)"""
        # In a real app, these would be loaded from a settings file or registry
        self.default_save_path.setText(os.path.expanduser("~/Videos"))
        self.default_format.setCurrentText("mp4")
        # Hotkeys labels are set in __init__ - in a real app, load/save and display current hotkeys

    def get_settings(self):
        """Get current settings as a dictionary"""
        return {
            "default_save_path": self.default_save_path.text(),
            "default_format": self.default_format.currentText(),
            # Hotkeys are not configurable in this basic version, just examples shown
        }


class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen Recorder")
        self.resize(900, 650) # Slightly wider for better layout
        self.setMinimumWidth(700) # Minimum width to maintain layout

        # Blue color theme stylesheet for main window and its children
        self.setStyleSheet("""
            QMainWindow {
                background-color: #eceff1; /* Light gray-blue background for main window */
            }
            QGroupBox {
                background-color: #e0f7fa; /* Light blue group box background */
                border: 1px solid #80deea;
                border-radius: 7px;
                margin-top: 6px; /* space above the group box title */
            }

            QGroupBox::title {
                top: -8px; /* position the title */
                left: 10px;
                subcontrol-origin: margin;
                subcontrol-position: top left; /* position at the top left */
                padding: 0 3px;
                color: #004d40; /* Dark teal title color */
                background-color: #e0f7fa; /* Match group box background */
            }


            QLabel {
                color: #263238; /* Dark blue-gray text color */
            }
            QPushButton {
                background-color: #00bcd4; /* Cyan button color */
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 7px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #26c6da; /* Slightly darker cyan on hover */
            }
            QPushButton:disabled {
                background-color: #b2ebf2; /* Light cyan for disabled buttons */
                color: #78909c; /* Grayish text for disabled buttons */
                border: 1px solid #80deea; /* Keep border for disabled buttons */
                font-weight: normal; /* Reset font weight for disabled state */
            }


            QCheckBox, QRadioButton {
                color: #263238; /* Dark blue-gray text color for checkboxes/radio buttons */
            }

            QSpinBox, QSlider, QComboBox {
                background-color: white;
                border: 1px solid #b2ebf2;
                border-radius: 3px;
                padding: 2px;
                selection-background-color: #80deea; /* Selection highlight color */
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid; /* just a single line */
                border-top-right-radius: 3px; /* same radius as border */
                border-bottom-right-radius: 3px;
            }

            QComboBox::down-arrow {
                image: url(icons/down_arrow.png); /* Replace with your arrow icon if needed */
            }

            QMenuBar {
                background-color: #e0f7fa; /* Light blue menu bar background */
                color: #263238; /* Dark blue-gray text color for menu */
                border-bottom: 1px solid #80deea;
            }

            QMenuBar::item {
                background: transparent;
            }

            QMenuBar::item:selected { /* when selected using mouse or keyboard */
                background: #80deea;
            }

            QMenu {
                background-color: #e0f7fa; /* Light blue menu background */
                color: #263238; /* Dark blue-gray text color for menu items */
                border: 1px solid #80deea;
            }

            QMenu::item:selected { /* when user selects item using mouse or keyboard */
                background: #80deea;
            }

            QProgressBar {
                border: 2px solid #80deea;
                border-radius: 5px;
                text-align: center;
                background-color: #e0f7fa; /* Light blue progress bar background */
                color: #263238; /* Dark blue-gray text color for progress */
            }

            QProgressBar::chunk {
                background-color: #00bcd4; /* Cyan progress bar chunk color */
                width: 20px;
                margin: 0.5px;
            }


        """)


        # State variables
        self.recording_thread = None
        self.recording_region = None
        self.is_recording = False
        self.is_paused = False
        self.elapsed_time = 0
        self.last_recording_file = None # To store the path of the last recording

        # Default settings
        self.settings = {
            "default_save_path": os.path.expanduser("~/Videos"),
            "default_format": "mp4",
            # Hotkeys settings would be here in a more advanced version
        }

        # Set up the UI components
        self.init_ui()
        self.update_status("Ready") # Initial status

    def init_ui(self):
        """Initialize the user interface"""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10) # Add some padding around main layout

        # Create menu bar
        self.create_menu_bar()

        # --- Top Section: Recording Mode and Audio ---
        top_section_layout = QHBoxLayout()

        # Recording mode section
        mode_group = QGroupBox("Recording Mode")
        mode_layout = QVBoxLayout()

        # Radio buttons for recording mode
        self.full_screen_radio = QRadioButton("Full Screen")
        self.region_radio = QRadioButton("Select Region")
        self.full_screen_radio.setChecked(True)

        mode_layout.addWidget(self.full_screen_radio)
        mode_layout.addWidget(self.region_radio)

        # Region selection button
        self.select_region_button = QPushButton("Select Region")
        self.select_region_button.clicked.connect(self.open_region_selector)
        self.select_region_button.setEnabled(False) # Disabled initially as Full Screen is default
        mode_layout.addWidget(self.select_region_button)

        # Connect radio buttons to enable/disable region selector
        self.full_screen_radio.toggled.connect(self.toggle_region_selector)

        mode_group.setLayout(mode_layout)
        top_section_layout.addWidget(mode_group)

        # Audio settings section
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QVBoxLayout()

        # Audio capture options
        self.mic_audio_checkbox = QCheckBox("Record Microphone") # Removed System Audio for now

        audio_layout.addWidget(self.mic_audio_checkbox)

        audio_group.setLayout(audio_layout)
        top_section_layout.addWidget(audio_group)

        main_layout.addLayout(top_section_layout)

        # --- Middle Section: Quality Settings ---
        quality_group = QGroupBox("Quality Settings")
        quality_layout = QGridLayout() # Using GridLayout for better alignment

        # Frame rate setting
        frame_rate_label = QLabel("Frame Rate:")
        self.frame_rate_spinbox = QSpinBox()
        self.frame_rate_spinbox.setRange(15, 60)
        self.frame_rate_spinbox.setValue(30)
        self.frame_rate_spinbox.setSuffix(" fps")

        quality_layout.addWidget(frame_rate_label, 0, 0, Qt.AlignLeft)
        quality_layout.addWidget(self.frame_rate_spinbox, 0, 1, Qt.AlignLeft)

        # Quality slider
        quality_label = QLabel("Quality:")
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(80)

        self.quality_value_label = QLabel("80%")
        self.quality_slider.valueChanged.connect(
            lambda value: self.quality_value_label.setText(f"{value}%"))

        quality_layout.addWidget(quality_label, 1, 0, Qt.AlignLeft)
        quality_layout.addWidget(self.quality_slider, 1, 1, 2, 1, Qt.AlignLeft) # Span 2 rows to align with label better
        quality_layout.addWidget(self.quality_value_label, 1, 2, Qt.AlignLeft)

        # Format selection
        format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "avi", "mov", "wmv"])
        quality_layout.addWidget(format_label, 3, 0, Qt.AlignLeft)
        quality_layout.addWidget(self.format_combo, 3, 1, Qt.AlignLeft)

        quality_group.setLayout(quality_layout)
        main_layout.addWidget(quality_group)

        # --- Preview and Status Section ---
        preview_status_layout = QHBoxLayout()

        # Preview panel
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        # Preview display
        self.preview_label = QLabel("Preview will appear here when recording")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #263238; color: #e0f7fa;") # Dark blue background, light text
        self.preview_label.setMinimumSize(320, 240)
        self.preview_label.setMaximumSize(640, 480) # Set max size for preview

        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)
        preview_status_layout.addWidget(preview_group, 2) # Take more space in layout

        # Status panel
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()

        # Timer display
        self.time_label = QLabel("00:00:00")
        self.time_label.setFont(QFont("Arial", 24)) # Larger font for timer
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #263238;") # Dark blue-gray color

        # Status message label
        self.status_message_label = QLabel("Ready") # Renamed from status_label
        self.status_message_label.setAlignment(Qt.AlignCenter)
        self.status_message_label.setFont(QFont("Arial", 12)) # Slightly smaller font for status
        self.status_message_label.setStyleSheet("color: #263238;") # Dark blue-gray color

        status_layout.addWidget(self.time_label)
        status_layout.addWidget(self.status_message_label)
        status_group.setLayout(status_layout)
        preview_status_layout.addWidget(status_group, 1) # Take less space

        main_layout.addLayout(preview_status_layout)

        # --- Bottom Section: Control Buttons ---
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter) # Center buttons horizontally

        self.start_button = QPushButton("Start Recording")
        self.start_button.clicked.connect(self.start_recording)
        self.start_button.setIcon(QIcon.fromTheme("media-record")) # Optional icons for buttons
        self.start_button.setIconSize(self.start_button.sizeHint())

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_resume_recording)
        self.pause_button.setEnabled(False)
        self.pause_button.setIcon(QIcon.fromTheme("media-playback-pause"))
        self.pause_button.setIconSize(self.pause_button.sizeHint())

        self.stop_button = QPushButton("Stop Recording")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)
        self.stop_button.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.stop_button.setIconSize(self.stop_button.sizeHint())

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)

        main_layout.addLayout(button_layout)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #b2ebf2; /* Light blue menu bar background */
                color: #004d40; /* Dark teal text color for menu */
                border-bottom: 1px solid #80deea;
            }

            QMenuBar::item {
                background: transparent;
            }

            QMenuBar::item:selected { /* when selected using mouse or keyboard */
                background: #80deea;
            }

            QMenu {
                background-color: #e0f7fa; /* Light blue menu background */
                color: #004d40; /* Dark teal text color for menu items */
                border: 1px solid #80deea;
            }

            QMenu::item:selected { /* when user selects item using mouse or keyboard */
                background: #80deea;
            }
        """)


        # File menu
        file_menu = menubar.addMenu("File")

        save_action = QAction("Save As...", self)
        save_action.triggered.connect(self.save_as)
        save_action.setEnabled(False)
        self.save_action = save_action

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Settings menu
        settings_menu = menubar.addMenu("Settings")

        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self.open_settings)

        settings_menu.addAction(preferences_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)

        help_menu.addAction(about_action)

    def toggle_region_selector(self, checked):
        """Enable/disable region selector button based on radio button selection"""
        self.select_region_button.setEnabled(self.region_radio.isChecked())
        if not checked: # When switching to region mode, clear any previous full screen selection (not applicable here, but good practice)
            self.recording_region = None

    def open_region_selector(self):
        """Open dialog to select recording region"""
        dialog = RegionSelectorDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_region:
            self.recording_region = dialog.selected_region
            QMessageBox.information(self, "Region Selected",
                                   f"Selected region: {self.recording_region}")
        else:
            # If user canceled, switch back to full screen mode
            self.full_screen_radio.setChecked(True)

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.settings = dialog.get_settings()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About Screen Recorder",
                         "Screen Recorder v1.0\n\n"
                         "A simple screen recording application with a blue theme.\n"
                         "Created with PyQt5.")

    def save_as(self):
        """Save recording to user-specified location - called automatically after recording"""
        if not self.last_recording_file:
            QMessageBox.warning(self, "No Recording", "No recording available to save.")
            return

        # Get current format and generate default filename
        file_format = self.format_combo.currentText()
        default_name = f"screen_recording_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_format}"

        # Open save dialog - now it's always opened when recording finishes
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Recording As", # Changed dialog title
            os.path.join(self.settings["default_save_path"], default_name),
            f"Video Files (*.{file_format})"
        )

        if file_path:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                # Copy the recorded file to the selected location
                shutil.copy2(self.last_recording_file, file_path)

                QMessageBox.information(self, "File Saved",
                                       f"Recording saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error",
                                    f"Failed to save file:\n{str(e)}")
            finally:
                self.last_recording_file = None # Clear last recording file path after saving or cancel

    def update_timer_display(self, seconds):
        """Update timer display with current elapsed time"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}")

    def update_preview(self, pixmap):
        """Update preview with the current frame"""
        scaled_pixmap = pixmap.scaled(
            self.preview_label.width(),
            self.preview_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation # Smoother scaling
        )
        self.preview_label.setPixmap(scaled_pixmap)

    def handle_recording_error(self, error_message):
        """Handle errors during recording"""
        self.update_status("Error")
        QMessageBox.critical(self, "Recording Error", error_message)
        self.reset_ui()

    def recording_finished(self, output_file):
        """Handle completion of recording - now automatically prompts for save as"""
        self.last_recording_file = output_file
        self.update_status("Recording Complete")
        self.save_action.setEnabled(True) # Enable "Save As..." menu option

        self.reset_ui()
        self.save_as() # Directly call save_as to prompt user to save after recording completes
        # QMessageBox.information(self, "Recording Complete", "Recording finished and saved temporarily. Use 'File' -> 'Save As...' to save permanently.") # No longer needed

    def reset_ui(self):
        """Reset UI to initial state after recording is complete"""
        self.is_recording = False
        self.is_paused = False
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.pause_button.setText("Pause")
        self.update_status("Ready") # Update status message to Ready
        self.preview_label.setText("Preview will appear here when recording") # Reset preview text

        # Re-enable settings
        self.full_screen_radio.setEnabled(True)
        self.region_radio.setEnabled(True)
        self.select_region_button.setEnabled(self.region_radio.isChecked())
        self.mic_audio_checkbox.setEnabled(True)
        self.frame_rate_spinbox.setEnabled(True)
        self.quality_slider.setEnabled(True)
        self.format_combo.setEnabled(True)

    def start_recording(self):
        """Start the recording process"""
        if self.is_recording:
            return

        # Check if region is selected when in region mode
        if self.region_radio.isChecked() and not self.recording_region:
            QMessageBox.warning(self, "No Region Selected",
                               "Please select a region to record first.")
            return

        # Disable settings during recording
        self.full_screen_radio.setEnabled(False)
        self.region_radio.setEnabled(False)
        self.select_region_button.setEnabled(False)
        self.mic_audio_checkbox.setEnabled(False)
        self.frame_rate_spinbox.setEnabled(False)
        self.quality_slider.setEnabled(False)
        self.format_combo.setEnabled(False)

        # Update UI for recording state
        self.is_recording = True
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.update_status("Recording") # Use update_status function
        self.elapsed_time = 0
        self.update_timer_display(0)
        self.save_action.setEnabled(False) # Disable save until recording is done
        self.preview_label.clear() # Clear any previous preview image

        # Start recording thread
        self.recording_thread = RecordingThread(
            record_full_screen=self.full_screen_radio.isChecked(),
            region=self.recording_region if self.region_radio.isChecked() else None,
            record_microphone=self.mic_audio_checkbox.isChecked(),
            record_system_audio=False, # System audio removed for now
            frame_rate=self.frame_rate_spinbox.value(),
            quality=self.quality_slider.value(),
            output_format=self.format_combo.currentText()
        )

        # Connect signals from the recording thread
        self.recording_thread.timer_updated.connect(self.update_timer_display)
        self.recording_thread.error_occurred.connect(self.handle_recording_error)
        self.recording_thread.recording_complete.connect(self.recording_finished)
        self.recording_thread.frame_captured.connect(self.update_preview)

        # Start the thread
        self.recording_thread.start()

    def pause_resume_recording(self):
        """Pause or resume the recording"""
        if not self.is_recording or not self.recording_thread:
            return

        if not self.is_paused:
            # Pause recording
            self.is_paused = True
            self.pause_button.setText("Resume")
            self.update_status("Paused") # Use update_status function
            self.recording_thread.pause()
        else:
            # Resume recording
            self.is_paused = False
            self.pause_button.setText("Pause")
            self.update_status("Recording") # Use update_status function
            self.recording_thread.resume()

    def stop_recording(self):
        """Stop the recording"""
        if not self.is_recording or not self.recording_thread:
            return

        self.update_status("Finishing...") # Use update_status function
        self.recording_thread.stop()
        self.pause_button.setEnabled(False) # Disable pause during finishing
        self.stop_button.setEnabled(False) # Disable stop again

        # The thread will emit recording_complete when done

    def update_status(self, message):
        """Updates the status message label with the provided message and visual cue"""
        self.status_message_label.setText(message)
        if message == "Recording":
            self.status_message_label.setStyleSheet("color: red; font-weight: bold;") # Red and bold when recording
        elif message == "Paused":
            self.status_message_label.setStyleSheet("color: orange; font-weight: bold;") # Orange and bold when paused
        elif message == "Error":
            self.status_message_label.setStyleSheet("color: darkred; font-weight: bold;") # Dark red for error
        elif message == "Recording Complete":
            self.status_message_label.setStyleSheet("color: green; font-weight: bold;") # Green when complete
        else:
            self.status_message_label.setStyleSheet("color: #263238; font-weight: normal;") # Default style

    def closeEvent(self, event):
        """Handle window close event"""
        if self.is_recording:
            # Confirm exit if recording is in progress
            reply = QMessageBox.question(
                self, "Exit Confirmation",
                "A recording is in progress. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Stop recording thread if it exists
                if self.recording_thread:
                    self.recording_thread.stop()
                    self.recording_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look and feel

    # Global application stylesheet for a base blue tone (can be further customized in widgets)
    app.setStyleSheet("""
        QApplication {
            background-color: #eceff1; /* Very light blue-gray background */
            color: #263238; /* Dark blue-gray text color (default) */
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
