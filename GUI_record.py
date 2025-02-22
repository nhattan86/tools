# pip install pillow opencv-python pygetwindow sounddevice numpy screeninfo

import tkinter as tk
from tkinter import ttk, Frame
from PIL import ImageGrab
import cv2
import numpy as np
import pygetwindow as gw
import sounddevice as sd
import wave
import threading
import time
import os
from datetime import datetime
from typing import Dict, List, Tuple

class ScreenRecorder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Screen Recorder")
        
        # Get screen dimensions for responsive design
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.aspect_ratio = screen_width / screen_height
        
        # Set window size based on screen dimensions
        window_width = min(800, int(screen_width * 0.7))
        window_height = int(window_width / self.aspect_ratio)
        self.root.geometry(f"{window_width}x{window_height}")
        
        # Control variables
        self.is_recording = False
        self.selected_window = None
        self.record_audio = False
        self.frame_count = 0
        self.start_time = 0
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main container with padding
        container = ttk.Frame(self.root, padding="20")
        container.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Style configuration
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"))
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))
        style.configure("Info.TLabel", font=("Helvetica", 10))
        
        # Title
        title_label = ttk.Label(container, text="Screen Recording Settings", style="Title.TLabel")
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Window selection frame
        window_frame = ttk.LabelFrame(container, text="Capture Selection", padding="10")
        window_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Full screen option
        ttk.Label(window_frame, text="Full Screen:", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        self.fullscreen_combo = ttk.Combobox(window_frame, width=40)
        self.fullscreen_combo.grid(row=1, column=0, sticky="ew", padx=5)
        
        # Application windows
        ttk.Label(window_frame, text="Application Windows:", style="Header.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        self.window_combo = ttk.Combobox(window_frame, width=40)
        self.window_combo.grid(row=3, column=0, sticky="ew", padx=5)
        
        # Update window lists
        self.update_window_lists()
        
        # Recording options frame
        options_frame = ttk.LabelFrame(container, text="Recording Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Audio checkbox
        self.audio_var = tk.BooleanVar()
        audio_check = ttk.Checkbutton(
            options_frame,
            text="Record Audio",
            variable=self.audio_var,
            style="Info.TLabel"
        )
        audio_check.grid(row=0, column=0, sticky="w", pady=5)
        
        # Recording info
        self.info_frame = ttk.LabelFrame(container, text="Recording Information", padding="10")
        self.info_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        self.info_label = ttk.Label(self.info_frame, text="Ready to record", style="Info.TLabel")
        self.info_label.grid(row=0, column=0, sticky="w")
        
        # Control buttons frame
        control_frame = ttk.Frame(container)
        control_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        self.record_button = ttk.Button(
            control_frame,
            text="Start Recording",
            command=self.toggle_recording,
            width=20
        )
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="Exit",
            command=self.root.quit,
            width=20
        ).pack(side=tk.LEFT, padx=5)

    def update_window_lists(self):
        # Get all monitors for full screen recording
        monitors = self.get_monitor_list()
        self.fullscreen_combo['values'] = monitors
        if monitors:
            self.fullscreen_combo.set(monitors[0])
            
        # Get all application windows
        windows = self.get_application_windows()
        self.window_combo['values'] = windows
        if windows:
            self.window_combo.set(windows[0])
            
    def get_monitor_list(self) -> List[str]:
        # Get primary monitor and additional monitors
        monitors = ["Primary Monitor"]
        try:
            import screeninfo
            monitors.extend([f"Monitor {i+2}" for i in range(len(screeninfo.get_monitors())-1)])
        except:
            pass
        return monitors
        
    def get_application_windows(self) -> List[str]:
        # Get all visible windows with titles
        windows = []
        for window in gw.getAllWindows():
            if window.title and window.visible:
                windows.append(f"{window.title} ({window.width}x{window.height})")
        return sorted(windows)

    def get_capture_area(self) -> Dict:
        # Check if full screen or window is selected
        if self.fullscreen_combo.get().startswith("Monitor"):
            # Get monitor dimensions
            return {
                'left': 0,
                'top': 0,
                'width': self.root.winfo_screenwidth(),
                'height': self.root.winfo_screenheight()
            }
        else:
            # Get window dimensions
            window_title = self.window_combo.get().split(" (")[0]
            try:
                window = gw.getWindowsWithTitle(window_title)[0]
                return {
                    'left': window.left,
                    'top': window.top,
                    'width': window.width,
                    'height': window.height
                }
            except:
                return None

    def start_recording(self):
        self.record_button.configure(text="Stop Recording")
        self.is_recording = True
        self.frame_count = 0
        self.start_time = time.time()
        
        # Create output directory if it doesn't exist
        if not os.path.exists('recordings'):
            os.makedirs('recordings')
            
        # Generate filename with new format
        timestamp = datetime.now().strftime("%H%M%S_%d%m%Y")
        self.video_filename = f"recordings/screen_{timestamp}.avi"
        self.audio_filename = f"recordings/audio_{timestamp}.wav"
        
        capture_area = self.get_capture_area()
        if not capture_area:
            return
            
        # Initialize video writer with XVID codec
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter(
            self.video_filename,
            fourcc,
            30.0,
            (capture_area['width'], capture_area['height'])
        )
        
        # Initialize audio recording if selected
        if self.audio_var.get():
            self.audio_file = wave.open(self.audio_filename, 'wb')
            self.audio_file.setnchannels(2)
            self.audio_file.setsampwidth(2)
            self.audio_file.setframerate(44100)
            
            def audio_callback(indata, frames, time, status):
                if self.is_recording:
                    self.audio_file.writeframes(indata.tobytes())
            
            self.audio_stream = sd.InputStream(
                channels=2,
                samplerate=44100,
                dtype=np.int16,
                callback=audio_callback
            )
            self.audio_stream.start()
        
        # Start recording thread
        self.record_thread = threading.Thread(target=self.record_screen)
        self.record_thread.start()
        
        # Update information
        self.update_info()

    def stop_recording(self):
        self.record_button.configure(text="Start Recording")
        self.is_recording = False
        
        if hasattr(self, 'video_writer'):
            self.video_writer.release()
            
        if self.audio_var.get() and hasattr(self, 'audio_stream'):
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_file.close()
            
        self.info_label.configure(
            text=f"Recording saved: {os.path.basename(self.video_filename)}"
        )

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def record_screen(self):
        capture_area = self.get_capture_area()
        if not capture_area:
            return
            
        while self.is_recording:
            # Capture screen
            screen = ImageGrab.grab(bbox=(
                capture_area['left'],
                capture_area['top'],
                capture_area['left'] + capture_area['width'],
                capture_area['top'] + capture_area['height']
            ))
            
            # Convert to numpy array
            frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            
            # Write frame
            self.video_writer.write(frame)
            self.frame_count += 1

    def update_info(self):
        if self.is_recording:
            duration = int(time.time() - self.start_time)
            fps = self.frame_count / duration if duration > 0 else 0
            
            # Format duration as HH:MM:SS
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            
            info_text = (
                f"Recording Duration: {hours:02d}:{minutes:02d}:{seconds:02d}\n"
                f"FPS: {fps:.1f}\n"
                f"Frames Recorded: {self.frame_count}"
            )
            self.info_label.configure(text=info_text)
            self.root.after(1000, self.update_info)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ScreenRecorder()
    app.run()
